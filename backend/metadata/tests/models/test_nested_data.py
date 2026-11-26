
from django.core.exceptions import ValidationError
from django.test import TestCase

from metadata.models import (
    Classifier,
    EndpointLabel,
    Enum,
    EnumLiteral,
    Multiplicity,
    Project,
    Relation,
    System,
)


class NestedDataTests(TestCase):
    def setUp(self):
        project = Project.objects.create(name="Test Project")
        self.system = System.objects.create(
            project=project,
            name="Test System",
        )

        self.source = Classifier.create(
            system_id=self.system.id,
            classifier_type="class",
            data={"name": "Source"},
        )
        self.target = Classifier.create(
            system_id=self.system.id,
            classifier_type="class",
            data={"name": "Target"},
        )

    def test_create_enum_with_literals(self):
        enum = Classifier.create(
            system_id=self.system.id,
            classifier_type="enum",
            data={
                "name": "Status",
                "literals": [
                    {"value": "PENDING", "order": 0},
                    {"value": "APPROVED", "order": 1},
                ],
            },
        )

        literals = list(
            enum.data.literals.values_list("value", flat=True)
        )

        self.assertEqual(literals, ["PENDING", "APPROVED"])
        self.assertEqual(EnumLiteral.objects.count(), 2)

    def test_create_association(self):
        relation = Relation.create(
            system_id=self.system.id,
            source_id=self.source.id,
            target_id=self.target.id,
            relation_type="association",
            data={
                "multiplicity": {
                    "source_lower": 1,
                    "source_upper": 1,
                    "target_lower": 0,
                    "target_upper": None,
                },
                "labels": {
                    "source": "owner",
                    "target": "items",
                },
            },
        )

        association = relation.data

        self.assertEqual(association.multiplicity.source_lower, 1)
        self.assertEqual(association.multiplicity.target_lower, 0)
        self.assertIsNone(association.multiplicity.target_upper)
        self.assertEqual(association.labels.source, "owner")
        self.assertEqual(association.labels.target, "items")

        self.assertEqual(Multiplicity.objects.count(), 1)
        self.assertEqual(EndpointLabel.objects.count(), 1)

    def test_create_composition_without_labels(self):
        relation = Relation.create(
            system_id=self.system.id,
            source_id=self.source.id,
            target_id=self.target.id,
            relation_type="composition",
            data={
                "multiplicity": {
                    "source_lower": 1,
                    "source_upper": 1,
                    "target_lower": 0,
                    "target_upper": None,
                },
            },
        )

        composition = relation.data

        self.assertEqual(composition.multiplicity.source_lower, 1)
        self.assertEqual(composition.multiplicity.target_lower, 0)

        # Labels should be created automatically when omitted.
        self.assertEqual(composition.labels.source, "")
        self.assertEqual(composition.labels.target, "")

        self.assertEqual(Multiplicity.objects.count(), 1)
        self.assertEqual(EndpointLabel.objects.count(), 1)

    def test_update_association_nested_data(self):
        relation = Relation.create(
            system_id=self.system.id,
            source_id=self.source.id,
            target_id=self.target.id,
            relation_type="association",
            data={
                "multiplicity": {
                    "source_lower": 1,
                    "source_upper": 1,
                    "target_lower": 0,
                    "target_upper": None,
                },
                "labels": {
                    "source": "owner",
                    "target": "items",
                },
            },
        )

        multiplicity_id = relation.data.multiplicity_id
        labels_id = relation.data.labels_id

        relation.update(data={
            "multiplicity": {"target_lower": 1},
            "labels": {"target": "updated"},
        })

        association = Relation.objects.get(pk=relation.pk).data

        # Existing records were updated
        self.assertEqual(association.multiplicity_id, multiplicity_id)
        self.assertEqual(association.labels_id, labels_id)

        # Changed values
        self.assertEqual(association.multiplicity.target_lower, 1)
        self.assertEqual(association.labels.target, "updated")

        # Unchanged values
        self.assertEqual(association.multiplicity.source_lower, 1)
        self.assertEqual(association.labels.source, "owner")

        # No additional records were created
        self.assertEqual(Multiplicity.objects.count(), 1)
        self.assertEqual(EndpointLabel.objects.count(), 1)

    def test_enum_creation_rollback(self):
        with self.assertRaises(ValidationError):
            Classifier.create(
                system_id=self.system.id,
                classifier_type="enum",
                data={
                    "name": "Status",
                    "literals": [
                        {"value": "PENDING", "order": 0},
                        {"value": "APPROVED", "order": -1},
                    ],
                },
            )

        self.assertFalse(Enum.objects.filter(name="Status").exists())
        self.assertEqual(EnumLiteral.objects.count(), 0)

    def test_relation_creation_rollback(self):
        for relation_type in ("association", "composition"):
            with self.subTest(relation_type=relation_type):
                with self.assertRaises(ValidationError):
                    Relation.create(
                        system_id=self.system.id,
                        source_id=self.source.id,
                        target_id=self.target.id,
                        relation_type=relation_type,
                        data={
                            "label": "x" * 256,  # Exceeds max_length=255
                            "multiplicity": {
                                "source_lower": 1,
                                "source_upper": 1,
                                "target_lower": 0,
                                "target_upper": None,
                            },
                            "labels": {
                                "source": "owner",
                                "target": "items",
                            },
                        },
                    )

                self.assertEqual(Relation.objects.count(), 0)
                self.assertEqual(Multiplicity.objects.count(), 0)
                self.assertEqual(EndpointLabel.objects.count(), 0)

    def test_update_composition_nested_data(self):
        relation = Relation.create(
            system_id=self.system.id,
            source_id=self.source.id,
            target_id=self.target.id,
            relation_type="composition",
            data={
                "multiplicity": {
                    "source_lower": 1,
                    "source_upper": 1,
                    "target_lower": 0,
                    "target_upper": None,
                },
            },
        )

        multiplicity_id = relation.data.multiplicity_id
        labels_id = relation.data.labels_id

        relation.update(data={
            "multiplicity": {"target_lower": 1},
            "labels": {"target": "parts"},
        })

        composition = Relation.objects.get(pk=relation.pk).data

        self.assertEqual(composition.multiplicity_id, multiplicity_id)
        self.assertEqual(composition.labels_id, labels_id)
        self.assertEqual(composition.multiplicity.target_lower, 1)
        self.assertEqual(composition.labels.target, "parts")

        self.assertEqual(Multiplicity.objects.count(), 1)
        self.assertEqual(EndpointLabel.objects.count(), 1)