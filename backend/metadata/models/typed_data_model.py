from typing import Any, ClassVar, Type

from django.apps import apps
from django.db import models, transaction


class TypedDataModel(models.Model):
    data_type_enum: ClassVar[Type[Any]]
    data_model_aliases: ClassVar[dict[Any, str]] = {}
    data_parent_field: ClassVar[str]

    class Meta:
        abstract = True

    @property
    def data(self):
        data_type = getattr(self, "type", None)
        if data_type is None:
                raise ValueError(
                    "The TypedDataModel base class requires a 'type' field "
                    "to be defined in the subclass."
                )

        data_model = self.get_data_model(data_type)

        if data_model is None:
            return None

        field = data_model._meta.model_name

        if field is None:
            return None

        try:
            return getattr(self, field)
        except AttributeError:
            return None

    @classmethod
    def get_data_model(cls, data_type) -> Type[models.Model] | None:
        data_type = cls.data_type_enum(data_type)

        model_name = cls.data_model_aliases.get(
            data_type,
            "".join(
                part.title()
                for part in data_type.name.split("_")
            ),
        )

        try:
            return apps.get_model("metadata", model_name)
        except LookupError:
            return None

    @staticmethod
    def normalize_data(
        model: Type[models.Model],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        normalized: dict[str, Any] = {}

        for name, value in data.items():
            field = next(
                (
                    field
                    for field in model._meta.fields
                    if field.name == name or field.attname == name
                ),
                None,
            )

            if field is None:
                normalized[name] = value
            elif isinstance(field, models.ForeignKey):
                normalized[field.attname] = value
            else:
                normalized[field.name] = value

        return normalized

    @classmethod
    @transaction.atomic
    def create_typed(
        cls,
        *,
        data_type,
        data: dict[str, Any],
        **fields,
    ):
        data_type = cls.data_type_enum(data_type)

        instance = cls.objects.create(
            type=data_type,
            **fields,
        )

        data_model = cls.get_data_model(data_type)

        if data_model is not None:
            data = cls.normalize_data(
                data_model,
                data,
            )

            typed_data = data_model(
                **{
                    cls.data_parent_field: instance,
                    **data,
                }
            )

            typed_data.full_clean()
            typed_data.save()

        return instance

    @transaction.atomic
    def update(self, *, data):
        instance_data = self.data

        if instance_data is None:
            return self

        data = self.normalize_data(
            type(instance_data),
            data,
        )

        for field, value in data.items():
            setattr(instance_data, field, value)

        instance_data.full_clean()
        instance_data.save()

        return self
