import os
import requests
import json
import re
import copy
from collections import defaultdict
from google.adk.tools import FunctionTool
from .navigation_planner import DATA_SECTION_ROLES, build_navigation_plan

METADATA_API_BASE = os.getenv("METADATA_API_BASE", "http://studio-api:8000/api/v1/metadata")
PROTOTYPE_API_BASE = os.getenv("PROTOTYPE_API_BASE", "http://studio-prototypes:8010")
_METADATA_API_KEY = os.getenv("METADATA_API_KEY")
_AUTH_HEADERS = {"Authorization": f"Bearer {_METADATA_API_KEY}"} if _METADATA_API_KEY else {}

from .styling_engine import *

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
            "hide id", "hide ids", "hide internal", "no id fields", "without ids", "ä¸è¦id", "éšè—id", "éš±è—id",
        )),
        "table_targets": [],
        "single_card_media": header_media or any(term in text for term in (
            "single card", "one card", "single image card", "image only", "only image", "media only",
            "limit 1 card", "limit one card",
        )) or (
            ("card" in text or "å¡ç‰‡" in str(prompt or ""))
            and ("image" in text or "media" in text or "å›¾ç‰‡" in str(prompt or "") or "ç…§ç‰‡" in str(prompt or ""))
            and ("single" in text or "one" in text or "only" in text or "å•ä¸ª" in str(prompt or "") or "ä¸€å¼ " in str(prompt or "") or "åª" in str(prompt or ""))
        ),
        "media_position": "header" if header_media else "",
    }
    data_intent["query_hints"] = {}
    interaction_intent = {
        "delete": "default",
        "multi_delete": False,
        "navigation_required": any(term in text for term in ("navigate", "navigation", "link to", "go to", "è·³è½¬", "å¯¼èˆª")),
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

    if any(term in text for term in ("all sections table", "everything table", "all data as table", "æ‰€æœ‰è¡¨æ ¼")):
        component_intent["*"] = "table"
    elif any(term in text for term in ("all cards", "everything card", "all data as cards", "æ‰€æœ‰å¡ç‰‡")):
        component_intent["*"] = "card"

    if any(term in text for term in ("no delete", "disable delete", "hide delete", "without delete", "ä¸è¦åˆ é™¤", "ç¦ç”¨åˆ é™¤")):
        interaction_intent["delete"] = "disabled"
    elif any(term in text for term in ("enable delete", "allow delete", "show delete", "å¯ä»¥åˆ é™¤")):
        interaction_intent["delete"] = "enabled"
    if any(term in text for term in ("multi delete", "bulk delete", "delete selected", "batch delete", "å¤šé€‰åˆ é™¤", "æ‰¹é‡åˆ é™¤")):
        interaction_intent["multi_delete"] = True
        interaction_intent["delete"] = "enabled"

    if any(term in text for term in ("sidebar left", "left sidebar", "left nav", "å·¦ä¾§æ ", "å·¦ä¾§å¯¼èˆª")):
        layout_intent["sidebar"] = True
        layout_intent["sidebar_side"] = "left"
    elif any(term in text for term in ("sidebar right", "right sidebar", "right nav", "å³ä¾§æ ", "å³ä¾§å¯¼èˆª")):
        layout_intent["sidebar"] = True
        layout_intent["sidebar_side"] = "right"
    if any(term in text for term in ("main full", "full main", "main full width", "full-width main", "ä¸»åŒºåŸŸå…¨å®½")):
        layout_intent["full"] = True
        layout_intent["main_width"] = "full"
    if any(term in text for term in ("header full", "full header", "é¡µé¦–å…¨å®½")):
        layout_intent["header_width"] = "full"
    if any(term in text for term in ("footer full", "full footer", "é¡µè„šå…¨å®½")):
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

    color_intent = intent.get("colorIntent") or {}
    if color_intent:
        tokens.update(color_intent)

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

def _apply_prompt_style_overrides(tokens: dict, prompt: str = "") -> dict:
    color_name, theme = _prompt_color_theme(prompt)
    scoped_overrides = _prompt_scoped_color_overrides(prompt)
    typography_overrides = _prompt_typography_overrides(prompt)
    if not theme or _prompt_is_button_only_color(prompt):
        if scoped_overrides or typography_overrides:
            tokens = dict(tokens or {})
            tokens.update(scoped_overrides)
            tokens.update(typography_overrides)
            _expand_design_tokens(tokens)
        return tokens
    if not theme:
        return tokens
    tokens = dict(tokens or {})
    variant_index = str(tokens.get("design.variant_index", ""))
    accent = theme["accent"]
    secondary = theme.get("secondary", accent)
    page = theme.get("page", tokens.get("page.body.bg_hex", "#f9fafb"))
    surface = theme.get("surface", tokens.get("region.main.bg_hex", "#ffffff"))
    border = theme.get("border", tokens.get("region.border_hex", "#e5e7eb"))
    text = theme.get("text", tokens.get("page.body.text_hex", "#111827"))
    muted = theme.get("muted", tokens.get("color.text.muted_hex", "#6b7280"))
    on_accent = _text_on_color(accent)

    # Root palette tokens — always forced by the prompt theme
    tokens.update({
        "accent.hex": accent,
        "color.secondary.hex": secondary,
        "page.body.bg_hex": page,
        "page.bg.hex": page,
        "region.main.bg_hex": surface,
        "region.sidebar.bg_hex": surface,
        "region.border_hex": border,
        "region.border_strong_hex": border,
        "page.body.text_hex": text,
        "color.text.muted_hex": muted,
        "design.prompt_color": color_name or "",
    })
    # Derived region/component tokens — defer to LLM fine-grained overrides if already set
    for _k, _v in {
        "region.header.bg_hex": accent,
        "region.header.text_hex": on_accent,
        "region.header.bg": f"bg-[{accent}]",
        "region.footer.bg_hex": accent,
        "region.footer.text_hex": on_accent,
        "nav.bg_hex": accent,
        "nav.text_hex": on_accent,
        "button.primary.bg_hex": accent,
        "button.primary.border_hex": accent,
        "button.primary.text_hex": on_accent,
        "button.ghost.text_hex": accent,
        "button.link.text_hex": accent,
        "input.border_focus_hex": accent,
        "badge.info.bg_hex": accent,
        "badge.info.text_hex": on_accent,
    }.items():
        tokens.setdefault(_k, _v)
    if variant_index in {"1", "2"}:
        if color_name in {"pink", "rose"}:
            accent = {"1": "#be185d", "2": "#ec4899"}[variant_index]
            secondary = {"1": "#f472b6", "2": "#fbcfe8"}[variant_index]
        elif color_name in {"purple", "violet"}:
            accent = {"1": "#6d28d9", "2": "#a855f7"}[variant_index]
            secondary = {"1": "#a78bfa", "2": "#ddd6fe"}[variant_index]
        else:
            accent = {"1": theme.get("accent", "#2563eb"), "2": theme.get("secondary", theme.get("accent", "#2563eb"))}[variant_index]
            secondary = theme.get("secondary", accent)
        on_accent = _text_on_color(accent)
        tokens.update({
            "accent.hex": accent,
            "color.secondary.hex": secondary,
            "region.header.bg_hex": accent,
            "region.header.text_hex": on_accent,
            "region.footer.bg_hex": accent,
            "region.footer.text_hex": on_accent,
            "nav.bg_hex": accent,
            "nav.text_hex": on_accent,
            "button.primary.bg_hex": accent,
            "button.primary.border_hex": accent,
            "button.primary.text_hex": on_accent,
            "button.ghost.text_hex": accent,
            "input.border_focus_hex": accent,
            "design.variant_index": variant_index,
        })
    if scoped_overrides:
        tokens.update(scoped_overrides)
    if typography_overrides:
        tokens.update(typography_overrides)
    _expand_design_tokens(tokens)
    return tokens

def _prompt_styling_overrides(prompt: str = "") -> dict:
    if _prompt_color_scope_lock(prompt):
        return {}
    color_name, theme = _prompt_color_theme(prompt)
    typography = _prompt_typography_overrides(prompt)
    if not theme and not typography:
        return {}
    out = {}
    if theme:
        out.update({
            "accentColor": theme["accent"],
            "backgroundColor": theme.get("page", "#f9fafb"),
            "textColor": theme.get("text", "#111827"),
            "selectedStyle": color_name or "custom",
        })
    if typography:
        out["typographyScale"] = "custom"
    return out

def _build_activity_diagrams(system_data: dict) -> list:
    diagrams = system_data.get("diagrams") or []
    classifiers = {str(c.get("id")): c for c in _as_list(system_data.get("classifiers"), "classifiers")}
    relations = {str(r.get("id")): r for r in _as_list(system_data.get("relations"), "relations")}
    out = []
    for diagram in diagrams:
        if diagram.get("type") != "activity": continue
        raw_nodes = diagram.get("nodes") or []; raw_edges = diagram.get("edges") or []; nodes = []; node_by_cls = {}
        for node in raw_nodes:
            cls_id = str(node.get("cls") or node.get("cls_id") or node.get("cls_ptr") or ""); classifier = classifiers.get(cls_id, {}); nodes.append({"id": str(node.get("id")), "cls_ptr": cls_id, "cls": classifier.get("data", {}), "data": node.get("data", {})})
            if cls_id: node_by_cls[cls_id] = str(node.get("id"))
        edges = []
        for edge in raw_edges:
            rel_id = str(edge.get("rel") or edge.get("rel_id") or edge.get("rel_ptr") or ""); relation = relations.get(rel_id, {}); source_cls = str(relation.get("source") or relation.get("source_id") or ""); target_cls = str(relation.get("target") or relation.get("target_id") or ""); source_ptr = node_by_cls.get(source_cls); target_ptr = node_by_cls.get(target_cls)
            if not source_ptr or not target_ptr: continue
            edges.append({"id": str(edge.get("id")), "source_ptr": source_ptr, "target_ptr": target_ptr, "rel_ptr": rel_id, "rel": relation.get("data", {}), "data": edge.get("data", {})})
        out.append({"id": str(diagram.get("id")), "name": diagram.get("name", ""), "type": "activity", "nodes": nodes, "edges": edges})
    return out

def _actor_refs(system_data: dict, actor_id: str | None, actor_name: str | None = None) -> set[str]:
    refs = {str(actor_id)} if actor_id else set()
    actor_name_norm = str(actor_name or "").lower()
    classifiers = {
        str(c.get("id")): c.get("data", {})
        for c in _as_list(system_data.get("classifiers"), "classifiers")
    }
    for diagram in system_data.get("diagrams", []):
        if diagram.get("type") != "usecase":
            continue
        for node in diagram.get("nodes", []):
            cls_id = str(node.get("cls") or node.get("cls_id") or node.get("cls_ptr") or "")
            cls = classifiers.get(cls_id, {})
            if cls.get("type") == "actor" and (
                cls_id == str(actor_id)
                or str(cls.get("name", "")).lower() == actor_name_norm
            ):
                refs.add(str(node.get("id")))
                refs.add(cls_id)
    return {ref for ref in refs if ref and ref != "None"}

def _ref_values(values) -> set[str]:
    out = set()
    for value in values or []:
        if isinstance(value, dict):
            ref = value.get("id") or value.get("value") or value.get("classifier") or value.get("node")
        else:
            ref = value
        if ref:
            out.add(str(ref))
    return out

def _ref_list(values) -> list[str]:
    out = []
    seen = set()
    for value in values or []:
        if isinstance(value, dict):
            ref = value.get("id") or value.get("value") or value.get("classifier") or value.get("node")
        else:
            ref = value
        if ref and str(ref) not in seen:
            out.append(str(ref))
            seen.add(str(ref))
    return out

def _name_tokens(value: str) -> set[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(value or ""))
    tokens = {
        token
        for token in re.split(r"[^A-Za-z0-9]+", spaced.lower())
        if len(token) > 1
    }
    singulars = {token[:-1] for token in tokens if len(token) > 3 and token.endswith("s")}
    return tokens | singulars

def _rank_models_for_text(text: str, models: list[str], prefer_collections: bool = False) -> list[str]:
    text_tokens = _name_tokens(text)
    ranked = []
    for index, model in enumerate(models or []):
        model_tokens = _name_tokens(model)
        if not model_tokens:
            continue
        overlap = len(text_tokens & model_tokens)
        compact_model = re.sub(r"[^a-z0-9]+", "", str(model).lower())
        compact_text = re.sub(r"[^a-z0-9]+", "", str(text).lower())
        substring = 2 if compact_model and compact_model in compact_text else 0
        collection_bonus = 1 if prefer_collections and _is_child_collection_model(model, text) else 0
        ranked.append((overlap + substring + collection_bonus, -index, model))
    ranked.sort(reverse=True)
    return [model for score, _index, model in ranked if score > 0]

def _infer_usecase_model(name: str, explicit_classes: list[str], classifiers: dict[str, dict], model_names: set[str]) -> str:
    for ref in explicit_classes:
        cls = classifiers.get(ref, {})
        cname = cls.get("name") or ref
        if cname in model_names:
            return cname
    ranked = _rank_models_for_text(name, sorted(model_names, key=len, reverse=True))
    return ranked[0] if ranked else ""

def _humanize_action_label(name: str, fallback: str = "Start") -> str:
    raw = re.sub(r"[_-]+", " ", str(name or "")).strip()
    if not raw:
        return fallback
    cleaned = re.sub(r"^(manage|view|track|write|browse|search|review)\s+", "", raw, flags=re.I).strip()
    if re.search(r"\b(apply|application|request|submit|onboard|register|book|schedule|reserve|approval|claim|ticket|case|workflow|process)\b", raw, re.I):
        return "Start"
    return cleaned[:1].upper() + cleaned[1:] if cleaned else fallback

def _is_child_collection_model(model_name: str, page_terms: str = "") -> bool:
    name_l = str(model_name or "").lower()
    if not name_l:
        return False
    if any(term in _name_tokens(name_l) for term in ("item", "line", "entry", "row", "detail", "selection", "membership", "mapping", "association")):
        return True
    return False

def _plural_page_id(model: str) -> str:
    base = _section_id(model or "items")
    if base.endswith("y"):
        return f"{base[:-1]}ies"
    if base.endswith("s"):
        return base
    return f"{base}s"

def _nav_mapping_for_usecase(usecase: dict, workflow_entry: bool = False) -> dict:
    name = str(usecase.get("name") or "")
    name_l = name.lower()
    primary = usecase.get("primary_model") or ""
    class_names = [m for m in usecase.get("class_names") or [] if m]
    ranked_models = _rank_models_for_text(name, class_names)

    def best_model(default: str = "") -> str:
        return primary or (ranked_models[0] if ranked_models else (class_names[0] if class_names else default))

    if any(term in name_l for term in ("system process", "background", "automated", "notification")):
        return {"role": "background", "page_id": "", "page_name": "", "page_model": primary, "operation_kind": "background"}

    if workflow_entry:
        page_model = best_model()
        page_id = _section_id(page_model or name)
        return {
            "role": "workflow_entry",
            "page_id": page_id,
            "page_name": _page_name(page_id),
            "page_model": page_model,
            "operation_kind": "start_workflow",
        }

    inline_terms = ("add", "remove", "delete", "update", "select", "write", "review", "rate")
    if any(term in name_l for term in inline_terms) and "manage" not in name_l:
        page_model = best_model()
        target_model = next((m for m in ranked_models + class_names if m and m != page_model), page_model)
        operation_kind = "delete" if any(term in name_l for term in ("remove", "delete")) else (
            "create_related" if target_model and target_model != page_model and any(term in name_l for term in ("add", "write", "create", "select")) else "object_operation"
        )
        return {
            "role": "inline_operation",
            "page_id": _section_id(page_model or name),
            "page_name": _page_name(page_model or name),
            "page_model": page_model,
            "operation_kind": operation_kind,
            "target_model": target_model,
        }

    if any(term in name_l for term in ("browse", "search", "catalog", "list", "overview", "directory")):
        page_model = best_model()
        page_id = _plural_page_id(page_model) if page_model else _section_id(name)
        return {"role": "collection_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "view_collection"}

    if "detail" in name_l or name_l.startswith("view "):
        page_model = best_model()
        page_id = f"{_section_id(page_model)}_detail" if page_model else _section_id(name)
        return {"role": "detail_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "view_detail"}

    if "track" in name_l or "history" in name_l:
        page_model = best_model()
        page_id = _plural_page_id(page_model) if page_model else _section_id(name)
        return {"role": "collection_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "view_collection"}

    if any(term in name_l for term in ("account", "profile", "settings")):
        page_model = best_model()
        page_id = _section_id(page_model or name)
        return {"role": "object_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": page_model, "operation_kind": "manage_object"}

    page_id = _section_id(primary or name)
    return {"role": "object_workspace", "page_id": page_id, "page_name": _page_name(page_id), "page_model": primary, "operation_kind": "manage_object"}

def _activity_action_indexes(system_data: dict) -> tuple[dict[str, dict], set[str], set[str]]:
    by_id = {}
    first_ids = set()
    all_ids = set()
    for diagram in system_data.get("activity_diagrams") or []:
        incoming = {}
        outgoing = {}
        action_ids = set()
        for node in diagram.get("nodes") or []:
            cls = node.get("cls") or {}
            if cls.get("type") == "action":
                nid = str(node.get("id"))
                cid = str(node.get("cls_ptr") or "")
                action_ids.add(nid)
                all_ids.update({nid, cid})
                by_id[nid] = {"node_id": nid, "classifier_id": cid, "name": cls.get("name", ""), "diagram_id": diagram.get("id"), "diagram_name": diagram.get("name", "")}
                if cid:
                    by_id[cid] = by_id[nid]
        for edge in diagram.get("edges") or []:
            source = str(edge.get("source_ptr") or "")
            target = str(edge.get("target_ptr") or "")
            if source and target:
                incoming.setdefault(target, []).append(source)
                outgoing.setdefault(source, []).append(target)
        for aid in action_ids:
            source_nodes = incoming.get(aid, [])
            if not source_nodes or any(((next((n for n in diagram.get("nodes") or [] if str(n.get("id")) == src), {}).get("cls") or {}).get("type") == "initial") for src in source_nodes):
                first_ids.add(aid)
                cls_id = by_id.get(aid, {}).get("classifier_id")
                if cls_id:
                    first_ids.add(cls_id)
    return by_id, first_ids, all_ids

def _usecase_has_workflow_entry(usecase: dict, has_activity_workflow: bool, activity_first_ids: set[str], activity_all_ids: set[str]) -> bool:
    if not has_activity_workflow:
        return False
    refs = set(usecase.get("activities") or []) | set(usecase.get("actions") or [])
    if refs:
        return bool(refs & (activity_first_ids or activity_all_ids))
    name_l = usecase.get("name", "").lower()
    passive_terms = {"browse", "search", "view", "track", "receive", "manage account", "settings", "profile", "history", "status"}
    if any(term in name_l for term in passive_terms):
        return False
    intent_terms = {
        "apply", "application", "request", "submit", "book", "schedule",
        "reserve", "register", "onboard", "approve", "approval", "claim", "ticket", "case",
        "process", "workflow"
    }
    if any(term in name_l for term in intent_terms):
        return True
    return False

def _infer_usecase_permissions(name: str) -> list[str]:
    name_l = str(name or "").lower()
    perms = {"view"}
    if any(term in name_l for term in ("add", "create", "write", "submit")):
        perms.add("create")
    if any(term in name_l for term in ("manage", "update", "edit", "select", "enter", "process", "confirm", "track")):
        perms.add("update")
    if "manage" in name_l and not any(term in name_l for term in ("account", "profile", "settings", "password")):
        if any(term in name_l for term in ("item", "items", "record", "records", "entry", "entries", "line", "lines")):
            perms.update({"create", "delete"})
    if any(term in name_l for term in ("delete", "remove", "cancel")):
        perms.add("delete")
    return [p for p in ("view", "create", "update", "delete") if p in perms]

def _build_usecase_navigation(system_data: dict, actor_id: str | None, actor_name: str | None = None) -> dict:
    refs = _actor_refs(system_data, actor_id, actor_name)
    classifiers = {
        str(c.get("id")): (c.get("data") or {})
        for c in _as_list(system_data.get("classifiers"), "classifiers")
    }
    model_names = {
        cdata.get("name")
        for cdata in classifiers.values()
        if cdata.get("name") and cdata.get("type") in {"class", "entity", "model"}
    }
    model_attrs = {
        cdata.get("name"): {a.get("name") for a in cdata.get("attributes", []) if a.get("name")}
        for cdata in classifiers.values()
        if cdata.get("name") and cdata.get("type") in {"class", "entity", "model"}
    }
    relations = {str(r.get("id")): r for r in _as_list(system_data.get("relations"), "relations")}
    usecases = {}
    includes = {}
    for diagram in system_data.get("diagrams", []):
        if diagram.get("type") != "usecase":
            continue
        node_by_cls = {}
        for node in diagram.get("nodes", []):
            cls_id = str(node.get("cls") or node.get("cls_id") or node.get("cls_ptr") or "")
            if cls_id:
                node_by_cls[cls_id] = str(node.get("id"))
        for edge in diagram.get("edges", []):
            rel_id = str(edge.get("rel") or edge.get("rel_id") or edge.get("rel_ptr") or "")
            rel = relations.get(rel_id, {})
            rdata = rel.get("data") or {}
            source = str(rel.get("source") or rel.get("source_id") or "")
            target = str(rel.get("target") or rel.get("target_id") or "")
            if rdata.get("type") == "interaction":
                source_cls = classifiers.get(source, {})
                target_cls = classifiers.get(target, {})
                uc_id = ""
                if source in refs and target_cls.get("type") == "usecase":
                    uc_id = target
                elif target in refs and source_cls.get("type") == "usecase":
                    uc_id = source
                if uc_id and uc_id not in usecases:
                    uc = classifiers.get(uc_id, {})
                    explicit_classes = _ref_list(uc.get("classes"))
                    model = _infer_usecase_model(uc.get("name", ""), explicit_classes, classifiers, model_names)
                    page_id = _section_id(uc.get("name") or "usecase")
                    class_names = [
                        classifiers.get(cid, {}).get("name")
                        for cid in explicit_classes
                        if classifiers.get(cid, {}).get("name") in model_names
                    ]
                    page_terms = f"{uc.get('name', '')} {uc.get('trigger', '')} {uc.get('precondition', '')}"
                    usecases[uc_id] = {
                        "id": uc_id,
                        "node_id": node_by_cls.get(uc_id, ""),
                        "name": uc.get("name", ""),
                        "page_id": page_id,
                        "page_name": _page_name(uc.get("name") or page_id),
                        "primary_model": model,
                        "permissions": _infer_usecase_permissions(uc.get("name", "")),
                        "classes": explicit_classes,
                        "class_names": class_names,
                        "pre_workflow_collections": [m for m in class_names if m != model and _is_child_collection_model(m, page_terms)],
                        "activities": sorted(_ref_values(uc.get("activities"))),
                        "actions": sorted(_ref_values(uc.get("actions"))),
                        "trigger": uc.get("trigger", ""),
                        "precondition": uc.get("precondition", ""),
                        "postcondition": uc.get("postcondition", ""),
                    }
            elif rdata.get("type") in {"inclusion", "extension"}:
                includes.setdefault(source, []).append({"type": rdata.get("type"), "usecase_id": target, "name": classifiers.get(target, {}).get("name", "")})
    activity_by_id, activity_first_ids, activity_all_ids = _activity_action_indexes(system_data)
    has_activity_workflow = bool(system_data.get("activity_diagrams"))
    actor_permissions = {}
    for uc_id, uc in usecases.items():
        uc["related_usecases"] = includes.get(uc_id, [])
        has_workflow_entry = _usecase_has_workflow_entry(uc, has_activity_workflow, activity_first_ids, activity_all_ids)
        ui_mapping = _nav_mapping_for_usecase(uc, has_workflow_entry)
        uc["ui_mapping"] = ui_mapping
        if ui_mapping.get("page_id"):
            uc["page_id"] = ui_mapping["page_id"]
            uc["page_name"] = ui_mapping.get("page_name") or _page_name(ui_mapping["page_id"])
        if ui_mapping.get("page_model"):
            uc["page_model"] = ui_mapping["page_model"]
        model = uc.get("primary_model")
        if model:
            current = set(actor_permissions.get(model, []))
            current.update(uc.get("permissions") or [])
            actor_permissions[model] = [p for p in ("view", "create", "update", "delete") if p in current]
        for related_model in uc.get("class_names") or []:
            if not related_model:
                continue
            current = set(actor_permissions.get(related_model, []))
            current.add("view")
            if _is_child_collection_model(related_model, f"{uc.get('name', '')} {uc.get('trigger', '')}"):
                current.update({"update", "delete"})
            actor_permissions[related_model] = [p for p in ("view", "create", "update", "delete") if p in current]
    page_entries = {}
    for uc in usecases.values():
        mapping = uc.get("ui_mapping") or {}
        page_id = mapping.get("page_id") or uc.get("page_id")
        if not page_id or mapping.get("role") == "background":
            continue
        current = page_entries.setdefault(page_id, {
            "page_id": page_id,
            "page_name": mapping.get("page_name") or uc.get("page_name") or _page_name(page_id),
            "primary_model": mapping.get("page_model") or uc.get("page_model") or uc.get("primary_model", ""),
            "roles": [],
            "usecases": [],
        })
        if mapping.get("role") and mapping["role"] not in current["roles"]:
            current["roles"].append(mapping["role"])
        current["usecases"].append(uc.get("name"))
    nav_pages = [
        entry["page_id"]
        for entry in page_entries.values()
        if any(role in entry["roles"] for role in ("collection_workspace", "object_workspace", "workflow_entry"))
    ]
    icon_actions = [pid for pid in nav_pages if any(term in pid for term in ("account", "profile", "settings", "search"))]
    workflow_entry_points = []
    for uc in usecases.values():
        if _usecase_has_workflow_entry(uc, has_activity_workflow, activity_first_ids, activity_all_ids):
            refs = set(uc.get("activities") or []) | set(uc.get("actions") or [])
            linked_actions = [activity_by_id[ref] for ref in refs if ref in activity_by_id]
            first_linked = next((a for a in linked_actions if a.get("node_id") in activity_first_ids or a.get("classifier_id") in activity_first_ids), None)
            first_action = first_linked or (linked_actions[0] if linked_actions else None)
            label = _humanize_action_label(uc.get("name", ""), "Start")
            workflow_entry_points.append({
                "page_id": uc.get("page_id"),
                "page_name": uc.get("page_name"),
                "usecase_name": uc.get("name"),
                "section_layout": "activity_start",
                "label": label,
                "button_label": label,
                "primary_model": uc.get("primary_model", ""),
                "related_models": uc.get("class_names") or [],
                "pre_workflow_collections": uc.get("pre_workflow_collections") or [],
                "starts_activity_node_id": first_action.get("node_id") if first_action else "",
                "starts_activity_name": first_action.get("name") if first_action else "",
                "reason": "Starts the executable workflow for this use case; downstream activity pages stay gated by active_process_node_id.",
            })
    nav = {
        "actor_refs": sorted(refs),
        "usecases": list(usecases.values()),
        "pages": list(page_entries.values()),
        "nav_bar_pages": nav_pages,
        "icon_actions": icon_actions,
        "actor_permissions": actor_permissions,
        "workflow_entry_points": workflow_entry_points,
        "_note": "Use usecases for high-level pages, navigation entries, icon buttons, and actor permissions; use activity_diagrams/workflow_plan only for executable workflow tasks.",
    }
    workflow_steps = _workflow_plan(system_data, actor_id, actor_name)
    nav["workflow_steps"] = workflow_steps
    nav["nav_plan"] = build_navigation_plan(nav, model_attrs, workflow_steps)
    return nav

def _workflow_plan(system_data: dict, actor_id: str | None, actor_name: str | None = None) -> list:
    refs = _actor_refs(system_data, actor_id, actor_name)
    classifiers = {
        str(c.get("id")): (c.get("data") or {})
        for c in _as_list(system_data.get("classifiers"), "classifiers")
    }

    def _class_name(ref) -> str:
        if isinstance(ref, dict):
            ref = ref.get("id") or ref.get("value") or ref.get("name")
        ref = str(ref or "")
        return classifiers.get(ref, {}).get("name") or ref

    def _class_refs(raw_classes) -> list:
        if isinstance(raw_classes, dict):
            refs = []
            for values in raw_classes.values():
                refs.extend(values or [])
            return refs
        return list(raw_classes or [])

    steps = []
    for diagram in system_data.get("activity_diagrams", []):
        nodes = {str(n.get("id")): n for n in diagram.get("nodes", [])}
        outgoing = {}
        for edge in diagram.get("edges", []):
            outgoing.setdefault(str(edge.get("source_ptr")), []).append(str(edge.get("target_ptr")))
        for node in diagram.get("nodes", []):
            cls = node.get("cls", {})
            if cls.get("type") != "action":
                continue
            actor_node = str(cls.get("actorNode") or "")
            if refs and actor_node not in refs:
                continue
            name = cls.get("name") or "Workflow Step"
            page_name = _workflow_page_name(name)
            page_id = _section_id(page_name)
            next_action_ids = [
                target
                for target in outgoing.get(str(node.get("id")), [])
                if (nodes.get(target, {}).get("cls") or {}).get("type") == "action"
            ]
            steps.append({
                "activity_node_id": str(node.get("id")),
                "activity_node_name": name,
                "actor_node": actor_node,
                "classes": [_class_name(ref) for ref in _class_refs(cls.get("classes")) if _class_name(ref)],
                "diagram_id": diagram.get("id"),
                "diagram_name": diagram.get("name"),
                "page_id": page_id,
                "page_name": page_name,
                "next_activity_node_ids": next_action_ids,
            })
    return steps

def _activity_models_for_step(step: dict, workflow_entries: list, known_models: set[str]) -> list[str]:
    name_l = str(step.get("activity_node_name") or step.get("page_name") or "").lower()
    explicit_step_models = [m for m in step.get("classes") or [] if m in known_models]
    if explicit_step_models:
        ranked = _rank_models_for_text(name_l, explicit_step_models, prefer_collections=True)
        return (ranked + [m for m in explicit_step_models if m not in ranked])[:2]
    entries = [e for e in workflow_entries if not e.get("diagram_id") or e.get("diagram_id") == step.get("diagram_id")]
    related = []
    for entry in entries or workflow_entries:
        related.extend(entry.get("pre_workflow_collections") or [])
        related.extend(entry.get("related_models") or [])
        if entry.get("primary_model"):
            related.append(entry.get("primary_model"))
    related = [m for m in dict.fromkeys(related) if m in known_models]
    if not related:
        return []

    prefer_collections = any(term in _name_tokens(name_l) for term in ("add", "select", "choose", "list", "review", "manage"))
    ranked = _rank_models_for_text(name_l, related, prefer_collections=prefer_collections)
    return ranked[:2] or related[:1]

def _activity_layout_for_step(step_name: str, model: str) -> str:
    name_tokens = _name_tokens(step_name)
    # "select/choose" = pick from options → card with select operation, not a form
    if any(term in name_tokens for term in ("select", "choose", "pick")):
        return "card"
    if any(term in name_tokens for term in (
        "enter", "fill", "input", "provide", "submit",
        "create", "add", "update", "edit", "write", "upload", "register",
        "book", "pay", "record",
    )):
        return "form"
    if _is_child_collection_model(model, step_name) or any(term in name_tokens for term in ("list", "browse", "review", "manage", "track", "history")):
        return "list"
    if any(term in name_tokens for term in ("confirmation", "confirm", "detail", "summary")):
        return "detail"
    return "detail"

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
    # but their name matches the activity action name â€” use this to avoid creating duplicates.
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

def _actor_name_from_context(system_context: dict, actor_id: str | None) -> str | None:
    for classifier in _as_list(system_context.get("classifiers"), "classifiers"):
        if str(classifier.get("id")) == str(actor_id): return (classifier.get("data") or {}).get("name")
    return None

def _apply_builtin_workflow_logic(interface_data: dict, system_id: str | None, actor_id: str | None) -> dict:
    data = dict(interface_data or {}); pages = list(data.get("pages") or []); sections = list(data.get("sections") or [])
    if system_id:
        system_context = _fetch_system_context_data(system_id)
        actor_name = _actor_name_from_context(system_context, actor_id)
        model_attrs = {}
        for c in _as_list(system_context.get("classifiers"), "classifiers"):
            cdata = c.get("data") or {}
            cname = cdata.get("name")
            if cname:
                model_attrs[cname] = {a.get("name") for a in cdata.get("attributes", []) if a.get("name")}
        usecase_navigation = _build_usecase_navigation(system_context, str(actor_id or ""), actor_name)
        workflow_steps = _workflow_plan(system_context, str(actor_id or ""), actor_name)
        pages, sections = _ensure_workflow_pages(pages, sections, workflow_steps, model_attrs, usecase_navigation)
    sections = _normalize_chrome_sections(_normalize_activity_action_sections(pages, sections)); data["pages"] = pages; data["sections"] = sections
    return data

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
    preferred = ["name", "title", "status", "price", "total", "quantity", "description", "created_at"]
    attrs = list(model_attrs.get(model) or [])
    selected = [name for name in preferred if name in attrs]
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
    if tokens & {"form", "enter", "submit", "create", "edit", "update", "provide", "select", "choose"}:
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

def _default_category_for_model(model: str, model_id_by_name: dict[str, str] | None = None) -> dict | None:
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
    layout = _infer_section_layout(page, candidate_index)
    page_id = _section_id(page.get("id") or page.get("name") or "page")
    sid = f"{page_id}_{_section_id(model or 'content')}_{layout}"
    attrs = _model_field_names(model_attrs, model, 8 if layout in {"table", "detail"} else 5)
    operations = {"create": layout == "form", "update": layout in {"detail", "form"}, "delete": False}
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

def _header_sections_for_candidate(normal_pages: list, candidate_index: int = 0, model_attrs: dict | None = None) -> list[dict]:
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

def _ensure_normal_page_navigation(pages: list, sections: list, normal_pages: list, candidate_index: int = 0) -> tuple[list, list]:
    if not normal_pages:
        return pages, sections
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    nav_methods = _navigation_methods([p.get("name") for p in normal_pages if p.get("name")])
    for section in sections:
        if section.get("position") == "footer" or _normalize_layout_alias(section.get("layout")) in _FOOTER_TEMPLATE_LAYOUTS:
            existing = section.get("methods") or []
            existing_names = {
                str(m.get("name") if isinstance(m, dict) else m).strip().lower()
                for m in existing
            }
            if nav_methods and (not existing_names or existing_names.issubset({"help", "privacy", "terms", "contact"})):
                section["methods"] = nav_methods
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
    keep_nav_id = header_nav_ids[0] if header_nav_ids else (sidebar_nav_ids[0] if sidebar_nav_ids else "")
    duplicate_nav_ids = set(nav_ids)
    if keep_nav_id:
        duplicate_nav_ids.discard(keep_nav_id)
    if duplicate_nav_ids:
        sections = [s for s in sections if str(s.get("id") or "") not in duplicate_nav_ids]
        section_map = {str(s.get("id")): s for s in sections if s.get("id")}
        for page in pages:
            page["sections"] = [
                ref for ref in (page.get("sections") or [])
                if _ref_id(ref) not in duplicate_nav_ids
            ]

    if not keep_nav_id:
        nav_section = (
            _sidebar_nav_section_for_candidate(normal_pages, candidate_index)
            if int(candidate_index or 0) % 3 == 2
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
        keep_nav_id = sid
    elif int(candidate_index or 0) % 3 != 2 and keep_nav_id in sidebar_nav_ids and not header_nav_ids:
        nav_section = section_map.get(keep_nav_id) or {}
        nav_section["position"] = "header"
        nav_section["layout"] = "nav-links"
        nav_section["component"] = "NavBar"
        style = dict(nav_section.get("style") or {})
        style.pop("sidebar_side", None)
        style.pop("sidebar_width", None)
        style["variant"] = "page-nav"
        nav_section["style"] = style

    if keep_nav_id:
        for page in normal_pages:
            refs = [{"value": _ref_id(ref)} for ref in page.get("sections") or [] if _ref_id(ref)]
            ref_ids = {_ref_id(ref) for ref in refs}
            if keep_nav_id not in ref_ids:
                keep_nav_section = section_map.get(keep_nav_id) or {}
                if keep_nav_section.get("position") == "sidebar":
                    page["sections"] = [{"value": keep_nav_id}] + refs
                else:
                    page["sections"] = refs
    return pages, sections

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
                "update": layout in {"list", "table", "detail", "form"},
                "delete": layout in {"list", "table", "card", "gallery"},
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

def _fetch_system_context_data(system_id: str) -> dict:
    response = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/", headers=_AUTH_HEADERS)
    response.raise_for_status()
    system_data = response.json()
    classifiers_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/classifiers/", headers=_AUTH_HEADERS)
    relations_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/relations/", headers=_AUTH_HEADERS)
    system_data["classifiers"] = classifiers_resp.json() if classifiers_resp.ok else []
    system_data["relations"] = relations_resp.json() if relations_resp.ok else []
    export_resp = requests.get(f"{METADATA_API_BASE}/systems/export/", params=[("system_ids", system_id)], headers=_AUTH_HEADERS)
    if export_resp.ok:
        exported = export_resp.json()
        if exported:
            exp = exported[0]
            system_data["diagrams"] = exp.get("diagrams", [])
            # Fall back to export classifiers/relations when dedicated endpoints fail
            if not system_data["classifiers"]:
                system_data["classifiers"] = exp.get("classifiers", [])
            if not system_data["relations"]:
                system_data["relations"] = exp.get("relations", [])
    system_data["activity_diagrams"] = _build_activity_diagrams(system_data)
    return system_data

def get_system_context(system_id: str) -> str:
    try:
        system_data = _fetch_system_context_data(system_id); system_data["workflow_plan"] = _workflow_plan(system_data, None); system_data["usecase_navigation"] = _build_usecase_navigation(system_data, None)
        return json.dumps(system_data, indent=2)
    except Exception as e: return f"Error fetching system context: {e}"

def get_interface_config(interface_id: str) -> str:
    try:
        response = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS); response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e: return f"Error fetching interface config: {e}"

def _build_known_attrs(system_id: str) -> dict[str, set[str]]:
    """Returns {ModelName: {attr_name, ...}} for validation. Empty on error."""
    try:
        ctx = _fetch_system_context_data(system_id)
        result = {}
        for c in _as_list(ctx, "classifiers"):
            name = (c.get("data") or {}).get("name", "")
            attrs = {a.get("name") for a in ((c.get("data") or {}).get("attributes") or []) if a.get("name")}
            if name:
                result[name] = attrs
        return result
    except Exception:
        return {}

def apply_interface_patch(interface_id: str, patch: dict) -> str:
    try:
        resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS)
        resp.raise_for_status()
        current = resp.json()
        data = dict(current.get("data") or {})
        def _norm_refs(refs: list) -> list:
            out = []
            for ref in refs or []:
                sid = ref.get("value") if isinstance(ref, dict) else ref
                if sid:
                    out.append({"value": str(sid)})
            return out

        if "sections" in patch:
            section_map = {str(s["id"]): s for s in data.get("sections", [])}
            for ps in patch["sections"]:
                sid = str(ps.get("id", ""))
                if not sid:
                    continue
                is_new = sid not in section_map
                if is_new:
                    section_map[sid] = {
                        "id": sid,
                        "name": ps.get("name") or sid,
                        "role": ps.get("role", ""),
                        "layout": ps.get("layout", "card"),
                        "component": ps.get("component") or _infer_section_component(ps),
                        "position": ps.get("position", "main"),
                        "col_span": ps.get("col_span", 12),
                        "primary_model": ps.get("primary_model", ""),
                        "class": ps.get("class") or ps.get("primary_model", ""),
                        "attributes": ps.get("attributes", []),
                        "field_layout": ps.get("field_layout", {}),
                        "behavior": ps.get("behavior", {}),
                        "related_to": ps.get("related_to"),
                        "relationship": ps.get("relationship", {}),
                        "relation_field": ps.get("relation_field"),
                        "operations": ps.get("operations", {"create": False, "update": False, "delete": False, "select": False}),
                        "data_source": ps.get("data_source", {}),
                        "query": ps.get("query", {}),
                        "style": ps.get("style", {}),
                    }
                for field in ("role", "layout", "component", "col_span", "position", "attributes", "field_layout", "behavior", "related_to", "relationship", "relation_field", "data_source", "query", "workflow", "label", "target_page", "workflow_action", "primary_model", "class", "text", "methods", "min_height"):
                    if field in ps:
                        section_map[sid][field] = ps[field]
                if "style" in ps:
                    section_map[sid]["style"] = {**(section_map[sid].get("style") or {}), **ps["style"]}
            data["sections"] = list(section_map.values())
        if "pages" in patch:
            page_map = {str(p["id"]): p for p in data.get("pages", [])}
            for pp in patch["pages"]:
                pid = str(pp.get("id", ""))
                if not pid:
                    continue
                if pid not in page_map:
                    page_map[pid] = {
                        "id": pid,
                        "name": pp.get("name") or pid,
                        "sections": _norm_refs(pp.get("sections") or []),
                        "primary_model": pp.get("primary_model", ""),
                        "category": pp.get("category", None),
                    }
                for field in ("layout", "gap", "name", "primary_model", "category", "type"):
                    if field in pp:
                        page_map[pid][field] = pp[field]
                if "sections" in pp:
                    page_map[pid]["sections"] = _norm_refs(pp["sections"])
            data["pages"] = list(page_map.values())
        if "styling" in patch:
            data["styling"] = {**(data.get("styling") or {}), **patch["styling"]}
        if "tokens" in patch:
            data["tokens"] = {**(data.get("tokens") or {}), **patch["tokens"]}
        # Validate attribute names against real classifier fields; warn agent so it can self-correct
        if "sections" in patch:
            known_attrs = _build_known_attrs(current.get("system", ""))
            warnings = []
            for sec in patch["sections"]:
                model = sec.get("primary_model") or sec.get("class", "")
                raw_attrs = sec.get("attributes") or []
                attr_names = [a if isinstance(a, str) else (a.get("name") if isinstance(a, dict) else "") for a in raw_attrs]
                valid = known_attrs.get(model, set())
                if valid:
                    bad = [a for a in attr_names if a and a not in valid and "." not in a]
                    if bad:
                        warnings.append(f"section '{sec.get('id')}': unknown attributes {bad} for model '{model}' â€” valid: {sorted(valid)}")
            if warnings:
                return "WARNING â€” patch rejected due to invented attribute names. Fix these and retry:\n" + "\n".join(warnings)
        try:
            data = _apply_builtin_workflow_logic(data, current.get("system"), current.get("actor"))
        except Exception:
            data["sections"] = _normalize_activity_action_sections(data.get("pages") or [], data.get("sections") or [])
        payload = {
            "id": interface_id,
            "name": current["name"],
            "description": current["description"],
            "system_id": current["system"],
            "actor_id": current["actor"],
            "data": data,
        }
        put_resp = requests.put(f"{METADATA_API_BASE}/interfaces/{interface_id}/", json=payload, headers=_AUTH_HEADERS)
        put_resp.raise_for_status()
        return f"Patched interface {interface_id} successfully."
    except Exception as e: return f"Error patching interface: {e}"

def run_seed_script(python_code: str) -> str:
    try:
        resp = requests.post(f"{PROTOTYPE_API_BASE}/seed_script", json={"script": python_code}, timeout=120)
        if resp.ok: return resp.text or "Seeded OK"
        return f"Seed failed ({resp.status_code}): {resp.text}"
    except Exception as e: return f"Error calling seed_script endpoint: {e}"

def get_available_paths(system_id: str, class_id: str, depth=2) -> str:
    try:
        system_json = get_system_context(system_id)
        if system_json.startswith("Error"): return system_json
        system_data = json.loads(system_json); classifiers = {c["id"]: c for c in system_data.get("classifiers", [])}; relations = system_data.get("relations", [])
        def traverse(cid, current_path, current_depth):
            if current_depth > depth: return []
            paths = []; cls = classifiers.get(cid)
            if not cls: return []
            for attr in cls.get("data", {}).get("attributes", []): attr_name = attr.get("name"); paths.append(f"{current_path}{attr_name}".lstrip("."))
            for rel in relations:
                source_id = rel.get("source"); target_id = rel.get("target"); rel_name = rel.get("name", "").lower()
                if source_id == cid: new_path = f"{current_path}{rel_name}."; paths.extend(traverse(target_id, new_path, current_depth + 1))
            return paths
        return json.dumps(list(set(traverse(class_id, "", 0))))
    except Exception as e: return f"Error computing paths: {e}"

def get_interface_full_context(interface_id: str) -> str:
    try:
        iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS); iface_resp.raise_for_status(); iface = iface_resp.json(); system_id = iface.get("system"); system_ctx = _fetch_system_context_data(system_id) if system_id else {}; actor_id = iface.get("actor"); actor_name = None
        for classifier in _as_list(system_ctx.get("classifiers"), "classifiers"):
            if str(classifier.get("id")) == str(actor_id): actor_name = (classifier.get("data") or {}).get("name"); break
        system_ctx["workflow_plan"] = _workflow_plan(system_ctx, str(actor_id or ""), actor_name); system_ctx["usecase_navigation"] = _build_usecase_navigation(system_ctx, str(actor_id or ""), actor_name); iface_clean = {k: v for k, v in iface.items() if k != "data"}; iface_clean["actor_name"] = actor_name or iface.get("actor_name") or iface.get("actor")
        # Build an explicit modelâ†’attributes quick reference to prevent LLM from inventing field names
        attr_ref = {}
        for c in _as_list(system_ctx.get("classifiers"), "classifiers"):
            cdata = c.get("data") or {}
            cname = cdata.get("name", "")
            if cname and cdata.get("type") not in ("actor",):
                attr_ref[cname] = [a.get("name") for a in cdata.get("attributes", []) if a.get("name")]
        if os.environ.get("ADK_FULL_CONTEXT", "").lower() not in {"1", "true", "yes"}:
            current_data = iface.get("data") or {}
            usecase_navigation = system_ctx.get("usecase_navigation") or {}
            activity_steps = [
                {
                    "activity_node_id": step.get("activity_node_id"),
                    "activity_node_name": step.get("activity_node_name"),
                    "actor": step.get("actor"),
                    "page_name": step.get("page_name"),
                    "primary_models": step.get("primary_models", []),
                    "next_activity_node_ids": step.get("next_activity_node_ids", []),
                }
                for step in system_ctx.get("workflow_plan", [])
            ]
            nav_plan = usecase_navigation.get("nav_plan") or {}
            return json.dumps({
                "ATTRIBUTE_REFERENCE": {
                    "_note": "USE ONLY these exact field names as section attributes. DO NOT invent new names.",
                    "models": attr_ref,
                },
                "interface": iface_clean,
                "current_interface": {
                    "pages": current_data.get("pages", []),
                    "sections": current_data.get("sections", []),
                    "styling": current_data.get("styling", {}),
                },
                "usecase_navigation": {
                    "pages": usecase_navigation.get("pages", []),
                    "nav_bar_pages": usecase_navigation.get("nav_bar_pages", []),
                    "icon_actions": usecase_navigation.get("icon_actions", []),
                    "workflow_entry_points": usecase_navigation.get("workflow_entry_points", []),
                    "actor_permissions": usecase_navigation.get("actor_permissions", {}),
                    "nav_plan": {
                        "pages": nav_plan.get("pages", []),
                        "sections": nav_plan.get("sections", []),
                        "operations": nav_plan.get("operations", []),
                        "workflows": nav_plan.get("workflows", []),
                    },
                },
                "workflow_plan": activity_steps,
            }, separators=(",", ":"))
        return json.dumps({
            "ATTRIBUTE_REFERENCE": {
                "_note": "USE ONLY these exact field names as section attributes. DO NOT invent new names.",
                "models": attr_ref,
            },
            "interface": iface_clean,
            "system": system_ctx,
        }, indent=2)
    except Exception as e: return f"Error fetching full context: {e}"


def _norm_candidate_styling(styling, prompt_for_style: str) -> dict:
    if styling:
        if isinstance(styling, str):
            try: styling = json.loads(styling)
            except Exception: styling = {}
        styling = dict(styling)
        for old, new in (("accent_color", "accentColor"), ("background_color", "backgroundColor"), ("text_color", "textColor"), ("selected_style", "selectedStyle")):
            if old in styling and new not in styling: styling[new] = styling.pop(old)
        if isinstance(styling.get("radius"), str):
            styling["radius"] = {"none": 0, "sm": 4, "md": 8, "lg": 12, "xl": 16, "2xl": 24}.get(styling["radius"], 8)
    else:
        styling = {}
    overrides = _prompt_styling_overrides(prompt_for_style)
    return {**styling, **overrides} if overrides else styling


_STYLING_TOKEN_KEYS = frozenset({
    "region.header.bg_hex", "region.header.text_hex",
    "region.footer.bg_hex", "region.footer.text_hex",
    "region.main.bg_hex", "region.sidebar.bg_hex", "region.border_hex",
    "component.card.bg_hex", "component.card.border_hex",
    "button.primary.bg_hex", "button.primary.text_hex",
    "button.secondary.bg_hex", "button.secondary.text_hex",
    "button.ghost.text_hex", "button.danger.bg_hex", "button.link.text_hex",
    "nav.bg_hex", "nav.text_hex",
    "table.header.bg_hex", "table.header.text_hex",
    "badge.info.bg_hex", "text.muted.hex",
})

def _norm_candidate_tokens(tokens, prompt_for_style: str, prompt_intent: dict, styling: dict | None = None) -> dict:
    if not tokens:
        tokens = {}
    if isinstance(tokens, str):
        try: tokens = json.loads(tokens)
        except Exception: tokens = {}
    tokens = dict(tokens)
    # Pre-populate fine-grained overrides from styling so setdefault in
    # _apply_prompt_style_overrides can preserve the LLM's independent choices
    for key in _STYLING_TOKEN_KEYS:
        if key not in tokens and isinstance(styling, dict) and styling.get(key):
            tokens[key] = styling[key]
    tokens = _apply_prompt_style_overrides(tokens, prompt_for_style)
    if prompt_intent.get("colorIntent"):
        tokens = {**tokens, **prompt_intent["colorIntent"]}
    return tokens


def validate_and_save_candidate(
    interface_id: str,
    candidate_index: int,
    name: str,
    description: str,
    pages: str,
    sections: str,
    tokens: str = "",
    styling: str = "",
    prompt: str = "",
    derived_from: str = "",
    designer_requirements: str = "",
    variation_strategy: str = "",
) -> str:
    """Validate and save one interface candidate (call once per candidate index 0, 1, 2).

    Args:
        interface_id: The interface UUID (from the message).
        candidate_index: 0, 1, or 2.
        name: Short display name for this design direction (e.g. "Card-forward Commerce").
        description: One sentence describing this candidate's visual approach.
        pages: JSON string containing a list of page objects. Each page: {id, name, type, sections: [{value: section_id}, ...]}.
               type is required and must be {"value":"normal","label":"Normal"} or {"value":"activity","label":"Activity"}.
               Pages do NOT contain section data â€” they only reference section IDs.
        sections: JSON string containing a list of ALL section definition objects. Each section must have:
                  id, name, layout, position, col_span, primary_model, attributes, operations, style.
                  This is SEPARATE from pages. Both pages[] and sections[] are required.
        tokens: Optional JSON string with design tokens.
        styling: Optional JSON string with global styling overrides.
        prompt: Original user design prompt (optional, for logging).
        derived_from: Optional source candidate index/id when regenerating from a selected candidate.
        designer_requirements: Optional human-in-the-loop requirements used for regeneration.
        variation_strategy: Optional short label for how this candidate differs from the source.
    """
    try:
        if isinstance(pages, str): pages = json.loads(pages)
        if isinstance(sections, str): sections = json.loads(sections)
        input_section_ids = {str(s.get("id")) for s in (sections or []) if isinstance(s, dict) and s.get("id")}
        prompt_for_style = designer_requirements or prompt
        prompt_intent = compile_prompt_intent(prompt_for_style)
        styling_dict = _norm_candidate_styling(styling, prompt_for_style)

        iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS)
        iface_resp.raise_for_status()
        iface = iface_resp.json()
        system_id = iface.get("system")
        tokens_d: dict = _norm_candidate_tokens(tokens, prompt_for_style, prompt_intent, styling_dict)

        cls_resp = requests.get(f"{METADATA_API_BASE}/systems/{system_id}/classifiers/", headers=_AUTH_HEADERS)
        classifiers_data = cls_resp.json() if cls_resp.ok else {}
        raw_classifiers = classifiers_data.get("classifiers", []) if isinstance(classifiers_data, dict) else classifiers_data
        model_attrs: dict = {}; model_id_by_name: dict = {}
        for c in raw_classifiers:
            cdata = c.get("data", {}); cname = cdata.get("name", "")
            attrs = {a.get("name", "") for a in cdata.get("attributes", []) if a.get("name")}
            if cname:
                model_attrs[cname] = attrs
                model_id_by_name[cname] = str(c.get("id") or cdata.get("id") or cname)
        known_models = set(model_attrs.keys())

        usecase_navigation: dict = {}
        try:
            system_context = _fetch_system_context_data(system_id)
            actor_name = _actor_name_from_context(system_context, iface.get("actor"))
            usecase_navigation = _build_usecase_navigation(system_context, str(iface.get("actor") or ""), actor_name)
            pages = _ensure_usecase_pages(pages, usecase_navigation)
        except Exception:
            usecase_navigation = {}
        sections = _normalize_activity_action_sections(pages, sections)
        sections = _normalize_chrome_sections(sections)

        def _norm_model(n): return re.sub(r'[\s_-]', '', str(n or '')).lower()
        model_names_fuzzy = {_norm_model(m): m for m in known_models}
        def _canonical_model_name(name): return name if name in known_models else model_names_fuzzy.get(_norm_model(name), "")

        page_names = {p.get("name", "") for p in pages}
        page_ref_to_name: dict = {}
        for p in pages:
            pname, pid = p.get("name", ""), p.get("id", "")
            if pname: page_ref_to_name[pname] = pname; page_ref_to_name[pname.lower()] = pname
            if pid: page_ref_to_name[pid] = pname; page_ref_to_name[pid.lower()] = pname

        # Validate sections
        errors: list = []
        for s in sections:
            s["layout"] = _normalize_layout_alias(s.get("layout"))
            s["operations"] = _normalize_section_operations(s.get("operations"))
            s["component"] = _infer_section_component(s)
            sname, layout = s.get("name", "?"), s.get("layout", "")
            if layout and layout not in _VALID_SECTION_LAYOUTS:
                errors.append(f"section '{sname}': invalid layout '{layout}'")
            pm = s.get("primary_model", "")
            if pm and pm not in known_models:
                errors.append(f"section '{sname}': unknown primary_model '{pm}'")
            for attr in s.get("attributes", []):
                attr_name = attr.get("name", attr) if isinstance(attr, dict) else attr
                if "." in attr_name:
                    first, rest = attr_name.split(".", 1)
                    canon = _canonical_model_name(first)
                    if not canon: errors.append(f"section '{sname}': dot-notation prefix '{first}' not a known model")
                    elif rest not in model_attrs.get(canon, set()): errors.append(f"section '{sname}': related attribute '{rest}' not found on {canon}")
                elif pm and pm in model_attrs and attr_name and attr_name not in model_attrs[pm]:
                    errors.append(f"section '{sname}': attribute '{attr_name}' not found on {pm}")
            avail_attrs = {(attr.get("name", attr) if isinstance(attr, dict) else attr) for attr in s.get("attributes", [])}
            s["field_layout"] = _normalize_field_layout(s)
            for field_ref in _field_layout_field_refs(s.get("field_layout")):
                if field_ref not in avail_attrs:
                    errors.append(f"section '{sname}': field_layout references '{field_ref}' which is not in attributes")
            sp = (s.get("style") or {}).get("success_page", "")
            if sp and sp not in page_names:
                errors.append(f"section '{sname}': success_page '{sp}' not in pages")
            workflow = s.get("workflow") or {}
            workflow_action = workflow.get("action") or s.get("workflow_action", "")
            if workflow_action and workflow_action not in {"complete", "complete_then_page", "complete_then_target", "navigate", "none"}:
                errors.append(f"section '{sname}': invalid workflow.action '{workflow_action}'")
            workflow_target = workflow.get("target_page") or workflow.get("targetPage") or s.get("target_page") or s.get("targetPage") or ""
            if workflow_target and workflow_target in page_ref_to_name:
                workflow["target_page"] = page_ref_to_name[workflow_target]; s["workflow"] = workflow
            if workflow_target and workflow_target not in page_names:
                norm_wt = page_ref_to_name.get(str(workflow_target).lower())
                if norm_wt: workflow["target_page"] = norm_wt; s["workflow"] = workflow
                else: errors.append(f"section '{sname}': workflow target_page '{workflow_target}' not in pages")
            for field, valid_vals in _VALID_SECTION_STYLE.items():
                val = (s.get("style") or {}).get(field, "")
                if val and val not in valid_vals:
                    errors.append(f"section '{sname}': invalid style.{field} '{val}'")

        # Auto-correct sections
        fixed_sections = []
        for s in sections:
            s = dict(s)
            s["layout"] = _normalize_layout_alias(s.get("layout"))
            s["operations"] = _normalize_section_operations(s.get("operations"))
            s["component"] = _infer_section_component(s)
            pm = s.get("primary_model", "")
            if pm and pm not in model_attrs:
                canon = model_names_fuzzy.get(_norm_model(pm))
                if canon: s["primary_model"] = s["class"] = pm = canon
            if pm and pm in model_attrs:
                new_attrs: list = []; attr_renames: dict = {}
                for attr in s.get("attributes", []):
                    attr_name = attr.get("name", attr) if isinstance(attr, dict) else attr
                    if "." in attr_name:
                        first, rest = attr_name.split(".", 1)
                        canon = _canonical_model_name(first)
                        if canon and rest in model_attrs.get(canon, set()):
                            norm = dict(attr) if isinstance(attr, dict) else {"name": attr_name}
                            canon_attr = f"{canon}.{rest}"
                            norm["name"] = canon_attr
                            norm.setdefault("source", "related"); norm.setdefault("readonly", True)
                            if canon_attr != attr_name: attr_renames[attr_name] = canon_attr
                            new_attrs.append(norm)
                    elif not pm or attr_name in model_attrs.get(pm, set()):
                        new_attrs.append(attr)
                if not new_attrs and s.get("layout") in _DATA_SECTION_LAYOUTS:
                    new_attrs = list(_model_field_names(model_attrs, pm, 6))
                s["attributes"] = new_attrs
                if attr_renames and isinstance(s.get("field_layout"), dict):
                    def _rename_fl(v):
                        if isinstance(v, str): return attr_renames.get(v, v)
                        if isinstance(v, list): return [_rename_fl(i) for i in v]
                        if isinstance(v, dict): return {k: _rename_fl(i) for k, i in v.items()}
                        return v
                    s["field_layout"] = {k: _rename_fl(v) for k, v in (s.get("field_layout") or {}).items()}
            s["field_layout"] = _normalize_field_layout(s)
            fixed_sections.append(s)
        for s in fixed_sections:
            if s.get("layout") in _DATA_SECTION_LAYOUTS:
                style = dict(s.get("style") or {})
                if not style.get("color") or style["color"] in {"blue", "green", "purple"}:
                    style["color"] = "accent"; s["style"] = style

        # Auto-correct pages
        fixed_pages = []
        for i, p in enumerate(pages):
            p = dict(p)
            p["type"] = _canonical_page_type(_infer_page_type_value(p))
            if not p.get("id"): p["id"] = f"page_{candidate_index}_{i}"
            p.setdefault("category", None)
            fixed_pages.append(p)
        for i, s in enumerate(fixed_sections):
            if not s.get("id"):
                model = (s.get("primary_model") or "chrome").lower().replace(" ", "_")
                fixed_sections[i] = {**s, "id": f"{model}_{s.get('layout', 'section')}_{candidate_index}_{i}"}
            if not fixed_sections[i].get("name"):
                fixed_sections[i]["name"] = fixed_sections[i]["id"]

        fixed_pages = _ensure_usecase_pages(fixed_pages, usecase_navigation)
        for s in fixed_sections:
            s["operations"] = _normalize_section_operations(s.get("operations"))
            s["component"] = _infer_section_component(s)
            s["field_layout"] = _normalize_field_layout(s)
        fixed_sections = _normalize_chrome_sections(fixed_sections)
        # fixed_pages, fixed_sections = _ensure_candidate_content_structure(
        #     fixed_pages,
        #     fixed_sections,
        #     model_attrs,
        #     int(candidate_index or 0),
        #     prompt_for_style,
        #     add_missing_content=False,
        # )
        fixed_sections = _apply_nav_methods(fixed_pages, fixed_sections, usecase_navigation)
        fixed_pages, fixed_sections, tokens_d, styling_d = apply_hard_constraints(fixed_pages, fixed_sections, tokens_d or {}, styling_dict or {}, prompt_intent)
        # fixed_pages, fixed_sections = _apply_candidate_region_composition(
        #     fixed_pages, fixed_sections, int(candidate_index or 0), prompt_for_style,
        #     preserve_layout=(derived_from != "" and not _prompt_requests_layout_change(prompt_for_style)),
        # )
        fixed_pages, fixed_sections = _dedupe_agent_header_shells(fixed_pages, fixed_sections)
        fixed_sections = _finalize_data_section_bindings(fixed_sections, model_attrs)
        for s in fixed_sections:
            s["component"] = _infer_section_component(s)
        auto_allowed_layouts = (
            _HEADER_TEMPLATE_LAYOUTS
            | _FOOTER_TEMPLATE_LAYOUTS
            | _HEADER_NAV_LAYOUTS
            | {"site-nav", "nav-links", "nav-bar", "activity_action", "activity_start", "activity_tasks"}
        )
        fixed_sections = [
            s for s in fixed_sections
            if str(s.get("id") or "") in input_section_ids
            or _normalize_layout_alias(s.get("layout")) in auto_allowed_layouts
            or s.get("position") in {"header", "footer"}
        ]

        # Normalize section refs and assign sections to pages that have none
        for i, p in enumerate(fixed_pages):
            if p.get("sections") is not None:
                fixed_pages[i] = {**p, "sections": [r if isinstance(r, dict) else {"value": r} for r in p["sections"]]}
        assignable = [s for s in fixed_sections if s.get("position", "main") not in {"header", "hero", "footer", "sidebar"} and s.get("layout") in {"card", "list", "table", "detail", "gallery", "form"}]
        if any(not p.get("sections") for p in fixed_pages) and assignable:
            model_to_secs: dict = defaultdict(list)
            for s in assignable: model_to_secs[s.get("primary_model", "")].append(s["id"])
            rebuilt: list = []; model_assigned: dict = defaultdict(int)
            for p in fixed_pages:
                if p.get("sections"): rebuilt.append(p); continue
                if _page_type_value(p) == "activity" or "workflow" in f"{p.get('id', '')} {p.get('name', '')}".lower():
                    rebuilt.append(p); continue
                pm = p.get("primary_model", "")
                cands = model_to_secs.get(pm, []); start = model_assigned[pm]
                assigned = [{"value": cands[start]}] if start < len(cands) else []
                if assigned: model_assigned[pm] += 1
                if not assigned and model_to_secs.get("", []):
                    fb = model_to_secs[""]
                    if model_assigned[""] < len(fb):
                        assigned = [{"value": fb[model_assigned[""]]}]; model_assigned[""] += 1
                rebuilt.append({**p, "sections": assigned})
            fixed_pages = rebuilt

        section_ids = {s["id"] for s in fixed_sections}
        for p in fixed_pages:
            p["sections"] = [ref for ref in (p.get("sections") or []) if _ref_id(ref) in section_ids]
        fixed_pages = _assign_default_page_categories(fixed_pages, fixed_sections, model_id_by_name)

        canonical_schema = {"version": 1, "pages": fixed_pages, "sections": fixed_sections, "tokens": tokens_d or {}, "styling": styling_d or {}, "prompt_intent": prompt_intent}
        data = dict(iface.get("data") or {})
        data["categories"] = _merge_page_categories(data.get("categories") or [], fixed_pages)
        candidates = list(data.get("candidates") or [])
        candidate = {
            "id": f"c{candidate_index}", "name": name, "description": description,
            "pages": fixed_pages, "sections": fixed_sections,
            "generated_by": "gemini_make_agent", "prompt": prompt or designer_requirements,
            "prompt_intent": prompt_intent, "canonical_schema": canonical_schema, "fallback": False,
            **({"tokens": tokens_d} if tokens_d else {}),
            **({"styling": styling_d} if styling_d else {}),
        }
        if derived_from != "": candidate["derived_from"] = derived_from
        if designer_requirements: candidate["designer_requirements"] = designer_requirements
        if variation_strategy: candidate["variation_strategy"] = variation_strategy
        while len(candidates) <= candidate_index: candidates.append(None)
        candidates[candidate_index] = candidate
        data["candidates"] = candidates
        payload = {"id": interface_id, "name": iface["name"], "description": iface.get("description", ""), "system_id": system_id, "actor_id": iface.get("actor"), "data": data}
        requests.put(f"{METADATA_API_BASE}/interfaces/{interface_id}/", json=payload, headers=_AUTH_HEADERS).raise_for_status()
        return f"OK: candidate {candidate_index} '{name}' saved successfully."
    except Exception as e:
        return f"Error saving candidate: {e}"

def get_candidate_regeneration_context(interface_id: str, candidate_index: int, designer_requirements: str = "") -> str:
    """Return the selected candidate as the baseline for human-guided regeneration."""
    try:
        iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS, timeout=30)
        iface_resp.raise_for_status()
        iface = iface_resp.json()
        data = dict(iface.get("data") or {})
        candidates = list(data.get("candidates") or [])
        idx = int(candidate_index)
        regeneration_base = data.get("regeneration_base_candidate") or {}
        if idx < 0 or idx >= len(candidates) or not candidates[idx]:
            if int(regeneration_base.get("selected_candidate_index", -1)) != idx or not regeneration_base.get("candidate"):
                return f"ERROR: candidate {candidate_index} not found."
            base = dict(regeneration_base.get("candidate") or {})
        else:
            base = dict(candidates[idx])
        context = {
            "interface_id": interface_id,
            "selected_candidate_index": idx,
            "designer_requirements": designer_requirements,
            "regeneration_contract": {
                "overwrite_candidate_indices": [0, 1, 2],
                "derive_from_selected_candidate": True,
                "preserve_page_semantics": True,
                "preserve_workflow_sections": [
                    "activity_start",
                    "activity_tasks",
                    "activity_action",
                ],
                "keep_task_pages_as_activity_pages": True,
                "keep_normal_pages_as_normal_pages": True,
            },
            "current_interface": {
                "name": iface.get("name"),
                "description": iface.get("description", ""),
                "system": iface.get("system"),
                "actor": iface.get("actor"),
            },
            "base_candidate": {
                "id": base.get("id"),
                "name": base.get("name"),
                "description": base.get("description", ""),
                "pages": base.get("pages", []),
                "sections": base.get("sections", []),
                "tokens": base.get("tokens", data.get("tokens", {})),
                "styling": base.get("styling", data.get("styling", {})),
                "variation_strategy": base.get("variation_strategy"),
            },
        }
        return json.dumps(context, indent=2)
    except Exception as e:
        return f"Error fetching candidate regeneration context: {e}"

