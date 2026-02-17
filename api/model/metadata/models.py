import uuid

from django.db import models
from metadata.utils import get_default_colors as get_default_colors_util


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField()


class System(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    color_palette = models.JSONField(default=dict, blank=True, null=True)
    settings = models.JSONField(default=dict, blank=True, null=True)

    def get_default_colors(self):
        """Get default classifier colors from system settings."""
        return get_default_colors_util(self.settings)


class Release(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    diagrams = models.JSONField()
    metadata = models.JSONField()
    interfaces = models.JSONField()
    release_notes = models.JSONField()


class Classifier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="classifiers", null=True, blank=True,
    )
    system = models.ForeignKey(
        System, on_delete=models.CASCADE, related_name="classifiers", null=True, blank=True,
    )
    data = models.JSONField()


class Interface(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    system = models.ForeignKey(System, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    actor = models.ForeignKey(Classifier, on_delete=models.CASCADE, null=True)
    data = models.JSONField(default=dict)


class Relation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    data = models.JSONField()
    system = models.ForeignKey(
        System, on_delete=models.CASCADE, related_name="relations"
    )
    source = models.ForeignKey(
        Classifier, related_name="relations_to", on_delete=models.CASCADE
    )
    target = models.ForeignKey(
        Classifier, related_name="relations_from", on_delete=models.CASCADE
    )
