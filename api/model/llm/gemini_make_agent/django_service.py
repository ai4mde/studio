"""Django-facing service functions for the migrated Gemini Make Agent."""

import json as _json
import logging
import os
import re as _re

import requests as _req
from diagram.models import Diagram
from llm.prompts.semantics import build_resolve_interface_semantics_prompt
from metadata.models import Interface, System

from .interface_patch import apply_interface_patch
from .interface_schemas import _DATA_SCHEMA, _LAYOUT_SCHEMA
from .uml_mapping.interface_planner import generate_interface_plan
from .uml_mapping.mapping_sections import (
    _drop_unreferenced_non_global_sections,
    _ensure_mapping_chrome_sections,
    _ensure_mapping_content_sections,
)
from .uml_mapping.metadata_context import _actor_name_from_context
from .section_utils import (
    _normalize_select_existing_sections,
    _normalize_layout_alias,
    _normalize_section_operations,
    _ref_id,
)
from .token_normalizer import _as_list
from .uml_mapping.uml_extractor import _sys_as_list, extract_uml_intelligence
from .uml_mapping.usecase_workflow import _build_activity_diagrams, _build_usecase_navigation
from .workflow_application import _apply_builtin_workflow_logic

logger = logging.getLogger(__name__)


def _interface_to_agent_dict(interface: Interface) -> dict:
    return {
        "id": str(interface.id),
        "name": interface.name,
        "description": interface.description,
        "system": str(interface.system_id),
        "actor": str(interface.actor_id) if interface.actor_id else None,
        "data": interface.data or {},
    }


def _node_position(node) -> tuple[object, object]:
    data = node.data or {}
    position = data.get("position") or {}
    return position.get("x", data.get("x")), position.get("y", data.get("y"))


def _system_context_from_orm(system_id: str) -> dict:
    system = System.objects.prefetch_related(
        "classifiers",
        "relations",
        "interfaces",
        "diagrams__nodes",
        "diagrams__edges",
    ).get(id=system_id)
    classifiers = [
        {
            "id": str(classifier.id),
            "project": str(classifier.project_id) if classifier.project_id else None,
            "system": str(classifier.system_id) if classifier.system_id else None,
            "original_system_id": (
                str(classifier.original_system_id)
                if classifier.original_system_id
                else None
            ),
            "data": classifier.data or {},
        }
        for classifier in system.classifiers.all()
    ]
    relations = [
        {
            "id": str(relation.id),
            "system": str(relation.system_id),
            "source": str(relation.source_id),
            "target": str(relation.target_id),
            "data": relation.data or {},
        }
        for relation in system.relations.all()
    ]
    diagrams = []
    nodes = []
    for diagram in Diagram.objects.filter(system=system).prefetch_related("nodes", "edges"):
        diagram_nodes = []
        diagram_edges = []
        for node in diagram.nodes.all():
            x, y = _node_position(node)
            node_payload = {
                "id": str(node.id),
                "diagram": str(node.diagram_id),
                "cls": str(node.cls_id) if node.cls_id else None,
                "data": node.data or {},
                "x": x,
                "y": y,
            }
            diagram_nodes.append(node_payload)
            nodes.append(node_payload)
        for edge in diagram.edges.all():
            diagram_edges.append(
                {
                    "id": str(edge.id),
                    "diagram": str(edge.diagram_id),
                    "rel": str(edge.rel_id) if edge.rel_id else None,
                    "data": edge.data or {},
                }
            )
        diagrams.append(
            {
                "id": str(diagram.id),
                "name": diagram.name,
                "description": diagram.description,
                "type": diagram.type,
                "system": str(diagram.system_id),
                "nodes": diagram_nodes,
                "edges": diagram_edges,
            }
        )
    interfaces = [
        {
            "id": str(interface.id),
            "name": interface.name,
            "description": interface.description,
            "system": str(interface.system_id),
            "actor": str(interface.actor_id) if interface.actor_id else None,
            "data": interface.data or {},
        }
        for interface in system.interfaces.all()
    ]
    context = {
        "id": str(system.id),
        "name": system.name,
        "description": system.description,
        "project": str(system.project_id),
        "classifiers": classifiers,
        "relations": relations,
        "diagrams": diagrams,
        "nodes": nodes,
        "interfaces": interfaces,
        "imported_classifiers": [],
    }
    context["activity_diagrams"] = _build_activity_diagrams(context)
    return context


