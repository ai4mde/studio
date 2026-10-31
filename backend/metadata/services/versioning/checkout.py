from uuid import UUID

from django.db import transaction

from metadata.models import Project, ProjectVersion

from .applicator import apply_project_changes
from .delta import generate_delta
from .serializer import serialize_project
from .versions import reconstruct_version


class ProjectCheckoutError(ValueError):
    """The requested version cannot be checked out."""


def _uuid(value: UUID | str, name: str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ProjectCheckoutError(f"Invalid {name} UUID") from exc


@transaction.atomic
def checkout_version(project_id: UUID | str, version_id: UUID | str) -> ProjectVersion:
    """Restore a version without losing uncommitted changes or changing history."""
    project_uuid = _uuid(project_id, "project")
    version_uuid = _uuid(version_id, "version")

    project = Project.objects.select_for_update().filter(pk=project_uuid).first()
    if project is None:
        raise ProjectCheckoutError("Project does not exist")

    version = ProjectVersion.objects.filter(
        pk=version_uuid, project_id=project.pk
    ).first()
    if version is None:
        raise ProjectCheckoutError("Version does not exist in this project")

    # When checking out a version must have been created before
    if project.current_version_id is None:
        raise ProjectCheckoutError("Project has no active version")

    active_version = project.current_version
    if active_version.project_id != project.pk:
        raise ProjectCheckoutError("Active version belongs to a different project")

    # Refuse to discard changes made since the active version was saved.
    current_state = serialize_project(project.pk)
    active_state = reconstruct_version(active_version.pk)
    if current_state != active_state:
        raise ProjectCheckoutError(
            "Project has uncommitted changes; create a version before checkout"
        )

    # If the requested version is already the active version, do nothing.
    if version.pk == active_version.pk:
        return version

    target_state = reconstruct_version(version.pk)
    delta = generate_delta(current_state, target_state)
    if delta:
        apply_project_changes(project.pk, delta)

    project.current_version = version
    project.save(update_fields=["current_version"])
    return version
