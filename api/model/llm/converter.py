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


def convert_to_ai4mde(clean_model: Dict[str, Any], system_id: str, diagram_id: str) -> Dict[str, Any]:
    """
    Convert a clean activity JSON model into an AI4MDE export-compatible structure.
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    node_id_map: Dict[str, str] = {}

    for node in clean_model.get("nodes", []):
        original_id = str(node.get("id", uuid.uuid4()))
        new_node_id = str(uuid.uuid4())
        cls_id = str(uuid.uuid4())

        node_type = str(node.get("type", "action"))
        name = node.get("name")
        role = _derive_role(node_type)

        cls_data: Dict[str, Any] = {
            "id": cls_id,
            "data": {
                "type": node_type,
                "role": role,
            },
        }
        if name is not None:
            cls_data["data"]["name"] = name

        node_payload: Dict[str, Any] = {
            "id": new_node_id,
            "diagram_id": diagram_id,
            "system_id": system_id,
            "position": {"x": 0, "y": 0},
            "cls": cls_data,
        }

        node_id_map[original_id] = new_node_id
        nodes.append(node_payload)

    for edge in clean_model.get("edges", []):
        rel_id = str(uuid.uuid4())
        edge_id = str(uuid.uuid4())

        edge_type = edge.get("type")
        condition = edge.get("condition")

        rel_data: Dict[str, Any] = {
            "id": rel_id,
            "data": {},
        }
        if edge_type is not None:
            rel_data["data"]["type"] = edge_type
        if condition is not None:
            rel_data["data"]["condition"] = condition

        source_original = edge.get("source")
        target_original = edge.get("target")

        edge_payload: Dict[str, Any] = {
            "id": edge_id,
            "diagram_id": diagram_id,
            "system_id": system_id,
            "source": node_id_map.get(str(source_original)),
            "target": node_id_map.get(str(target_original)),
            "is_directed": True,
            "guard": "",
            "weight": "",
            "position_handlers": [],
            "rel": rel_data,
        }

        edges.append(edge_payload)

    return {
        "diagrams": [
            {
                "id": diagram_id,
                "type": "activity",
                "system": system_id,
                "name": "Generated Diagram",
                "description": "",
                "nodes": nodes,
                "edges": edges,
            }
        ]
    }

