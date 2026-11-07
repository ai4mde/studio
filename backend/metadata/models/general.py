import uuid

from django.db import models


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField(default="", blank=True)
    current_release = models.ForeignKey(
        "Release",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_release_of",
    )


class System(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="systems",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(default="", blank=True)


class Release(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="releases",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    release_notes = models.JSONField(default=list)
    project_data = models.JSONField(default=dict)

    def __str__(self):
        return self.name