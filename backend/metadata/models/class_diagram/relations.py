import uuid

from django.db import models

from ..relation import RelationDataModel
from ..mixins.nested_data import NestedDataMixin


class Multiplicity(models.Model):
    """
        Relation multiplicity for association and composition

        Examples:
            1       => lower=1, upper=1
            0..1    => lower=0, upper=1   
            0..*    => lower=0, upper=None
            1..*    => lower=1, upper=None       
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    source_lower = models.PositiveIntegerField()
    source_upper = models.PositiveIntegerField(blank=True, null=True)

    target_lower = models.PositiveIntegerField()
    target_upper = models.PositiveIntegerField(blank=True, null=True)


class EndpointLabel(models.Model):
    """
        Endpoint labels for relations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    source = models.CharField(max_length=255, blank=True, default="")
    target = models.CharField(max_length=255, blank=True, default="")


MULTIPLICITY_AND_LABELS = {
    "multiplicity": {
        "source_lower": 1,
        "source_upper": 1,
        "target_lower": 1,
        "target_upper": 1,
    },
    "labels": {
        "source": "",
        "target": "",
    },
}



class Association(NestedDataMixin, RelationDataModel):
    nested_forward = MULTIPLICITY_AND_LABELS

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



class Composition(NestedDataMixin, RelationDataModel):
    nested_forward = MULTIPLICITY_AND_LABELS
    
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
