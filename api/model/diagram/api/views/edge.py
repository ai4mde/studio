from typing import List
from uuid import UUID
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from ninja import Router

import diagram.api.utils as utils

from diagram.api.schemas import CreateEdge, EdgeSchema, UpdateEdge
from diagram.models import Node, Edge
from diagram.api.utils.edge import fetch_and_update_edges, delete_edge


edge = Router()


@edge.get("/", response=List[EdgeSchema])
def list_edges(request):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    return fetch_and_update_edges(diagram)


@edge.post("/", response=EdgeSchema)
def create_edge(request: HttpRequest, data: CreateEdge):
    diagram = utils.get_diagram(request)
    source = Node.objects.get(id=data.source)
    target = Node.objects.get(id=data.target)

    if not diagram:
        return 404, "Diagram not found"

    edge = utils.create_edge(diagram, data.rel, source, target)

    return edge


@edge.patch("/{uuid:edge_id}/", response=EdgeSchema)
def update_edge(request: HttpRequest, edge_id: UUID, data: UpdateEdge):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    edge_obj = get_object_or_404(Edge, id=edge_id, diagram=diagram)

    if data.rel is not None:
        current = edge_obj.rel.data or {}
        merged = {**current, **data.rel}
        new_type = merged.get("type", current.get("type"))

        # default fallback if type is missing
        if new_type is None:
            new_type = current.get("type")

        # canonical shapes per type
        if new_type in ("association", "composition"):
            labels = merged.get("labels") or {}
            mult = merged.get("multiplicity") or {}

            cleaned = {
                "type": new_type,
                "label": merged.get("label", ""),
                "labels": {
                    "source": labels.get("source", ""),
                    "target": labels.get("target", ""),
                },
                "multiplicity": {
                    "source": mult.get("source", ""),
                    "target": mult.get("target", ""),
                },
            }

        elif new_type == "dependency":
            cleaned = {
                "type": "dependency",
                "label": merged.get("label", ""),
            }

        elif new_type == "generalization":
            cleaned = {
                "type": "generalization",
            }

        else:
            cleaned = merged

        edge_obj.rel.data = cleaned
        edge_obj.rel.save()

    if data.data is not None:
        current_data = edge_obj.data or {}
        updated_data = {**current_data, **data.data}
        edge_obj.data = updated_data
        edge_obj.save()

    return edge_obj


@edge.delete("/{uuid:edge_id}/", response=bool)
def delete_edge(request: HttpRequest, edge_id: str):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    if utils.delete_edge(diagram=diagram, edge_id=edge_id):
        return True
    return False


@edge.get("/{uuid:edge_id}/", response=EdgeSchema)
def edge_node(request: HttpRequest, edge_id: str):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    return diagram.edges.get(id=edge_id)


__all__ = ["edge"]
