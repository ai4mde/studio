from ninja import Router, Schema

from typing import List, Optional
from django.core.exceptions import ObjectDoesNotExist
from ninja.responses import Response

from metadata.api.schemas import CreateSystem, ReadSystem, UpdateSystem, ExportSingleSystem, ImportSingleSystem
from metadata.models import Project, System
from .meta import meta
from .classifiers import classifiers, classes, actors
from .relations import relations, classifier_relations
from .node import nodes

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


@systems.post("/import/")
def import_systems(request, payload: List[ImportSingleSystem]):
    try:
        systems_data = [s.dict() for s in payload]
        for system_data in systems_data:
            System.import_from_json(system_data)
        return Response({"status": "success", "count": len(systems_data)}, status=200)
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=400)


systems.add_router("/{uuid:system_id}/meta", meta, tags=["metadata"])
systems.add_router("/{uuid:system_id}/classifiers", classifiers, tags=["metadata"])
systems.add_router("/{uuid:system_id}/classes", classes, tags=["metadata"])
systems.add_router("/{uuid:system_id}/actors", actors, tags=["metadata"])
systems.add_router("/{uuid:system_id}/relations", relations, tags=["metadata"])
systems.add_router("/{uuid:system_id}/classifier-relations", classifier_relations, tags=["metadata"])
systems.add_router("/{uuid:system_id}/nodes", nodes, tags=["metadata"])


__all__ = ["systems"]
