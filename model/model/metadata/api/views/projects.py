from ninja import Router
from typing import List
from metadata.models import Project
from metadata.api.schemas import project as schema

projects = Router()

@projects.get('/', response=List[schema.ReadProject])
def list_projects(request):
    qs = Project.objects.all()
    return qs

@projects.post('/', response=schema.ReadProject)
def create_project(request, payload: schema.CreateProject):
    print(payload)
    pass

@projects.put('/{uuid:id}', response=schema.ReadProject)
def update_project(request, id, payload: schema.UpdateProject):
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