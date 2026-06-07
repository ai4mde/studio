"""Metadata context helpers for the Django-hosted UML mapping flow."""

from diagram.models import Diagram
from metadata.models import System

from ..token_normalizer import _as_list
from .usecase_workflow import _build_activity_diagrams


def _node_position(node) -> tuple[object, object]:
    data = node.data or {}
    position = data.get("position") or {}
    return position.get("x", data.get("x")), position.get("y", data.get("y"))


def _fetch_system_context_data(system_id: str) -> dict:
    system = System.objects.prefetch_related(
        "classifiers",
        "relations",
        "diagrams__nodes",
        "diagrams__edges",
    ).get(id=system_id)
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
    system_data = {
        "id": str(system.id),
        "name": system.name,
        "description": system.description,
        "project": str(system.project_id),
        "classifiers": [
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
        ],
        "relations": [
            {
                "id": str(relation.id),
                "system": str(relation.system_id),
                "source": str(relation.source_id),
                "target": str(relation.target_id),
                "data": relation.data or {},
            }
            for relation in system.relations.all()
        ],
        "diagrams": diagrams,
        "nodes": nodes,
    }
    system_data["activity_diagrams"] = _build_activity_diagrams(system_data)
    return system_data


def _actor_name_from_context(system_context: dict, actor_id: str | None) -> str | None:
    for classifier in _as_list(system_context.get("classifiers"), "classifiers"):
        if str(classifier.get("id")) == str(actor_id):
            return (classifier.get("data") or {}).get("name")
    return None
