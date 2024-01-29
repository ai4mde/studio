from typing import List
from django.http import HttpRequest

from ninja import Router

import diagram.api.utils as utils

from diagram.api.schemas import CreateEdge, EdgeSchema


edge = Router()


@edge.get("/", response=List[EdgeSchema])
def list_edges(request):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    return diagram.edges.all()


@edge.post("/", response=EdgeSchema)
def create_edge(request: HttpRequest, data: CreateEdge):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    edge = utils.create_edge(diagram, data.rel)

    return edge


@edge.get("/{uuid:edge_id}/", response=EdgeSchema)
def edge_node(request: HttpRequest, edge_id: str):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    return diagram.edges.get(id=edge_id)


__all__ = ["edge"]
