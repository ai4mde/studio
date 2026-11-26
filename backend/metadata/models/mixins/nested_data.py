from typing import Any, ClassVar

from django.db import models


class NestedDataMixin:
    nested_forward: ClassVar[dict[str, dict[str, Any]]] = {}
    nested_reverse: ClassVar[tuple[str, ...]] = ()

    @classmethod
    def prepare_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = dict(data)

        for name, defaults in cls.nested_forward.items():
            # allow caller to reference an existing related object instead of creating a new one
            if f"{name}_id" in data:
                continue

            values = data.get(name)

            if values is not None and not isinstance(values, dict):
                continue

            field = cls._meta.get_field(name)
            related_model = field.remote_field.model

            related = related_model(**{
                **defaults,
                **(values or {}),
            })
            related.full_clean()
            related.save()

            data[name] = related.pk
    
        return data

    @classmethod
    def extract_reverse_data(
        cls,
        data: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
        data = dict(data)
        nested = {}

        for name in cls.nested_reverse:
            if name in data:
                nested[name] = data.pop(name)

        return data, nested

    def prepare_update(self, data: dict[str, Any]) -> dict[str, Any]:
        data = dict(data)

        for name in self.nested_forward:
            values = data.pop(name, None)

            if values is None:
                continue

            related = getattr(self, name)

            for field, value in values.items():
                setattr(related, field, value)

            related.full_clean()
            related.save()

        return data

    def create_reverse_data(
        self,
        nested: dict[str, list[dict[str, Any]]],
    ) -> None:
        for name, items in nested.items():
            relation = self._meta.get_field(name)
            related_model = relation.related_model
            parent_field = relation.field.name

            for values in items:
                related = related_model(
                    **{
                        **values,
                        parent_field: self,
                    }
                )
                related.full_clean()
                related.save()