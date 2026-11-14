from uuid import UUID

from django.core import serializers
from django.core.exceptions import ValidationError
from django.db import transaction

from metadata.models import Project, Release
from .restore import (
    _check_no_uuid_collisions,
    _snapshot_ids_and_references,
    restore_project,
)
from .utils import validate_snapshot


class ProjectAlreadyExistsError(ValidationError):
    def __init__(self, project_id: UUID):
        self.project_id = project_id
        super().__init__(
            "This project already exists. Import the file as a version "
            "from the project's Versions tab instead."
        )


@transaction.atomic
def import_project(
    snapshot: dict,
    name: str = "Imported version",
    description: str | None = None,
    release_notes: list[str] | None = None,
) -> Project:
    try:
        project_id = UUID(str(snapshot["project_id"]))
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ValidationError("Snapshot has an invalid project ID.") from exc

    if Project.objects.filter(pk=project_id).exists():
        raise ProjectAlreadyExistsError(project_id)

    validate_snapshot(snapshot, project_id)
    snapshot_ids = _snapshot_ids_and_references(snapshot["objects"])
    _check_no_uuid_collisions(project_id, snapshot_ids)

    # The restore project expects the Project entry to be in the DB already
    # So we create it before we call it from the deserialized data
    project_record = next(
        obj for obj in snapshot["objects"]
        if obj["model"] == Project._meta.label_lower
    )
    try:
        project_entry = next(serializers.deserialize("python", [project_record]))
        project_entry.object.save(force_insert=True)
    except (ValueError, TypeError) as exc:
        raise ValidationError(f"Could not deserialize project: {exc}") from exc

    project = restore_project(project_id, snapshot)

    release = Release.objects.create(
        project=project,
        name=name,
        description=description or "",
        release_notes=release_notes or [],
        project_data=snapshot,
    )
    project.current_release = release
    project.save(update_fields=["current_release"])
    return project
