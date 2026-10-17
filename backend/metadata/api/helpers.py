from typing import TypeVar

from django.db import models
from ninja import Schema


ModelType = TypeVar("ModelType", bound=models.Model)


def update_instance(
    instance: ModelType,
    payload: Schema,
) -> ModelType:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)

    instance.full_clean()
    instance.save()

    return instance


def create_instance(
    model: type[ModelType],
    payload: Schema,
) -> ModelType:
    instance = model(**payload.model_dump())
    instance.full_clean()
    instance.save()

    return instance