def resolve_interface_semantics_with_llm(
    uml_intel: dict,
    interface_plan: dict,
) -> dict:
    """Ask Gemini to resolve layout/component choices; return safe overrides."""
    decisions = uml_intel.get("semantic_decisions") or []
    if not decisions:
        return {}
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {}
    model_name = os.getenv("SEMANTIC_RESOLVER_MODEL") or os.getenv(
        "ADK_AGENT_MODEL",
        "gemini-2.0-flash-lite",
    )
    if "/" in model_name:
        provider, raw_name = model_name.split("/", 1)
        model_name = raw_name if provider == "gemini" else "gemini-2.0-flash-lite"
    elif not model_name.startswith("gemini-"):
        model_name = "gemini-2.0-flash-lite"

    allowed = {
        "model_layouts": ["table", "list", "gallery", "timeline", "map"],
        "model_components": [
            "DataTable",
            "ObjectList",
            "CardGrid",
            "PersonCardGrid",
            "CategoryTileGrid",
            "TimelineList",
            "MapView",
        ],
        "activity_layouts": ["form", "detail", "list"],
        "activity_components": [
            "ObjectForm",
            "DetailPanel",
            "SummaryPanel",
            "ObjectList",
        ],
        "activity_roles": [
            "object_form",
            "object_detail",
            "object_collection",
        ],
        "workflow_intents": [
            "select_existing",
            "check",
            "create_record",
            "update_record",
            "notify",
            "confirm",
        ],
        "condition_operators": [">", ">=", "==", "!=", "<", "<="],
        "context_binding_modes": ["hidden", "readonly", "select"],
        "actor_model_scopes": ["self_profile", "collection", "assigned", "hidden"],
    }
    prompt = build_resolve_interface_semantics_prompt(
        allowed=allowed,
        actor_permissions=uml_intel.get("actor_intel", {}).get("target_permissions", {}),
        model_graph=uml_intel.get("model_graph") or {},
        workflow_intel=uml_intel.get("workflow_intel") or {},
        decisions=decisions,
        interface_plan=interface_plan,
    )
    try:
        resp = _req.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0, "maxOutputTokens": 8192},
            },
            timeout=12,
        )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        text = _re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
        raw = _json.loads(text)
    except Exception as exc:
        logger.warning("semantic resolver fallback to rules: %s", exc)
        return {}

    valid_models = set((uml_intel.get("actor_intel") or {}).get("target_permissions") or {})
    clean_actor_model_scopes = {}
    for model, scope in (raw.get("actor_model_scopes") or {}).items():
        if model in valid_models and scope in allowed["actor_model_scopes"]:
            clean_actor_model_scopes[model] = scope
    clean_models = {}
    for model, cfg in (raw.get("models") or {}).items():
        if model not in valid_models or not isinstance(cfg, dict):
            continue
        layout = cfg.get("layout")
        component = cfg.get("component")
        if layout in allowed["model_layouts"] and component in allowed["model_components"]:
            clean_models[model] = {"layout": layout, "component": component}

    valid_actions = {
        step.get("action")
        for wf in (uml_intel.get("workflow_intel") or {}).get("workflows", [])
        for step in (wf.get("steps") or [])
        if step.get("action")
    }
    model_graph = uml_intel.get("model_graph") or {}
    def _valid_fields(model: str) -> set[str]:
        return {
            str(attr.get("name") or "")
            for attr in ((model_graph.get(model) or {}).get("attributes") or [])
            if attr.get("name")
        }

    def _clean_fields(model: str, values) -> list[str]:
        valid = _valid_fields(model)
        out = []
        for field in values or []:
            field = str(field)
            if field in valid and field not in out:
                out.append(field)
        return out

    def _fields_from_legacy_updates(model: str, values) -> list[str]:
        valid = _valid_fields(model)
        out = []
        for update in values or []:
            if not isinstance(update, dict):
                continue
            field = str(update.get("field") or "")
            if field in valid and field not in out:
                out.append(field)
        return out

    clean_steps = {}
    for action, cfg in (raw.get("activity_steps") or {}).items():
        if action not in valid_actions or not isinstance(cfg, dict):
            continue
        layout = cfg.get("layout")
        component = cfg.get("component")
        role = cfg.get("role")
        if layout in allowed["activity_layouts"] and component in allowed["activity_components"]:
            model = cfg.get("model")
            model = model if model in valid_models else ""
            readonly_fields = _clean_fields(model, cfg.get("readonly_fields") or [])
            editable_fields = _clean_fields(model, cfg.get("editable_fields") or cfg.get("fields") or [])
            clean_steps[action] = {
                "layout": layout,
                "component": component,
                "role": role if role in allowed["activity_roles"] else "",
                **({"model": model} if model else {}),
                **({"readonly_fields": readonly_fields} if readonly_fields else {}),
                **({"editable_fields": editable_fields} if editable_fields else {}),
            }

    clean_workflow_steps = {}
    for action, cfg in (raw.get("workflow_steps") or {}).items():
        if action not in valid_actions or not isinstance(cfg, dict):
            continue
        intent = cfg.get("intent")
        if intent not in allowed["workflow_intents"]:
            continue
        step = {"intent": intent}
        for key in ("context_model", "target_model"):
            model = cfg.get(key)
            if model in model_graph:
                step[key] = model
        for key in ("input_models", "output_models"):
            models = [
                str(model)
                for model in (cfg.get(key) or [])
                if str(model) in model_graph
            ]
            if models:
                step[key] = models
        target_model = step.get("target_model") or step.get("context_model") or ""
        readonly_fields = _clean_fields(target_model, cfg.get("readonly_fields") or [])
        editable_fields = _clean_fields(target_model, cfg.get("editable_fields") or [])
        for field in _fields_from_legacy_updates(target_model, cfg.get("field_updates") or []):
            if field not in editable_fields:
                editable_fields.append(field)
        if readonly_fields:
            step["readonly_fields"] = readonly_fields
        if editable_fields:
            step["editable_fields"] = editable_fields
        binding = cfg.get("context_binding")
        if isinstance(binding, dict):
            binding_model = binding.get("model")
            binding_mode = binding.get("mode")
            if binding_model in model_graph and binding_mode in allowed["context_binding_modes"]:
                step["context_binding"] = {"model": binding_model, "mode": binding_mode}
        condition = cfg.get("condition")
        if isinstance(condition, dict):
            condition_model = condition.get("model")
            condition_field = condition.get("field")
            operator = condition.get("operator")
            if (
                condition_model in model_graph
                and condition_field in _valid_fields(condition_model)
                and operator in allowed["condition_operators"]
            ):
                step["condition"] = {
                    "model": condition_model,
                    "field": condition_field,
                    "operator": operator,
                    "threshold": str(condition.get("threshold", "")),
                }
        for key in ("true_next", "false_next"):
            target_action = cfg.get(key)
            if target_action in valid_actions:
                step[key] = target_action
        clean_workflow_steps[action] = step

    return {
        "actor_model_scopes": clean_actor_model_scopes,
        "models": clean_models,
        "activity_steps": clean_steps,
        "workflow_steps": clean_workflow_steps,
    }


