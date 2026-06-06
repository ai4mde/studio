import re

from .token_normalizer import _section_id
from .uml_mapping.usecase_workflow import (
    _activity_layout_for_step,
    _activity_models_for_step,
    _humanize_action_label,
    _is_child_collection_model,
    _name_tokens,
)


def _normalize_section_operations(operations) -> dict:
    defaults = {"create": False, "update": False, "delete": False, "select": False}
    select_terms = {"select", "choose", "pick", "bulk_select", "multi_select", "batch_select"}
    false_terms = {"", "0", "false", "no", "none", "null", "off"}

    def enabled(value) -> bool:
        if isinstance(value, str):
            return value.strip().lower() not in false_terms
        return bool(value)

    if isinstance(operations, dict):
        normalized = dict(defaults)
        normalized.update({
            "create": any(enabled(operations.get(term, False)) for term in ("create", "add")),
            "update": any(enabled(operations.get(term, False)) for term in ("update", "edit")),
            "delete": any(enabled(operations.get(term, False)) for term in ("delete", "remove")),
            "select": any(enabled(operations.get(term, False)) for term in select_terms),
        })
        return normalized
    if isinstance(operations, str):
        operations = re.split(r"[\s,;|]+", operations)
    if isinstance(operations, list):
        values = {str(value).strip().lower() for value in operations}
        return {
            "create": bool({"create", "add"} & values),
            "update": bool({"update", "edit"} & values),
            "delete": bool({"delete", "remove"} & values),
            "select": bool(select_terms & values),
        }
    return defaults.copy()

_LAYOUT_ALIASES = {
    "nav": "nav-links",
    "navigation": "nav-links",
    "navbar": "nav-links",
    "side-nav": "nav-links",
    "top-nav": "nav-links",
    "footer-links": "link-grid",
    "footer-brand": "brand-strip",
    "service-strip": "service-bar",
}

_HEADER_TEMPLATE_LAYOUTS = {
    "promo-bar", "logo", "search-bar", "icon-actions", "nav-links", "main-header", "minimal-header",
    "commerce-header", "dashboard-header", "split-header", "app-header", "compact-header", "mega-header",
    "hero-header", "tabbed-header", "glass-header", "command-header", "site-nav",
}
_HEADER_SHELL_LAYOUTS = {
    "main-header", "minimal-header", "commerce-header", "dashboard-header",
    "split-header", "app-header", "compact-header", "mega-header", "hero-header", "tabbed-header",
    "glass-header", "command-header",
}
_HEADER_NAV_LAYOUTS = {
    "nav-links", "site-nav", "nav-bar", "main-header", "commerce-header", "dashboard-header",
    "split-header", "app-header", "compact-header", "mega-header", "hero-header", "tabbed-header",
    "glass-header", "command-header",
}
_PAGE_NAV_LAYOUTS = {"nav-links", "site-nav", "nav-bar", "tabbed-header", "mega-header"}
_FOOTER_TEMPLATE_LAYOUTS = {
    "service-bar", "link-grid", "brand-strip", "compact-footer", "legal-footer",
    "newsletter-footer", "social-footer", "mega-footer", "site-footer", "split-footer", "app-footer",
    "cta-footer", "minimal-footer",
}
_CHROME_TEMPLATE_LAYOUTS = _HEADER_TEMPLATE_LAYOUTS | _FOOTER_TEMPLATE_LAYOUTS
_VALID_SECTION_LAYOUTS = {"card", "list", "table", "detail", "gallery", "filter", "form", "activity_action", "activity_start", "activity_tasks"} | _CHROME_TEMPLATE_LAYOUTS
_DATA_SECTION_LAYOUTS = {"card", "list", "table", "detail", "gallery", "form"}
_DATA_SECTION_ROLES = {"object_collection", "object_detail", "object_summary", "child_collection", "object_form"}
_VALID_SECTION_STYLE = {
    "color": {
        "blue", "sky", "cyan", "aqua", "teal", "turquoise", "green", "emerald", "lime",
        "yellow", "amber", "gold", "orange", "red", "rose", "pink", "purple", "violet",
        "indigo", "navy", "brown", "beige", "tan", "cream", "slate", "zinc", "neutral",
        "black", "white", "accent", "accent-secondary",
    },
    "density": {"compact", "normal", "spacious"},
    "nav_height": {"compact", "normal", "tall", "xl"},
    "shadow": {"none", "sm", "md", "lg", "xl"},
    "border": {"none", "light", "colored", "strong"},
    "bg": {"white", "light", "gray", "dark"},
    "header_style": {"default", "large", "small", "colored", "hidden"},
    "display_mode": {"grid", "carousel", "banner"},
    "card_style": {"default", "product", "category", "compact"},
    "list_style": {"default", "product", "cart-item", "related"},
    "form_style": {"default", "auth", "step", "summary"},
    "image_position": {"left", "top", "right"},
    "image_size": {"sm", "md", "lg"},
    "banner_height": {"sm", "md", "lg", "xl"},
    "image_ratio": {"wide", "16:9", "4:3", "1:1", "portrait"},
    "logo_size": {"sm", "md", "lg", "xl"},
    "logo_shape": {"rounded", "circle", "square"},
}

