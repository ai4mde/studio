import uuid
from typing import Dict, Any, List


def _derive_role(node_type: str) -> str:
    if node_type in {"initial", "final", "decision", "merge", "fork", "join"}:
        return "control"
    if node_type == "action":
        return "action"
    if node_type == "object":
        return "object"
    return "action"


def convert_to_ai4mde(
    clean_model: Dict[str, Any],
    system_id: str,
    diagram_id: str,
    name: str = "GeneratedActivity",
    description: str = "",
) -> Dict[str, Any]:
    """
    Convert a clean activity JSON model into an AI4MDE export-compatible structure.
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    # Map from clean node id (e.g. "n1") to classifier id (cls_data.id)
    classifier_id_by_clean_id: Dict[str, str] = {}

    project_id = str(uuid.uuid4())

    # Simple auto-layout: place nodes in a vertical column with spacing,
    # so they don't overlap in the diagram editor.
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

        # Align with existing AI4MDE activity classifier defaults so that
        # Pydantic validation and frontend expectations are satisfied.
        if node_type in {"initial", "final"}:
            base_data["activity_scope"] = "activity"
            # Control nodes in existing examples also carry scheduling fields.
            base_data.setdefault("schedule", "")
            base_data.setdefault("scheduled", False)

        if node_type not in {"initial", "final"} and role == "control":
            # Other control nodes (decision, merge, fork, join) commonly
            # include scheduling fields as well.
            base_data.setdefault("schedule", "")
            base_data.setdefault("scheduled", False)

        if node_type == "action":
            # Minimal required fields
            base_data["name"] = node_name or ""
            base_data["body"] = ""
            base_data["localPrecondition"] = ""
            base_data["localPostcondition"] = ""
            # Additional optional fields observed in SimpleActivityTest.json
            base_data.setdefault("page", None)
            base_data.setdefault("classes", None)
            base_data.setdefault("publish", None)
            base_data.setdefault("actorNode", None)
            base_data.setdefault("namespace", "")
            base_data.setdefault("operation", None)
            base_data.setdefault("subscribe", None)
            base_data.setdefault("customCode", None)
            base_data.setdefault("isAutomatic", False)
            base_data.setdefault("actorNodeName", None)
            base_data.setdefault("application_models", None)

        cls_data_payload: Dict[str, Any] = {
            "id": cls_id,
            "project": project_id,
            "system": system_id,
            "data": base_data,
        }

        node_payload: Dict[str, Any] = {
            "cls_data": cls_data_payload,
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
        nodes.append(node_payload)

    for edge in clean_model.get("edges", []):
        rel_id = str(uuid.uuid4())
        edge_id = str(uuid.uuid4())

        edge_type = edge.get("type") or "controlflow"
        # API expects condition to be None or a ControlFlowCondition object;
        # store simple labels (e.g. "Yes"/"No") in guard so serialization doesn't 500.
        raw_condition = edge.get("condition")
        guard = str(raw_condition) if raw_condition is not None else ""
        condition_value = None  # avoid Pydantic validation error on GET diagram

        source_original = str(edge.get("source"))
        target_original = str(edge.get("target"))

        rel_data_payload: Dict[str, Any] = {
            "id": rel_id,
            "data": {
                "type": edge_type,
                "guard": guard,
                "weight": "",
                "condition": condition_value,
                "is_directed": True,
                "position_handlers": [],
            },
            "system": system_id,
            "source": classifier_id_by_clean_id.get(source_original),
            "target": classifier_id_by_clean_id.get(target_original),
        }

        edge_payload: Dict[str, Any] = {
            "rel_data": rel_data_payload,
            "id": edge_id,
            "diagram": diagram_id,
            "rel": rel_id,
            "data": {},
        }

        edges.append(edge_payload)

    return {
        "interfaces": [],
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
    }

