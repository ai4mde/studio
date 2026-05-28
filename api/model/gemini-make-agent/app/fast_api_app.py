# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import google.auth
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

setup_telemetry()
try:
    _, project_id = google.auth.default()
    logging_client = google_cloud_logging.Client()
    cloud_logger = logging_client.logger(__name__)
except Exception:
    cloud_logger = None

import logging as python_logging
logger = python_logging.getLogger(__name__)


def _resolve_interface_semantics_with_llm(uml_intel: dict, interface_plan: dict) -> dict:
    """Ask the LLM to resolve layout/component choices; return safe overrides or {}."""
    import json as _json
    import re as _re
    import requests as _req

    decisions = uml_intel.get("semantic_decisions") or []
    if not decisions:
        return {}
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {}
    model_name = os.getenv("SEMANTIC_RESOLVER_MODEL") or os.getenv("ADK_AGENT_MODEL", "gemini-2.0-flash-lite")
    if "/" in model_name:
        provider, raw_name = model_name.split("/", 1)
        model_name = raw_name if provider == "gemini" else "gemini-2.0-flash-lite"
    elif not model_name.startswith("gemini-"):
        model_name = "gemini-2.0-flash-lite"

    allowed = {
        "model_layouts": ["table", "list", "gallery", "calendar", "timeline", "map"],
        "model_components": ["DataTable", "ObjectList", "CardGrid", "PersonCardGrid", "CategoryTileGrid", "CalendarView", "TimelineList", "MapView"],
        "activity_layouts": ["form", "detail", "list"],
        "activity_components": ["ObjectForm", "DetailPanel", "SummaryPanel", "ObjectList"],
        "activity_roles": ["object_form", "object_detail", "object_collection"],
    }
    prompt = (
        "Resolve UI semantic decisions for a UML-derived interface. Output JSON only.\n"
        "Do not invent models, fields, pages, or unsupported components.\n"
        "Use forms only when the user must enter/create/update data. Use detail/summary for review, consult, monitor, confirm, approve, discharge, analyze.\n\n"
        f"Allowed values: {_json.dumps(allowed)}\n"
        f"Actor permissions: {_json.dumps(uml_intel.get('actor_intel', {}).get('target_permissions', {}), ensure_ascii=False)}\n"
        f"Decisions: {_json.dumps(decisions, ensure_ascii=False)}\n"
        f"Initial plan summary: {_json.dumps({'pages': interface_plan.get('pages', []), 'sections': interface_plan.get('sections', [])}, ensure_ascii=False)[:12000]}\n\n"
        "Schema:\n"
        "{\n"
        '  "models": {"ModelName": {"layout": "table|list|gallery|calendar|timeline|map", "component": "..." }},\n'
        '  "activity_steps": {"Exact action name": {"layout": "form|detail|list", "component": "ObjectForm|DetailPanel|SummaryPanel|ObjectList", "role": "object_form|object_detail|object_collection"}}\n'
        "}\n"
    )
    try:
        resp = _req.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}",
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0, "maxOutputTokens": 2048}},
            timeout=12,
        )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        text = _re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
        raw = _json.loads(text)
    except Exception as e:
        logger.warning(f"semantic resolver fallback to rules: {e}")
        return {}

    valid_models = set((uml_intel.get("actor_intel") or {}).get("target_permissions") or {})
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
    clean_steps = {}
    for action, cfg in (raw.get("activity_steps") or {}).items():
        if action not in valid_actions or not isinstance(cfg, dict):
            continue
        layout = cfg.get("layout")
        component = cfg.get("component")
        role = cfg.get("role")
        if layout in allowed["activity_layouts"] and component in allowed["activity_components"]:
            clean_steps[action] = {
                "layout": layout,
                "component": component,
                "role": role if role in allowed["activity_roles"] else "",
            }

    return {"models": clean_models, "activity_steps": clean_steps}

allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

# Artifact bucket for ADK (created by Terraform, passed via env var)
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
session_service_uri = os.environ.get("SESSION_SERVICE_URI")
artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
)
app.title = "gemini-make-agent"
app.description = "API for interacting with the Agent gemini-make-agent"


@app.middleware("http")
async def root_health_response(request: Request, call_next):
    """Avoid noisy ADK root redirects from Docker/Traefik health probes."""
    if request.url.path == "/":
        return JSONResponse({"status": "ok", "service": "gemini-make-agent"})
    return await call_next(request)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/debug_uml_extract/{interface_id}")
