from typing import List, Optional

from django.core.exceptions import ObjectDoesNotExist
from ninja import Router, Schema

from metadata.api.schemas import CreateSystem, ExportSingleSystem, ReadSystem, UpdateSystem
from metadata.models import Project, System

from .classifiers import actors, classes, classifiers
from .meta import meta
from .node import nodes
from .relations import classifier_relations, relations

systems = Router()


@systems.get("/", response=List[ReadSystem])
def list_systems(request, project: Optional[str] = None):
    qs = None
    if project:
        qs = System.objects.filter(project=project)
    else:
        qs = System.objects.all()
    return qs


@systems.get("/{uuid:id}/", response=ReadSystem)
def read_system(request, id):
    return System.objects.prefetch_related("diagrams").get(id=id)


@systems.post("/", response=ReadSystem)
def create_system(request, system: CreateSystem):
    return System.objects.create(
        name=system.name,
        description=system.description,
        project=Project.objects.get(pk=system.project),
    )


@systems.put("/{uuid:id}", response=ReadSystem)
def update_system(request, id, payload: UpdateSystem):
    print(payload)
    return None


@systems.delete("/{uuid:id}/")
def delete_system(request, id):
    try:
        system = System.objects.get(id=id)
        system.delete()
    except ObjectDoesNotExist:
        raise Exception("System not found")
    return True


class ImportResult(Schema):
    success: bool
    message: str


@systems.get("/export/", response=List[ExportSingleSystem])
def export_systems(request):
    system_ids = request.GET.getlist("system_ids")
    systems_qs = System.objects.filter(id__in=system_ids)
    return systems_qs


systems.add_router("/{uuid:system_id}/meta", meta, tags=["metadata"])
systems.add_router("/{uuid:system_id}/classifiers", classifiers, tags=["metadata"])
systems.add_router("/{uuid:system_id}/classes", classes, tags=["metadata"])
systems.add_router("/{uuid:system_id}/actors", actors, tags=["metadata"])
systems.add_router("/{uuid:system_id}/relations", relations, tags=["metadata"])
systems.add_router("/{uuid:system_id}/classifier-relations", classifier_relations, tags=["metadata"])
systems.add_router("/{uuid:system_id}/nodes", nodes, tags=["metadata"])


__all__ = ["systems"]