def _candidate_variant_name(prompt: str, index: int) -> str:
    color_name, _ = _prompt_color_theme(prompt)
    prefix = (color_name or "Agent").replace("_", " ").title()
    suffixes = ("Card Gallery", "Data Table", "Showcase")
    return f"{prefix} {suffixes[index % len(suffixes)]}"

def _prompt_layout_traits(prompt: str) -> dict:
    text = str(prompt or "").lower()
    return {
        "full": any(term in text for term in ("full width", "full-width", "edge to edge", "edge-to-edge", "full bleed", "full-bleed")),
        "wide": any(term in text for term in ("wide", "wider", "wide main", "wide content")),
        "contained": any(term in text for term in ("contained", "narrow", "centered", "center aligned")),
        "dashboard": any(term in text for term in ("dashboard", "admin", "analytics", "operational", "dense")),
        "sidebar": any(term in text for term in ("sidebar", "side nav", "left nav", "right nav", "rail")),
        "right_sidebar": any(term in text for term in ("right sidebar", "sidebar right", "right nav", "right rail")),
        "minimal": any(term in text for term in ("minimal", "clean", "simple", "focused")),
        "form": any(term in text for term in ("form", "wizard", "application", "onboarding")),
    }

def _page_layout_dict(page: dict) -> dict:
    raw = page.get("layout") or {}
    if isinstance(raw, dict):
        out = dict(raw)
    elif raw:
        out = {"value": raw}
    else:
        out = {"value": "default"}
    return out

