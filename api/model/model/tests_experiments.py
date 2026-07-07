from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase
from llm.converter import convert_to_ai4mde
from metadata.models import (
    Classifier,
    Project,
    System,
    SystemGenerationArtifacts,
    SystemRevision,
    create_system_revision,
    get_current_revision,
    get_semantic_sketch_plan,
    get_topology_artifact,
    persist_semantic_generation_artifacts,
)


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

    def _import_linear_system_and_create_baseline_revision(
        self,
        *,
        action_name: str = "Review Request",
    ):
        clean_model = {
            "nodes": [
                {"id": "n1", "type": "initial"},
                {"id": "n2", "type": "action", "name": action_name},
                {"id": "n3", "type": "final"},
            ],
            "edges": [
                {"source": "n1", "target": "n2", "type": "control"},
                {"source": "n2", "target": "n3", "type": "control"},
            ],
        }
        exported = convert_to_ai4mde(
            clean_model=clean_model,
            system_id=str(self.system.id),
            diagram_id=str(uuid4()),
            name=str(self.system.name),
            description=str(self.system.description),
            project_id=str(self.project.id),
        )
        self.project.import_systems_from_json(exported)
        self.system.refresh_from_db()
        revision = create_system_revision(
            system_id=str(self.system.id),
            process_text="Receive request, review it, then finish.",
            pipeline_profile="semantic_deterministic",
            activity_graph=clean_model,
            ai4mde_export=exported,
            topology_artifact={"structures": []},
            semantic_sketch_plan={
                "root_actions": [{"slot_id": "ROOT_START", "action": action_name}],
                "branch_plans": [],
            },
            revision_origin=SystemRevision.REVISION_ORIGIN_BASELINE,
        )
        return revision

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

    def test_generate_model_endpoint_defaults_to_semantic_deterministic_profile(self):
        with patch(
            "model.experiment_pipeline.run_pipeline",
            return_value={
                "session_id": "s1",
                "project_id": str(self.project.id),
                "mode": "baseline",
                "pipeline_profile": "semantic_deterministic",
                "use_experimental_compiler": False,
                "enable_sketch_review_agent": False,
                "enable_prompted_sketch_repair_agent": False,
                "enable_graph_repair_agent": False,
                "systems": [],
            },
        ) as mock_run:
            response = self.client.post(
                "/api/v1/generate-model",
                data={
                    "process_text": "Receive request, validate it, send confirmation.",
                    "mode": "baseline",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs["pipeline_profile"], "semantic_deterministic")

    def test_generate_model_endpoint_accepts_semantic_deterministic_profile(self):
        with patch(
            "model.experiment_pipeline.run_pipeline",
            return_value={
                "session_id": "s1",
                "project_id": str(self.project.id),
                "mode": "baseline",
                "pipeline_profile": "semantic_deterministic",
                "use_experimental_compiler": False,
                "enable_sketch_review_agent": False,
                "enable_prompted_sketch_repair_agent": False,
                "enable_graph_repair_agent": False,
                "systems": [],
            },
        ) as mock_run:
            response = self.client.post(
                "/api/v1/generate-model",
                data={
                    "process_text": "Receive request, validate it, send confirmation.",
                    "mode": "baseline",
                    "pipeline_profile": "semantic_deterministic",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["pipeline_profile"], "semantic_deterministic")

        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs["pipeline_profile"], "semantic_deterministic")

    def test_generate_model_endpoint_supports_summary_response_mode(self):
        with patch(
            "model.experiment_pipeline.run_pipeline",
            return_value={
                "session_id": "s1",
                "project_id": str(self.project.id),
                "mode": "baseline",
                "pipeline_profile": "semantic_deterministic",
                "use_experimental_compiler": False,
                "enable_sketch_review_agent": False,
                "enable_prompted_sketch_repair_agent": False,
                "enable_graph_repair_agent": False,
                "systems": [
                    {
                        "system_id": "sys1",
                        "activity_graph": {"nodes": [], "edges": []},
                        "ai4mde": [{"id": "sys1"}],
                    }
                ],
            },
        ) as mock_run:
            response = self.client.post(
                "/api/v1/generate-model",
                data={
                    "process_text": "Receive request, validate it, send confirmation.",
                    "mode": "baseline",
                    "pipeline_profile": "semantic_deterministic",
                    "response_mode": "summary",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            payload,
            {
                "session_id": "s1",
                "project_id": str(self.project.id),
                "mode": "baseline",
                "pipeline_profile": "semantic_deterministic",
            },
        )
        mock_run.assert_called_once()

    def test_project_delete_cascades_system_revisions(self):
        project = Project.objects.create(
            name="Cascade Delete Project",
            description="Ensures revision persistence does not break project deletion.",
        )
        system = System.objects.create(
            name="Cascade System",
            project=project,
            description="System attached to the project.",
        )
        revision = SystemRevision.objects.create(
            system=system,
            revision_index=0,
            process_text="Start, review, end.",
            pipeline_profile="semantic_deterministic",
            activity_graph={"nodes": [], "edges": []},
            ai4mde_export={"id": str(system.id)},
        )
        system.current_revision = revision
        system.save(update_fields=["current_revision"])

        project_id = project.id
        system_id = system.id
        revision_id = revision.id

        project.delete()

        self.assertFalse(Project.objects.filter(id=project_id).exists())
        self.assertFalse(System.objects.filter(id=system_id).exists())
        self.assertFalse(SystemRevision.objects.filter(id=revision_id).exists())

    def test_generate_model_endpoint_forwards_direct_refinement_inputs(self):
        topology_artifact = {"structures": []}
        semantic_plan = {
            "root_actions": [{"slot_id": "ROOT_START", "action": "Review Request"}],
            "branch_plans": [],
        }
        with patch(
            "model.experiment_pipeline.run_pipeline",
            return_value={
                "session_id": "s1",
                "project_id": str(self.project.id),
                "mode": "refinement",
                "pipeline_profile": "semantic_deterministic",
                "use_experimental_compiler": False,
                "enable_sketch_review_agent": False,
                "enable_prompted_sketch_repair_agent": False,
                "enable_graph_repair_agent": False,
                "systems": [],
            },
        ) as mock_run:
            response = self.client.post(
                "/api/v1/generate-model",
                data={
                    "process_text": "Receive request, review it, then finish.",
                    "mode": "refinement",
                    "pipeline_profile": "semantic_deterministic",
                    "current_topology_artifact": topology_artifact,
                    "current_semantic_sketch_plan": semantic_plan,
                    "instruction": "Rename 'Review Request' to 'Validate Request'",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        self.assertEqual(kwargs["current_topology_artifact"], topology_artifact)
        self.assertEqual(kwargs["current_semantic_sketch_plan"], semantic_plan)
        self.assertEqual(kwargs["refinement_instruction"], "Rename 'Review Request' to 'Validate Request'")

    def test_generate_model_endpoint_defaults_to_full_response_mode(self):
        full_payload = {
            "session_id": "s1",
            "project_id": str(self.project.id),
            "mode": "baseline",
            "pipeline_profile": "semantic_deterministic",
            "use_experimental_compiler": False,
            "enable_sketch_review_agent": False,
            "enable_prompted_sketch_repair_agent": False,
            "enable_graph_repair_agent": False,
            "systems": [
                {
                    "system_id": "sys1",
                    "activity_graph": {"nodes": [], "edges": []},
                    "ai4mde": [{"id": "sys1"}],
                }
            ],
        }
        with patch(
            "model.experiment_pipeline.run_pipeline",
            return_value=full_payload,
        ):
            response = self.client.post(
                "/api/v1/generate-model",
                data={
                    "process_text": "Receive request, validate it, send confirmation.",
                    "mode": "baseline",
                    "pipeline_profile": "semantic_deterministic",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), full_payload)

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

    def test_refine_model_endpoint_defaults_to_stable_profile(self):
        refined_export = convert_to_ai4mde(
            clean_model={
                "nodes": [
                    {"id": "n1", "type": "initial"},
                    {"id": "n2", "type": "action", "name": "Validate request"},
                    {"id": "n3", "type": "final"},
                ],
                "edges": [
                    {"source": "n1", "target": "n2", "type": "control"},
                    {"source": "n2", "target": "n3", "type": "control"},
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
        mock_refine.assert_called_once()
        _, kwargs = mock_refine.call_args
        self.assertEqual(kwargs["pipeline_profile"], "stable")

    def test_refine_model_endpoint_uses_semantic_refinement_planner(self):
        persist_semantic_generation_artifacts(
            system_id=str(self.system.id),
            process_text="Receive request, validate it, send confirmation.",
            pipeline_profile="semantic_deterministic",
            topology_artifact={
                "structures": [
                    {
                        "id": "T1",
                        "type": "decision",
                        "parent": "ROOT",
                        "parent_branch": None,
                        "branches": ["approved", "rejected"],
                        "purpose": "approval decision",
                    }
                ]
            },
            semantic_sketch_plan={
                "root_actions": [
                    {"slot_id": "ROOT_START", "action": "review request"},
                    {"slot_id": "AFTER_T1", "action": "finalize request"},
                ],
                "branch_plans": [
                    {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
                    {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
                ],
            },
        )

        updated_topology = {
            "structures": [
                {
                    "id": "T1",
                    "type": "decision",
                    "parent": "ROOT",
                    "parent_branch": None,
                    "branches": ["approved", "rejected", "manual_review"],
                    "purpose": "approval decision",
                }
            ]
        }
        updated_semantics = {
            "root_actions": [
                {"slot_id": "ROOT_START", "action": "review request"},
                {"slot_id": "AFTER_T1", "action": "finalize request"},
            ],
            "branch_plans": [
                {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
                {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
                {"structure_id": "T1", "branch": "manual_review", "intent": "continue", "steps": [{"action": "perform manual review"}]},
            ],
        }
        clean_model = {
            "nodes": [
                {"id": "n1", "type": "initial"},
                {"id": "n2", "type": "action", "name": "review request"},
                {"id": "n3", "type": "action", "name": "finalize request"},
                {"id": "n4", "type": "final"},
            ],
            "edges": [
                {"source": "n1", "target": "n2", "type": "control"},
                {"source": "n2", "target": "n3", "type": "control"},
                {"source": "n3", "target": "n4", "type": "control"},
            ],
        }

        with patch(
            "model.experiment_pipeline.generate_refinement_plan",
            return_value={
                "artifact": {
                    "updated_topology_artifact": updated_topology,
                    "updated_semantic_sketch_plan": updated_semantics,
                    "refinement_trace": {"user_instruction": "Add a fallback review route."},
                }
            },
        ) as mock_planner, patch(
            "model.experiment_pipeline.compile_topology_and_semantics_to_activity_sketch",
            return_value={"sketch": "deterministic"},
        ), patch(
            "model.experiment_pipeline.repair_activity_sketch",
            return_value=({"sketch": "repaired"}, []),
        ), patch(
            "model.experiment_pipeline.compile_activity_sketch",
            return_value=clean_model,
        ), patch(
            "model.experiment_pipeline.import_to_ai4mde",
        ):
            response = self.client.post(
                "/api/v1/refine-model",
                data={
                    "process_text": "Receive request, validate it, send confirmation.",
                    "selected_system_id": str(self.system.id),
                    "refinement_instruction": "Add a fallback review route.",
                    "pipeline_profile": "semantic_deterministic",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        mock_planner.assert_called_once()
        self.assertEqual(payload["process_text"], "Receive request, validate it, send confirmation.")
        self.assertEqual(payload["topology_artifact"], updated_topology)
        self.assertEqual(payload["semantic_sketch_plan"], updated_semantics)
        self.assertEqual(payload["refinement_trace"], {"user_instruction": "Add a fallback review route."})
        self.assertIn("activity_graph", payload)
        self.assertTrue(payload["artifact_diff"]["topology_artifact_diff"]["changed"])
        self.assertEqual(
            payload["artifact_diff"]["topology_artifact_diff"]["structures"]["modified"][0]["id"],
            "T1",
        )
        topology_modified = payload["artifact_diff"]["topology_artifact_diff"]["structures"]["modified"][0]
        self.assertEqual(topology_modified["before"]["type"], topology_modified["after"]["type"])
        self.assertEqual(topology_modified["before"]["id"], topology_modified["after"]["id"])
        self.assertEqual(topology_modified["before"]["parent"], topology_modified["after"]["parent"])
        self.assertEqual(topology_modified["before"]["branches"], ["approved", "rejected"])
        self.assertEqual(topology_modified["after"]["branches"], ["approved", "rejected", "manual_review"])
        self.assertEqual(
            payload["artifact_diff"]["topology_artifact_diff"]["structures"]["removed"],
            [],
        )
        self.assertEqual(
            payload["artifact_diff"]["semantic_sketch_plan_diff"]["branch_plans"]["added"][0]["branch"],
            "manual_review",
        )
        self.assertEqual(
            payload["artifact_diff"]["semantic_sketch_plan_diff"]["root_actions"]["modified"],
            [],
        )
        self.assertEqual(
            payload["artifact_diff"]["semantic_sketch_plan_diff"]["branch_plans"]["removed"],
            [],
        )
        modified_branch_plans = payload["artifact_diff"]["semantic_sketch_plan_diff"]["branch_plans"]["modified"]
        self.assertEqual(modified_branch_plans, [])
        self.assertIsNotNone(payload["current_revision_id"])
        self.assertEqual(payload["revision_index"], 1)
        persisted = SystemGenerationArtifacts.objects.get(system_id=str(self.system.id))
        self.assertEqual(persisted.topology_artifact, updated_topology)
        self.assertEqual(persisted.semantic_sketch_plan, updated_semantics)
        self.system.refresh_from_db()
        self.assertIsNotNone(self.system.current_revision_id)
        current_revision = get_current_revision(str(self.system.id))
        self.assertEqual(current_revision.revision_index, 1)
        self.assertEqual(current_revision.parent_revision.revision_index, 0)
        self.assertEqual(current_revision.topology_artifact, updated_topology)
        self.assertEqual(current_revision.revision_origin, SystemRevision.REVISION_ORIGIN_AI_REFINEMENT)

    def test_refine_model_endpoint_supports_hitl_shape_without_process_text(self):
        persist_semantic_generation_artifacts(
            system_id=str(self.system.id),
            process_text="Receive request, review it, then finish.",
            pipeline_profile="semantic_deterministic",
            topology_artifact={"structures": []},
            semantic_sketch_plan={
                "root_actions": [{"slot_id": "ROOT_START", "action": "Review Request"}],
                "branch_plans": [],
            },
        )
        updated_topology = {"structures": []}
        updated_semantics = {
            "root_actions": [{"slot_id": "ROOT_START", "action": "Validate Request"}],
            "branch_plans": [],
        }
        clean_model = {
            "nodes": [
                {"id": "n1", "type": "initial"},
                {"id": "n2", "type": "action", "name": "Validate Request"},
                {"id": "n3", "type": "final"},
            ],
            "edges": [
                {"source": "n1", "target": "n2", "type": "control"},
                {"source": "n2", "target": "n3", "type": "control"},
            ],
        }

        with patch(
            "model.experiment_pipeline.generate_refinement_plan",
            return_value={
                "artifact": {
                    "updated_topology_artifact": updated_topology,
                    "updated_semantic_sketch_plan": updated_semantics,
                    "refinement_trace": {"user_instruction": "Rename 'Review Request' to 'Validate Request'"},
                }
            },
        ) as mock_planner, patch(
            "model.experiment_pipeline.compile_topology_and_semantics_to_activity_sketch",
            return_value={"sketch": "deterministic"},
        ), patch(
            "model.experiment_pipeline.repair_activity_sketch",
            return_value=({"sketch": "repaired"}, []),
        ), patch(
            "model.experiment_pipeline.compile_activity_sketch",
            return_value=clean_model,
        ), patch(
            "model.experiment_pipeline.import_to_ai4mde",
        ):
            response = self.client.post(
                "/api/v1/refine-model",
                data={
                    "system_id": str(self.system.id),
                    "instruction": "Rename 'Review Request' to 'Validate Request'",
                    "pipeline_profile": "semantic_deterministic",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["system_id"], str(self.system.id))
        self.assertEqual(payload["process_text"], "Receive request, review it, then finish.")
        self.assertEqual(payload["topology_artifact"], updated_topology)
        self.assertEqual(payload["semantic_sketch_plan"], updated_semantics)
        self.assertTrue(payload["artifact_diff"]["semantic_sketch_plan_diff"]["changed"])
        self.assertEqual(
            payload["artifact_diff"]["semantic_sketch_plan_diff"]["root_actions"]["modified"][0]["slot_id"],
            "ROOT_START",
        )
        self.assertEqual(
            payload["refinement_trace"],
            {"user_instruction": "Rename 'Review Request' to 'Validate Request'"},
        )
        args, kwargs = mock_planner.call_args
        self.assertEqual(args[0], "Receive request, review it, then finish.")
        self.assertEqual(payload["revision_index"], 1)
        self.assertEqual(payload["revision_origin"], SystemRevision.REVISION_ORIGIN_AI_REFINEMENT)

    def test_synchronize_human_edit_endpoint_creates_human_sync_revision(self):
        baseline_revision = self._import_linear_system_and_create_baseline_revision()
        action_classifier = self.system.classifiers.get(data__type="action")
        action_classifier.data["name"] = "Validate Request"
        action_classifier.save(update_fields=["data"])

        response = self.client.post(
            "/api/v1/synchronize-human-edit",
            data={"system_id": str(self.system.id)},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["system_id"], str(self.system.id))
        self.assertEqual(payload["revision_origin"], SystemRevision.REVISION_ORIGIN_HUMAN_SYNC)
        self.assertEqual(payload["revision_index"], 1)
        self.assertEqual(payload["parent_revision_id"], str(baseline_revision.id))
        self.assertEqual(
            payload["semantic_sketch_plan"]["root_actions"],
            [{"slot_id": "ROOT_START", "action": "Validate Request"}],
        )
        self.assertFalse(payload["synchronization_diagnostics"]["reused_current_revision_artifacts"])

        self.system.refresh_from_db()
        self.assertIsNotNone(self.system.current_revision_id)
        self.assertNotEqual(self.system.current_revision_id, baseline_revision.id)
        current_revision = get_current_revision(str(self.system.id))
        self.assertEqual(current_revision.revision_index, 1)
        self.assertEqual(current_revision.revision_origin, SystemRevision.REVISION_ORIGIN_HUMAN_SYNC)
        self.assertEqual(
            current_revision.semantic_sketch_plan["root_actions"],
            [{"slot_id": "ROOT_START", "action": "Validate Request"}],
        )

    def test_synchronize_human_edit_endpoint_returns_diagnostics_for_invalid_graph(self):
        from diagram.models import Node

        baseline_revision = self._import_linear_system_and_create_baseline_revision()
        diagram = self.system.diagrams.get()
        classifier = Classifier.objects.create(
            project=self.project,
            system=self.system,
            data={"name": "Detached Review", "type": "action"},
        )
        Node.objects.create(
            diagram=diagram,
            cls=classifier,
            data={"position": {"x": 240, "y": 80}},
        )

        response = self.client.post(
            "/api/v1/synchronize-human-edit",
            data={"system_id": str(self.system.id)},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 422)
        payload = response.json()
        self.assertEqual(
            payload["summary"],
            "The edited Studio model is not structurally valid enough to synchronize into semantic-deterministic artifacts.",
        )
        self.assertGreater(payload["topology_report"]["metrics"]["disconnected_node_count"], 0)
        self.system.refresh_from_db()
        self.assertEqual(self.system.current_revision_id, baseline_revision.id)
        self.assertEqual(self.system.revisions.count(), 1)

    def test_system_revisions_endpoint_lists_revision_history(self):
        persist_semantic_generation_artifacts(
            system_id=str(self.system.id),
            process_text="Receive request, review it, then finish.",
            pipeline_profile="semantic_deterministic",
            topology_artifact={"structures": []},
            semantic_sketch_plan={
                "root_actions": [{"slot_id": "ROOT_START", "action": "Review Request"}],
                "branch_plans": [],
            },
        )
        current_revision = get_current_revision(str(self.system.id))

        response = self.client.get(f"/api/v1/system-revisions/{self.system.id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["system_id"], str(self.system.id))
        self.assertEqual(payload["current_revision_id"], str(current_revision.id))
        self.assertEqual(len(payload["revisions"]), 1)
        self.assertEqual(payload["revisions"][0]["revision_index"], 0)
        self.assertEqual(
            payload["revisions"][0]["revision_origin"],
            SystemRevision.REVISION_ORIGIN_BASELINE,
        )
        self.assertTrue(payload["revisions"][0]["is_current"])

    def test_restore_revision_endpoint_switches_current_revision(self):
        baseline_export = convert_to_ai4mde(
            clean_model={
                "nodes": [
                    {"id": "n1", "type": "initial"},
                    {"id": "n2", "type": "action", "name": "Review Request"},
                    {"id": "n3", "type": "final"},
                ],
                "edges": [
                    {"source": "n1", "target": "n2", "type": "control"},
                    {"source": "n2", "target": "n3", "type": "control"},
                ],
            },
            system_id=str(self.system.id),
            diagram_id=str(uuid4()),
            name=str(self.system.name),
            description=str(self.system.description),
            project_id=str(self.project.id),
        )
        baseline_revision = SystemRevision.objects.create(
            system=self.system,
            revision_index=0,
            process_text="Receive request, review it, then finish.",
            pipeline_profile="semantic_deterministic",
            topology_artifact={"structures": []},
            semantic_sketch_plan={
                "root_actions": [{"slot_id": "ROOT_START", "action": "Review Request"}],
                "branch_plans": [],
            },
            activity_graph={
                "nodes": [
                    {"id": "n1", "type": "initial"},
                    {"id": "n2", "type": "action", "name": "Review Request"},
                    {"id": "n3", "type": "final"},
                ],
                "edges": [
                    {"source": "n1", "target": "n2", "type": "control"},
                    {"source": "n2", "target": "n3", "type": "control"},
                ],
            },
            ai4mde_export=baseline_export,
        )
        refined_export = convert_to_ai4mde(
            clean_model={
                "nodes": [
                    {"id": "n1", "type": "initial"},
                    {"id": "n2", "type": "action", "name": "Validate Request"},
                    {"id": "n3", "type": "final"},
                ],
                "edges": [
                    {"source": "n1", "target": "n2", "type": "control"},
                    {"source": "n2", "target": "n3", "type": "control"},
                ],
            },
            system_id=str(self.system.id),
            diagram_id=str(uuid4()),
            name=str(self.system.name),
            description=str(self.system.description),
            project_id=str(self.project.id),
        )
        refined_revision = SystemRevision.objects.create(
            system=self.system,
            revision_index=1,
            parent_revision=baseline_revision,
            process_text="Receive request, review it, then finish.",
            pipeline_profile="semantic_deterministic",
            topology_artifact={"structures": []},
            semantic_sketch_plan={
                "root_actions": [{"slot_id": "ROOT_START", "action": "Validate Request"}],
                "branch_plans": [],
            },
            activity_graph={
                "nodes": [
                    {"id": "n1", "type": "initial"},
                    {"id": "n2", "type": "action", "name": "Validate Request"},
                    {"id": "n3", "type": "final"},
                ],
                "edges": [
                    {"source": "n1", "target": "n2", "type": "control"},
                    {"source": "n2", "target": "n3", "type": "control"},
                ],
            },
            ai4mde_export=refined_export,
            refinement_trace={"user_instruction": "Rename 'Review Request' to 'Validate Request'"},
            refinement_instruction="Rename 'Review Request' to 'Validate Request'",
        )
        self.system.current_revision = refined_revision
        self.system.save(update_fields=["current_revision"])

        with patch("model.experiment_pipeline.import_to_ai4mde") as mock_import:
            response = self.client.post(
                "/api/v1/restore-revision",
                data={
                    "system_id": str(self.system.id),
                    "revision_id": str(baseline_revision.id),
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["current_revision_id"], str(baseline_revision.id))
        self.assertEqual(payload["revision_index"], 0)
        self.assertEqual(payload["revision_origin"], SystemRevision.REVISION_ORIGIN_BASELINE)
        self.system.refresh_from_db()
        self.assertEqual(self.system.current_revision_id, baseline_revision.id)
        mock_import.assert_called_once_with(self.project, baseline_export)


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

    def test_run_pipeline_includes_activity_graph_and_ai4mde_for_baseline(self):
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
        topology_artifact = {"structures": []}
        semantic_plan = {
            "root_actions": [{"slot_id": "ROOT_START", "action": "Validate request"}],
            "branch_plans": [],
        }
        debug_bundle = {
            "parsed": clean_model,
            "executed_stages": [
                "Topology Artifact",
                "Semantic Planner",
                "Deterministic Sketch Builder",
                "Sketch Repair",
                "Deterministic Compiler",
                "Validation",
            ],
            "stage_artifacts": {
                "topology_artifact": topology_artifact,
                "semantic_plan": semantic_plan,
            },
        }

        with patch(
            "model.experiment_pipeline.generate_activity_model",
            return_value=debug_bundle,
        ) as mock_generate:
            with patch("model.experiment_pipeline.import_to_ai4mde") as mock_import, patch(
                "model.experiment_pipeline._create_revision_snapshot",
                return_value={
                    "revision_id": "rev-1",
                    "revision_index": 0,
                    "parent_revision_id": None,
                    "revision_origin": SystemRevision.REVISION_ORIGIN_BASELINE,
                },
            ):
                from model.experiment_pipeline import run_pipeline

                payload = run_pipeline(
                    "Receive request, validate it, send confirmation.",
                    "baseline",
                    project_id=str(self.project.id),
                    pipeline_profile="semantic_deterministic",
                )

        self.assertEqual(payload["pipeline_profile"], "semantic_deterministic")
        self.assertEqual(len(payload["systems"]), 1)
        self.assertEqual(payload["systems"][0]["activity_graph"], clean_model)
        self.assertEqual(payload["systems"][0]["executed_stages"], debug_bundle["executed_stages"])
        self.assertIn("ai4mde", payload["systems"][0])
        self.assertEqual(payload["systems"][0]["topology_artifact"], topology_artifact)
        self.assertEqual(payload["systems"][0]["semantic_sketch_plan"], semantic_plan)
        self.assertEqual(payload["systems"][0]["revision_index"], 0)
        self.assertEqual(
            payload["systems"][0]["revision_origin"],
            SystemRevision.REVISION_ORIGIN_BASELINE,
        )
        mock_generate.assert_called_once()
        _, kwargs = mock_generate.call_args
        self.assertTrue(kwargs["debug"])
        self.assertEqual(kwargs["pipeline_profile"], "semantic_deterministic")
        mock_import.assert_called_once()

    def test_run_pipeline_persists_semantic_artifacts_for_baseline_generation(self):
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
        topology_artifact = {
            "structures": [
                {
                    "id": "T1",
                    "type": "decision",
                    "parent": "ROOT",
                    "parent_branch": None,
                    "branches": ["approved", "rejected"],
                    "purpose": "approval split",
                }
            ]
        }
        semantic_plan = {
            "root_actions": [{"slot_id": "ROOT_START", "action": "validate request"}],
            "branch_plans": [{"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []}],
        }
        debug_bundle = {
            "parsed": clean_model,
            "executed_stages": [
                "Topology Artifact",
                "Semantic Planner",
                "Deterministic Sketch Builder",
                "Sketch Repair",
                "Deterministic Compiler",
                "Validation",
            ],
            "stage_artifacts": {
                "topology_artifact": topology_artifact,
                "semantic_plan": semantic_plan,
            },
        }

        with patch(
            "model.experiment_pipeline.generate_activity_model",
            return_value=debug_bundle,
        ):
            from model.experiment_pipeline import run_pipeline

            payload = run_pipeline(
                "Receive request, validate it, send confirmation.",
                "baseline",
                project_id=str(self.project.id),
                pipeline_profile="semantic_deterministic",
            )

        system_id = payload["systems"][0]["system_id"]
        persisted = SystemGenerationArtifacts.objects.get(system_id=system_id)
        self.assertEqual(persisted.process_text, "Receive request, validate it, send confirmation.")
        self.assertEqual(persisted.pipeline_profile, "semantic_deterministic")
        self.assertEqual(get_topology_artifact(system_id), topology_artifact)
        self.assertEqual(get_semantic_sketch_plan(system_id), semantic_plan)
        current_revision = get_current_revision(system_id)
        self.assertEqual(current_revision.revision_index, 0)
        self.assertEqual(current_revision.activity_graph, clean_model)
        self.assertEqual(current_revision.revision_origin, SystemRevision.REVISION_ORIGIN_BASELINE)

    def test_run_pipeline_persists_semantic_artifacts_for_candidate_generation(self):
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
        topology_artifact = {
            "structures": [
                {
                    "id": "T2",
                    "type": "loop",
                    "parent": "ROOT",
                    "parent_branch": None,
                    "branches": ["retry", "success"],
                    "purpose": "retry validation",
                }
            ]
        }
        semantic_plan = {
            "root_actions": [{"slot_id": "ROOT_START", "action": "review request"}],
            "branch_plans": [{"structure_id": "T2", "branch": "retry", "intent": "loop_back", "steps": []}],
        }
        system_id = str(uuid4())
        candidate_export = convert_to_ai4mde(
            clean_model=clean_model,
            system_id=system_id,
            diagram_id=str(uuid4()),
            name="Candidate 1",
            description="candidate",
            project_id=str(self.project.id),
        )

        with patch(
            "model.experiment_pipeline.generate_and_convert_candidates",
            return_value=[
                {
                    "clean": clean_model,
                    "ai4mde": candidate_export,
                    "debug_bundle": {
                        "parsed": clean_model,
                        "stage_artifacts": {
                            "topology_artifact": topology_artifact,
                            "semantic_plan": semantic_plan,
                        },
                    },
                }
            ],
        ):
            from model.experiment_pipeline import run_pipeline

            payload = run_pipeline(
                "Receive request, validate it, send confirmation.",
                "refinement",
                project_id=str(self.project.id),
                pipeline_profile="semantic_deterministic",
            )

        generated_system_id = payload["systems"][0]["system_id"]
        persisted = SystemGenerationArtifacts.objects.get(system_id=generated_system_id)
        self.assertEqual(persisted.pipeline_profile, "semantic_deterministic")
        self.assertEqual(get_topology_artifact(generated_system_id), topology_artifact)
        self.assertEqual(get_semantic_sketch_plan(generated_system_id), semantic_plan)
        current_revision = get_current_revision(generated_system_id)
        self.assertEqual(current_revision.revision_index, 0)
        self.assertEqual(current_revision.revision_origin, SystemRevision.REVISION_ORIGIN_AI_REFINEMENT)

    def test_run_pipeline_supports_direct_semantic_refinement(self):
        current_topology_artifact = {"structures": []}
        current_semantic_sketch_plan = {
            "root_actions": [{"slot_id": "ROOT_START", "action": "Review Request"}],
            "branch_plans": [],
        }
        updated_topology_artifact = {"structures": []}
        updated_semantic_sketch_plan = {
            "root_actions": [{"slot_id": "ROOT_START", "action": "Validate Request"}],
            "branch_plans": [],
        }
        clean_model = {
            "nodes": [
                {"id": "n1", "type": "initial"},
                {"id": "n2", "type": "action", "name": "Validate Request"},
                {"id": "n3", "type": "final"},
            ],
            "edges": [
                {"source": "n1", "target": "n2", "type": "control"},
                {"source": "n2", "target": "n3", "type": "control"},
            ],
        }

        with patch(
            "model.experiment_pipeline.generate_refinement_plan",
            return_value={
                "artifact": {
                    "updated_topology_artifact": updated_topology_artifact,
                    "updated_semantic_sketch_plan": updated_semantic_sketch_plan,
                    "refinement_trace": {
                        "user_instruction": "Rename 'Review Request' to 'Validate Request'",
                    },
                }
            },
        ) as mock_planner, patch(
            "model.experiment_pipeline.compile_topology_and_semantics_to_activity_sketch",
            return_value={"sketch": "deterministic"},
        ) as mock_compile_sketch, patch(
            "model.experiment_pipeline.repair_activity_sketch",
            return_value=({"sketch": "repaired"}, []),
        ) as mock_repair, patch(
            "model.experiment_pipeline.compile_activity_sketch",
            return_value=clean_model,
        ) as mock_compile_graph:
            from model.experiment_pipeline import run_pipeline

            payload = run_pipeline(
                "Receive request, review it, then finish.",
                "refinement",
                project_id=str(self.project.id),
                pipeline_profile="semantic_deterministic",
                current_topology_artifact=current_topology_artifact,
                current_semantic_sketch_plan=current_semantic_sketch_plan,
                refinement_instruction="Rename 'Review Request' to 'Validate Request'",
            )

        self.assertEqual(payload["mode"], "refinement")
        self.assertEqual(payload["pipeline_profile"], "semantic_deterministic")
        self.assertEqual(len(payload["systems"]), 1)
        self.assertEqual(payload["systems"][0]["topology_artifact"], updated_topology_artifact)
        self.assertEqual(payload["systems"][0]["semantic_sketch_plan"], updated_semantic_sketch_plan)
        self.assertTrue(payload["systems"][0]["artifact_diff"]["semantic_sketch_plan_diff"]["changed"])
        self.assertEqual(
            payload["systems"][0]["artifact_diff"]["semantic_sketch_plan_diff"]["root_actions"]["modified"][0]["slot_id"],
            "ROOT_START",
        )
        self.assertEqual(
            payload["systems"][0]["refinement_trace"],
            {"user_instruction": "Rename 'Review Request' to 'Validate Request'"},
        )
        self.assertEqual(payload["systems"][0]["revision_index"], 0)
        generated_system_id = payload["systems"][0]["system_id"]
        persisted = SystemGenerationArtifacts.objects.get(system_id=generated_system_id)
        self.assertEqual(persisted.process_text, "Receive request, review it, then finish.")
        self.assertEqual(persisted.pipeline_profile, "semantic_deterministic")
        self.assertEqual(persisted.topology_artifact, updated_topology_artifact)
        self.assertEqual(persisted.semantic_sketch_plan, updated_semantic_sketch_plan)
        current_revision = get_current_revision(generated_system_id)
        self.assertEqual(current_revision.revision_index, 0)
        self.assertEqual(current_revision.refinement_instruction, "Rename 'Review Request' to 'Validate Request'")
        mock_planner.assert_called_once()
        mock_compile_sketch.assert_called_once_with(
            updated_topology_artifact,
            updated_semantic_sketch_plan,
        )
        mock_repair.assert_called_once()
        mock_compile_graph.assert_called_once()
