"""UML mapping section materialization helpers."""

from .navigation_planner import DATA_SECTION_ROLES
from ..section_utils import (
    _CHROME_TEMPLATE_LAYOUTS,
    _HEADER_NAV_LAYOUTS,
    _HEADER_SHELL_LAYOUTS,
    _HEADER_TEMPLATE_LAYOUTS,
    _fallback_model_for_page,
    _infer_section_component,
    _infer_section_layout,
    _model_field_names,
    _normalize_layout_alias,
    _normalize_section_operations,
    _page_type_value,
    _ref_id,
    _ensure_section_data_relationships,
    _navigation_methods,
    _workflow_icon_links,
)
from ..token_normalizer import _page_name, _section_id
from ..candidate_defaults import (
    _default_section_for_page,
    _ensure_normal_page_navigation,
    _footer_sections_for_candidate,
    _header_sections_for_candidate,
)
from .usecase_workflow import _is_child_collection_model


def _ensure_mapping_chrome_sections(pages: list, sections: list) -> tuple[list, list]:
    """Add stable app chrome during UML mapping so candidates can focus on visual variants."""
    pages = [dict(p) for p in pages or []]
    sections = [dict(s) for s in sections or []]
    normal_pages = [p for p in pages if _page_type_value(p) != "activity"]
    if not normal_pages:
        return pages, sections

    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    if not any(s.get("position") == "header" for s in sections):
        _inject_chrome_sections(
            _header_sections_for_candidate(normal_pages, 0),
            sections,
            section_map,
            normal_pages,
            prepend=True,
        )

    if not any(s.get("position") == "footer" for s in sections):
        _inject_chrome_sections(
            _footer_sections_for_candidate(0, normal_pages),
            sections,
            section_map,
            normal_pages,
            prepend=False,
        )

    pages, sections = _ensure_normal_page_navigation(pages, sections, normal_pages, 0)
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    global_region_ids = [
        str(s.get("id"))
        for s in sections
        if s.get("id") and s.get("position") in {"header", "sidebar", "footer"}
    ]

    for page in normal_pages:
        refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
        ref_ids = {_ref_id(ref) for ref in refs}
        before = [
            {"value": sid}
            for sid in global_region_ids
            if sid not in ref_ids and (section_map.get(sid) or {}).get("position") in {"header", "sidebar"}
        ]
        after = [
            {"value": sid}
            for sid in global_region_ids
            if sid not in ref_ids and (section_map.get(sid) or {}).get("position") == "footer"
        ]
        if before or after:
            page["sections"] = before + refs + after

    return pages, sections

def _ensure_mapping_content_sections(
    pages: list,
    sections: list,
    usecase_navigation: dict,
    model_attrs: dict,
) -> tuple[list, list]:
    """Materialize OOUI/data support sections once during UML mapping, not during candidate generation."""
    pages, sections = _materialize_nav_plan_sections(
        pages,
        sections,
        (usecase_navigation or {}).get("nav_plan") or {},
        model_attrs,
    )
    pages, sections = _ensure_workflow_entry_sections(pages, sections, usecase_navigation or {})
    pages, sections = _ensure_candidate_content_structure(
        pages,
        sections,
        model_attrs,
        0,
        "",
        add_missing_content=True,
    )
    pages, sections = _ensure_pre_workflow_content_sections(
        pages,
        sections,
        usecase_navigation or {},
        model_attrs,
        0,
        add_missing_content=True,
    )
    sections = _apply_nav_methods(pages, sections, usecase_navigation or {})
    pages, sections = _ensure_section_data_relationships(pages, sections, model_attrs)
    return pages, sections

