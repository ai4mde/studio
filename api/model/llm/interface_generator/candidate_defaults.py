from .section_utils import (
    _FOOTER_TEMPLATE_LAYOUTS,
    _PAGE_NAV_LAYOUTS,
    _fallback_model_for_page,
    _infer_section_layout,
    _model_field_names,
    _navigation_methods,
    _normalize_layout_alias,
    _page_type_value,
    _ref_id,
)
from .token_normalizer import _section_id


def _default_category_for_model(model: str, model_id_by_name: dict[str, str] | None = None) -> dict | None:
    """Build default category for model."""
    model = str(model or "").strip()
    if not model:
        return None
    model_id_by_name = model_id_by_name or {}
    return {
        "label": model,
        "value": {
            "id": str(model_id_by_name.get(model) or model),
            "name": model,
        },
    }

def _model_for_page_category(page: dict, sections_by_id: dict[str, dict], known_models: set[str]) -> str:
    """Infer the model that should own a page category from its bound sections."""
    explicit = str(page.get("primary_model") or "").strip()
    if explicit in known_models:
        return explicit
    for ref in page.get("sections") or []:
        section = sections_by_id.get(_ref_id(ref) or "")
        model = str((section or {}).get("primary_model") or "").strip()
        if model in known_models:
            return model
    fallback = _fallback_model_for_page(page, known_models)
    return fallback if fallback in known_models else ""

def _assign_default_page_categories(pages: list, sections: list, model_id_by_name: dict[str, str] | None = None) -> list:
    """Assign default page categories."""
    model_id_by_name = model_id_by_name or {}
    known_models = set(model_id_by_name.keys())
    sections_by_id = {str(s.get("id")): s for s in sections or [] if s.get("id")}
    next_pages = []
    for raw in pages or []:
        page = dict(raw)
        if _page_type_value(page) == "activity":
            page["category"] = None
            next_pages.append(page)
            continue
        if page.get("category"):
            next_pages.append(page)
            continue
        model = _model_for_page_category(page, sections_by_id, known_models)
        page["category"] = _default_category_for_model(model, model_id_by_name)
        next_pages.append(page)
    return next_pages

def _merge_page_categories(categories: list, pages: list) -> list:
    """Merge page categories."""
    merged = []
    seen = set()
    for category in categories or []:
        if not isinstance(category, dict):
            continue
        cid = str(category.get("id") or ((category.get("value") or {}).get("id") if isinstance(category.get("value"), dict) else "") or "")
        name = str(category.get("name") or ((category.get("value") or {}).get("name") if isinstance(category.get("value"), dict) else "") or category.get("label") or "")
        if not cid and not name:
            continue
        key = cid or name
        seen.add(key)
        merged.append(category)
    for page in pages or []:
        category = page.get("category")
        if not isinstance(category, dict):
            continue
        value = category.get("value") if isinstance(category.get("value"), dict) else {}
        cid = str(value.get("id") or category.get("id") or "")
        name = str(value.get("name") or category.get("name") or category.get("label") or "")
        key = cid or name
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append({"id": cid or name, "name": name or cid})
    return merged

def _default_section_for_page(page: dict, model: str, model_attrs: dict, candidate_index: int) -> dict:
    """Build default section for page."""
    layout = _infer_section_layout(page, candidate_index)
    page_id = _section_id(page.get("id") or page.get("name") or "page")
    sid = f"{page_id}_{_section_id(model or 'content')}_{layout}"
    attrs = _model_field_names(model_attrs, model, 8 if layout in {"table", "detail"} else 5)
    page_text = f"{page.get('id', '')} {page.get('name', '')}".lower()
    is_select_existing = any(term in page_text for term in ("search", "select", "choose", "pick", "browse"))
    operations = {
        "create": layout == "form" and not is_select_existing,
        "update": layout in {"detail", "form"} and not is_select_existing,
        "delete": False,
        "select": is_select_existing,
    }
    style = {
        "color": "accent",
        "density": ("normal", "compact", "spacious")[candidate_index % 3],
        "shadow": "md" if layout in {"card", "gallery", "detail"} else "sm",
        "border": "light",
        "bg": "white",
        "header_style": "large" if layout in {"gallery", "detail"} else "default",
    }
    if layout in {"card", "gallery"}:
        style.update({"display_mode": "grid", "card_style": "default", "columns": "3"})
    elif layout == "list":
        style.update({"list_style": "default"})
    elif layout == "form":
        style.update({"form_style": "step", "cta_label": "Continue"})
    elif layout == "detail":
        style.update({"image_position": "left", "image_size": "md"})
    return {
        "id": sid,
        "name": page.get("name", sid).replace("_", " "),
        "layout": layout,
        "primary_model": model,
        "class": model,
        "attributes": attrs,
        "operations": operations,
        "query": {},
        "col_span": 12,
        "position": "main",
        "style": style,
    }

