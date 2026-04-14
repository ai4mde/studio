"""Generic HTML Emitter — completely semantic-free.

render_node  : one AST node → HTML string (with Jinja2 block syntax for loops/conditionals)
render_page  : list of AST nodes → full page HTML string

AST node types
──────────────
Loop:
    {"loop": "<iterable>", "as": "<var>", "children": [Node, ...]}
    Renders as:  {% for <var> in <iterable> %}...{% endfor %}

Conditional:
    {
        "if": "<expression>",
        "children":      [Node, ...],   # the {% if %} branch
        "elif":          [{"condition": "<expression>", "children": [Node, ...]}, ...],  # optional
        "else_children": [Node, ...],   # optional {% else %} branch
    }
    Renders as:  {% if <expression> %}...{% elif <c> %}...{% else %}...{% endif %}

Raw:
    {"inner_html": "<raw html string>"}   (no "tag" key)
    Renders as-is — use sparingly for SVG or pre-built markup.

Element:
    {
        "tag":        str,          # html tag name, defaults to "div"
        "attrs":      dict,         # html attributes; list values → space-joined string
        "htmx":       dict,         # htmx attributes, prefixed with hx-
        "text":       str,          # literal text content (rendered before children)
        "bind":       str,          # Jinja2 variable to interpolate: {{ bind }}
        "inner_html": str,          # raw HTML to inject inside tag (alongside children)
        "children":   [Node, ...],  # child nodes (rendered recursively)
    }
    Self-closing tags (input, img, etc.) are rendered without children or closing tag.
"""

SELF_CLOSING = {
    "input", "img", "br", "hr", "meta", "link",
    "area", "col", "embed", "param", "source", "track", "wbr",
}


def normalize_attrs(attrs: dict) -> dict:
    """Coerce list values to space-joined strings (e.g. Tailwind class lists)."""
    return {k: " ".join(v) if isinstance(v, list) else v for k, v in attrs.items()}


def normalize_node(node: dict) -> dict:
    """Normalize a node to schema-friendly form before rendering.

    - Moves hx-* keys from attrs into the htmx map.
    - Keeps explicit node["htmx"] values as source of truth when both exist.
    - Recursively normalizes child node containers.
    """
    out = dict(node)

    attrs = dict(out.get("attrs", {}) or {})
    htmx = dict(out.get("htmx", {}) or {})

    moved = {}
    remove_keys = []
    for key, value in attrs.items():
        if key.startswith("hx-"):
            moved[key[3:]] = value
            remove_keys.append(key)
    for key in remove_keys:
        attrs.pop(key, None)

    for key, value in moved.items():
        htmx.setdefault(key, value)

    if attrs:
        out["attrs"] = attrs
    else:
        out.pop("attrs", None)

    if htmx:
        out["htmx"] = htmx
    else:
        out.pop("htmx", None)

    if "children" in out and isinstance(out.get("children"), list):
        out["children"] = [normalize_node(c) if isinstance(c, dict) else c for c in out["children"]]

    if "else_children" in out and isinstance(out.get("else_children"), list):
        out["else_children"] = [normalize_node(c) if isinstance(c, dict) else c for c in out["else_children"]]

    if "elif" in out and isinstance(out.get("elif"), list):
        norm_elif = []
        for branch in out["elif"]:
            if not isinstance(branch, dict):
                norm_elif.append(branch)
                continue
            b = dict(branch)
            if "children" in b and isinstance(b.get("children"), list):
                b["children"] = [normalize_node(c) if isinstance(c, dict) else c for c in b["children"]]
            norm_elif.append(b)
        out["elif"] = norm_elif

    return out


def _resolve_variant_class(tag: str, variant: str, theme: dict) -> str:
    """Look up the Tailwind classes for a variant from the theme token map.

    The LLM may have stored the token under several possible key shapes:
      element.<tag>.<variant>, component.<tag>.<variant>,
      component.<variant>, region.<variant>, or the variant name itself.
    Returns the first match found, or empty string if none.
    """
    tokens = theme.get("tokens") or {}
    for key in (
        f"element.{tag}.{variant}",
        f"component.{tag}.{variant}",
        f"component.{variant}",
        f"region.{variant}",
        variant,
    ):
        classes = tokens.get(key)
        if classes:
            return classes
    return ""