def _drop_unreferenced_non_global_sections(pages: list, sections: list) -> list:
    referenced = {
        _ref_id(ref)
        for page in pages or []
        for ref in (page.get("sections") or [])
        if _ref_id(ref)
    }
    result = []
    for section in sections or []:
        sid = str(section.get("id") or "")
        if not sid or sid in referenced:
            result.append(section)
            continue
        if section.get("position") in {"header", "footer", "sidebar"}:
            result.append(section)
            continue
        layout = _normalize_layout_alias(section.get("layout"))
        if layout in _CHROME_TEMPLATE_LAYOUTS:
            result.append(section)
    return result

def _dedupe_agent_header_shells(pages: list, sections: list) -> tuple[list, list]:
    """Agent output may compose many header elements, but only one header/nav shell."""
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    header_shell_ids = [
        sid for sid, section in section_map.items()
        if section.get("position") == "header"
        and _normalize_layout_alias(section.get("layout")) in _HEADER_SHELL_LAYOUTS
    ]
    if len(header_shell_ids) <= 1:
        return pages, sections
    duplicate_ids = set(header_shell_ids[1:])
    next_sections = [section for section in sections if str(section.get("id")) not in duplicate_ids]
    next_pages = []
    for page in pages:
        page = dict(page)
        page["sections"] = [
            ref for ref in (page.get("sections") or [])
            if _ref_id(ref) and _ref_id(ref) not in duplicate_ids
        ]
        next_pages.append(page)
    return next_pages, next_sections

def _inject_chrome_sections(new_sections: list, sections: list, section_map: dict, pages: list, prepend: bool) -> None:
    for s in new_sections:
        sid = s["id"]; suffix = 2
        while sid in section_map:
            sid = f"{s['id']}_{suffix}"; suffix += 1
        s["id"] = sid
        sections.append(s); section_map[sid] = s
    for page in pages:
        refs = page.get("sections") or []
        ref_ids = {_ref_id(ref) for ref in refs}
        new_refs = [{"value": s["id"]} for s in new_sections if s["id"] not in ref_ids]
        if new_refs:
            page["sections"] = new_refs + refs if prepend else refs + new_refs


