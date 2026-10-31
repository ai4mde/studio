import json
from uuid import UUID

from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q

from metadata.services.versioning.types import ModelRows, ProjectModels, ProjectState

from .constants import EXCLUDED_FIELDS, PROJECT_MODEL_SCOPES, SNAPSHOT_FORMAT, SNAPSHOT_SCHEMA_VERSION


class ProjectSerializationError(ValueError):
    """The project cannot be represented as a self-contained snapshot."""


def _project_uuid(project_id):
    try:
        return UUID(str(project_id))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ProjectSerializationError("Invalid project UUID") from exc


def _collect_rows(model, lookup_paths, project_id) -> ModelRows:
    """Retrieve all database rows for a model that are reachable from the given project ID."""
    scope_filter = Q()
    for path in lookup_paths:
        scope_filter |= Q(**{path: project_id})

    field_names = [
        field.attname for field in model._meta.concrete_fields
        if field.attname not in EXCLUDED_FIELDS.get(model._meta.label, ())
    ]
    return {
        str(row[model._meta.pk.attname]): row
        for row in (
            model._base_manager.filter(scope_filter)
            .order_by(model._meta.pk.attname)
            .values(*field_names)
        )
    }


def _verify_project_references(snapshot_models, models_by_label):
    """Check that all foreign keys point to objects included in the project snapshot."""
    model_keys = set(snapshot_models)
    for label, rows in snapshot_models.items():
        model = models_by_label[label]
        for field in model._meta.concrete_fields:
            if field.attname in EXCLUDED_FIELDS.get(label, ()):
                continue
            if not isinstance(field, (models.ForeignKey, models.OneToOneField)):
                continue
            target_label = field.remote_field.model._meta.label
            for pk, row in rows.items():
                foreign_pk = row[field.attname]
                if foreign_pk is None:
                    continue
                if target_label not in model_keys:
                    raise ProjectSerializationError(
                        f"{label}({pk}).{field.attname} references an "
                        f"unregistered model: {target_label}. Add its project "
                        "scope to PROJECT_MODEL_SCOPES or explicitly define "
                        "how to handle that external reference."
                    )
                if str(foreign_pk) not in snapshot_models[target_label]:
                    raise ProjectSerializationError(
                        f"{label}({pk}).{field.attname} references "
                        f"{target_label}({foreign_pk}) outside this project "
                        "or missing from its snapshot."
                    )


def serialize_project(project_id) -> ProjectState:
    """Read all data belonging to a project and return it as a JSON-serializable dictionary"""

    project_id = _project_uuid(project_id)
    project_model = apps.get_model("metadata", "Project")
    if not project_model._base_manager.filter(pk=project_id).exists():
        raise ProjectSerializationError(f"Project {project_id} does not exist")

    snapshot_models: ProjectModels = {}
    models_by_label = {}

    for label, paths in sorted(PROJECT_MODEL_SCOPES.items()):
        app_label, model_name = label.split(".", 1)
        model = apps.get_model(app_label, model_name)
        models_by_label[label] = model
        snapshot_models[label] = _collect_rows(model, paths, project_id)

    _verify_project_references(snapshot_models, models_by_label)
    snapshot = {
        "format": SNAPSHOT_FORMAT,
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "project_id": str(project_id),
        "models": snapshot_models,
    }

    try:
        return json.loads(
            json.dumps(
                snapshot,
                cls=DjangoJSONEncoder,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        )
    except (TypeError, ValueError) as exc:
        raise ProjectSerializationError(
            "Project contains a field value that cannot be encoded as JSON"
        ) from exc


def project_snapshot_json(project_id) -> str:
    """Return a stable JSON string, suitable for hashing or local inspection."""
    return json.dumps(serialize_project(project_id), sort_keys=True, separators=(",", ":"))