def debug_uml_extract(interface_id: str) -> dict:
    """Return UML extraction and planning diagnostics for an interface."""
    try:
        interface = Interface.objects.get(id=interface_id)
        iface = _interface_to_agent_dict(interface)
        system_data = _system_context_from_orm(str(interface.system_id))
        actor_id = str(iface.get("actor") or "")
        actor_name = _actor_name_from_context(system_data, actor_id)

        raw_rels = _sys_as_list(system_data, "relations")
        rel_types = list(
            {
                (r.get("data") or {}).get("type")
                for r in raw_rels
                if isinstance(r, dict) and r.get("data")
            }
        )

        intel = extract_uml_intelligence(system_data, actor_id, actor_name or "")
        plan = generate_interface_plan(intel)
        return {
            "actor": actor_name,
            "rel_types_in_data": rel_types,
            "total_models_in_graph": len(intel["model_graph"]),
            "models_with_compositions": {
                m: [c["model"] for c in info["compositions_owned"]]
                for m, info in intel["model_graph"].items()
                if info["compositions_owned"]
            },
            "models_with_associations": {
                m: [a["model"] for a in info["associations"][:3]]
                for m, info in intel["model_graph"].items()
                if info["associations"]
            },
            "actor_permissions": intel["actor_intel"]["target_permissions"],
            "use_cases": [
                {"name": u["name"], "model": u["primary_model"], "role": u["page_role"]}
                for u in intel["actor_intel"]["target_use_cases"]
            ],
            "workflows": [
                {
                    "name": w["name"],
                    "step_count": w["step_count"],
                    "steps": [
                        {
                            "action": s["action"],
                            "model": s.get("model"),
                            "is_automatic": s.get("is_automatic"),
                            "actor_node_name": s.get("actor_node_name"),
                        }
                        for s in w["steps"]
                    ],
                }
                for w in intel["workflow_intel"]["workflows"]
            ],
            "semantic_decisions": intel["semantic_decisions"],
            "plan_pages": [
                {"id": p["id"], "model": p["primary_model"], "sections": p["sections"]}
                for p in plan["pages"]
            ],
            "plan_sections": [
                {"id": s["id"], "component": s["component"]}
                for s in plan["sections"]
            ],
        }
    except Interface.DoesNotExist:
        return {"error": f"Interface {interface_id} not found."}
    except Exception as exc:
        import traceback

        return {"error": str(exc), "tb": traceback.format_exc()}


