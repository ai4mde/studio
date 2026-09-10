import uuid

from django.db import models

from metadata.models import System
from .types import DiagramType


class Diagram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    type = models.CharField(choices=DiagramType.choices, max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    system = models.ForeignKey(
        System, on_delete=models.CASCADE, related_name="diagrams"
    )