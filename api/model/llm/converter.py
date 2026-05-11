import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)

REFERENCE_TOP_LEVEL_KEYS = {
    "classifiers",
    "description",
    "diagrams",
    "id",
    "imported_classifiers",
    "interfaces",
    "name",
    "project",
    "relations",
}
REFERENCE_CLASSIFIER_KEYS = {"data", "id", "original_system_id", "project", "system"}
REFERENCE_RELATION_KEYS = {"data", "id", "source", "system", "target"}
REFERENCE_CONTROLFLOW_DATA_KEYS = {
    "condition",
    "guard",
    "is_directed",
    "position_handlers",
    "type",
    "weight",
}
REFERENCE_OBJECTFLOW_DATA_KEYS = {
    "cls",
    "guard",
    "is_directed",
    "position_handlers",
    "type",
    "weight",
}
REFERENCE_DIAGRAM_KEYS = {"description", "edges", "id", "name", "nodes", "system", "type"}
REFERENCE_NODE_KEYS = {"cls", "data", "diagram", "id"}
REFERENCE_NODE_DATA_KEYS = {"position"}
REFERENCE_POSITION_KEYS = {"x", "y"}
REFERENCE_EDGE_KEYS = {"data", "diagram", "id", "rel"}
REFERENCE_ACTION_KEYS = {
    "body",
    "isAutomatic",
    "localPostcondition",
    "localPrecondition",
    "name",
    "namespace",
    "role",
    "type",
}
REFERENCE_INITIAL_KEYS = {"activity_scope", "role", "schedule", "scheduled", "type"}
REFERENCE_FINAL_KEYS = {"activity_scope", "role", "type"}

EDGE_TYPE_MAPPING = {
    "control": "controlflow",
    "object": "objectflow",
    # Accept legacy values without changing them again.
    "controlflow": "controlflow",
    "objectflow": "objectflow",
}


def _derive_role(node_type: str) -> str:
    if node_type in {"initial", "final", "decision", "merge", "fork", "join"}:
        return "control"
    if node_type == "action":
        return "action"
    if node_type == "object":
        return "object"
    return "action"


def _validate_exact_keys(actual: set[str], expected: set[str], label: str) -> None:
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"{label} keys mismatch: missing={missing}, extra={extra}")