def _prompt_requests_layout_change(prompt: str) -> bool:
    text = str(prompt or "").lower()
    # Unambiguous layout terms always count
    if any(term in text for term in (
        "layout", "æŽ’ç‰ˆ", "å¸ƒå±€", "region", "sidebar", "side bar", "left nav", "right nav",
        "split", "rail", "å·¦ä¾§", "å³ä¾§", "ä¾§è¾¹æ ", "full width", "full-width",
        "wide", "contained", "compact", "dense", "spacious", "table", "gallery", "list",
        "detail", "details", "form", "filter",
    )):
        return True
    # "nav", "header", "footer" etc. also appear in color requests ("change header color").
    # Only treat them as layout requests when there is no color context in the prompt.
    color_context = any(c in text for c in (
        "color", "colour", "é¡”è‰²", "é¢œè‰²", "èƒŒæ™¯", "background", "#", "hex",
        "red", "blue", "sky", "cyan", "aqua", "teal", "turquoise", "green", "emerald", "lime",
        "purple", "violet", "indigo", "orange", "yellow", "amber", "gold", "pink", "rose",
        "navy", "brown", "beige", "tan", "cream",
        "ç™½", "é»‘", "ç°", "çº¢", "è“", "ç»¿", "ç´«", "æ©™", "é»„", "ç²‰",
        "white", "black", "grey", "gray", "slate", "zinc", "neutral",
    ))
    if color_context:
        return False
    return any(term in text for term in (
        "nav", "navigation", "navbar", "header", "footer", "hero", "main", "wide",
        "list", "detail", "form", "filter", "contained",
        "card", "å¯¼èˆª", "é¡µå¤´", "é¡µè„š",
    ))

