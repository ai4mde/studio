import uuid

from django.core.exceptions import (
    ValidationError,
    ValidationErrorMessageArg,
)
from django.db import models, transaction

from .core import Project, Classifier
from .types import RelationType, AggregatorType, OperatorType


class RelationManager(models.Manager['Relation']):
    @transaction.atomic
    def create_with_extensions(
        self,
        *,
        type: str,
        project: Project,
        source: Classifier,
        target: Classifier,
        extension_data: dict[type["RelationExtensionBase"], dict] | None = None,
    ) -> "Relation":
        extension_data = extension_data or {}

        # Create the base relation
        relation = self.create(
            type=type,
            project=project,
            source=source,
            target=target,
        )

        # Create any extensions for the relation
        # This will throw an error if any of the extensions are not allowed
        # and the transaction will be rolled back, preventing incomplete relations from being created
        for model, data in extension_data.items():
            model.objects.create(relation=relation, **data)

        # Make sure the extensions are valid for the relation type
        relation.validate_completeness()
        return relation


class Relation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    type = models.CharField(max_length=32, choices=RelationType.choices)

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="relations"
    )
    source = models.ForeignKey(
        Classifier, related_name="relations_from", on_delete=models.CASCADE
    )
    target = models.ForeignKey(
        Classifier, related_name="relations_to", on_delete=models.CASCADE
    )
    objects = RelationManager()

    class Meta:
        indexes = [
            models.Index(fields=["project", "type"]),
        ]
    
    # Filled in at the end of the file
    REQUIRED_EXTENSIONS: dict[str, tuple[type[models.Model], ...]] = {}

    def validate_completeness(self) -> None:
        errors: dict[str, ValidationErrorMessageArg] = {}
        required = self.REQUIRED_EXTENSIONS.get(self.type, ())

        for model in required:
            related_name = model.__name__.lower()
            if not hasattr(self, related_name):
                errors[related_name] = [
                    f"Missing required extension '{related_name}' for relation type '{self.type}'"
                ]

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Do not allow changing relation type after creation
        # This would allow for invalid combinations of relation and extensions
        if not self._state.adding:
            old_type = type(self).objects.only("type").get(pk=self.pk).type
            if old_type != self.type:
                raise ValidationError("Cannot change relation type after creation")
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.type} from {self.source} to {self.target}"


class RelationExtensionBase(models.Model):
    """
        Base class to extend specific relation types
        with additional attributes
    """
    relation = models.OneToOneField(
        Relation,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="%(class)s",
    )

    # Each extension subclass should define its own allowed relation types
    ALLOWED_RELATION_TYPES: tuple[str, ...] = ()

    class Meta:
        abstract = True
    
    def clean(self):
        super().clean()

        if not self.ALLOWED_RELATION_TYPES:
            raise RuntimeError(
                f"{self.__class__.__name__} must define ALLOWED_RELATION_TYPES"
            )
        
        if self.relation.type not in self.ALLOWED_RELATION_TYPES:
            raise ValidationError(
                f"{self.__class__.__name__} not allowed for relation type '{self.relation.type}'"
            )

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        required = self.relation.REQUIRED_EXTENSIONS.get(self.relation.type, ())

        if type(self) in required:
            raise ValidationError(
                f"{type(self).__name__} is required for relation type '{self.relation.type}' "
                "and cannot be deleted independently"
            )

        return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.relation}"


class RelationLabel(RelationExtensionBase):
    """
        Labels for association, composition, dependency
    """
    ALLOWED_RELATION_TYPES = (
        RelationType.ASSOCIATION,
        RelationType.COMPOSITION,
        RelationType.DEPENDENCY,
    )

    label = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self) -> str:
        return self.label or ""


class RelationEndpointLabels(RelationExtensionBase):
    """
        Endpoint labels for association and composition
    """
    ALLOWED_RELATION_TYPES = (
        RelationType.ASSOCIATION,
        RelationType.COMPOSITION,
    )

    source = models.CharField(max_length=255, blank=True, null=True)
    target = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self) -> str:
        return f"Source: {self.source}, Target: {self.target}"


class RelationMultiplicity(RelationExtensionBase):
    """
        Relation multiplicity for association and composition

        Examples:
            1       => lower=1, upper=1
            0..1    => lower=0, upper=1   
            0..*    => lower=0, upper=None
            1..*    => lower=1, upper=None       
    """
    ALLOWED_RELATION_TYPES = (
        RelationType.ASSOCIATION,
        RelationType.COMPOSITION,
    )

    source_lower = models.PositiveIntegerField()
    source_upper = models.PositiveIntegerField(null=True, blank=True) # Null means *

    target_lower = models.PositiveIntegerField()
    target_upper = models.PositiveIntegerField(null=True, blank=True) # Null means *

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
        if lower == upper:
            return str(lower)
        return f"{lower}..{upper}"
    
    @property
    def source_multiplicity(self) -> str:
        return self._format(self.source_lower, self.source_upper)
    
    @property
    def target_multiplicity(self) -> str:
        return self._format(self.target_lower, self.target_upper)
    
    def __str__(self) -> str:
        return f"{self.source_multiplicity} -> {self.target_multiplicity}"


class AssociationExtension(RelationExtensionBase):
    """
        Additional attributes for association relations
    """
    ALLOWED_RELATION_TYPES = (RelationType.ASSOCIATION,)
    derived = models.BooleanField(default=False)

    def __str__(self):
        return super().__str__() + f" [derived={self.derived}]"


class FlowExtension(RelationExtensionBase):
    """
        Additional attributes for control flow relations
    """
    ALLOWED_RELATION_TYPES = (
        RelationType.CONTROLFLOW,
        RelationType.OBJECTFLOW,
    )
    guard = models.CharField(max_length=255, default="", blank=True)
    weight = models.CharField(max_length=255, default="", blank=True)
    
    def __str__(self):
        return super().__str__() + f" [guard={self.guard}, weight={self.weight}]"


class Condition(RelationExtensionBase):
    ALLOWED_RELATION_TYPES = (RelationType.CONTROLFLOW,)
    else_condition = models.BooleanField(default=False)
    aggregator = models.CharField(max_length=5, blank=True, null=True, choices=AggregatorType.choices)
    operator = models.CharField(max_length=2, blank=True, null=True, choices=OperatorType.choices)
    value = models.CharField(max_length=255, blank=True, null=True)
    # TODO add relation to attribute (belongs to class classifier)

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


class InterfaceExtension(RelationExtensionBase):
    """
        Additional attributes for interface relations
    """
    ALLOWED_RELATION_TYPES = (RelationType.INTERFACE,)
    # TODO add relations to Interface classifier


Relation.REQUIRED_EXTENSIONS = {
    RelationType.INTERFACE: (InterfaceExtension,),
    RelationType.ASSOCIATION: (
        RelationLabel,
        RelationMultiplicity,
    ),
    RelationType.COMPOSITION: (
        RelationLabel,
        RelationMultiplicity,
    ),
}