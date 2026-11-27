import json
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import File, Form, Query, Router
from ninja.files import UploadedFile

from metadata.api.helpers import create_instance, update_instance
from metadata.api.schemas.project import (
    ProjectCreate, 
    ProjectRead, 
    ProjectUpdate,
    ProjectList,
)
from metadata.models import (
    Association,
    Composition,
    EndpointLabel,
    Multiplicity,
    Project,
)
from metadata.services.versioning import snapshot_project
from metadata.services.versioning.systems import export_systems
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
    


# ============================================================
# Added for the frontend migration (not part of the original routes)
# ============================================================
def _json_download(data: dict, filename: str) -> HttpResponse:
    response = HttpResponse(
        json.dumps(data, indent=2),
        content_type="application/json",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@router.get("/{project_id}/export/")
def export_project(request, project_id: UUID):
    """The current state of the project, in the same format as a release export."""
    get_object_or_404(Project, id=project_id)
    return _json_download(
        snapshot_project(project_id),
        f"project-{project_id}.json",
    )


@router.get("/{project_id}/systems/export/", response={200: None, 400: dict})
def export_project_systems(
    request,
    project_id: UUID,
    system_ids: Query[list[UUID]],
):
    """Selected systems of the project, to import into a project later."""
    get_object_or_404(Project, id=project_id)

    try:
        data = export_systems(project_id, system_ids)
    except ValidationError as exc:
        return 400, {"message": exc.messages[0]}

    return _json_download(data, f"systems-{project_id}.json")

