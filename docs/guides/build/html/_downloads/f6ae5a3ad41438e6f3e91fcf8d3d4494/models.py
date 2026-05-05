import uuid

from django.db import models
from metadata.models import System


class Prototype(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField()
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    metadata = models.JSONField(default=dict)
    database_hash = models.CharField(max_length=256, null=True)