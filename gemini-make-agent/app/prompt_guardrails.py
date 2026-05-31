"""Legacy prompt-intent parser and hard constraints for root-agent patches."""

import copy
import re

from .prompt_intent import page_layout_dict as _page_layout_dict
from .prompt_intent import prompt_layout_traits as _prompt_layout_traits
from .styling_engine import (
    _prompt_color_scope_lock,
    _prompt_scoped_color_overrides,
    _prompt_typography_overrides,
)
from .tools import (
    _attr_name,
    _attr_type,
    _component_for_layout,
    _field_kind,
    _normalize_layout_alias,
    _normalize_section_operations,
)


def compile_prompt_intent(prompt: str = "") -> dict:
    text = str(prompt or "").lower()
    original_prompt = str(prompt or "")
    has_image_word = any(term in text for term in ("image", "picture", "photo", "media", "banner")) or any(
        term in original_prompt for term in ("\u56fe\u7247", "\u56fe\u50cf", "\u7167\u7247", "\u6d77\u62a5")
    )
    has_header_word = any(term in text for term in ("header", "top bar", "banner")) or any(
        term in original_prompt for term in ("\u9875\u5934", "\u5934\u90e8", "\u9876\u90e8", "\u6a2a\u5e45")
    )
    header_media = has_image_word and has_header_word
    color_overrides = _prompt_scoped_color_overrides(prompt)
    typography_overrides = _prompt_typography_overrides(prompt)
    color_scope_lock = _prompt_color_scope_lock(prompt)
    layout_intent = _prompt_layout_traits(prompt)
    component_intent: dict[str, str] = {}
    data_intent = {
        "hide_id_fields": any(term in text for term in (
            "hide id", "hide ids", "hide internal", "no id fields", "without ids", "ÃƒÂ¤Ã‚Â¸Ã‚ÂÃƒÂ¨Ã‚Â¦Ã‚Âid", "ÃƒÂ©Ã…Â¡Ã‚ÂÃƒÂ¨Ã¢â‚¬â€Ã‚Âid", "ÃƒÂ©Ã…Â¡Ã‚Â±ÃƒÂ¨Ã¢â‚¬â€Ã‚Âid",
        )),
        "table_targets": [],
        "single_card_media": header_media or any(term in text for term in (
            "single card", "one card", "single image card", "image only", "only image", "media only",
            "limit 1 card", "limit one card",
        )) or (
            ("card" in text or "ÃƒÂ¥Ã‚ÂÃ‚Â¡ÃƒÂ§Ã¢â‚¬Â°Ã¢â‚¬Â¡" in str(prompt or ""))
            and ("image" in text or "media" in text or "ÃƒÂ¥Ã¢â‚¬ÂºÃ‚Â¾ÃƒÂ§Ã¢â‚¬Â°Ã¢â‚¬Â¡" in str(prompt or "") or "ÃƒÂ§Ã¢â‚¬Â¦Ã‚Â§ÃƒÂ§Ã¢â‚¬Â°Ã¢â‚¬Â¡" in str(prompt or ""))
            and ("single" in text or "one" in text or "only" in text or "ÃƒÂ¥Ã‚ÂÃ¢â‚¬Â¢ÃƒÂ¤Ã‚Â¸Ã‚Âª" in str(prompt or "") or "ÃƒÂ¤Ã‚Â¸Ã¢â€šÂ¬ÃƒÂ¥Ã‚Â¼Ã‚Â " in str(prompt or "") or "ÃƒÂ¥Ã‚ÂÃ‚Âª" in str(prompt or ""))
        ),
        "media_position": "header" if header_media else "",
    }
    data_intent["query_hints"] = {}
    interaction_intent = {
        "delete": "default",
        "multi_delete": False,
        "navigation_required": any(term in text for term in ("navigate", "navigation", "link to", "go to", "ÃƒÂ¨Ã‚Â·Ã‚Â³ÃƒÂ¨Ã‚Â½Ã‚Â¬", "ÃƒÂ¥Ã‚Â¯Ã‚Â¼ÃƒÂ¨Ã‹â€ Ã‚Âª")),
    }

    data_layouts = ("table", "card", "cards", "gallery", "list", "form", "detail")
    target_patterns = (
        r"\b(?P<target>[a-zA-Z][\w\s-]{1,40}?)\s+(?:as|in|with|use|using|into|to)\s+(?P<layout>table|cards?|gallery|list|form|detail)\b",
        r"\b(?P<layout>table|cards?|gallery|list|form|detail)\s+(?:for|on|of)\s+(?P<target>[a-zA-Z][\w\s-]{1,40}?)\b",
    )
    for pattern in target_patterns:
        for match in re.finditer(pattern, text):
            target = re.sub(r"\s+", " ", match.group("target")).strip(" .,:;")
            layout = match.group("layout")
            if layout == "cards":
                layout = "card"
            if target and layout in data_layouts:
                component_intent[target] = layout
                if layout == "table":
                    data_intent["table_targets"].append(target)

    if any(term in text for term in ("all sections table", "everything table", "all data as table", "ÃƒÂ¦Ã¢â‚¬Â°Ã¢â€šÂ¬ÃƒÂ¦Ã…â€œÃ¢â‚¬Â°ÃƒÂ¨Ã‚Â¡Ã‚Â¨ÃƒÂ¦Ã‚Â Ã‚Â¼")):
        component_intent["*"] = "table"
    elif any(term in text for term in ("all cards", "everything card", "all data as cards", "ÃƒÂ¦Ã¢â‚¬Â°Ã¢â€šÂ¬ÃƒÂ¦Ã…â€œÃ¢â‚¬Â°ÃƒÂ¥Ã‚ÂÃ‚Â¡ÃƒÂ§Ã¢â‚¬Â°Ã¢â‚¬Â¡")):
        component_intent["*"] = "card"

    if any(term in text for term in ("no delete", "disable delete", "hide delete", "without delete", "ÃƒÂ¤Ã‚Â¸Ã‚ÂÃƒÂ¨Ã‚Â¦Ã‚ÂÃƒÂ¥Ã‹â€ Ã‚Â ÃƒÂ©Ã¢â€žÂ¢Ã‚Â¤", "ÃƒÂ§Ã‚Â¦Ã‚ÂÃƒÂ§Ã¢â‚¬ÂÃ‚Â¨ÃƒÂ¥Ã‹â€ Ã‚Â ÃƒÂ©Ã¢â€žÂ¢Ã‚Â¤")):
        interaction_intent["delete"] = "disabled"
    elif any(term in text for term in ("enable delete", "allow delete", "show delete", "ÃƒÂ¥Ã‚ÂÃ‚Â¯ÃƒÂ¤Ã‚Â»Ã‚Â¥ÃƒÂ¥Ã‹â€ Ã‚Â ÃƒÂ©Ã¢â€žÂ¢Ã‚Â¤")):
        interaction_intent["delete"] = "enabled"
    if any(term in text for term in ("multi delete", "bulk delete", "delete selected", "batch delete", "ÃƒÂ¥Ã‚Â¤Ã…Â¡ÃƒÂ©Ã¢â€šÂ¬Ã¢â‚¬Â°ÃƒÂ¥Ã‹â€ Ã‚Â ÃƒÂ©Ã¢â€žÂ¢Ã‚Â¤", "ÃƒÂ¦Ã¢â‚¬Â°Ã‚Â¹ÃƒÂ©Ã¢â‚¬Â¡Ã‚ÂÃƒÂ¥Ã‹â€ Ã‚Â ÃƒÂ©Ã¢â€žÂ¢Ã‚Â¤")):
        interaction_intent["multi_delete"] = True
        interaction_intent["delete"] = "enabled"

    if any(term in text for term in ("sidebar left", "left sidebar", "left nav", "ÃƒÂ¥Ã‚Â·Ã‚Â¦ÃƒÂ¤Ã‚Â¾Ã‚Â§ÃƒÂ¦Ã‚Â Ã‚Â", "ÃƒÂ¥Ã‚Â·Ã‚Â¦ÃƒÂ¤Ã‚Â¾Ã‚Â§ÃƒÂ¥Ã‚Â¯Ã‚Â¼ÃƒÂ¨Ã‹â€ Ã‚Âª")):
        layout_intent["sidebar"] = True
        layout_intent["sidebar_side"] = "left"
    elif any(term in text for term in ("sidebar right", "right sidebar", "right nav", "ÃƒÂ¥Ã‚ÂÃ‚Â³ÃƒÂ¤Ã‚Â¾Ã‚Â§ÃƒÂ¦Ã‚Â Ã‚Â", "ÃƒÂ¥Ã‚ÂÃ‚Â³ÃƒÂ¤Ã‚Â¾Ã‚Â§ÃƒÂ¥Ã‚Â¯Ã‚Â¼ÃƒÂ¨Ã‹â€ Ã‚Âª")):
        layout_intent["sidebar"] = True
        layout_intent["sidebar_side"] = "right"
    if any(term in text for term in ("main full", "full main", "main full width", "full-width main", "ÃƒÂ¤Ã‚Â¸Ã‚Â»ÃƒÂ¥Ã…â€™Ã‚ÂºÃƒÂ¥Ã…Â¸Ã…Â¸ÃƒÂ¥Ã¢â‚¬Â¦Ã‚Â¨ÃƒÂ¥Ã‚Â®Ã‚Â½")):
        layout_intent["full"] = True
        layout_intent["main_width"] = "full"
    if any(term in text for term in ("header full", "full header", "ÃƒÂ©Ã‚Â¡Ã‚ÂµÃƒÂ©Ã‚Â¦Ã¢â‚¬â€œÃƒÂ¥Ã¢â‚¬Â¦Ã‚Â¨ÃƒÂ¥Ã‚Â®Ã‚Â½")):
        layout_intent["header_width"] = "full"
    if any(term in text for term in ("footer full", "full footer", "ÃƒÂ©Ã‚Â¡Ã‚ÂµÃƒÂ¨Ã¢â‚¬Å¾Ã…Â¡ÃƒÂ¥Ã¢â‚¬Â¦Ã‚Â¨ÃƒÂ¥Ã‚Â®Ã‚Â½")):
        layout_intent["footer_width"] = "full"

    query_hints = data_intent["query_hints"]
    if any(term in text for term in ("latest", "newest", "recent", "most recent", "last item")):
        query_hints["order"] = "latest"
    elif any(term in text for term in ("oldest", "first item", "earliest")):
        query_hints["order"] = "oldest"
    if any(term in text for term in ("active only", "only active", "enabled only")):
        query_hints.setdefault("filters", []).append({"kind": "active", "value": "true"})
    for status_value in ("approved", "pending", "rejected", "accepted", "completed", "open", "closed"):
        if re.search(rf"\b(?:only\s+)?{status_value}\b", text):
            query_hints.setdefault("filters", []).append({"kind": "status", "value": status_value})
    for match in re.finditer(r"\b(?P<field>[a-zA-Z_][\w]*)\s*(?:=|equals|is)\s*['\"]?(?P<value>[a-zA-Z0-9_. -]{1,40})['\"]?", text):
        field = match.group("field").strip()
        value = match.group("value").strip(" .,'\"")
        if field and value and field not in {"button", "color", "style", "layout", "card", "image"}:
            query_hints.setdefault("filters", []).append({"kind": "field", "field": field, "value": value})

    return {
        "version": 1,
        "source": prompt or "",
        "colorIntent": color_overrides,
        "typographyIntent": typography_overrides,
        "colorPolicy": {
            "scope_lock": color_scope_lock,
            "preserve_other_colors": bool(color_scope_lock),
        },
        "layoutIntent": layout_intent,
        "componentIntent": component_intent,
        "dataIntent": data_intent,
        "interactionIntent": interaction_intent,
    }