def _normalize_layout_alias(layout) -> str:
    if isinstance(layout, list):
        raw_values = layout
    else:
        raw_values = re.split(r"[,|/]+", str(layout or ""))
    values = [str(value or "").strip() for value in raw_values if str(value or "").strip()]
    for value in values:
        normalized = _LAYOUT_ALIASES.get(value, value)
        if normalized in _CHROME_TEMPLATE_LAYOUTS or normalized in {"card", "list", "table", "detail", "gallery", "filter", "form", "activity_action", "activity_start", "activity_tasks"}:
            return normalized
    value = values[0] if values else ""
    return _LAYOUT_ALIASES.get(value, value)

def _workflow_task_section(step: dict, model: str, model_attrs: dict) -> dict:
    page_id = _section_id(step.get("page_id") or step.get("page_name") or "workflow")
    model_id = _section_id(model)
    layout = _activity_layout_for_step(step.get("activity_node_name", ""), model)
    name_l = f"{step.get('activity_node_name', '')} {model}".lower()
    style = {
        "color": "accent",
        "density": "compact" if layout in {"list", "table"} else "normal",
        "shadow": "sm",
        "border": "light",
        "bg": "white",
    }
    if layout == "list":
        style["list_style"] = "default"
    if layout == "form":
        style["form_style"] = "step"
        style["cta_label"] = "Save"
    return {
        "id": f"{page_id}_{model_id}_task_content",
        "name": f"{step.get('activity_node_name') or 'Task'} {model}",
        "layout": layout,
        "primary_model": model,
        "class": model,
        "attributes": _model_field_names(model_attrs, model, 8),
        "operations": {
            "create": layout == "form",
            "update": layout in {"form", "list", "table", "detail"},
            "delete": layout in {"list", "table"},
        },
        "query": {},
        "col_span": 12,
        "position": "main",
        "style": style,
    }

def _ensure_workflow_pages(pages: list, sections: list, workflow_steps: list, model_attrs: dict | None = None, usecase_navigation: dict | None = None) -> tuple[list, list]:
    if not workflow_steps:
        return pages, sections
    model_attrs = model_attrs or {}
    known_models = set(model_attrs.keys())
    workflow_entries = (usecase_navigation or {}).get("workflow_entry_points") or []
    pages = [dict(p) for p in pages]
    sections = [dict(s) for s in sections]
    section_ids = {str(s.get("id")) for s in sections}
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}

    def page_action_id(p: dict) -> str:
        action = p.get("action") or {}
        if isinstance(action, dict):
            return str(action.get("value") or action.get("id") or "")
        return ""

    page_by_action = {page_action_id(p): p for p in pages if page_action_id(p)}
    # Fallback index: Step-5 pages from interface_planner have no action.value (no node UUID),
    # but their name matches the activity action name ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â use this to avoid creating duplicates.
    page_by_name = {
        _section_id(p.get("name") or ""): p
        for p in pages
        if _page_type_value(p) == "activity" and not page_action_id(p)
    }
    for step in workflow_steps:
        node_id = step["activity_node_id"]
        name_key = _section_id(step.get("activity_node_name") or "")
        page = page_by_action.get(node_id) or page_by_name.get(name_key)
        if not page:
            page = {
                "id": step["page_id"],
                "name": step["page_name"],
                "primary_model": "",
                "type": {"value": "activity", "label": "Activity"},
                "action": {"value": node_id, "label": step["activity_node_name"]},
                "sections": [],
                "category": None,
            }
            pages.append(page)
            page_by_action[node_id] = page
        else:
            page["type"] = {"value": "activity", "label": "Activity"}
            page["action"] = {"value": node_id, "label": step["activity_node_name"]}
            page.setdefault("category", None)
            page.setdefault("sections", [])
        refs = page.get("sections") or []
        ref_ids = {str(ref.get("value") if isinstance(ref, dict) else ref) for ref in refs}
        has_existing_content = any(
            (section_map.get(sid) or {}).get("layout") not in {"filter", "activity_action", "activity_start", "activity_tasks"}
            and (section_map.get(sid) or {}).get("position", "main") == "main"
            for sid in ref_ids
        )
        for sid in list(ref_ids):
            existing = section_map.get(sid) or {}
            model = existing.get("primary_model") or existing.get("class")
            if (
                model
                and existing.get("position", "main") == "main"
                and existing.get("layout") not in {"filter", "activity_action", "activity_start", "activity_tasks"}
            ):
                desired_layout = _activity_layout_for_step(step.get("activity_node_name", ""), model)
                existing["layout"] = desired_layout
                if desired_layout == "form":
                    existing["role"] = "object_form"
                    existing["component"] = existing.get("component") or "ObjectForm"
                    style = existing.get("style") if isinstance(existing.get("style"), dict) else {}
                    style["form_style"] = style.get("form_style") or "step"
                    style["cta_label"] = style.get("cta_label") or "Save"
                    existing["style"] = style
                elif desired_layout == "list":
                    existing["role"] = existing.get("role") or "object_collection"
                else:
                    existing["role"] = existing.get("role") or "object_detail"
                existing["operations"] = {
                    "create": desired_layout == "form",
                    "update": desired_layout in {"form", "list", "table", "detail"},
                    "delete": desired_layout in {"list", "table"},
                }
        for model in ([] if has_existing_content else _activity_models_for_step(step, workflow_entries, known_models)[:1]):
            content = _workflow_task_section(step, model, model_attrs)
            if any((section_map.get(sid) or {}).get("primary_model") == model and (section_map.get(sid) or {}).get("layout") != "filter" for sid in ref_ids):
                continue
            sid = content["id"]
            suffix = 2
            base_sid = sid
            while sid in section_ids:
                sid = f"{base_sid}_{suffix}"
                suffix += 1
            content["id"] = sid
            sections.append(content)
            section_ids.add(sid)
            section_map[sid] = content
            refs.append({"value": sid})
            ref_ids.add(sid)
        existing_action_ids = [
            sid for sid in ref_ids
            if (section_map.get(sid) or {}).get("type") == "activity_action"
            or (section_map.get(sid) or {}).get("layout") == "activity_action"
        ]
        button_id = existing_action_ids[0] if existing_action_ids else f"{_section_id(page.get('id') or page.get('name'))}_workflow_action"
        if not existing_action_ids:
            if button_id not in section_ids:
                button = {
                    "id": button_id,
                    "name": f"{page.get('name', step['page_name']).replace('_', ' ')} Continue",
                    "label": "Continue",
                    "type": "activity_action",
                    "layout": "activity_action",
                    "primary_model": "",
                    "class": "",
                    "operations": {"create": False, "update": False, "delete": False},
                    "attributes": [],
                    "methods": [],
                    "col_span": 12,
                    "position": "main",
                    "style": {"variant": "wizard_next", "align": "right", "size": "lg"},
                    "workflow": {"action": "complete"},
                }
                sections.append(button)
                section_map[button_id] = button
                section_ids.add(button_id)
            if button_id not in ref_ids:
                refs.append({"value": button_id})
            page["sections"] = refs
    return pages, sections