def _ensure_candidate_content_structure(
    pages: list,
    sections: list,
    model_attrs: dict,
    candidate_index: int = 0,
    prompt: str = "",
    add_missing_content: bool = True,
) -> tuple[list, list]:
    known_models = set(model_attrs.keys())
    sections = [dict(s) for s in sections]
    for section in sections:
        section["layout"] = _normalize_layout_alias(section.get("layout"))
        if section.get("component") == "NavBar" and not section.get("layout"):
            section["layout"] = "nav-links"
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    activity_section_ids = {sid for sid, s in section_map.items() if s.get("type") == "activity_action" or s.get("layout") == "activity_action"}
    chrome_layouts = _CHROME_TEMPLATE_LAYOUTS | {"activity_start", "activity_tasks"}

    _, sections = _dedupe_agent_header_shells([], sections)
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    keep_header_shell_id = next(
        (
            sid for sid, section in section_map.items()
            if section.get("position") == "header"
            and _normalize_layout_alias(section.get("layout")) in _HEADER_SHELL_LAYOUTS
        ),
        "",
    )

    fixed_pages = []
    normal_pages = []
    activity_pages = []
    normal_pages_by_key = {}
    for page in pages:
        page = dict(page)
        refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
        if keep_header_shell_id:
            seen_header_shell = False
            deduped_refs = []
            for ref in refs:
                section = section_map.get(ref["value"]) or {}
                is_header_shell_ref = (
                    section.get("position") == "header"
                    and _normalize_layout_alias(section.get("layout")) in _HEADER_SHELL_LAYOUTS
                )
                if is_header_shell_ref:
                    if seen_header_shell:
                        continue
                    seen_header_shell = True
                deduped_refs.append(ref)
            refs = deduped_refs
        if _page_type_value(page) != "activity":
            refs = [ref for ref in refs if ref["value"] not in activity_section_ids]
            page["sections"] = refs
            page_key = _section_id(page.get("name") or page.get("id") or page.get("display_name"))
            if page_key and page_key in normal_pages_by_key:
                existing = normal_pages_by_key[page_key]
                existing_refs = [{"value": _ref_id(ref)} for ref in existing.get("sections") or [] if _ref_id(ref)]
                existing_ids = {_ref_id(ref) for ref in existing_refs}
                existing["sections"] = existing_refs + [ref for ref in refs if ref["value"] not in existing_ids]
                continue
            normal_pages_by_key[page_key] = page
            normal_pages.append(page)
        else:
            page["sections"] = refs
            activity_pages.append(page)

    normal_page_ids = {_section_id(p.get("id") or p.get("name")) for p in normal_pages}
    has_header_region = any(s.get("id") and s.get("position") == "header" for s in sections)
    if normal_pages and not has_header_region:
        _inject_chrome_sections(_header_sections_for_candidate(normal_pages, candidate_index, model_attrs), sections, section_map, normal_pages, prepend=True)

    has_footer_region = any(s.get("id") and s.get("position") == "footer" for s in sections)
    if normal_pages and not has_footer_region:
        _inject_chrome_sections(_footer_sections_for_candidate(candidate_index, normal_pages), sections, section_map, normal_pages, prepend=False)

    _all_pages_for_nav = normal_pages + activity_pages
    _all_pages_for_nav, sections = _ensure_normal_page_navigation(_all_pages_for_nav, sections, normal_pages, candidate_index)
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}

    def _is_global_region_section(section: dict) -> bool:
        position = section.get("position")
        if position not in {"header", "sidebar", "footer"} or not section.get("id"):
            return False
        layout = section.get("layout")
        style = section.get("style") or {}
        role = str(section.get("role") or "").lower()
        scope = str(section.get("scope") or style.get("scope") or "").lower()
        if scope == "global":
            return True
        if layout in chrome_layouts:
            return True
        if not section.get("primary_model"):
            return True
        return role in {
            "brand", "navigation", "search", "actions", "action", "promo", "utility",
            "status", "summary", "kpi", "stats", "legal", "contact", "help", "footer",
        }

    header_region_ids = [
        str(s.get("id")) for s in sections
        if _is_global_region_section(s) and s.get("position") == "header"
    ]
    sidebar_region_ids = [
        str(s.get("id")) for s in sections
        if _is_global_region_section(s) and s.get("position") == "sidebar"
    ]
    footer_region_ids = [
        str(s.get("id")) for s in sections
        if _is_global_region_section(s) and s.get("position") == "footer"
    ]
    if header_region_ids or sidebar_region_ids or footer_region_ids:
        for page in normal_pages:
            refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
            ref_ids = {_ref_id(ref) for ref in refs}
            header_refs = [{"value": sid} for sid in header_region_ids if sid not in ref_ids]
            sidebar_refs = [{"value": sid} for sid in sidebar_region_ids if sid not in ref_ids]
            footer_refs = [{"value": sid} for sid in footer_region_ids if sid not in ref_ids]
            if header_refs or sidebar_refs or footer_refs:
                page["sections"] = header_refs + sidebar_refs + refs + footer_refs

    referenced_region_ids = {
        _ref_id(ref)
        for page in normal_pages
        for ref in (page.get("sections") or [])
        if _ref_id(ref)
    }

    def _best_page_for_region_section(section: dict) -> dict | None:
        if not normal_pages:
            return None
        pm = str(section.get("primary_model") or "")
        if pm:
            pm_key = _section_id(pm)
            for page in normal_pages:
                page_pm = str(page.get("primary_model") or "")
                page_text = f"{page.get('id', '')} {page.get('name', '')}"
                if page_pm == pm or pm_key in _section_id(page_text):
                    return page
        return normal_pages[0]

    for section in sections:
        sid = str(section.get("id") or "")
        position = section.get("position")
        if not sid or sid in referenced_region_ids or position not in {"header", "sidebar", "footer"}:
            continue
        page = _best_page_for_region_section(section)
        if not page:
            continue
        refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
        if position == "footer":
            page["sections"] = refs + [{"value": sid}]
        else:
            page["sections"] = [{"value": sid}] + refs
        referenced_region_ids.add(sid)

    for page in normal_pages:
        model = _fallback_model_for_page(page, known_models)
        if model and not page.get("primary_model"):
            page["primary_model"] = model
        ref_ids = {_ref_id(ref) for ref in page.get("sections") or []}
        has_content = False
        for sid in ref_ids:
            section = section_map.get(sid) or {}
            if section.get("position", "main") == "main" and section.get("layout") not in chrome_layouts and section.get("layout") != "activity_action":
                has_content = True
                if model and not section.get("primary_model"):
                    section["primary_model"] = model
                    section["class"] = model
                if section.get("primary_model") in model_attrs and not section.get("attributes"):
                    section["attributes"] = _model_field_names(model_attrs, section["primary_model"])
                section.setdefault("operations", {"create": False, "update": False, "delete": False})
        if add_missing_content and not has_content and model:
            section = _default_section_for_page(page, model, model_attrs, candidate_index)
            dedupe_id = section["id"]
            suffix = 2
            while dedupe_id in section_map:
                dedupe_id = f"{section['id']}_{suffix}"
                suffix += 1
            section["id"] = dedupe_id
            sections.append(section)
            section_map[dedupe_id] = section
            page.setdefault("sections", [])
            page["sections"].append({"value": dedupe_id})
    fixed_pages = normal_pages + activity_pages
    return fixed_pages, sections

