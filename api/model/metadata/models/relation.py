import uuid

from django.db import models

from .classifier import Classifier
from .core import Project
from .extension_base import ExtensionBase, TypeExtensionModel
from .types import RelationType, AggregatorType, OperatorType


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
    # TODO add relation to attribute (belongs to class classifier) ALSO ADD A WAY TO VALIDATE THIS

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

    # @property
    # def parsed_value(self):
    # TODO Parse value based on the attribute type (e.g. int, string, bool)

    def __str__(self) -> str:
        # TODO Extend with attribute information when available
        if self.else_condition:
            return "Else"
        if self.aggregator and self.operator and self.value:
            return f"{self.aggregator} {self.operator} {self.value}"
        return "Condition"


class InterfaceExtension(SingleRelationExtensionBase):
    ALLOWED_TYPES = (RelationType.INTERFACE,)
    # TODO add relations to interface classifier
