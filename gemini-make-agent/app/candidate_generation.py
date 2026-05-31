"""Candidate generation and regeneration logic for interface variants."""

import copy
import json
import os
import re
from collections import defaultdict

import requests

from .interface_schemas import (
    _CANDIDATE_FULL_SCHEMA,
    _CANDIDATE_TOKENS_EXAMPLE,
)
from .service_clients import METADATA_API_BASE, _AUTH_HEADERS, render_candidate_preview_func
from .section_utils import (
    _DATA_SECTION_LAYOUTS,
    _FOOTER_TEMPLATE_LAYOUTS,
    _HEADER_NAV_LAYOUTS,
    _HEADER_TEMPLATE_LAYOUTS,
    _VALID_SECTION_LAYOUTS,
    _VALID_SECTION_STYLE,
    _canonical_page_type,
    _finalize_data_section_bindings,
    _infer_page_type_value,
    _infer_section_component,
    _model_field_names,
    _normalize_activity_action_sections,
    _normalize_chrome_sections,
    _normalize_field_layout,
    _normalize_layout_alias,
    _normalize_section_operations,
    _page_type_value,
    _ref_id,
)
from .token_normalizer import _expand_design_tokens
from .usecase_workflow import _build_usecase_navigation
from .metadata_context import _actor_name_from_context, _fetch_system_context_data
from .candidate_defaults import (
    _assign_default_page_categories,
    _merge_page_categories,
)
from .mapping_sections import (
    _apply_nav_methods,
    _dedupe_agent_header_shells,
    _ensure_usecase_pages,
)


def _norm_candidate_styling(styling) -> dict:
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
    # LLM-generated styling is the source of truth.
    return styling


_STYLING_TOKEN_KEYS = frozenset({
    "region.header.bg_hex", "region.header.text_hex",
    "region.footer.bg_hex", "region.footer.text_hex",
    "region.main.bg_hex", "region.sidebar.bg_hex", "region.border_hex",
    "component.card.bg_hex", "component.card.border_hex",
    "button.primary.bg_hex", "button.primary.text_hex",
    "button.secondary.bg_hex", "button.secondary.text_hex",
    "button.ghost.text_hex", "button.danger.bg_hex", "button.link.text_hex",
    "input.bg_hex", "input.border_hex", "input.border_focus_hex", "input.text_hex",
    "nav.bg_hex", "nav.text_hex",
    "table.header.bg_hex", "table.header.text_hex",
    "badge.info.bg_hex", "text.muted.hex",
})

def _norm_candidate_tokens(tokens, styling: dict | None = None) -> dict:
    if not tokens:
        tokens = {}
    if isinstance(tokens, str):
        try: tokens = json.loads(tokens)
        except Exception: tokens = {}
    tokens = dict(tokens)
    # Pre-populate fine-grained overrides from styling.
    for key in _STYLING_TOKEN_KEYS:
        if key not in tokens and isinstance(styling, dict) and styling.get(key):
            tokens[key] = styling[key]
    # LLM-generated tokens/styling are the source of truth.
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
               Pages do NOT contain section data ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â they only reference section IDs.
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
        styling_dict = _norm_candidate_styling(styling)

        iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS)
        iface_resp.raise_for_status()
        iface = iface_resp.json()
        system_id = iface.get("system")
        tokens_d: dict = _norm_candidate_tokens(tokens, styling_dict)

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

        # Normalize sections with a small guardrail layer:
        # supported layouts/styles, UML-bound attributes, and valid workflow targets.
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
            if s.get("layout") not in _VALID_SECTION_LAYOUTS:
                s["layout"] = "card" if pm else "main-header"
                s["component"] = _infer_section_component(s)
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
            workflow = dict(s.get("workflow") or {})
            workflow_action = workflow.get("action") or s.get("workflow_action", "")
            if workflow_action and workflow_action not in {"complete", "complete_then_page", "complete_then_target", "navigate", "none"}:
                workflow.pop("action", None)
            workflow_target = workflow.get("target_page") or workflow.get("targetPage") or s.get("target_page") or s.get("targetPage") or ""
            normalized_target = page_ref_to_name.get(str(workflow_target), "") or page_ref_to_name.get(str(workflow_target).lower(), "")
            if workflow_target and normalized_target:
                workflow["target_page"] = normalized_target
            elif workflow_target and workflow_target not in page_names:
                workflow.pop("target_page", None); workflow.pop("targetPage", None)
            if workflow:
                s["workflow"] = workflow
            style = dict(s.get("style") or {})
            for field, valid_vals in _VALID_SECTION_STYLE.items():
                if style.get(field) and style[field] not in valid_vals:
                    style.pop(field, None)
            s["style"] = style
            s["field_layout"] = _normalize_field_layout(s)
            fixed_sections.append(s)
        for s in fixed_sections:
            if s.get("layout") in _DATA_SECTION_LAYOUTS:
                style = dict(s.get("style") or {})
                if not style.get("color") or style["color"] in {"blue", "green", "purple"}:
                    style["color"] = "accent"; s["style"] = style

        # Normalize pages
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
        fixed_sections = _apply_nav_methods(fixed_pages, fixed_sections, usecase_navigation)
        styling_d = styling_dict or {}
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

        data = dict(iface.get("data") or {})
        data["categories"] = _merge_page_categories(data.get("categories") or [], fixed_pages)
        candidates = list(data.get("candidates") or [])
        candidate = {
            "id": f"c{candidate_index}", "name": name, "description": description,
            "pages": fixed_pages, "sections": fixed_sections,
            "generated_by": "gemini_make_agent", "prompt": prompt or designer_requirements,
            **({"tokens": tokens_d} if tokens_d else {}),
            **({"styling": styling_d} if styling_d else {}),
        }
        if derived_from != "": candidate["derived_from"] = derived_from
        if designer_requirements: candidate["designer_requirements"] = designer_requirements
        if variation_strategy: candidate["variation_strategy"] = variation_strategy
        while len(candidates) <= candidate_index: candidates.append(None)
        candidates[candidate_index] = candidate
        data["candidates"] = candidates
        payload = {
            "id": interface_id,
            "name": iface["name"],
            "description": iface.get("description", ""),
            "system_id": system_id,
            "actor_id": iface.get("actor"),
            "data": data,
        }
        save_resp = requests.put(
            f"{METADATA_API_BASE}/interfaces/{interface_id}/",
            json=payload,
            headers=_AUTH_HEADERS,
            timeout=60,
        )
        if not save_resp.ok:
            return f"Error saving candidate: metadata PUT failed ({save_resp.status_code}): {save_resp.text[:1000]}"
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
    prefix = "Agent"
    suffixes = ("Gallery", "Table", "Showcase")
    return f"{prefix} {suffixes[index % len(suffixes)]}"


