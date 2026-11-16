from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction

from metadata.models import Project, Release
from metadata.services.versioning.restore import restore_project
from metadata.services.versioning.snapshot import snapshot_project
from metadata.services.versioning.utils import validate_snapshot


@transaction.atomic
def create_release(
    project_id: UUID | str,
    name: str,
    description: str | None = None,
    release_notes: list[str] | None = None,
) -> Release:
    snapshot = snapshot_project(project_id)

    release = Release.objects.create(
        project_id=project_id,
        name=name,
        description=description or "",
        release_notes=release_notes or [],
        project_data=snapshot,
    )
    
    project = release.project
    project.current_release = release
    project.save(update_fields=["current_release"])
    
    return release


def export_release(release_id: UUID | str) -> dict:
    release = Release.objects.only("project_data").get(pk=release_id)
    return release.project_data


def import_release(
    project_id: UUID | str,
    snapshot: dict,
    name: str,
    description: str | None = None,
    release_notes: list[str] | None = None,
) -> Release:
    validate_snapshot(snapshot, project_id)
    project = Project.objects.get(pk=project_id)

    return Release.objects.create(
        project=project,
        name=name,
        description=description or "",
        release_notes=release_notes or [],
        project_data=snapshot,
    )


@transaction.atomic
def restore_release(
    release_id: UUID | str,
    force: bool = False,
) -> Project:
    release = Release.objects.select_related("project").get(
        pk=release_id
    )

    project = Project.objects.select_for_update().get(
        pk=release.project_id
    )

    current_release = project.current_release

    if not force:
        if current_release is None:
            raise ValidationError(
                "Cannot verify whether the project has unsaved changes. "
                "Use force=True to restore anyway."
            )

        current_snapshot = snapshot_project(project.pk)

        if current_release.project_data != current_snapshot:
            raise ValidationError(
                "Current project state has changed since the last release. "
                "Create a new release before restoring another one, "
                "or use force=True to discard these changes."
            )

    restored_project = restore_project(
        project.pk,
        release.project_data,
    )

    restored_project.current_release = release
    restored_project.save(update_fields=["current_release"])

    return restored_project