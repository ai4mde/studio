from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router

from generator.api.schemas.prototype import (
    PrototypeCreate,
    PrototypeRead,
    PrototypeUpdate,
)
from generator.models import Prototype
from generator.services.prototype import (
    create_prototype as create_prototype_service,
    delete_prototype as delete_prototype_service,
    delete_system_prototypes as delete_system_prototypes_service,
    get_active_prototype as get_active_prototype_service,
    run_prototype as run_prototype_service,
    stop_prototypes as stop_prototypes_service,
)

router = Router()


@router.get("/", response=list[PrototypeRead])
def list_prototypes(request, system: UUID | None = None):
    if system:
        return Prototype.objects.filter(system_id=system)
    return Prototype.objects.all()


@router.get("/{uuid:id}/meta/", response=dict)
def read_prototype_meta(request, id: UUID):
    prototype = get_object_or_404(Prototype, id=id)
    return prototype.metadata


@router.get("/active_prototype/")
def get_active_prototype(request):
    return get_active_prototype_service()


@router.get("/{uuid:id}/", response=PrototypeRead)
def read_prototype(request, id: UUID):
    return get_object_or_404(Prototype, id=id)


@router.get("/{str:database_hash}/", response=list[PrototypeRead])
def list_prototypes_hash(request, database_hash: str):
    return Prototype.objects.filter(database_hash=database_hash)


@router.post("/", response=PrototypeRead)
def create_prototype(request, prototype: PrototypeCreate):
    return create_prototype_service(prototype)


@router.delete("/{uuid:id}/", response=bool)
def delete_prototype(request, id: UUID):
    return delete_prototype_service(id)


@router.delete("/system/{uuid:system_id}/", response=bool)
def delete_system_prototypes(request, system_id: UUID):
    return delete_system_prototypes_service(system_id)



@router.put("/{uuid:id}/", response=bool)
def update_prototype(
    request,
    id: UUID,
    payload: PrototypeUpdate,
):
    return bool(
        Prototype.objects.filter(pk=id).update(
            **payload.model_dump()
        )
    )


@router.post("/stop_prototypes/", response=bool)
def stop_prototypes(request):
    return stop_prototypes_service()


@router.post("/run/{uuid:prototype_id}/", response=bool)
def run_prototype(request, prototype_id: UUID):
    return run_prototype_service(prototype_id)
