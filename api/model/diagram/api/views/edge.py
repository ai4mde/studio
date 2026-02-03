from typing import List
from uuid import UUID
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from ninja import Router
from pydantic import BaseModel

import diagram.api.utils as utils

from diagram.api.schemas import CreateEdge, EdgeSchema, UpdateEdge, DiagramUsageItem, RelationUsageResponse, PatchEdge
from diagram.models import Node, Edge, Edge
from diagram.api.utils.edge import fetch_and_update_edges, remove_edge_from_diagram, delete_relation_everywhere
from metadata.specification import Relation


edge = Router()


@edge.get("/", response=List[EdgeSchema])
def list_edges(request):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    return fetch_and_update_edges(diagram)


@edge.get("/{uuid:edge_id}/relation-usage/", response=RelationUsageResponse)
def relation_usage(request, edge_id: str):
    diagram = utils.get_diagram(request)
    if not diagram:
        return 404, "Diagram not found"

    edge = diagram.edges.select_related("rel").filter(id=edge_id).first()
    if not edge:
        return 404, "Edge not found"

    rel = edge.rel
    rel_label = (rel.data or {}).get("label") or (rel.data or {}).get("type") or str(rel.id)

    edges = Edge.objects.select_related("diagram", "diagram__system").filter(rel=rel)

    seen = set()
    usage_items = []
    for e in edges:
        d = e.diagram
        if d.id == diagram.id:
            continue
        if d.id in seen:
            continue
        seen.add(d.id)

        usage_items.append(DiagramUsageItem(
            diagram_id=str(d.id),
            diagram_name=d.name,
            system_id=str(d.system.id),
            system_name=d.system.name,
        ))

    return RelationUsageResponse(
        relation_id=str(rel.id),
        usages=usage_items,
    )


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
        PatchModel.model_validate({"rel": merged})
        new_type = merged.get("type", current.get("type"))

        # default fallback if type is missing
        if new_type is None:
            new_type = current.get("type")

        # canonical shapes per type
        if new_type in ("association", "composition"):
            labels = merged.get("labels") or {}
            mult = merged.get("multiplicity") or {}

            cleaned = {
                **merged,
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
                **merged,
                "type": "dependency",
                "label": merged.get("label", ""),
            }

        elif new_type == "generalization":
            cleaned = {
                **merged,
                "type": "generalization",
            }

        else:
            cleaned = merged

        edge_obj.rel.data = cleaned
        edge_obj.rel.save()

    if data.data is not None:
        current_data = edge_obj.data or {}
        patch = data.data.model_dump(exclude_unset=True, exclude_none=True)
        updated_data = {**current_data, **patch}
        edge_obj.data = updated_data
        edge_obj.save()

    return edge_obj


@edge.delete("/{uuid:edge_id}/", response=bool)
def remove_edge(request: HttpRequest, edge_id: str):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    return remove_edge_from_diagram(diagram=diagram, edge_id=edge_id)


@edge.delete("/{uuid:edge_id}/hard/", response=bool)
def hard_delete_relation(request: HttpRequest, edge_id: str):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    return delete_relation_everywhere(diagram=diagram, edge_id=edge_id)


class PatchModel(BaseModel):
    rel: Relation


@edge.get("/{uuid:edge_id}/", response=EdgeSchema)
def edge_node(request: HttpRequest, edge_id: str):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    return diagram.edges.get(id=edge_id)


__all__ = ["edge"]
