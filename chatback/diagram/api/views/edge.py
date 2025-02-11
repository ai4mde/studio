from typing import List
from django.http import HttpRequest

from ninja import Router

import diagram.api.utils as utils

from diagram.api.schemas import CreateEdge, EdgeSchema
from diagram.models import Node
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
