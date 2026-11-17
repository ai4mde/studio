"""
    Tests for the routes added during the frontend migration:
    deleting a release, exporting a project, and exporting/importing systems.
"""
import json

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from config.auth import create_token
from diagram.models import Diagram, Node
from metadata.models import (
    Classifier,
    Multiplicity,
    Project,
    Relation,
    Release,
    System,
)
from metadata.services.versioning import create_release


METADATA_URL = "/api/v1/metadata"


class AddedVersioningRoutesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.project = Project.objects.create(name="Shop")
        cls.orders = System.objects.create(project=cls.project, name="Orders")
        cls.billing = System.objects.create(project=cls.project, name="Billing")

        cls.order = Classifier.create(
            system_id=cls.orders.pk, classifier_type="class", data={"name": "Order"}
        )
        cls.line = Classifier.create(
            system_id=cls.orders.pk, classifier_type="class", data={"name": "OrderLine"}
        )
        cls.relation = Relation.create(
            system_id=cls.orders.pk,
            source_id=cls.order.pk,
            target_id=cls.line.pk,
            relation_type="association",
            data={
                "label": "has",
                "multiplicity": {
                    "source_lower": 1,
                    "source_upper": 1,
                    "target_lower": 0,
                    "target_upper": None,
                },
            },
        )
        cls.diagram = Diagram.objects.create(system=cls.orders, name="Orders", type="classes")
        Node.objects.create(diagram=cls.diagram, classifier=cls.order)
        Node.objects.create(diagram=cls.diagram, classifier=cls.line)

        Classifier.create(
            system_id=cls.billing.pk, classifier_type="class", data={"name": "Invoice"}
        )

        cls.target = Project.objects.create(name="Target")

        get_user_model().objects.create_user(
            username="added-routes-tester", password="test-password"
        )

    def setUp(self):
        _, token = create_token("added-routes-tester", "test-password")
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    def _upload(self, url, data, **fields):
        file = SimpleUploadedFile(
            "upload.json",
            json.dumps(data).encode("utf-8"),
            content_type="application/json",
        )
        return self.client.post(url, data={"file": file, **fields})

    def _export_orders(self):
        response = self.client.get(
            f"{METADATA_URL}/projects/{self.project.pk}/systems/export/",
            {"system_ids": [str(self.orders.pk)]},
        )
        self.assertEqual(response.status_code, 200, response.content)
        return json.loads(response.content)

    # Deleting a release

    def test_delete_release(self):
        release = create_release(self.project.pk, "v1")

        response = self.client.delete(f"{METADATA_URL}/releases/{release.pk}/")

        self.assertEqual(response.status_code, 204, response.content)
        self.assertFalse(Release.objects.filter(pk=release.pk).exists())
        self.project.refresh_from_db()
        self.assertIsNone(self.project.current_release)

    # Exporting a project

    def test_project_export_can_be_imported_again(self):
        response = self.client.get(f"{METADATA_URL}/projects/{self.project.pk}/export/")
        self.assertEqual(response.status_code, 200, response.content)
        snapshot = json.loads(response.content)
        self.assertEqual(snapshot["project_id"], str(self.project.pk))

        Project.objects.filter(pk=self.project.pk).delete()

        response = self._upload(f"{METADATA_URL}/projects/import/", snapshot)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            set(System.objects.filter(project_id=self.project.pk).values_list("name", flat=True)),
            {"Orders", "Billing"},
        )

    # Exporting systems

    def test_systems_export_only_contains_the_selected_systems(self):
        data = self._export_orders()
        models = {obj["model"] for obj in data["objects"]}
        pks = {obj["pk"] for obj in data["objects"]}

        self.assertNotIn("metadata.project", models)
        self.assertIn(str(self.orders.pk), pks)
        self.assertNotIn(str(self.billing.pk), pks)
        self.assertIn(str(self.relation.pk), pks)
        self.assertIn(str(self.diagram.pk), pks)
        # The association's multiplicity has no link to a system, but is needed
        self.assertIn("metadata.multiplicity", models)
        self.assertNotIn(
            "Invoice",
            [obj["fields"].get("name") for obj in data["objects"]],
        )

    def test_systems_export_rejects_systems_of_another_project(self):
        other = System.objects.create(project=self.target, name="Elsewhere")

        response = self.client.get(
            f"{METADATA_URL}/projects/{self.project.pk}/systems/export/",
            {"system_ids": [str(other.pk)]},
        )

        self.assertEqual(response.status_code, 400, response.content)

    # Importing systems

    def test_import_systems_into_another_project(self):
        data = self._export_orders()
        multiplicities_before = Multiplicity.objects.count()

        response = self._upload(
            f"{METADATA_URL}/releases/import_systems/{self.target.pk}/",
            data,
            name="With orders",
            release_notes=json.dumps(["Imported the orders system"]),
        )

        self.assertEqual(response.status_code, 200, response.content)
        imported = System.objects.get(project=self.target, name="Orders")
        self.assertNotEqual(imported.pk, self.orders.pk)
        self.assertEqual(
            Classifier.objects.filter(system=imported).count(),
            Classifier.objects.filter(system=self.orders).count(),
        )
        self.assertEqual(Relation.objects.filter(system=imported).count(), 1)
        self.assertEqual(Node.objects.filter(diagram__system=imported).count(), 2)
        self.assertEqual(Multiplicity.objects.count(), multiplicities_before + 1)

        release = Release.objects.get(project=self.target, name="With orders")
        self.assertEqual(release.release_notes, ["Imported the orders system"])

        # The source project is untouched
        self.assertEqual(System.objects.filter(project=self.project).count(), 2)

    def test_import_systems_twice_creates_two_copies(self):
        data = self._export_orders()
        url = f"{METADATA_URL}/releases/import_systems/{self.target.pk}/"

        self.assertEqual(self._upload(url, data, name="First").status_code, 200)
        self.assertEqual(self._upload(url, data, name="Second").status_code, 200)

        self.assertEqual(
            System.objects.filter(project=self.target, name="Orders").count(), 2
        )

    def test_import_systems_rejects_a_project_file(self):
        project_file = json.loads(
            self.client.get(f"{METADATA_URL}/projects/{self.project.pk}/export/").content
        )

        response = self._upload(
            f"{METADATA_URL}/releases/import_systems/{self.target.pk}/",
            project_file,
            name="Wrong file",
        )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertFalse(System.objects.filter(project=self.target).exists())