def _header_sections_for_candidate(normal_pages: list, candidate_index: int = 0) -> list[dict]:
    """Create a single editable header template section with deterministic variation."""
    nav_methods = _navigation_methods([p.get("name") for p in normal_pages if p.get("name")])
    variant = candidate_index % 3
    ops = {"create": False, "update": False, "delete": False}
    templates = ("main-header", "split-header", "dashboard-header", "commerce-header", "app-header", "compact-header", "mega-header", "minimal-header", "hero-header", "tabbed-header", "glass-header", "command-header")
    layout = templates[candidate_index % len(templates)]
    style = {
        "color": "accent",
        "density": ("normal", "compact", "spacious")[variant],
        "shadow": ("sm", "md", "lg")[variant],
        "border": "light",
        "bg": "white",
        "header_variant": {
            "main-header": "commerce",
            "commerce-header": "commerce",
            "split-header": "split-dark",
            "dashboard-header": "dashboard",
            "app-header": "app",
            "compact-header": "compact",
            "mega-header": "mega",
            "minimal-header": "minimal",
            "hero-header": "hero",
            "tabbed-header": "tabs",
            "glass-header": "glass",
            "command-header": "command",
        }.get(layout, "commerce"),
        "nav_height": ("normal", "compact", "tall")[variant],
    }
    return [{
        "id": "app_header_template",
        "name": "Header",
        "role": "header",
        "layout": layout,
        "component": "HeaderTemplate",
        "primary_model": "",
        "class": "",
        "attributes": [],
        "operations": ops,
        "methods": nav_methods,
        "text": "Search",
        "col_span": 12,
        "position": "header",
        "style": style,
    }]

def _footer_sections_for_candidate(candidate_index: int = 0, normal_pages: list | None = None) -> list[dict]:
    """Build footer chrome sections for a generated candidate variant."""
    ops = {"create": False, "update": False, "delete": False}
    templates = ("site-footer", "mega-footer", "legal-footer", "newsletter-footer", "compact-footer", "social-footer", "split-footer", "app-footer", "cta-footer", "minimal-footer")
    layout = templates[candidate_index % len(templates)]
    nav_methods = _navigation_methods([p.get("name") for p in (normal_pages or []) if p.get("name")])
    return [{
        "id": "app_footer_template",
        "name": "Footer",
        "role": "footer",
        "layout": layout,
        "component": "FooterTemplate",
        "primary_model": "",
        "class": "",
        "attributes": [],
        "operations": ops,
        "methods": nav_methods or ["Help", "Privacy", "Terms", "Contact"],
        "col_span": 12,
        "position": "footer",
        "style": {
            "color": "accent",
            "density": ("normal", "compact", "spacious")[candidate_index % 3],
            "shadow": "sm",
            "border": "light",
            "bg": "white",
            "footer_variant": layout,
        },
    }]

def _top_nav_section_for_candidate(normal_pages: list, candidate_index: int = 0) -> dict:
    """Build the top navigation section for a candidate variant."""
    nav_methods = _navigation_methods([p.get("name") for p in normal_pages if p.get("name")])
    return {
        "id": "app_page_nav",
        "name": "Navigation",
        "role": "navigation",
        "layout": "site-nav",
        "component": "NavBar",
        "primary_model": "",
        "class": "",
        "attributes": [],
        "operations": {"create": False, "update": False, "delete": False, "select": False},
        "methods": nav_methods,
        "col_span": 12,
        "position": "header",
        "style": {
            "color": "accent",
            "density": ("normal", "compact", "spacious")[int(candidate_index or 0) % 3],
            "shadow": "sm",
            "border": "light",
            "bg": "white",
            "variant": "page-nav",
            "nav_height": ("compact", "normal", "tall")[int(candidate_index or 0) % 3],
        },
    }

def _sidebar_nav_section_for_candidate(normal_pages: list, candidate_index: int = 0) -> dict:
    """Build the sidebar navigation section for a candidate variant."""
    nav_methods = _navigation_methods([p.get("name") for p in normal_pages if p.get("name")])
    side = "left" if int(candidate_index or 0) % 2 == 0 else "right"
    return {
        "id": "app_sidebar_nav",
        "name": "Navigation",
        "role": "navigation",
        "layout": "site-nav",
        "component": "NavBar",
        "primary_model": "",
        "class": "",
        "attributes": [],
        "operations": {"create": False, "update": False, "delete": False, "select": False},
        "methods": nav_methods,
        "col_span": 12,
        "position": "sidebar",
        "style": {
            "color": "accent",
            "density": ("normal", "compact", "spacious")[int(candidate_index or 0) % 3],
            "shadow": "sm",
            "border": "light",
            "bg": "white",
            "variant": "rail",
            "sidebar_side": side,
            "sidebar_width": 3,
            "nav_height": "tall",
            "full_height": True,
        },
    }

