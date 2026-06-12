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
                    "pipeline_profile": "both_agents",
                    "enable_sketch_review_agent": False,
                    "enable_prompted_sketch_repair_agent": True,
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["project_id"], str(self.project.id))
        self.assertEqual(payload["system_id"], str(self.system.id))
        self.assertEqual(payload["name"], "Candidate System Refined")
        self.assertEqual(payload["refinement_instruction"], "Add a confirmation step.")
        self.assertEqual(payload["pipeline_profile"], "both_agents")
        self.assertFalse(payload["enable_sketch_review_agent"])
        self.assertTrue(payload["enable_prompted_sketch_repair_agent"])
        self.assertTrue(payload["enable_graph_repair_agent"])

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
        self.assertEqual(kwargs["pipeline_profile"], "both_agents")
        self.assertFalse(kwargs["enable_sketch_review_agent"])
        self.assertTrue(kwargs["enable_prompted_sketch_repair_agent"])
        self.assertTrue(kwargs["enable_graph_repair_agent"])

    def test_generate_model_endpoint_forwards_pipeline_profile_configuration(self):
        with patch(
            "model.experiment_pipeline.run_pipeline",
            return_value={
                "session_id": "s1",
                "project_id": str(self.project.id),
                "mode": "baseline",
                "pipeline_profile": "stable",
                "use_experimental_compiler": False,
                "enable_sketch_review_agent": True,
                "enable_prompted_sketch_repair_agent": True,
                "enable_graph_repair_agent": False,
                "systems": [],
            },
        ) as mock_run:
            response = self.client.post(
                "/api/v1/generate-model",
                data={
                    "process_text": "Receive request, validate it, send confirmation.",
                    "mode": "baseline",
                    "pipeline_profile": "stable",
                    "enable_sketch_review_agent": True,
                    "enable_prompted_sketch_repair_agent": True,
                    "enable_graph_repair_agent": False,
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["enable_sketch_review_agent"])
        self.assertTrue(payload["enable_prompted_sketch_repair_agent"])
        self.assertFalse(payload["enable_graph_repair_agent"])

        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs["pipeline_profile"], "stable")
        self.assertTrue(kwargs["enable_sketch_review_agent"])
        self.assertTrue(kwargs["enable_prompted_sketch_repair_agent"])
        self.assertFalse(kwargs["enable_graph_repair_agent"])

    def test_generate_model_endpoint_forwards_experimental_compiler_flag(self):
        with patch(
            "model.experiment_pipeline.run_pipeline",
            return_value={
                "session_id": "s1",
                "project_id": str(self.project.id),
                "mode": "baseline",
                "pipeline_profile": "stable",
                "use_experimental_compiler": True,
                "enable_sketch_review_agent": False,
                "enable_graph_repair_agent": False,
                "systems": [],
            },
        ) as mock_run:
            response = self.client.post(
                "/api/v1/generate-model",
                data={
                    "process_text": "Receive request, validate it, send confirmation.",
                    "mode": "baseline",
                    "use_experimental_compiler": True,
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["use_experimental_compiler"])

        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        self.assertTrue(kwargs["use_experimental_compiler"])

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


class ExperimentPipelineCompilerTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Compiler Project",
            description="Testing experimental compiler pipeline.",
        )

    def test_run_pipeline_uses_experimental_compiler_for_baseline(self):
        clean_model = {
            "nodes": [
                {"id": "n1", "type": "initial"},
                {"id": "n2", "type": "action", "name": "Validate request"},
                {"id": "n3", "type": "final"},
            ],
            "edges": [
                {"source": "n1", "target": "n2", "type": "control"},
                {"source": "n2", "target": "n3", "type": "control"},
            ],
        }

        with patch(
            "model.experiment_pipeline.model_activity_with_experimental_compiler",
            return_value=clean_model,
        ) as mock_compiler:
            from model.experiment_pipeline import run_pipeline

            payload = run_pipeline(
                "Receive request, validate it, send confirmation.",
                "baseline",
                project_id=str(self.project.id),
                use_experimental_compiler=True,
                enable_prompted_sketch_repair_agent=True,
            )

        self.assertTrue(payload["use_experimental_compiler"])
        self.assertEqual(payload["mode"], "baseline")
        self.assertEqual(len(payload["systems"]), 1)
        mock_compiler.assert_called_once_with(
            "Receive request, validate it, send confirmation.",
            use_sketch_review_agent=False,
            use_prompted_sketch_repair_agent=True,
        )

    def test_run_pipeline_rejects_experimental_compiler_for_refinement(self):
        from model.experiment_pipeline import run_pipeline

        with self.assertRaisesMessage(
            ValueError,
            "experimental compiler is currently supported only for baseline mode",
        ):
            run_pipeline(
                "Receive request, validate it, send confirmation.",
                "refinement",
                project_id=str(self.project.id),
                use_experimental_compiler=True,
            )
