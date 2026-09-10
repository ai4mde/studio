import uuid

from django.db import models

from metadata.models import Relation
from .diagram import Diagram

class Edge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    diagram = models.ForeignKey(
        Diagram,
        on_delete=models.CASCADE,
        related_name="edges",
    )
    relation = models.ForeignKey(
        Relation,
        on_delete=models.CASCADE,
        related_name="edges",
    )

    # Visual attributes, when not given the frontend will use the default values
    width = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    color = models.CharField(
        max_length=7,
        null=True,
        blank=True,
    )
    font = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    rounded = models.BooleanField(default=False)

    @property
    def source(self):
        return self.diagram.nodes.get(
            classifier=self.relation.source
        )

    @property
    def target(self):
        return self.diagram.nodes.get(
            classifier=self.relation.target
        )

    class Meta:
        # A relation can only be used once per diagram
        constraints = [
            models.UniqueConstraint(
                fields=["diagram", "relation"],
                name="unique_relation_per_diagram",
            )
        ]


class EdgeControlPoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    edge = models.ForeignKey(
        Edge,
        on_delete=models.CASCADE,
        related_name="control_points",
    )
    x_position = models.IntegerField()
    y_position = models.IntegerField()
    order = models.PositiveIntegerField()