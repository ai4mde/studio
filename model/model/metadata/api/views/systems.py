from typing import List, Optional

from metadata.api.schemas import CreateSystem, ReadSystem, UpdateSystem
from metadata.models import System
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
def read_system(request, project, id):
    return System.objects.get(id=id)


@systems.post("/", response=ReadSystem)
def create_system(request, payload: CreateSystem):
    print(payload)
    pass


@systems.put("/{uuid:id}", response=ReadSystem)
def update_system(request, id, payload: UpdateSystem):
    print(payload)
    pass


@systems.delete("/{uuid:id}")
def delete_system(request, id):
    print(id)
    pass


__all__ = ["systems"]
