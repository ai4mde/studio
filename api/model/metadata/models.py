import uuid

from django.db import models, transaction


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
            System.import_from_json(system_data)
            system_ids.append(system_data["id"])

        cls.delete_missing(project.systems, system_ids)

        return project


class System(ImportMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="systems",
    )
    name = models.CharField(max_length=255)
    description = models.TextField()

    @classmethod
    @transaction.atomic
    def import_from_json(cls, data):
        from diagram.models import Diagram # Prevent circular import
        system, _ = cls.upsert_from_json(data)

        classifier_ids = []
        for classifier_data in data['classifiers']:
            Classifier.import_from_json(classifier_data)
            classifier_ids.append(classifier_data['id'])
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


class Release(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    project_data = models.JSONField(default=dict) # Contains the entire json blob of the project, systems, classifiers, relations etc.
    release_notes = models.JSONField()


class Classifier(ImportMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="classifiers", null=True, blank=True,
    )
    system = models.ForeignKey(
        System, on_delete=models.CASCADE, related_name="classifiers", null=True, blank=True,
    )
    data = models.JSONField()


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
