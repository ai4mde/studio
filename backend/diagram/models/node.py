import uuid

from django.db import models

from metadata.models import Classifier
from .diagram import Diagram


class Node(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    diagram = models.ForeignKey(
        Diagram,
        on_delete=models.CASCADE,
        related_name="nodes",
    )
    classifier = models.ForeignKey(
        Classifier,
        on_delete=models.CASCADE,
        related_name="nodes",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    x_position = models.IntegerField(default=0)
    y_position = models.IntegerField(default=0)

    # Visual attributes, when not given the frontend will use the default values
    height = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
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
    
    class Meta:
        # A classifier can only be used once per diagram
        constraints = [
            models.UniqueConstraint(
                fields=["diagram", "classifier"],
                name="unique_classifier_per_diagram",
            )
        ]
