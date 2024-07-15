import uuid

from django.db import models
from metadata.models import System


class Prototype(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField()
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    running = models.BooleanField(default=False)
    container_id = models.CharField(max_length=255, blank=True, null=True)
    container_url = models.URLField(blank=True, null=True)
    container_port = models.IntegerField(blank=True, null=True)