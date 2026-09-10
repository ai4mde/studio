from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router

from metadata.new_api.helpers import create_instance, update_instance
from metadata.new_api.schemas.projects import (
    ProjectCreate, 
    ProjectRead, 
    ProjectUpdate,
)
from metadata.models import Project


router = Router()


@router.get("/", response=list[ProjectRead])
def list_projects(request):
    return Project.objects.all()


@router.get("/{project_id}", response=ProjectRead)
def read_project(request, project_id: UUID):
    return get_object_or_404(Project, id=project_id)


@router.post("/", response=ProjectRead)
def create_project(request, payload: ProjectCreate):
    return create_instance(Project, payload)


@router.patch("/{project_id}", response=ProjectRead)
def update_project(
    request,
    project_id: UUID,
    payload: ProjectUpdate,
):
    project = get_object_or_404(Project, id=project_id)
    return update_instance(project, payload)


@router.delete("/{project_id}", response={204: None})
def delete_project(request, project_id: UUID):
    project = get_object_or_404(Project, id=project_id)
    project.delete()
    return 204, None