def _normalize_activity_action_sections(pages: list, sections: list) -> list:
    activity_page_section_ids = set()
    for page in pages:
        page_type = page.get("type", {}); page_type_value = page_type.get("value") if isinstance(page_type, dict) else page_type
        if page_type_value != "activity": continue
        for ref in page.get("sections") or []: activity_page_section_ids.add(str(ref.get("value") if isinstance(ref, dict) else ref))
    for section in sections:
        sid = str(section.get("id", "")); is_activity_action = section.get("type") == "activity_action" or section.get("layout") == "activity_action"
        if not is_activity_action: continue
        operations = _normalize_section_operations(section.get("operations"))
        section["operations"] = operations
        has_data_shape = bool(section.get("primary_model")) or bool(section.get("attributes")) or any(operations.values())
        if has_data_shape and sid not in activity_page_section_ids:
            section["layout"] = "list"; section.pop("type", None); section.pop("workflow", None); section.pop("workflow_action", None); section.pop("target_page", None); section.pop("targetPage", None); style = section.get("style") or {}
            if style.get("variant") in {"button", "link", "fab", "wizard_next", "auto"}: style.pop("variant", None)
            section["style"] = style; continue
        section["type"] = "activity_action"; section["layout"] = "activity_action"; section["primary_model"] = ""; section["class"] = ""; section["attributes"] = []; section["operations"] = {"create": False, "update": False, "delete": False}; section.setdefault("label", section.get("name") or "Continue"); workflow = section.get("workflow") or {}; workflow.setdefault("action", section.get("workflow_action") or "complete"); section["workflow"] = workflow
    # Deduplicate: per activity page, keep only one activity_action (prefer complete/complete_then_page)
    section_map = {str(s.get("id", "")): s for s in sections}
    to_remove: set = set()
    for page in pages:
        page_type = page.get("type", {}); page_type_value = page_type.get("value") if isinstance(page_type, dict) else page_type
        if page_type_value != "activity": continue
        ref_ids = [str(r.get("value") if isinstance(r, dict) else r) for r in (page.get("sections") or [])]
        action_ids = [sid for sid in ref_ids if (section_map.get(sid) or {}).get("layout") == "activity_action"]
        if len(action_ids) <= 1: continue
        action_ids.sort(key=lambda sid: 0 if (section_map.get(sid) or {}).get("workflow", {}).get("action") in {"complete", "complete_then_page"} else 1)
        extras = set(action_ids[1:])
        to_remove |= extras
        page["sections"] = [r for r in (page.get("sections") or []) if str(r.get("value") if isinstance(r, dict) else r) not in extras]
    if to_remove:
        sections = [s for s in sections if str(s.get("id", "")) not in to_remove]
    return sections

def _normalize_chrome_sections(sections: list) -> list:
    """Keep header/footer/navigation chrome out of workflow/action rendering paths."""
    normalized = []
    for section in sections or []:
        section = dict(section)
        layout = _normalize_layout_alias(section.get("layout"))
        role = str(section.get("role") or "").lower()
        position = section.get("position")
        is_chrome = (
            layout in _CHROME_TEMPLATE_LAYOUTS
            or position in {"header", "footer"}
            or role in {"header", "footer", "navigation", "nav", "brand"}
        )
        if is_chrome:
            # If the agent assigned a data/action layout to a chrome position, replace with
            # the positional default so _infer_section_component returns the right component.
            if layout not in _CHROME_TEMPLATE_LAYOUTS:
                layout = "site-footer" if position == "footer" else "main-header"
            section["layout"] = layout
            section["primary_model"] = ""
            section["class"] = ""
            section["attributes"] = []
            section["operations"] = {"create": False, "update": False, "delete": False, "select": False}
            section.pop("type", None)
            for key in ("workflow", "workflow_action", "target_page", "targetPage"):
                section.pop(key, None)
            # Clear any stale component so _infer_section_component runs fresh from layout.
            section.pop("component", None)
            section["component"] = _infer_section_component(section)
        normalized.append(section)
    return normalized

