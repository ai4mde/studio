from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router

from diagram.models import Diagram
from diagram.api.schemas.diagram import (
    DiagramCreate,
    DiagramRead,
    DiagramUpdate,
)
from metadata.api.helpers import create_instance, update_instance


router = Router()


@router.get("/", response=list[DiagramRead])
def list_diagrams(request, system_id: UUID):
    return Diagram.objects.filter(system_id=system_id)


@router.get("/{diagram_id}/", response=DiagramRead)  # TODO change to full diagram schema when implemented
def read_diagram(request, diagram_id: UUID):
    return get_object_or_404(Diagram, id=diagram_id)


@router.post("/", response=DiagramRead)
def create_diagram(request, payload: DiagramCreate):
    return create_instance(Diagram, payload)


@router.patch("/{diagram_id}/", response=DiagramRead)
def update_diagram(request, diagram_id: UUID, payload: DiagramUpdate):
    diagram = get_object_or_404(Diagram, id=diagram_id)
    return update_instance(diagram, payload)


@router.delete("/{diagram_id}/", response={204: None})
def delete_diagram(request, diagram_id: UUID):
    diagram = get_object_or_404(Diagram, id=diagram_id)
    diagram.delete()

    return 204, None