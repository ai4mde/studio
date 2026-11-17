import json
from copy import deepcopy
from collections import Counter
from uuid import uuid4

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from diagram.models import Diagram, Edge, EdgeControlPoint, Node
from metadata.models import (
    Action,
    Actor,
    Association,
    Attribute,
    Category,
    ClassClassifier,
    Classifier,
    Composition,
    EndpointLabel,
    Enum,
    EnumLiteral,
    Interface,
    Multiplicity,
    Operation,
    Page,
    PageSection,
    Project,
    Relation,
    SectionAttribute,
    SectionComponent,
    System,
)
from metadata.services.versioning import (
    snapshot_project,
    create_release,
    export_release,
    import_release,
    restore_release,
)

from metadata.services.versioning.snapshot import PROJECT_MODELS
from metadata.services.versioning.utils import validate_snapshot


class SnapshotProjectTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.project = Project.objects.create(name="Project A", description="First")
        cls.other_project = Project.objects.create(name="Project B", description="Second")
        cls.system = System.objects.create(project=cls.project, name="System A1")
        cls.second_system = System.objects.create(
            project=cls.project, name="System A2"
        )
        cls.other_system = System.objects.create(
            project=cls.other_project, name="System B1"
        )

        # Classifiers are stored as a base record and a type-specific record.
        cls.customer = Classifier.objects.create(system=cls.system, type="class")
        cls.customer_data = ClassClassifier.objects.create(
            classifier=cls.customer, name="Customer"
        )
        cls.order = Classifier.objects.create(system=cls.system, type="class")
        cls.order_data = ClassClassifier.objects.create(
            classifier=cls.order, name="Order"
        )
        cls.enum = Classifier.objects.create(system=cls.system, type="enum")
        cls.enum_data = Enum.objects.create(classifier=cls.enum, name="Status")
        cls.literal = EnumLiteral.objects.create(
            enum=cls.enum_data, value="Pending", order=0
        )
        cls.attribute = Attribute.objects.create(
            uml_class=cls.customer_data,
            name="status",
            type="enum",
            enum=cls.enum_data,
        )
        cls.operation = Operation.objects.create(
            uml_class=cls.customer_data, name="display", type="string"
        )
        cls.actor = Classifier.objects.create(system=cls.system, type="actor")
        cls.actor_data = Actor.objects.create(classifier=cls.actor, name="User")

        # Relations have base records, type-specific records, and helper rows.
        cls.relation = Relation.objects.create(
            system=cls.system,
            source=cls.customer,
            target=cls.order,
            type="association",
        )
        cls.multiplicity = Multiplicity.objects.create(
            source_lower=0, target_lower=1
        )
        cls.endpoint_labels = EndpointLabel.objects.create(
            source="customer", target="orders"
        )
        cls.association = Association.objects.create(
            relation=cls.relation,
            label="places",
            multiplicity=cls.multiplicity,
            labels=cls.endpoint_labels,
        )
        cls.composition_relation = Relation.objects.create(
            system=cls.second_system,
            source=cls.customer,
            target=cls.order,
            type="composition",
        )
        cls.composition_multiplicity = Multiplicity.objects.create(
            source_lower=1, target_lower=0
        )
        cls.composition_labels = EndpointLabel.objects.create(
            source="whole", target="part"
        )
        cls.composition = Composition.objects.create(
            relation=cls.composition_relation,
            multiplicity=cls.composition_multiplicity,
            labels=cls.composition_labels,
        )

        # Diagram layout, node hierarchy, relation references, control points.
        cls.diagram = Diagram.objects.create(
            system=cls.system, type="class", name="Overview"
        )
        cls.second_diagram = Diagram.objects.create(
            system=cls.second_system, type="class", name="Other view"
        )
        cls.parent_node = Node.objects.create(
            diagram=cls.diagram,
            classifier=cls.customer,
            x_position=10,
            y_position=20,
        )
        cls.child_node = Node.objects.create(
            diagram=cls.diagram,
            classifier=cls.order,
            parent=cls.parent_node,
            x_position=30,
            y_position=40,
        )
        cls.edge = Edge.objects.create(
            diagram=cls.diagram, relation=cls.relation, rounded=True
        )
        cls.control_point = EdgeControlPoint.objects.create(
            edge=cls.edge, x_position=15, y_position=25, order=0
        )

        # Interface subtree and links to the classifier-owned attribute.
        cls.interface = Interface.objects.create(
            system=cls.system,
            name="Customer UI",
            description="A simple interface",
            actor=cls.actor_data,
        )
        cls.category = Category.objects.create(
            interface=cls.interface, name="Customers"
        )
        cls.page = Page.objects.create(
            interface=cls.interface, name="Customer detail", category=cls.category
        )
        cls.section = SectionComponent.objects.create(
            interface=cls.interface,
            name="Customer form",
            uml_class=cls.customer_data,
        )
        cls.page_section = PageSection.objects.create(
            page=cls.page, section=cls.section, order=0
        )
        cls.section_attribute = SectionAttribute.objects.create(
            section=cls.section, attribute=cls.attribute, order=0
        )

        # A second project with its own nested data to detect leaks.
        cls.foreign_classifier = Classifier.objects.create(
            system=cls.other_system, type="action"
        )
        cls.foreign_action = Action.objects.create(
            classifier=cls.foreign_classifier, name="External action"
        )
        cls.foreign_diagram = Diagram.objects.create(
            system=cls.other_system, type="activity", name="External view"
        )
        cls.foreign_node = Node.objects.create(
            diagram=cls.foreign_diagram, classifier=cls.foreign_classifier
        )
        cls.foreign_interface = Interface.objects.create(
            system=cls.other_system,
            name="External UI",
            description="Not part of Project A",
        )

    @staticmethod
    def by_model(snapshot, model):
        return {
            str(record["pk"]): record
            for record in snapshot["objects"]
            if record["model"] == model._meta.label_lower
        }

    def test_snapshot_is_json_serializable_and_uses_expected_envelope(self):
        snapshot = snapshot_project(self.project.pk)

        self.assertEqual(snapshot["schema_version"], 1)
        self.assertEqual(snapshot["project_id"], str(self.project.pk))
        self.assertIsInstance(snapshot["objects"], list)
        self.assertEqual(json.loads(json.dumps(snapshot)), snapshot)
        self.assertTrue(snapshot["objects"])
        for obj in snapshot["objects"]:
            self.assertEqual(set(obj), {"model", "pk", "fields"})
            self.assertIsInstance(obj["fields"], dict)

    def test_export_contains_project_and_all_of_its_systems(self):
        snapshot = snapshot_project(self.project.pk)

        projects = self.by_model(snapshot, Project)
        systems = self.by_model(snapshot, System)
        self.assertEqual(set(projects), {str(self.project.pk)})
        self.assertEqual(
            set(systems), {str(self.system.pk), str(self.second_system.pk)}
        )
        self.assertEqual(projects[str(self.project.pk)]["fields"]["name"], "Project A")
        self.assertEqual(
            systems[str(self.system.pk)]["fields"]["project"],
            str(self.project.pk),
        )

    def test_includes_typed_classifiers_and_classifier_owned_data(self):
        snapshot = snapshot_project(self.project.pk)

        self.assertEqual(
            set(self.by_model(snapshot, Classifier)),
            {str(self.customer.pk), str(self.order.pk), str(self.enum.pk), str(self.actor.pk)},
        )
        for model, obj in (
            (ClassClassifier, self.customer_data),
            (Enum, self.enum_data),
            (EnumLiteral, self.literal),
            (Attribute, self.attribute),
            (Operation, self.operation),
            (Actor, self.actor_data),
        ):
            with self.subTest(model=model.__name__):
                self.assertIn(str(obj.pk), self.by_model(snapshot, model))

        self.assertEqual(
            self.by_model(snapshot, ClassClassifier)[str(self.customer_data.pk)][
                "fields"
            ]["name"],
            "Customer",
        )
        self.assertEqual(
            self.by_model(snapshot, Attribute)[str(self.attribute.pk)]["fields"]["enum"],
            str(self.enum.pk),
        )
        self.assertEqual(
            self.by_model(snapshot, EnumLiteral)[str(self.literal.pk)]["fields"]["enum"],
            str(self.enum.pk),
        )

    def test_includes_relation_types_and_both_kinds_of_helper_records(self):
        snapshot = snapshot_project(self.project.pk)

        self.assertEqual(
            set(self.by_model(snapshot, Relation)),
            {str(self.relation.pk), str(self.composition_relation.pk)},
        )
        self.assertIn(str(self.association.pk), self.by_model(snapshot, Association))
        self.assertIn(str(self.composition.pk), self.by_model(snapshot, Composition))
        self.assertEqual(
            set(self.by_model(snapshot, Multiplicity)),
            {str(self.multiplicity.pk), str(self.composition_multiplicity.pk)},
        )
        self.assertEqual(
            set(self.by_model(snapshot, EndpointLabel)),
            {str(self.endpoint_labels.pk), str(self.composition_labels.pk)},
        )
        relation_fields = self.by_model(snapshot, Relation)[str(self.relation.pk)]["fields"]
        self.assertEqual(relation_fields["source"], str(self.customer.pk))
        self.assertEqual(relation_fields["target"], str(self.order.pk))
        association_fields = self.by_model(snapshot, Association)[
            str(self.association.pk)
        ]["fields"]
        self.assertEqual(association_fields["multiplicity"], str(self.multiplicity.pk))
        self.assertEqual(association_fields["labels"], str(self.endpoint_labels.pk))

    def test_includes_diagram_hierarchy_and_layout(self):
        snapshot = snapshot_project(self.project.pk)

        self.assertEqual(
            set(self.by_model(snapshot, Diagram)),
            {str(self.diagram.pk), str(self.second_diagram.pk)},
        )
        self.assertEqual(
            set(self.by_model(snapshot, Node)),
            {str(self.parent_node.pk), str(self.child_node.pk)},
        )
        self.assertIn(str(self.edge.pk), self.by_model(snapshot, Edge))
        self.assertIn(
            str(self.control_point.pk), self.by_model(snapshot, EdgeControlPoint)
        )
        node_fields = self.by_model(snapshot, Node)[str(self.child_node.pk)]["fields"]
        self.assertEqual(node_fields["parent"], str(self.parent_node.pk))
        self.assertEqual(node_fields["classifier"], str(self.order.pk))
        self.assertEqual(node_fields["x_position"], 30)
        edge_fields = self.by_model(snapshot, Edge)[str(self.edge.pk)]["fields"]
        self.assertEqual(edge_fields["relation"], str(self.relation.pk))
        self.assertTrue(edge_fields["rounded"])
        point_fields = self.by_model(snapshot, EdgeControlPoint)[
            str(self.control_point.pk)
        ]["fields"]
        self.assertEqual(point_fields["edge"], str(self.edge.pk))
        self.assertEqual(point_fields["x_position"], 15)

    def test_includes_interface_hierarchy_and_references(self):
        snapshot = snapshot_project(self.project.pk)

        for model, obj in (
            (Interface, self.interface),
            (Category, self.category),
            (Page, self.page),
            (SectionComponent, self.section),
            (PageSection, self.page_section),
            (SectionAttribute, self.section_attribute),
        ):
            with self.subTest(model=model.__name__):
                self.assertIn(str(obj.pk), self.by_model(snapshot, model))

        fields = self.by_model(snapshot, PageSection)[str(self.page_section.pk)][
            "fields"
        ]
        self.assertEqual(fields["page"], str(self.page.pk))
        self.assertEqual(fields["section"], str(self.section.pk))
        self.assertEqual(
            self.by_model(snapshot, SectionAttribute)[str(self.section_attribute.pk)][
                "fields"
            ]["attribute"],
            str(self.attribute.pk),
        )

    def test_does_not_export_records_from_another_project(self):
        snapshot = snapshot_project(self.project.pk)
        exported = {(o["model"], str(o["pk"])) for o in snapshot["objects"]}

        for obj in (
            self.other_project,
            self.other_system,
            self.foreign_classifier,
            self.foreign_action,
            self.foreign_diagram,
            self.foreign_node,
            self.foreign_interface,
        ):
            with self.subTest(model=obj._meta.label_lower):
                self.assertNotIn((obj._meta.label_lower, str(obj.pk)), exported)

    def test_all_objects_come_from_registry_and_releases_are_excluded(self):
        snapshot = snapshot_project(self.project.pk)
        allowed = {model._meta.label_lower for model in PROJECT_MODELS}

        self.assertEqual(
            {o["model"] for o in snapshot["objects"]} - allowed,
            set(),
        )
        self.assertNotIn("metadata.release", allowed)
        self.assertNotIn(
            "metadata.release", {o["model"] for o in snapshot["objects"]}
        )

    def test_release_snapshots_are_not_recursively_exported(self):
        # Release was added after the backend archive used for these tests.
        # Skip this check if it has not been registered yet.
        try:
            release_model = apps.get_model("metadata", "Release")
        except LookupError:
            self.skipTest("Release model has not been registered")

        release_model.objects.create(
            project=self.project,
            name="First version",
            project_data={"schema_version": 1, "objects": []},
            release_notes=[],
        )
        snapshot = snapshot_project(self.project.pk)
        self.assertFalse(
            any(obj["model"] == release_model._meta.label_lower
                for obj in snapshot["objects"])
        )

    def test_snapshot_is_deterministically_ordered_and_has_no_duplicates(self):
        first = snapshot_project(self.project.pk)
        second = snapshot_project(self.project.pk)
        self.assertEqual(first, second)

        model_order = {model._meta.label_lower: i for i, model in enumerate(PROJECT_MODELS)}
        objects = first["objects"]
        self.assertEqual(
            [model_order[o["model"]] for o in objects],
            sorted(model_order[o["model"]] for o in objects),
        )
        for label in {o["model"] for o in objects}:
            pks = [o["pk"] for o in objects if o["model"] == label]
            self.assertEqual(pks, sorted(pks))
        keys = [(o["model"], str(o["pk"])) for o in objects]
        self.assertTrue(all(count == 1 for count in Counter(keys).values()))

    def test_accepts_uuid_as_string(self):
        self.assertEqual(
            snapshot_project(str(self.project.pk)),
            snapshot_project(self.project.pk),
        )

    def test_nonexistent_project_raises_does_not_exist(self):
        with self.assertRaises(Project.DoesNotExist):
            snapshot_project(uuid4())

    def test_empty_project_only_contains_its_project_record(self):
        empty = Project.objects.create(name="Empty project")
        snapshot = snapshot_project(empty.pk)

        self.assertEqual(snapshot["project_id"], str(empty.pk))
        self.assertEqual(len(snapshot["objects"]), 1)
        self.assertEqual(snapshot["objects"][0]["model"], Project._meta.label_lower)
        self.assertEqual(snapshot["objects"][0]["pk"], str(empty.pk))

    def test_snapshot_reads_current_state_without_writing_to_database(self):
        with CaptureQueriesContext(connection) as queries:
            before = snapshot_project(self.project.pk)

        writes = (
            query["sql"]
            for query in queries
            if query["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
        )
        self.assertEqual(list(writes), [])

        Project.objects.filter(pk=self.project.pk).update(name="Project A updated")
        after = snapshot_project(self.project.pk)
        self.assertEqual(
            self.by_model(before, Project)[str(self.project.pk)]["fields"]["name"],
            "Project A",
        )
        self.assertEqual(
            self.by_model(after, Project)[str(self.project.pk)]["fields"]["name"],
            "Project A updated",
        )


    def test_current_release_is_excluded_from_snapshot(self):
        release = create_release(self.project.pk, "Version 1")

        snapshot = snapshot_project(self.project.pk)
        project_data = self.by_model(snapshot, Project)[str(self.project.pk)]

        self.assertNotIn("current_release", project_data["fields"])
        self.assertEqual(snapshot, release.project_data)

        self.project.refresh_from_db()
        self.assertEqual(self.project.current_release_id, release.pk)

    def test_create_release_saves_independent_snapshot(self):
        release = create_release(
            self.project.pk,
            "Version 1",
            description="Initial version",
            release_notes=["Initial snapshot"],
        )

        original_snapshot = deepcopy(release.project_data)

        self.assertEqual(release.name, "Version 1")
        self.assertEqual(release.description, "Initial version")
        self.assertEqual(release.release_notes, ["Initial snapshot"])
        self.assertEqual(export_release(release.pk), original_snapshot)

        # Changing the live project must not change the saved release.
        Project.objects.filter(pk=self.project.pk).update(name="Modified")

        release.refresh_from_db()

        self.assertEqual(release.project_data, original_snapshot)
        self.assertNotEqual(
            snapshot_project(self.project.pk),
            original_snapshot,
        )

    def test_import_release_does_not_modify_project(self):
        snapshot = snapshot_project(self.project.pk)

        imported = import_release(
            self.project.pk,
            snapshot,
            name="Imported version",
        )

        self.assertEqual(imported.project_data, snapshot)
        self.assertEqual(export_release(imported.pk), snapshot)
        self.assertEqual(snapshot_project(self.project.pk), snapshot)

        # Importing a release must not activate it.
        self.project.refresh_from_db()
        self.assertIsNone(self.project.current_release_id)

    def test_validate_snapshot_rejects_invalid_objects(self):
        snapshot = snapshot_project(self.project.pk)

        cases = []

        invalid_version = deepcopy(snapshot)
        invalid_version["schema_version"] = 999
        cases.append(invalid_version)

        invalid_project = deepcopy(snapshot)
        invalid_project["project_id"] = str(uuid4())
        cases.append(invalid_project)

        missing_project = deepcopy(snapshot)
        missing_project["objects"] = [
            obj for obj in missing_project["objects"]
            if obj["model"] != Project._meta.label_lower
        ]
        cases.append(missing_project)

        duplicate_object = deepcopy(snapshot)
        duplicate_object["objects"].append(
            deepcopy(duplicate_object["objects"][0])
        )
        cases.append(duplicate_object)

        disallowed_model = deepcopy(snapshot)
        disallowed_model["objects"][0]["model"] = "auth.user"
        cases.append(disallowed_model)

        for invalid_snapshot in cases:
            with self.subTest(snapshot=invalid_snapshot):
                with self.assertRaises(ValidationError):
                    validate_snapshot(invalid_snapshot, self.project.pk)

    def test_restore_release_round_trip(self):
        release = create_release(self.project.pk, "Version 1")
        original_snapshot = deepcopy(release.project_data)

        # Modify the existing project.
        Project.objects.filter(pk=self.project.pk).update(
            name="Changed project"
        )
        ClassClassifier.objects.filter(pk=self.customer_data.pk).update(
            name="Changed Customer"
        )
        Diagram.objects.filter(pk=self.diagram.pk).update(
            name="Changed diagram"
        )

        # Add an object that was not in the release.
        extra_diagram = Diagram.objects.create(
            system=self.system,
            type="class",
            name="Temporary diagram",
        )

        self.assertNotEqual(
            snapshot_project(self.project.pk),
            original_snapshot,
        )

        restored = restore_release(release.pk, force=True)

        # Complete project state should match the saved snapshot.
        self.assertEqual(
            snapshot_project(self.project.pk),
            original_snapshot,
        )

        # Newly created records must be removed.
        self.assertFalse(
            Diagram.objects.filter(pk=extra_diagram.pk).exists()
        )

        # The selected version must become the current release.
        self.assertEqual(restored.current_release_id, release.pk)

    def test_restore_release_preserves_relationships(self):
        release = create_release(self.project.pk, "Version 1")

        restore_release(release.pk, force=True)

        # Classifiers still belong to their original systems.
        customer = Classifier.objects.get(pk=self.customer.pk)
        self.assertEqual(customer.system_id, self.system.pk)

        # Typed classifier data is still connected.
        customer_data = ClassClassifier.objects.get(
            pk=self.customer_data.pk
        )
        self.assertEqual(customer_data.classifier_id, self.customer.pk)

        # Diagram node hierarchy is preserved.
        child = Node.objects.get(pk=self.child_node.pk)
        self.assertEqual(child.parent_id, self.parent_node.pk)
        self.assertEqual(child.classifier_id, self.order.pk)

        # Relation references are preserved.
        relation = Relation.objects.get(pk=self.relation.pk)
        self.assertEqual(relation.source_id, self.customer.pk)
        self.assertEqual(relation.target_id, self.order.pk)

        # Helper records survive restoration.
        association = Association.objects.get(pk=self.association.pk)
        self.assertEqual(
            association.multiplicity_id,
            self.multiplicity.pk,
        )
        self.assertEqual(
            association.labels_id,
            self.endpoint_labels.pk,
        )

        # Diagram edge references are preserved.
        edge = Edge.objects.get(pk=self.edge.pk)
        self.assertEqual(edge.relation_id, self.relation.pk)

        control_point = EdgeControlPoint.objects.get(
            pk=self.control_point.pk
        )
        self.assertEqual(control_point.edge_id, self.edge.pk)

    def test_restore_rejects_unsaved_changes(self):
        release = create_release(self.project.pk, "Version 1")

        Project.objects.filter(pk=self.project.pk).update(
            name="Unsaved changes"
        )

        with self.assertRaises(ValidationError):
            restore_release(release.pk)

        # Failed restore must leave the changes intact.
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Unsaved changes")
        self.assertEqual(self.project.current_release_id, release.pk)

        # Explicit force should allow restoration.
        restore_release(release.pk, force=True)

        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Project A")

    def test_restore_without_unsaved_changes(self):
        release_a = create_release(self.project.pk, "Version A")

        # Create a second version with changed data.
        Project.objects.filter(pk=self.project.pk).update(
            name="Version B project"
        )
        release_b = create_release(self.project.pk, "Version B")

        self.assertEqual(
            snapshot_project(self.project.pk),
            release_b.project_data,
        )

        # No unsaved changes: force should not be required.
        restored = restore_release(release_a.pk)

        self.assertEqual(restored.current_release_id, release_a.pk)
        self.assertEqual(
            snapshot_project(self.project.pk),
            release_a.project_data,
        )

    def test_failed_restore_does_not_delete_existing_data(self):
        release = create_release(self.project.pk, "Version 1")

        before = snapshot_project(self.project.pk)

        # Remove a required system from the stored snapshot.
        broken_snapshot = deepcopy(release.project_data)
        broken_snapshot["objects"] = [
            obj for obj in broken_snapshot["objects"]
            if not (
                obj["model"] == System._meta.label_lower
                and obj["pk"] == str(self.system.pk)
            )
        ]

        release.project_data = broken_snapshot
        release.save(update_fields=["project_data"])

        with self.assertRaises(ValidationError):
            restore_release(release.pk, force=True)

        # Failed restoration must not change the active project.
        self.assertEqual(snapshot_project(self.project.pk), before)

        self.assertTrue(
            System.objects.filter(pk=self.system.pk).exists()
        )
        self.assertTrue(
            Classifier.objects.filter(pk=self.customer.pk).exists()
        )

    def test_restore_does_not_modify_other_projects(self):
        release = create_release(self.project.pk, "Version 1")

        other_before = snapshot_project(self.other_project.pk)

        restore_release(release.pk, force=True)

        other_after = snapshot_project(self.other_project.pk)

        self.assertEqual(other_before, other_after)