def _page_type_value(page: dict) -> str:
    page_type = page.get("type")
    if isinstance(page_type, dict):
        return str(page_type.get("value") or "").strip().lower()
    return str(page_type or "").strip().lower()

def _infer_page_type_value(page: dict) -> str:
    explicit = _page_type_value(page)
    if explicit in {"normal", "activity"}:
        return explicit
    action = page.get("action")
    page_key = f"{page.get('id', '')} {page.get('name', '')} {page.get('display_name', '')}".lower()
    if action or "workflow" in page_key:
        return "activity"
    return "normal"

def _canonical_page_type(value: str) -> dict:
    if value == "activity":
        return {"value": "activity", "label": "Activity"}
    return {"value": "normal", "label": "Normal"}

def _ref_id(ref) -> str:
    return str(ref.get("value") if isinstance(ref, dict) else ref or "")

def _navigation_methods(names: list[str]) -> list[dict]:
    return [
        {"name": str(name), "label": str(name).replace("_", " "), "action": "navigate"}
        for name in names
        if name
    ]

def _workflow_icon_links(usecase_navigation: dict, page_by_id: dict | None = None) -> list[dict]:
    links = []
    seen = set()
    page_by_id = page_by_id or {}
    for entry in (usecase_navigation or {}).get("workflow_entry_points") or []:
        page_id = _section_id(entry.get("page_id") or entry.get("page_name"))
        if not page_id or page_id in seen:
            continue
        page = page_by_id.get(page_id) or {}
        page_name = page.get("name") or entry.get("page_name") or _page_name(page_id)
        label = entry.get("button_label") or entry.get("label") or entry.get("usecase_name") or "Start"
        links.append({"page": page_name, "label": label, "icon": "task"})
        seen.add(page_id)
    return links

def _infer_section_component(section: dict) -> str:
    """
    Generically infers a suitable high-fidelity component name based on 
    layout and model characteristics, avoiding app-specific hardcoding.
    """
    component = section.get("component")
    if component:
        return str(component)
    
    layout = _normalize_layout_alias(section.get("layout"))
    role = str(section.get("role") or "")
    model_name = str(section.get("primary_model") or section.get("class") or "").lower()
    attrs = {str(a.get("name") if isinstance(a, dict) else a).lower() for a in section.get("attributes", [])}
    
    # Generic rules based on data traits
    has_image = any(term in attrs for term in ("image", "img", "url", "avatar", "photo", "media"))
    is_person = any(term in model_name for term in ("user", "customer", "employee", "doctor", "member", "actor"))
    
    if layout == "logo": return "Logo"
    if layout == "search-bar": return "SearchBar"
    if layout == "icon-actions": return "IconActions"
    if layout in _FOOTER_TEMPLATE_LAYOUTS: return "FooterTemplate"
    if layout in _HEADER_TEMPLATE_LAYOUTS and layout not in {"logo", "search-bar", "icon-actions", "site-nav", "nav-links"}:
        return "HeaderTemplate"
    if layout in {"site-nav", "nav-links", "nav-bar"}: return "NavBar"
    
    if layout == "form":
        if any(term in model_name for term in ("address", "location")): return "AddressForm"
        if any(term in model_name for term in ("payment", "card", "billing")): return "PaymentForm"
        return "ObjectForm"
        
    if layout == "gallery" or layout == "card":
        if has_image: return "ImageCardGrid" if layout == "gallery" else "ImageCard"
        if is_person: return "PersonCardGrid"
        return "ObjectCardGrid"
        
    if layout == "detail":
        return "ObjectDetailPanel" if not has_image else "MediaDetailPanel"
        
    if layout == "table": return "DataTable"
    if layout == "list": return "ObjectList"
    if layout == "filter": return "FilterPanel"
    
    return "SectionPanel"


def _is_select_existing_text(text: str) -> bool:
    tokens = _name_tokens(text)
    if tokens & {"search", "select", "choose", "pick", "browse"}:
        return True
    text_l = str(text or "").lower()
    return any(phrase in text_l for phrase in ("find existing", "select existing", "choose existing", "pick existing"))


