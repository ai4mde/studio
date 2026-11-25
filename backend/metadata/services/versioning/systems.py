"""
    Exporting selected systems of a project, and importing them into a project.

    Both build on the snapshot format of snapshot_project: a systems export is a
    project snapshot with only the selected systems and everything that belongs
    to them. Importing gives every object a new id, attaches the systems to the
    target project and restores the combined snapshot with restore_project.
"""
import uuid
from copy import deepcopy
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction

from metadata.models import Release
from metadata.services.versioning.releases import create_release
from metadata.services.versioning.restore import restore_project
from metadata.services.versioning.snapshot import snapshot_project


PROJECT_LABEL = "metadata.project"
SYSTEM_LABEL = "metadata.system"


def _references(obj: dict) -> set[str]:
    """The ids an object points to through its foreign keys."""
    found: set[str] = set()

    for value in obj["fields"].values():
        if isinstance(value, str):
            found.add(value)
        elif isinstance(value, list):
            found.update(item for item in value if isinstance(item, str))

    return found


def export_systems(project_id: UUID | str, system_ids: list[UUID]) -> dict:
    snapshot = snapshot_project(project_id)
    objects = [obj for obj in snapshot["objects"] if obj["model"] != PROJECT_LABEL]

    wanted = {str(system_id) for system_id in system_ids}
    found = {str(obj["pk"]) for obj in objects if obj["model"] == SYSTEM_LABEL}

    if not wanted:
        raise ValidationError("Select at least one system to export.")
    if not wanted <= found:
        raise ValidationError("Some of the selected systems don't belong to this project.")

    all_ids = {str(obj["pk"]) for obj in objects}
    kept = set(wanted)

    changed = True
    while changed:
        changed = False

        for obj in objects:
            pk = str(obj["pk"])
            if pk in kept or obj["model"] == SYSTEM_LABEL:
                continue

            references = _references(obj)

            # Belongs to something that is exported (a classifier, diagram, ...)
            belongs_to_kept = bool(references & kept)

            # Or is a plain record that an exported object depends on, like
            # the Multiplicity and EndpointLabel of an association
            used_by_kept = not (references & all_ids) and any(
                pk in _references(other)
                for other in objects
                if str(other["pk"]) in kept
            )

            if belongs_to_kept or used_by_kept:
                kept.add(pk)
                changed = True

    return {
        "schema_version": snapshot["schema_version"],
        "project_id": snapshot["project_id"],
        "system_ids": sorted(wanted),
        "objects": [obj for obj in objects if str(obj["pk"]) in kept],
    }


@transaction.atomic
def import_systems(
    project_id: UUID | str,
    systems_snapshot: dict,
    name: str,
    description: str | None = None,
    release_notes: list[str] | None = None,
) -> Release:
    if not isinstance(systems_snapshot, dict) or not isinstance(
        systems_snapshot.get("objects"), list
    ):
        raise ValidationError("This file isn't a systems export.")

    objects = deepcopy(systems_snapshot["objects"])

    if any(obj.get("model") == PROJECT_LABEL for obj in objects):
        raise ValidationError(
            "This is a project file. Import it from the Projects page, "
            "or as a version from a file."
        )
    if not any(obj.get("model") == SYSTEM_LABEL for obj in objects):
        raise ValidationError("The file doesn't contain any systems.")

    # New ids, so the same systems can be imported more than once and into
    # any project. Typed data shares its id with its classifier or relation,
    # so they end up with the same new id as well.
    new_ids: dict[str, str] = {}
    for obj in objects:
        new_ids.setdefault(str(obj["pk"]), str(uuid.uuid4()))

    for obj in objects:
        obj["pk"] = new_ids[str(obj["pk"])]

        for field, value in obj["fields"].items():
            if isinstance(value, str) and value in new_ids:
                obj["fields"][field] = new_ids[value]
            elif isinstance(value, list):
                obj["fields"][field] = [
                    new_ids.get(item, item) if isinstance(item, str) else item
                    for item in value
                ]

        if obj["model"] == SYSTEM_LABEL:
            obj["fields"]["project"] = str(project_id)

    # Restore the project with its current content plus the imported systems,
    # then save the result as a new release
    current = snapshot_project(project_id)
    restore_project(
        project_id,
        {**current, "objects": current["objects"] + objects},
    )

    return create_release(
        project_id=project_id,
        name=name,
        description=description,
        release_notes=release_notes,
    )
