
"""Three-way merging of project states without database writes."""

from copy import deepcopy

from django.apps import apps
from django.db import models

from .constants import EXCLUDED_FIELDS
from .delta import ProjectDeltaError, generate_delta
from .types import ProjectRow, ProjectState, MergeConflict, MergeConflictKind, MergeResult


class ProjectMergeError(ValueError):
    """The input project states cannot be compared safely."""


def _conflict(
    kind: MergeConflictKind,
    model: str,
    object_id: str,
    field: str | None,
    base: object,
    local: object,
    incoming: object,
) -> MergeConflict:
    return {
        "kind": kind,
        "model": model,
        "id": object_id,
        "field": field,
        "base": deepcopy(base),
        "local": deepcopy(local),
        "incoming": deepcopy(incoming),
    }


def _missing_references(
    state: ProjectState,
    base: ProjectState,
    local: ProjectState,
    incoming: ProjectState,
) -> list[MergeConflict]:
    """Find references to objects that the given state does not contain."""
    conflicts: list[MergeConflict] = []

    for label, rows in state["models"].items():
        model = apps.get_model(label)
        for fk in model._meta.concrete_fields:
            if not isinstance(fk, models.ForeignKey):
                continue
            if fk.attname in EXCLUDED_FIELDS.get(label, ()):
                continue

            target_label = fk.remote_field.model._meta.label
            for object_id, row in sorted(rows.items()):
                reference = row[fk.attname]
                if reference is None and fk.null:
                    continue
                if (
                    reference is not None
                    and target_label in state["models"]
                    and str(reference) in state["models"][target_label]
                ):
                    continue

                def previous_value(source: ProjectState) -> object:
                    source_row = source["models"][label].get(object_id)
                    return source_row.get(fk.attname) if source_row is not None else None

                conflicts.append(
                    _conflict(
                        "MISSING_REFERENCE",
                        label,
                        object_id,
                        fk.attname,
                        previous_value(base),
                        previous_value(local),
                        previous_value(incoming),
                    )
                )

    return conflicts


def _merge_candidate(
    base: ProjectState,
    local: ProjectState,
    incoming: ProjectState,
) -> tuple[ProjectState, list[MergeConflict]]:
    """Build a provisional merged state and collect conflicts without writing to the DB."""
    try:
        # Validate snapshot format, schema, IDs, and row primary keys.
        generate_delta(base, local)
        generate_delta(base, incoming)
    except ProjectDeltaError as exc:
        raise ProjectMergeError(str(exc)) from exc

    project_id = base["project_id"]
    for name, state in (("base", base), ("local", local), ("incoming", incoming)):
        if set(state["models"]["metadata.Project"]) != {project_id}:
            raise ProjectMergeError(f"{name} must preserve the project row")

        # A broken reference in an input is invalid data, not a merge conflict.
        invalid = _missing_references(state, state, state, state)
        if invalid:
            first = invalid[0]
            raise ProjectMergeError(
                f"{name} contains an invalid foreign-key reference: "
                f"{first['model']}({first['id']}).{first['field']}"
            )

    merged: ProjectState = deepcopy(base)
    conflicts: list[MergeConflict] = []

    for label in sorted(base["models"]):
        base_rows = base["models"][label]
        local_rows = local["models"][label]
        incoming_rows = incoming["models"][label]
        result_rows: dict[str, ProjectRow] = {}

        for object_id in sorted(base_rows.keys() | local_rows.keys() | incoming_rows.keys()):
            original = base_rows.get(object_id)
            ours = local_rows.get(object_id)
            theirs = incoming_rows.get(object_id)

            if original is None:
                if ours is not None and theirs is not None and ours != theirs:
                    conflicts.append(_conflict(
                        "CREATE_CREATE", label, object_id, None, None, ours, theirs
                    ))
                    # Provisional value for later reference checks, never returned on conflict.
                    result_rows[object_id] = deepcopy(ours)
                elif ours is not None or theirs is not None:
                    result_rows[object_id] = deepcopy(ours if ours is not None else theirs)
                continue

            if ours is None and theirs is None:
                continue  # Both branches deleted the object.

            if ours is None:
                if theirs != original:
                    conflicts.append(_conflict(
                        "DELETE_UPDATE", label, object_id, None, original, None, theirs
                    ))
                    result_rows[object_id] = deepcopy(theirs)
                continue

            if theirs is None:
                if ours != original:
                    conflicts.append(_conflict(
                        "UPDATE_DELETE", label, object_id, None, original, ours, None
                    ))
                    result_rows[object_id] = deepcopy(ours)
                continue

            result_row: ProjectRow = {}
            for field in sorted(original):
                base_value = original[field]
                local_value = ours[field]
                incoming_value = theirs[field]

                if local_value == incoming_value:
                    chosen = local_value
                elif local_value == base_value:
                    chosen = incoming_value
                elif incoming_value == base_value:
                    chosen = local_value
                else:
                    conflicts.append(_conflict(
                        "FIELD", label, object_id, field,
                        base_value, local_value, incoming_value,
                    ))
                    # Keep a provisional value so other reference conflicts can be found.
                    chosen = local_value

                result_row[field] = deepcopy(chosen)

            result_rows[object_id] = result_row

        merged["models"][label] = result_rows

    # Check relationships even if other conflicts were found earlier.
    conflicts.extend(_missing_references(merged, base, local, incoming))
    return merged, conflicts


def merge_project_states(
    base: ProjectState,
    local: ProjectState,
    incoming: ProjectState,
) -> MergeResult:
    """Merge divergent project states, returning a state only if conflict-free."""
    merged, conflicts = _merge_candidate(base, local, incoming)
    if conflicts:
        return {"state": None, "conflicts": conflicts}
    return {"state": merged, "conflicts": []}
