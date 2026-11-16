
from copy import deepcopy
from uuid import uuid4

from django.test import TestCase

from diagram.models import Diagram, Edge, Node
from metadata.models import (
    Association,
    Attribute,
    Classifier,
    Project,
    Relation,
    System,
)
from metadata.models.types import DataType

from prose.services.model_creation import add_to_diagram


class ModelCreationTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.system = System.objects.create(
            project=self.project,
            name="Test System",
        )
        self.diagram = Diagram.objects.create(
            system=self.system,
            name="Class Diagram",
            type="class",
        )

        self.classifiers = [
            {
                "id": str(uuid4()),
                "type": "class",
                "name": "Customer",
                "attributes": [
                    {
                        "name": "email",
                        "type": DataType.STRING,
                        "derived": False,
                        "description": None,
                        "body": None,
                    }
                ],
            },
            {
                "id": str(uuid4()),
                "type": "class",
                "name": "Order",
                "attributes": [],
            },
        ]

        self.relations = [
            {
                "id": str(uuid4()),
                "type": "association",
                "source": self.classifiers[0]["id"],
                "target": self.classifiers[1]["id"],
                "derived": False,
                "label": "",
                "multiplicity": {
                    "source_lower": 1,
                    "source_upper": 1,
                    "target_lower": 0,
                    "target_upper": None,
                },
            }
        ]

    def test_creates_classifiers_attributes_nodes_and_edges(self):
        result = add_to_diagram(
            self.diagram,
            self.classifiers,
            self.relations,
        )

        self.assertEqual(result.pk, self.diagram.pk)
        self.assertEqual(Classifier.objects.filter(system=self.system).count(), 2)
        self.assertEqual(Attribute.objects.count(), 1)
        self.assertEqual(Relation.objects.filter(system=self.system).count(), 1)
        self.assertEqual(Node.objects.filter(diagram=self.diagram).count(), 2)
        self.assertEqual(Edge.objects.filter(diagram=self.diagram).count(), 1)

        customer = Classifier.objects.get(
            system=self.system,
            classclassifier__name="Customer",
        )
        attribute = Attribute.objects.get(uml_class=customer.data)

        self.assertEqual(attribute.name, "email")
        self.assertEqual(attribute.type, DataType.STRING)

    def test_relation_connects_correct_classifiers(self):
        add_to_diagram(self.diagram, self.classifiers, self.relations)

        customer = Classifier.objects.get(
            classclassifier__name="Customer",
            system=self.system,
        )
        order = Classifier.objects.get(
            classclassifier__name="Order",
            system=self.system,
        )

        relation = Relation.objects.get(system=self.system)

        self.assertEqual(relation.source, customer)
        self.assertEqual(relation.target, order)
        self.assertEqual(relation.type, "association")

        association = Association.objects.get(relation=relation)

        self.assertEqual(association.multiplicity.source_lower, 1)
        self.assertEqual(association.multiplicity.source_upper, 1)
        self.assertEqual(association.multiplicity.target_lower, 0)
        self.assertIsNone(association.multiplicity.target_upper)

    def test_repeated_import_does_not_create_duplicates(self):
        add_to_diagram(self.diagram, self.classifiers, self.relations)
        add_to_diagram(self.diagram, self.classifiers, self.relations)

        self.assertEqual(Classifier.objects.filter(system=self.system).count(), 2)
        self.assertEqual(Attribute.objects.count(), 1)
        self.assertEqual(Relation.objects.filter(system=self.system).count(), 1)
        self.assertEqual(Node.objects.filter(diagram=self.diagram).count(), 2)
        self.assertEqual(Edge.objects.filter(diagram=self.diagram).count(), 1)

    def test_existing_metadata_reused_in_another_diagram(self):
        add_to_diagram(self.diagram, self.classifiers, self.relations)

        other_diagram = Diagram.objects.create(
            system=self.system,
            name="Second Diagram",
            type="class",
        )

        # Simulate a new LLM response with different temporary UUIDs.
        classifiers = deepcopy(self.classifiers)
        relations = deepcopy(self.relations)

        old_ids = [item["id"] for item in classifiers]

        for classifier in classifiers:
            classifier["id"] = str(uuid4())

        relations[0]["id"] = str(uuid4())
        relations[0]["source"] = classifiers[0]["id"]
        relations[0]["target"] = classifiers[1]["id"]

        self.assertNotEqual(old_ids[0], classifiers[0]["id"])

        add_to_diagram(other_diagram, classifiers, relations)

        # Existing system metadata should be reused.
        self.assertEqual(Classifier.objects.filter(system=self.system).count(), 2)
        self.assertEqual(Attribute.objects.count(), 1)
        self.assertEqual(Relation.objects.filter(system=self.system).count(), 1)

        # Each diagram gets its own visual nodes and edges.
        self.assertEqual(other_diagram.nodes.count(), 2)
        self.assertEqual(other_diagram.edges.count(), 1)

        self.assertEqual(
            set(self.diagram.nodes.values_list("classifier_id", flat=True)),
            set(other_diagram.nodes.values_list("classifier_id", flat=True)),
        )

        self.assertEqual(
            self.diagram.edges.get().relation_id,
            other_diagram.edges.get().relation_id,
        )

    def test_invalid_relation_rolls_back_all_changes(self):
        relations = deepcopy(self.relations)
        relations[0]["target"] = str(uuid4())

        with self.assertRaises(ValueError):
            add_to_diagram(self.diagram, self.classifiers, relations)

        self.assertEqual(Classifier.objects.filter(system=self.system).count(), 0)
        self.assertEqual(Attribute.objects.count(), 0)
        self.assertEqual(Relation.objects.filter(system=self.system).count(), 0)
        self.assertEqual(Node.objects.filter(diagram=self.diagram).count(), 0)
        self.assertEqual(Edge.objects.filter(diagram=self.diagram).count(), 0)

    def test_duplicate_classifier_ids_rejected(self):
        classifiers = deepcopy(self.classifiers)
        classifiers[1]["id"] = classifiers[0]["id"]

        with self.assertRaises(ValueError):
            add_to_diagram(self.diagram, classifiers, self.relations)

        self.assertEqual(Classifier.objects.filter(system=self.system).count(), 0)
        self.assertEqual(Node.objects.filter(diagram=self.diagram).count(), 0)