def _is_content_region_section(section: dict) -> bool:
    layout = _normalize_layout_alias(section.get("layout"))
    if layout in _CHROME_TEMPLATE_LAYOUTS or layout in {"activity_action", "activity_start", "activity_tasks"}:
        return False
    if section.get("position") in {"header", "footer"}:
        return False
    return layout in {"card", "list", "table", "detail", "gallery", "filter", "form"} and (
        section.get("primary_model") or section.get("attributes") or section.get("role") in {"data", "collection", "summary", "filter"}
    )

def _apply_candidate_region_composition(pages: list, sections: list, candidate_index: int, prompt: str = "", preserve_layout: bool = False) -> tuple[list, list]:
    """Give first-generation candidates meaningfully different region placement.

    Regeneration keeps the selected candidate's section placement unless the user
    explicitly asks for layout/chrome/region changes.
    """
    if preserve_layout:
        return pages, sections
    pages = copy.deepcopy(pages or [])
    sections = copy.deepcopy(sections or [])
    section_map = {str(s.get("id")): s for s in sections if s.get("id")}
    normal_pages = [p for p in pages if _page_type_value(p) != "activity"]
    if not normal_pages:
        return pages, sections

    # Work page-by-page so a candidate keeps each page's domain content, but the
    # regions differ across candidates. Never move the only content section off main.
    for page in normal_pages:
        refs = [_ref_id(ref) for ref in (page.get("sections") or []) if _ref_id(ref)]
        content_ids = [sid for sid in refs if _is_content_region_section(section_map.get(sid) or {})]
        if len(content_ids) < 2:
            continue
        idx = int(candidate_index or 0) % 3
        if idx == 0:
            # Editorial/executive direction: one lead section in hero, the rest in main.
            hero_id = content_ids[0]
            hero = section_map.get(hero_id)
            if hero and hero.get("layout") not in {"table", "form", "filter"}:
                style = dict(hero.get("style") or {})
                hero["position"] = "hero"
                hero["col_span"] = 12
                style.setdefault("surface_level", "elevated")
                style.setdefault("text_class", "si-text-display")
                hero["style"] = style
        elif idx == 1:
            # Operational direction: left rail for filters/summaries/navigation, main for work.
            sidebar_id = next(
                (sid for sid in content_ids if (section_map.get(sid) or {}).get("layout") in {"filter", "detail", "card", "list"}),
                content_ids[0],
            )
            sidebar = section_map.get(sidebar_id)
            if sidebar:
                style = dict(sidebar.get("style") or {})
                sidebar["position"] = "sidebar"
                sidebar["col_span"] = 12
                if sidebar.get("layout") in {"table", "gallery", "form"}:
                    sidebar["layout"] = "list"
                    sidebar["component"] = _component_for_layout(sidebar, "list")
                style["sidebar_side"] = "left"
                style["sidebar_width"] = 3
                style.setdefault("bg", "white")
                style.setdefault("shadow", "sm")
                sidebar["style"] = style
        else:
            # Showcase/detail direction: hero lead plus a right utility/detail rail.
            hero_id = content_ids[0]
            right_id = content_ids[-1] if content_ids[-1] != hero_id else ""
            hero = section_map.get(hero_id)
            if hero and hero.get("layout") not in {"table", "form", "filter"}:
                style = dict(hero.get("style") or {})
                hero["position"] = "hero"
                hero["col_span"] = 12
                style.setdefault("surface_level", "elevated")
                style.setdefault("text_class", "si-text-display")
                hero["style"] = style
            right = section_map.get(right_id) if right_id else None
            if right:
                style = dict(right.get("style") or {})
                right["position"] = "sidebar"
                right["col_span"] = 12
                if right.get("layout") in {"table", "gallery", "form"}:
                    right["layout"] = "list"
                    right["component"] = _component_for_layout(right, "list")
                style["sidebar_side"] = "right"
                style["sidebar_width"] = 3
                style.setdefault("bg", "white")
                style.setdefault("shadow", "md")
                right["style"] = style

    # Keep at least one data/work section in main on every normal page.
    for page in normal_pages:
        refs = [_ref_id(ref) for ref in (page.get("sections") or []) if _ref_id(ref)]
        content = [section_map.get(sid) for sid in refs if _is_content_region_section(section_map.get(sid) or {})]
        if content and not any((s or {}).get("position", "main") == "main" for s in content):
            content[-1]["position"] = "main"
            content[-1]["col_span"] = 12
    return pages, sections

