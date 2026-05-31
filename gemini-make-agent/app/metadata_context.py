"""Metadata context tools shared by ADK tools and FastAPI endpoints."""

import json
import os

import requests

from .service_clients import METADATA_API_BASE, _AUTH_HEADERS
from .styling_engine import _as_list
from .tools import _build_activity_diagrams, _build_usecase_navigation, _workflow_plan


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



def get_interface_full_context(interface_id: str) -> str:
    try:
        iface_resp = requests.get(f"{METADATA_API_BASE}/interfaces/{interface_id}/", headers=_AUTH_HEADERS); iface_resp.raise_for_status(); iface = iface_resp.json(); system_id = iface.get("system"); system_ctx = _fetch_system_context_data(system_id) if system_id else {}; actor_id = iface.get("actor"); actor_name = None
        for classifier in _as_list(system_ctx.get("classifiers"), "classifiers"):
            if str(classifier.get("id")) == str(actor_id): actor_name = (classifier.get("data") or {}).get("name"); break
        system_ctx["workflow_plan"] = _workflow_plan(system_ctx, str(actor_id or ""), actor_name); system_ctx["usecase_navigation"] = _build_usecase_navigation(system_ctx, str(actor_id or ""), actor_name); iface_clean = {k: v for k, v in iface.items() if k != "data"}; iface_clean["actor_name"] = actor_name or iface.get("actor_name") or iface.get("actor")
        # Build an explicit modelÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢attributes quick reference to prevent LLM from inventing field names
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

