"""Interface patch application for the root refinement agent."""

import requests

from .service_clients import METADATA_API_BASE, _AUTH_HEADERS
from .tools import (
    _apply_builtin_workflow_logic,
    _build_known_attrs,
    _infer_section_component,
    _normalize_activity_action_sections,
)


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
                        warnings.append(f"section '{sec.get('id')}': unknown attributes {bad} for model '{model}' ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â valid: {sorted(valid)}")
            if warnings:
                return "WARNING ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â patch rejected due to invented attribute names. Fix these and retry:\n" + "\n".join(warnings)
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
        put_resp = requests.put(f"{METADATA_API_BASE}/interfaces/{interface_id}/", json=payload, headers=_AUTH_HEADERS, timeout=60)
        if not put_resp.ok:
            return f"Error patching interface: metadata PUT failed ({put_resp.status_code}): {put_resp.text[:1000]}"
        return f"Patched interface {interface_id} successfully."
    except Exception as e: return f"Error patching interface: {e}"

