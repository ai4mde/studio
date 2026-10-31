"""Utilities for navigating the project version graph."""

from uuid import UUID

from metadata.models import ProjectVersion


class ProjectVersionGraphError(ValueError):
    """The requested version ancestry is invalid or ambiguous."""


def _version_uuid(value: UUID | str | ProjectVersion) -> UUID:
    if isinstance(value, ProjectVersion):
        return value.pk
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ProjectVersionGraphError("Invalid version UUID") from exc


def _ancestor_ids(
    version_id: UUID,
    parents: dict[UUID, tuple[UUID | None, UUID | None]],
) -> set[UUID]:
    """Find all ancestors, including the version itself, through both parent links."""
    visited: set[UUID] = set()
    visiting: set[UUID] = set()
    stack = [(version_id, False)]

    while stack:
        current, finished = stack.pop()
        if finished:
            visiting.remove(current)
            visited.add(current)
            continue
        if current in visited:
            continue
        if current in visiting:
            raise ProjectVersionGraphError("Cycle detected in version history")
        if current not in parents:
            raise ProjectVersionGraphError("Version history crosses project boundaries")

        parent_id, merge_parent_id = parents[current]
        if parent_id is None and merge_parent_id is not None:
            raise ProjectVersionGraphError("A root version cannot have a merge parent")

        visiting.add(current)
        stack.append((current, True))
        for ancestor_id in (parent_id, merge_parent_id):
            if ancestor_id is not None:
                stack.append((ancestor_id, False))

    return visited


def find_common_ancestor(
    first: UUID | str | ProjectVersion,
    second: UUID | str | ProjectVersion,
) -> ProjectVersion | None:
    """Find the nearest common ancestor of two versions, or None if they are unrelated."""
    first_id = _version_uuid(first)
    second_id = _version_uuid(second)

    versions = dict(
        ProjectVersion.objects.filter(pk__in=(first_id, second_id)).values_list(
            "pk", "project_id"
        )
    )
    if first_id not in versions or second_id not in versions:
        raise ProjectVersionGraphError("Version does not exist")
    if versions[first_id] != versions[second_id]:
        raise ProjectVersionGraphError("Versions belong to different projects")

    parents = {
        version_id: (parent_id, merge_parent_id)
        for version_id, parent_id, merge_parent_id in ProjectVersion.objects.filter(
            project_id=versions[first_id]
        ).values_list("pk", "parent_id", "merge_parent_id")
    }

    common = _ancestor_ids(first_id, parents) & _ancestor_ids(second_id, parents)
    if not common:
        return None

    # Exclude any common ancestor that is itself a parent of a common version.
    # The remaining nodes are the nearest common ancestors in the DAG.
    older = {
        ancestor_id
        for version_id in common
        for ancestor_id in parents[version_id]
        if ancestor_id in common
    }
    nearest = common - older
    if len(nearest) != 1:
        raise ProjectVersionGraphError("Multiple common ancestors; merge base is ambiguous")

    return ProjectVersion.objects.get(pk=nearest.pop())