def _ensure_usecase_pages(pages: list, usecase_navigation: dict) -> list:
    if not usecase_navigation:
        return pages
    pages = [dict(p) for p in pages]
    existing = {_section_id(p.get("id") or p.get("name")) for p in pages}
    page_entries = usecase_navigation.get("pages") or []
    if not page_entries:
        page_entries = [
            {
                "page_id": usecase.get("page_id"),
                "page_name": usecase.get("page_name"),
                "primary_model": usecase.get("page_model") or usecase.get("primary_model", ""),
                "usecases": [usecase.get("name")],
            }
            for usecase in usecase_navigation.get("usecases") or []
            if (usecase.get("ui_mapping") or {}).get("role") != "background"
        ]
    for page_entry in page_entries:
        page_id = _section_id(page_entry.get("page_id") or page_entry.get("page_name"))
        if not page_id or page_id in existing:
            continue
        pages.append({
            "id": page_id,
            "name": page_entry.get("page_name") or _page_name(page_id),
            "primary_model": page_entry.get("primary_model", ""),
            "type": {"value": "normal", "label": "Normal"},
            "sections": [],
            "category": None,
            "source_usecases": page_entry.get("usecases") or [],
        })
        existing.add(page_id)
    return pages

def _ensure_workflow_entry_sections(pages: list, sections: list, usecase_navigation: dict) -> tuple[list, list]:
    entries = usecase_navigation.get("workflow_entry_points") or []
    if not entries:
        return pages, sections
    pages = [dict(p) for p in pages]
    sections = [dict(s) for s in sections]
    section_ids = {str(s.get("id")) for s in sections if s.get("id")}
    page_by_id = {_section_id(p.get("id") or p.get("name")): p for p in pages}
    for entry in entries:
        page = page_by_id.get(_section_id(entry.get("page_id") or entry.get("page_name")))
        if not page:
            continue
        sid = f"{_section_id(page.get('id') or page.get('name'))}_workflow_start"
        if sid not in section_ids:
            sections.append({
                "id": sid,
                "name": entry.get("label") or "Start Workflow",
                "label": entry.get("label") or "Start Workflow",
                "type": "activity_start",
                "layout": "activity_start",
                "primary_model": "",
                "class": "",
                "operations": {"create": False, "update": False, "delete": False},
                "attributes": [],
                "methods": [],
                "col_span": 12,
                "position": "main",
                "style": {"color": "accent", "density": "normal", "shadow": "sm", "bg": "white", "columns": "1", "cta_label": entry.get("button_label") or "Start"},
            })
            section_ids.add(sid)
        refs = page.get("sections") or []
        if sid not in {_ref_id(ref) for ref in refs}:
            page["sections"] = refs + [{"value": sid}]
    return pages, sections

