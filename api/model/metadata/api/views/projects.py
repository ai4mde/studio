from typing import List

from metadata.api.schemas import CreateProject, ReadProject, UpdateProject, ExportProject, ImportProject
from metadata.models import Project
from ninja import Router
from ninja.responses import Response

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
    except Exception as e:
        raise Exception("Failed to delete project, error: " + e)
    return True


@projects.get("/export/{uuid:project_id}/", response=ExportProject)
def export_project(request, project_id: str):
    project = Project.objects.get(id=project_id)
    if not project:
        raise Exception("Project not found")
    return project


@projects.post("/import/")
def import_project(request, payload: ImportProject):
    try:
        json_data = payload.dict()
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
