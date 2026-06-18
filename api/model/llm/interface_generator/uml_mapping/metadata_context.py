"""Metadata context helpers for the Django-hosted UML mapping flow."""

from diagram.models import Diagram
from metadata.models import System

from ..token_normalizer import _as_list
from .usecase_workflow import _build_activity_diagrams


def _node_position(node) -> tuple[object, object]:
    """Read a node position tuple from metadata when coordinates are available."""
    data = node.data or {}
    position = data.get("position") or {}
    return position.get("x", data.get("x")), position.get("y", data.get("y"))


def _fetch_system_context_data(system_id: str) -> dict:
    """Load classifiers and relations needed for UML-aware interface generation."""
    system = System.objects.prefetch_related(
        "classifiers",
        "relations",
        "interfaces",
        "diagrams__nodes",
        "diagrams__edges",
    ).get(id=system_id)
    classifiers = [
        {
            "id": str(c.id),
            "project": str(c.project_id) if c.project_id else None,
            "system": str(c.system_id) if c.system_id else None,
            "original_system_id": str(c.original_system_id) if c.original_system_id else None,
            "data": c.data or {},
        }
        for c in system.classifiers.all()
    ]
    relations = [
        {
            "id": str(r.id),
            "system": str(r.system_id),
            "source": str(r.source_id),
            "target": str(r.target_id),
            "data": r.data or {},
        }
        for r in system.relations.all()
    ]
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
            diagram_edges.append({
                "id": str(edge.id),
                "diagram": str(edge.diagram_id),
                "rel": str(edge.rel_id) if edge.rel_id else None,
                "data": edge.data or {},
            })
        diagrams.append({
            "id": str(diagram.id),
            "name": diagram.name,
            "description": diagram.description,
            "type": diagram.type,
            "system": str(diagram.system_id),
            "nodes": diagram_nodes,
            "edges": diagram_edges,
        })
    interfaces = [
        {
            "id": str(i.id),
            "name": i.name,
            "description": i.description,
            "system": str(i.system_id),
            "actor": str(i.actor_id) if i.actor_id else None,
            "data": i.data or {},
        }
        for i in system.interfaces.all()
    ]
    context = {
        "id": str(system.id),
        "name": system.name,
        "description": system.description,
        "project": str(system.project_id),
        "classifiers": classifiers,
        "relations": relations,
        "diagrams": diagrams,
        "nodes": nodes,
        "interfaces": interfaces,
        "imported_classifiers": [],
    }
    context["activity_diagrams"] = _build_activity_diagrams(context)
    return context


def _actor_name_from_context(system_context: dict, actor_id: str | None) -> str | None:
    """Resolve an actor classifier id to its display name from system context."""
    for classifier in _as_list(system_context.get("classifiers"), "classifiers"):
        if str(classifier.get("id")) == str(actor_id):
            return (classifier.get("data") or {}).get("name")
    return None