def _intent_target_matches(section: dict, target: str) -> bool:
    if target == "*":
        return bool(section.get("primary_model")) or section.get("layout") in {"card", "list", "table", "detail", "gallery", "form"}
    haystack = " ".join(str(section.get(key, "")) for key in ("id", "name", "primary_model", "class", "role", "layout")).lower()
    needle = re.sub(r"[\s_-]+", "", str(target or "").lower())
    compact_haystack = re.sub(r"[\s_-]+", "", haystack)
    return bool(needle and (needle in compact_haystack or str(target).lower() in haystack))

def apply_hard_constraints(pages: list, sections: list, tokens: dict, styling: dict, prompt_intent: dict) -> tuple[list, list, dict, dict]:
    pages = copy.deepcopy(pages or [])
    sections = copy.deepcopy(sections or [])
    tokens = dict(tokens or {})
    styling = dict(styling or {})
    intent = prompt_intent or {}

    # LLM-generated schema is the source of truth for color tokens.
    # The old regex prompt parser is intentionally not applied here because it
    # misreads multi-target requests such as "header blue searchbar green button pink".
    # color_intent = intent.get("colorIntent") or {}
    # if color_intent:
    #     tokens.update(color_intent)

    layout_intent = intent.get("layoutIntent") or {}
    if layout_intent:
        for page in pages:
            layout = _page_layout_dict(page)
            if layout_intent.get("main_width"):
                layout["main_width"] = layout_intent["main_width"]
            elif layout_intent.get("full"):
                layout["main_width"] = "full"
            if layout_intent.get("header_width"):
                layout["header_width"] = layout_intent["header_width"]
            if layout_intent.get("footer_width"):
                layout["footer_width"] = layout_intent["footer_width"]
            if layout_intent.get("hero_width"):
                layout["hero_width"] = layout_intent["hero_width"]
            page["layout"] = layout
        if layout_intent.get("sidebar") and layout_intent.get("sidebar_side"):
            side = layout_intent.get("sidebar_side") or "left"
            nav_sections = [s for s in sections if _normalize_layout_alias(s.get("layout")) in {"site-nav", "nav-links", "nav-bar"} or s.get("component") == "NavBar"]
            for nav in nav_sections[:1]:
                nav["position"] = "sidebar"
                nav["layout"] = "site-nav"
                nav["component"] = "NavBar"
                style = dict(nav.get("style") or {})
                style["sidebar_side"] = side
                style.setdefault("sidebar_width", 3)
                nav["style"] = style

    component_intent = intent.get("componentIntent") or {}
    if component_intent:
        for section in sections:
            for target, layout in component_intent.items():
                if _intent_target_matches(section, target):
                    section["layout"] = layout
                    section["component"] = _component_for_layout(section, layout)
                    if layout == "table":
                        section["col_span"] = 12
                    style = dict(section.get("style") or {})
                    if layout in {"gallery", "card"}:
                        style.setdefault("columns", "3" if layout == "gallery" else "2")
                    section["style"] = style

    data_intent = intent.get("dataIntent") or {}
    hide_ids = data_intent.get("hide_id_fields")
    if data_intent.get("single_card_media"):
        converted_media_card = False
        for section in sections:
            if converted_media_card or not section.get("primary_model"):
                continue
            attrs = section.get("attributes") or []
            media_attr = next(
                (
                    _attr_name(attr)
                    for attr in attrs
                    if _attr_name(attr) and _field_kind(_attr_name(attr), _attr_type(attr)) == "media"
                ),
                "",
            )
            if not media_attr:
                continue
            attr_names = [_attr_name(attr) for attr in attrs if _attr_name(attr)]
            section["layout"] = "card"
            section["component"] = "ImageCard"
            if data_intent.get("media_position") == "header":
                section["position"] = "header"
                section["col_span"] = 12
            else:
                section["col_span"] = int(section.get("col_span") or 12)
            query = dict(section.get("query") or {})
            query["limit"] = 1
            query_hints = data_intent.get("query_hints") or {}
            attr_lookup = {name.lower(): name for name in attr_names}

            def _first_attr(candidates: tuple[str, ...]) -> str:
                for exact in candidates:
                    if exact in attr_lookup:
                        return attr_lookup[exact]
                for attr_name in attr_names:
                    low = attr_name.lower()
                    if any(candidate in low for candidate in candidates):
                        return attr_name
                return ""

            if query_hints.get("order"):
                order_field = _first_attr(("created_at", "updated_at", "date", "time", "timestamp", "id"))
                if order_field:
                    direction = "asc" if query_hints.get("order") == "oldest" else "desc"
                    query["order_by"] = [{"field": order_field, "direction": direction}]

            query_filters = list(query.get("filters") or [])

            def _append_filter(field: str, value: str, operator: str = "eq") -> None:
                if not field:
                    return
                item = {"field": field, "operator": operator, "value": str(value)}
                if item not in query_filters:
                    query_filters.append(item)

            for filter_hint in query_hints.get("filters") or []:
                kind = filter_hint.get("kind")
                if kind == "field":
                    field = attr_lookup.get(str(filter_hint.get("field") or "").lower())
                    _append_filter(field, filter_hint.get("value", ""))
                elif kind == "active":
                    field = _first_attr(("is_active", "active", "enabled", "is_enabled"))
                    _append_filter(field, filter_hint.get("value", "true"))
                elif kind == "status":
                    field = _first_attr(("status", "state", "decision"))
                    _append_filter(field, filter_hint.get("value", ""))
            if query_filters:
                query["filters"] = query_filters
            section["query"] = query
            style = dict(section.get("style") or {})
            style.update({
                "display_mode": "banner" if data_intent.get("media_position") == "header" else "grid",
                "card_style": "default",
                "columns": "1",
                "image_position": "top",
                "image_size": "lg",
            })
            if data_intent.get("media_position") == "header":
                style["header_style"] = "hidden"
            section["style"] = style
            hidden = [name for name in attr_names if name != media_attr]
            section["field_layout"] = {
                "image": media_attr,
                "hidden": hidden,
                "field_styles": {
                    media_attr: {"col_span": 12, "height": "lg", "label": "hidden"},
                    **{name: {"visible": "hidden"} for name in hidden},
                },
            }
            ops = _normalize_section_operations(section.get("operations"))
            ops["create"] = False
            ops["update"] = False
            ops["delete"] = False
            section["operations"] = ops
            converted_media_card = True
    interaction_intent = intent.get("interactionIntent") or {}
    for section in sections:
        if hide_ids and section.get("attributes"):
            attrs = [a.get("name", a) if isinstance(a, dict) else a for a in section.get("attributes", [])]
            hidden = [field for field in attrs if re.search(r"(^id$|_id$|id$|uuid|pk|internal)", str(field), re.I)]
            if hidden:
                layout = dict(section.get("field_layout") or {})
                layout["hidden"] = sorted(set([*(layout.get("hidden") or []), *hidden]))
                field_styles = dict(layout.get("field_styles") or {})
                for field in hidden:
                    field_styles[field] = {**(field_styles.get(field) or {}), "visible": "hidden"}
                layout["field_styles"] = field_styles
                section["field_layout"] = layout
        ops = _normalize_section_operations(section.get("operations"))
        if interaction_intent.get("delete") == "disabled":
            ops["delete"] = False
        elif interaction_intent.get("delete") == "enabled" and section.get("primary_model"):
            ops["delete"] = True
        if interaction_intent.get("multi_delete") and section.get("primary_model"):
            ops["select"] = True
            ops["delete"] = True
            style = dict(section.get("style") or {})
            style["multi_select"] = True
            section["style"] = style
        section["operations"] = ops
        if intent.get("interactionIntent", {}).get("navigation_required") and section.get("layout") in {"card", "list", "table", "gallery"}:
            section.setdefault("behavior", {})

    return pages, sections, tokens, styling

