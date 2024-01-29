from typing import List, Optional

from metadata.api.schemas import CreateSystem, ReadSystem, UpdateSystem
from metadata.models import Project, System
from ninja import Router

systems = Router()


@systems.get("/", response=List[ReadSystem])
def list_systems(request, project: Optional[str]):
    qs = None
    if project:
        qs = System.objects.filter(project=project)
    else:
        qs = System.objects.all()
    return qs


@systems.get("/{uuid:id}", response=ReadSystem)
def read_system(request, id):
    system = System.objects.prefetch_related("diagrams").get(id=id)

    return {
        "id": system.id,
        "name": system.name,
        "description": system.description,
        "diagrams_by_type": {
            "classes": system.diagrams.filter(type="classes"),
            "activity": system.diagrams.filter(type="activity"),
            "usecase": system.diagrams.filter(type="usecase"),
            "component": system.diagrams.filter(type="component"),
        },
    }


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
    pass


@systems.delete("/{uuid:id}")
def delete_system(request, id):
    print(id)
    pass


__all__ = ["systems"]
