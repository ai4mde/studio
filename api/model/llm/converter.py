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

    for node in clean_model.get("nodes", []):
        original_id = str(node.get("id"))
        cls_id = str(uuid.uuid4())
        node_id = str(uuid.uuid4())

        node_type = str(node.get("type", "action"))
        node_name = node.get("name")
        role = _derive_role(node_type)

        cls_data_payload: Dict[str, Any] = {
            "id": cls_id,
            "project": project_id,
            "system": system_id,
            "data": {
                "role": role,
                "type": node_type,
            },
        }

        if node_type in {"initial", "final"}:
            cls_data_payload["data"]["activity_scope"] = "activity"

        if node_type == "action":
            cls_data_payload["data"]["name"] = node_name or ""
            cls_data_payload["data"]["body"] = ""
            cls_data_payload["data"]["localPrecondition"] = ""
            cls_data_payload["data"]["localPostcondition"] = ""

        node_payload: Dict[str, Any] = {
            "cls_data": cls_data_payload,
            "id": node_id,
            "diagram": diagram_id,
            "cls": cls_id,
            "data": {
                "position": {
                    "x": 0,
                    "y": 0,
                }
            },
        }

        classifier_id_by_clean_id[original_id] = cls_id
        nodes.append(node_payload)

    for edge in clean_model.get("edges", []):
        rel_id = str(uuid.uuid4())
        edge_id = str(uuid.uuid4())

        edge_type = edge.get("type") or "controlflow"
        condition = edge.get("condition")

        source_original = str(edge.get("source"))
        target_original = str(edge.get("target"))

        rel_data_payload: Dict[str, Any] = {
            "id": rel_id,
            "data": {
                "type": edge_type,
                "guard": "",
                "weight": "",
                "condition": condition,
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