def _ensure_pre_workflow_content_sections(
    pages: list,
    sections: list,
    usecase_navigation: dict,
    model_attrs: dict,
    candidate_index: int = 0,
    add_missing_content: bool = True,
) -> tuple[list, list]:
    if not add_missing_content:
        return pages, sections
    entries = usecase_navigation.get("workflow_entry_points") or []
    if not entries:
        return pages, sections
    pages = [dict(p) for p in pages]
    sections = [dict(s) for s in sections]
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    page_by_id = {_section_id(p.get("id") or p.get("name")): p for p in pages}
    known_models = set(model_attrs.keys())

    for entry in entries:
        page_id = _section_id(entry.get("page_id") or entry.get("page_name"))
        page = page_by_id.get(page_id)
        if not page:
            continue
        refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
        ref_ids = {_ref_id(ref) for ref in refs}
        main_data_sections = [
            section_map.get(sid) or {}
            for sid in ref_ids
            if (section_map.get(sid) or {}).get("position", "main") == "main"
            and (section_map.get(sid) or {}).get("layout") in {"card", "list", "table", "detail", "gallery", "form"}
        ]
        preferred_models = [
            m for m in (entry.get("pre_workflow_collections") or [])
            if m in known_models
        ]
        if not preferred_models:
            preferred_models = [
                m for m in (entry.get("related_models") or [])
                if m in known_models and _is_child_collection_model(m, f"{entry.get('page_name', '')} {entry.get('usecase_name', '')}")
            ]
        if not preferred_models:
            preferred_models = [m for m in [entry.get("primary_model")] if m in known_models]
        model = preferred_models[0] if preferred_models else ""
        if not model:
            continue
        has_model_section = any(s.get("primary_model") == model for s in main_data_sections)
        if has_model_section:
            continue
        sid = f"{page_id}_{_section_id(model)}_pre_workflow"
        suffix = 2
        base_sid = sid
        while sid in section_map:
            sid = f"{base_sid}_{suffix}"
            suffix += 1
        page_text = f"{page_id} {page.get('name', '')} {entry.get('usecase_name', '')}".lower()
        is_select_existing = any(term in page_text for term in ("search", "select", "choose", "pick", "browse"))
        layout = "list" if _is_child_collection_model(model, f"{entry.get('page_name', '')} {entry.get('usecase_name', '')}") else _infer_section_layout({"id": page_id, "name": page.get("name", "")}, candidate_index)
        style = {
            "color": "accent",
            "density": "compact" if layout in {"list", "table"} else "normal",
            "shadow": "sm",
            "border": "light",
            "bg": "white",
        }
        if layout == "list":
            style["list_style"] = "default"
        section = {
            "id": sid,
            "name": f"{model} Items" if _is_child_collection_model(model, page_id) else f"{model} Overview",
            "layout": layout,
            "primary_model": model,
            "class": model,
            "attributes": _model_field_names(model_attrs, model, 8),
            "operations": {
                "create": False,
                "update": layout in {"list", "table", "detail", "form"} and not is_select_existing,
                "delete": layout in {"list", "table", "card", "gallery"} and not is_select_existing,
                "select": is_select_existing,
            },
            "query": {},
            "col_span": 12,
            "position": "main",
            "style": style,
        }
        sections.append(section)
        section_map[sid] = section
        activity_start_refs = [ref for ref in refs if (section_map.get(_ref_id(ref)) or {}).get("layout") == "activity_start"]
        other_refs = [ref for ref in refs if ref not in activity_start_refs]
        page["sections"] = other_refs + [{"value": sid}] + activity_start_refs
    return pages, sections