# â”€â”€ LLM-first candidate generation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_LAYOUT_SCHEMA = """
=== SECTION FIELDS ===
layout: "card"|"list"|"table"|"detail"|"gallery"|"filter"|"form"
        |"activity_action"|"activity_start"|"activity_tasks"
        |"promo-bar"|"logo"|"search-bar"|"icon-actions"|"nav-links"
        |"site-nav"|"main-header"|"minimal-header"|"commerce-header"
        |"dashboard-header"|"split-header"|"app-header"|"compact-header"
        |"mega-header"|"hero-header"|"tabbed-header"|"glass-header"
        |"command-header"
        |"service-bar"|"link-grid"|"brand-strip"|"site-footer"
        |"compact-footer"|"legal-footer"|"newsletter-footer"|"social-footer"
        |"mega-footer"|"split-footer"|"app-footer"|"cta-footer"|"minimal-footer"

component: match to layout:
  table â†’ DataTable
  card â†’ CardGrid | ProductCardGrid | PersonCardGrid | ObjectCardGrid | ImageCard | ImageCardGrid | CategoryTileGrid
  list â†’ ObjectList | LineItemList | RelatedObjectList
  detail â†’ DetailPanel | ProductDetailPanel
  gallery â†’ ImageCardGrid | ObjectCardGrid
  form â†’ ObjectForm
  filter â†’ (keep existing or use ObjectForm)
  site-nav â†’ NavBar
  site-footer â†’ SiteFooter
  logo â†’ Logo | BrandLockup | ImageLogo
  search-bar â†’ SearchBar
  icon-actions â†’ IconActions
  nav-links â†’ NavBar
  header templates â†’ HeaderTemplate
  footer templates â†’ FooterTemplate

