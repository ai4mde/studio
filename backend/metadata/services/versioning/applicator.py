from heapq import heappop, heappush
from uuid import UUID

from django.apps import apps
from django.db import models, transaction

from metadata.models import Project

from .constants import EXCLUDED_FIELDS, PROJECT_MODEL_SCOPES
from .delta import ProjectDeltaError, apply_delta
from .serializer import serialize_project
from .types import ProjectDelta, ProjectState


class ProjectApplicationError(ValueError):
    """The requested changes cannot safely be applied to the project."""


def _model_classes() -> dict[str, type[models.Model]]:
    """Get all model classes that are part of the project serialization scope."""
    return {label: apps.get_model(label) for label in PROJECT_MODEL_SCOPES}


def _foreign_keys(model: type[models.Model]):
    """Get all relations from the current model to other models in the project serialization scope."""
    return (
        field
        for field in model._meta.concrete_fields
        if isinstance(field, (models.ForeignKey, models.OneToOneField))
        and field.attname not in EXCLUDED_FIELDS.get(model._meta.label, ())
    )


def _validate_target(
    state: ProjectState,
    project_id: UUID,
    model_classes: dict[str, type[models.Model]],
) -> None:
    """Check target rows and project-local references before writing anything."""
    if state["project_id"] != str(project_id):
        raise ProjectApplicationError("The target belongs to a different project")

    project_rows = state["models"]["metadata.Project"]
    if set(project_rows) != {str(project_id)}:
        raise ProjectApplicationError("The project row must be preserved")

    for label, rows in state["models"].items():
        model = model_classes[label]
        pk_name = model._meta.pk.attname
        fields = {
            field.attname
            for field in model._meta.concrete_fields
            if field.attname not in EXCLUDED_FIELDS.get(label, ())
        }
        fks = tuple(_foreign_keys(model))

        for object_id, row in rows.items():
            if set(row) != fields or str(row.get(pk_name)) != object_id:
                raise ProjectApplicationError(
                    f"Wrong fields or primary key for {label}({object_id})"
                )

            # Check for each foreign key that the referenced object exists in the target state.
            for fk in fks:
                referenced_id = row[fk.attname]
                # If it is null, make sure it is allowed in the model definition, otherwise raise an error
                if referenced_id is None:
                    if not fk.null:
                        raise ProjectApplicationError(
                            f"Missing required reference {label}({object_id}).{fk.attname}"
                        )
                    continue

                # Get the label of the target model
                target_label = fk.remote_field.model._meta.label
                
                # If the target model is not in the state, or the referenced object is not in the target model, raise an error
                if (target_label not in state["models"] or
                        str(referenced_id) not in state["models"][target_label]):
                    raise ProjectApplicationError(
                        f"Invalid project reference {label}({object_id}).{fk.attname}"
                    )


def _blocked_early_deletes(
    before: ProjectState,
    removed: set[tuple[str, str]],
    model_classes: dict[str, type[models.Model]],
) -> set[tuple[str, str]]:
    """Find objects scheduled for deletion that are still referenced by retained objects."""
    blocked: set[tuple[str, str]] = set()

    # Iterate over all models and their foreign keys.
    for label, rows in before["models"].items():
        for fk in _foreign_keys(model_classes[label]):
            target_label = fk.remote_field.model._meta.label

            # Find deleted objects referenced by objects we are keeping.
            # Deleting them too early could cascade to retained objects.
            for object_id, row in rows.items():
                if (label, object_id) in removed or row[fk.attname] is None:
                    continue

                target = (target_label, str(row[fk.attname]))
                if target in removed:
                    blocked.add(target)

    return blocked


def _delete_records(
    keys: set[tuple[str, str]], # Model label and object ID pairs to delete
    before: ProjectState,
    model_classes: dict[str, type[models.Model]],
) -> None:
    """Delete referencing rows before their dependencies."""
    # Initialize a count of incoming references for each object to be deleted
    incoming = {key: 0 for key in keys}
    # Initialize a mapping of each object to the set of objects it references
    dependencies: dict[tuple[str, str], set[tuple[str, str]]] = {}

    # Create the ordering of deletions based on foreign key dependencies
    for key in keys:
        label, object_id = key
        row = before["models"][label][object_id]
        # Find objects referenced by this row that are also being deleted,
        # Excluding empty references and those that are set to null on delete.
        targets = {
            (fk.remote_field.model._meta.label, str(row[fk.attname]))
            for fk in _foreign_keys(model_classes[label])
            if row[fk.attname] is not None
            and fk.remote_field.on_delete is not models.SET_NULL
        } & keys
        targets.discard(key) # Ignore self-references to avoid cycles
        
        # Store the dependencies for this object and update the incoming reference counts for its targets
        dependencies[key] = targets
        for target in targets:
            incoming[target] += 1

    # Find objects that can be deleted now because nothing must be deleted before them.
    ready = []
    for key, count in incoming.items():
        if count == 0:
            heappush(ready, key)

    deleted = 0
    while ready:
        # Delete the next object that has no remaning dependencies
        key = heappop(ready)
        label, object_id = key
        model_classes[label]._base_manager.filter(pk=object_id).delete()
        deleted += 1
        
        # An object was deleted, update the counts of objects that were depending on it, so they may now be ready for deletion as well.
        for target in dependencies[key]:
            incoming[target] -= 1
            
            # No incoming references remain for this target, so it can now be deleted as well.
            if incoming[target] == 0:
                heappush(ready, target)

    if deleted != len(keys):
        raise ProjectApplicationError("Cyclic references prevent safe deletion")


