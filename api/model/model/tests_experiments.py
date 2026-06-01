from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase
from llm.converter import convert_to_ai4mde
from metadata.models import Project, System


class ExperimentEndpointTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Refinement Project",
            description="Testing refinement experiment endpoint.",
        )
        self.system = System.objects.create(
            name="Candidate System",
            project=self.project,
            description="Initial candidate imported into the project.",
        )

    def test_refine_model_endpoint_updates_selected_system(self):
        refined_export = convert_to_ai4mde(
            clean_model={
                "nodes": [
                    {"id": "n1", "type": "initial"},
                    {"id": "n2", "type": "action", "name": "Validate request"},
                    {"id": "n3", "type": "action", "name": "Send confirmation"},
                    {"id": "n4", "type": "final"},
                ],
                "edges": [
                    {"source": "n1", "target": "n2", "type": "control"},
                    {"source": "n2", "target": "n3", "type": "control"},
                    {"source": "n3", "target": "n4", "type": "control"},
                ],
            },
            system_id=str(self.system.id),
            diagram_id=str(uuid4()),
            name="Candidate System Refined",
            description="Refined candidate",
            project_id=str(self.project.id),
        )

        with patch(
            "model.experiment_pipeline.refine_activity_model",
            return_value=refined_export,
        ) as mock_refine:
            response = self.client.post(
                "/api/v1/refine-model",
                data={
                    "process_text": "Receive request, validate it, send confirmation.",
                    "selected_system_id": str(self.system.id),
                    "refinement_instruction": "Add a confirmation step.",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["project_id"], str(self.project.id))
        self.assertEqual(payload["system_id"], str(self.system.id))
        self.assertEqual(payload["name"], "Candidate System Refined")
        self.assertEqual(payload["refinement_instruction"], "Add a confirmation step.")

        self.system.refresh_from_db()
        self.assertEqual(self.system.name, "Candidate System Refined")
        self.assertEqual(self.system.diagrams.count(), 1)
        self.assertEqual(self.system.classifiers.count(), 4)
        self.assertEqual(self.system.relations.count(), 3)

        mock_refine.assert_called_once()
        _, kwargs = mock_refine.call_args
        self.assertEqual(
            kwargs["process_text"],
            "Receive request, validate it, send confirmation.",
        )
        self.assertEqual(
            kwargs["refinement_instruction"],
            "Add a confirmation step.",
        )
        self.assertEqual(kwargs["current_model"]["id"], str(self.system.id))

    def test_refine_model_endpoint_rejects_unknown_system(self):
        response = self.client.post(
            "/api/v1/refine-model",
            data={
                "process_text": "x",
                "selected_system_id": str(uuid4()),
                "refinement_instruction": "y",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("does not exist", response.json()["error"])
