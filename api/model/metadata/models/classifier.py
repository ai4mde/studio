import uuid

from django.db import models
from django.core.exceptions import ValidationError


from .core import Project
from .extension_base import ExtensionBase, TypeExtensionModel
from .types import ActivityScope, ClassifierType, AttributeType
from .fields import PythonCodeField, TypedForeignKey


class Classifier(TypeExtensionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    type = models.CharField(max_length=32, choices=ClassifierType.choices)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="classifiers",
    )

    # Fill this after extensions have been created (at the end of file)
    REQUIRED_EXTENSIONS: dict[str, tuple[type["ExtensionBase"], ...]] = {}

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
        return "control" if self.type in control_nodes else self.type

    def __str__(self) -> str:
        return f"{self.type} in {self.project}"

class ClassifierExtensionBase(ExtensionBase):
    OWNER_FIELD_NAME = "classifier"

    class Meta:
        abstract = True


class SingleClassifierExtensionBase(ClassifierExtensionBase):
    classifier = models.OneToOneField(
        Classifier,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="%(class)s",
    )

    class Meta:
        abstract = True


class MultiClassifierExtensionBase(ClassifierExtensionBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    classifier = models.ForeignKey(
        Classifier,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    class Meta:
        abstract = True


class NamedElement(SingleClassifierExtensionBase):
    ALLOWED_TYPES = (
        ClassifierType.CLASS,
        ClassifierType.ENUMERATION,
        ClassifierType.INTERFACE,
        ClassifierType.SIGNAL,
        ClassifierType.SYSTEM_BOUNDARY,
        ClassifierType.USECASE,
        ClassifierType.ACTOR,
        ClassifierType.ACTION,
        ClassifierType.EVENT,
        ClassifierType.COMPONENT,
        ClassifierType.CONTAINER,
        ClassifierType.SYSTEM,
    )


    name = models.CharField(max_length=255)
    namespace = models.CharField(max_length=255, blank=True, null=True)


class EnumLiteral(MultiClassifierExtensionBase):
    ALLOWED_TYPES = (ClassifierType.ENUMERATION,)
    text = models.CharField(max_length=255)


class ClassExtension(SingleClassifierExtensionBase):
    ALLOWED_TYPES = (ClassifierType.CLASS,)
    abstract = models.BooleanField(default=False)
    leaf = models.BooleanField(default=False)


class ClassAttribute(MultiClassifierExtensionBase):
    ALLOWED_TYPES = (ClassifierType.CLASS,)

    name = models.CharField(max_length=255)
    attribute_type = models.CharField(max_length=32, choices=AttributeType.choices)
    derived = models.BooleanField(default=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    body = PythonCodeField(blank=True, null=True)

    enum = TypedForeignKey( # type: ignore[call-arg]
        Classifier,
        on_delete=models.CASCADE,
        related_name="enum_attributes",
        null=True,
        blank=True,
        allowed_types=(ClassifierType.ENUMERATION,),
        limit_choices_to={"type": ClassifierType.ENUMERATION}
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


class ClassMethod(MultiClassifierExtensionBase):
    ALLOWED_TYPES = (ClassifierType.CLASS,)

    name = models.CharField(max_length=255)
    body = PythonCodeField(blank=True, null=True)


class SystemBoundaryExtension(SingleClassifierExtensionBase):
    ALLOWED_TYPES = (ClassifierType.SYSTEM_BOUNDARY,)
    system = TypedForeignKey( # type: ignore[call-arg]
        Classifier,
        on_delete=models.CASCADE,
        related_name="boundaries",
        limit_choices_to={"type": ClassifierType.SYSTEM},
        allowed_types=(ClassifierType.SYSTEM,),
    )


class ActionExtension(SingleClassifierExtensionBase):
    ALLOWED_TYPES = (ClassifierType.ACTION,)
    is_automatic = models.BooleanField(default=False)
    custom_code = PythonCodeField(blank=True, null=True)


class ObjectExtension(SingleClassifierExtensionBase):
    ALLOWED_TYPES = (ClassifierType.OBJECT,)
    state = models.CharField(max_length=255, blank=True, null=True)
    # rel to avoid shadowing object variable
    rel_object = TypedForeignKey( # type: ignore[call-arg]
        Classifier,
        on_delete=models.CASCADE,
        related_name="objects",
        allowed_types=(ClassifierType.CLASS,),
        limit_choices_to={"type": ClassifierType.CLASS}
    )


class EventExtension(SingleClassifierExtensionBase):
    ALLOWED_TYPES = (ClassifierType.EVENT,)
    signal = TypedForeignKey( # type: ignore[call-arg] (Django doesn't understand the addition of allowed types to the field, but it works as intended)
        Classifier,
        on_delete=models.CASCADE,
        related_name="events",
        allowed_types=(ClassifierType.SIGNAL,),
        limit_choices_to={"type": ClassifierType.SIGNAL}
    )


class InitialExtension(SingleClassifierExtensionBase):
    ALLOWED_TYPES = (ClassifierType.INITIAL,)
    scheduled = models.BooleanField(default=False)
    schedule = models.CharField(max_length=255, blank=True, null=True)

    def clean(self):
        super().clean()

        if self.scheduled and not self.schedule:
            raise ValidationError("Scheduled initial nodes must have a schedule defined")
        if not self.scheduled and self.schedule:
            raise ValidationError("No schedule should be defined when the initial node is not scheduled")


class FinalExtension(SingleClassifierExtensionBase):
    ALLOWED_TYPES = (ClassifierType.FINAL,)
    activity_scope = models.CharField(max_length=8, choices=ActivityScope.choices)


class SwimlaneExtension(SingleClassifierExtensionBase):
    ALLOWED_TYPES = (ClassifierType.SWIMLANE,)

    component = TypedForeignKey( # type: ignore[call-arg]
        Classifier,
        on_delete=models.SET_NULL,
        related_name="component_swimlanes",
        allowed_types=(ClassifierType.COMPONENT,),
        limit_choices_to={"type": ClassifierType.COMPONENT},
        null=True,
        blank=True,
    )
    actor = TypedForeignKey( # type: ignore[call-arg]
        Classifier,
        on_delete=models.CASCADE,
        related_name="actor_swimlanes",
        allowed_types=(ClassifierType.ACTOR,),
        limit_choices_to={"type": ClassifierType.ACTOR},
        null=True,
        blank=True,
    )
    parent = TypedForeignKey( # type: ignore[call-arg]
        Classifier,
        on_delete=models.PROTECT, 
        related_name="child_swimlanes",
        allowed_types=(ClassifierType.SWIMLANE,),
        limit_choices_to={"type": ClassifierType.SWIMLANE},
        blank=True,
        null=True,
    )

    @property
    def is_leaf(self) -> bool:
        return not self.classifier.child_swimlanes.exists()

    def clean(self):
        super().clean()

        if self.is_leaf:
            if self.actor is None:
                raise ValidationError("Leaf swimlanes must have an actor")
            if self.component is not None:
                raise ValidationError("Leaf swimlanes cannot have a component")
        else:
            if self.actor is not None:
                raise ValidationError("Non-leaf swimlanes cannot have an actor")