def _normalize_select_existing_sections(pages: list, sections: list) -> list:
    """Search/select/browse pages choose existing records instead of creating new ones."""
    section_page_text: dict[str, str] = {}
    for page in pages or []:
        if not isinstance(page, dict):
            continue
        page_text = f"{page.get('id', '')} {page.get('name', '')} {page.get('display_name', '')} {page.get('activity_name', '')}"
        if not _is_select_existing_text(page_text):
            continue
        for ref in page.get("sections") or []:
            sid = _ref_id(ref)
            if sid:
                section_page_text[sid] = f"{section_page_text.get(sid, '')} {page_text}"

    fixed = []
    for section in sections or []:
        if not isinstance(section, dict):
            fixed.append(section)
            continue
        section = dict(section)
        sid = str(section.get("id") or "")
        layout = _normalize_layout_alias(section.get("layout"))
        role = str(section.get("role") or "")
        position = str(section.get("position") or "main")
        is_data_section = bool(section.get("primary_model")) or bool(section.get("attributes")) or role in _DATA_SECTION_ROLES
        probe = f"{sid} {section.get('name', '')} {section.get('display_name', '')} {section_page_text.get(sid, '')}"
        if position == "main" and layout != "activity_action" and is_data_section and _is_select_existing_text(probe):
            if layout in {"form", "gallery"}:
                layout = "card"
                section["layout"] = layout
            section["operations"] = {"create": False, "update": False, "delete": False, "select": True}
            section["role"] = "object_collection" if role in {"", "object_form"} else role
            section["component"] = {
                "table": "DataTable",
                "list": "ObjectList",
                "gallery": "ObjectCardGrid",
                "card": "ObjectCardGrid",
            }.get(layout, "ObjectCardGrid")
        fixed.append(section)
    return fixed

def _field_layout_field_refs(field_layout) -> set[str]:
    refs = set()
    if not isinstance(field_layout, dict):
        return refs
    slot_keys = {"image", "video", "media", "avatar", "hero", "title", "subtitle", "primary", "price", "description", "count"}
    list_keys = {"secondary", "badges", "meta", "facts", "fields", "hidden"}
    for key, value in field_layout.items():
        if key in slot_keys and isinstance(value, str) and value:
            refs.add(value)
        elif key in list_keys and isinstance(value, list):
            refs.update(str(v) for v in value if isinstance(v, str) and v)
        elif key == "columns" and isinstance(value, list):
            for column in value:
                if isinstance(column, dict) and column.get("field"):
                    refs.add(str(column["field"]))
        elif key == "groups" and isinstance(value, list):
            for group in value:
                if isinstance(group, dict) and isinstance(group.get("fields"), list):
                    refs.update(str(v) for v in group["fields"] if isinstance(v, str) and v)
        elif key == "field_styles" and isinstance(value, dict):
            refs.update(str(field) for field in value.keys() if field)
    return refs

_FIELD_SLOT_MAP = {
    "card": {"image", "video", "media", "title", "subtitle", "primary", "secondary", "hidden"},
    "gallery": {"image", "video", "media", "title", "subtitle", "primary", "secondary", "hidden"},
    "list": {"columns", "hidden"},
    "table": {"columns", "hidden"},
    "detail": {"image", "video", "media", "title", "hero", "fields", "hidden"},
    "form": {"fields", "hidden"},
    "filter": {"fields", "hidden"},
}
_COMPONENT_FIELD_SLOT_MAP = {
    "ProductCardGrid": _FIELD_SLOT_MAP["card"],
    "CategoryTileGrid": {"image", "title", "subtitle", "secondary", "hidden"},
    "PersonCardGrid": {"image", "title", "subtitle", "secondary", "hidden"},
    "CardGrid": _FIELD_SLOT_MAP["card"],
    "DataTable": _FIELD_SLOT_MAP["table"],
    "ObjectList": _FIELD_SLOT_MAP["list"],
    "LineItemList": _FIELD_SLOT_MAP["list"],
    "RelatedObjectList": _FIELD_SLOT_MAP["list"],
    "ProductDetailPanel": _FIELD_SLOT_MAP["detail"],
    "DetailPanel": _FIELD_SLOT_MAP["detail"],
    "SummaryPanel": {"title", "fields", "hidden"},
    "ObjectForm": _FIELD_SLOT_MAP["form"],
    "AddressForm": _FIELD_SLOT_MAP["form"],
    "PaymentMethodForm": _FIELD_SLOT_MAP["form"],
    "ReviewForm": _FIELD_SLOT_MAP["form"],
    "FilterPanel": _FIELD_SLOT_MAP["filter"],
    "SearchBar": _FIELD_SLOT_MAP["filter"],
    "Logo": set(),
    "BrandLockup": set(),
    "ImageLogo": set(),
    "IconActions": set(),
    "SiteFooter": set(),
    "FooterLinkGrid": set(),
}

def _attr_name(attr) -> str:
    return str(attr.get("name") if isinstance(attr, dict) else attr or "")

def _attr_type(attr) -> str:
    return str(attr.get("type") if isinstance(attr, dict) else "").lower()

def _field_kind(name: str, type_name: str = "") -> str:
    low = name.lower()
    if type_name in {"image", "video"} or any(term in low for term in ("image", "img", "photo", "avatar", "thumbnail", "media", "video", "poster")):
        return "media"
    if low in {"id", "uuid"} or low.endswith("_id") or any(term in low for term in ("internal", "password", "token", "secret")):
        return "hidden"
    if any(term in low for term in ("name", "title", "code", "number", "label", "subject")):
        return "title"
    if any(term in low for term in ("price", "amount", "total", "status", "state", "date", "created", "updated", "count", "quantity")):
        return "primary"
    if any(term in low for term in ("description", "summary", "body", "content", "note", "comment", "message")):
        return "body"
    return "secondary"