position: "main"|"sidebar"|"header"|"hero"|"footer"
col_span: 12|6|4|3

style (include only relevant keys):
  color: "accent"|"accent-secondary"|"blue"|"green"|"purple"|"orange"|"rose"|"slate"
         (use "accent" for all data sections; use specific colors for chrome/decorative)
  density: "compact"|"normal"|"spacious"
  columns: "1"|"2"|"3"|"4"          (card/gallery only)
  display_mode: "grid"|"carousel"|"banner"  (card only)
  card_style: "default"|"product"|"category"|"compact"
  list_style: "default"|"product"|"cart-item"|"related"
  form_style: "default"|"auth"|"step"|"summary"
  image_position: "left"|"top"|"right"    (detail only)
  image_size: "sm"|"md"|"lg"             (detail only)
  image_ratio: "wide"|"16:9"|"4:3"|"1:1"
  banner_height: "sm"|"md"|"lg"|"xl"
  shadow: "none"|"sm"|"md"|"lg"
  border: "none"|"light"|"colored"
  bg: "white"|"light"|"dark"|"transparent"
  header_style: "default"|"large"|"hidden"
  nav_height: "compact"|"normal"|"tall"|"xl"   (nav/header sections)
  sidebar_side: "left"|"right"                 (sidebar sections only)
  sidebar_width: 2..6                          (sidebar sections only)
  logo_size: "sm"|"md"|"lg"|"xl"
  logo_shape: "rounded"|"circle"|"square"
  logo_variant: "lockup"|"image-only"|"text-only"   (logo sections: lockup=icon+text, image-only=icon only, text-only=text only)
  logo_url: image URL string (only if user asked for logo image)
  image_url: image URL string (only for ImageCard/banner)
  cta_label: button text string e.g. "Save" | "Submit" | "Continue"  (form sections)
  login_label: auth submit button label (form_style="auth") e.g. "Sign in" | "Log in"
  step_icon: emoji or "" for step header icon (form_style="step") e.g. "ðŸ“‹" | "ðŸ’³"
  total_label: label for total row (form_style="summary") e.g. "Total" | "Order total"
  seller_label: e.g. "Sold by" (card/list sections â€” empty string to hide)
  availability_label: e.g. "In stock" | "Out of stock" (card/list/detail â€” empty string to hide)
  delivery_label: e.g. "Free delivery" | "Ships in 2-3 days" (card/list/detail â€” empty string to hide)
  action_variant: "link"|"ghost"|"button"  (icon-actions sections: how action items are styled)
  show_logout: true|false                  (icon-actions sections: show/hide logout link)
  logout_label: string e.g. "Sign out"    (icon-actions sections: label for logout link)
  variant: "button"|"link"|"fab"|"wizard_next"|"auto"  (activity_action sections only: visual style of the action)
  align: "left"|"center"|"right"                       (activity_action sections only)
  size: "sm"|"md"|"lg"                                 (activity_action sections only)

=== PAGE FIELDS ===
layout.value: "vertical"|"horizontal"|"vertical-reverse"|"horizontal-reverse"
layout.main_width: "contained"|"wide"|"full"
layout.header_width: "contained"|"full"
layout.hero_width: "contained"|"full"
layout.footer_width: "contained"|"full"
gap.value: "compact"|"normal"|"spacious"

=== GLOBAL STYLING (one set per candidate) ===
fontFamily: "inter"|"roboto"|"poppins"|"playfair"|"mono"|"geist"
textSize: "xs"|"sm"|"md"|"lg"|"xl"
  xs = body 13px, ultra-compact data-dense
  sm = body 14px, compact dashboard
  md = body 16px, default balanced
  lg = body 18px, readable/spacious
  xl = body 20px, large/editorial/accessibility
accentColor: hex e.g. "#2563eb"
accentSecondary: hex e.g. "#60a5fa"
backgroundColor: hex e.g. "#ffffff"
textColor: hex e.g. "#111827"
radius: 0|4|8|16|24
buttonStyle: "solid"|"outline"|"ghost"|"gradient"
cardHover: "lift"|"glow"|"border"|"none"
imageRatio: "1:1"|"4:3"|"16:9"|"portrait"|"wide"
divider: "none"|"line"|"shadow"|"wave"
pageMaxWidth: "sm"|"md"|"lg"|"xl"|"2xl"|"full"

