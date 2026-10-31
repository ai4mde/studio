"""Resolve three-way merge conflicts without changing the database."""

from copy import deepcopy
import json

from django.apps import apps

from .delta import ProjectDeltaError, generate_delta
from .merge import _merge_candidate, _missing_references, ProjectMergeError
from .types import MergeConflict, MergeResolution, ProjectState


class ProjectMergeResolutionError(ValueError):
    """A conflict resolution is missing, invalid, or produces an invalid state."""


def _conflict_key(conflict: MergeConflict | MergeResolution) -> tuple[str, str, str, str | None]:
    return (conflict["kind"], conflict["model"], conflict["id"], conflict["field"])


def _restore_target(
    merged: ProjectState,
    conflict: MergeConflict,
    base: ProjectState,
    local: ProjectState,
    incoming: ProjectState,
) -> None:
    """Restore a referenced row from a branch where it still exists."""
    label, object_id, field = conflict["model"], conflict["id"], conflict["field"]
    if field is None:
        raise ProjectMergeResolutionError("Missing-reference conflict has no field")

    row = merged["models"][label].get(object_id)
    if row is None:
        raise ProjectMergeResolutionError(f"Referencing object {label}({object_id}) was removed")

    fk = next(
        f for f in apps.get_model(label)._meta.concrete_fields if f.attname == field
    )
    target_label = fk.remote_field.model._meta.label
    target_id = str(row[field])
    target_rows = merged["models"].get(target_label)
    if target_rows is None:
        raise ProjectMergeResolutionError(f"Reference target model {target_label} is not versioned")
    if target_id in target_rows:
        return  # Another resolution already restored the target.

    for source in (local, incoming, base):
        source_row = source["models"][target_label].get(target_id)
        if source_row is not None:
            target_rows[target_id] = deepcopy(source_row)
            return
    raise ProjectMergeResolutionError(f"Cannot restore missing reference {target_label}({target_id})")


def resolve_merge_conflicts(
    base: ProjectState,
    local: ProjectState,
    incoming: ProjectState,
    resolutions: list[MergeResolution],
) -> ProjectState:
    """Apply explicit choices to merge conflicts and return a validated merged state."""
    # Recompute conflicts so choices cannot refer to a different or stale merge.
    try:
        merged, conflicts = _merge_candidate(base, local, incoming)
    except ProjectMergeError as exc:
        raise ProjectMergeResolutionError(str(exc)) from exc

    expected = {_conflict_key(conflict): conflict for conflict in conflicts}
    provided: dict[tuple[str, str, str, str | None], MergeResolution] = {}

    for resolution in resolutions:
        try:
            key = _conflict_key(resolution)
        except (TypeError, KeyError) as exc:
            raise ProjectMergeResolutionError("Malformed conflict resolution") from exc
        if key in provided:
            raise ProjectMergeResolutionError(f"Duplicate conflict resolution: {key}")
        if key not in expected:
            raise ProjectMergeResolutionError(f"Unknown or stale conflict resolution: {key}")
        provided[key] = resolution

    missing = expected.keys() - provided.keys()
    if missing:
        raise ProjectMergeResolutionError(f"Missing conflict resolutions: {sorted(missing, key=str)}")

    # Resolve edits and object existence before handling relationships.
    for key, conflict in expected.items():
        kind, label, object_id, field = key
        if kind == "MISSING_REFERENCE":
            continue

        resolution = provided[key]
        choice = resolution.get("choice")
        if "value" in resolution and choice != "CUSTOM":
            raise ProjectMergeResolutionError("Only CUSTOM resolutions may contain a value")

        rows = merged["models"][label]
        if kind == "FIELD":
            if field is None or choice not in ("LOCAL", "INCOMING", "BASE", "CUSTOM"):
                raise ProjectMergeResolutionError(f"Invalid field resolution for {label}({object_id})")
            if choice == "CUSTOM":
                if "value" not in resolution:
                    raise ProjectMergeResolutionError("CUSTOM resolution requires a value")
                value = resolution["value"]
                try:
                    json.dumps(value, allow_nan=False)
                except (ValueError, TypeError) as exc:
                    raise ProjectMergeResolutionError("CUSTOM value must be JSON serializable") from exc
            else:
                value = conflict[{"LOCAL": "local", "INCOMING": "incoming", "BASE": "base"}[choice]]
            rows[object_id][field] = deepcopy(value)
        else:
            if choice not in ("LOCAL", "INCOMING"):
                raise ProjectMergeResolutionError(f"Invalid object resolution for {label}({object_id})")
            row = conflict["local" if choice == "LOCAL" else "incoming"]
            if row is None:
                rows.pop(object_id, None)
            else:
                rows[object_id] = deepcopy(row)

    # Resolve dangling references after all field and object choices are applied.
    for key, conflict in expected.items():
        if conflict["kind"] != "MISSING_REFERENCE":
            continue
        choice = provided[key].get("choice")
        if "value" in provided[key]:
            raise ProjectMergeResolutionError("A reference resolution cannot contain a value")
        label, object_id = conflict["model"], conflict["id"]
        if choice == "DELETE_OBJECT":
            if label == "metadata.Project":
                raise ProjectMergeResolutionError("Cannot delete the project")
            merged["models"][label].pop(object_id, None)
        elif choice == "RESTORE_TARGET":
            _restore_target(merged, conflict, base, local, incoming)
        else:
            raise ProjectMergeResolutionError(f"Invalid reference resolution for {label}({object_id})")

    # Choices can introduce further dangling references or invalid row structures.
    if set(merged["models"]["metadata.Project"]) != {base["project_id"]}:
        raise ProjectMergeResolutionError("The project row must be preserved")
    try:
        generate_delta(base, merged)
    except ProjectDeltaError as exc:
        raise ProjectMergeResolutionError(str(exc)) from exc

    dangling = _missing_references(merged, base, local, incoming)
    if dangling:
        first = dangling[0]
        raise ProjectMergeResolutionError(
            f"Resolved merge contains an invalid reference: "
            f"{first['model']}({first['id']}).{first['field']}"
        )

    return merged
