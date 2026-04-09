from django.db import models
from django.core.exceptions import ValidationError


class TypedForeignKey(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        if "allowed_types" not in kwargs:
            raise TypeError("TypedForeignKey requires 'allowed_types'")

        self.allowed_types = kwargs.pop("allowed_types")
        super().__init__(*args, **kwargs)

    def clean(self, value, model_instance):
        value = super().clean(value, model_instance)

        if value is None:
            return value

        # Resolve to instance if needed
        if not hasattr(value, "type"):
            value = self.remote_field.model.objects.get(pk=value)

        value_type = getattr(value, "type", None)

        if value_type is None:
            raise ValidationError(
                f"{self.name} must reference an object with a 'type' attribute"
            )

        if value_type not in self.allowed_types:
            raise ValidationError(
                f"{self.name} must reference type(s) {self.allowed_types}, got '{value_type}'"
            )

        return value