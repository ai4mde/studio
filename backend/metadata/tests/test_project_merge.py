import json
from copy import deepcopy
from uuid import UUID, uuid4

from django.core import serializers
from django.core.exceptions import ValidationError
from django.test import TestCase

from diagram.models import Diagram, Edge, Node
from metadata.models import (
    Association,
    Attribute,
    ClassClassifier,
    Classifier,
    EndpointLabel,
    Enum,
    Interface,
    Multiplicity,
    Page,
    PageSection,
    Project,
    Relation,
    Release,
    SectionComponent,
    Swimlane,
    System,
)
from metadata.services.versioning.merge import (
    _index_objects,
    _object_key,
    merge_snapshots,
)

from metadata.services.versioning import (
    MergeConflictError,
    merge_releases,
    create_release,
    restore_release,
    snapshot_project,
)
from metadata.services.versioning.snapshot import (
    PROJECT_MODELS,
    SCHEMA_VERSION,
)


class MergeFixtureMixin:
    """Common, valid project graph used by both merge test classes."""

    @classmethod
    def setUpTestData(cls):
        cls.project = Project.objects.create(name="Shared project", description="Base")
        cls.system = System.objects.create(project=cls.project, name="Main system")

        cls.customer = Classifier.objects.create(system=cls.system, type="class")
        cls.customer_data = ClassClassifier.objects.create(
            classifier=cls.customer, name="Customer"
        )
        cls.order = Classifier.objects.create(system=cls.system, type="class")
        cls.order_data = ClassClassifier.objects.create(
            classifier=cls.order, name="Order"
        )

        cls.relation = Relation.objects.create(
            system=cls.system,
            source=cls.customer,
            target=cls.order,
            type="association",
        )
        cls.multiplicity = Multiplicity.objects.create(
            source_lower=0, target_lower=1
        )
        cls.labels = EndpointLabel.objects.create(
            source="customer", target="orders"
        )
        cls.association = Association.objects.create(
            relation=cls.relation,
            label="places",
            multiplicity=cls.multiplicity,
            labels=cls.labels,
        )

        # One diagram already has the source and target nodes (for edge tests).
        # A separate empty diagram is used for duplicate-node tests.
        cls.diagram = Diagram.objects.create(
            system=cls.system, type="class", name="Overview"
        )
        cls.customer_node = Node.objects.create(
            diagram=cls.diagram, classifier=cls.customer
        )
        cls.order_node = Node.objects.create(
            diagram=cls.diagram, classifier=cls.order
        )
        cls.empty_diagram = Diagram.objects.create(
            system=cls.system, type="class", name="Empty diagram"
        )

        # Used to test an ordinary (non-diagram) unique constraint:
        # PageSection must be unique on (page, order).
        cls.interface = Interface.objects.create(
            system=cls.system, name="UI", description="A shared interface"
        )
        cls.page = Page.objects.create(interface=cls.interface, name="Details")
        cls.section_a = SectionComponent.objects.create(
            interface=cls.interface, name="Section A"
        )
        cls.section_b = SectionComponent.objects.create(
            interface=cls.interface, name="Section B"
        )

    def base_snapshot(self):
        return snapshot_project(self.project.pk)

    @staticmethod
    def add_record(snapshot, instance):
        """Append a correctly serialized *unsaved* Django model instance."""
        record = json.loads(serializers.serialize("json", [instance]))[0]
        snapshot["objects"].append(record)
        return record

    @staticmethod
    def record(snapshot, model, pk):
        return next(
            item
            for item in snapshot["objects"]
            if item["model"] == model._meta.label_lower
            and UUID(str(item["pk"])) == UUID(str(pk))
        )

    @staticmethod
    def drop_record(snapshot, model, pk):
        snapshot["objects"] = [
            item
            for item in snapshot["objects"]
            if not (
                item["model"] == model._meta.label_lower
                and UUID(str(item["pk"])) == UUID(str(pk))
            )
        ]

    @staticmethod
    def indexed(snapshot):
        return {_object_key(item): item for item in snapshot["objects"]}

    def make_branches_with_diagrams(self):
        base = self.base_snapshot()
        ground_truth = deepcopy(base)
        incoming = deepcopy(base)
        diagram_a = Diagram(system_id=self.system.pk, type="class", name="Diagram A")
        diagram_b = Diagram(system_id=self.system.pk, type="class", name="Diagram B")
        self.add_record(ground_truth, diagram_a)
        self.add_record(incoming, diagram_b)
        return ground_truth, incoming, diagram_a, diagram_b

    def make_duplicate_nodes(self):
        base = self.base_snapshot()
        ground_truth = deepcopy(base)
        incoming = deepcopy(base)
        node_a = Node(diagram_id=self.empty_diagram.pk, classifier_id=self.customer.pk)
        node_b = Node(diagram_id=self.empty_diagram.pk, classifier_id=self.customer.pk)
        self.add_record(ground_truth, node_a)
        self.add_record(incoming, node_b)
        return ground_truth, incoming, node_a, node_b


