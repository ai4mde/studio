from typing import Any, Optional
import uuid

from django.db import models, transaction
from django.db.models import Max


class ImportMixin(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def get_import_field_map(cls) -> dict[str, str]:
        return {
            field.name: (
                field.attname if isinstance(field, models.ForeignKey) else field.name
            )
            for field in cls._meta.fields
            if not field.primary_key
        }

    @classmethod
    def upsert_from_json(cls, data: dict):
        if "id" not in data:
            raise ValueError(f"Missing 'id' field for {cls.__name__}")

        field_map = cls.get_import_field_map()
        
        missing_fields = [field for field in field_map if field not in data]
        if missing_fields:
            raise ValueError(f"Missing fields for {cls.__name__}: {missing_fields}")

        values = {
            model_field: data[json_field]
            for json_field, model_field in field_map.items()
        }


        instance, created = cls.objects.get_or_create(
            id=data["id"],
            defaults=values,
        )

        if created:
            return instance, created
        
        changed_fields = []

        for field, new_value in values.items():
            if getattr(instance, field) != new_value:
                setattr(instance, field, new_value)
                changed_fields.append(field)

        if changed_fields:
            instance.save(update_fields=changed_fields)

        return instance, False
    
    @classmethod
    def import_from_json(cls, data: dict):
        instance, _ = cls.upsert_from_json(data)
        return instance

    @staticmethod
    def delete_missing(manager, ids):
        if ids is None:
            return
        manager.exclude(id__in=ids).delete()


class Project(ImportMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField()

    @classmethod
    @transaction.atomic
    def import_from_json(cls, data):
        # Expects the data to be validated using the ImportProject schema
        # So all required fields should be present and valid
        project, _ = cls.upsert_from_json(data)

        system_ids = []
        for system_data in data["systems"]:
            imported_system_data = system_data.copy()
            imported_system_data["project"] = str(project.id)
            System.import_from_json(
                imported_system_data,
                project=project,
            )
            system_ids.append(imported_system_data["id"])

        cls.delete_missing(project.systems, system_ids)

        return project
    
    @transaction.atomic
    def import_systems_from_json(self, data:  list[dict]):
        for system_data in data:
            imported_system_data = system_data.copy()
            imported_system_data["project"] = self.id # Associate the imported system with the current project
            System.import_from_json(
                imported_system_data,
                project=self, # Associate the imported classifiers with the current project. This shouldn't be necessary as the classifier should not have a project field (should be inferred from the system)
            )
        # After importing all systems, check if there are any classifiers that can be moved back to their original system
        Classifier.move_to_original_system(self)


class System(ImportMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="systems",
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    current_revision = models.ForeignKey(
        "SystemRevision",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    @classmethod
    def get_import_field_map(cls) -> dict[str, str]:
        field_map = super().get_import_field_map()
        field_map.pop("current_revision", None)
        return field_map

    @classmethod
    @transaction.atomic
    def import_from_json(cls, data, project: Optional[Project] = None):
        from diagram.models import Diagram # Prevent circular import
        system, _ = cls.upsert_from_json(data)

        classifier_ids = []
        for classifier_data in data['classifiers']:
            classifier_data_copy = classifier_data.copy() # To avoid mutating the original data which might cause unintended side effects
            if project:
                classifier_data_copy['project'] = project.id
            Classifier.import_from_json(classifier_data_copy)
            classifier_ids.append(classifier_data_copy['id'])

        for classifier_data in data.get('imported_classifiers', []):
            # For now just add the classifier to the current system and add the original_system_id
            # This is because the system it belongs to might not be importe yet
            # Or it might be imported after this system is imported
            # After all systems are imported we can move all classifiers back to the original system if it exists
            imported_classifier_data = classifier_data.copy() # To avoid mutating the original data which might cause unintended side effects
            if project:
                imported_classifier_data['project'] = project.id
            imported_classifier_data['original_system_id'] = (
                classifier_data.get('original_system_id') or imported_classifier_data.get('system')
            )
            imported_classifier_data['system'] = system.id
            Classifier.import_from_json(imported_classifier_data)
            classifier_ids.append(imported_classifier_data['id'])
        cls.delete_missing(system.classifiers, classifier_ids)

        relation_ids = []
        for relation_data in data['relations']:
            Relation.import_from_json(relation_data)
            relation_ids.append(relation_data['id'])
        cls.delete_missing(system.relations, relation_ids)

        diagram_ids = []
        for diagram_data in data['diagrams']:
            Diagram.import_from_json(diagram_data)
            diagram_ids.append(diagram_data['id'])
        cls.delete_missing(system.diagrams, diagram_ids)

        interface_ids = []
        for interface_data in data['interfaces']:
            Interface.import_from_json(interface_data)
            interface_ids.append(interface_data['id'])
        cls.delete_missing(system.interfaces, interface_ids)

        return system


class SystemRevision(models.Model):
    REVISION_ORIGIN_BASELINE = "baseline"
    REVISION_ORIGIN_HUMAN_SYNC = "human_sync"
    REVISION_ORIGIN_AI_REFINEMENT = "ai_refinement"
    REVISION_ORIGIN_CHOICES = [
        (REVISION_ORIGIN_BASELINE, "Baseline"),
        (REVISION_ORIGIN_HUMAN_SYNC, "Human Sync"),
        (REVISION_ORIGIN_AI_REFINEMENT, "AI Refinement"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name="revisions",
    )
    revision_index = models.IntegerField()
    parent_revision = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="child_revisions",
    )
    process_text = models.TextField()
    pipeline_profile = models.CharField(max_length=64)
    topology_artifact = models.JSONField(null=True, blank=True)
    semantic_sketch_plan = models.JSONField(null=True, blank=True)
    activity_graph = models.JSONField()
    ai4mde_export = models.JSONField()
    refinement_trace = models.JSONField(null=True, blank=True)
    refinement_instruction = models.TextField(null=True, blank=True)
    revision_origin = models.CharField(
        max_length=32,
        choices=REVISION_ORIGIN_CHOICES,
        default=REVISION_ORIGIN_BASELINE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["revision_index", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["system", "revision_index"],
                name="unique_revision_index_per_system",
            ),
        ]


class SystemGenerationArtifacts(models.Model):
    system = models.OneToOneField(
        System,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="generation_artifacts",
    )
    process_text = models.TextField()
    pipeline_profile = models.CharField(max_length=64)
    topology_artifact = models.JSONField()
    semantic_sketch_plan = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


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


def persist_semantic_generation_artifacts(
    *,
    system_id: str,
    process_text: str,
    pipeline_profile: str,
    topology_artifact: dict[str, Any],
    semantic_sketch_plan: dict[str, Any],
) -> SystemGenerationArtifacts:
    system = System.objects.get(pk=system_id)
    artifacts, _ = SystemGenerationArtifacts.objects.update_or_create(
        system=system,
        defaults={
            "process_text": process_text,
            "pipeline_profile": pipeline_profile,
            "topology_artifact": topology_artifact,
            "semantic_sketch_plan": semantic_sketch_plan,
        },
    )
    return artifacts


def create_system_revision(
    *,
    system_id: str,
    process_text: str,
    pipeline_profile: str,
    activity_graph: dict[str, Any],
    ai4mde_export: dict[str, Any] | list[dict[str, Any]],
    topology_artifact: Optional[dict[str, Any]] = None,
    semantic_sketch_plan: Optional[dict[str, Any]] = None,
    refinement_trace: Optional[dict[str, Any]] = None,
    refinement_instruction: Optional[str] = None,
    revision_origin: str = SystemRevision.REVISION_ORIGIN_BASELINE,
    parent_revision_id: Optional[str] = None,
    set_as_current: bool = True,
) -> SystemRevision:
    system = System.objects.select_related("current_revision").get(pk=system_id)
    max_index = system.revisions.aggregate(max_revision_index=Max("revision_index"))["max_revision_index"]
    revision = SystemRevision.objects.create(
        system=system,
        revision_index=0 if max_index is None else int(max_index) + 1,
        parent_revision_id=parent_revision_id,
        process_text=process_text,
        pipeline_profile=pipeline_profile,
        topology_artifact=topology_artifact,
        semantic_sketch_plan=semantic_sketch_plan,
        activity_graph=activity_graph,
        ai4mde_export=ai4mde_export,
        refinement_trace=refinement_trace,
        refinement_instruction=refinement_instruction,
        revision_origin=revision_origin,
    )
    if set_as_current:
        system.current_revision = revision
        system.save(update_fields=["current_revision"])
    return revision


def _backfill_revision_from_legacy_sidecar(
    system: System,
    *,
    fallback_process_text: Optional[str] = None,
    fallback_pipeline_profile: Optional[str] = None,
) -> Optional[SystemRevision]:
    if system.current_revision_id:
        return system.current_revision
    if system.revisions.exists():
        revision = system.revisions.order_by("-revision_index", "-created_at").first()
        system.current_revision = revision
        system.save(update_fields=["current_revision"])
        return revision

    legacy_artifacts = SystemGenerationArtifacts.objects.filter(system=system).first()
    if legacy_artifacts is None and not fallback_process_text:
        return None

    from metadata.api.schemas import ExportSingleSystem
    from llm.refinement_generator import _get_clean_model

    ai4mde_system = ExportSingleSystem.model_validate(system).model_dump(mode="json")
    ai4mde_export = [ai4mde_system]
    clean_graph = _get_clean_model(ai4mde_export)
    revision = SystemRevision.objects.create(
        system=system,
        revision_index=0,
        parent_revision=None,
        process_text=(legacy_artifacts.process_text if legacy_artifacts else str(fallback_process_text)),
        pipeline_profile=(
            legacy_artifacts.pipeline_profile
            if legacy_artifacts
            else str(fallback_pipeline_profile or "stable")
        ),
        topology_artifact=legacy_artifacts.topology_artifact if legacy_artifacts else None,
        semantic_sketch_plan=legacy_artifacts.semantic_sketch_plan if legacy_artifacts else None,
        activity_graph=clean_graph,
        ai4mde_export=ai4mde_export,
        refinement_trace=None,
        refinement_instruction=None,
        revision_origin=SystemRevision.REVISION_ORIGIN_BASELINE,
    )
    system.current_revision = revision
    system.save(update_fields=["current_revision"])
    return revision


def get_current_revision(
    system_id: str,
    *,
    fallback_process_text: Optional[str] = None,
    fallback_pipeline_profile: Optional[str] = None,
) -> Optional[SystemRevision]:
    system = System.objects.select_related("current_revision").get(pk=system_id)
    if system.current_revision_id:
        return system.current_revision
    return _backfill_revision_from_legacy_sidecar(
        system,
        fallback_process_text=fallback_process_text,
        fallback_pipeline_profile=fallback_pipeline_profile,
    )


def list_system_revisions(system_id: str) -> list[SystemRevision]:
    get_current_revision(system_id)
    return list(
        SystemRevision.objects.filter(system_id=system_id).order_by("revision_index", "created_at")
    )


def set_current_revision(system_id: str, revision_id: str) -> SystemRevision:
    revision = SystemRevision.objects.select_related("system").get(pk=revision_id, system_id=system_id)
    system = revision.system
    system.current_revision = revision
    system.save(update_fields=["current_revision"])
    return revision


def get_topology_artifact(system_id: str) -> Optional[dict[str, Any]]:
    revision = get_current_revision(system_id)
    if revision is not None and revision.topology_artifact is not None:
        return revision.topology_artifact
    artifacts = SystemGenerationArtifacts.objects.filter(system_id=system_id).first()
    if artifacts is None:
        return None
    return artifacts.topology_artifact


def get_semantic_sketch_plan(system_id: str) -> Optional[dict[str, Any]]:
    revision = get_current_revision(system_id)
    if revision is not None and revision.semantic_sketch_plan is not None:
        return revision.semantic_sketch_plan
    artifacts = SystemGenerationArtifacts.objects.filter(system_id=system_id).first()
    if artifacts is None:
        return None
    return artifacts.semantic_sketch_plan


def get_generation_process_text(system_id: str) -> Optional[str]:
    revision = get_current_revision(system_id)
    if revision is not None:
        return revision.process_text
    artifacts = SystemGenerationArtifacts.objects.filter(system_id=system_id).first()
    if artifacts is None:
        return None
    return artifacts.process_text
