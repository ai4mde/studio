"""Django-facing service functions for the migrated Gemini Make Agent."""

import json as _json
import logging
import os
import re as _re

from llm.prompts.interface_edit import build_interface_edit_prompt
from metadata.models import Interface, System

from .interface_patch import apply_interface_patch
from .uml_mapping.mapping_sections import (
    _drop_unreferenced_non_global_sections,
    _ensure_mapping_chrome_sections,
    _ensure_mapping_content_sections,
)
from .uml_mapping.metadata_context import _actor_name_from_context, _fetch_system_context_data
from .section_utils import (
    _normalize_select_existing_sections,
    _normalize_layout_alias,
    _normalize_section_operations,
    _ref_id,
)
from .token_normalizer import _as_list
from .uml_mapping.uml_extractor import _sys_as_list, extract_uml_intelligence
from .uml_mapping.usecase_workflow import _build_usecase_navigation
from .workflow_application import _apply_builtin_workflow_logic

from .semantic_mapper.engine import TransformationEngine as _TKBEngine
from .semantic_mapper.adapter import system_data_to_tkb_input as _to_tkb_input, extract_interface_for_actor as _extract_actor_iface

logger = logging.getLogger(__name__)



def _strip_json_fence(value: str) -> str:
    text = str(value or "").strip()
    if text.startswith("```"):
        newline = text.find("\n")
        if newline != -1 and text[3:newline].strip().lower() in {"", "json"}:
            text = text[newline + 1:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


def _interface_to_agent_dict(interface: Interface) -> dict:
    """Serialize an Interface ORM object into the agent payload shape."""
    return {
        "id": str(interface.id),
        "name": interface.name,
        "description": interface.description,
        "system": str(interface.system_id),
        "actor": str(interface.actor_id) if interface.actor_id else None,
        "data": interface.data or {},
    }


def _sync_method_into_section(section: dict, classifier_id: str, model_name: str, method: dict, method_name: str) -> bool:
    """Write a method into a section's methods list if the section matches the classifier. Returns True if changed."""
    section_class = str(section.get("class") or "")
    if section_class != str(classifier_id) and section_class != model_name:
        return False
    sec_methods = section.setdefault("methods", [])
    existing = next((m for m in sec_methods if isinstance(m, dict) and m.get("name") == method_name), None)
    if existing:
        if not existing.get("body"):
            existing["body"] = method["body"]
            return True
        return False
    sec_methods.append({
        "name": method_name,
        "call_name": method.get("call_name") or method_name,
        "label": method.get("label") or method_name,
        "body": method["body"],
        "parameters": method.get("parameters") or [],
        "description": method.get("description") or "",
    })
    return True


def _sync_method_to_interface_sections(
    classifier_id: str,
    model_name: str,
    method: dict,
    system_id: str,
) -> None:
    """Write a newly-generated method body into every Interface section that references this classifier.

    This ensures the body flows into both models.py generation and action_panel rendering,
    which both read from Interface section.methods rather than Classifier.custom_methods.
    """
    from metadata.models import Interface as _Iface

    method_name = method.get("name") or ""
    if not method_name or not method.get("body"):
        return

    for iface in _Iface.objects.filter(system_id=system_id):
        data = iface.data or {}
        sections = data.get("sections") or []
        changed = any(
            _sync_method_into_section(section, classifier_id, model_name, method, method_name)
            for section in sections
        )
        if changed:
            try:
                _Iface.objects.filter(id=iface.id).update(data=data)
            except Exception:
                pass


def _generate_missing_method_bodies(
    system_data: dict,
    model_graph: dict,
    system_id: str,
) -> None:
    """At map time: auto-generate LLM method bodies for methods that have a description but no body."""
    import ast as _ast
    from metadata.models import Classifier as _Clf
    from llm.handler import llm_handler as _llm, remove_reply_markdown as _rmmd

    # Build shared context strings from model_graph
    model_lines: list[str] = []
    rel_lines: list[str] = []
    for mn, info in model_graph.items():
        attrs = info.get("attributes") or []
        parts = [f"{a['name']}({a.get('type', 'str')})" for a in attrs if a.get("name")]
        for assoc in info.get("associations") or []:
            rel, card = assoc["model"], assoc["cardinality"]
            parts.append(f"{rel.lower()}_set(→{rel}[])" if card == "1-many" else f"{rel.lower()}(→{rel})")
        model_lines.append(f"{mn}: " + (", ".join(parts) or "(no fields)"))
        for assoc in info.get("associations") or []:
            rel, card = assoc["model"], assoc["cardinality"]
            if card == "1-many":
                rel_lines.append(f"{mn} 1-many {rel}: access self.{rel.lower()}_set.all()")
            elif card in ("many-1", "1-1"):
                rel_lines.append(f"{mn} →{rel}: access self.{rel.lower()}")

    model_ctx = "\n".join(model_lines) or "(none)"
    rel_ctx = "\n".join(rel_lines) or "(none)"

    raw_cls = _sys_as_list(system_data, "classifiers")
    for c in raw_cls:
        if not isinstance(c, dict) or not c.get("id"):
            continue
        cdata = c.get("data") or {}
        if cdata.get("type") not in {"class", "entity", "model"}:
            continue
        model_name = cdata.get("name") or ""
        if not model_name:
            continue
        # Classifiers store methods in "methods" field (UML diagram style).
        # "custom_methods" is a legacy fallback.
        methods_field = "methods" if cdata.get("methods") else "custom_methods"
        methods = cdata.get("methods") or cdata.get("custom_methods") or []
        if not methods:
            continue

        updated = False
        newly_generated: list[dict] = []
        for method in methods:
            if not isinstance(method, dict):
                continue
            if method.get("body") or not method.get("description") or not method.get("name"):
                continue  # already has body, or nothing to generate from

            info = model_graph.get(model_name) or {}
            attrs = info.get("attributes") or []
            clf_summary = f"{model_name}: " + ", ".join(
                f"{a['name']}({a.get('type', 'str')})" for a in attrs if a.get("name")
            )
            reverse_hints = "; ".join(
                f"self.{a['model'].lower()}_set.all() → {a['model']}[]"
                for a in (info.get("associations") or [])
                if a["cardinality"] == "1-many"
            ) or "self.relatedmodel_set.all()"

            try:
                raw = _llm(
                    prompt_name="DIAGRAM_GENERATE_METHOD",
                    model="llama-3.3-70b-versatile",
                    input_data={
                        "django_version": "5.0.2",
                        "target_class": model_name,
                        "method_name": method["name"],
                        "method_description": method["description"],
                        "classifier_summary": clf_summary,
                        "model_context": model_ctx,
                        "relation_context": rel_ctx,
                        "reverse_fk_pattern": reverse_hints,
                    },
                )
                body = _rmmd(raw).strip()
                _ast.parse(body)  # validate syntax; raises SyntaxError if invalid
                method["body"] = body
                updated = True
                newly_generated.append(method)
            except Exception:
                pass  # skip silently — prototype still works without this method

        if updated:
            try:
                _Clf.objects.filter(id=c["id"], system_id=system_id).update(
                    data={**cdata, methods_field: methods}
                )
            except Exception:
                pass


def _sync_all_classifier_methods_to_interfaces(system_id: str) -> None:
    """After map overwrites Interface sections, re-sync all Classifier method bodies.

    Called after the Interface is saved so the sync lands on the final section state,
    not an intermediate version that gets overwritten.
    """
    from metadata.models import Classifier as _Clf

    for clf in _Clf.objects.filter(system_id=system_id):
        cdata = clf.data or {}
        if cdata.get("type") not in {"class", "entity", "model"}:
            continue
        model_name = cdata.get("name") or ""
        if not model_name:
            continue
        all_methods = (cdata.get("methods") or []) + (cdata.get("custom_methods") or [])
        for method in all_methods:
            if isinstance(method, dict) and method.get("body") and method.get("name"):
                _sync_method_to_interface_sections(str(clf.id), model_name, method, str(system_id))


def _ensure_action_panel_sections(interface_id: str, system_id: str) -> None:
    """For each page that has a detail/form section for a model with custom methods,
    ensure a dedicated action section (attributes=[]) exists so action_panel renders.

    Uses a deterministic section id so re-running is idempotent.
    Only adds action sections to detail/form pages — not to list/collection pages.
    """
    from metadata.models import Interface as _Iface, Classifier as _Clf

    # Build: model_name → (classifier_id, methods_with_bodies)
    clf_methods: dict[str, dict] = {}
    for clf in _Clf.objects.filter(system_id=system_id):
        cdata = clf.data or {}
        if cdata.get("type") not in {"class", "entity", "model"}:
            continue
        model_name = cdata.get("name") or ""
        if not model_name:
            continue
        all_methods = (cdata.get("methods") or []) + (cdata.get("custom_methods") or [])
        methods = [
            m for m in all_methods
            if isinstance(m, dict) and m.get("body") and m.get("name")
        ]
        if methods:
            clf_methods[model_name] = {"clf_id": str(clf.id), "methods": methods}

    if not clf_methods:
        return

    iface = _Iface.objects.filter(id=interface_id).first()
    if not iface:
        return

    data = iface.data or {}
    pages = data.get("pages") or []
    sections = data.get("sections") or []
    section_map = {str(s.get("id") or ""): s for s in sections if s.get("id")}
    existing_ids = {str(s.get("id") or "") for s in sections}
    changed = False

    _detail_roles = {"object_detail", "object_form", "object_summary"}

    for page in pages:
        page_id = str(page.get("id") or "")
        page_section_refs = page.get("sections") or []
        page_sections = [
            section_map.get(str(_ref_id(ref) or ""))
            for ref in page_section_refs
        ]
        page_sections = [s for s in page_sections if s]

        for model_name, info in clf_methods.items():
            clf_id = info["clf_id"]
            methods = info["methods"]

            # Only add action section if page already has a detail/form section for this model
            has_detail = any(
                s.get("role") in _detail_roles and
                str(s.get("class") or s.get("primary_model") or "") in {clf_id, model_name}
                for s in page_sections
            )
            if not has_detail:
                continue

            # Deterministic id — safe to re-run
            action_id = f"{page_id}_{model_name.lower()}_action_panel"
            if action_id in existing_ids:
                continue  # already exists

            new_section = {
                "id": action_id,
                "name": f"{model_name} Actions",
                "role": "child_collection",
                "class": clf_id,
                "primary_model": model_name,
                "page_id": page_id,
                "layout": "list",
                "component": "ObjectList",
                "position": "main",
                "col_span": 12,
                "attributes": [],
                "methods": [
                    {
                        "name": m["name"],
                        "call_name": m.get("call_name") or m["name"],
                        "label": m.get("label") or m["name"],
                        "body": m["body"],
                        "parameters": m.get("parameters") or [],
                        "description": m.get("description") or "",
                    }
                    for m in methods
                ],
            }
            sections.append(new_section)
            existing_ids.add(action_id)
            page["sections"] = page_section_refs + [{"value": action_id}]
            changed = True

    if changed:
        data["sections"] = sections
        _Iface.objects.filter(id=interface_id).update(data=data)



_DATA_LAYOUTS = {
    "card", "list", "table", "detail", "gallery", "filter", "form", "timeline", "map",
}

_DATA_ROLES = {
    "object_collection", "object_detail", "object_summary",
    "child_collection", "object_form", "filter",
}


def _build_model_attrs_from_system(system_data: dict) -> dict:
    """Build model_attrs dict from system classifier data."""
    return {
        cdata.get("name"): {
            a.get("name", "")
            for a in cdata.get("attributes", [])
            if isinstance(a, dict) and a.get("name")
        }
        for classifier in _as_list(system_data.get("classifiers"), "classifiers")
        if isinstance(classifier, dict)
        for cdata in [classifier.get("data", {})]
        if cdata.get("name")
    }


def _normalize_section_model(section: dict, page_model_by_id: dict) -> dict:
    """Normalize primary_model/class and layout on a section dict."""
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
    is_data_section = (
        layout in _DATA_LAYOUTS or role in _DATA_ROLES or bool(section.get("attributes"))
    )
    if is_data_section and model:
        section["primary_model"] = str(model)
        section["class"] = str(model)
    else:
        section.setdefault("primary_model", "")
        section.setdefault("class", "")
    section["layout"] = layout
    return section


def map_uml_to_interface(interface_id: str) -> dict:
    """Run rules-based UML-to-interface mapping and save it via metadata API."""
    if not interface_id:
        return {"status": "error", "message": "interface_id required"}

    try:
        interface = Interface.objects.get(id=interface_id)
        iface = _interface_to_agent_dict(interface)
        system_data = _fetch_system_context_data(str(interface.system_id))
        actor_id = str(iface.get("actor") or "")
        actor_name = _actor_name_from_context(system_data, actor_id) or ""

        uml_intel = extract_uml_intelligence(system_data, actor_id, actor_name)
        _generate_missing_method_bodies(system_data, uml_intel["model_graph"], str(interface.system_id))

        tkb_input = _to_tkb_input(system_data)
        tkb_output = _TKBEngine().transform(tkb_input)
        pages, sections = _extract_actor_iface(tkb_output, actor_name, system_data)
        # Semantic profiles (CRUD/Lookup/Config/Search/StateTransition) computed by
        # TKB intent_rules — passed downstream to build_navigation_plan so section
        # composition uses the YAML rule results rather than Python heuristics.
        semantic_profiles: dict = tkb_output.get("semantic_profiles") or {}
        section_composition: dict = tkb_output.get("section_composition") or {}
        page_model_by_id = {
            str(p.get("id") or ""): str(
                p.get("primary_model") or p.get("model") or p.get("class") or ""
            )
            for p in pages or []
        }

        db_pages = [
            {
                "id": p["id"],
                "name": p.get("name") or p["id"],
                "primary_model": p.get("primary_model") or "",
                "type": p.get("type") or {"value": "normal", "label": "Normal"},
                "nav": p.get("nav", True),
                "sections": [
                    {"value": _ref_id(sid)}
                    for sid in (p.get("sections") or [])
                    if _ref_id(sid)
                ],
                "category": None,
            }
            for p in pages
        ]
        db_sections = [
            {
                **_normalize_section_model(s, page_model_by_id),
                "operations": _normalize_section_operations(s.get("operations")),
            }
            for s in sections
        ]

        model_attrs = _build_model_attrs_from_system(system_data)
        usecase_navigation = _build_usecase_navigation(
            system_data, actor_id, actor_name,
            semantic_profiles=semantic_profiles,
            section_composition=section_composition,
            model_graph=uml_intel.get("model_graph") or {},
        )
        completed = _apply_builtin_workflow_logic(
            {"pages": db_pages, "sections": db_sections},
            iface.get("system"),
            iface.get("actor"),
            system_context=system_data,
            usecase_navigation=usecase_navigation,
            model_attrs=model_attrs,
        )
        db_pages = completed.get("pages") or db_pages
        db_sections = completed.get("sections") or db_sections
        db_pages, db_sections = _ensure_mapping_content_sections(
            db_pages,
            db_sections,
            usecase_navigation,
            model_attrs,
            uml_intel.get("model_graph") or {},
            semantic_profiles=semantic_profiles,
        )
        db_pages, db_sections = _ensure_mapping_chrome_sections(db_pages, db_sections)
        db_sections = _drop_unreferenced_non_global_sections(db_pages, db_sections)
        db_sections = _normalize_select_existing_sections(db_pages, db_sections)

        data = dict(interface.data or {})
        data.update({"pages": db_pages, "sections": db_sections})
        Interface.objects.filter(id=interface_id).update(data=data)

        # Sync Classifier custom_methods bodies into the freshly-saved Interface sections.
        # Must run AFTER the Interface is saved — map overwrites sections, so any earlier
        # sync would be lost.
        _sync_all_classifier_methods_to_interfaces(str(interface.system_id))

        # Ensure each detail/form page has a dedicated action section for models with methods.
        _ensure_action_panel_sections(interface_id, str(interface.system_id))

        return {
            "status": "ok",
            "message": f"Mapped {len(db_pages)} pages and {len(db_sections)} sections.",
            "page_count": len(db_pages),
            "section_count": len(db_sections),
        }
    except Interface.DoesNotExist:
        return {"status": "error", "message": f"Interface {interface_id} not found."}
    except Exception as exc:
        import traceback

        logger.exception("map_uml_to_interface error")
        return {"status": "error", "message": str(exc), "detail": traceback.format_exc()}


def map_uml_to_all_interfaces(system_id: str) -> dict:
    """Run UML-to-interface mapping for every interface in a system."""
    if not system_id:
        return {"status": "error", "message": "system_id required"}

    try:
        interfaces = [
            _interface_to_agent_dict(interface)
            for interface in Interface.objects.filter(system_id=system_id).order_by("id")
        ]
    except Exception as exc:
        return {"status": "error", "message": f"Failed to list interfaces: {exc}"}

    if not interfaces:
        return {"status": "error", "message": "No interfaces found for this system."}

    results = []
    for iface in interfaces:
        iface_id = str(iface.get("id") or "")
        actor = str(iface.get("actor") or "")
        try:
            result = map_uml_to_interface(iface_id)
            results.append({"interface_id": iface_id, "actor": actor, **result})
        except Exception as exc:
            results.append(
                {
                    "interface_id": iface_id,
                    "actor": actor,
                    "status": "error",
                    "message": str(exc),
                }
            )

    succeeded = sum(1 for r in results if r.get("status") == "ok")
    return {
        "status": "ok",
        "message": f"Mapped {succeeded}/{len(results)} interfaces.",
        "results": results,
    }


def apply_prompt_to_interface(interface_id: str, system_id: str, user_request: str) -> dict:
    """Use Gemini to convert a UI edit request into a safe interface patch."""
    if not interface_id:
        return {"status": "error", "message": "interface_id required"}
    if not user_request:
        return {"status": "error", "message": "user_request required"}

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "message": "GEMINI_API_KEY or GOOGLE_API_KEY is required for prompt-based interface edits.",
        }

    try:
        import google.genai as _genai

        interface = Interface.objects.get(id=interface_id)
        iface = _interface_to_agent_dict(interface)
        system_id = system_id or str(iface.get("system") or "")
        system_context = _fetch_system_context_data(system_id) if system_id else {}
        actor_name = _actor_name_from_context(system_context, iface.get("actor")) or ""

        classifiers = []
        for classifier in _as_list(system_context.get("classifiers"), "classifiers"):
            cdata = classifier.get("data", {}) if isinstance(classifier, dict) else {}
            name = cdata.get("name", "")
            attrs = [
                attr.get("name")
                for attr in (cdata.get("attributes") or [])
                if isinstance(attr, dict) and attr.get("name")
            ]
            if name:
                classifiers.append({"name": name, "attributes": attrs})

        current_data = {
            key: iface.get("data", {}).get(key)
            for key in ("pages", "sections", "tokens", "styling", "layout_config")
            if isinstance(iface.get("data"), dict) and key in iface.get("data", {})
        }

        prompt = build_interface_edit_prompt(
            actor_name=actor_name,
            classifiers=classifiers,
            current_data=current_data,
            user_request=user_request,
        )

        client = _genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.getenv("DJANGO_AGENT_MODEL", "gemini-2.5-flash-lite"),
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "max_output_tokens": 65536,
            },
        )
        raw_text = _strip_json_fence(str(getattr(response, "text", "") or ""))
        patch = _json.loads(raw_text)
        if not isinstance(patch, dict):
            return {"status": "error", "message": "Model did not return a JSON object patch."}

        result = apply_interface_patch(interface_id, patch)
        if str(result).startswith("Patched interface"):
            return {"status": "ok", "message": result, "patch": patch}
        return {"status": "error", "message": result, "patch": patch}
    except Interface.DoesNotExist:
        return {"status": "error", "message": f"Interface {interface_id} not found."}
    except Exception as exc:
        import traceback

        return {"status": "error", "message": str(exc), "detail": traceback.format_exc()}