class MergeSnapshotsTests(MergeFixtureMixin, TestCase):
    """Pure snapshot merging rules and frontend-readable conflict details."""

    def test_identical_snapshots_merge_without_duplicate_records(self):
        snapshot = self.base_snapshot()
        merged = merge_snapshots(snapshot, deepcopy(snapshot))
        self.assertEqual(merged, snapshot)
        self.assertEqual(len(self.indexed(merged)), len(merged["objects"]))

    def test_additions_from_both_versions_are_kept(self):
        ground_truth, incoming, diagram_a, diagram_b = (
            self.make_branches_with_diagrams()
        )
        merged = merge_snapshots(ground_truth, incoming)
        records = self.indexed(merged)
        self.assertIn((Diagram._meta.label_lower, diagram_a.pk), records)
        self.assertIn((Diagram._meta.label_lower, diagram_b.pk), records)
        self.assertEqual(
            merged["project_id"], str(self.project.pk)
        )
        self.assertEqual(merged["schema_version"], SCHEMA_VERSION)

    def test_ground_truth_wins_for_the_same_object(self):
        ground_truth = self.base_snapshot()
        incoming = deepcopy(ground_truth)
        self.record(ground_truth, Project, self.project.pk)["fields"]["name"] = "A name"
        self.record(incoming, Project, self.project.pk)["fields"]["name"] = "B name"
        self.record(ground_truth, ClassClassifier, self.customer.pk)["fields"][
            "name"
        ] = "Client A"
        self.record(incoming, ClassClassifier, self.customer.pk)["fields"][
            "name"
        ] = "Client B"

        merged = merge_snapshots(ground_truth, incoming)
        self.assertEqual(
            self.record(merged, Project, self.project.pk)["fields"]["name"],
            "A name",
        )
        self.assertEqual(
            self.record(merged, ClassClassifier, self.customer.pk)["fields"][
                "name"
            ],
            "Client A",
        )

    def test_ground_truth_wins_entire_record_not_individual_fields(self):
        ground_truth = self.base_snapshot()
        incoming = deepcopy(ground_truth)
        a = self.record(ground_truth, System, self.system.pk)["fields"]
        b = self.record(incoming, System, self.system.pk)["fields"]
        a["name"] = "A system"
        b["description"] = "B-only change"

        merged = merge_snapshots(ground_truth, incoming)
        fields = self.record(merged, System, self.system.pk)["fields"]
        self.assertEqual(fields, a)
        self.assertNotEqual(fields["description"], "B-only change")

    def test_new_classifiers_and_their_typed_records_are_kept(self):
        base = self.base_snapshot()
        ground_truth = deepcopy(base)
        incoming = deepcopy(base)
        classifier_a = Classifier(system_id=self.system.pk, type="class")
        classifier_b = Classifier(system_id=self.system.pk, type="class")
        self.add_record(ground_truth, classifier_a)
        self.add_record(
            ground_truth, ClassClassifier(classifier_id=classifier_a.pk, name="From A")
        )
        self.add_record(incoming, classifier_b)
        self.add_record(
            incoming, ClassClassifier(classifier_id=classifier_b.pk, name="From B")
        )

        merged = merge_snapshots(ground_truth, incoming)
        self.assertEqual(
            self.record(merged, ClassClassifier, classifier_a.pk)["fields"]["name"],
            "From A",
        )
        self.assertEqual(
            self.record(merged, ClassClassifier, classifier_b.pk)["fields"]["name"],
            "From B",
        )
        self.record(merged, Classifier, classifier_a.pk)
        self.record(merged, Classifier, classifier_b.pk)

    def test_new_child_records_are_merged_independently(self):
        base = self.base_snapshot()
        ground_truth = deepcopy(base)
        incoming = deepcopy(base)
        attribute_a = Attribute(
            uml_class_id=self.customer.pk, name="email", type="string"
        )
        attribute_b = Attribute(
            uml_class_id=self.customer.pk, name="phone", type="string"
        )
        self.add_record(ground_truth, attribute_a)
        self.add_record(incoming, attribute_b)

        merged = merge_snapshots(ground_truth, incoming)
        self.record(merged, Attribute, attribute_a.pk)
        self.record(merged, Attribute, attribute_b.pk)

    def test_missing_from_one_version_is_not_treated_as_a_deletion(self):
        base = self.base_snapshot()
        for deleting_ground_truth in (True, False):
            with self.subTest(deleting_ground_truth=deleting_ground_truth):
                ground_truth = deepcopy(base)
                incoming = deepcopy(base)
                if deleting_ground_truth:
                    self.drop_record(ground_truth, Diagram, self.empty_diagram.pk)
                else:
                    self.drop_record(incoming, Diagram, self.empty_diagram.pk)

                merged = merge_snapshots(ground_truth, incoming)
                self.record(merged, Diagram, self.empty_diagram.pk)

    def test_source_snapshots_are_not_mutated(self):
        ground_truth, incoming, _, _ = self.make_branches_with_diagrams()
        original_a, original_b = deepcopy(ground_truth), deepcopy(incoming)
        merge_snapshots(ground_truth, incoming)
        self.assertEqual(ground_truth, original_a)
        self.assertEqual(incoming, original_b)

    def test_result_is_deterministically_ordered(self):
        ground_truth, incoming, _, _ = self.make_branches_with_diagrams()
        first = merge_snapshots(ground_truth, incoming)
        second = merge_snapshots(ground_truth, incoming)
        self.assertEqual(first, second)
        model_order = {
            model._meta.label_lower: index
            for index, model in enumerate(PROJECT_MODELS)
        }
        actual_keys = [
            (model_order[item["model"]], UUID(item["pk"]).int)
            for item in first["objects"]
        ]
        self.assertEqual(actual_keys, sorted(actual_keys))

    def test_uuid_text_formats_identify_the_same_record(self):
        value = uuid4()
        first = {"model": System._meta.label_lower, "pk": str(value)}
        second = {"model": System._meta.label_lower, "pk": value.hex.upper()}
        self.assertEqual(_object_key(first), _object_key(second))

    def test_index_rejects_duplicate_ids_even_with_different_uuid_formats(self):
        snapshot = self.base_snapshot()
        duplicate = deepcopy(self.record(snapshot, System, self.system.pk))
        duplicate["pk"] = UUID(duplicate["pk"]).hex.upper()
        snapshot["objects"].append(duplicate)
        with self.assertRaises(ValidationError):
            _index_objects(snapshot)

    def test_merge_rejects_invalid_uuid(self):
        incoming = self.base_snapshot()
        self.record(incoming, System, self.system.pk)["pk"] = "not-a-uuid"
        with self.assertRaises(ValidationError):
            merge_snapshots(self.base_snapshot(), incoming)

    def test_duplicate_diagram_nodes_report_names_and_resolution(self):
        ground_truth, incoming, node_a, node_b = self.make_duplicate_nodes()
        with self.assertRaises(MergeConflictError) as captured:
            merge_snapshots(ground_truth, incoming)

        error = captured.exception
        self.assertEqual(error.code, "DUPLICATE_DIAGRAM_NODE")
        self.assertIn("Empty diagram", error.message)
        self.assertIn("Customer", error.message)
        self.assertTrue(error.resolution)
        self.assertEqual(
            set(error.details["object_ids"]), {str(node_a.pk), str(node_b.pk)}
        )
        self.assertEqual(error.to_dict()["code"], error.code)
        json.dumps(error.to_dict())  # Usable as an API response.

    def test_duplicate_diagram_edges_report_relation_and_resolution(self):
        base = self.base_snapshot()
        ground_truth = deepcopy(base)
        incoming = deepcopy(base)
        edge_a = Edge(diagram_id=self.diagram.pk, relation_id=self.relation.pk)
        edge_b = Edge(diagram_id=self.diagram.pk, relation_id=self.relation.pk)
        self.add_record(ground_truth, edge_a)
        self.add_record(incoming, edge_b)

        with self.assertRaises(MergeConflictError) as captured:
            merge_snapshots(ground_truth, incoming)

        error = captured.exception
        self.assertEqual(error.code, "DUPLICATE_DIAGRAM_EDGE")
        self.assertIn("Overview", error.message)
        self.assertIn("Customer", error.message)
        self.assertIn("Order", error.message)
        self.assertEqual(
            set(error.details["object_ids"]), {str(edge_a.pk), str(edge_b.pk)}
        )

    def test_generic_unique_constraint_reports_conflicting_values(self):
        base = self.base_snapshot()
        ground_truth = deepcopy(base)
        incoming = deepcopy(base)
        # Both use the same page and order, but different sections/UUIDs.
        first = PageSection(page_id=self.page.pk, section_id=self.section_a.pk, order=0)
        second = PageSection(page_id=self.page.pk, section_id=self.section_b.pk, order=0)
        self.add_record(ground_truth, first)
        self.add_record(incoming, second)

        with self.assertRaises(MergeConflictError) as captured:
            merge_snapshots(ground_truth, incoming)

        error = captured.exception
        self.assertEqual(error.code, "DUPLICATE_UNIQUE_VALUE")
        self.assertIn("Details", error.message)
        self.assertTrue(error.resolution)
        self.assertEqual(
            set(error.details["object_ids"]), {str(first.pk), str(second.pk)}
        )

    def test_missing_references_report_a_readable_conflict(self):
        # Simulate damaged stored data; normally an exported project is closed
        # under FK references, so an ordinary two-way union won't cause this.
        ground_truth = self.base_snapshot()
        incoming = deepcopy(ground_truth)
        self.drop_record(ground_truth, System, self.system.pk)
        self.drop_record(incoming, System, self.system.pk)

        with self.assertRaises(MergeConflictError) as captured:
            merge_snapshots(ground_truth, incoming)

        error = captured.exception
        self.assertEqual(error.code, "MISSING_REFERENCE")
        self.assertEqual(error.details["target_model"], System._meta.label_lower)
        self.assertEqual(error.details["target_id"], str(self.system.pk))
        self.assertIn("missing", error.message.lower())
        self.assertTrue(error.resolution)

    def test_incompatible_classifier_types_are_reported(self):
        ground_truth = self.base_snapshot()
        incoming = deepcopy(ground_truth)

        # B converts a class into an enum. A keeps it as a class.
        self.record(incoming, Classifier, self.customer.pk)["fields"]["type"] = "enum"
        self.drop_record(incoming, ClassClassifier, self.customer.pk)
        self.add_record(incoming, Enum(classifier_id=self.customer.pk, name="Status"))

        with self.assertRaises(MergeConflictError) as captured:
            merge_snapshots(ground_truth, incoming)

        error = captured.exception
        self.assertEqual(error.code, "INCOMPATIBLE_OBJECT_TYPE")
        self.assertEqual(error.details["object_id"], str(self.customer.pk))
        self.assertIn("incompatible", error.message.lower())

    def test_incompatible_relation_types_are_reported(self):
        from metadata.models import Composition

        ground_truth = self.base_snapshot()
        incoming = deepcopy(ground_truth)
        self.record(incoming, Relation, self.relation.pk)["fields"]["type"] = (
            "composition"
        )
        self.drop_record(incoming, Association, self.relation.pk)
        self.add_record(
            incoming,
            Composition(
                relation_id=self.relation.pk,
                multiplicity_id=self.multiplicity.pk,
                labels_id=self.labels.pk,
            ),
        )

        with self.assertRaises(MergeConflictError) as captured:
            merge_snapshots(ground_truth, incoming)

        error = captured.exception
        self.assertEqual(error.code, "INCOMPATIBLE_OBJECT_TYPE")
        self.assertEqual(error.details["object_id"], str(self.relation.pk))
        self.assertIn("relationship", error.message)

    def test_nullable_self_reference_is_preserved_in_union(self):
        ground_truth = self.base_snapshot()
        incoming = deepcopy(ground_truth)
        first = Classifier(system_id=self.system.pk, type="swimlane")
        second = Classifier(system_id=self.system.pk, type="swimlane")
        self.add_record(incoming, first)
        self.add_record(incoming, second)
        self.add_record(incoming, Swimlane(classifier_id=first.pk))
        self.add_record(
            incoming, Swimlane(classifier_id=second.pk, parent_id=first.pk)
        )

        merged = merge_snapshots(ground_truth, incoming)
        self.assertEqual(
            self.record(merged, Swimlane, second.pk)["fields"]["parent"],
            str(first.pk),
        )


