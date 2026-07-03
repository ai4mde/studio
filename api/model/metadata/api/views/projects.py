from typing import List

from django.core.exceptions import ObjectDoesNotExist
from ninja import Router
from ninja.responses import Response

from metadata.api.schemas import (
    CreateProject,
    ExportProject,
    ImportProject,
    ReadProject,
    UpdateProject,
)
from metadata.models import Project

projects = Router()


@projects.get("/", response=List[ReadProject])
def list_projects(request):
    qs = Project.objects.all()
    return qs


@projects.get("/{uuid:project_id}", response=ReadProject)
def read_project(request, project_id):
    return Project.objects.get(id=project_id)


@projects.post("/", response=ReadProject)
def create_project(request, project: CreateProject):
    return Project.objects.create(
        name=project.name,
        description=project.description,
    )


@projects.put("/{uuid:project_id}", response=ReadProject)
def update_project(request, project_id, payload: UpdateProject):
    print(project_id)
    print(payload)
    return None


@projects.delete("/{uuid:project_id}")
def delete_project(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        project.delete()
    except ObjectDoesNotExist:
        raise ObjectDoesNotExist("Project not found")
    return True


@projects.get("/export/{uuid:project_id}/", response=ExportProject)
def export_project(request, project_id: str):
    project = Project.objects.get(id=project_id)
    if not project:
        raise ObjectDoesNotExist("Project not found")
    return project


@projects.post("/import/")
def import_project(request, payload: ImportProject, force: bool = False):
    try:
        json_data = payload.dict()
        
        existing_project = Project.objects.filter(id=json_data.get("id")).first()
        if existing_project and not force:
            return Response(
                {
                    "status": "error",
                    "code": "PROJECT_EXISTS",
                    "project_id": existing_project.id,
                    "project_name": existing_project.name,
                },
                status=409,
            )

        project = Project.import_from_json(json_data)
        return Response(
            {
                "status": "success",
                "project_id": project.id,
            },
            status=200,
        )
    except Exception as e:
        return Response(
            {
                "status": "error",
                "message": str(e),
            },
            status=400,
        )


__all__ = ["projects"]
