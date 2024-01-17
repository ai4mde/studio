from ninja import Router
from typing import List
from metadata.models import Project
from metadata.api.schemas import ReadProject, CreateProject, UpdateProject

projects = Router()

@projects.get('/', response=List[ReadProject])
def list_projects(request):
    qs = Project.objects.all()
    return qs

@projects.get('/{uuid:id}', response=ReadProject)
def read_project(request, id):
    return Project.objects.get(id=id)

@projects.post('/', response=ReadProject)
def create_project(request, payload: CreateProject):
    print(payload)
    pass

@projects.put('/{uuid:id}', response=ReadProject)
def update_project(request, id, payload: UpdateProject):
    print(id)
    print(payload)
    pass

@projects.delete('/{uuid:id}')
def delete_project(request, id):
    print(id)
    pass

__all__ = [
    'projects'
]