class MergeReleasesTests(MergeFixtureMixin, TestCase):
    """Release persistence, project isolation, and restore integration."""

    def store_release(self, snapshot, name):
        return Release.objects.create(
            project=self.project,
            name=name,
            description="",
            release_notes=[],
            project_data=deepcopy(snapshot),
        )

    def test_merge_creates_one_new_release_with_metadata(self):
        ground_truth, incoming, diagram_a, diagram_b = (
            self.make_branches_with_diagrams()
        )
        release_a = self.store_release(ground_truth, "Version A")
        release_b = self.store_release(incoming, "Version B")
        before_count = Release.objects.count()

        merged = merge_releases(
            ground_truth_id=release_a.pk,
            incoming_id=release_b.pk,
            name="Merged A+B",
            description="Combined both diagrams",
            release_notes=["Reviewed by both users"],
        )

        self.assertEqual(Release.objects.count(), before_count + 1)
        self.assertEqual(merged.project_id, self.project.pk)
        self.assertEqual(merged.name, "Merged A+B")
        self.assertEqual(merged.description, "Combined both diagrams")
        self.assertEqual(merged.release_notes, ["Reviewed by both users"])
        self.record(merged.project_data, Diagram, diagram_a.pk)
        self.record(merged.project_data, Diagram, diagram_b.pk)

    def test_merge_does_not_change_live_project_or_current_release(self):
        active = create_release(self.project.pk, "Active")
        before = self.base_snapshot()
        ground_truth, incoming, _, _ = self.make_branches_with_diagrams()
        release_a = self.store_release(ground_truth, "A")
        release_b = self.store_release(incoming, "B")

        merge_releases(release_a.pk, release_b.pk, name="Merged")

        self.assertEqual(self.base_snapshot(), before)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_release_id, active.pk)

    def test_merge_does_not_modify_source_releases(self):
        ground_truth, incoming, _, _ = self.make_branches_with_diagrams()
        release_a = self.store_release(ground_truth, "A")
        release_b = self.store_release(incoming, "B")
        original_a, original_b = deepcopy(ground_truth), deepcopy(incoming)

        merge_releases(release_a.pk, release_b.pk, name="Merged")

        release_a.refresh_from_db()
        release_b.refresh_from_db()
        self.assertEqual(release_a.project_data, original_a)
        self.assertEqual(release_b.project_data, original_b)

    def test_merging_different_projects_raises_structured_conflict(self):
        ground_truth = self.store_release(self.base_snapshot(), "A")
        other_project = Project.objects.create(name="Unrelated project")
        other_release = Release.objects.create(
            project=other_project,
            name="Other version",
            project_data=snapshot_project(other_project.pk),
        )
        before_count = Release.objects.count()

        with self.assertRaises(MergeConflictError) as captured:
            merge_releases(ground_truth.pk, other_release.pk, name="Should fail")

        self.assertEqual(captured.exception.code, "DIFFERENT_PROJECTS")
        self.assertIn("different projects", captured.exception.message)
        self.assertEqual(Release.objects.count(), before_count)

    def test_merge_conflict_does_not_create_a_release(self):
        ground_truth, incoming, _, _ = self.make_duplicate_nodes()
        release_a = self.store_release(ground_truth, "A")
        release_b = self.store_release(incoming, "B")
        before_count = Release.objects.count()
        before_live = self.base_snapshot()

        with self.assertRaises(MergeConflictError) as captured:
            merge_releases(release_a.pk, release_b.pk, name="Should fail")

        self.assertEqual(captured.exception.code, "DUPLICATE_DIAGRAM_NODE")
        self.assertEqual(Release.objects.count(), before_count)
        self.assertEqual(self.base_snapshot(), before_live)

    def test_merged_release_can_be_restored_with_its_relationships(self):
        ground_truth, incoming, diagram_a, diagram_b = (
            self.make_branches_with_diagrams()
        )
        # A adds a new classifier and typed record, then places it on its diagram.
        new_classifier = Classifier(system_id=self.system.pk, type="class")
        self.add_record(ground_truth, new_classifier)
        self.add_record(
            ground_truth,
            ClassClassifier(classifier_id=new_classifier.pk, name="Invoice"),
        )
        new_node = Node(diagram_id=diagram_a.pk, classifier_id=new_classifier.pk)
        self.add_record(ground_truth, new_node)

        # B adds an edge to its diagram. It needs source and target nodes, too.
        self.add_record(
            incoming, Node(diagram_id=diagram_b.pk, classifier_id=self.customer.pk)
        )
        self.add_record(
            incoming, Node(diagram_id=diagram_b.pk, classifier_id=self.order.pk)
        )
        new_edge = Edge(diagram_id=diagram_b.pk, relation_id=self.relation.pk)
        self.add_record(incoming, new_edge)

        release_a = self.store_release(ground_truth, "A")
        release_b = self.store_release(incoming, "B")
        merged = merge_releases(release_a.pk, release_b.pk, name="Merged")

        # A successful merge must be loadable, not just a valid JSON blob.
        restored_project = restore_release(merged.pk, force=True)
        self.assertEqual(restored_project.pk, self.project.pk)
        self.assertEqual(self.base_snapshot(), merged.project_data)
        self.assertTrue(Diagram.objects.filter(pk=diagram_a.pk).exists())
        self.assertTrue(Diagram.objects.filter(pk=diagram_b.pk).exists())
        self.assertEqual(
            Node.objects.get(pk=new_node.pk).classifier_id, new_classifier.pk
        )
        self.assertEqual(
            Edge.objects.get(pk=new_edge.pk).relation_id, self.relation.pk
        )
        self.assertEqual(
            ClassClassifier.objects.get(pk=new_classifier.pk).name, "Invoice"
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_release_id, merged.pk)

    def test_merged_swimlane_tree_can_be_restored(self):
        ground_truth = self.base_snapshot()
        incoming = deepcopy(ground_truth)
        lane_a = Classifier(system_id=self.system.pk, type="swimlane")
        lane_b = Classifier(system_id=self.system.pk, type="swimlane")
        self.add_record(incoming, lane_a)
        self.add_record(incoming, lane_b)
        self.add_record(incoming, Swimlane(classifier_id=lane_a.pk))
        self.add_record(
            incoming, Swimlane(classifier_id=lane_b.pk, parent_id=lane_a.pk)
        )

        release_a = self.store_release(ground_truth, "A")
        release_b = self.store_release(incoming, "B")
        merged = merge_releases(release_a.pk, release_b.pk, name="Merged")
        restore_release(merged.pk, force=True)

        self.assertEqual(Swimlane.objects.get(pk=lane_b.pk).parent_id, lane_a.pk)
        self.assertEqual(self.base_snapshot(), merged.project_data)
