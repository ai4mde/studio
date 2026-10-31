
    
  
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .general import Project


class ProjectVersion(models.Model):
    """An immutable version node; its delta is relative to its primary parent."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )
    merge_parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="merge_children",
    )
    delta = models.JSONField(default=list)
    checkpoint = models.JSONField(
        null=True,
        blank=True,
        default=None,
    )
    message = models.TextField(default="", blank=True)
    # Unlike auto_now_add, a default allows imported versions to retain their timestamps.
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def clean(self):
        super().clean()
        errors = {}
        if self.parent_id is not None:
            if self.parent_id == self.pk:
                errors["parent"] = "A version cannot be its own parent."
            elif self.project_id and ProjectVersion.objects.filter(
                pk=self.parent_id
            ).exclude(project_id=self.project_id).exists():
                errors["parent"] = "The parent must belong to the same project."
        if self.merge_parent_id is not None:
            if self.merge_parent_id == self.pk:
                errors["merge_parent"] = "A version cannot merge with itself."
            elif self.merge_parent_id == self.parent_id:
                errors["merge_parent"] = "The merge parent must differ from the primary parent."
            elif self.project_id and ProjectVersion.objects.filter(
                pk=self.merge_parent_id
            ).exclude(project_id=self.project_id).exists():
                errors["merge_parent"] = "The merge parent must belong to the same project."
        if errors:
            raise ValidationError(errors)


