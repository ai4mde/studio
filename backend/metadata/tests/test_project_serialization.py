"""Integration tests for project-scoped database serialization."""

from django.apps import apps
from django.test import TestCase

from diagram.models import Diagram, Edge, EdgeControlPoint, Node
from metadata.models import (
    Association,
    Attribute,
    ClassClassifier,
    Classifier,
    EndpointLabel,
    Interface,
    Multiplicity,
    Page,
    PageSection,
    Project,
    Relation,
    SectionAttribute,
    SectionComponent,
    System,
)
from metadata.services.versioning import (
    ProjectSerializationError,
    project_snapshot_json,
    serialize_project,
)
from metadata.services.versioning.constants import (
    PROJECT_MODEL_SCOPES,
    EXCLUDED_FIELDS,
    VERSION_METADATA_MODELS,
)


class ProjectSerializerTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Project")
        self.system = System.objects.create(project=self.project, name="Main")
        self.classifier = Classifier.objects.create(system=self.system, type="class")
        self.uml_class = ClassClassifier._base_manager.create(
            classifier=self.classifier, name="Customer"
        )

    def test_all_database_columns_and_related_tables_are_present(self):
        attribute = Attribute.objects.create(
            uml_class=self.uml_class,
            name="email",
            type="string",
            body="return 'ok'",
        )
        relation = Relation.objects.create(
            system=self.system,
            source=self.classifier,
            target=self.classifier,
            type="association",
        )
        multiplicity = Multiplicity.objects.create(source_lower=1, target_lower=0)
        labels = EndpointLabel.objects.create(source="owner", target="owned")
        Association.objects.create(
            relation=relation, multiplicity=multiplicity, labels=labels
        )

        diagram = Diagram.objects.create(system=self.system, type="class")
        Node.objects.create(diagram=diagram, classifier=self.classifier)
        edge = Edge.objects.create(diagram=diagram, relation=relation)
        point = EdgeControlPoint.objects.create(
            edge=edge, x_position=20, y_position=30, order=1
        )

        interface = Interface.objects.create(
            system=self.system, name="UI", description="Example"
        )
        page = Page.objects.create(interface=interface, name="Home")
        section = SectionComponent.objects.create(interface=interface, name="Main")
        PageSection.objects.create(page=page, section=section, order=0)
        SectionAttribute.objects.create(section=section, attribute=attribute, order=0)

        snapshot = serialize_project(self.project.pk)
        self.assertEqual(snapshot["project_id"], str(self.project.pk))
        self.assertEqual(set(snapshot["models"]), set(PROJECT_MODEL_SCOPES))

        def row(model, pk):
            return snapshot["models"][model._meta.label][str(pk)]

        # All concrete DB fields are included, including nullable fields,
        # FKs (as *_id), and fields on typed-data and detail models.
        for model, pk in (
            (Project, self.project.pk),
            (Classifier, self.classifier.pk),
            (ClassClassifier, self.uml_class.pk),
            (Association, relation.pk),
            (Multiplicity, multiplicity.pk),
            (EndpointLabel, labels.pk),
            (EdgeControlPoint, point.pk),
            (SectionAttribute, attribute.section_attributes.get().pk),
        ):
            expected = {
                field.attname for field in model._meta.concrete_fields
            } - EXCLUDED_FIELDS.get(model._meta.label, frozenset())
            self.assertEqual(set(row(model, pk)), expected)

        self.assertEqual(
            row(ClassClassifier, self.uml_class.pk)["name"], "Customer"
        )
        self.assertEqual(
            row(ClassClassifier, self.uml_class.pk)["classifier_id"],
            str(self.classifier.pk),
        )
        self.assertEqual(
            row(Association, relation.pk)["multiplicity_id"], str(multiplicity.pk)
        )
        self.assertEqual(
            row(EdgeControlPoint, point.pk)["edge_id"], str(edge.pk)
        )

    def test_project_scope_excludes_other_projects(self):
        other = Project.objects.create(name="Other")
        other_system = System.objects.create(project=other, name="Other system")
        other_classifier = Classifier.objects.create(
            system=other_system, type="class"
        )
        ClassClassifier._base_manager.create(classifier=other_classifier, name="Other")

        snapshot = serialize_project(self.project.pk)
        self.assertNotIn(str(other.pk), snapshot["models"]["metadata.Project"])
        self.assertNotIn(
            str(other_classifier.pk), snapshot["models"]["metadata.Classifier"]
        )

    def test_cross_project_reference_is_rejected(self):
        other = Project.objects.create(name="Other")
        other_system = System.objects.create(project=other, name="Other system")
        other_classifier = Classifier.objects.create(
            system=other_system, type="class"
        )
        diagram = Diagram.objects.create(system=self.system, type="class")
        Node.objects.create(diagram=diagram, classifier=other_classifier)

        with self.assertRaisesRegex(ProjectSerializationError, "outside this project"):
            serialize_project(self.project.pk)

    def test_output_is_stable(self):
        self.assertEqual(
            project_snapshot_json(self.project.pk),
            project_snapshot_json(self.project.pk),
        )

    def test_unknown_project_is_rejected(self):
        import uuid

        with self.assertRaises(ProjectSerializationError):
            serialize_project(uuid.uuid4())

    def test_registry_lists_current_metadata_and_diagram_models(self):
        # A newly added model must be deliberately registered so it isn't
        # silently omitted from portable project snapshots.
        actual_models = {
            model._meta.label
            for app_label in ("metadata", "diagram")
            for model in apps.get_app_config(app_label).get_models()
        }
        self.assertEqual(actual_models - VERSION_METADATA_MODELS, set(PROJECT_MODEL_SCOPES))

    def test_active_version_pointer_does_not_change_serialized_project(self):
        from metadata.models import ProjectVersion

        before = serialize_project(self.project.pk)
        version = ProjectVersion.objects.create(project=self.project, delta=[])
        self.project.current_version = version
        self.project.save(update_fields=["current_version"])
        self.assertEqual(serialize_project(self.project.pk), before)
        self.assertNotIn(
            "current_version_id",
            serialize_project(self.project.pk)["models"]["metadata.Project"][str(self.project.pk)],
        )
