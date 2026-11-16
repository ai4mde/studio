import json
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from ninja import File, Form, Router
from ninja.files import UploadedFile

from metadata.api.helpers import create_instance, update_instance
from metadata.api.schemas.project import (
    ProjectCreate, 
    ProjectRead, 
    ProjectUpdate,
    ProjectList,
)
from metadata.models import Project
from metadata.services.versioning.import_project import (
    ProjectAlreadyExistsError,
    import_project as import_project_service,
)


router = Router()


@router.get("/", response=list[ProjectList])
def list_projects(request):
    return Project.objects.all()


@router.post(
    "/import/",
    response={
        200: ProjectRead,
        400: dict,
        409: dict,
    },
)
def import_project(
    request,
    file: File[UploadedFile],
    name: Form[str] = "Imported version",
):
    try:
        snapshot = json.load(file)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 400, {"message": "The uploaded file is not valid JSON."}

    try:
        project = import_project_service(snapshot, name)
    except ProjectAlreadyExistsError as exc:
        return 409, {"message": exc.messages[0]}
    except ValidationError as exc:
        return 400, {"message": exc.messages[0]}
    except IntegrityError:
        return 400, {"message": "The snapshot conflicts with existing data."}

    return project


@router.get("/{project_id}/", response=ProjectRead)
def read_project(request, project_id: UUID):
    return get_object_or_404(Project, id=project_id)


@router.post("/", response=ProjectRead)
def create_project(request, payload: ProjectCreate):
    return create_instance(Project, payload)


@router.patch("/{project_id}/", response=ProjectRead)
def update_project(
    request,
    project_id: UUID,
    payload: ProjectUpdate,
):
    project = get_object_or_404(Project, id=project_id)
    return update_instance(project, payload)


@router.delete("/{project_id}/", response={204: None})
def delete_project(request, project_id: UUID):
    project = get_object_or_404(Project, id=project_id)
    project.delete()
    return 204, None