def _resolve_tag_level_class(tag: str, theme: dict) -> str:
    """Best-effort dynamic token lookup for nodes without explicit variants.

    In strict dynamic mode, some AST nodes may not define a variant. This helper
    attempts to resolve a class from tag-scoped token keys only, without relying
    on static defaults.
    """
    tokens = theme.get("tokens") or {}
    if not isinstance(tokens, dict) or not tokens:
        return ""

    candidates = []
    for key, value in tokens.items():
        if not isinstance(value, str) or not value.strip():
            continue
        if key.startswith(f"element.{tag}.") or key.startswith(f"component.{tag}."):
            candidates.append((key, value.strip()))

    if len(candidates) == 1:
        return candidates[0][1]
    return ""


def render_node(node: dict, theme: dict | None = None) -> str:
    """Render a single AST node to an HTML string."""
    node = normalize_node(node)

    # ── Loop node ─────────────────────────────────────────────────────────────
    if "loop" in node:
        var = node.get("as", "item")
        inner = "".join(render_node(c, theme) for c in node.get("children", []))
        return f"{{% for {var} in {node['loop']} %}}{inner}{{% endfor %}}"

    # ── Conditional node ─────────────────────────────────────────────────────
    if "if" in node:
        inner = "".join(render_node(c, theme) for c in node.get("children", []))
        result = f"{{% if {node['if']} %}}{inner}"
        for branch in node.get("elif", []):
            elif_inner = "".join(render_node(c, theme) for c in branch.get("children", []))
            result += f"{{% elif {branch['condition']} %}}{elif_inner}"
        if "else_children" in node:
            else_inner = "".join(render_node(c, theme) for c in node["else_children"])
            result += f"{{% else %}}{else_inner}"
        return result + "{% endif %}"

    # ── Raw node — no tag, just inline HTML ───────────────────────────────────
    if "inner_html" in node and "tag" not in node:
        return node["inner_html"]

    # ── Element node ──────────────────────────────────────────────────────────
    tag = node.get("tag", "div")
    attrs = normalize_attrs(node.get("attrs", {}))
    htmx = node.get("htmx", {})

    # Resolve variant → Tailwind classes from theme tokens
    variant = node.get("variant")
    strict_dynamic = True
    if isinstance(theme, dict):
        strict_dynamic = bool(theme.get("strict_dynamic", True))

    token_class = ""
    if theme:
        if variant:
            token_class = _resolve_variant_class(tag, variant, theme)
        else:
            token_class = _resolve_tag_level_class(tag, theme)

    if token_class:
        existing = attrs.get("class", "")
        # Strict mode: dynamic token class owns the visual style for consistency.
        attrs["class"] = token_class if strict_dynamic else (f"{existing} {token_class}".strip() if existing else token_class)

    attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    hx_str = " ".join(f'hx-{k}="{v}"' for k, v in htmx.items())
    parts = " ".join(filter(None, [attr_str, hx_str]))

    # Pass theme down to child renders
    def _render_child(c: dict) -> str:
        return render_node(c, theme)

    if tag in SELF_CLOSING:
        return f"<{tag}{' ' + parts if parts else ''}/>"

    open_tag = f"<{tag}{' ' + parts if parts else ''}>"
    content = node.get("text", "")
    if "bind" in node:
        content += f"{{{{ {node['bind']} }}}}"
    if "inner_html" in node:
        content += node["inner_html"]
    content += "".join(_render_child(c) for c in node.get("children", []))
    return f"{open_tag}{content}</{tag}>"


def render_page(ast_nodes: list, theme: dict | None = None) -> str:
    """Render a page's AST (list of nodes) to a full HTML string."""
    return "".join(render_node(n, theme) for n in ast_nodes)
