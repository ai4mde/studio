from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router

from metadata.new_api.helpers import create_instance, update_instance
from metadata.new_api.schemas.systems import (
    SystemCreate,
    SystemRead,
    SystemUpdate,
)
from metadata.models import System


router = Router()


@router.get("/", response=list[SystemRead])
def list_systems(request, project_id: UUID):
    return System.objects.filter(project_id=project_id)


@router.get("/{system_id}", response=SystemRead)
def read_system(request, system_id: UUID):
    return get_object_or_404(System, id=system_id)


@router.post("/", response=SystemRead)
def create_system(request, payload: SystemCreate):
    return create_instance(System, payload)


@router.patch("/{system_id}", response=SystemRead)
def update_system(
    request,
    system_id: UUID,
    payload: SystemUpdate,
):
    system = get_object_or_404(System, id=system_id)

    return update_instance(system, payload)


@router.delete("/{system_id}", response={204: None})
def delete_system(request, system_id: UUID):
    system = get_object_or_404(System, id=system_id)
    system.delete()

    return 204, None
