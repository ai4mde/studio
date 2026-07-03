from typing import Optional
import uuid

from django.db import models, transaction

from metadata.abstract_models import ImportMixin

class Project(ImportMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField()


class System(ImportMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="systems",
    )
    name = models.CharField(max_length=255)
    description = models.TextField()


class Release(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    project_data = models.JSONField(default=dict) # Contains the entire json blob of the project, systems, classifiers, relations etc.
    release_notes = models.JSONField()


class Classifier(ImportMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    # Project attribute is redundant and should be removed as it can be inferred from the system, so try to avoid using it
    # So it is easier to remove in the future
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="classifiers", null=True, blank=True,
    )
    system = models.ForeignKey(
        System, on_delete=models.CASCADE, related_name="classifiers", null=True, blank=True,
    )
    # To track the original system for classifiers that are moved between systems
    # For instance when you import a system that references a classifier from a system that does not exists
    # We can add the classifier to the current system but keep track of where it came from so that if the original system is imported later we can move it back
    original_system_id = models.UUIDField(null=True, blank=True)
    data = models.JSONField()

    @classmethod
    def move_to_original_system(cls, project: Optional[Project] = None):
        queryset = cls.objects.filter(original_system_id__isnull=False)

        if project is not None:
            queryset = queryset.filter(project=project)

        existing_system_ids = set(
            System.objects.values_list("id", flat=True)
            if project is None
            else project.systems.values_list("id", flat=True)
        )

        for classifier in queryset:
            if classifier.system_id == classifier.original_system_id:
                classifier.original_system_id = None
                classifier.save(update_fields=["original_system_id"])
                continue

            if classifier.original_system_id in existing_system_ids:
                classifier.system_id = classifier.original_system_id
                classifier.original_system_id = None
                classifier.save(update_fields=["system_id", "original_system_id"])
        

class Interface(ImportMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name="interfaces",
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    actor = models.ForeignKey(Classifier, on_delete=models.CASCADE, null=True)
    data = models.JSONField(default=dict)


class Relation(ImportMixin):
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