def _parse_llm_json(text: str):
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except Exception:
        pass

    decoder = json.JSONDecoder()
    candidates_pattern = re.search(r'"candidates"\s*:\s*\[', raw)
    preferred_starts = []
    if candidates_pattern:
        container_start = raw.rfind("{", 0, candidates_pattern.start())
        preferred_starts.append(container_start if container_start >= 0 else 0)
    starts = [i for i, ch in enumerate(raw) if ch in "[{"]
    fallback_obj = None
    for start in [*preferred_starts, *starts]:
        try:
            obj, _end = decoder.raw_decode(raw[start:])
            if isinstance(obj, dict) and isinstance(obj.get("candidates"), list):
                return obj
            if isinstance(obj, list):
                return obj
            if fallback_obj is None:
                fallback_obj = obj
        except Exception:
            continue
    if fallback_obj is not None:
        return fallback_obj

    repaired = raw
    while repaired.endswith("}") and repaired.count("{") < repaired.count("}"):
        repaired = repaired[:-1].rstrip()
        try:
            return json.loads(repaired)
        except Exception:
            continue
    raise ValueError("LLM response was not valid JSON")


def _candidate_list_from_llm_response(text: str) -> list:
    result = _parse_llm_json(text)
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and isinstance(result.get("candidates"), list):
        return result["candidates"]
    return []



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
            "Each candidate MUST follow user requirement:\n"
            # "  Candidate 0: DARK/NEUTRAL palette - accentColor from #1e293b #0f172a #1d4ed8 #0369a1 #1e3a5f; backgroundColor #0f172a or #111827; textColor #f1f5f9\n"
            # "  Candidate 1: VIBRANT/COLORFUL palette - accentColor from #7c3aed #0891b2 #059669 #dc2626 #d97706; backgroundColor #ffffff or #f8fafc; textColor #111827\n"
            # "  Candidate 2: WARM/EDITORIAL palette - accentColor from #ea580c #d97706 #be185d #9333ea #b45309; backgroundColor #fffbeb or #fdf4ff or #fff7ed; textColor #1c1917\n"
            "Each candidate MUST also differ in axes that user did not specify:\n"
            # "  - data section layout (table vs card vs gallery vs list)\n"
            # "  - nav placement (header top bar vs left sidebar vs right sidebar)\n"
            # "  - page width (contained vs wide vs full)\n"
            # "  - density (compact vs normal vs spacious)\n"
            # "  - typography (fontFamily + textSize ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â inter/roboto/poppins/playfair/mono + xs/sm/md/lg/xl)\n"
            # "  - border radius (0 vs 8 vs 16 vs 24)\n"
            # "  - button style (solid vs outline vs ghost vs gradient)\n"
            "Every page must have navigation unless user requires otherwise.\n"
            "Respect the designer prompt. \n"
            "Keep object_form -> form, object_detail -> detail, activity_* layouts unchanged.\n"
            "COLOR SCOPING: Match each requested color to its exact UI scope for every candidate. If the prompt assigns a color to header/topbar, set tokens['region.header.bg_hex'] to that color. If it assigns a color to accent/brand/theme, set styling.accentColor and tokens['accent.hex'] to that color. If it assigns a color to buttons/CTA/actions, set tokens['button.primary.bg_hex'] and tokens['button.primary.border_hex'] to that color, even when accentColor is different. If it assigns a color to footer, page/background, cards, search/input fields, nav, table headers, badges, links, or muted text, use the matching fine-grained token keys. Do not make unrelated tokens the same color unless the user explicitly asks for a monochrome theme.\n"
            # "COLOR HIERARCHY (mandatory for every candidate): region.header.bg_hex, accentColor, and backgroundColor must be visually distinct Ã¢â‚¬â€ do not assign the same hex to all three. accentColor is for interactive elements only (buttons, links, highlights), not for large background regions."
        )

        user_prompt_text = (
            f"Pages: {json.dumps(page_skeleton, ensure_ascii=False)}\n"
            f"Sections: {json.dumps(section_skeleton, ensure_ascii=False)}\n\n"
            f"DESIGNER PROMPT: {prompt or '(no specific requirements ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â explore freely)'}\n\n"
            f"{diversity_rules}\n\n"
            "Output exactly 3 candidates as JSON. Use ONLY the section/page ids provided above.\n"
            '{"candidates": [{"name": "...", "pages": [{"id": "...", "layout": {"value": "vertical", "main_width": "...", "header_width": "...", "footer_width": "..."}, "gap": {"value": "..."}}], '
            '"sections": [{"id": "...", "layout": "...", "component": "...", "position": "...", "col_span": 12, "style": {"color": "accent", "density": "...", "columns": "...", "shadow": "...", "bg": "...", "nav_height": "...", "sidebar_side": "...", "sidebar_width": 3}}], '
            '"styling": {"fontFamily": "...", "textSize": "xs|sm|md|lg|xl", "accentColor": "#hex", "accentSecondary": "#hex", "backgroundColor": "#hex", "textColor": "#hex", "radius": 8, "buttonStyle": "...", "cardHover": "...", "divider": "...", "pageMaxWidth": "..."}, '
            f'{_CANDIDATE_TOKENS_EXAMPLE}' + '}]}'
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
        candidates = _candidate_list_from_llm_response(response.text)
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
            "Each variant MUST differ from the others on axes that user:\n"
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
            "COLOR SCOPING: Match each requested color to its exact UI scope for every candidate. If the prompt assigns a color to header/topbar, set tokens['region.header.bg_hex'] to that color. If it assigns a color to accent/brand/theme, set styling.accentColor and tokens['accent.hex'] to that color. If it assigns a color to buttons/CTA/actions, set tokens['button.primary.bg_hex'] and tokens['button.primary.border_hex'] to that color, even when accentColor is different. If it assigns a color to footer, page/background, cards, search/input fields, nav, table headers, badges, links, or muted text, use the matching fine-grained token keys. Do not make unrelated tokens the same color unless the user explicitly asks for a monochrome theme.\n"
            "COLOR HIERARCHY (mandatory for every candidate): region.header.bg_hex, accentColor, and backgroundColor must be visually distinct Ã¢â‚¬â€ do not assign the same hex to all three. accentColor is for interactive elements only (buttons, links, highlights), not for large background regions."
        )

        user_prompt_text = (
            f"Pages: {json.dumps(page_skeleton, ensure_ascii=False)}\n"
            f"Sections: {json.dumps(section_skeleton, ensure_ascii=False)}\n\n"
            f"BASE CANDIDATE STYLING (starting point ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â inherit unless requirements override): {base_ctx}\n"
            f"DESIGNER REQUIREMENTS: {designer_requirements or '(explore visual variations of the base candidate)'}\n\n"
            f"{diversity_rules}\n\n"
            "Output exactly 3 candidates as JSON. Use ONLY the section/page ids provided above.\n"
            '{"candidates": [{"name": "...", "pages": [{"id": "...", "layout": {"value": "vertical", "main_width": "...", "header_width": "...", "footer_width": "..."}, "gap": {"value": "..."}}], '
            '"sections": [{"id": "...", "layout": "...", "component": "...", "position": "...", "col_span": 12, "style": {"color": "accent", "density": "...", "columns": "...", "shadow": "...", "bg": "...", "nav_height": "...", "sidebar_side": "...", "sidebar_width": 3}}], '
            '"styling": {"fontFamily": "...", "textSize": "xs|sm|md|lg|xl", "accentColor": "#hex", "accentSecondary": "#hex", "backgroundColor": "#hex", "textColor": "#hex", "radius": 8, "buttonStyle": "...", "cardHover": "...", "divider": "...", "pageMaxWidth": "..."}, '
            f'{_CANDIDATE_TOKENS_EXAMPLE}' + '}]}'
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
        candidates = _candidate_list_from_llm_response(response.text)
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
    # Fine-grained hex overrides ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â must be set before _expand_design_tokens (which uses setdefault)
    _FINE_GRAINED_HEX = (
        "region.header.bg_hex", "region.header.text_hex",
        "region.footer.bg_hex", "region.footer.text_hex",
        "region.main.bg_hex", "region.sidebar.bg_hex", "region.border_hex",
        "component.card.bg_hex", "component.card.border_hex",
        "button.primary.bg_hex", "button.primary.text_hex",
        "button.secondary.bg_hex", "button.secondary.text_hex",
        "button.ghost.text_hex", "button.danger.bg_hex", "button.link.text_hex",
        "input.bg_hex", "input.border_hex", "input.border_focus_hex", "input.text_hex",
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


def _tokens_from_llm_schema(llm_candidate: dict, base_tokens: dict, prompt: str, index: int) -> dict:
    """Prefer the LLM's complete top-level tokens; use styling only as a fallback seed."""
    llm_styling = llm_candidate.get("styling") or {}
    if isinstance(llm_styling, str):
        try:
            llm_styling = json.loads(llm_styling)
        except Exception:
            llm_styling = {}

    tokens = _tokens_from_llm_styling(llm_styling, base_tokens, prompt, index)
    llm_tokens = llm_candidate.get("tokens") or {}
    if isinstance(llm_tokens, str):
        try:
            llm_tokens = json.loads(llm_tokens)
        except Exception:
            llm_tokens = {}

    if isinstance(llm_tokens, dict):
        for key, value in llm_tokens.items():
            if value is not None and value != "":
                tokens[str(key)] = value

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
        # Do not merge regex parser styling overrides here. The LLM candidate
        # schema should decide fine-grained styling/token values.
        base_styling = dict(data.get("styling") or {})

        llm_candidates = _llm_generate_3_candidates(pages, sections, prompt)

        if not llm_candidates:
            return "ERROR: LLM failed to generate candidates."
        results = []
        for index in range(3):
            llm_cand = llm_candidates[index]
            variant_pages, variant_sections = _merge_llm_candidate(pages, sections, llm_cand)
            variant_pages, variant_sections = _dedupe_agent_header_shells(variant_pages, variant_sections)

            llm_styling = llm_cand.get("styling") or {}
            llm_tokens = llm_cand.get("tokens") or {}
            tokens = _tokens_from_llm_schema(llm_cand, raw_base_tokens, prompt, index)

            styling = dict(base_styling or {})
            for key in (
                "fontFamily", "radius", "buttonStyle", "cardHover", "imageRatio", "divider",
                "pageMaxWidth", "accentColor", "accentSecondary", "backgroundColor", "textColor",
                *_STYLING_TOKEN_KEYS,
            ):
                if llm_styling.get(key) is not None:
                    styling[key] = llm_styling[key]
                elif isinstance(llm_tokens, dict) and llm_tokens.get(key) is not None:
                    styling[key] = llm_tokens[key]
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
        # Do not merge regex parser styling overrides here. The LLM candidate
        # schema should decide fine-grained styling/token values.
        base_styling = dict(base_styling_raw or {})

        llm_candidates = _llm_regenerate_3_candidates(pages, sections, designer_requirements, base_styling_raw)
        if not llm_candidates:
            return "ERROR: LLM failed to regenerate candidates."

        results = []
        for index in range(3):
            llm_cand = llm_candidates[index]
            variant_pages, variant_sections = _merge_llm_candidate(pages, sections, llm_cand)
            variant_pages, variant_sections = _dedupe_agent_header_shells(variant_pages, variant_sections)

            llm_styling = llm_cand.get("styling") or {}
            llm_tokens = llm_cand.get("tokens") or {}
            tokens = _tokens_from_llm_schema(llm_cand, raw_base_tokens, designer_requirements, index)

            styling = dict(base_styling or {})
            for key in (
                "fontFamily", "radius", "buttonStyle", "cardHover", "imageRatio", "divider",
                "pageMaxWidth", "accentColor", "accentSecondary", "backgroundColor", "textColor",
                *_STYLING_TOKEN_KEYS,
            ):
                if llm_styling.get(key) is not None:
                    styling[key] = llm_styling[key]
                elif isinstance(llm_tokens, dict) and llm_tokens.get(key) is not None:
                    styling[key] = llm_tokens[key]
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