Fine-grained color overrides (hex â€” set independently from accentColor/backgroundColor to establish visual hierarchy):
  region.header.bg_hex: hex â€” header bar background (default = accentColor; MUST differ from accentColor per COLOR HIERARCHY rule)
  region.header.text_hex: hex â€” header text/icon color (default = auto contrast on header bg)
  region.footer.bg_hex: hex â€” footer background (default = backgroundColor)
  region.footer.text_hex: hex â€” footer text color
  region.main.bg_hex: hex â€” main content area background
  region.sidebar.bg_hex: hex â€” sidebar background (when nav is in sidebar position)
  region.border_hex: hex â€” default divider / border color
  component.card.bg_hex: hex â€” card tile background
  component.card.border_hex: hex â€” card border color
  button.primary.bg_hex: hex â€” primary button fill (default = accentColor)
  button.primary.text_hex: hex â€” primary button label color (default = auto contrast)
  button.secondary.bg_hex: hex â€” secondary button fill (default = surface)
  button.secondary.text_hex: hex â€” secondary button label color
  button.ghost.text_hex: hex â€” ghost/text button color (default = accentColor)
  button.danger.bg_hex: hex â€” danger/destructive button fill (default = #dc2626; use orange or deep red for softer themes)
  button.link.text_hex: hex â€” inline link color (default = accentColor)
  nav.bg_hex: hex â€” nav bar/sidebar background (default = region.header.bg_hex)
  nav.text_hex: hex â€” nav links/icon color (default = auto contrast on nav bg)
  table.header.bg_hex: hex â€” table column header background
  table.header.text_hex: hex â€” table column header text color
  badge.info.bg_hex: hex â€” info/status badge background (default = accentColor)
  text.muted.hex: hex â€” secondary/muted text color used in labels, captions, table headers

=== ROLE â†’ LAYOUT (non-negotiable, must match exactly) ===
role='object_collection'       â†’ layout: table|card|gallery|list  (per candidate direction)
role='child_collection'        â†’ same as object_collection
role='object_detail'           â†’ layout: detail,  component: DetailPanel or ProductDetailPanel
role='object_summary'          â†’ layout: detail,  component: DetailPanel
role='object_form'             â†’ layout: form,    component: ObjectForm
role='navigation'              â†’ layout: site-nav, component: NavBar
role='header'                  â†’ layout: any header template (app-header, glass-header, minimal-header, compact-header, dashboard-header, split-header, hero-header, tabbed-header, command-header)
role='footer'                  â†’ layout: any footer template (site-footer, compact-footer, app-footer, minimal-footer, mega-footer, cta-footer)
activity_action/activity_start/activity_tasks â†’ keep layout unchanged (chrome); other sections on activity pages â†’ infer: select/chooseâ†’ card, enter/fillâ†’ form, review/confirmâ†’ detail

=== RULES ===
- nav/header chrome sections â†’ position="header" (or "sidebar" for sidebar nav)
- footer chrome sections â†’ position="footer"
- hero sections â†’ position="hero", col_span=12
- sidebar sections â†’ must include style.sidebar_side and style.sidebar_width
- Every page MUST have navigation (header nav OR sidebar NavBar)
- Data sections: color="accent" unless the design direction specifies otherwise
- Activity chrome (activity_action/activity_start/activity_tasks): keep layout as-is; content sections: infer layout from step name
"""

_CANDIDATE_FULL_SCHEMA = f"""\nYou output layout + style decisions for an interface. DO NOT change: id, name, primary_model, class, attributes, operations, role, behavior, data_source, query, field_layout.

{_LAYOUT_SCHEMA}
- 3 candidates must be structurally different: vary page main_width, nav placement, data section layouts, density, font, accent color
"""


def _llm_generate_3_candidates(pages: list, sections: list, prompt: str) -> list | None:
    """Call Gemini to generate 3 layout/style variants. Returns list of 3 candidate dicts or None on failure."""
    try:
        import google.genai as _genai
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        client = _genai.Client(api_key=api_key)

        # Skeleton: semantic context only, no current layout values (avoids LLM anchoring to old state)
        section_skeleton = [
            {
                "id": s.get("id", ""),
                "name": s.get("name", ""),
                "primary_model": s.get("primary_model", ""),
                "role": s.get("role", ""),
            }
            for s in sections if s.get("id")
        ]
        page_skeleton = [
            {"id": p.get("id", ""), "name": p.get("name", ""), "type": p.get("type", "")}
            for p in pages if p.get("id")
        ]

        diversity_rules = (
            "Generate exactly 3 structurally and visually distinct candidates.\n"
            "MANDATORY color assignment - each candidate MUST use a different color family unless user requires otherwise:\n"
            "  Candidate 0: DARK/NEUTRAL palette - accentColor from #1e293b #0f172a #1d4ed8 #0369a1 #1e3a5f; backgroundColor #0f172a or #111827; textColor #f1f5f9\n"
            "  Candidate 1: VIBRANT/COLORFUL palette - accentColor from #7c3aed #0891b2 #059669 #dc2626 #d97706; backgroundColor #ffffff or #f8fafc; textColor #111827\n"
            "  Candidate 2: WARM/EDITORIAL palette - accentColor from #ea580c #d97706 #be185d #9333ea #b45309; backgroundColor #fffbeb or #fdf4ff or #fff7ed; textColor #1c1917\n"
            "Each candidate MUST also differ all of these axes unless user requires otherwise:\n"
            "  - data section layout (table vs card vs gallery vs list)\n"
            "  - nav placement (header top bar vs left sidebar vs right sidebar)\n"
            "  - page width (contained vs wide vs full)\n"
            "  - density (compact vs normal vs spacious)\n"
            "  - typography (fontFamily + textSize â€” inter/roboto/poppins/playfair/mono + xs/sm/md/lg/xl)\n"
            "  - border radius (0 vs 8 vs 16 vs 24)\n"
            "  - button style (solid vs outline vs ghost vs gradient)\n"
            "Every page must have navigation unless user requires otherwise.\n"
            "Respect the designer prompt - if it specifies a color, apply it to all 3 but still vary backgroundColor/textColor/accentSecondary.\n"
            "Keep object_form -> form, object_detail -> detail, activity_* layouts unchanged.\n"
            "COLOR SCOPING: Match color changes to their scope - use region.header.bg_hex for header, region.footer.bg_hex for footer, backgroundColor for page background. Only change accentColor when buttons/brand/primary color is explicitly the target. Never use accentColor to color a single region.\n"
            "COLOR HIERARCHY (mandatory for every candidate): region.header.bg_hex, accentColor, and backgroundColor must be visually distinct — do not assign the same hex to all three. accentColor is for interactive elements only (buttons, links, highlights), not for large background regions."
        )

        user_prompt_text = (
            f"Pages: {json.dumps(page_skeleton, ensure_ascii=False)}\n"
            f"Sections: {json.dumps(section_skeleton, ensure_ascii=False)}\n\n"
            f"DESIGNER PROMPT: {prompt or '(no specific requirements â€” explore freely)'}\n\n"
            f"{diversity_rules}\n\n"
            "Output exactly 3 candidates as JSON. Use ONLY the section/page ids provided above.\n"
            '{"candidates": [{"name": "...", "pages": [{"id": "...", "layout": {"value": "vertical", "main_width": "...", "header_width": "...", "footer_width": "..."}, "gap": {"value": "..."}}], '
            '"sections": [{"id": "...", "layout": "...", "component": "...", "position": "...", "col_span": 12, "style": {"color": "accent", "density": "...", "columns": "...", "shadow": "...", "bg": "...", "nav_height": "...", "sidebar_side": "...", "sidebar_width": 3}}], '
            '"styling": {"fontFamily": "...", "textSize": "xs|sm|md|lg|xl", "accentColor": "#hex", "accentSecondary": "#hex", "backgroundColor": "#hex", "textColor": "#hex", "radius": 8, "buttonStyle": "...", "cardHover": "...", "divider": "...", "pageMaxWidth": "...", "region.header.bg_hex": "#hex or omit", "region.header.text_hex": "#hex or omit", "region.footer.bg_hex": "#hex or omit", "region.footer.text_hex": "#hex or omit", "region.main.bg_hex": "#hex or omit", "region.sidebar.bg_hex": "#hex or omit", "region.border_hex": "#hex or omit", "component.card.bg_hex": "#hex or omit", "component.card.border_hex": "#hex or omit", "button.primary.bg_hex": "#hex or omit", "button.primary.text_hex": "#hex or omit", "button.secondary.bg_hex": "#hex or omit", "button.secondary.text_hex": "#hex or omit", "button.ghost.text_hex": "#hex or omit", "button.danger.bg_hex": "#hex or omit", "button.link.text_hex": "#hex or omit", "nav.bg_hex": "#hex or omit", "nav.text_hex": "#hex or omit", "table.header.bg_hex": "#hex or omit", "table.header.text_hex": "#hex or omit", "badge.info.bg_hex": "#hex or omit", "text.muted.hex": "#hex or omit"}}]}'
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_prompt_text,
            config={
                "system_instruction": f"You are a UI designer creating 3 structurally and visually distinct interface layout candidates. Follow the schema and role rules exactly.\n\n{_CANDIDATE_FULL_SCHEMA}",
                "response_mime_type": "application/json",
                "max_output_tokens": 65536,
            },
        )
        print(f"[llm_generate_3_candidates] raw response:\n{response.text}", flush=True)
        result = json.loads(response.text)
        # LLM sometimes returns the array directly instead of {"candidates": [...]}
        if isinstance(result, list):
            candidates = result
        else:
            candidates = result.get("candidates") or []
        if len(candidates) < 3:
            print(f"[llm_generate_3_candidates] only got {len(candidates)} candidates, falling back", flush=True)
            return None
        return candidates[:3]
    except Exception as e:
        import traceback
        print(f"[llm_generate_3_candidates] failed: {e}\n{traceback.format_exc()}", flush=True)
        return None


def _llm_regenerate_3_candidates(pages: list, sections: list, designer_requirements: str, base_styling: dict) -> list | None:
    """Like _llm_generate_3_candidates but anchored to the selected candidate's existing layout and styling."""
    try:
        import google.genai as _genai
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        client = _genai.Client(api_key=api_key)

        # Include current layout as context so LLM knows what to preserve vs. what to vary
        section_skeleton = [
            {
                "id": s.get("id", ""),
                "name": s.get("name", ""),
                "primary_model": s.get("primary_model", ""),
                "role": s.get("role", ""),
                "current_layout": s.get("layout", ""),
                "current_component": s.get("component", ""),
                "current_position": s.get("position", ""),
            }
            for s in sections if s.get("id")
        ]
        page_skeleton = [
            {
                "id": p.get("id", ""),
                "name": p.get("name", ""),
                "current_main_width": (p.get("layout") or {}).get("main_width", "contained"),
                "current_header_width": (p.get("layout") or {}).get("header_width", "contained"),
            }
            for p in pages if p.get("id")
        ]

        base_ctx = ", ".join(
            f"{k}={v}" for k, v in {
                "fontFamily": base_styling.get("fontFamily", "inter"),
                "textSize": base_styling.get("textSize", "md"),
                "accentColor": base_styling.get("accentColor", "#2563eb"),
                "backgroundColor": base_styling.get("backgroundColor", "#f9fafb"),
                "textColor": base_styling.get("textColor", "#111827"),
                "radius": base_styling.get("radius", 8),
                "buttonStyle": base_styling.get("buttonStyle", "solid"),
                "cardHover": base_styling.get("cardHover", "none"),
            }.items()
        )

        diversity_rules = (
            "Generate exactly 3 meaningfully different refinements of the base candidate.\n"
            "Each variant MUST differ from the others on at least 2 of these axes:\n"
            "  - color palette (accentColor, backgroundColor, textColor)\n"
            "  - typography (fontFamily, textSize)\n"
            "  - density (compact vs normal vs spacious)\n"
            "  - border radius (0 vs 8 vs 16 vs 24)\n"
            "  - button style (solid vs outline vs ghost vs gradient)\n"
            "  - card hover effect (lift vs glow vs border vs none)\n"
            "  - page width (contained vs wide vs full)\n"
            "  - nav placement (header vs sidebar)\n"
            "Apply the DESIGNER REQUIREMENTS to all 3 variants. "
            "Preserve the base candidate's section roles and data bindings. "
            "You may change layout/component/position for collection sections (object_collection, child_collection) "
            "but must keep object_form as form, object_detail as detail, activity_* layouts unchanged.\n"
            "COLOR SCOPING: Match color changes to their scope — use region.header.bg_hex for header, region.footer.bg_hex for footer, backgroundColor for page background. Only change accentColor when buttons/brand/primary color is explicitly the target. Never use accentColor to color a single region.\n"
            "COLOR HIERARCHY (mandatory for every candidate): region.header.bg_hex, accentColor, and backgroundColor must be visually distinct — do not assign the same hex to all three. accentColor is for interactive elements only (buttons, links, highlights), not for large background regions."
        )

        user_prompt_text = (
            f"Pages: {json.dumps(page_skeleton, ensure_ascii=False)}\n"
            f"Sections: {json.dumps(section_skeleton, ensure_ascii=False)}\n\n"
            f"BASE CANDIDATE STYLING (starting point â€” inherit unless requirements override): {base_ctx}\n"
            f"DESIGNER REQUIREMENTS: {designer_requirements or '(explore visual variations of the base candidate)'}\n\n"
            f"{diversity_rules}\n\n"
            "Output exactly 3 candidates as JSON. Use ONLY the section/page ids provided above.\n"
            '{"candidates": [{"name": "...", "pages": [{"id": "...", "layout": {"value": "vertical", "main_width": "...", "header_width": "...", "footer_width": "..."}, "gap": {"value": "..."}}], '
            '"sections": [{"id": "...", "layout": "...", "component": "...", "position": "...", "col_span": 12, "style": {"color": "accent", "density": "...", "columns": "...", "shadow": "...", "bg": "...", "nav_height": "...", "sidebar_side": "...", "sidebar_width": 3}}], '
            '"styling": {"fontFamily": "...", "textSize": "xs|sm|md|lg|xl", "accentColor": "#hex", "accentSecondary": "#hex", "backgroundColor": "#hex", "textColor": "#hex", "radius": 8, "buttonStyle": "...", "cardHover": "...", "divider": "...", "pageMaxWidth": "...", "region.header.bg_hex": "#hex or omit", "region.header.text_hex": "#hex or omit", "region.footer.bg_hex": "#hex or omit", "region.footer.text_hex": "#hex or omit", "region.main.bg_hex": "#hex or omit", "region.sidebar.bg_hex": "#hex or omit", "region.border_hex": "#hex or omit", "component.card.bg_hex": "#hex or omit", "component.card.border_hex": "#hex or omit", "button.primary.bg_hex": "#hex or omit", "button.primary.text_hex": "#hex or omit", "button.secondary.bg_hex": "#hex or omit", "button.secondary.text_hex": "#hex or omit", "button.ghost.text_hex": "#hex or omit", "button.danger.bg_hex": "#hex or omit", "button.link.text_hex": "#hex or omit", "nav.bg_hex": "#hex or omit", "nav.text_hex": "#hex or omit", "table.header.bg_hex": "#hex or omit", "table.header.text_hex": "#hex or omit", "badge.info.bg_hex": "#hex or omit", "text.muted.hex": "#hex or omit"}}]}'
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_prompt_text,
            config={
                "system_instruction": f"You are a UI designer creating visual refinements of a selected interface design. Follow the schema and role rules exactly.\n\n{_CANDIDATE_FULL_SCHEMA}",
                "response_mime_type": "application/json",
                "max_output_tokens": 65536,
            },
        )
        result = json.loads(response.text)
        if isinstance(result, list):
            candidates = result
        else:
            candidates = result.get("candidates") or []
        if len(candidates) < 3:
            return None
        return candidates[:3]
    except Exception as e:
        import traceback
        print(f"[llm_regenerate_3_candidates] failed: {e}\n{traceback.format_exc()}", flush=True)
        return None


_COLLECTION_LAYOUTS = {"card", "table", "gallery", "list"}

def _allowed_layout(role: str, base_layout: str, proposed: str) -> str:
    """Return the layout to actually apply after LLM merge, protecting role-locked sections."""
    if role == "object_form" and proposed != "form":
        return base_layout
    if role in {"object_detail", "object_summary"} and proposed in _COLLECTION_LAYOUTS:
        return base_layout
    if role == "navigation" and proposed not in {"site-nav", "nav-links"}:
        return base_layout
    if role and role.startswith("activity_"):
        return base_layout
    return proposed


def _merge_llm_candidate(base_pages: list, base_sections: list, llm_candidate: dict) -> tuple[list, list]:
    """Merge LLM layout/style decisions onto base pages/sections, preserving all data fields."""
    pages = copy.deepcopy(base_pages)
    sections = copy.deepcopy(base_sections)

    llm_sec_map = {str(s.get("id", "")): s for s in (llm_candidate.get("sections") or []) if s.get("id")}
    llm_page_map = {str(p.get("id", "")): p for p in (llm_candidate.get("pages") or []) if p.get("id")}

    for sec in sections:
        sid = str(sec.get("id", ""))
        llm = llm_sec_map.get(sid)
        if not llm:
            continue
        role = str(sec.get("role") or "")
        # Layout: enforce role-based constraints to prevent LLM from breaking form/detail/activity sections
        if llm.get("layout") is not None:
            safe = _allowed_layout(role, str(sec.get("layout") or ""), llm["layout"])
            sec["layout"] = safe
            # Only apply component if layout was accepted
            if safe == llm["layout"] and llm.get("component") is not None:
                sec["component"] = llm["component"]
        for field in ("position", "col_span"):
            if llm.get(field) is not None:
                sec[field] = llm[field]
        if llm.get("style"):
            merged = dict(sec.get("style") or {})
            merged.update(llm["style"])
            sec["style"] = merged

    for page in pages:
        pid = str(page.get("id", ""))
        llm = llm_page_map.get(pid)
        if not llm:
            continue
        if llm.get("layout"):
            merged = dict(page.get("layout") or {})
            merged.update(llm["layout"])
            page["layout"] = merged
        if llm.get("gap"):
            page["gap"] = llm["gap"]

    return pages, sections


_TEXT_SIZE_TOKENS = {
    "xs": {"typography.hero.size": "44px", "typography.display.size": "32px", "typography.title-md.size": "17px", "typography.lead.size": "15px", "typography.body.size": "13px", "typography.caption.size": "10px", "typography.label.size": "12px"},
    "sm": {"typography.hero.size": "48px", "typography.display.size": "34px", "typography.title-md.size": "18px", "typography.lead.size": "16px", "typography.body.size": "14px", "typography.caption.size": "11px", "typography.label.size": "13px"},
    "md": {"typography.hero.size": "56px", "typography.display.size": "40px", "typography.title-md.size": "20px", "typography.lead.size": "18px", "typography.body.size": "16px", "typography.caption.size": "12px", "typography.label.size": "14px"},
    "lg": {"typography.hero.size": "64px", "typography.display.size": "46px", "typography.title-md.size": "24px", "typography.lead.size": "20px", "typography.body.size": "18px", "typography.caption.size": "13px", "typography.label.size": "15px"},
    "xl": {"typography.hero.size": "72px", "typography.display.size": "52px", "typography.title-md.size": "28px", "typography.lead.size": "22px", "typography.body.size": "20px", "typography.caption.size": "14px", "typography.label.size": "16px"},
}


def _tokens_from_llm_styling(llm_styling: dict, base_tokens: dict, prompt: str, index: int) -> dict:
    """Build color + typography tokens seeded from LLM styling output, then expand."""
    tokens = dict(base_tokens or {})
    accent = llm_styling.get("accentColor") or ""
    secondary = llm_styling.get("accentSecondary") or ""
    if accent:
        tokens.update({
            "accent.hex": accent,
            "region.header.bg_hex": accent,
            "region.footer.bg_hex": accent,
            "nav.bg_hex": accent,
            "button.primary.bg_hex": accent,
            "button.primary.border_hex": accent,
            "button.ghost.text_hex": accent,
            "input.border_focus_hex": accent,
        })
    if secondary:
        tokens["color.secondary.hex"] = secondary
    bg = llm_styling.get("backgroundColor") or ""
    if bg:
        tokens["page.body.bg_hex"] = bg
        tokens["page.bg.hex"] = bg
    text_color = llm_styling.get("textColor") or ""
    if text_color:
        tokens["page.body.text_hex"] = text_color
        tokens["text.primary.hex"] = text_color
    # Fine-grained hex overrides â€” must be set before _expand_design_tokens (which uses setdefault)
    _FINE_GRAINED_HEX = (
        "region.header.bg_hex", "region.header.text_hex",
        "region.footer.bg_hex", "region.footer.text_hex",
        "region.main.bg_hex", "region.sidebar.bg_hex", "region.border_hex",
        "component.card.bg_hex", "component.card.border_hex",
        "button.primary.bg_hex", "button.primary.text_hex",
        "button.secondary.bg_hex", "button.secondary.text_hex",
        "button.ghost.text_hex", "button.danger.bg_hex", "button.link.text_hex",
        "nav.bg_hex", "nav.text_hex",
        "table.header.bg_hex", "table.header.text_hex",
        "badge.info.bg_hex", "text.muted.hex",
    )
    for key in _FINE_GRAINED_HEX:
        val = llm_styling.get(key) or ""
        if val:
            tokens[key] = val
    text_size = llm_styling.get("textSize") or ""
    if text_size in _TEXT_SIZE_TOKENS:
        tokens.update(_TEXT_SIZE_TOKENS[text_size])
    tokens["design.variant_index"] = str(index)
    _expand_design_tokens(tokens)
    return tokens


def generate_candidate_set(interface_id: str, prompt: str = "") -> str:
    """Generate and save exactly 3 candidates from the current interface DSL and designer prompt."""
    try:
        iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS, timeout=30)
        iface_resp.raise_for_status()
        iface = iface_resp.json()
        data = dict(iface.get("data") or {})
        pages = data.get("pages") or []
        sections = data.get("sections") or []
        if not pages or not sections:
            return "ERROR: Interface has no pages/sections to generate candidates from."

        raw_base_tokens = dict(data.get("tokens") or {})
        base_styling = {**dict(data.get("styling") or {}), **_prompt_styling_overrides(prompt)}

        llm_candidates = _llm_generate_3_candidates(pages, sections, prompt)

        if not llm_candidates:
            return "ERROR: LLM failed to generate candidates."
        results = []
        for index in range(3):
            llm_cand = llm_candidates[index]
            variant_pages, variant_sections = _merge_llm_candidate(pages, sections, llm_cand)
            variant_pages, variant_sections = _dedupe_agent_header_shells(variant_pages, variant_sections)

            llm_styling = llm_cand.get("styling") or {}
            tokens = _tokens_from_llm_styling(llm_styling, raw_base_tokens, prompt, index)

            styling = dict(base_styling or {})
            for key in ("fontFamily", "radius", "buttonStyle", "cardHover", "imageRatio", "divider", "pageMaxWidth", "accentColor", "backgroundColor", "textColor"):
                if llm_styling.get(key) is not None:
                    styling[key] = llm_styling[key]
            styling["variantIndex"] = index
            styling["variantName"] = llm_cand.get("name") or _candidate_variant_name(prompt, index)
            variant_name = llm_cand.get("name") or _candidate_variant_name(prompt, index)
            variation_strategy = llm_cand.get("name") or _candidate_variant_name(prompt, index)

            result = validate_and_save_candidate(
                interface_id=interface_id,
                candidate_index=index,
                name=variant_name,
                description=f"Agent-generated candidate {index + 1} using '{prompt or 'current'}' as the designer requirement.",
                pages=json.dumps(variant_pages),
                sections=json.dumps(variant_sections),
                tokens=json.dumps(tokens) if tokens else "",
                styling=json.dumps(styling) if styling else "",
                prompt=prompt,
                variation_strategy=variation_strategy,
            )
            results.append(result)
            if not str(result).startswith("OK:"):
                return f"ERROR: candidate {index} failed: {result}"
            render_candidate_preview_func(interface_id, index)
        return "OK: generated and saved 3 candidates. " + " | ".join(results)
    except Exception as e:
        return f"ERROR: generate_candidate_set failed: {e}"

