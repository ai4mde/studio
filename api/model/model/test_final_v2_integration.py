from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase

from llm.converter import convert_to_ai4mde
from llm.technical_validity import TechnicalValidityError
from metadata.models import ProvisionalCandidate, Project, System
from model.experiment_pipeline import _convert_candidate_graph, run_pipeline


def _candidate(project: Project, index: int):
    graph = {
        "nodes": [{"id": f"work-{index}", "type": "action", "name": "editable work"}],
        "edges": [],
    }
    return {
        "clean": graph,
        "ai4mde": convert_to_ai4mde(
            clean_model=graph,
            system_id=str(uuid4()),
            diagram_id=str(uuid4()),
            name=f"Candidate {index}",
            description="candidate",
            project_id=str(project.id),
        ),
        "technical_validity": {
            "technical_accepted": True,
            "normalization_applied": False,
            "normalizations": [],
            "dropped_edges": [],
            "quality_warnings": [],
            "conversion_result": "accepted",
            "import_result": "not_checked",
            "failure_reason": None,
        },
    }


class FinalV2PipelineIntegrationTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Final V2 integration")

    def test_behaviorally_imperfect_graph_is_accepted_with_soft_warnings(self):
        candidate = _convert_candidate_graph(
            {
                "nodes": [{"node_id": " work ", "type": "action", "name": "editable work"}],
                "edges": [],
            },
            system_id=str(uuid4()),
            diagram_id=str(uuid4()),
            name="Editable candidate",
            description="candidate",
            project_id=str(self.project.id),
        )

        report = candidate["technical_validity"]
        warning_codes = {warning["code"] for warning in report["quality_warnings"]}
        self.assertTrue(report["technical_accepted"])
        self.assertTrue(report["normalization_applied"])
        self.assertEqual(report["conversion_result"], "accepted")
        self.assertIn("missing_initial_node", warning_codes)
        self.assertIn("missing_final_node", warning_codes)

    def test_provisional_candidate_set_rolls_back_as_one_request(self):
        candidates = [_candidate(self.project, index) for index in range(1, 4)]
        original_bulk_create = ProvisionalCandidate.objects.bulk_create

        def create_one_then_fail(objects, *args, **kwargs):
            original_bulk_create(objects[:1], *args, **kwargs)
            raise RuntimeError("candidate persistence failed")

        with patch(
            "model.experiment_pipeline.generate_and_convert_candidates",
            return_value=candidates,
        ), patch(
            "model.experiment_pipeline.ProvisionalCandidate.objects.bulk_create",
            side_effect=create_one_then_fail,
        ):
            with self.assertRaisesMessage(RuntimeError, "candidate persistence failed"):
                run_pipeline(
                    "Perform editable work.",
                    "refinement",
                    project_id=str(self.project.id),
                    pipeline_profile="semantic_deterministic",
                )

        self.assertEqual(ProvisionalCandidate.objects.filter(project=self.project).count(), 0)
        self.assertEqual(System.objects.filter(project=self.project).count(), 0)

    def test_official_import_failure_is_reported_as_technical_failure(self):
        graph = {
            "nodes": [{"id": "work", "type": "action", "name": "editable work"}],
            "edges": [],
        }
        debug_bundle = {"parsed": graph, "executed_stages": [], "stage_artifacts": {}}

        with patch(
            "model.experiment_pipeline.generate_activity_model",
            return_value=debug_bundle,
        ), patch(
            "model.experiment_pipeline.import_to_ai4mde",
            side_effect=ValueError("Studio import rejected payload"),
        ):
            with self.assertRaisesMessage(TechnicalValidityError, "failed AI4MDE import"):
                run_pipeline(
                    "Perform editable work.",
                    "baseline",
                    project_id=str(self.project.id),
                    pipeline_profile="semantic_deterministic",
                )

        self.assertEqual(System.objects.filter(project=self.project).count(), 0)
