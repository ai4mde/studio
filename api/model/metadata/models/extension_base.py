import uuid

from django.core.exceptions import ValidationError, ValidationErrorMessageArg
from django.db import models, transaction


class TypeExtensionManager(models.Manager):
    @transaction.atomic
    def create_with_extensions(
        self,
        *,
        type: str,
        extension_data: dict[type["ExtensionBase"], dict | list[dict]] | None = None,
        **extra_fields,
    ):
        extension_data = extension_data or {}

        instance = self.create(type=type, **extra_fields)

        for model, data in extension_data.items():
            owner_field_name = model.OWNER_FIELD_NAME
            if owner_field_name is None:
                raise RuntimeError(
                    f"{model.__name__} must define OWNER_FIELD_NAME"
                )

            if isinstance(data, list):
                if not model.allows_multiple():
                    raise ValidationError(
                        f"{model.__name__} does not allow multiple instances but a list was provided"
                    )
                for item in data:
                    model.objects.create(**{owner_field_name: instance}, **item)
            else:
                model.objects.create(**{owner_field_name: instance}, **data)
    
        instance.validate_completeness()
        return instance
        

class TypeExtensionModel(models.Model):
    """
    Abstract base for models like Classifier or Relation.
    Subclasses must define a Django 'type' field.
    """
    type: str

    objects = TypeExtensionManager()

    REQUIRED_EXTENSIONS: dict[str, tuple[type['ExtensionBase'], ...]] = {}

    class Meta:
        abstract = True

    def validate_completeness(self) -> None:
        errors: dict[str, ValidationErrorMessageArg] = {}
        required = self.REQUIRED_EXTENSIONS.get(self.type, ())

        for model in required:
            accessor_name = model.get_owner_accessor_name()

            if model.allows_multiple():
                relation = getattr(self, accessor_name)
                if not relation.exists():
                    errors[accessor_name] = [
                        f"At least one {model.__name__} extension is required for type '{self.type}'"
                    ]
            else:
                try:
                    getattr(self, accessor_name)
                except model.DoesNotExist:
                    errors[accessor_name] = [
                        f"A {model.__name__} extension is required for type '{self.type}'"
                    ]
            
        if errors:
            raise ValidationError(errors)

    @transaction.atomic
    def add_extensions(
        self,
        extension_data: dict[type["ExtensionBase"], dict | list[dict]],
    ) -> None:
        for model, data in extension_data.items():
            owner_field_name = model.OWNER_FIELD_NAME
            if owner_field_name is None:
                raise RuntimeError(
                    f"{model.__name__} must define OWNER_FIELD_NAME"
                )

            if isinstance(data, list):
                if not model.allows_multiple():
                    raise ValidationError(
                        f"{model.__name__} does not allow multiple instances but a list was provided"
                    )
                for item in data:
                    model.objects.create(**{owner_field_name: self}, **item)
            else:
                model.objects.create(**{owner_field_name: self}, **data)
        self.validate_completeness()

    def save(self, *args, **kwargs):
        # Do not allow changing classifier type after creation
        # This would allow for invalid combinations of classifier and extensions
        if not self._state.adding:
            cls = self.__class__
            old_type = cls.objects.only("type").get(pk=self.pk).type
            if old_type != self.type:
                raise ValidationError("Cannot change type after creation")
        return super().save(*args, **kwargs)


class ExtensionBase(models.Model):
    """
    Generic base class for extensions attached to a TypeExtensionModel.
    
    Subclasses must define:
    - OWNER_FIELD_NAME: the field pointing to the owner model.
    - ALLOWED_TYPES: which owner.type values this extension is valid for.
    """
    OWNER_FIELD_NAME: str | None = None
    ALLOWED_TYPES: tuple[str, ...] = ()

    class Meta:
        abstract = True

    def get_owner(self) -> "TypeExtensionModel":
        if self.OWNER_FIELD_NAME is None:
            raise RuntimeError(
                f"{self.__class__.__name__} must define OWNER_FIELD_NAME"
            )
        return getattr(self, self.OWNER_FIELD_NAME)

    @classmethod
    def get_owner_field(cls) -> models.Field:
        if cls.OWNER_FIELD_NAME is None:
            raise RuntimeError(
                f"{cls.__name__} must define OWNER_FIELD_NAME"
            )
        return cls._meta.get_field(cls.OWNER_FIELD_NAME)

    @classmethod
    def get_owner_accessor_name(cls) -> str:
        field = cls.get_owner_field()
        related_name = field.remote_field.related_name

        if related_name is None:
            raise RuntimeError(
                f"{cls.__name__}'s OWNER_FIELD_NAME must have a related_name defined"
            )

        return related_name

    @classmethod
    def allows_multiple(cls) -> bool:
        return isinstance(cls.get_owner_field(), models.ForeignKey)

    def clean(self) -> None:
        super().clean()

        if not self.ALLOWED_TYPES:
            raise RuntimeError(
                f"{self.__class__.__name__} must define ALLOWED_TYPES"
            )
        owner = self.get_owner()

        if owner.type not in self.ALLOWED_TYPES:
            raise ValidationError(
                f"{self.__class__.__name__} not allowed for type '{owner.type}'"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        owner = self.get_owner()
        required_extensions = owner.REQUIRED_EXTENSIONS.get(owner.type, ())
    
        if type(self) in required_extensions:
            raise ValidationError(
                f"{type(self).__name__} extension is required for type '{owner.type}'"
                "and cannot be deleted independently"
            )

        return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return str(self.get_owner())