
from uuid import UUID

from django.core.exceptions import ValidationError

from metadata.models import Project
from metadata.services.versioning.snapshot import (
    PROJECT_MODELS,
    SCHEMA_VERSION,
)

def validate_snapshot(snapshot: dict, project_id: UUID | str) -> None:
    if not isinstance(snapshot, dict):
        raise ValidationError("Snapshot must be a dictionary.")

    if snapshot.get("schema_version") != SCHEMA_VERSION:
        raise ValidationError("Unsupported snapshot schema version.")

    if snapshot.get("project_id") != str(project_id):
        raise ValidationError("Snapshot belongs to a different project.")

    objects = snapshot.get("objects")
    if not isinstance(objects, list):
        raise ValidationError("Snapshot objects must be a list.")

    allowed_models = {
        model._meta.label_lower for model in PROJECT_MODELS
    }

    seen = set()

    for obj in objects:
        if (
            not isinstance(obj, dict)
            or obj.get("model") not in allowed_models
            or not isinstance(obj.get("pk"), str)
            or not isinstance(obj.get("fields"), dict)
        ):
            raise ValidationError(f"Invalid snapshot object: {obj}")

        key = (obj["model"], obj["pk"])

        if key in seen:
            raise ValidationError(f"Duplicate snapshot object: {key}")

        seen.add(key)

    project_objects = [
        obj for obj in objects
        if obj["model"] == Project._meta.label_lower
    ]

    if len(project_objects) != 1:
        raise ValidationError("Snapshot must contain exactly one project.")

    if project_objects[0]["pk"] != str(project_id):
        raise ValidationError("Snapshot project ID does not match.")