def map_uml_to_interface(interface_id: str) -> dict:
    """Run rules-based UML-to-interface mapping and save it via metadata API."""
    if not interface_id:
        return {"status": "error", "message": "interface_id required"}

    try:
        interface = Interface.objects.get(id=interface_id)
        iface = _interface_to_agent_dict(interface)
        system_data = _system_context_from_orm(str(interface.system_id))
        actor_id = str(iface.get("actor") or "")
        actor_name = _actor_name_from_context(system_data, actor_id) or ""

        uml_intel = extract_uml_intelligence(system_data, actor_id, actor_name)
        initial_plan = generate_interface_plan(uml_intel)
        semantic_overrides = resolve_interface_semantics_with_llm(uml_intel, initial_plan)
        plan = (
            generate_interface_plan(uml_intel, semantic_overrides)
            if semantic_overrides
            else initial_plan
        )

        pages = plan["pages"]
        sections = plan["sections"]
        page_model_by_id = {
            str(p.get("id") or ""): str(
                p.get("primary_model") or p.get("model") or p.get("class") or ""
            )
            for p in pages or []
        }
        data_layouts = {
            "card",
            "list",
            "table",
            "detail",
            "gallery",
            "filter",
            "form",
            "timeline",
            "map",
        }
        data_roles = {
            "object_collection",
            "object_detail",
            "object_summary",
            "child_collection",
            "object_form",
            "filter",
        }

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
            is_data_section = (
                layout in data_layouts or role in data_roles or bool(section.get("attributes"))
            )
            if is_data_section and model:
                section["primary_model"] = str(model)
                section["class"] = str(model)
            else:
                section.setdefault("primary_model", "")
                section.setdefault("class", "")
            section["layout"] = layout
            return section

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
                **normalize_section_model(s),
                "operations": _normalize_section_operations(s.get("operations")),
            }
            for s in sections
        ]

        model_attrs = {}
        for classifier in _as_list(system_data.get("classifiers"), "classifiers"):
            cdata = classifier.get("data", {}) if isinstance(classifier, dict) else {}
            cname = cdata.get("name", "")
            attrs = {
                a.get("name", "")
                for a in cdata.get("attributes", [])
                if isinstance(a, dict) and a.get("name")
            }
            if cname:
                model_attrs[cname] = attrs
        usecase_navigation = _build_usecase_navigation(system_data, actor_id, actor_name)
        completed = _apply_builtin_workflow_logic(
            {"pages": db_pages, "sections": db_sections},
            iface.get("system"),
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
        db_pages, db_sections = _ensure_mapping_chrome_sections(db_pages, db_sections)
        db_sections = _drop_unreferenced_non_global_sections(db_pages, db_sections)
        db_sections = _normalize_select_existing_sections(db_pages, db_sections)

        data = dict(interface.data or {})
        data.update({"pages": db_pages, "sections": db_sections})
        Interface.objects.filter(id=interface_id).update(data=data)

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

        logger.error("map_uml_to_interface error: %s", exc)
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
        system_context = _system_context_from_orm(system_id) if system_id else {}
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

        prompt = (
            "Convert the user's UI edit request into one JSON patch for the interface editor.\n"
            "Output JSON only. Do not include markdown.\n"
            "Patch schema: {\"pages\": [...], \"sections\": [...], \"styling\": {...}, \"tokens\": {...}}.\n"
            "Only include fields that must change. Preserve existing human edits unless explicitly asked.\n"
            "Every changed page/section must include its existing id. New page/section ids must be stable snake_case strings.\n"
            "Data-bound section attributes must use only real classifier attributes listed below.\n"
            "Do not invent model fields. For static/chrome/media sections use primary_model='', class='', attributes=[].\n\n"
            f"Actor: {actor_name}\n"
            f"Classifiers: {_json.dumps(classifiers, ensure_ascii=False)}\n"
            f"Current interface: {_json.dumps(current_data, ensure_ascii=False)[:50000]}\n"
            f"User request: {user_request}\n\n"
            f"Editable layout fields:\n{_LAYOUT_SCHEMA}\n\n"
            f"Editable data fields:\n{_DATA_SCHEMA}\n"
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
        raw_text = str(getattr(response, "text", "") or "").strip()
        raw_text = _re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text).strip()
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
