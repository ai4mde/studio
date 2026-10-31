from copy import deepcopy
from uuid import UUID

from django.db import transaction

from metadata.models import Project, ProjectVersion

from .constants import CHECKPOINT_INTERVAL
from .delta import (
    ProjectDeltaError,
    apply_delta,
    empty_project_state,
    generate_delta,
)
from .serializer import serialize_project
from .types import ProjectDelta, ProjectState


class ProjectVersionError(ValueError):
    """A version cannot be created or reconstructed."""


def _uuid(value: UUID | str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ProjectVersionError("Invalid UUID") from exc


def should_checkpoint(parent: ProjectVersion | None) -> bool:
    """Check whether the next version needs a checkpoint."""
    count = 0
    current = parent

    while current is not None:
        if current.checkpoint is not None:
            break

        count += 1

        if count >= CHECKPOINT_INTERVAL - 1:
            return True

        current = current.parent

    return False


def reconstruct_version(version_id: UUID | str | ProjectVersion) -> ProjectState:
    """Reconstruct a version using the nearest checkpoint and subsequent deltas."""
    if isinstance(version_id, ProjectVersion):
        version_id = version_id.pk

    version = ProjectVersion.objects.filter(pk=_uuid(version_id)).first()
    if version is None:
        raise ProjectVersionError("Version does not exist")

    project_id = version.project_id
    history: list[ProjectVersion] = []
    visited: set[UUID] = set()
    current = version

    while True:
        # Should never happen, something was coded wrong
        if current.pk in visited:
            raise ProjectVersionError("Cycle detected in version history")
        visited.add(current.pk)

        # Should never happen, something was coded wrong
        if current.project_id != project_id:
            raise ProjectVersionError("Version history crosses project boundaries")

        # Stop at the nearest checkpoint.
        if current.checkpoint is not None:
            state: ProjectState = deepcopy(current.checkpoint)
            break

        history.append(current)

        if current.parent_id is None:
            if current.merge_parent_id is not None:
                raise ProjectVersionError("A root version cannot have a merge parent")

            state = empty_project_state(project_id)
            break

        current = current.parent

    for node in reversed(history):
        try:
            delta: ProjectDelta = node.delta
            state = apply_delta(state, delta)
        except (ProjectDeltaError, TypeError, KeyError) as exc:
            raise ProjectVersionError(
                f"Cannot reconstruct version {node.pk}: {exc}"
            ) from exc

    return state


@transaction.atomic
def create_version(project_id: UUID | str, message: str = "") -> ProjectVersion:
    """Save changes since the active version and make the new version active."""
    project = Project.objects.select_for_update().filter(pk=_uuid(project_id)).first()
    if project is None:
        raise ProjectVersionError("Project does not exist")

    parent: ProjectVersion | None = None
    if project.current_version_id is not None:
        parent = project.current_version

        # Preventative check, should never happen if the database is consistent
        if parent.project_id != project.pk:
            raise ProjectVersionError(
                "The active version must belong to the same project"
            )
    
        previous_state = reconstruct_version(parent.pk)

    else:
        # Someone is trying to create a version for a project that has no active version, but already has versions in the database.
        # This should never happen if the database is consistent.
        if ProjectVersion.objects.filter(project_id=project.pk).exists():
            raise ProjectVersionError(
                "Project already has versions but no active version"
            )

        # We start with an empty project state if there is no active version.
        previous_state = empty_project_state(project.pk)

    current_state = serialize_project(project.pk)
    delta = generate_delta(previous_state, current_state)
    if not delta:
        raise ProjectVersionError("No changes since the active version")

    version = ProjectVersion(
        project=project,
        parent=parent,
        delta=delta,
        checkpoint=current_state if should_checkpoint(parent) else None,
        message=message,
    )
    version.full_clean()
    version.save()

    project.current_version = version
    project.save(update_fields=["current_version"])
    return version
