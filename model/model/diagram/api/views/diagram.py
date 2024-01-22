from typing import List

from diagram.api.schemas import CreateDiagram, ReadDiagram, UpdateDiagram
from diagram.models import Diagram
from ninja import Router

diagrams = Router()


@diagrams.get("/", response=List[ReadDiagram])
def list_diagrams(request):
    qs = Diagram.objects.all()
    return qs


@diagrams.get("/{uuid:id}", response=ReadDiagram)
def read_diagram(request, id):
    return Diagram.objects.get(id=id)


@diagrams.post("/", response=ReadDiagram)
def create_diagram(request, project: CreateDiagram):
    return Diagram.objects.create(
        name=project.name,
        description=project.description,
    )


@diagrams.put("/{uuid:id}", response=ReadDiagram)
def update_diagram(request, id, payload: UpdateDiagram):
    print(id)
    print(payload)
    pass


@diagrams.delete("/{uuid:id}")
def delete_diagram(request, id):
    print(id)
    pass


__all__ = ["diagrams"]