def _supported_field_slots(section: dict) -> set[str]:
    component = str(section.get("component") or "")
    layout = str(section.get("layout") or "")
    return set(_COMPONENT_FIELD_SLOT_MAP.get(component) or _FIELD_SLOT_MAP.get(layout) or set())

def _field_list(value) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, dict) and item.get("field"):
            result.append(str(item["field"]))
        elif isinstance(item, str) and item:
            result.append(item)
    return result

def _component_for_layout(section: dict, layout: str) -> str:
    if layout == "table":
        return "DataTable"
    if layout == "list":
        return "ObjectList"
    if layout == "form":
        return "ObjectForm"
    if layout == "filter":
        return "FilterPanel"
    section = {**section, "layout": layout}
    return _infer_section_component(section)

def _normalize_field_layout(section: dict) -> dict:
    attrs = section.get("attributes") or []
    attr_names = [_attr_name(attr) for attr in attrs if _attr_name(attr)]
    if not attr_names or not section.get("primary_model"):
        return {}
    attr_set = set(attr_names)
    supported = _supported_field_slots(section)
    if not supported:
        return {}

    raw = section.get("field_layout") if isinstance(section.get("field_layout"), dict) else {}
    existing_styles = raw.get("field_styles") if isinstance(raw.get("field_styles"), dict) else {}
    cleaned_styles = {}
    for fname, cfg in existing_styles.items():
        if fname not in attr_set or not isinstance(cfg, dict):
            continue
        clean = {}
        if isinstance(cfg.get("order"), int) or str(cfg.get("order", "")).isdigit():
            clean["order"] = int(cfg.get("order"))
        if str(cfg.get("col_span", "")) in {"3", "4", "6", "8", "12"}:
            clean["col_span"] = int(cfg.get("col_span"))
        if cfg.get("height") in {"sm", "md", "lg", "xl"}:
            clean["height"] = cfg.get("height")
        if cfg.get("text_size") in {"xs", "sm", "md", "lg", "xl"}:
            clean["text_size"] = cfg.get("text_size")
        if cfg.get("align") in {"left", "center", "right"}:
            clean["align"] = cfg.get("align")
        if cfg.get("label") in {"show", "hidden"}:
            clean["label"] = cfg.get("label")
        if cfg.get("visible") in {"show", "hidden"}:
            clean["visible"] = cfg.get("visible")
        if clean:
            cleaned_styles[fname] = clean

    hidden = [f for f in _field_list(raw.get("hidden")) if f in attr_set]
    for attr in attrs:
        name = _attr_name(attr)
        if name and _field_kind(name, _attr_type(attr)) == "hidden" and name not in hidden:
            hidden.append(name)
    for name, cfg in cleaned_styles.items():
        if cfg.get("visible") == "hidden" and name not in hidden:
            hidden.append(name)
    visible_names = [name for name in attr_names if name not in set(hidden)]

    def first_existing(keys: list[str]) -> str:
        for key in keys:
            value = raw.get(key)
            if isinstance(value, str) and value in visible_names:
                return value
        return ""

    media = first_existing(["media", "image", "video", "avatar"])
    title = first_existing(["title"])
    subtitle = first_existing(["subtitle"])
    primary = first_existing(["primary", "price", "count"])
    secondary = [f for f in (_field_list(raw.get("secondary")) + _field_list(raw.get("meta")) + _field_list(raw.get("facts"))) if f in visible_names]
    fields = [f for f in (_field_list(raw.get("fields")) + _field_list(raw.get("columns"))) if f in visible_names]
    hero = [f for f in _field_list(raw.get("hero")) if f in visible_names]

    by_kind = {name: _field_kind(name, _attr_type(attr)) for name, attr in zip(attr_names, attrs)}
    if not media:
        media = next((n for n in visible_names if by_kind.get(n) == "media"), "")
    if not title:
        title = next((n for n in visible_names if by_kind.get(n) == "title"), "")
    if not primary:
        primary = next((n for n in visible_names if by_kind.get(n) == "primary" and n != title), "")
    if not secondary:
        secondary = [n for n in visible_names if n not in {media, title, primary} and by_kind.get(n) in {"secondary", "body", "primary"}][:4]
    if not fields:
        fields = visible_names
    if not hero:
        hero = [n for n in visible_names if n in {title, primary} or by_kind.get(n) == "body"][:4]

    out = {}
    if "image" in supported and media:
        media_attr = next((a for a in attrs if _attr_name(a) == media), None)
        if _attr_type(media_attr) == "video":
            if "video" in supported:
                out["video"] = media
            elif "media" in supported:
                out["media"] = media
        else:
            out["image"] = media
    elif "media" in supported and media:
        out["media"] = media
    if "title" in supported and title:
        out["title"] = title
    if "subtitle" in supported and subtitle:
        out["subtitle"] = subtitle
    if "primary" in supported and primary:
        out["primary"] = primary
    if "secondary" in supported:
        out["secondary"] = [f for f in secondary if f not in {media, title, primary}]
    if "columns" in supported:
        out["columns"] = fields
    if "fields" in supported:
        out["fields"] = fields
    if "hero" in supported:
        out["hero"] = hero
    if "hidden" in supported and hidden:
        out["hidden"] = hidden
    if cleaned_styles:
        out["field_styles"] = cleaned_styles
    return out

