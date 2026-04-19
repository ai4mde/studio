SELF_CLOSING = {
    "input", "img", "br", "hr", "meta", "link",
    "area", "col", "embed", "param", "source", "track", "wbr",
}


def normalize_attrs(attrs: dict) -> dict:
    return {k: " ".join(v) if isinstance(v, list) else v for k, v in attrs.items()}


def normalize_node(node: dict) -> dict:
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

    if isinstance(out.get("children"), list):
        out["children"] = [normalize_node(c) if isinstance(c, dict) else c for c in out["children"]]
    if isinstance(out.get("else_children"), list):
        out["else_children"] = [normalize_node(c) if isinstance(c, dict) else c for c in out["else_children"]]
    if isinstance(out.get("elif"), list):
        norm_elif = []
        for branch in out["elif"]:
            if not isinstance(branch, dict):
                norm_elif.append(branch)
                continue
            b = dict(branch)
            if isinstance(b.get("children"), list):
                b["children"] = [normalize_node(c) if isinstance(c, dict) else c for c in b["children"]]
            norm_elif.append(b)
        out["elif"] = norm_elif
    return out


def _resolve_variant_class(tag: str, variant: str, theme: dict) -> str:
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
    node = normalize_node(node)

    if "loop" in node:
        var = node.get("as", "item")
        inner = "".join(render_node(c, theme) for c in node.get("children", []))
        return f"{{% for {var} in {node['loop']} %}}{inner}{{% endfor %}}"

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

    if "inner_html" in node and "tag" not in node:
        return node["inner_html"]

    tag = node.get("tag", "div")
    attrs = normalize_attrs(node.get("attrs", {}))
    htmx = node.get("htmx", {})

    variant = node.get("variant")
    token_class = ""
    strict_dynamic = True
    if isinstance(theme, dict):
        strict_dynamic = bool(theme.get("strict_dynamic", True))
        if variant:
            token_class = _resolve_variant_class(tag, variant, theme)
        else:
            token_class = _resolve_tag_level_class(tag, theme)

    if token_class:
        existing = attrs.get("class", "")
        attrs["class"] = token_class if strict_dynamic else (f"{existing} {token_class}".strip() if existing else token_class)

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
    content += "".join(render_node(c, theme) for c in node.get("children", []))
    return f"{open_tag}{content}</{tag}>"


def render_page(ast_nodes: list, theme: dict | None = None) -> str:
    return "".join(render_node(n, theme) for n in ast_nodes)