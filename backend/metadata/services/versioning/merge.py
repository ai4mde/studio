from copy import deepcopy
from uuid import UUID

from django.core import serializers
from django.core.exceptions import ValidationError
from django.db import models, transaction

from diagram.models import Diagram, Edge, Node
from metadata.models import Classifier, Relation, Release
from metadata.services.versioning.restore import _snapshot_ids_and_references
from metadata.services.versioning.snapshot import (
    EXCLUDED_FIELDS,
    PROJECT_MODELS,
    SCHEMA_VERSION,
)
from metadata.services.versioning.utils import validate_snapshot


class MergeConflictError(Exception):
    """Conflicts that are encountered when merging two snapshots, which can be resolved by the user."""

    def __init__(
        self,
        code: str,
        message: str,
        resolution: str,
        details: dict | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.resolution = resolution
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict:
        """A dictionary to return to the frontend"""
        return {
            "code": self.code,
            "message": self.message,
            "resolution": self.resolution,
            "details": self.details,
        }


def _object_key(item: dict) -> tuple[str, UUID]:
    """Key to compare two snapshot records"""
    try:
        pk = UUID(item["pk"])
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValidationError(
            f"Invalid UUID for {item['model']}: {item['pk']!r}"
        ) from exc
    return item["model"], pk


def _index_objects(snapshot: dict) -> dict[tuple[str, UUID], dict]:
    """Index snapshot records by (model label, UUID)"""
    indexed = {}
    for item in snapshot["objects"]:
        key = _object_key(item)
        if key in indexed:
            raise ValidationError(f"Duplicate snapshot record: {key}.")
        indexed[key] = item
    return indexed


def _record_for(
    model: type[models.Model], value: object,
    indexed: dict[tuple[str, UUID], dict],
) -> dict | None:
    """Get a record from the snapshots"""
    if value is None:
        return None
    try:
        return indexed.get((model._meta.label_lower, UUID(str(value))))
    except (TypeError, ValueError, AttributeError):
        return None


def _display_name(
    model: type[models.Model], value: object,
    indexed: dict[tuple[str, UUID], dict],
) -> str:
    """Get a name from the snapshots, without querying the live database."""
    item = _record_for(model, value, indexed)

    # Fallback in the case it is not found
    if item is None:
        return str(model._meta.verbose_name)

    # If the model contains a human-readable name, use it.
    fields = item["fields"]
    for name in ("name", "title", "label"):
        if isinstance(fields.get(name), str) and fields[name].strip():
            return fields[name].strip()

    # Base classifiers have their names in a separate type-specific record.
    if model is Classifier:
        for child_model in PROJECT_MODELS:
            # If this is a Data field classifier, the name is there
            pk_field = child_model._meta.pk
            if (
                isinstance(pk_field, models.OneToOneField)
                and pk_field.remote_field.model is Classifier
            ):
                child = _record_for(child_model, value, indexed)
                if child is not None and child["fields"].get("name"):
                    return str(child["fields"]["name"])
        return str(fields.get("type") or "classifier")

    if model is Relation:
        source = _display_name(Classifier, fields.get("source"), indexed)
        target = _display_name(Classifier, fields.get("target"), indexed)
        return f"{source} → {target}"

    return str(model._meta.verbose_name)


def _check_missing_references(
    objects: list[dict], indexed: dict[tuple[str, UUID], dict],
) -> None:
    """Give users a concrete explanation when merging leaves a broken link."""
    by_label = {model._meta.label_lower: model for model in PROJECT_MODELS}

    for item in objects:
        model = by_label[item["model"]]
        for field in model._meta.concrete_fields:
            if field.name in EXCLUDED_FIELDS.get(model, set()):
                continue
            if not isinstance(field, models.ForeignKey):
                continue

            value = item["pk"] if field.primary_key else item["fields"].get(field.name)
            if value is None:
                continue
            target = field.remote_field.model
            try:
                target_key = (target._meta.label_lower, UUID(str(value)))
            except (TypeError, ValueError, AttributeError):
                # Invalid UUIDs are rejected by the existing restore validator.
                continue
            if target_key in indexed:
                continue

            source_name = _display_name(model, item["pk"], indexed)
            source_type = str(model._meta.verbose_name)
            target_type = str(target._meta.verbose_name)
            raise MergeConflictError(
                code="MISSING_REFERENCE",
                message=(
                    f"The {source_type} '{source_name}' refers to a {target_type} "
                    "that is missing from the merged version."
                ),
                resolution=(
                    "Open the affected version, restore the missing object or "
                    "remove the broken reference, save a new version, and retry."
                ),
                details={
                    "source_model": model._meta.label_lower,
                    "source_id": str(item["pk"]),
                    "field": field.name,
                    "target_model": target._meta.label_lower,
                    "target_id": str(value),
                },
            )


def _check_simple_uniqueness(objects: list[dict]) -> None:
    """Reject duplicate values in unconditional field-based uniqueness rules."""
    by_model: dict[type[models.Model], list[dict]] = {
        model: [] for model in PROJECT_MODELS
    }
    labels = {model._meta.label_lower: model for model in PROJECT_MODELS}
    for item in objects:
        by_model[labels[item["model"]]].append(item)
    indexed = {_object_key(item): item for item in objects}

    for model, records in by_model.items():
        unique_sets: set[tuple[str, ...]] = set()
        unique_sets.update(
            (field.name,)
            for field in model._meta.concrete_fields
            if field.unique and not field.primary_key
        )
        unique_sets.update(tuple(fields) for fields in model._meta.unique_together)
        unique_sets.update(
            tuple(constraint.fields)
            for constraint in model._meta.constraints
            if isinstance(constraint, models.UniqueConstraint)
            and constraint.fields
            and constraint.condition is None
            and not constraint.expressions
        )

        for field_names in unique_sets:
            seen: dict[tuple[str, ...], dict] = {}
            for item in records:
                values = []
                for field_name in field_names:
                    field = model._meta.get_field(field_name)
                    value = (
                        item["pk"] if field.primary_key
                        else item["fields"].get(field.name)
                    )
                    if isinstance(field, models.ForeignKey) and value is not None:
                        value = str(UUID(str(value)))
                    values.append(value)

                # PostgreSQL allows multiple NULLs in standard unique constraints.
                if any(value is None for value in values):
                    continue
                unique_value = tuple(str(value) for value in values)
                prior = seen.get(unique_value)
                if prior is None or _object_key(prior) == _object_key(item):
                    seen[unique_value] = item
                    continue

                if model is Node and set(field_names) == {"diagram", "classifier"}:
                    diagram = _display_name(Diagram, item["fields"]["diagram"], indexed)
                    classifier = _display_name(
                        Classifier, item["fields"]["classifier"], indexed
                    )
                    code = "DUPLICATE_DIAGRAM_NODE"
                    message = (
                        f"The diagram '{diagram}' contains two nodes for "
                        f"the classifier '{classifier}'."
                    )
                    resolution = (
                        "Remove one of the duplicate nodes from either version, "
                        "save a new version, and try merging again."
                    )
                elif model is Edge and set(field_names) == {"diagram", "relation"}:
                    diagram = _display_name(Diagram, item["fields"]["diagram"], indexed)
                    relation = _display_name(
                        Relation, item["fields"]["relation"], indexed
                    )
                    code = "DUPLICATE_DIAGRAM_EDGE"
                    message = (
                        f"The diagram '{diagram}' contains two edges for "
                        f"the relationship '{relation}'."
                    )
                    resolution = (
                        "Remove one of the duplicate edges from either version, "
                        "save a new version, and try merging again."
                    )
                else:
                    shared_values = []
                    for field_name, value in zip(field_names, values):
                        field = model._meta.get_field(field_name)
                        field_label = str(field.verbose_name)
                        if isinstance(field, models.ForeignKey):
                            value_label = _display_name(
                                field.remote_field.model, value, indexed
                            )
                        else:
                            value_label = str(value)
                        shared_values.append(f"{field_label} '{value_label}'")
                    code = "DUPLICATE_UNIQUE_VALUE"
                    message = (
                        f"Two {model._meta.verbose_name} entries conflict "
                        f"because both use {', '.join(shared_values)}."
                    )
                    resolution = (
                        "Change or remove one of the conflicting entries in "
                        "either version, save a new version, and retry the merge."
                    )

                raise MergeConflictError(
                    code=code,
                    message=message,
                    resolution=resolution,
                    details={
                        "model": model._meta.label_lower,
                        "object_ids": [str(prior["pk"]), str(item["pk"])],
                        "fields": list(field_names),
                        "values": [str(value) for value in values],
                    },
                )


def _check_typed_records(objects: list[dict]) -> None:
    """Reject typed details inconsistent with their base classifier/relation."""
    indexed = {_object_key(item): item for item in objects}
    for base_model in (Classifier, Relation):
        children = [
            model for model in PROJECT_MODELS
            if isinstance(model._meta.pk, models.OneToOneField)
            and model._meta.pk.remote_field.model is base_model
        ]
        base_label = base_model._meta.label_lower
        for child_model in children:
            expected_type = child_model._meta.model_name
            suffix = "classifier" if base_model is Classifier else "relation"
            if expected_type.endswith(suffix):
                expected_type = expected_type[:-len(suffix)]

            for item in objects:
                if item["model"] != child_model._meta.label_lower:
                    continue
                key = _object_key(item)
                base = indexed[(base_label, key[1])]
                actual_type = base["fields"].get("type")
                if actual_type == expected_type:
                    continue

                readable_name = _display_name(base_model, item["pk"], indexed)
                entity_type = "classifier" if base_model is Classifier else "relationship"
                raise MergeConflictError(
                    code="INCOMPATIBLE_OBJECT_TYPE",
                    message=(
                        f"The {entity_type} '{readable_name}' has incompatible "
                        f"types in the merged version: '{actual_type}' and "
                        f"'{expected_type}'."
                    ),
                    resolution=(
                        "Make the object's type consistent in both versions, "
                        "save a new version, and try merging again."
                    ),
                    details={
                        "model": base_label,
                        "object_id": str(item["pk"]),
                        "typed_model": child_model._meta.label_lower,
                        "actual_type": actual_type,
                        "expected_type": expected_type,
                    },
                )


def merge_snapshots(ground_truth: dict, incoming: dict) -> dict:
    """Union of snapshots, with the ground-truth record winning any overlap."""
    project_id = ground_truth["project_id"]

    merged = _index_objects(incoming)
    merged.update(_index_objects(ground_truth))

    model_order = {
        model._meta.label_lower: index
        for index, model in enumerate(PROJECT_MODELS)
    }
    objects = [
        deepcopy(merged[key])
        for key in sorted(merged, key=lambda k: (model_order[k[0]], k[1]))
    ]
    result = {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "objects": objects,
    }

    validate_snapshot(result, project_id)
    indexed = {_object_key(item): item for item in objects}
    _check_missing_references(objects, indexed)
    _snapshot_ids_and_references(objects)
    _check_simple_uniqueness(objects)
    _check_typed_records(objects)
    try:
        list(serializers.deserialize("python", objects))
    except Exception as exc:
        raise ValidationError(
            f"Merged snapshot cannot be deserialized: {exc}"
        ) from exc

    return result


@transaction.atomic
def merge_releases(
    ground_truth_id: UUID | str,
    incoming_id: UUID | str,
    name: str,
    description: str | None = None,
    release_notes: list[str] | None = None,
) -> Release:
    """Store a new release without changing the project or source releases."""
    ground_truth = Release.objects.get(pk=ground_truth_id)
    incoming = Release.objects.get(pk=incoming_id)

    if ground_truth.project_id != incoming.project_id:
        raise MergeConflictError(
            code="DIFFERENT_PROJECTS",
            message="These versions belong to different projects and cannot be merged.",
            resolution="Select two versions from the same project.",
        )

    snapshot = merge_snapshots(ground_truth.project_data, incoming.project_data)
    return Release.objects.create(
        project_id=ground_truth.project_id,
        name=name,
        description=description or "",
        release_notes=release_notes or [],
        project_data=snapshot,
    )
