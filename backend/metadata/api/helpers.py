from typing import Any, TypeVar

from django.db import models
from ninja import Schema


ModelType = TypeVar("ModelType", bound=models.Model)


def to_model_fields(
    model: type[models.Model],
    data: dict[str, Any],
) -> dict[str, Any]:
    """
        ModelSchema dumps foreign keys under the field name
        (e.g. "system") with a plain id as the value. Django
        expects an instance there, or the id under the column
        name ("system_id"), so map those to the column name.
    """
    fields = {field.name: field for field in model._meta.fields}
    out: dict[str, Any] = {}

    for name, value in data.items():
        field = fields.get(name)

        if field is not None and field.is_relation:
            out[field.attname] = value
        else:
            out[name] = value

    return out


def update_instance(
    instance: ModelType,
    payload: Schema,
) -> ModelType:
    data = to_model_fields(
        type(instance),
        payload.model_dump(exclude_unset=True),
    )

    for field, value in data.items():
        setattr(instance, field, value)

    instance.full_clean()
    instance.save()

    return instance


def create_instance(
    model: type[ModelType],
    payload: Schema,
) -> ModelType:
    instance = model(**to_model_fields(model, payload.model_dump()))
    instance.full_clean()
    instance.save()

    return instance