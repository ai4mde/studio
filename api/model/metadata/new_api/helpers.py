from django.db import models
from ninja import Schema


def update_instance(
    instance: models.Model,
    payload: Schema,
) -> models.Model:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)

    instance.full_clean()
    instance.save()

    return instance