def unwrap_ai4mde_systems_export(
    model: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> Dict[str, Any]:
    if isinstance(model, list):
        if len(model) != 1:
            raise ValueError("AI4MDE export payload must contain exactly one system object")
        system = model[0]
        if not isinstance(system, dict):
            raise ValueError("AI4MDE export payload entry must be a dict")
        return system
    if not isinstance(model, dict):
        raise ValueError("AI4MDE model must be a dict or single-item list")
    return model


def validate_ai4mde_json(model: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
    """
    Validate a single-system AI4MDE export payload against the native Studio shape.

    Raises ``ValueError`` with a concrete message on structural problems so
    callers fail locally instead of with an opaque 422 from the API.
    """
    system = unwrap_ai4mde_systems_export(model)

    _validate_exact_keys(set(system.keys()), REFERENCE_TOP_LEVEL_KEYS, "system")

    project_id = str(system.get("project") or "").strip()
    if not project_id or project_id == "00000000-0000-0000-0000-000000000000":
        raise ValueError("system.project must be a real project UUID")

    classifiers = system.get("classifiers")
    relations = system.get("relations")
    diagrams = system.get("diagrams")
    if not isinstance(classifiers, list):
        raise ValueError("classifiers must be a list")
    if not isinstance(relations, list):
        raise ValueError("relations must be a list")
    if not isinstance(diagrams, list):
        raise ValueError("diagrams must be a list")

    cls_ids: Set[str] = set()
    for i, c in enumerate(classifiers):
        if not isinstance(c, dict):
            raise ValueError(f"classifiers[{i}] must be a dict")
        _validate_exact_keys(set(c.keys()), REFERENCE_CLASSIFIER_KEYS, f"classifiers[{i}]")
        cid = c.get("id")
        if not cid:
            raise ValueError(f"classifiers[{i}] missing id")
        sid = str(cid)
        if sid in cls_ids:
            raise ValueError(f"duplicate classifier id: {sid}")
        cls_ids.add(sid)
        if str(c.get("project")) != project_id:
            raise ValueError(f"classifier {sid} project does not match system.project")
        if c.get("original_system_id", None) is not None:
            raise ValueError(f"classifier {sid} original_system_id must be null")

        data = c.get("data")
        if not isinstance(data, dict):
            raise ValueError(f"classifier {sid} data must be a dict")
        node_type = str(data.get("type") or "")
        if node_type == "action":
            _validate_exact_keys(set(data.keys()), REFERENCE_ACTION_KEYS, f"classifier {sid} action data")
        elif node_type == "initial":
            _validate_exact_keys(set(data.keys()), REFERENCE_INITIAL_KEYS, f"classifier {sid} initial data")
        elif node_type == "final":
            _validate_exact_keys(set(data.keys()), REFERENCE_FINAL_KEYS, f"classifier {sid} final data")

    rel_ids: Set[str] = set()
    for i, r in enumerate(relations):
        if not isinstance(r, dict):
            raise ValueError(f"relations[{i}] must be a dict")
        _validate_exact_keys(set(r.keys()), REFERENCE_RELATION_KEYS, f"relations[{i}]")
        rid = r.get("id")
        if not rid:
            raise ValueError(f"relations[{i}] missing id")
        rsid = str(rid)
        if rsid in rel_ids:
            raise ValueError(f"duplicate relation id: {rsid}")
        rel_ids.add(rsid)
        src, tgt = r.get("source"), r.get("target")
        if src is None or tgt is None:
            raise ValueError(
                f"relation {rsid} missing source or target "
                f"(source={src!r}, target={tgt!r})"
            )
        src_s, tgt_s = str(src), str(tgt)
        if src_s not in cls_ids:
            raise ValueError(
                f"relation {rsid} source {src_s!r} is not a known classifier id"
            )
        if tgt_s not in cls_ids:
            raise ValueError(
                f"relation {rsid} target {tgt_s!r} is not a known classifier id"
            )
        data = r.get("data")
        if not isinstance(data, dict):
            raise ValueError(f"relation {rsid} data must be a dict")
        relation_type = str(data.get("type") or "")
        if relation_type == "controlflow":
            _validate_exact_keys(
                set(data.keys()),
                REFERENCE_CONTROLFLOW_DATA_KEYS,
                f"relation {rsid} data",
            )
        elif relation_type == "objectflow":
            _validate_exact_keys(
                set(data.keys()),
                REFERENCE_OBJECTFLOW_DATA_KEYS,
                f"relation {rsid} data",
            )
        else:
            raise ValueError(
                f"relation {rsid} data.type {relation_type!r} is not a valid AI4MDE activity relation type"
            )

    node_ids: Set[str] = set()
    edge_ids: Set[str] = set()

    for d_idx, d in enumerate(diagrams):
        if not isinstance(d, dict):
            raise ValueError(f"diagrams[{d_idx}] must be a dict")
        _validate_exact_keys(set(d.keys()), REFERENCE_DIAGRAM_KEYS, f"diagrams[{d_idx}]")
        nodes = d.get("nodes")
        edges = d.get("edges")
        if not isinstance(nodes, list):
            raise ValueError(f"diagrams[{d_idx}].nodes must be a list")
        if not isinstance(edges, list):
            raise ValueError(f"diagrams[{d_idx}].edges must be a list")

        for n_idx, n in enumerate(nodes):
            if not isinstance(n, dict):
                raise ValueError(f"diagrams[{d_idx}].nodes[{n_idx}] must be a dict")
            _validate_exact_keys(set(n.keys()), REFERENCE_NODE_KEYS, f"diagrams[{d_idx}].nodes[{n_idx}]")
            nid = str(n["id"])
            if nid in node_ids:
                raise ValueError(f"duplicate node id: {nid}")
            node_ids.add(nid)
            ncls = str(n["cls"])
            if ncls not in cls_ids:
                raise ValueError(
                    f"node {nid} cls {ncls!r} is not listed in classifiers"
                )
            node_data = n.get("data")
            if not isinstance(node_data, dict):
                raise ValueError(f"node {nid} data must be a dict")
            _validate_exact_keys(set(node_data.keys()), REFERENCE_NODE_DATA_KEYS, f"node {nid} data")
            position = node_data.get("position")
            if not isinstance(position, dict):
                raise ValueError(f"node {nid} data.position must be a dict")
            _validate_exact_keys(set(position.keys()), REFERENCE_POSITION_KEYS, f"node {nid} position")

        for e_idx, e in enumerate(edges):
            if not isinstance(e, dict):
                raise ValueError(f"diagrams[{d_idx}].edges[{e_idx}] must be a dict")
            _validate_exact_keys(set(e.keys()), REFERENCE_EDGE_KEYS, f"diagrams[{d_idx}].edges[{e_idx}]")
            eid = str(e["id"])
            if eid in edge_ids:
                raise ValueError(f"duplicate edge id: {eid}")
            edge_ids.add(eid)
            erel = str(e["rel"])
            if erel not in rel_ids:
                raise ValueError(
                    f"edge {eid} rel {erel!r} is not listed in relations"
                )


def convert_to_ai4mde(
    clean_model: Dict[str, Any],
    system_id: str,
    diagram_id: str,
    name: str = "GeneratedActivity",
    description: str = "",
    project_id: Optional[str] = None,
    *,
    wrap_as_systems_array: bool = True,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Convert a clean activity JSON model into an AI4MDE export-compatible structure.

    The Studio ``System.import_from_json`` path imports top-level ``classifiers``
    and ``relations`` before ``diagrams``. Embeddings under ``cls_data`` /
    ``rel_data`` alone are not enough: nodes reference classifiers and edges
    reference relations that must already exist in those lists.

    ``project_id`` is required and must be the UUID of an existing Studio
    project. The converter never invents project ids.

    Each classifier includes ``original_system_id: null`` to match native exports.

    **File / UI import shape:** Some importers expect a JSON **array** of systems
    (same as multi-system export). Set ``wrap_as_systems_array=True`` to return
    ``[ { ...system... } ]`` instead of a single object.

    ``imported_classifiers`` is always present (possibly empty) for release
    import payloads.
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    classifiers: List[Dict[str, Any]] = []
    relations: List[Dict[str, Any]] = []

    classifier_id_by_clean_id: Dict[str, str] = {}
    node_type_by_clean_id: Dict[str, str] = {}

    if not project_id or not str(project_id).strip():
        raise ValueError("project_id is required and must refer to an existing Project")
    export_project_id = str(project_id)
    system_project_id = str(project_id)

    node_vertical_spacing = 120
    start_y = 0

    for index, node in enumerate(clean_model.get("nodes", [])):
        original_id = str(node.get("id"))
        cls_id = str(uuid.uuid4())
        node_id = str(uuid.uuid4())

        node_type = str(node.get("type", "action"))
        node_name = node.get("name")
        role = _derive_role(node_type)

        base_data: Dict[str, Any] = {
            "role": role,
            "type": node_type,
        }

        if node_type in {"initial", "final"}:
            base_data["activity_scope"] = "activity"
            if node_type == "initial":
                base_data["schedule"] = ""
                base_data["scheduled"] = False

        if node_type == "action":
            base_data["name"] = node_name or ""
            base_data["body"] = ""
            base_data["localPrecondition"] = ""
            base_data["localPostcondition"] = ""
            base_data["namespace"] = ""
            base_data["isAutomatic"] = False

        cls_payload: Dict[str, Any] = {
            "id": cls_id,
            "project": export_project_id,
            "system": system_id,
            "original_system_id": None,
            "data": base_data,
        }
        classifiers.append(cls_payload)

        node_payload: Dict[str, Any] = {
            "id": node_id,
            "diagram": diagram_id,
            "cls": cls_id,
            "data": {
                "position": {
                    "x": 0,
                    "y": start_y + index * node_vertical_spacing,
                }
            },
        }

        classifier_id_by_clean_id[original_id] = cls_id
        node_type_by_clean_id[original_id] = node_type
        nodes.append(node_payload)

    for edge in clean_model.get("edges", []):
        rel_id = str(uuid.uuid4())
        edge_id = str(uuid.uuid4())

        clean_edge_type = str(edge.get("type") or "control")
        edge_type = EDGE_TYPE_MAPPING.get(clean_edge_type, clean_edge_type)
        raw_condition = edge.get("condition")
        guard = str(raw_condition) if raw_condition is not None else ""
        condition_value = None

        source_original = str(edge.get("source"))
        target_original = str(edge.get("target"))

        source_cls = classifier_id_by_clean_id.get(source_original)
        target_cls = classifier_id_by_clean_id.get(target_original)
        if source_cls is None:
            raise ValueError(
                f"edge references unknown source node id {source_original!r} "
                f"(known: {list(classifier_id_by_clean_id.keys())})"
            )
        if target_cls is None:
            raise ValueError(
                f"edge references unknown target node id {target_original!r} "
                f"(known: {list(classifier_id_by_clean_id.keys())})"
            )

        if edge_type == "controlflow":
            relation_data: Dict[str, Any] = {
                "type": edge_type,
                "guard": guard,
                "weight": "",
                "condition": condition_value,
                "is_directed": True,
                "position_handlers": [],
            }
        elif edge_type == "objectflow":
            object_cls = ""
            if node_type_by_clean_id.get(source_original) == "object":
                object_cls = source_cls
            elif node_type_by_clean_id.get(target_original) == "object":
                object_cls = target_cls

            relation_data = {
                "type": edge_type,
                "guard": guard,
                "weight": "",
                "cls": object_cls,
                "is_directed": True,
                "position_handlers": [],
            }
        else:
            raise ValueError(
                f"edge type {clean_edge_type!r} is not supported for AI4MDE conversion"
            )

        rel_payload: Dict[str, Any] = {
            "id": rel_id,
            "data": relation_data,
            "system": system_id,
            "source": source_cls,
            "target": target_cls,
        }
        relations.append(rel_payload)

        edge_payload: Dict[str, Any] = {
            "id": edge_id,
            "diagram": diagram_id,
            "rel": rel_id,
            "data": {},
        }

        edges.append(edge_payload)

    result: Dict[str, Any] = {
        "interfaces": [],
        "imported_classifiers": [],
        "classifiers": classifiers,
        "relations": relations,
        "diagrams": [
            {
                "nodes": nodes,
                "edges": edges,
                "id": diagram_id,
                "type": "activity",
                "name": name,
                "description": description,
                "system": system_id,
            }
        ],
        "id": system_id,
        "name": name,
        "description": description,
        "project": system_project_id,
    }

    exported: Union[Dict[str, Any], List[Dict[str, Any]]]
    if wrap_as_systems_array:
        exported = [result]
    else:
        exported = result

    validate_ai4mde_json(exported)

    try:
        dumped = json.dumps(exported, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        logger.warning("AI4MDE JSON not serializable: %s", exc)
    else:
        max_len = 16000
        if len(dumped) > max_len:
            logger.debug(
                "AI4MDE export JSON (%d chars, truncated): %s…",
                len(dumped),
                dumped[:max_len],
            )
        else:
            logger.debug("AI4MDE export JSON: %s", dumped)

    return exported
