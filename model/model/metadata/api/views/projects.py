from typing import List

from metadata.api.schemas import CreateProject, ReadProject, UpdateProject
from metadata.models import Project
from ninja import Router

projects = Router()


@projects.get("/", response=List[ReadProject])
def list_projects(request):
    qs = Project.objects.all()
    return qs


@projects.get("/{uuid:id}", response=ReadProject)
def read_project(request, id):
    return Project.objects.get(id=id)


@projects.post("/", response=ReadProject)
def create_project(request, project: CreateProject):
    return Project.objects.create(
        name=project.name,
        description=project.description,
    )


@projects.put("/{uuid:id}", response=ReadProject)
def update_project(request, id, payload: UpdateProject):
    print(id)
    print(payload)
    pass


@projects.delete("/{uuid:id}")
def delete_project(request, id):
    print(id)
    pass


__all__ = ["projects"]