def _apply_nav_methods(pages: list, sections: list, usecase_navigation: dict) -> list:
    nav_ids = {_section_id(pid) for pid in (usecase_navigation.get("nav_bar_pages") or []) if pid}
    page_by_id = {_section_id(p.get("id") or p.get("name")): p for p in pages}
    nav_names = [
        (page_by_id.get(pid) or {}).get("name") or _page_name(pid)
        for pid in usecase_navigation.get("nav_bar_pages") or []
        if _section_id(pid) in page_by_id
    ]
    workflow_icon_links = _workflow_icon_links(usecase_navigation, page_by_id)
    if not nav_names and not workflow_icon_links:
        return sections
    fixed = []
    for section in sections:
        section = dict(section)
        layout = _normalize_layout_alias(section.get("layout"))
        if nav_ids and (layout in (_HEADER_NAV_LAYOUTS | {"nav-bar"}) or (section.get("position") in {"header", "sidebar"} and layout in {"site-nav", "nav-links", "nav-bar"})):
            section["layout"] = layout
            section["methods"] = _navigation_methods(nav_names)
        if section.get("position") == "header" or layout in _HEADER_TEMPLATE_LAYOUTS or layout == "icon-actions":
            style = dict(section.get("style") or {})
            if workflow_icon_links and not style.get("icon_links"):
                style["icon_links"] = workflow_icon_links[:2]
            section["style"] = style
        fixed.append(section)
    return fixed

def _materialize_nav_plan_sections(pages: list, sections: list, nav_plan: dict, model_attrs: dict) -> tuple[list, list]:
    if not nav_plan:
        return pages, sections
    pages = [dict(p) for p in pages]
    sections = [dict(s) for s in sections]
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    page_by_id = {_section_id(p.get("id") or p.get("name")): p for p in pages}

    for section_plan in nav_plan.get("sections") or []:
        if section_plan.get("role") not in DATA_SECTION_ROLES:
            continue
        sid = section_plan.get("id")
        page_id = _section_id(section_plan.get("page_id"))
        model = section_plan.get("primary_model") or ""
        if not sid or not page_id or not model or sid in section_map:
            continue
        if model not in model_attrs:
            continue
        editable = set(section_plan.get("editable_fields") or [])
        operations = _normalize_section_operations(section_plan.get("operations"))
        operations["update"] = bool(operations.get("update") or editable)
        attrs = list(section_plan.get("visible_fields") or [])
        attrs.extend([
            {"name": name, "source": "related", "readonly": True}
            for name in section_plan.get("related_visible_fields") or []
        ])
        if not attrs:
            attrs = _model_field_names(model_attrs, model, 8)
        section = {
            "id": sid,
            "name": section_plan.get("name") or sid,
            "role": section_plan.get("role"),
            "layout": section_plan.get("layout") or "detail",
            "component": section_plan.get("component") or _infer_section_component(section_plan),
            "primary_model": model,
            "class": model,
            "attributes": attrs,
            "field_layout": section_plan.get("field_layout") or {},
            "behavior": section_plan.get("behavior") or {},
            "related_to": section_plan.get("related_to"),
            "relationship": section_plan.get("relationship") or {},
            "relation_field": section_plan.get("relation_field"),
            "operations": operations,
            "data_source": section_plan.get("data_source") or {},
            "query": section_plan.get("query") or {},
            "col_span": section_plan.get("col_span", 12),
            "position": "main",
            "style": section_plan.get("style") or {"color": "accent", "density": "normal", "shadow": "sm", "bg": "white"},
        }
        sections.append(section)
        section_map[sid] = section
        page = page_by_id.get(page_id)
        if page:
            refs = page.get("sections") or []
            if sid not in {_ref_id(ref) for ref in refs}:
                page["sections"] = refs + [{"value": sid}]
    return pages, sections



