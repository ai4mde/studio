import uuid

from django.core.exceptions import ValidationError, ValidationErrorMessageArg
from django.db import models, transaction

from .core import Project
from .types import (
    ClassifierType,
    ActivityScope,
    AttributeType,
)


class ClassifierManager(models.Manager['Classifier']):
    @transaction.atomic
    def create_with_extensions(
        self,
        *,
        type: str,
        project: Project,
        extension_data: dict[type["ClassifierExtensionBase"], dict] | None = None,
    ):
        extension_data = extension_data or {}

        # Create the base classifier
        classifier = self.create(
            type=type,
            project=project,
        )

        # Create any extensions for the classifier
        # This will throw an error if any of the extensions are not allowed
        # and the transaction will be rolled back, preventing incomplete classifiers from being created
        for model, data in extension_data.items():
            model.objects.create(classifier=classifier, **data)

        return classifier


class Classifier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    type = models.CharField(max_length=32, choices=ClassifierType.choices)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="classifiers",
    )
    objects = ClassifierManager()
    
    class Meta:
        indexes = [
            models.Index(fields=["project", "type"]),
        ]

    @property
    def role(self) -> str:
        control_nodes = (
            ClassifierType.MERGE,
            ClassifierType.DECISION,
            ClassifierType.JOIN,
            ClassifierType.FORK,
            ClassifierType.INITIAL,
            ClassifierType.FINAL,
        )
        return (
            'control'
            if self.type in control_nodes
            else self.type
        )

    REQUIRED_EXTENSIONS: dict[str, tuple[type[models.Model], ...]] = {}

    def validate_completeness(self) -> None:
        errors: dict[str, ValidationErrorMessageArg] = {}
        required = self.REQUIRED_EXTENSIONS.get(self.type, ())
    
        for model in required:
            related_name = model.__name__.lower()
            if not hasattr(self, related_name):
                errors[related_name] = [
                    f"{model.__name__} extension is required for {self.type} classifiers"
                ]

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Do not allow changing classifier type after creation
        # This would allow for invalid combinations of classifier and extensions
        if not self._state.adding:
            old_type = type(self).objects.only("type").get(pk=self.pk).type
            if old_type != self.type:
                raise ValidationError("Cannot change classifier type after creation")
        return super().save(*args, **kwargs)
    
    def __str__(self) -> str:
        return f"{self.type} in {self.project}"


class ClassifierExtensionBase(models.Model):
    """
        Base class to extend specific classifier types 
        with additional attributes 
    """
    classifier = models.OneToOneField(
        Classifier,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="%(class)s",
    )

    # Each extension subclass should define its own allowed classifier types
    ALLOWED_CLASSIFIER_TYPES: tuple[str, ...] = ()

    class Meta:
        abstract = True

    def clean(self):
        super().clean()

        if not self.ALLOWED_CLASSIFIER_TYPES:
            raise RuntimeError(
                f"{self.__class__.__name__} must define ALLOWED_CLASSIFIER_TYPES"
            )

        if self.classifier.type not in self.ALLOWED_CLASSIFIER_TYPES:
            raise ValidationError(
                f"{self.__class__.__name__} not allowed for classifier type '{self.classifier.type}'"
            )

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        required = self.classifier.REQUIRED_EXTENSIONS.get(self.classifier.type, ())

        if type(self) in required:
            raise ValidationError(
                f"{type(self).__name__} extension is required for classifier type '{self.classifier.type}' "
                "and cannot be deleted independently"
            )

        return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.classifier}"


class NamedElement(ClassifierExtensionBase):
    ALLOWED_CLASSIFIER_TYPES = (
        ClassifierType.CLASS,
        ClassifierType.ENUMERATION,
        ClassifierType.INTERFACE,
        ClassifierType.SIGNAL,
        ClassifierType.SYSTEM_BOUNDARY,
        ClassifierType.USECASE,
        ClassifierType.ACTOR,
        ClassifierType.ACTION,
        ClassifierType.EVENT,
        # TODO add component nodes when merged
    )


    name = models.CharField(max_length=255)
    namespace = models.CharField(max_length=255, blank=True, null=True)

# Extension, however there can be multiple?
# class Literals()


class ClassExtension(ClassifierExtensionBase):
    ALLOWED_CLASSIFIER_TYPES = (ClassifierType.CLASS,)
    abstract = models.BooleanField(default=False)
    leaf = models.BooleanField(default=False)


class ClassAttribute(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=32, choices=AttributeType.choices)
    derived = models.BooleanField(default=False)
    description = models.CharField(max_length=255, blank=True, null=True)

    class_instance = models.ForeignKey(
        ClassExtension, related_name="attributes", on_delete=models.CASCADE,
    )
    # Relation to Enum, however, enum doesn't have any actual attributes
    # Only relations to literals, however, i dont want to make a 
    # Extension which is only referenced by the literals
    # Directly putting the literals to the relation also doesn't work
    # As it contains a one to one relation
    # enum = models.ForeignKey(

    # )