def _model_field_names(model_attrs: dict, model: str, limit: int = 6) -> list[str]:
    preferred = ["image_url", "photo_url", "avatar_url", "thumbnail_url", "poster_url", "cover_url", "logo_url", "name", "title", "status", "price", "total", "quantity", "description", "created_at"]
    attrs = list(model_attrs.get(model) or [])
    media = [name for name in attrs if name and _field_kind(name) == "media"]
    selected = [name for name in preferred if name in attrs]
    for name in media:
        if name not in selected:
            selected.insert(0, name)
    selected.extend([name for name in attrs if name and name not in selected and name.lower() != "id"])
    return selected[:limit] or attrs[:limit]

def _finalize_data_section_bindings(sections: list, model_attrs: dict, limit: int = 8) -> list:
    data_layouts = {"card", "list", "table", "detail", "gallery", "filter", "form"}
    model_names = set(model_attrs.keys())
    model_names_fuzzy = {re.sub(r"[\s_-]", "", str(name or "")).lower(): name for name in model_names}

    def canonical_model(name: str) -> str:
        if name in model_attrs:
            return name
        return model_names_fuzzy.get(re.sub(r"[\s_-]", "", str(name or "")).lower(), "")

    fixed = []
    for section in sections:
        section = dict(section)
        section["layout"] = _normalize_layout_alias(section.get("layout"))
        layout = section.get("layout", "")
        component = str(section.get("component") or "")
        if component == "NavBar" and layout in {"", "nav", "navigation", "navbar"}:
            section["layout"] = "nav-links"
            layout = "nav-links"

        pm = canonical_model(str(section.get("primary_model") or section.get("class") or ""))
        if pm:
            section["primary_model"] = pm
            section["class"] = pm

        if pm and layout in data_layouts:
            valid_attrs = set(model_attrs.get(pm) or [])
            normalized_attrs = []
            for attr in section.get("attributes") or []:
                attr_name = attr.get("name", attr) if isinstance(attr, dict) else attr
                attr_name = str(attr_name or "")
                if not attr_name:
                    continue
                if "." in attr_name:
                    first, rest = attr_name.split(".", 1)
                    related_model = canonical_model(first)
                    if related_model and rest in set(model_attrs.get(related_model) or []):
                        normalized = dict(attr) if isinstance(attr, dict) else {"name": attr_name}
                        normalized["name"] = f"{related_model}.{rest}"
                        normalized.setdefault("source", "related")
                        normalized.setdefault("readonly", True)
                        normalized_attrs.append(normalized)
                    continue
                if attr_name in valid_attrs:
                    normalized_attrs.append(attr)
            if not normalized_attrs:
                normalized_attrs = _model_field_names(model_attrs, pm, limit)
            section["attributes"] = normalized_attrs
        section["component"] = _infer_section_component(section)
        section["field_layout"] = _normalize_field_layout(section)
        fixed.append(section)
    return fixed

def _snake_name(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(value or ""))
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

def _guess_relation_field(child_model: str, parent_model: str, model_attrs: dict) -> str:
    attrs = set(model_attrs.get(child_model) or [])
    parent_snake = _snake_name(parent_model)
    candidates = [
        f"{parent_snake}_id",
        f"{parent_snake}id",
        f"{parent_model}_id",
        f"{parent_model}Id",
        f"{parent_model.lower()}_id",
        f"{parent_model.lower()}id",
    ]
    for candidate in candidates:
        if candidate in attrs:
            return candidate
    return ""

def _related_models_from_attrs(section: dict, model_attrs: dict) -> list[str]:
    related: list[str] = []
    known = set(model_attrs.keys())
    known_fuzzy = {re.sub(r"[\s_-]", "", name).lower(): name for name in known}
    for attr in section.get("attributes") or []:
        name = attr.get("name", attr) if isinstance(attr, dict) else attr
        if "." not in str(name):
            continue
        prefix = str(name).split(".", 1)[0]
        model = prefix if prefix in known else known_fuzzy.get(re.sub(r"[\s_-]", "", prefix).lower(), "")
        if model and model not in related and model != section.get("primary_model"):
            related.append(model)
    return related

def _default_join_for_models(source_model: str, related_model: str) -> dict:
    related_snake = _snake_name(related_model)
    source_snake = _snake_name(source_model)
    return {
        "type": "left",
        "model": related_model,
        "on": f"{source_model}.{related_snake}_id = {related_model}.id"
        if related_snake
        else f"{source_model}.{source_snake}_id = {related_model}.id",
    }

def _section_is_data(section: dict) -> bool:
    layout = _normalize_layout_alias(section.get("layout"))
    role = str(section.get("role") or "")
    return bool(
        section.get("primary_model")
        and (
            layout in {"card", "list", "table", "detail", "gallery", "filter", "form", "calendar", "timeline", "map"}
            or role in DATA_SECTION_ROLES
            or section.get("attributes")
        )
    )

def _section_is_collection(section: dict) -> bool:
    layout = _normalize_layout_alias(section.get("layout"))
    role = str(section.get("role") or "")
    return layout in {"card", "list", "table", "gallery", "calendar", "timeline", "map"} or role in {"object_collection", "child_collection", "related_collection"}