def debug_uml_extract(interface_id: str) -> dict:
    import os, requests as _req
    from app.uml_extractor import extract_uml_intelligence
    from app.interface_planner import generate_interface_plan
    METADATA_API_BASE = os.getenv("METADATA_API_BASE", "http://studio-api:8000/api/v1/metadata")
    KEY = os.getenv("METADATA_API_KEY")
    H = {"Authorization": f"Bearer {KEY}"} if KEY else {}
    try:
        from app.tools import _fetch_system_context_data, _actor_name_from_context
        iface = _req.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=H, timeout=30).json()
        system_data = _fetch_system_context_data(iface.get("system"))
        actor_id = str(iface.get("actor") or "")
        actor_name = _actor_name_from_context(system_data, actor_id)

        # show raw relation types present in data
        from app.uml_extractor import _sys_as_list
        raw_rels = _sys_as_list(system_data, "relations")
        rel_types = list({(r.get("data") or {}).get("type") for r in raw_rels if isinstance(r, dict) and r.get("data")})

        intel = extract_uml_intelligence(system_data, actor_id, actor_name or "")
        plan = generate_interface_plan(intel)
        return {
            "actor": actor_name,
            "rel_types_in_data": rel_types,
            "total_models_in_graph": len(intel["model_graph"]),
            "models_with_compositions": {m: [c["model"] for c in info["compositions_owned"]] for m, info in intel["model_graph"].items() if info["compositions_owned"]},
            "models_with_associations": {m: [a["model"] for a in info["associations"][:3]] for m, info in intel["model_graph"].items() if info["associations"]},
            "actor_permissions": intel["actor_intel"]["target_permissions"],
            "use_cases": [{"name": u["name"], "model": u["primary_model"], "role": u["page_role"]} for u in intel["actor_intel"]["target_use_cases"]],
            "workflows": [{"name": w["name"], "step_count": w["step_count"], "steps": [{"action": s["action"], "model": s.get("model"), "is_automatic": s.get("is_automatic"), "actor_node_name": s.get("actor_node_name")} for s in w["steps"]]} for w in intel["workflow_intel"]["workflows"]],
            "semantic_decisions": intel["semantic_decisions"],
            "plan_pages": [{"id": p["id"], "model": p["primary_model"], "sections": p["sections"]} for p in plan["pages"]],
            "plan_sections": [{"id": s["id"], "component": s["component"]} for s in plan["sections"]],
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "tb": traceback.format_exc()}


@app.post("/map_uml_to_interface")
def map_uml_to_interface(payload: dict) -> dict:
    """Directly run rules-based UML→interface mapping and save to DB."""
    import json as _json
    import requests as _req
    from app.uml_extractor import extract_uml_intelligence
    from app.interface_planner import generate_interface_plan
    from app.tools import (
        _fetch_system_context_data,
        _actor_name_from_context,
        _normalize_layout_alias,
        _normalize_section_operations,
        METADATA_API_BASE,
        _AUTH_HEADERS,
    )

    interface_id = str(payload.get("interface_id") or "")
    if not interface_id:
        return {"status": "error", "message": "interface_id required"}

    try:
        iface = _req.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS, timeout=30).json()
        system_data = _fetch_system_context_data(iface.get("system"))
        actor_id = str(iface.get("actor") or "")
        actor_name = _actor_name_from_context(system_data, actor_id) or ""

        uml_intel = extract_uml_intelligence(system_data, actor_id, actor_name)
        initial_plan = generate_interface_plan(uml_intel)
        semantic_overrides = _resolve_interface_semantics_with_llm(uml_intel, initial_plan)
        plan = generate_interface_plan(uml_intel, semantic_overrides) if semantic_overrides else initial_plan

        pages = plan["pages"]
        sections = plan["sections"]
        page_model_by_id = {
            str(p.get("id") or ""): str(p.get("primary_model") or p.get("model") or p.get("class") or "")
            for p in pages or []
        }
        data_layouts = {"card", "list", "table", "detail", "gallery", "filter", "form", "calendar", "timeline", "map"}
        data_roles = {"object_collection", "object_detail", "object_summary", "child_collection", "object_form", "filter"}

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
            is_data_section = layout in data_layouts or role in data_roles or bool(section.get("attributes"))
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
                "sections": [{"value": sid} for sid in (p.get("sections") or [])],
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

        resp = _req.patch(
            f"{METADATA_API_BASE}/interfaces/{interface_id}/data/",
            json={"pages": db_pages, "sections": db_sections},
            headers=_AUTH_HEADERS,
            timeout=30,
        )
        resp.raise_for_status()

        return {
            "status": "ok",
            "message": f"Mapped {len(db_pages)} pages and {len(db_sections)} sections.",
            "page_count": len(db_pages),
            "section_count": len(db_sections),
        }
    except Exception as e:
        import traceback
        logger.error(f"map_uml_to_interface error: {e}")
        return {"status": "error", "message": str(e), "detail": traceback.format_exc()}


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    if cloud_logger:
        try:
            cloud_logger.log_struct(feedback.model_dump(), severity="INFO")
        except Exception as e:
            logger.error(f"Failed to log to Cloud Logging: {e}")
            logger.info(f"Feedback: {feedback.model_dump()}")
    else:
        logger.info(f"Feedback: {feedback.model_dump()}")
        
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
