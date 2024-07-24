from typing import List

from diagram.api.schemas import CreateDiagram, FullDiagram, ReadDiagram, UpdateDiagram
from diagram.models import Diagram
from metadata.models import System
from ninja import Router

from .node import node
from .edge import edge
from .system import system

diagrams = Router()


@diagrams.get("/", response=List[ReadDiagram])
def list_diagrams(request):
    qs = Diagram.objects.all()
    return qs


@diagrams.get("/{uuid:diagram_id}", response=FullDiagram)
def read_diagram(request, diagram_id):
    return Diagram.objects.get(id=diagram_id)


@diagrams.post("/", response=ReadDiagram)
def create_diagram(request, body: CreateDiagram):
    system = System.objects.get(id=body.system)
    diagram = Diagram.objects.create(
        name=body.name,
        system=system,
        type=body.type,
    )
    return diagram


@diagrams.patch("/{uuid:diagram_id}/", response=ReadDiagram)
def update_diagram(request, diagram_id, payload: UpdateDiagram):
    diagram = Diagram.objects.get(id=diagram_id)

    if payload.name:
        diagram.name = payload.name
        diagram.save()

    if payload.description:
        diagram.description = payload.description
        diagram.save()

    return diagram


@diagrams.delete("/{uuid:diagram_id}/")
def delete_diagram(request, diagram_id):
    print(diagram_id)
    return None


diagrams.add_router("/{uuid:diagram}/node", node)
diagrams.add_router("/{uuid:diagram}/edge", edge)
diagrams.add_router("/system/", system)

__all__ = ["diagrams"]
