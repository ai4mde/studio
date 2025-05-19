from typing import List
from django.http import HttpRequest

from ninja import Router
from pydantic import BaseModel

import diagram.api.utils as utils

from diagram.api.schemas import CreateEdge, EdgeSchema, PatchEdge
from diagram.models import Node, Edge
from diagram.api.utils.edge import fetch_and_update_edges, delete_edge
from metadata.specification import Relation


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



class PatchModel(BaseModel):
    rel: Relation


@edge.patch("/{uuid:edge_id}/", response=EdgeSchema)
def update_edge(request: HttpRequest, edge_id: str, data: PatchEdge):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    edge = diagram.edges.get(id=edge_id)

    if data.rel is not None:
        new_rel = {**edge.rel.data, **data.rel}
        PatchModel.model_validate({"rel": new_rel})
        edge.rel.data = new_rel
        edge.rel.save()

    if data.data is not None:
        edge.data = {**edge.data, **data.data.model_dump()}
        edge.save()

    return edge

@edge.get("/{uuid:edge_id}/", response=EdgeSchema)
def edge_node(request: HttpRequest, edge_id: str):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    return diagram.edges.get(id=edge_id)


__all__ = ["edge"]
