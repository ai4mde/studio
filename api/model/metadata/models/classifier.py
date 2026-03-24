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
        extension_data: dict[type["ClassifierExtensionBase"], dict | list[dict]] | None = None,
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
            if isinstance(data, list):
                if not model.allows_multiple():
                    raise ValidationError(
                        f"{model.__name__} does not allow multiple instances, but a list was provided"
                    )
                for item in data:
                    model.objects.create(classifier=classifier, **item)
            else:
                model.objects.create(classifier=classifier, **data)

        classifier.validate_completeness()
        return classifier

    @transaction.atomic
    def add_extensions(
        self,
        extension_data: dict[type["ClassifierExtensionBase"], dict | list[dict]],
    ) -> None:
        """
            Add extensions to an existing classifier.
        """
        for model, data in extension_data.items():
            if isinstance(data, list):
                if not model.allows_multiple():
                    raise ValidationError(
                        f"{model.__name__} does not allow multiple instances, but a list was provided"
                    )
                for item in data:
                    model.objects.create(classifier=self, **item)
            else:
                model.objects.create(classifier=self, **data)


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

    REQUIRED_EXTENSIONS: dict[str, tuple[type["ClassifierExtensionBase"], ...]] = {}

    # Just a copy, make sure to understand this to check if the logic checks out
    def validate_completeness(self) -> None:
        errors: dict[str, ValidationErrorMessageArg] = {}
        required = self.REQUIRED_EXTENSIONS.get(self.type, ())
    
        for model in required:
            accessor_name = model.get_classifier_accessor_name()

            try:
                relation = getattr(self, accessor_name)
            except model.DoesNotExist:
                errors[accessor_name] = [
                    f"{model.__name__} extension is required for classifier type '{self.type}'"
                ]
                continue

            if hasattr(relation, "exists") and not relation.exists():
                errors[accessor_name] = [
                    f"At least one {model.__name__} extension is required for classifier type '{self.type}'"
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
        Base class for classifier extensions
        Subclasses define how they reference the classifier
    """
    # Each extension subclass should define its own allowed classifier types
    ALLOWED_CLASSIFIER_TYPES: tuple[str, ...] = ()

    class Meta:
        abstract = True

    def get_classifier(self) -> "Classifier":
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_classifier()"
        )

    @classmethod
    def get_classifier_accessor_name(cls) -> str:
        field = cls._meta.get_field("classifier")
        related_name = field.remote_field.related_name

        if related_name is None:
            raise RuntimeError(
                f"{cls.__name__} must define a related_name for the classifier field"
            )

        return related_name

    @classmethod
    def allows_multiple(cls) -> bool:
        field = cls._meta.get_field("classifier")
        return isinstance(field, models.ForeignKey)

    def clean(self):
        super().clean()

        if not self.ALLOWED_CLASSIFIER_TYPES:
            raise RuntimeError(
                f"{self.__class__.__name__} must define ALLOWED_CLASSIFIER_TYPES"
            )

        classifier = self.get_classifier()

        if classifier.type not in self.ALLOWED_CLASSIFIER_TYPES:
            raise ValidationError(
                f"{self.__class__.__name__} not allowed for classifier type '{classifier.type}'"
            )

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        classifier = self.get_classifier()
        required = classifier.REQUIRED_EXTENSIONS.get(classifier.type, ())

        if type(self) in required:
            raise ValidationError(
                f"{type(self).__name__} extension is required for classifier type '{classifier.type}' "
                "and cannot be deleted independently"
            )

        return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.get_classifier()}"


class SingleClassifierExtensionBase(ClassifierExtensionBase):
    classifier = models.OneToOneField(
        Classifier,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="%(class)s",
    )

    class Meta:
        abstract = True
    
    def get_classifier(self) -> "Classifier":
        return self.classifier


class MultiClassifierExtensionBase(ClassifierExtensionBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    classifier = models.ForeignKey(
        Classifier,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    class Meta:
        abstract = True

    def get_classifier(self) -> "Classifier":
        return self.classifier


class NamedElement(SingleClassifierExtensionBase):
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


class EnumLiteral(MultiClassifierExtensionBase):
    ALLOWED_CLASSIFIER_TYPES = (ClassifierType.ENUMERATION,)
    text = models.CharField(max_length=255)


class ClassExtension(SingleClassifierExtensionBase):
    ALLOWED_CLASSIFIER_TYPES = (ClassifierType.CLASS,)
    abstract = models.BooleanField(default=False)
    leaf = models.BooleanField(default=False)


class ClassAttribute(MultiClassifierExtensionBase):
    ALLOWED_CLASSIFIER_TYPES = (ClassifierType.CLASS,)

    name = models.CharField(max_length=255)
    attribute_type = models.CharField(max_length=32, choices=AttributeType.choices)
    derived=models.BooleanField(default=False)
    description = models.CharField(max_length=255, blank=True, null=True)

    enum = models.ForeignKey(
        Classifier,
        on_delete=models.CASCADE,
        related_name="enum_attributes",
        null=True,
        blank=True,
    )

    def clean(self):
        super().clean()

        if self.attribute_type == AttributeType.ENUM:
            if self.enum is None:
                raise ValidationError("Enum attribute must reference an enum classifier")
            if self.enum.type != ClassifierType.ENUMERATION:
                raise ValidationError("Enum attribute must reference an enumeration classifier")
        else:
            if self.enum is not None:
                raise ValidationError("Only enum attributes can reference an enum classifier")

# TODO Add classifierOperation what is this?
# Also where is a derived attribute stored?

# TODO add when component nodes are merged
# class SystemBoundaryExtension(SingleClassifierExtensionBase):
#     ALLOWED_CLASSIFIER_TYPES = (ClassifierType.SYSTEM_BOUNDARY,)
#     system = models.ForeignKey(
#         Classifier,
#         on_delete=models.CASCADE,
#         related_name="system_link",
#         limit_choices_to={"type": ClassifierType.SYSTEM},
#     )


class ActionExtension(SingleClassifierExtensionBase):
    ALLOWED_CLASSIFIER_TYPES = (ClassifierType.ACTION,)
    is_automatic = models.BooleanField(default=False)
    customCode = models.TextField(blank=True, null=True)


class ObjectExtension(SingleClassifierExtensionBase):
    ALLOWED_CLASSIFIER_TYPES = (ClassifierType.OBJECT,)
    state = models.CharField(max_length=255, blank=True, null=True)
    object = models.ForeignKey(
        Classifier,
        on_delete=models.CASCADE,
        related_name="objects",
        limit_choices_to={"type": ClassifierType.CLASS} # Does this work as I think it does? Check documentation
    )


class EventExtension(SingleClassifierExtensionBase):
    ALLOWED_CLASSIFIER_TYPES = (ClassifierType.EVENT,)
    signal = models.ForeignKey(
        Classifier,
        on_delete=models.CASCADE,
        related_name="events",
        limit_choices_to={"type": ClassifierType.SIGNAL}
    )


class InitialExtension(SingleClassifierExtensionBase):
    ALLOWED_CLASSIFIER_TYPES = (ClassifierType.INITIAL,)
    scheduled = models.BooleanField(default=False)
    schedule = models.CharField(max_length=255, blank=True, null=True)

    def clean(self):
        super().clean()

        if self.scheduled and not self.schedule:
            raise ValidationError("Scheduled initial nodes must have a schedule defined")
        if not self.scheduled and self.schedule:
            raise ValidationError("No schedule should be defined when the initial node is not scheduled")


class FinalExtension(SingleClassifierExtensionBase):
    ALLOWED_CLASSIFIER_TYPES = (ClassifierType.FINAL,)
    activity_scope = models.CharField(max_length=8, choices=ActivityScope.choices)


class SwimlaneExtension(SingleClassifierExtensionBase):
    component = models.ForeignKey(
        Classifier,
        on_delete=models.SET_NULL,
        related_name="swimlanes",
        # limit_choices_to={"type": ClassifierType.Component} # TODO REBASE TO DEVELOP!!!
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        Classifier,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    parent = models.ForeignKey(
        Classifier,
        on_delete=models.SET_NULL, # TODO Check this further perhaps some custom logic
        blank=True,
        null=True,
        limit_choices_to={"type": ClassifierType.SWIMLANE},
    )
