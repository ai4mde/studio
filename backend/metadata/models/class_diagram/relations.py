from django.db import models

from ..relation import RelationDataModel


class Multiplicity(models.Model):
    """
        Relation multiplicity for association and composition

        Examples:
            1       => lower=1, upper=1
            0..1    => lower=0, upper=1   
            0..*    => lower=0, upper=None
            1..*    => lower=1, upper=None       
    """
    source_lower = models.PositiveIntegerField()
    source_upper = models.PositiveIntegerField(blank=True, null=True)

    target_lower = models.PositiveIntegerField()
    target_upper = models.PositiveIntegerField(blank=True, null=True)


class EndpointLabel(models.Model):
    """
        Endpoint labels for relations
    """
    source = models.CharField(max_length=255, blank=True, default="")
    target = models.CharField(max_length=255, blank=True, default="")


class Association(RelationDataModel):
    derived = models.BooleanField(default=False)
    label = models.CharField(max_length=255, blank=True, default="")
    multiplicity = models.OneToOneField(
        Multiplicity,
        on_delete=models.CASCADE,
        related_name="association",
    )
    labels = models.OneToOneField(
        EndpointLabel,
        on_delete=models.CASCADE,
        related_name="association",
    )


class Composition(RelationDataModel):
    label = models.CharField(max_length=255, blank=True, default="")
    multiplicity = models.OneToOneField(
        Multiplicity,
        on_delete=models.CASCADE,
        related_name="composition",
    )
    labels = models.OneToOneField(
        EndpointLabel,
        on_delete=models.CASCADE,
        related_name="composition",
    )


class Dependency(RelationDataModel):
    label = models.CharField(max_length=255, blank=True, default="")
