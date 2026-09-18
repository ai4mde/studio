from django.db import models

from .classifier import Classifier
from .general import System
from .types import RelationType


class Relation(models.Model):
    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name="relations",
    )
    source = models.ForeignKey(
        Classifier,
        related_name="relations_to",
        on_delete=models.CASCADE,
    )
    target = models.ForeignKey(
        Classifier,
        related_name="relations_from",
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        max_length=32,
        choices=RelationType.choices,
    )

    @property
    def data(self):
        # When creating a new RelationType make sure the reverse relation related name is the same as the RelationType value
        # This will allow the Relation to get the correct data model for the relation type
        # If this name is already taken, you can add a new entry to the RELATION_DATA_FIELDS dictionary below to map the RelationType to the correct related name
        RELATION_DATA_FIELDS = {
            RelationType.INTERFACE: "interfacerelation",
        }
        field = RELATION_DATA_FIELDS.get(self.type) or self.type

        try:
            return getattr(self, field)
        except AttributeError:
            return None


# Inherit from this class when making a new node type. Make sure to use the same class anme as defined in RelationType
class RelationDataModel(models.Model):
    relation = models.OneToOneField(
        Relation,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="%(class)s",
    )

    class Meta:
        abstract = True