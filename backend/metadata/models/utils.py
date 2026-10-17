from django.core.exceptions import ValidationError


class ValidationMixin:
    def require_if(self, condition, field, message=None):
        if condition and not getattr(self, field):
            raise ValidationError({
                field: message or f"{field} is required."
            })

    def forbid_if(self, condition, field, message=None):
        if condition and getattr(self, field) not in (None, "", False):
            raise ValidationError({
                field: message or f"{field} must be empty."
            })

    def mutually_exclusive(self, *fields):
        active = [
            field
            for field in fields
            if getattr(self, field) not in (None, "", False)
        ]

        if len(active) > 1:
            raise ValidationError(
                f"Only one of {', '.join(fields)} may be set."
            )

    def require_one_of(self, *fields):
        if not any(
            getattr(self, field) not in (None, "", False)
            for field in fields
        ):
            raise ValidationError(
                f"One of {', '.join(fields)} is required."
            )

    def require_value_in(self, field, allowed_values, message=None):
        value = getattr(self, field)

        if value is not None and value not in allowed_values:
            raise ValidationError({
                field: message or f"{field} has an invalid value."
            })

    def require_related_type(
        self,
        field,
        allowed_types,
        type_field="type",
        message=None,
    ):
        related = getattr(self, field)

        if related is None:
            return

        if getattr(related, type_field) not in allowed_types:
            raise ValidationError({
                field: message or f"{field} has an invalid type."
            })

    def forbid_fields_if(self, condition, *fields):
        if not condition:
            return

        for field in fields:
            self.forbid_if(condition, field)
