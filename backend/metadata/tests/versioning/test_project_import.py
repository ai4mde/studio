from copy import deepcopy
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from diagram.models import Diagram, Edge, Node
from metadata.models import (
    ClassClassifier,
    Classifier,
    Project,
    Release,
    Relation,
    System,
)
from metadata.services.versioning import snapshot_project
from metadata.services.versioning.import_project import (
    ProjectAlreadyExistsError,
    import_project,
)


class ImportProjectTests(TestCase):
    def setUp(self):
        source = Project.objects.create(name="Exported project", description="Original")
        system = System.objects.create(project=source, name="Main system")
        customer = Classifier.objects.create(system=system, type="class")
        customer_data = ClassClassifier.objects.create(
            classifier=customer, name="Customer"
        )
        order = Classifier.objects.create(system=system, type="class")
        ClassClassifier.objects.create(classifier=order, name="Order")
        relation = Relation.objects.create(
            system=system, source=customer, target=order, type="association"
        )
        diagram = Diagram.objects.create(
            system=system, name="Overview", type="class"
        )
        parent_node = Node.objects.create(diagram=diagram, classifier=customer)
        child_node = Node.objects.create(
            diagram=diagram, classifier=order, parent=parent_node
        )
        edge = Edge.objects.create(diagram=diagram, relation=relation)

        self.ids = {
            "project": source.pk,
            "system": system.pk,
            "customer": customer.pk,
            "customer_data": customer_data.pk,
            "order": order.pk,
            "relation": relation.pk,
            "diagram": diagram.pk,
            "parent_node": parent_node.pk,
            "child_node": child_node.pk,
            "edge": edge.pk,
        }
        self.snapshot = snapshot_project(source.pk)
        source.delete()

    def test_import_creates_new_project(self):
        project = import_project(self.snapshot)

        self.assertEqual(project.pk, self.ids["project"])
        self.assertEqual(project.name, "Exported project")
        self.assertEqual(project.description, "Original")
        self.assertEqual(System.objects.filter(project=project).count(), 1)
        self.assertEqual(snapshot_project(project.pk), self.snapshot)

    def test_import_preserves_object_uuids(self):
        import_project(self.snapshot)

        for model, key in (
            (System, "system"),
            (Classifier, "customer"),
            (ClassClassifier, "customer_data"),
            (Relation, "relation"),
            (Diagram, "diagram"),
            (Node, "parent_node"),
            (Node, "child_node"),
            (Edge, "edge"),
        ):
            with self.subTest(model=model.__name__, key=key):
                self.assertTrue(model.objects.filter(pk=self.ids[key]).exists())

    def test_import_preserves_relationships(self):
        import_project(self.snapshot)

        system = System.objects.get(pk=self.ids["system"])
        customer_data = ClassClassifier.objects.get(pk=self.ids["customer_data"])
        relation = Relation.objects.get(pk=self.ids["relation"])
        diagram = Diagram.objects.get(pk=self.ids["diagram"])
        child = Node.objects.get(pk=self.ids["child_node"])
        edge = Edge.objects.get(pk=self.ids["edge"])

        self.assertEqual(system.project_id, self.ids["project"])
        self.assertEqual(customer_data.classifier_id, self.ids["customer"])
        self.assertEqual(relation.source_id, self.ids["customer"])
        self.assertEqual(relation.target_id, self.ids["order"])
        self.assertEqual(diagram.system_id, self.ids["system"])
        self.assertEqual(child.parent_id, self.ids["parent_node"])
        self.assertEqual(child.classifier_id, self.ids["order"])
        self.assertEqual(edge.diagram_id, self.ids["diagram"])
        self.assertEqual(edge.relation_id, self.ids["relation"])

    def test_import_creates_and_activates_initial_release(self):
        project = import_project(
            self.snapshot,
            name="Imported baseline",
            description="First release",
            release_notes=["Imported from file"],
        )

        project.refresh_from_db()
        self.assertEqual(Release.objects.filter(project=project).count(), 1)
        release = project.current_release
        self.assertIsNotNone(release)
        self.assertEqual(release.name, "Imported baseline")
        self.assertEqual(release.description, "First release")
        self.assertEqual(release.release_notes, ["Imported from file"])
        self.assertEqual(release.project_data, self.snapshot)
        # current_release is deliberately excluded from project snapshots.
        self.assertEqual(snapshot_project(project.pk), self.snapshot)

    def test_duplicate_project_is_rejected_without_changes(self):
        import_project(self.snapshot)
        before = snapshot_project(self.ids["project"])

        with self.assertRaises(ProjectAlreadyExistsError):
            import_project(self.snapshot)

        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Release.objects.count(), 1)
        self.assertEqual(snapshot_project(self.ids["project"]), before)

    def test_object_uuid_collision_with_another_project_is_rejected(self):
        other = Project.objects.create(name="Unrelated project")
        existing_system = System.objects.create(
            pk=self.ids["system"], project=other, name="Unrelated system"
        )
        with self.assertRaises(ValidationError):
            import_project(self.snapshot)

        self.assertFalse(Project.objects.filter(pk=self.ids["project"]).exists())
        self.assertEqual(Release.objects.count(), 0)
        existing_system.refresh_from_db()
        self.assertEqual(existing_system.project_id, other.pk)
        self.assertEqual(existing_system.name, "Unrelated system")

    def test_invalid_snapshot_is_rejected_without_writes(self):
        invalid = deepcopy(self.snapshot)
        invalid["objects"].append(deepcopy(invalid["objects"][0]))

        with self.assertRaises(ValidationError):
            import_project(invalid)

        self.assertFalse(Project.objects.filter(pk=self.ids["project"]).exists())
        self.assertEqual(Release.objects.count(), 0)

    def test_failure_after_creating_root_project_rolls_back(self):
        # Force failure during graph restoration, after the root Project row
        # has been inserted. The outer transaction must roll back that row.
        with patch(
            "metadata.services.versioning.import_project.restore_project",
            side_effect=ValidationError("Simulated restore failure"),
        ):
            with self.assertRaises(ValidationError):
                import_project(self.snapshot)

        self.assertFalse(Project.objects.filter(pk=self.ids["project"]).exists())
        self.assertFalse(System.objects.filter(pk=self.ids["system"]).exists())
        self.assertEqual(Release.objects.count(), 0)
