from copy import deepcopy
from uuid import UUID

from .constants import (
    PROJECT_MODEL_SCOPES,
    SNAPSHOT_FORMAT,
    SNAPSHOT_SCHEMA_VERSION,
)
from .types import (
    ProjectState,
    ProjectDelta,
    FieldChange,
    CreateOperation,
    UpdateOperation,
    DeleteOperation,
)


class ProjectDeltaError(ValueError):
    """A snapshot or delta is malformed, incompatible, or cannot be applied."""



def empty_project_state(project_id) -> ProjectState:
    """Return the baseline for an initial version (all tables empty)."""
    try:
        project_id = str(UUID(str(project_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ProjectDeltaError("Invalid project UUID") from exc

    return {
        "format": SNAPSHOT_FORMAT,
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "project_id": project_id,
        "models": {label: {} for label in sorted(PROJECT_MODEL_SCOPES)},
    }


def _validate_snapshot(snapshot: ProjectState) -> None:
    """Validate that a project state is well-formed and compatible with the current schema."""
    if not isinstance(snapshot, dict) or set(snapshot) != {
        "format", "schema_version", "project_id", "models"
    }:
        raise ProjectDeltaError("Expected a serialized project state")

    if (
        snapshot["format"] != SNAPSHOT_FORMAT
        or snapshot["schema_version"] != SNAPSHOT_SCHEMA_VERSION
    ):
        raise ProjectDeltaError(
            "Unsupported project state format or schema version"
        )

    try:
        if str(UUID(snapshot["project_id"])) != snapshot["project_id"]:
            raise ValueError("Non-canonical project UUID")
    except (TypeError, ValueError, AttributeError) as exc:
        raise ProjectDeltaError("Invalid project UUID in state") from exc

    models = snapshot["models"]

    if (
        not isinstance(models, dict)
        or set(models) != set(PROJECT_MODEL_SCOPES)
    ):
        raise ProjectDeltaError(
            "Project state does not match the registered model scopes"
        )

    for model, rows in models.items():
        if not isinstance(rows, dict):
            raise ProjectDeltaError(
                f"{model} must contain a mapping of IDs to rows"
            )

        for object_id, row in rows.items():
            if (
                not isinstance(object_id, str)
                or not isinstance(row, dict)
                or row.get("id") != object_id
                or not all(isinstance(name, str) for name in row)
            ):
                raise ProjectDeltaError(
                    f"Invalid row or primary key in {model}({object_id})"
                )


def _check_compatible(before: ProjectState, after: ProjectState) -> None:
    _validate_snapshot(before)
    _validate_snapshot(after)

    if before["project_id"] != after["project_id"]:
        raise ProjectDeltaError(
            "Cannot compare states from different projects"
        )



def generate_delta(
    old_state: ProjectState,
    new_state: ProjectState,
) -> ProjectDelta:
    """Generate CREATE, UPDATE, and DELETE operations between two project states."""
    _check_compatible(old_state, new_state)

    operations: ProjectDelta = []

    for model in sorted(PROJECT_MODEL_SCOPES):
        old_rows = old_state["models"][model]
        new_rows = new_state["models"][model]

        for object_id in sorted(old_rows.keys() | new_rows.keys()):

            # Create
            if object_id not in old_rows:
                operations.append(
                    CreateOperation(
                        operation="CREATE",
                        model=model,
                        id=object_id,
                        data=deepcopy(new_rows[object_id]),
                    )
                )

            # Delete
            elif object_id not in new_rows:
                operations.append(
                    DeleteOperation(
                        operation="DELETE",
                        model=model,
                        id=object_id,
                        data=deepcopy(old_rows[object_id]),
                    )
                )

            # Update
            else:
                old = old_rows[object_id]
                new = new_rows[object_id]

                if old == new:
                    continue

                if old.keys() != new.keys():
                    raise ProjectDeltaError(
                        f"Fields differ between states for {model}({object_id}); "
                        "a schema migration is required"
                    )

                changes: dict[str, FieldChange] = {
                    field: {
                        "old": deepcopy(old[field]),
                        "new": deepcopy(new[field]),
                    }
                    for field in sorted(old)
                    if old[field] != new[field]
                }

                if "id" in changes:
                    raise ProjectDeltaError(
                        f"Cannot change the primary key of {model}({object_id})"
                    )

                operations.append(
                    UpdateOperation(
                        operation="UPDATE",
                        model=model,
                        id=object_id,
                        changes=changes,
                    )
                )

    return operations


def apply_delta(state: ProjectState, delta: ProjectDelta) -> ProjectState:
    """Apply a delta to a copy of the project state without modifying the database."""
    _validate_snapshot(state)
    result = deepcopy(state)
    seen: set[tuple[str, str]] = set()

    for index, op in enumerate(delta):
        if not isinstance(op, dict):
            raise ProjectDeltaError(
                f"Operation {index} must be an object"
            )

        operation = op.get("operation")
        model = op.get("model")
        object_id = op.get("id")

        if operation not in ("CREATE", "UPDATE", "DELETE"):
            raise ProjectDeltaError(
                f"Unknown delta operation at index {index}"
            )

        if not isinstance(model, str) or model not in result["models"]:
            raise ProjectDeltaError(
                f"Unknown model in operation {index}: {model}"
            )

        if not isinstance(object_id, str):
            raise ProjectDeltaError(
                f"Invalid object ID in operation {index}"
            )

        identity = (model, object_id)

        if identity in seen:
            raise ProjectDeltaError(
                f"Duplicate operation for {model}({object_id})"
            )

        seen.add(identity)

        required = (
            {"operation", "model", "id", "changes"}
            if operation == "UPDATE"
            else {"operation", "model", "id", "data"}
        )

        if set(op) != required:
            raise ProjectDeltaError(
                f"Invalid {operation} payload for {model}({object_id})"
            )

        rows = result["models"][model]

        if op["operation"] == "CREATE":
            data = op["data"]

            if (
                not isinstance(data, dict)
                or data.get("id") != object_id
            ):
                raise ProjectDeltaError(
                    f"Invalid CREATE row for {model}({object_id})"
                )

            if object_id in rows:
                raise ProjectDeltaError(
                    f"Cannot CREATE existing {model}({object_id})"
                )

            rows[object_id] = deepcopy(data)

        elif op["operation"] == "DELETE":
            if object_id not in rows:
                raise ProjectDeltaError(
                    f"Cannot DELETE missing {model}({object_id})"
                )

            if rows[object_id] != op["data"]:
                raise ProjectDeltaError(
                    f"Stale DELETE for {model}({object_id})"
                )

            del rows[object_id]

        else:  # UPDATE
            if object_id not in rows:
                raise ProjectDeltaError(
                    f"Cannot UPDATE missing {model}({object_id})"
                )

            changes = op["changes"]

            if (
                not isinstance(changes, dict)
                or not changes
                or "id" in changes
            ):
                raise ProjectDeltaError(
                    f"Invalid UPDATE fields for {model}({object_id})"
                )

            row = rows[object_id]

            for field, change in changes.items():
                if (
                    not isinstance(field, str)
                    or field not in row
                    or not isinstance(change, dict)
                    or set(change) != {"old", "new"}
                ):
                    raise ProjectDeltaError(
                        f"Invalid change for "
                        f"{model}({object_id}).{field}"
                    )

                if row[field] != change["old"]:
                    raise ProjectDeltaError(
                        f"Stale UPDATE for "
                        f"{model}({object_id}).{field}"
                    )

                row[field] = deepcopy(change["new"])

    _validate_snapshot(result)

    return result


def invert_delta(delta: ProjectDelta) -> ProjectDelta:
    """Return operations that undo a delta."""
    inverted: ProjectDelta = []
    for op in reversed(delta):
        if (
            not isinstance(op, dict)
            or op.get("operation") not in ("CREATE", "UPDATE", "DELETE")
        ):
            raise ProjectDeltaError("Invalid operation to invert")

        if op["operation"] == "CREATE":
            inverse_delete = DeleteOperation(
                operation="DELETE",
                model=op["model"],
                id=op["id"],
                data=deepcopy(op["data"]),
            )
            inverted.append(inverse_delete)

        elif op["operation"] == "DELETE":
            inverse_create = CreateOperation(
                operation="CREATE",
                model=op["model"],
                id=op["id"],
                data=deepcopy(op["data"]),
            )
            inverted.append(inverse_create)

        else:
            inverse_update = UpdateOperation(
                operation="UPDATE",
                model=op["model"],
                id=op["id"],
                changes={
                    field: {
                        "old": deepcopy(change["new"]),
                        "new": deepcopy(change["old"]),
                    }
                    for field, change in op["changes"].items()
                },
            )
            inverted.append(inverse_update)

    return inverted
