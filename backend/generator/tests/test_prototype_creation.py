import json
from copy import deepcopy
from unittest.mock import patch

from django.test import TestCase

from generator.api.schemas.prototype import PrototypeCreate
from generator.models import Prototype
from generator.services.prototype import (
    PROTOTYPE_API_URL,
    calculate_database_hash,
    create_prototype,
)
from metadata.models import Project, System


class PrototypeCreationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        project = Project.objects.create(name="Test project")
        cls.system = System.objects.create(name="Test system", project=project)

    @patch("generator.services.prototype.requests.post")
    def test_create_builds_metadata_stores_hash_and_calls_generator(self, post):
        post.return_value.status_code = 200
        payload = PrototypeCreate(
            name="Test prototype",
            description="A generated prototype",
            system_id=self.system.id,
            interface_ids=[],
            use_authentication=True,
            database_prototype_name="previous-prototype",
        )

        prototype = create_prototype(payload)
        prototype.refresh_from_db()

        self.assertEqual(Prototype.objects.count(), 1)
        self.assertEqual(prototype.system_id, self.system.id)
        self.assertEqual(prototype.name, "Test prototype")
        self.assertEqual(prototype.description, "A generated prototype")
        self.assertEqual(
            prototype.metadata,
            {"diagrams": [], "interfaces": [], "use_authentication": True},
        )
        self.assertEqual(len(prototype.database_hash), 64)
        self.assertEqual(
            prototype.database_hash,
            calculate_database_hash(self.system, prototype.metadata),
        )

        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args, (f"{PROTOTYPE_API_URL}/generate",))
        self.assertEqual(kwargs["json"], {
            "id": str(prototype.id),
            "name": "Test prototype",
            "system": str(self.system.id),
            "metadata": json.dumps(prototype.metadata),
            "database_prototype_name": "previous-prototype",
        })

    def test_hash_is_order_independent_without_modifying_metadata(self):
        metadata = {
            "diagrams": [{
                "type": "class",
                "nodes": [{
                    "classifier": {
                        "id": "class-1",
                        "type": "class",
                        "data": {
                            "attributes": [{"id": "b"}, {"id": "a"}],
                            "operations": [{"id": "d"}, {"id": "c"}],
                        },
                    },
                }],
                "edges": [],
            }],
        }
        original = deepcopy(metadata)
        first_hash = calculate_database_hash(self.system, metadata)
        self.assertEqual(metadata, original)

        reordered = deepcopy(metadata)
        classifier_data = reordered["diagrams"][0]["nodes"][0]["classifier"]["data"]
        classifier_data["attributes"].reverse()
        classifier_data["operations"].reverse()
        self.assertEqual(first_hash, calculate_database_hash(self.system, reordered))