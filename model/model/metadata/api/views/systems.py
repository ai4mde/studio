from typing import List, Optional

from ninja import Router

from metadata.api.schemas import CreateSystem, ReadSystem, UpdateSystem
from metadata.models import Project, System

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
    system = System.objects.prefetch_related("diagram_set").get(id=id)
    return {
        "id": system.id,
        "name": system.name,
        "description": system.description,
        "diagrams": {
            "classes": system.diagram_set.filter(type="class"),
            "activity": system.diagram_set.filter(type="activity"),
            "usecase": system.diagram_set.filter(type="usecase"),
            "component": system.diagram_set.filter(type="component"),
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
