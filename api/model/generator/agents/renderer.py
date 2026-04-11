"""Generic HTML Emitter — completely semantic-free.

render_node  : one AST node → HTML string (with Jinja2 block syntax for loops/conditionals)
render_page  : list of AST nodes → full page HTML string

AST node types
──────────────
Loop:
    {"loop": "<iterable>", "as": "<var>", "children": [Node, ...]}
    Renders as:  {% for <var> in <iterable> %}...{% endfor %}

Conditional:
    {"if": "<expression>", "children": [Node, ...]}
    Renders as:  {% if <expression> %}...{% endif %}

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


def render_node(node: dict) -> str:
    """Render a single AST node to an HTML string."""
    # ── Loop node ─────────────────────────────────────────────────────────────
    if "loop" in node:
        var = node.get("as", "item")
        inner = "".join(render_node(c) for c in node.get("children", []))
        return f"{{% for {var} in {node['loop']} %}}{inner}{{% endfor %}}"

    # ── Conditional node ──────────────────────────────────────────────────────
    if "if" in node:
        inner = "".join(render_node(c) for c in node.get("children", []))
        return f"{{% if {node['if']} %}}{inner}{{% endif %}}"

    # ── Raw node — no tag, just inline HTML ───────────────────────────────────
    if "inner_html" in node and "tag" not in node:
        return node["inner_html"]

    # ── Element node ──────────────────────────────────────────────────────────
    tag = node.get("tag", "div")
    attrs = normalize_attrs(node.get("attrs", {}))
    htmx = node.get("htmx", {})

    attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    hx_str = " ".join(f'hx-{k}="{v}"' for k, v in htmx.items())
    parts = " ".join(filter(None, [attr_str, hx_str]))

    if tag in SELF_CLOSING:
        return f"<{tag}{' ' + parts if parts else ''}/>"

    open_tag = f"<{tag}{' ' + parts if parts else ''}>"
    content = node.get("text", "")
    if "bind" in node:
        content += f"{{{{ {node['bind']} }}}}"
    if "inner_html" in node:
        content += node["inner_html"]
    content += "".join(render_node(c) for c in node.get("children", []))
    return f"{open_tag}{content}</{tag}>"


def render_page(ast_nodes: list) -> str:
    """Render a page's AST (list of nodes) to a full HTML string."""
    return "".join(render_node(n) for n in ast_nodes)