def _ensure_section_data_relationships(
    pages: list,
    sections: list,
    model_attrs: dict,
) -> tuple[list, list]:
    """Populate SP data-source, related-object, and item-click metadata from OOUI page structure."""
    pages = [dict(p) for p in pages or []]
    sections = [dict(s) for s in sections or []]
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}

    detail_page_by_model: dict[str, str] = {}
    detail_section_by_page: dict[str, dict] = {}
    for page in pages:
        page_id = str(page.get("id") or "")
        page_model = str(page.get("primary_model") or "")
        refs = [_ref_id(ref) for ref in page.get("sections") or [] if _ref_id(ref)]
        data_sections = [section_map.get(ref) for ref in refs if section_map.get(ref)]
        candidates = [
            s for s in data_sections
            if s
            and str(s.get("primary_model") or "") == page_model
            and (
                str(s.get("role") or "") == "object_detail"
                or _normalize_layout_alias(s.get("layout")) in {"detail", "form"}
            )
        ]
        if not candidates:
            candidates = [
                s for s in data_sections
                if s
                and str(s.get("role") or "") == "object_detail"
                and str(s.get("primary_model") or "")
            ]
        if candidates:
            detail_section_by_page[page_id] = candidates[0]
            model = str(candidates[0].get("primary_model") or "")
            if model and model not in detail_page_by_model:
                detail_page_by_model[model] = page.get("name") or page_id

    for page in pages:
        page_id = str(page.get("id") or "")
        source_section = detail_section_by_page.get(page_id)
        source_id = str((source_section or {}).get("id") or "")
        source_model = str((source_section or {}).get("primary_model") or "")
        for ref in page.get("sections") or []:
            section = section_map.get(_ref_id(ref) or "")
            if not section or not _section_is_data(section):
                continue
            model = str(section.get("primary_model") or "")
            section.setdefault("class", model)

            data_source = dict(section.get("data_source") or {})
            data_source["mode"] = "query"
            data_source.setdefault("from", {"model": model})
            if not isinstance(data_source.get("from"), dict) or not data_source["from"].get("model"):
                data_source["from"] = {"model": model}
            joins = list(data_source.get("joins") or [])
            joined_models = {str(join.get("model") or "") for join in joins if isinstance(join, dict)}
            for related_model in _related_models_from_attrs(section, model_attrs):
                if related_model not in joined_models:
                    joins.append(_default_join_for_models(model, related_model))
                    joined_models.add(related_model)
            data_source["joins"] = joins
            section["data_source"] = data_source

            query = dict(section.get("query") or {})
            role = str(section.get("role") or "")
            if source_id and source_id != str(section.get("id") or "") and _section_is_collection(section):
                if not section.get("related_to"):
                    section["related_to"] = source_id
                relationship = dict(section.get("relationship") or {})
                if source_model and source_model == model:
                    relationship.setdefault("mode", "same_parent")
                    query.setdefault("exclude_source", True)
                else:
                    relationship.setdefault("mode", "direct")
                    relation_field = section.get("relation_field") or _guess_relation_field(model, source_model, model_attrs)
                    if relation_field:
                        section["relation_field"] = relation_field
                relationship.setdefault("source_model", source_model)
                relationship.setdefault("target_model", model)
                section["relationship"] = relationship
                if role in {"child_collection", "related_collection"}:
                    query.setdefault("limit", 4)
            section["query"] = query

            if _section_is_collection(section):
                target_page = detail_page_by_model.get(model)
                if target_page and target_page != page.get("name"):
                    behavior = dict(section.get("behavior") or {})
                    item_click = dict(behavior.get("item_click") or {})
                    if not item_click.get("type") or item_click.get("type") == "none":
                        item_click.update({"type": "navigate", "target_page": target_page})
                    elif item_click.get("type") == "navigate" and not item_click.get("target_page"):
                        item_click["target_page"] = target_page
                    behavior["item_click"] = item_click
                    section["behavior"] = behavior

    return pages, list(section_map.values())

def _infer_section_layout(page: dict, candidate_index: int = 0) -> str:
    tokens = _name_tokens(f"{page.get('name', '')} {page.get('id', '')}")
    if tokens & {"detail", "view", "profile", "summary"}:
        return "detail"
    if tokens & {"search", "select", "choose", "pick", "browse"}:
        return "card" if candidate_index % 2 == 0 else "list"
    if tokens & {"form", "enter", "submit", "create", "edit", "update", "provide"}:
        return "form"
    if tokens & {"list", "manage", "track", "history", "item", "line", "entry", "row"}:
        return "list"
    if tokens & {"browse", "catalog", "gallery", "showcase", "discover"}:
        return "gallery" if candidate_index % 2 == 0 else "card"
    return ("card", "table", "list")[candidate_index % 3]

def _fallback_model_for_page(page: dict, known_models: set[str]) -> str:
    if page.get("primary_model"):
        return str(page.get("primary_model"))
    page_name = f"{page.get('name', '')} {page.get('id', '')}".lower()
    for model in sorted(known_models):
        if model.lower() in page_name:
            return model
    non_process = [m for m in sorted(known_models) if m.lower() not in {"user", "group", "permission"}]
    return non_process[0] if non_process else ""


