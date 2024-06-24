from typing import List, Optional

from metadata.api.schemas import CreateSystem, ReadSystem, UpdateSystem
from metadata.models import Project, System
from .meta import meta
from .classifiers import classifiers, classes

from ninja import Router

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


@systems.delete("/{uuid:id}")
def delete_system(request, id):
    print(id)
    return None


systems.add_router("/{uuid:system_id}/meta", meta)
systems.add_router("/{uuid:system_id}/classifiers", classifiers)
systems.add_router("/{uuid:system_id}/classes", classes)

__all__ = ["systems"]