def _create_records(
    created: dict[tuple[str, str], dict],
    before: ProjectState,
    model_classes: dict[str, type[models.Model]],
) -> list[tuple[str, str, dict]]:
    """Create all records. Records that get referenced by non-nullable foreign keys must be created first"""
    pending = dict(created)                         # Keep track of what we still need to create
    inserted = set()                                # Track successfully created records to avoid duplicates
    deferred: list[tuple[str, str, dict]] = []      # Keep track of records that have nullable foreign keys that need to be set after all non-nullable references are created
    existing = {                                    # Keep track of all existing records in the database to avoid creating duplicates
        (label, object_id)
        for label, rows in before["models"].items()
        for object_id in rows
    }

    while pending:
        progressed = False
        for key, row in sorted(list(pending.items())):
            label, object_id = key
            model = model_classes[label]
            ready = True
            values = dict(row)
            nullable = {}

            for fk in _foreign_keys(model):
                value = row[fk.attname]
                
                # No references to check for null values, so we can skip this foreign key
                if value is None:
                    continue

                target_key = (fk.remote_field.model._meta.label, str(value))
                # If the foreign key is nullable, we can defer setting it until later
                if fk.null:
                    values[fk.attname] = None
                    nullable[fk.attname] = value
                # If the foreign key is not nullable, we need to check if the target record has already been created or exists in the database
                # If not we can't create this record yet, so we mark it as not ready and break out of the loop
                elif target_key not in existing and target_key not in inserted:
                    ready = False
                    break
            
            # If the record is not ready to be created because it has non-nullable foreign keys that reference records that haven't been created yet,
            # we skip it for now and will try again in the next iteration of the loop
            if not ready:
                continue

            # Prevent creating if it already exists in the database.
            # This is a preventative check
            if model._base_manager.filter(pk=object_id).exists():
                raise ProjectApplicationError(
                    f"Cannot CREATE existing {label}({object_id})"
                )

            # Create the record
            model._base_manager.create(**values)
            
            # Save relations we temporarily set to null for later restoration
            if nullable:
                deferred.append((label, object_id, nullable))

            # Mark this record as created and remove it from the pending list so we don't try to create it again
            inserted.add(key)
            del pending[key]
            progressed = True

        if not progressed:
            raise ProjectApplicationError("Non-nullable foreign-key cycle in CREATE operations")

    return deferred


@transaction.atomic
def apply_project_changes(project_id: UUID | str, delta: ProjectDelta) -> None:
    """Apply one delta to an existing project"""
    try:
        project_uuid = UUID(str(project_id))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ProjectApplicationError("Invalid project UUID") from exc

    project = Project.objects.select_for_update().filter(pk=project_uuid).first()
    if project is None:
        raise ProjectApplicationError("Project does not exist")

    # Serialize the project which is currenlty in the database
    before = serialize_project(project.pk)
    try:
        after = apply_delta(before, delta)
    except (ProjectDeltaError, TypeError, KeyError) as exc:
        raise ProjectApplicationError(str(exc)) from exc

    models_by_label = _model_classes()
    _validate_target(after, project_uuid, models_by_label)

    created = {}
    removed = set()
    updated = {}
    for operation in delta:
        key = (operation["model"], operation["id"])
        if operation["operation"] == "CREATE":
            created[key] = operation["data"]
        elif operation["operation"] == "DELETE":
            removed.add(key)
        else:
            updated[key] = {
                field: change["new"]
                for field, change in operation["changes"].items()
            }

    if ("metadata.Project", str(project_uuid)) in removed or ("metadata.Project", str(project_uuid)) in created:
        raise ProjectApplicationError("Cannot create or delete the existing project")

    # Delete rows early if no retained object currently references them.
    early = removed - _blocked_early_deletes(before, removed, models_by_label)
    _delete_records(early, before, models_by_label)

    # Deferred contains the list of records that were created with temporarily null foreign keys that need to be restored after all non-nullable references have been created.
    deferred = _create_records(created, before, models_by_label)

    # All new non-null FK targets now exist. Update retained objects before
    # removing the old objects they may currently reference.
    for (label, object_id), fields in sorted(updated.items()):
        model = models_by_label[label]
        if model._base_manager.filter(pk=object_id).update(**fields) != 1:
            raise ProjectApplicationError(f"Cannot apply UPDATE: object {label}({object_id}) does not exist")

    # Delete any remaining rows that were not deleted early (blocked)
    _delete_records(removed - early, before, models_by_label)

    # Restore nullable references after all new rows exist.
    for label, object_id, fields in deferred:
        if models_by_label[label]._base_manager.filter(pk=object_id).update(**fields) != 1:
            raise ProjectApplicationError(f"Cannot restore deferred references: missing {label}({object_id})")

    # Validate the changed model instances once all references are in place.
    for label, object_id in sorted(set(created) | set(updated)):
        models_by_label[label]._base_manager.get(pk=object_id).full_clean()

    if serialize_project(project.pk) != after:
        raise ProjectApplicationError("Database state differs from the requested result")
