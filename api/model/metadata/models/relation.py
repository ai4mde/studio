import uuid
from datetime import datetime
from typing import Any

from django.db import models
from django.core.exceptions import ValidationError

from .classifier import ClassAttribute, Classifier
from .core import Project
from .extension_base import ExtensionBase, TypeExtensionModel
from .types import RelationType, AggregatorType, OperatorType, AttributeType, ClassifierType
from .fields import TypedForeignKey


class Relation(TypeExtensionModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    type = models.CharField(max_length=32, choices=Relation.choices)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="relations",
    )
    source = models.ForeignKey(
        Classifier,
        related_name="relations_from",
        on_delete=models.CASCADE,
    )
    target = models.ForeignKey(
        Classifier,
        related_name="relations_to",
        on_delete=models.CASCADE,
    )

    REQUIRED_EXTENSIONS: dict[str, tuple[type["ExtensionBase"], ...]] = {}

    class Meta:
        indexes = [
            models.Index(fields=["project", "type"]),
        ]

    def __str__(self) -> str:
        return f"{self.source} from {self.source} to {self.target}"


class RelationExtensionBase(ExtensionBase):
    OWNER_FIELD_NAME = "relation"

    class Meta:
        abstract = True


class SingleRelationExtensionBase(RelationExtensionBase):
    relation = models.OneToOneField(
        Relation,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="%(class)s"
    )

    class Meta:
        abstract = True


class RelationLabel(SingleRelationExtensionBase):
    ALLOWED_TYPES = (
        RelationType.ASSOCIATION,
        RelationType.COMPOSITION,
        RelationType.DEPENDENCY,
    )

    label = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self) -> str:
        return self.label or ""


class RelationEndpointLabels(RelationExtensionBase):
    ALLOWED_TYPES = (
        RelationType.ASSOCIATION,
        RelationType.COMPOSITION,
    )

    source = models.CharField(max_length=255, blank=True, null=True)
    target = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self) -> str:
        return f"Source: {self.source or ''}, Target: {self.target or ''}"


class RelationMultiplicity(RelationExtensionBase):
    """
        Relation multiplicity for association and composition

        Examples:
            1       => lower=1, upper=1
            0..1    => lower=0, upper=1   
            0..*    => lower=0, upper=None
            1..*    => lower=1, upper=None       
    """
    ALLOWED_TYPES = (
        RelationType.ASSOCIATION,
        RelationType.COMPOSITION,
    )

    source_lower = models.PositiveIntegerField()
    source_upper = models.PositiveIntegerField(blank=True, null=True)

    target_lower = models.PositiveIntegerField()
    target_upper = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(source_upper__isnull=True) |
                    models.Q(source_upper__gte=models.F("source_lower"))
                ),
                name="relmult_source_upper_gte_lower_or_null",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(target_upper__isnull=True) |
                    models.Q(target_upper__gte=models.F("target_lower"))
                ),
                name="relmult_target_upper_gte_lower_or_null",
            ),
        ]

    @staticmethod
    def _format(lower: int, upper: int | None) -> str:
        if upper is None:
            return f"{lower}..*"
        elif lower == upper:
            return str(lower)
        return f"{lower}..{upper}"

    @property
    def source_multiplicity(self) -> str:
        return self._format(self.source_lower, self.source_upper)

    @property
    def target_multiplicity(self) -> str:
        return self._format(self.target_lower, self.target_upper)

    def __str__(self) -> str:
        return f"Source: {self.source_multiplicity}, Target: {self.target_multiplicity}"


class AssociationExtension(SingleRelationExtensionBase):
    ALLOWED_TYPES = (RelationType.ASSOCIATION,)
    derived = models.BooleanField(default=False)

    def __str__(self) -> str:
        return super().__str__() + f", [derived={self.derived}]"


class FlowExtension(SingleRelationExtensionBase):
    ALLOWED_TYPES = (
        RelationType.CONTROLFLOW,
        RelationType.OBJECTFLOW,
    )
    guard = models.CharField(max_length=255, default="", blank=True)
    weight = models.CharField(max_length=255, default="", blank=True)

    def __str__(self) -> str:
                return super().__str__() + f" [guard={self.guard}, weight={self.weight}]" 


class Condition(SingleRelationExtensionBase):
    ALLOWED_TYPES = (RelationType.CONTROLFLOW,)
    else_condition = models.BooleanField(default=False)
    aggregator = models.CharField(max_length=5, blank=True, null=True, choices=AggregatorType.choices)
    operator = models.CharField(max_length=2, blank=True, null=True, choices=OperatorType.choices)
    value = models.CharField(max_length=255, blank=True, null=True)
    
    attribute = models.ForeignKey(
        ClassAttribute,
        on_delete=models.CASCADE,
        related_name="conditions",
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(else_condition=False) |
                    (
                        models.Q(aggregator__isnull=True) &
                        models.Q(operator__isnull=True) &
                        models.Q(value__isnull=True)
                    )
                ),
                name="condition_else_has_no_expr",
            ),
        ]

    @property
    def parsed_value(self) -> Any:
        if self.else_condition:
            return None

        if self.attribute is None or self.value is None:
            return None

        attr_type = self.attribute.attribute_type

        try:
            # ENUM not yet supported.
            # IN the future we should let the user select a literal when they select an ENUM
            if attr_type == AttributeType.STRING or attr_type == AttributeType.ENUM:
                return self.value

            if attr_type == AttributeType.INT:
                return int(self.value)

            if attr_type == AttributeType.BOOL:
                # assume valid input: "true" / "false"
                return self.value.lower() == "true"

            if attr_type == AttributeType.DATETIME:
                return datetime.fromisoformat(self.value)

        except ValueError as e:
            raise ValidationError(
                f"Could not parse value '{self.value}' for type '{attr_type}': {e}"
            )

        raise ValidationError(f"Unsupported attribute type '{attr_type}'")

    def __str__(self) -> str:
        if self.else_condition:
            return "Else"
        if self.attribute:
            return f"{self.attribute.name} {self.aggregator} {self.operator} {self.parsed_value}"
        return "Condition"


class InterfaceExtension(SingleRelationExtensionBase):
    ALLOWED_TYPES = (RelationType.INTERFACE,)
    provided = TypedForeignKey( # type: ignore[call-arg]
        Classifier,
        on_delete=models.CASCADE,
        related_name="provided_interface_relations",
        null=True,
        blank=True,
        allowed_types=(ClassifierType.INTERFACE,),
        limit_choices_to={"type": ClassifierType.INTERFACE}
    )
    required = TypedForeignKey( # type: ignore[call-arg]
        Classifier,
        on_delete=models.CASCADE,
        related_name="required_interface_relations",
        null=True,
        blank=True,
        allowed_types=(ClassifierType.INTERFACE,),
        limit_choices_to={"type": ClassifierType.INTERFACE}
    )
