import uuid

from django.db import models

class Interface(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    system = models.ForeignKey(
        "System",
        on_delete=models.CASCADE,
        related_name="interfaces",
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    actor = models.ForeignKey(
        "Actor",
        on_delete=models.CASCADE,
    )