def regenerate_candidate_set(interface_id: str, selected_candidate_index: int, designer_requirements: str = "") -> str:
    """Regenerate exactly 3 candidates from a selected/base candidate using deterministic variants."""
    try:
        context_raw = get_candidate_regeneration_context(interface_id, selected_candidate_index, designer_requirements)
        if str(context_raw).startswith("ERROR") or str(context_raw).startswith("Error"):
            return context_raw
        context = json.loads(context_raw)
        base = context.get("base_candidate") or {}
        pages = base.get("pages") or []
        sections = base.get("sections") or []
        if not pages or not sections:
            return "ERROR: selected candidate has no pages/sections."
        raw_base_tokens = copy.deepcopy(base.get("tokens") or {})
        base_styling_raw = dict(base.get("styling") or {})
        base_styling = {**base_styling_raw, **_prompt_styling_overrides(designer_requirements)}

        llm_candidates = _llm_regenerate_3_candidates(pages, sections, designer_requirements, base_styling_raw)
        if not llm_candidates:
            return "ERROR: LLM failed to regenerate candidates."

        results = []
        for index in range(3):
            llm_cand = llm_candidates[index]
            variant_pages, variant_sections = _merge_llm_candidate(pages, sections, llm_cand)
            variant_pages, variant_sections = _dedupe_agent_header_shells(variant_pages, variant_sections)

            llm_styling = llm_cand.get("styling") or {}
            tokens = _tokens_from_llm_styling(llm_styling, raw_base_tokens, designer_requirements, index)

            styling = dict(base_styling or {})
            for key in ("fontFamily", "radius", "buttonStyle", "cardHover", "imageRatio", "divider", "pageMaxWidth", "accentColor", "backgroundColor", "textColor"):
                if llm_styling.get(key) is not None:
                    styling[key] = llm_styling[key]
            styling["variantIndex"] = index
            styling["variantName"] = llm_cand.get("name") or _candidate_variant_name(designer_requirements, index)
            variant_name = f"{llm_cand.get('name') or _candidate_variant_name(designer_requirements, index)} Regen"
            variation_strategy = llm_cand.get("name") or _candidate_variant_name(designer_requirements, index)

            result = validate_and_save_candidate(
                interface_id=interface_id,
                candidate_index=index,
                name=variant_name,
                description=f"Regenerated from candidate {selected_candidate_index + 1} with {styling.get('variantName', '')} structure.",
                pages=json.dumps(variant_pages),
                sections=json.dumps(variant_sections),
                tokens=json.dumps(tokens) if tokens else "",
                styling=json.dumps(styling) if styling else "",
                prompt=designer_requirements,
                derived_from=str(selected_candidate_index),
                designer_requirements=designer_requirements,
                variation_strategy=variation_strategy,
            )
            results.append(result)
            if not str(result).startswith("OK:"):
                return f"ERROR: regenerated candidate {index} failed: {result}"
            render_candidate_preview_func(interface_id, index)
        return "OK: regenerated and saved 3 candidates. " + " | ".join(results)
    except Exception as e:
        return f"ERROR: regenerate_candidate_set failed: {e}"

def analyze_interface_from_uml(interface_id: str) -> str:
    """
    Extract full UML intelligence from all 3 diagram types for an interface's system.
    Returns a JSON string with model_graph, actor permissions, workflows, and
    a rule-based interface plan (pages + sections) plus semantic_decisions for LLM review.
    """
    try:
        import json as _json
        from .uml_extractor import extract_uml_intelligence
        from .interface_planner import generate_interface_plan

        iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS, timeout=30)
        iface_resp.raise_for_status()
        iface = iface_resp.json()
        system_id = iface.get("system")
        actor_id = iface.get("actor") or ""

        system_data = _fetch_system_context_data(system_id)
        actor_name = _actor_name_from_context(system_data, str(actor_id))

        uml_intel = extract_uml_intelligence(system_data, str(actor_id), actor_name or "")
        interface_plan = generate_interface_plan(uml_intel)

        return _json.dumps({
            "interface_id": interface_id,
            "actor": actor_name,
            "meta": uml_intel.get("_meta", {}),
            "actor_permissions": uml_intel["actor_intel"].get("target_permissions", {}),
            "workflows": [
                {"name": w["name"], "step_count": w["step_count"], "steps": w["steps"]}
                for w in uml_intel["workflow_intel"].get("workflows", [])
            ],
            "model_graph_summary": {
                m: {
                    "attributes": [a["name"] for a in info.get("attributes", [])],
                    "layout_score": {k: round(v, 2) for k, v in (info.get("layout_score") or {}).items() if v > 0.3},
                    "composition_children": [c["model"] for c in info.get("compositions_owned", [])],
                    "composition_parent": info.get("composition_parent"),
                    "associations": [{"model": a["model"], "cardinality": a["cardinality"]} for a in info.get("associations", [])[:5]],
                }
                for m, info in uml_intel["model_graph"].items()
                if m in uml_intel["actor_intel"].get("target_permissions", {})
            },
            "interface_plan": interface_plan,
            "semantic_decisions": uml_intel.get("semantic_decisions", []),
        }, ensure_ascii=False)
    except Exception as e:
        import traceback
        return f"ERROR: analyze_interface_from_uml failed: {e}\n{traceback.format_exc()}"


def save_interface_plan(interface_id: str, pages_json: str, sections_json: str) -> str:
    """
    Save the final interface plan (pages + sections) to the database.
    pages_json and sections_json are JSON strings of the respective arrays.
    Replaces the current interface data completely.
    """
    try:
        import json as _json
        pages = _json.loads(pages_json) if isinstance(pages_json, str) else pages_json
        sections = _json.loads(sections_json) if isinstance(sections_json, str) else sections_json

        page_model_by_id = {
            str(p.get("id") or ""): str(p.get("primary_model") or p.get("model") or p.get("class") or "")
            for p in pages or []
        }
        data_layouts = {"card", "list", "table", "detail", "gallery", "filter", "form", "calendar", "timeline", "map"}

        def normalize_section_model(section: dict) -> dict:
            section = dict(section or {})
            model = (
                section.get("primary_model")
                or section.get("model")
                or section.get("class")
                or page_model_by_id.get(str(section.get("page_id") or ""), "")
                or ""
            )
            layout = _normalize_layout_alias(section.get("layout"))
            role = str(section.get("role") or "")
            is_data_section = layout in data_layouts or role in DATA_SECTION_ROLES or bool(section.get("attributes"))
            if is_data_section and model:
                section["primary_model"] = str(model)
                section["class"] = str(model)
            else:
                section.setdefault("primary_model", "")
                section.setdefault("class", "")
            section["layout"] = layout
            return section

        # Normalize pages to DB format
        db_pages = [
            {
                "id": p["id"],
                "name": p.get("name") or p["id"],
                "primary_model": p.get("primary_model") or p.get("model") or "",
                "type": {"value": "normal", "label": "Normal"},
                "sections": [{"value": _ref_id(sid)} for sid in (p.get("sections") or []) if _ref_id(sid)],
                "category": None,
            }
            for p in pages
        ]

        # Normalize sections to DB format
        db_sections = [
            {
                **normalize_section_model(s),
                "operations": _normalize_section_operations(s.get("operations")),
            }
            for s in sections
        ]

        if not db_pages:
            return "ERROR: pages list is empty â€” nothing to save."

        try:
            iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS, timeout=30)
            iface_resp.raise_for_status()
            iface = iface_resp.json()
            system_id = iface.get("system")
            system_context = _fetch_system_context_data(system_id) if system_id else {}
            actor_name = _actor_name_from_context(system_context, iface.get("actor"))
            usecase_navigation = _build_usecase_navigation(system_context, str(iface.get("actor") or ""), actor_name)
            model_attrs = {}
            for classifier in _as_list(system_context.get("classifiers"), "classifiers"):
                cdata = classifier.get("data", {}) if isinstance(classifier, dict) else {}
                cname = cdata.get("name", "")
                attrs = {a.get("name", "") for a in cdata.get("attributes", []) if a.get("name")}
                if cname:
                    model_attrs[cname] = attrs
            completed = _apply_builtin_workflow_logic(
                {"pages": db_pages, "sections": db_sections},
                system_id,
                iface.get("actor"),
            )
            db_pages = completed.get("pages") or db_pages
            db_sections = completed.get("sections") or db_sections
            db_pages, db_sections = _ensure_mapping_content_sections(
                db_pages,
                db_sections,
                usecase_navigation,
                model_attrs,
            )
        except Exception:
            pass

        db_pages, db_sections = _ensure_mapping_chrome_sections(db_pages, db_sections)
        db_sections = _drop_unreferenced_non_global_sections(db_pages, db_sections)

        resp = requests.patch(
            f"{METADATA_API_BASE}/interfaces/{interface_id}/data/",
            json={"pages": db_pages, "sections": db_sections},
            headers=_AUTH_HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        return f"OK: saved {len(db_pages)} pages and {len(db_sections)} sections to interface {interface_id}."
    except Exception as e:
        return f"ERROR: save_interface_plan failed: {e}"


analyze_interface_from_uml_tool = FunctionTool(func=analyze_interface_from_uml)
save_interface_plan_tool = FunctionTool(func=save_interface_plan)


def render_candidate_preview_func(interface_id: str, candidate_index: int) -> str:
    try:
        resp = requests.post(f"{METADATA_API_BASE}/interfaces/{interface_id}/candidates/{candidate_index}/render/", headers=_AUTH_HEADERS, timeout=60)
        if resp.ok: return f"OK: preview rendered for candidate {candidate_index}."
        return f"Render failed ({resp.status_code}): {resp.text}"
    except Exception as e: return f"Error rendering preview: {e}"

system_context_tool = FunctionTool(func=get_system_context)
interface_config_tool = FunctionTool(func=get_interface_config)
update_interface_patch_tool = FunctionTool(func=apply_interface_patch)
run_seed_script_tool = FunctionTool(func=run_seed_script)
get_available_paths_tool = FunctionTool(func=get_available_paths)
get_interface_full_context_tool = FunctionTool(func=get_interface_full_context)
generate_candidate_set_tool = FunctionTool(func=generate_candidate_set)
regenerate_candidate_set_tool = FunctionTool(func=regenerate_candidate_set)