def _find_nav_section_ids(section_map: dict) -> tuple[list, list, list]:
    """Find nav, header-nav, and sidebar-nav section ids from section_map."""
    nav_ids = [
        sid for sid, section in section_map.items()
        if (
            _normalize_layout_alias(section.get("layout")) in {"site-nav", "nav-links", "nav-bar"}
            or str(section.get("component") or "") == "NavBar"
            or str(section.get("role") or "").lower() == "navigation"
        )
    ]
    header_nav_ids = [
        sid for sid, section in section_map.items()
        if section.get("position") == "header"
        and _normalize_layout_alias(section.get("layout")) in _PAGE_NAV_LAYOUTS
    ]
    sidebar_nav_ids = [
        sid for sid in nav_ids
        if (section_map.get(sid) or {}).get("position") == "sidebar"
    ]
    return nav_ids, header_nav_ids, sidebar_nav_ids


def _assign_nav_to_pages(normal_pages: list, keep_nav_id: str, section_map: dict) -> None:
    """Ensure every normal page references keep_nav_id, prepending sidebar navs."""
    for page in normal_pages:
        refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
        ref_ids = {_ref_id(ref) for ref in refs}
        if keep_nav_id not in ref_ids:
            keep_nav_section = section_map.get(keep_nav_id) or {}
            if keep_nav_section.get("position") == "sidebar":
                page["sections"] = [{"value": keep_nav_id}] + refs
            else:
                page["sections"] = refs


def _inject_footer_nav_methods(sections: list, nav_methods: list) -> None:
    """Add navigation methods to footer sections that lack meaningful methods."""
    if not nav_methods:
        return
    generic_methods = {"help", "privacy", "terms", "contact"}
    for section in sections:
        is_footer = (
            section.get("position") == "footer"
            or _normalize_layout_alias(section.get("layout")) in _FOOTER_TEMPLATE_LAYOUTS
        )
        if not is_footer:
            continue
        existing = section.get("methods") or []
        existing_names = {str(m.get("name") if isinstance(m, dict) else m).strip().lower() for m in existing}
        if not existing_names or existing_names.issubset(generic_methods):
            section["methods"] = nav_methods


def _create_or_promote_nav_section(
    keep_nav_id: str,
    sidebar_nav_ids: list,
    header_nav_ids: list,
    sections: list,
    section_map: dict,
    normal_pages: list,
    candidate_index: int,
) -> str:
    """Create a new nav section or promote a sidebar nav to header; return the nav id to keep."""
    if not keep_nav_id:
        use_sidebar = int(candidate_index or 0) % 3 == 2
        nav_section = (
            _sidebar_nav_section_for_candidate(normal_pages, candidate_index)
            if use_sidebar
            else _top_nav_section_for_candidate(normal_pages, candidate_index)
        )
        sid = nav_section["id"]
        suffix = 2
        while sid in section_map:
            sid = f"{nav_section['id']}_{suffix}"
            suffix += 1
        nav_section["id"] = sid
        sections.append(nav_section)
        section_map[sid] = nav_section
        return sid
    if int(candidate_index or 0) % 3 != 2 and keep_nav_id in sidebar_nav_ids and not header_nav_ids:
        nav_section = section_map.get(keep_nav_id) or {}
        nav_section["position"] = "header"
        nav_section["layout"] = "nav-links"
        nav_section["component"] = "NavBar"
        style = dict(nav_section.get("style") or {})
        style.pop("sidebar_side", None)
        style.pop("sidebar_width", None)
        style["variant"] = "page-nav"
        nav_section["style"] = style
    return keep_nav_id


def _ensure_normal_page_navigation(pages: list, sections: list, normal_pages: list, candidate_index: int = 0) -> tuple[list, list]:
    """Ensure normal page navigation."""
    if not normal_pages:
        return pages, sections
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    nav_methods = _navigation_methods([p.get("name") for p in normal_pages if p.get("name")])
    _inject_footer_nav_methods(sections, nav_methods)
    nav_ids, header_nav_ids, sidebar_nav_ids = _find_nav_section_ids(section_map)
    if header_nav_ids:
        keep_nav_id = header_nav_ids[0]
    elif sidebar_nav_ids:
        keep_nav_id = sidebar_nav_ids[0]
    else:
        keep_nav_id = ""
    duplicate_nav_ids = set(nav_ids)
    if keep_nav_id:
        duplicate_nav_ids.discard(keep_nav_id)
    if duplicate_nav_ids:
        sections = [s for s in sections if str(s.get("id") or "") not in duplicate_nav_ids]
        section_map = {str(s.get("id")): s for s in sections if s.get("id")}
        for page in pages:
            page["sections"] = [ref for ref in (page.get("sections") or []) if _ref_id(ref) not in duplicate_nav_ids]

    keep_nav_id = _create_or_promote_nav_section(
        keep_nav_id, sidebar_nav_ids, header_nav_ids,
        sections, section_map, normal_pages, candidate_index,
    )
    if keep_nav_id:
        _assign_nav_to_pages(normal_pages, keep_nav_id, section_map)
    return pages, sections



