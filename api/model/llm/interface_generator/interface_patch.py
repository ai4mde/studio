"""Interface patch application for Django-hosted interface refinement."""

from metadata.models import Classifier, Interface
from .section_utils import (
    _normalize_select_existing_sections,
    _infer_section_component,
    _normalize_activity_action_sections,
)
from .workflow_application import _apply_builtin_workflow_logic


def _build_known_attrs_from_orm(system_id: str) -> dict[str, set[str]]:
    """Build known attrs from orm."""
    known: dict[str, set[str]] = {}
    for classifier in Classifier.objects.filter(system_id=system_id):
        cdata = classifier.data or {}
        name = cdata.get("name", "")
        if not name:
            continue
        known[name] = {
            attr.get("name", "")
            for attr in (cdata.get("attributes") or [])
            if isinstance(attr, dict) and attr.get("name")
        }
    return known


def _drop_deprecated_section_fields(section: dict) -> dict:
    """Remove deprecated per-record action fields from incoming section patches."""
    section = dict(section or {})
    section.pop("item_actions", None)
    return section


def _norm_refs(refs: list) -> list:
    """Normalize page section references to canonical ref objects."""
    out = []
    for ref in refs or []:
        if isinstance(ref, dict) and ref.get("type") == "card":
            card = {k: v for k, v in ref.items() if k != "sections"}
            card["sections"] = [
                {"value": str(s.get("value") or s)} if isinstance(s, dict) else {"value": str(s)}
                for s in (ref.get("sections") or [])
                if (s.get("value") if isinstance(s, dict) else s)
            ]
            out.append(card)
        else:
            sid = ref.get("value") if isinstance(ref, dict) else ref
            if sid:
                out.append({"value": str(sid)})
    return out


_SECTION_UPDATE_FIELDS = (
    "role", "layout", "component", "col_span", "position", "attributes", "field_layout",
    "behavior", "related_to", "relationship", "relation_field", "data_source", "query",
    "workflow", "label", "target_page", "workflow_action", "primary_model", "class",
    "text", "methods", "min_height",
)

_PAGE_UPDATE_FIELDS = ("layout", "gap", "name", "primary_model", "category", "type")


def _apply_sections_patch(data: dict, patch_sections: list) -> dict:
    """Apply the sections portion of a patch to the interface data dict."""
    section_map = {str(s["id"]): s for s in data.get("sections", [])}
    for raw_ps in patch_sections:
        ps = _drop_deprecated_section_fields(raw_ps)
        sid = str(ps.get("id", ""))
        if not sid:
            continue
        if sid not in section_map:
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
        for field in _SECTION_UPDATE_FIELDS:
            if field in ps:
                section_map[sid][field] = ps[field]
        if "style" in ps:
            section_map[sid]["style"] = {**(section_map[sid].get("style") or {}), **ps["style"]}
    data["sections"] = list(section_map.values())
    return data


def _apply_pages_patch(data: dict, patch_pages: list) -> dict:
    """Apply the pages portion of a patch to the interface data dict."""
    page_map = {str(p["id"]): p for p in data.get("pages", [])}
    for pp in patch_pages:
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
        for field in _PAGE_UPDATE_FIELDS:
            if field in pp:
                page_map[pid][field] = pp[field]
        if "sections" in pp:
            page_map[pid]["sections"] = _norm_refs(pp["sections"])
    data["pages"] = list(page_map.values())
    return data


def _validate_section_attrs(patch_sections: list, system_id: str) -> str | None:
    """Validate attribute names against known ORM classifier fields. Returns a warning string or None."""
    known_attrs = _build_known_attrs_from_orm(system_id)
    warnings = []
    for sec in patch_sections:
        model = sec.get("primary_model") or sec.get("class", "")
        raw_attrs = sec.get("attributes") or []
        attr_names = [a if isinstance(a, str) else (a.get("name") if isinstance(a, dict) else "") for a in raw_attrs]
        valid = known_attrs.get(model, set())
        if valid:
            bad = [a for a in attr_names if a and a not in valid and "." not in a]
            if bad:
                warnings.append(f"section '{sec.get('id')}': unknown attributes {bad} for model '{model}' — valid: {sorted(valid)}")
    if warnings:
        return "WARNING — patch rejected due to invented attribute names. Fix these and retry:\n" + "\n".join(warnings)
    return None


def apply_interface_patch(interface_id: str, patch: dict) -> str:
    """Apply interface patch."""
    try:
        interface = Interface.objects.get(id=interface_id)
        data = dict(interface.data or {})

        if "sections" in patch:
            data = _apply_sections_patch(data, patch["sections"])
        if "pages" in patch:
            data = _apply_pages_patch(data, patch["pages"])
        if "styling" in patch:
            data["styling"] = {**(data.get("styling") or {}), **patch["styling"]}
        if "tokens" in patch:
            data["tokens"] = {**(data.get("tokens") or {}), **patch["tokens"]}
        if "sections" in patch:
            warning = _validate_section_attrs(patch["sections"], str(interface.system_id))
            if warning:
                return warning
        try:
            data = _apply_builtin_workflow_logic(
                data,
                str(interface.system_id),
                str(interface.actor_id) if interface.actor_id else "",
            )
        except Exception:
            data["sections"] = _normalize_activity_action_sections(data.get("pages") or [], data.get("sections") or [])
        data["sections"] = _normalize_select_existing_sections(data.get("pages") or [], data.get("sections") or [])
        Interface.objects.filter(id=interface_id).update(data=data)
        return f"Patched interface {interface_id} successfully."
    except Interface.DoesNotExist:
        return f"Error patching interface: Interface {interface_id} not found."
    except Exception as e:
        return f"Error patching interface: {e}"
