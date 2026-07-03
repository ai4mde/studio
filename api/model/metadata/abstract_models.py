from django.db import models, transaction

class ImportMixin(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def get_import_field_map(cls) -> dict[str, str]:
        return {
            field.name: (
                field.attname if isinstance(field, models.ForeignKey) else field.name
            )
            for field in cls._meta.fields
            if not field.primary_key
        }

    @classmethod
    def upsert_from_json(cls, data: dict):
        if "id" not in data:
            raise ValueError(f"Missing 'id' field for {cls.__name__}")

        field_map = cls.get_import_field_map()

        missing_fields = [field for field in field_map if field not in data]
        if missing_fields:
            raise ValueError(f"Missing fields for {cls.__name__}: {missing_fields}")

        values = {
            model_field: data[json_field]
            for json_field, model_field in field_map.items()
        }

        instance, created = cls.objects.get_or_create(
            id=data["id"],
            defaults=values,
        )

        if created:
            return instance, created

        changed_fields = []

        for field, new_value in values.items():
            if getattr(instance, field) != new_value:
                setattr(instance, field, new_value)
                changed_fields.append(field)

        if changed_fields:
            instance.save(update_fields=changed_fields)

        return instance, False

    @classmethod
    def import_from_json(cls, data: dict):
        instance, _ = cls.upsert_from_json(data)
        return instance

    @staticmethod
    def delete_missing(manager, ids):
        if ids is None:
            return
        manager.exclude(id__in=ids).delete()

