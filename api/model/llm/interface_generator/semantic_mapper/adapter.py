"""
Adapter: system_data → TKB engine metadata format.

system_data (from _fetch_system_context_data) has:
  - node.cls = classifier UUID string
  - edge.rel = relation UUID string

The TKB engine expects:
  - node.cls_ptr = classifier UUID
  - node.cls = embedded classifier data dict
  - edge.source / edge.target = node UUIDs (for UseCase per_edge_actor)
  - edge.source_ptr / edge.target_ptr = classifier UUIDs (for class edge matching)
  - edge.rel = {"data": {...}} with type and multiplicity

Activity diagrams are already enriched by _build_activity_diagrams in system_data
as system_data["activity_diagrams"] — those are used as-is.
"""

from __future__ import annotations


def enrich_diagrams(system_data: dict) -> list[dict]:
    """
    Return a list of diagrams ready for the TKB engine.

    UseCase and Class diagrams are enriched from the raw system_data.
    Activity diagrams are taken from system_data["activity_diagrams"]
    (already pre-enriched by _build_activity_diagrams).
    """
    classifiers = {
        str(c.get("id") or ""): c.get("data", {}) or {}
        for c in system_data.get("classifiers", [])
        if c.get("id")
    }
    relations = {
        str(r.get("id") or ""): r
        for r in system_data.get("relations", [])
        if r.get("id")
    }

    result: list[dict] = []

    for diagram in system_data.get("diagrams", []):
        dtype = diagram.get("type", "")
        if dtype == "activity":
            continue  # handled below via activity_diagrams

        enriched_nodes, node_by_cls = _enrich_nodes(diagram, classifiers)
        enriched_edges = _enrich_edges(diagram, relations, node_by_cls, dtype)

        result.append({
            "id": str(diagram.get("id") or ""),
            "type": dtype,
            "nodes": enriched_nodes,
            "edges": enriched_edges,
        })

    # Activity diagrams — already enriched by usecase_workflow._build_activity_diagrams
    for ad in system_data.get("activity_diagrams", []):
        # Normalise cls field: _build_activity_diagrams stores cls as a flat dict
        # (no nested "data" key) which cls_data() handles via its fallback branch.
        result.append(ad)

    return result


def _enrich_nodes(
    diagram: dict, classifiers: dict[str, dict]
) -> tuple[list[dict], dict[str, str]]:
    """Enrich diagram nodes and return (enriched_nodes, node_by_cls_id)."""
    enriched: list[dict] = []
    node_by_cls: dict[str, str] = {}  # classifier_id → node_id

    for node in diagram.get("nodes", []):
        node_id = str(node.get("id") or "")
        cls_id = str(node.get("cls") or node.get("cls_ptr") or "")
        cls_data = dict(classifiers.get(cls_id, {}))

        # node.data may carry type overrides (e.g. UseCase node type)
        node_data = node.get("data") or {}
        merged = {**cls_data, **node_data}

        if cls_id:
            node_by_cls[cls_id] = node_id

        enriched.append({
            "id": node_id,
            "cls_ptr": cls_id or node_id,
            "cls": {"data": merged},
        })

    return enriched, node_by_cls


def _enrich_edges(
    diagram: dict,
    relations: dict[str, dict],
    node_by_cls: dict[str, str],
    dtype: str,
) -> list[dict]:
    """
    Enrich diagram edges with resolved source/target and relation data.

    Field semantics differ by diagram type:
      - UseCase: `source`/`target` = node UUIDs (used by edge_source_id → find_node)
        No source_ptr/target_ptr — they would shadow `source`/`target` in edge_source_id.
      - Classes: `source_ptr`/`target_ptr` = classifier UUIDs (used by _run_on_edges
        and find_node_by_ptr). Also set `source`/`target` as node UUIDs for completeness.
    """
    enriched: list[dict] = []

    for edge in diagram.get("edges", []):
        rel_id = str(edge.get("rel") or "")
        relation = relations.get(rel_id, {})
        rel_data = dict(relation.get("data", {}) or {})

        src_cls_id = str(relation.get("source") or "")
        tgt_cls_id = str(relation.get("target") or "")
        src_node_id = node_by_cls.get(src_cls_id, "")
        tgt_node_id = node_by_cls.get(tgt_cls_id, "")

        base = {
            "id": str(edge.get("id") or ""),
            "rel": {"data": rel_data},
            "source": src_node_id,
            "target": tgt_node_id,
        }

        if dtype == "classes":
            # Class diagram edges need classifier UUIDs for _run_on_edges matching
            base["source_ptr"] = src_cls_id
            base["target_ptr"] = tgt_cls_id

        enriched.append(base)

    return enriched


def system_data_to_tkb_input(system_data: dict) -> dict:
    """
    Convert system_data into TKB engine input format.

    Returns a dict with 'diagrams' and 'classifiers' keys.
    """
    return {
        "diagrams": enrich_diagrams(system_data),
        "classifiers": system_data.get("classifiers", []),
    }


def extract_interface_for_actor(
    tkb_output: dict,
    actor_name: str,
    system_data: dict | None = None,
) -> tuple[list[dict], list[dict]]:
    """
    Pull pages and sections for a specific actor from TKB engine output.

    Resolves section.class UUID → class name so the existing
    normalize_section_model() in django_service.py works correctly.

    Args:
        tkb_output: dict returned by TransformationEngine.transform()
        actor_name: sanitized actor name (must match interface label)
        system_data: optional system context for UUID→name resolution

    Returns:
        (pages, sections) ready for Interface.data update
    """
    from .sanitization import app_name_sanitization

    target_label = app_name_sanitization(actor_name)

    cls_name_by_id: dict[str, str] = {}
    if system_data:
        for c in system_data.get("classifiers", []):
            cid = str(c.get("id") or "")
            cname = (c.get("data") or {}).get("name", "")
            if cid and cname:
                cls_name_by_id[cid] = cname

    for iface in tkb_output.get("interfaces", []):
        label = iface.get("label", "")
        if label == target_label or app_name_sanitization(label) == target_label:
            data = iface.get("value", {}).get("data", {})
            pages = data.get("pages", [])
            sections = _resolve_class_uuids(data.get("sections", []), cls_name_by_id)
            return pages, sections

    return [], []


def _resolve_class_uuids(sections: list[dict], cls_name_by_id: dict[str, str]) -> list[dict]:
    """
    Replace section.class UUID with the class name string so that
    normalize_section_model() in django_service.py can resolve the model.
    """
    resolved = []
    for s in sections:
        s = dict(s)
        cls_ptr = str(s.get("class") or "")
        if cls_ptr and cls_ptr in cls_name_by_id:
            cls_name = cls_name_by_id[cls_ptr]
            s["class"] = cls_name
            s.setdefault("primary_model", cls_name)
        resolved.append(s)
    return resolved
