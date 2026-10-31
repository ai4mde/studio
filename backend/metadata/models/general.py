import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField(default="", blank=True)
    current_version = models.ForeignKey(
        "metadata.ProjectVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_projects",
    )

    def clean(self):
        super().clean()
        if (
            self.current_version_id is not None
            and self.current_version.project_id != self.pk
        ):
            raise ValidationError(
                {"current_version": "The active version must belong to this project."}
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

