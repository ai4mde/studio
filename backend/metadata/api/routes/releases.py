import json
from uuid import UUID

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from ninja import File, Form, Router
from ninja.files import UploadedFile

from metadata.api.schemas.project import ProjectRead
from metadata.api.schemas.releases import (
    ReleaseCreate,
    ReleaseList,
    ReleaseMerge,
)
from metadata.models import Release
from metadata.services.versioning import (
    MergeConflictError,
    create_release as create_release_service,
    export_release as export_release_service,
    import_release as import_release_service,
    restore_release as restore_release_service,
    merge_releases as merge_releases_service
)


router = Router()


@router.get("/", response=list[ReleaseList])
def list_releases(request, project_id: UUID):
    return Release.objects.filter(
        project_id=project_id
    ).order_by("-created_at")


@router.post("/", response=ReleaseList)
def create_release(request, payload: ReleaseCreate):
    release = create_release_service(
        project_id=payload.project,
        name=payload.name,
        description=payload.description,
        release_notes=payload.release_notes,
    )

    return 201, release



@router.get("/{release_id}/export/")
def export_release(request, release_id: UUID):
    snapshot = export_release_service(release_id)

    response = HttpResponse(
        json.dumps(snapshot, indent=2),
        content_type="application/json",
    )

    response["Content-Disposition"] = (
        f'attachment; filename="release-{release_id}.json"'
    )

    return response


@router.post("/import/{project_id}/", response=ReleaseList)
def import_release(
    request,
    project_id: UUID,
    file: File[UploadedFile],
    name: Form[str],
    description: Form[str] = "",
):
    try:
        snapshot = json.load(file)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValidationError("Invalid JSON file.")

    return import_release_service(
        project_id=project_id,
        snapshot=snapshot,
        name=name,
        description=description,
    )


@router.post(
    "/{release_id}/restore/",
    response={
        200: ProjectRead,
        409: dict,
    },
)
def restore_release_route(
    request,
    release_id: UUID,
    force: bool = False,
):
    try:
        return restore_release_service(
            release_id=release_id,
            force=force,
        )
    except ValidationError as exc:
        return 409, {
            "message": exc.messages[0]
        }


@router.post(
    "/merge/",
    response={
        200: ReleaseList,
        409: dict,
    },
)
def merge_releases_route(request, payload: ReleaseMerge):
    try:
        return merge_releases_service(
            ground_truth_id=payload.ground_truth_id,
            incoming_id=payload.incoming_id,
            name=payload.name,
            description=payload.description,
            release_notes=payload.release_notes,
        )
    except MergeConflictError as exc:
        return 409, exc.to_dict()