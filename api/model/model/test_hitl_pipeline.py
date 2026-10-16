from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

from django.db import close_old_connections
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase

from diagram.models import Diagram
from llm.converter import convert_to_ai4mde
from llm.human_edit_synchronizer import HumanEditSynchronizationError
from metadata.api.schemas import ExportSingleSystem
from metadata.models import (
    ProvisionalCandidate,
    Project,
    System,
    SystemGenerationArtifacts,
    SystemRevision,
    create_system_revision,
)
from model.experiment_pipeline import (
    RefinementConflictError,
    _native_process_snapshot,
    _unrepresentable_refinement_fields,
    get_system_revisions,
    import_to_ai4mde,
    refine_selected_model,
    restore_revision,
    run_pipeline,
    select_provisional_candidate,
    synchronize_human_edit,
)
from model.auth import create_token


PROCESS_TEXT = "Receive request, review it, then archive it."
TOPOLOGY = {"structures": []}
SEMANTICS = {
    "root_actions": [
        {
            "slot_id": "ROOT_START",
            "actions": [
                {"action": "receive request"},
                {"action": "review request"},
                {"action": "archive request"},
            ],
        }
    ],
    "branch_plans": [],
}
GRAPH = {
    "nodes": [
        {"id": "n1", "type": "initial"},
        {"id": "n2", "type": "action", "name": "receive request"},
        {"id": "n3", "type": "action", "name": "review request"},
        {"id": "n4", "type": "action", "name": "archive request"},
        {"id": "n5", "type": "final"},
    ],
    "edges": [
        {"source": "n1", "target": "n2", "type": "control"},
        {"source": "n2", "target": "n3", "type": "control"},
        {"source": "n3", "target": "n4", "type": "control"},
        {"source": "n4", "target": "n5", "type": "control"},
    ],
}


def _candidate(project, index):
    graph = {
        **GRAPH,
        "nodes": [dict(node) for node in GRAPH["nodes"]],
        "edges": [dict(edge) for edge in GRAPH["edges"]],
    }
    graph["nodes"][2]["name"] = f"review request option {index}"
    semantics = {
        "root_actions": [
            {
                "slot_id": "ROOT_START",
                "actions": [
                    {"action": "receive request"},
                    {"action": f"review request option {index}"},
                    {"action": "archive request"},
                ],
            }
        ],
        "branch_plans": [],
    }
    exported = convert_to_ai4mde(
        clean_model=graph,
        system_id=str(uuid4()),
        diagram_id=str(uuid4()),
        name=f"Candidate {index}",
        description="Provisional candidate",
        project_id=str(project.id),
    )
    return {
        "clean": graph,
        "ai4mde": exported,
        "debug_bundle": {
            "parsed": graph,
            "executed_stages": ["Topology Artifact", "Semantic Planner"],
            "stage_artifacts": {
                "topology_artifact": TOPOLOGY,
                "semantic_plan": semantics,
            },
        },
    }


class CandidateGenerationFailureCleanupTests(TestCase):
    class GenerationFailure(Exception):
        pass

    def _candidate_row(self, project, *, selected_system=None):
        return ProvisionalCandidate.objects.create(
            project=project,
            session_id=f"Session_{uuid4().hex[:12]}",
            candidate_index=1,
            candidate_count=3,
            process_text=PROCESS_TEXT,
            pipeline_profile="semantic_deterministic",
            activity_graph=GRAPH,
            ai4mde_export={},
            selected_system=selected_system,
        )

    def _run_failed_generation(self, project):
        failure = self.GenerationFailure("topology generation failed")
        with (
            patch(
                "model.experiment_pipeline.resolve_experiment_project",
                return_value=project,
            ),
            patch(
                "model.experiment_pipeline.generate_and_convert_candidates",
                side_effect=failure,
            ),
        ):
            with self.assertRaises(self.GenerationFailure) as raised:
                run_pipeline(
                    PROCESS_TEXT,
                    "refinement",
                    pipeline_profile="semantic_deterministic",
                )
        self.assertIs(raised.exception, failure)

    def test_failed_generation_deletes_only_its_new_empty_project(self):
        failed_project = Project.objects.create(name="Failed", description="Empty")
        ordinary_project = Project.objects.create(name="Ordinary", description="Keep")

        self._run_failed_generation(failed_project)

        self.assertFalse(Project.objects.filter(pk=failed_project.pk).exists())
        self.assertTrue(Project.objects.filter(pk=ordinary_project.pk).exists())

    def test_successful_generation_keeps_project(self):
        project = Project.objects.create(name="Successful", description="Keep")
        generated = [_candidate(project, index) for index in range(1, 4)]
        with (
            patch(
                "model.experiment_pipeline.resolve_experiment_project",
                return_value=project,
            ),
            patch(
                "model.experiment_pipeline.generate_and_convert_candidates",
                return_value=generated,
            ),
        ):
            run_pipeline(
                PROCESS_TEXT,
                "refinement",
                pipeline_profile="semantic_deterministic",
            )

        self.assertTrue(Project.objects.filter(pk=project.pk).exists())
        self.assertEqual(project.provisional_candidates.count(), 3)

    def test_project_with_system_is_not_deleted(self):
        project = Project.objects.create(name="System", description="Keep")
        System.objects.create(project=project, name="Official", description="Model")

        self._run_failed_generation(project)

        self.assertTrue(Project.objects.filter(pk=project.pk).exists())

    def test_project_with_diagram_is_not_deleted(self):
        project = Project.objects.create(name="Diagram", description="Keep")
        system = System.objects.create(project=project, name="Official", description="Model")
        Diagram.objects.create(
            system=system,
            type="activity",
            name="Official",
            description="Model",
        )

        self._run_failed_generation(project)

        self.assertTrue(Project.objects.filter(pk=project.pk).exists())

    def test_project_with_revision_is_not_deleted(self):
        project = Project.objects.create(name="Revision", description="Keep")
        system = System.objects.create(project=project, name="Official", description="Model")
        SystemRevision.objects.create(
            system=system,
            revision_index=0,
            process_text=PROCESS_TEXT,
            pipeline_profile="semantic_deterministic",
            activity_graph=GRAPH,
            ai4mde_export={},
        )

        self._run_failed_generation(project)

        self.assertTrue(Project.objects.filter(pk=project.pk).exists())

    def test_project_with_provisional_candidate_is_not_deleted(self):
        project = Project.objects.create(name="Candidate", description="Keep")
        self._candidate_row(project)

        self._run_failed_generation(project)

        self.assertTrue(Project.objects.filter(pk=project.pk).exists())

    def test_selected_candidate_project_is_not_deleted(self):
        project = Project.objects.create(name="Selected", description="Keep")
        system = System.objects.create(project=project, name="Official", description="Model")
        self._candidate_row(project, selected_system=system)

        self._run_failed_generation(project)

        self.assertTrue(Project.objects.filter(pk=project.pk).exists())

    def test_existing_project_id_is_never_cleanup_eligible(self):
        project = Project.objects.create(name="Existing", description="Keep")
        failure = self.GenerationFailure("topology generation failed")
        with patch(
            "model.experiment_pipeline.generate_and_convert_candidates",
            side_effect=failure,
        ):
            with self.assertRaises(self.GenerationFailure):
                run_pipeline(
                    PROCESS_TEXT,
                    "refinement",
                    project_id=str(project.id),
                    pipeline_profile="semantic_deterministic",
                )

        self.assertTrue(Project.objects.filter(pk=project.pk).exists())

    def test_cleanup_failure_does_not_replace_generation_failure(self):
        project = Project.objects.create(name="Cleanup failure", description="Keep")
        generation_failure = self.GenerationFailure("topology generation failed")
        cleanup_failure = RuntimeError("cleanup failed")
        with (
            patch(
                "model.experiment_pipeline.resolve_experiment_project",
                return_value=project,
            ),
            patch(
                "model.experiment_pipeline.generate_and_convert_candidates",
                side_effect=generation_failure,
            ),
            patch(
                "model.experiment_pipeline._delete_failed_empty_project",
                side_effect=cleanup_failure,
            ),
            self.assertLogs("model.experiment_pipeline", level="ERROR"),
        ):
            with self.assertRaises(self.GenerationFailure) as raised:
                run_pipeline(
                    PROCESS_TEXT,
                    "refinement",
                    pipeline_profile="semantic_deterministic",
                )

        self.assertIs(raised.exception, generation_failure)
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())


class CandidateSelectionContractTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Candidate project", description="Candidate selection")

    def test_generation_is_provisional_and_selection_creates_one_baseline_revision_zero(self):
        generated = [_candidate(self.project, index) for index in range(1, 4)]
        with patch(
            "model.experiment_pipeline.generate_and_convert_candidates",
            return_value=generated,
        ):
            payload = run_pipeline(
                PROCESS_TEXT,
                "refinement",
                project_id=str(self.project.id),
                pipeline_profile="semantic_deterministic",
            )

        self.assertEqual(len(payload["candidates"]), 3)
        self.assertTrue(all(entry["provisional"] for entry in payload["candidates"]))
        self.assertEqual(System.objects.filter(project=self.project).count(), 0)
        self.assertEqual(SystemRevision.objects.count(), 0)
        self.assertEqual(ProvisionalCandidate.objects.filter(project=self.project).count(), 3)

        selected = select_provisional_candidate(
            candidate_id=payload["candidates"][1]["candidate_id"]
        )

        self.assertEqual(System.objects.filter(project=self.project).count(), 1)
        self.assertEqual(SystemRevision.objects.count(), 1)
        revision = SystemRevision.objects.get()
        self.assertEqual(revision.revision_index, 0)
        self.assertEqual(revision.revision_origin, SystemRevision.REVISION_ORIGIN_BASELINE)
        self.assertEqual(revision.process_text, PROCESS_TEXT)
        self.assertEqual(revision.topology_artifact, TOPOLOGY)
        self.assertEqual(
            revision.semantic_sketch_plan,
            generated[1]["debug_bundle"]["stage_artifacts"]["semantic_plan"],
        )
        self.assertEqual(revision.activity_graph, generated[1]["clean"])
        self.assertEqual(revision.ai4mde_export, generated[1]["ai4mde"])
        self.assertEqual(revision.candidate_index, 2)
        self.assertEqual(revision.candidate_count, 3)
        self.assertEqual(
            System.objects.get(pk=selected["system_id"]).current_revision_id,
            revision.id,
        )
        self.assertEqual(selected["candidate_index"], 2)
        self.assertEqual(selected["candidate_count"], 3)
        self.assertEqual(
            ProvisionalCandidate.objects.filter(selected_system__isnull=False).count(),
            1,
        )
        self.assertEqual(
            SystemRevision.objects.filter(system_id=selected["system_id"]).count(),
            1,
        )

        later_revision = create_system_revision(
            system_id=selected["system_id"],
            process_text=PROCESS_TEXT,
            pipeline_profile="semantic_deterministic",
            topology_artifact=revision.topology_artifact,
            semantic_sketch_plan=revision.semantic_sketch_plan,
            activity_graph=revision.activity_graph,
            ai4mde_export=revision.ai4mde_export,
            revision_origin=SystemRevision.REVISION_ORIGIN_AI_REFINEMENT,
            parent_revision_id=str(revision.id),
        )
        reselected = select_provisional_candidate(
            candidate_id=payload["candidates"][1]["candidate_id"]
        )
        self.assertEqual(reselected["revision_id"], str(revision.id))
        self.assertEqual(reselected["revision_index"], 0)
        self.assertEqual(
            reselected["revision_origin"],
            SystemRevision.REVISION_ORIGIN_BASELINE,
        )
        self.assertNotEqual(reselected["revision_id"], str(later_revision.id))

        with self.assertRaisesMessage(ValueError, "a different candidate has already been selected"):
            select_provisional_candidate(candidate_id=payload["candidates"][0]["candidate_id"])

    def test_selected_candidate_can_be_refined_immediately_without_human_sync(self):
        generated = [_candidate(self.project, index) for index in range(1, 4)]
        with patch(
            "model.experiment_pipeline.generate_and_convert_candidates",
            return_value=generated,
        ):
            payload = run_pipeline(
                PROCESS_TEXT,
                "refinement",
                project_id=str(self.project.id),
                pipeline_profile="semantic_deterministic",
            )

        selected = select_provisional_candidate(
            candidate_id=payload["candidates"][1]["candidate_id"]
        )
        baseline = SystemRevision.objects.get(
            system_id=selected["system_id"],
            revision_index=0,
        )
        updated_graph = {
            **baseline.activity_graph,
            "nodes": [dict(node) for node in baseline.activity_graph["nodes"]],
            "edges": [dict(edge) for edge in baseline.activity_graph["edges"]],
        }
        updated_graph["nodes"][2]["name"] = "approve request"
        updated_semantics = {
            "root_actions": [
                {
                    "slot_id": "ROOT_START",
                    "actions": [
                        {"action": "receive request"},
                        {"action": "approve request"},
                        {"action": "archive request"},
                    ],
                }
            ],
            "branch_plans": [],
        }
        refinement_result = {
            "artifact_diff": {},
            "updated_artifacts": {
                "updated_topology_artifact": TOPOLOGY,
                "updated_semantic_sketch_plan": updated_semantics,
                "refinement_trace": {"user_instruction": "approve the request"},
            },
            "clean_graph": updated_graph,
        }

        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            return_value=refinement_result,
        ) as semantic_refine:
            refined = refine_selected_model(
                None,
                selected_system_id=selected["system_id"],
                refinement_instruction="approve the request",
            )

        semantic_refine.assert_called_once_with(
            PROCESS_TEXT,
            current_topology_artifact=baseline.topology_artifact,
            current_semantic_sketch_plan=baseline.semantic_sketch_plan,
            refinement_instruction="approve the request",
        )
        self.assertEqual(
            refined["revision_origin"],
            SystemRevision.REVISION_ORIGIN_AI_REFINEMENT,
        )
        self.assertEqual(refined["parent_revision_id"], str(baseline.id))
        self.assertEqual(
            SystemRevision.objects.filter(
                system_id=selected["system_id"],
                revision_origin=SystemRevision.REVISION_ORIGIN_HUMAN_SYNC,
            ).count(),
            0,
        )

    def test_selected_candidate_layout_is_persisted_in_baseline_revision(self):
        generated = [_candidate(self.project, index) for index in range(1, 4)]
        with patch(
            "model.experiment_pipeline.generate_and_convert_candidates",
            return_value=generated,
        ):
            payload = run_pipeline(
                PROCESS_TEXT,
                "refinement",
                project_id=str(self.project.id),
                pipeline_profile="semantic_deterministic",
            )

        selected_candidate = generated[1]
        exported_system = selected_candidate["ai4mde"][0]
        exported_nodes = exported_system["diagrams"][0]["nodes"]
        arranged_positions = {
            str(node["id"]): {"x": 120 + index * 80, "y": 90 + index * 60}
            for index, node in enumerate(exported_nodes)
        }

        selected = select_provisional_candidate(
            candidate_id=payload["candidates"][1]["candidate_id"],
            node_positions=arranged_positions,
        )

        revision = SystemRevision.objects.get(
            system_id=selected["system_id"],
            revision_index=0,
        )
        revision_nodes = revision.ai4mde_export[0]["diagrams"][0]["nodes"]
        self.assertEqual(
            {
                str(node["id"]): node["data"]["position"]
                for node in revision_nodes
            },
            arranged_positions,
        )
        official_nodes = System.objects.get(pk=selected["system_id"]).diagrams.get(
            type="activity"
        ).nodes.all()
        self.assertEqual(
            {str(node.id): node.data["position"] for node in official_nodes},
            arranged_positions,
        )
        self.assertEqual(revision.revision_origin, SystemRevision.REVISION_ORIGIN_BASELINE)
        self.assertEqual(revision.activity_graph, selected_candidate["clean"])
        self.assertEqual(revision.topology_artifact, TOPOLOGY)
        self.assertEqual(
            revision.semantic_sketch_plan,
            selected_candidate["debug_bundle"]["stage_artifacts"]["semantic_plan"],
        )
        self.assertEqual(SystemRevision.objects.filter(system_id=selected["system_id"]).count(), 1)
        self.assertFalse(
            SystemRevision.objects.filter(
                system_id=selected["system_id"],
                revision_origin=SystemRevision.REVISION_ORIGIN_HUMAN_SYNC,
            ).exists()
        )

    def test_candidate_layout_rejects_unknown_nodes_before_promotion(self):
        generated = [_candidate(self.project, index) for index in range(1, 4)]
        with patch(
            "model.experiment_pipeline.generate_and_convert_candidates",
            return_value=generated,
        ):
            payload = run_pipeline(
                PROCESS_TEXT,
                "refinement",
                project_id=str(self.project.id),
                pipeline_profile="semantic_deterministic",
            )

        with self.assertRaisesMessage(
            ValueError,
            "candidate layout references unknown node ids",
        ):
            select_provisional_candidate(
                candidate_id=payload["candidates"][1]["candidate_id"],
                node_positions={str(uuid4()): {"x": 10, "y": 20}},
            )

        self.assertEqual(System.objects.filter(project=self.project).count(), 0)
        self.assertEqual(SystemRevision.objects.count(), 0)


class CandidateSelectionConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Concurrent candidate project",
            description="Concurrent candidate selection",
        )
        self.candidates = []
        for index in range(1, 3):
            generated = _candidate(self.project, index)
            self.candidates.append(
                ProvisionalCandidate.objects.create(
                    project=self.project,
                    session_id="concurrent-session",
                    candidate_index=index,
                    candidate_count=2,
                    process_text=PROCESS_TEXT,
                    pipeline_profile="semantic_deterministic",
                    activity_graph=generated["clean"],
                    ai4mde_export=generated["ai4mde"],
                    topology_artifact=TOPOLOGY,
                    semantic_sketch_plan=generated["debug_bundle"]["stage_artifacts"]["semantic_plan"],
                )
            )

    def test_concurrent_selection_creates_exactly_one_official_revision_zero(self):
        barrier = Barrier(2)

        def select_candidate(candidate_id):
            close_old_connections()
            try:
                barrier.wait(timeout=5)
                return ("selected", select_provisional_candidate(candidate_id=str(candidate_id)))
            except ValueError as exc:
                return ("rejected", str(exc))
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(
                executor.map(
                    select_candidate,
                    [candidate.id for candidate in self.candidates],
                )
            )

        self.assertEqual([status for status, _ in results].count("selected"), 1)
        self.assertEqual([status for status, _ in results].count("rejected"), 1)
        self.assertIn(
            "a different candidate has already been selected",
            next(value for status, value in results if status == "rejected"),
        )
        self.assertEqual(System.objects.filter(project=self.project).count(), 1)
        self.assertEqual(SystemRevision.objects.count(), 1)
        revision = SystemRevision.objects.get()
        self.assertEqual(revision.revision_index, 0)
        self.assertEqual(revision.revision_origin, SystemRevision.REVISION_ORIGIN_BASELINE)
        self.assertEqual(
            ProvisionalCandidate.objects.filter(selected_system__isnull=False).count(),
            1,
        )


class HitlRevisionFlowTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="hitl-test-user", password="test-password")
        _, token = create_token(user.username, "test-password")
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        self.project = Project.objects.create(name="HITL project", description="HITL tests")
        self.system_id = str(uuid4())
        self.exported = convert_to_ai4mde(
            clean_model=GRAPH,
            system_id=self.system_id,
            diagram_id=str(uuid4()),
            name="HITL system",
            description="Synchronized system",
            project_id=str(self.project.id),
        )
        import_to_ai4mde(self.project, self.exported)
        self.baseline = create_system_revision(
            system_id=self.system_id,
            process_text=PROCESS_TEXT,
            pipeline_profile="semantic_deterministic",
            topology_artifact=TOPOLOGY,
            semantic_sketch_plan=SEMANTICS,
            activity_graph=GRAPH,
            ai4mde_export=self.exported,
            revision_origin=SystemRevision.REVISION_ORIGIN_BASELINE,
        )

    def _unchanged_refinement_result(self):
        return {
            "artifact_diff": {},
            "updated_artifacts": {
                "updated_topology_artifact": TOPOLOGY,
                "updated_semantic_sketch_plan": SEMANTICS,
                "refinement_trace": {},
            },
            "clean_graph": GRAPH,
        }

    def _baseline_with_guard(self):
        flow = System.objects.get(pk=self.system_id).relations.get(
            pk=self.exported[0]["relations"][0]["id"]
        )
        flow.data["guard"] = "approved"
        flow.save(update_fields=["data"])
        graph = {
            **GRAPH,
            "nodes": [dict(node) for node in GRAPH["nodes"]],
            "edges": [dict(edge) for edge in GRAPH["edges"]],
        }
        graph["edges"][0]["condition"] = "approved"
        self.baseline.activity_graph = graph
        self.baseline.ai4mde_export = [
            ExportSingleSystem.model_validate(System.objects.get(pk=self.system_id)).model_dump(mode="json")
        ]
        self.baseline.save(update_fields=["activity_graph", "ai4mde_export"])
        return graph, flow

    def test_saved_process_edit_requires_sync_before_refinement(self):
        classifier = System.objects.get(pk=self.system_id).classifiers.get(data__name="review request")
        classifier.data["name"] = "validate request"
        classifier.save(update_fields=["data"])

        with patch("model.experiment_pipeline._run_semantic_refinement_from_artifacts") as planner:
            response = self.client.post(
                "/api/v1/refine-model",
                data={"system_id": self.system_id, "instruction": "add a review"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "refinement_conflict")
        self.assertIn("Sync with AI", response.json()["detail"])
        planner.assert_not_called()
        classifier.refresh_from_db()
        self.assertEqual(classifier.data["name"], "validate request")
        self.assertEqual(System.objects.get(pk=self.system_id).current_revision_id, self.baseline.id)

    def test_saved_action_body_requires_sync_before_refinement(self):
        action = System.objects.get(pk=self.system_id).classifiers.get(data__name="review request")
        action.data["body"] = "human implementation"
        action.save(update_fields=["data"])

        with patch("model.experiment_pipeline._run_semantic_refinement_from_artifacts") as planner:
            response = self.client.post(
                "/api/v1/refine-model",
                data={"system_id": self.system_id, "instruction": "keep the flow"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "refinement_conflict")
        planner.assert_not_called()
        action.refresh_from_db()
        self.assertEqual(action.data["body"], "human implementation")

    def test_saved_flow_guard_requires_sync_before_refinement(self):
        flow = System.objects.get(pk=self.system_id).relations.first()
        flow.data["guard"] = "approved"
        flow.save(update_fields=["data"])

        with patch("model.experiment_pipeline._run_semantic_refinement_from_artifacts") as planner:
            response = self.client.post(
                "/api/v1/refine-model",
                data={"system_id": self.system_id, "instruction": "keep the flow"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "refinement_conflict")
        planner.assert_not_called()
        flow.refresh_from_db()
        self.assertEqual(flow.data["guard"], "approved")

    def test_synced_action_body_is_safely_rejected_by_refinement(self):
        action = System.objects.get(pk=self.system_id).classifiers.get(data__name="review request")
        action.data["body"] = "human implementation"
        action.save(update_fields=["data"])
        synced = synchronize_human_edit(system_id=self.system_id)

        with patch("model.experiment_pipeline._run_semantic_refinement_from_artifacts") as planner:
            response = self.client.post(
                "/api/v1/refine-model",
                data={"system_id": self.system_id, "instruction": "keep the flow"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "unsupported_refinement_fields")
        planner.assert_not_called()
        action.refresh_from_db()
        self.assertEqual(action.data["body"], "human implementation")
        self.assertEqual(
            str(System.objects.get(pk=self.system_id).current_revision_id),
            synced["revision_id"],
        )

    def test_all_editable_action_and_flow_fields_are_audited(self):
        self.assertEqual(_unrepresentable_refinement_fields(self.exported), [])
        action = next(item for item in self.exported[0]["classifiers"] if item["data"]["type"] == "action")
        flow = self.exported[0]["relations"][0]
        fields = [
            ("action", action["id"], "body", "human code"),
            ("action", action["id"], "localPrecondition", "approved"),
            ("action", action["id"], "localPostcondition", "archived"),
            ("action", action["id"], "isAutomatic", True),
            ("action", action["id"], "customCode", "return true"),
            ("action", action["id"], "namespace", "human"),
            ("action", action["id"], "operation", {"name": "run"}),
            ("action", action["id"], "publish", ["done"]),
            ("action", action["id"], "subscribe", ["start"]),
            ("action", action["id"], "classes", {"input": ["Order"]}),
            ("action", action["id"], "application_models", ["app"]),
            ("action", action["id"], "page", "checkout"),
            ("action", action["id"], "actorNode", "actor-id"),
            ("action", action["id"], "actorNodeName", "Customer"),
            ("action", action["id"], "futureEditableField", "new"),
            ("controlflow", flow["id"], "weight", "2"),
            ("controlflow", flow["id"], "is_directed", False),
        ]
        for kind, item_id, field, value in fields:
            with self.subTest(kind=kind, field=field):
                changed = deepcopy(self.exported)
                collection = "classifiers" if kind == "action" else "relations"
                item = next(item for item in changed[0][collection] if item["id"] == item_id)
                item["data"][field] = value
                self.assertIn(f"{kind}.{field}", _unrepresentable_refinement_fields(changed))

        for kind, field, value in (
            ("initial", "scheduled", True),
            ("initial", "schedule", "daily"),
            ("decision", "decisionInput", "choice"),
            ("join", "join_spec", "and"),
            ("merge", "merge_spec", "or"),
        ):
            with self.subTest(kind=kind, field=field):
                changed = deepcopy(self.exported)
                item = next(
                    (item for item in changed[0]["classifiers"] if item["data"]["type"] == kind),
                    None,
                )
                if item is None:
                    continue
                item["data"][field] = value
                self.assertIn(f"{kind}.{field}", _unrepresentable_refinement_fields(changed))

    def test_supported_guard_and_layout_only_fields_pass_roundtrip_audit(self):
        changed = deepcopy(self.exported)
        changed[0]["relations"][0]["data"]["guard"] = "approved"
        changed[0]["relations"][0]["data"]["label"] = ""
        changed[0]["diagrams"][0]["nodes"][0]["data"]["position"] = {"x": 800, "y": 400}
        changed[0]["relations"][0]["data"]["position_handlers"] = [{"x": 2, "y": 3}]
        self.assertEqual(_unrepresentable_refinement_fields(changed), [])
        self.assertEqual(
            _native_process_snapshot(changed)["classifiers"],
            _native_process_snapshot(self.exported)["classifiers"],
        )

    def test_control_nodes_and_flow_condition_field_inventory(self):
        graph = {
            "nodes": [
                {"id": "n1", "type": "initial"},
                {"id": "n2", "type": "decision", "name": "choose", "label": "choose?"},
                {"id": "n3", "type": "fork", "name": "split"},
                {"id": "n4", "type": "join", "name": "join"},
                {"id": "n5", "type": "merge", "name": "merge"},
                {"id": "n6", "type": "final"},
            ],
            "edges": [
                {"source": f"n{i}", "target": f"n{i + 1}", "type": "control"}
                for i in range(1, 6)
            ],
        }
        exported = convert_to_ai4mde(
            clean_model=graph, system_id=str(uuid4()), diagram_id=str(uuid4()),
            project_id=str(self.project.id),
        )
        self.assertEqual(_unrepresentable_refinement_fields(exported), [])
        control_fields = {
            "initial": {"scheduled": True, "schedule": "daily", "activity_scope": "flow"},
            "decision": {"decisionInput": "choice", "decisionInputFlow": "other", "page": "decision"},
            "join": {"join_spec": "and", "is_combine_duplicate": True},
            "merge": {"merge_spec": "or", "is_combine_duplicate": True, "page": "merge"},
            "final": {"activity_scope": "flow"},
        }
        for kind, values in control_fields.items():
            for field, value in values.items():
                with self.subTest(kind=kind, field=field):
                    changed = deepcopy(exported)
                    classifier = next(
                        item for item in changed[0]["classifiers"] if item["data"]["type"] == kind
                    )
                    classifier["data"][field] = value
                    self.assertIn(f"{kind}.{field}", _unrepresentable_refinement_fields(changed))

        for kind in ("fork", "join"):
            changed = deepcopy(exported)
            classifier = next(
                item for item in changed[0]["classifiers"] if item["data"]["type"] == kind
            )
            classifier["data"].update(height=100, width=200)
            self.assertEqual(_unrepresentable_refinement_fields(changed), [])
            self.assertEqual(_native_process_snapshot(changed), _native_process_snapshot(exported))

        changed = deepcopy(exported)
        changed[0]["relations"][0]["data"]["condition"] = {"isElse": True}
        self.assertIn("controlflow.condition", _unrepresentable_refinement_fields(changed))

    def test_object_flow_fields_and_classifier_reference_are_audited(self):
        exported = convert_to_ai4mde(
            clean_model={
                "nodes": [
                    {"id": "n1", "type": "initial"},
                    {"id": "n2", "type": "object"},
                    {"id": "n3", "type": "action", "name": "process"},
                    {"id": "n4", "type": "final"},
                ],
                "edges": [
                    {"source": "n1", "target": "n3", "type": "control"},
                    {"source": "n2", "target": "n3", "type": "object"},
                    {"source": "n3", "target": "n4", "type": "control"},
                ],
            },
            system_id=str(uuid4()), diagram_id=str(uuid4()), project_id=str(self.project.id),
        )
        self.assertEqual(_unrepresentable_refinement_fields(exported), [])
        flow = next(item for item in exported[0]["relations"] if item["data"]["type"] == "objectflow")
        guarded = deepcopy(exported)
        next(item for item in guarded[0]["relations"] if item["id"] == flow["id"])["data"]["guard"] = "approved"
        self.assertEqual(_unrepresentable_refinement_fields(guarded), [])
        for field, value in (("weight", "2"), ("is_directed", False), ("cls", "unrelated-id")):
            with self.subTest(field=field):
                changed = deepcopy(exported)
                item = next(item for item in changed[0]["relations"] if item["id"] == flow["id"])
                item["data"][field] = value
                self.assertIn(f"objectflow.{field}", _unrepresentable_refinement_fields(changed))

    def test_system_and_diagram_fields_cannot_be_silently_dropped(self):
        for field, value in (("interfaces", [{"id": "other"}]), ("imported_classifiers", [{"id": "other"}])):
            with self.subTest(field=field):
                changed = deepcopy(self.exported)
                changed[0][field] = value
                self.assertTrue(_unrepresentable_refinement_fields(changed))
                self.assertNotEqual(_native_process_snapshot(changed), _native_process_snapshot(self.exported))

        changed = deepcopy(self.exported)
        changed[0]["diagrams"][0]["name"] = "Human diagram title"
        self.assertIn("diagram.name", _unrepresentable_refinement_fields(changed))
        self.assertNotEqual(_native_process_snapshot(changed), _native_process_snapshot(self.exported))

    def test_activity_graph_partition_without_native_lane_mapping_blocks_refinement(self):
        graph = deepcopy(GRAPH)
        graph["nodes"][1]["partition"] = "Finance"
        self.baseline.activity_graph = graph
        self.baseline.save(update_fields=["activity_graph"])

        with patch("model.experiment_pipeline._run_semantic_refinement_from_artifacts") as planner:
            response = self.client.post(
                "/api/v1/refine-model",
                data={"system_id": self.system_id, "instruction": "keep the flow"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "unsupported_refinement_fields")
        self.assertIn("partition", response.json()["detail"])
        planner.assert_not_called()

    def test_structured_flow_condition_rejects_refinement_without_loss(self):
        flow = System.objects.get(pk=self.system_id).relations.first()
        flow.data["condition"] = {"isElse": True}
        flow.save(update_fields=["data"])

        with patch("model.experiment_pipeline._run_semantic_refinement_from_artifacts") as planner:
            response = self.client.post(
                "/api/v1/refine-model",
                data={"system_id": self.system_id, "instruction": "keep the flow"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "unsupported_refinement_fields")
        self.assertIn("condition", response.json()["detail"])
        planner.assert_not_called()
        flow.refresh_from_db()
        self.assertEqual(flow.data["condition"], {"isElse": True})

    def test_action_conditions_and_flow_weight_require_sync_then_block_refinement(self):
        for kind, field, value in (
            ("action", "localPrecondition", "approved"),
            ("action", "localPostcondition", "archived"),
            ("flow", "weight", "2"),
        ):
            with self.subTest(field=field):
                system = System.objects.get(pk=self.system_id)
                item = (
                    system.classifiers.get(data__name="review request")
                    if kind == "action" else system.relations.first()
                )
                item.data[field] = value
                item.save(update_fields=["data"])
                with patch("model.experiment_pipeline._run_semantic_refinement_from_artifacts") as planner:
                    response = self.client.post(
                        "/api/v1/refine-model",
                        data={"system_id": self.system_id, "instruction": "keep the flow"},
                        content_type="application/json",
                    )
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json()["error"], "refinement_conflict")
                planner.assert_not_called()

                synchronize_human_edit(system_id=self.system_id)
                with patch("model.experiment_pipeline._run_semantic_refinement_from_artifacts") as planner:
                    response = self.client.post(
                        "/api/v1/refine-model",
                        data={"system_id": self.system_id, "instruction": "keep the flow"},
                        content_type="application/json",
                    )
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.json()["error"], "unsupported_refinement_fields")
                self.assertIn(field, response.json()["detail"])
                planner.assert_not_called()
                item.refresh_from_db()
                self.assertEqual(item.data[field], value)

                item.data[field] = ""
                item.save(update_fields=["data"])
                synchronize_human_edit(system_id=self.system_id)

    def test_action_conditions_and_weight_changed_during_refinement_cannot_import(self):
        for kind, field, value in (
            ("action", "localPrecondition", "approved"),
            ("action", "localPostcondition", "archived"),
            ("flow", "weight", "2"),
        ):
            with self.subTest(field=field):
                system = System.objects.get(pk=self.system_id)
                item = (
                    system.classifiers.get(data__name="review request")
                    if kind == "action" else system.relations.first()
                )

                def save_during_refinement(*args, **kwargs):
                    item.data[field] = value
                    item.save(update_fields=["data"])
                    return self._unchanged_refinement_result()

                with patch(
                    "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
                    side_effect=save_during_refinement,
                ), patch("model.experiment_pipeline.import_to_ai4mde") as importer:
                    with self.assertRaises(RefinementConflictError):
                        refine_selected_model(
                            None, selected_system_id=self.system_id,
                            refinement_instruction="keep the flow",
                        )
                importer.assert_not_called()
                item.refresh_from_db()
                self.assertEqual(item.data[field], value)
                item.data[field] = ""
                item.save(update_fields=["data"])

    def test_flow_guard_that_cannot_roundtrip_is_not_synchronized(self):
        flow = System.objects.get(pk=self.system_id).relations.first()
        flow.data["guard"] = "approved"
        flow.save(update_fields=["data"])
        with self.assertRaises(HumanEditSynchronizationError) as raised:
            synchronize_human_edit(system_id=self.system_id)

        self.assertIn("Flow guard", str(raised.exception))
        flow.refresh_from_db()
        self.assertEqual(flow.data["guard"], "approved")
        self.assertEqual(System.objects.get(pk=self.system_id).current_revision_id, self.baseline.id)

    def test_refinement_that_drops_synchronized_guard_does_not_import(self):
        _, flow = self._baseline_with_guard()

        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            return_value=self._unchanged_refinement_result(),
        ), patch("model.experiment_pipeline.import_to_ai4mde") as importer:
            with self.assertRaises(RefinementConflictError):
                refine_selected_model(
                    None, selected_system_id=self.system_id, refinement_instruction="keep the flow"
                )

        importer.assert_not_called()
        flow.refresh_from_db()
        self.assertEqual(flow.data["guard"], "approved")

    def test_refinement_preserves_guard_when_graph_retains_condition(self):
        graph_with_guard, _ = self._baseline_with_guard()
        synced = synchronize_human_edit(system_id=self.system_id)
        refinement_result = {
            **self._unchanged_refinement_result(),
            "clean_graph": graph_with_guard,
        }
        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            return_value=refinement_result,
        ):
            refined = refine_selected_model(
                None, selected_system_id=self.system_id, refinement_instruction="keep the flow"
            )

        self.assertEqual(refined["revision_origin"], "ai_refinement")
        self.assertEqual(refined["parent_revision_id"], synced["revision_id"])
        self.assertIn(
            "approved",
            [relation.data.get("guard") for relation in System.objects.get(pk=self.system_id).relations.all()],
        )

    def test_refinement_cannot_move_guard_to_a_different_flow(self):
        graph_with_guard, flow = self._baseline_with_guard()
        moved_graph = {
            **graph_with_guard,
            "edges": [dict(edge) for edge in graph_with_guard["edges"]],
        }
        del moved_graph["edges"][0]["condition"]
        moved_graph["edges"][1]["condition"] = "approved"
        refinement_result = {
            **self._unchanged_refinement_result(),
            "clean_graph": moved_graph,
        }

        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            return_value=refinement_result,
        ), patch("model.experiment_pipeline.import_to_ai4mde") as importer:
            with self.assertRaises(RefinementConflictError):
                refine_selected_model(
                    None, selected_system_id=self.system_id, refinement_instruction="keep the flow"
                )

        importer.assert_not_called()
        flow.refresh_from_db()
        self.assertEqual(flow.data["guard"], "approved")

    def test_flow_guard_edit_during_refinement_is_not_imported(self):
        flow = System.objects.get(pk=self.system_id).relations.first()

        def save_during_refinement(*args, **kwargs):
            flow.data["guard"] = "changed while refining"
            flow.save(update_fields=["data"])
            return self._unchanged_refinement_result()

        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            side_effect=save_during_refinement,
        ), patch("model.experiment_pipeline.import_to_ai4mde") as importer:
            with self.assertRaises(RefinementConflictError):
                refine_selected_model(
                    None, selected_system_id=self.system_id, refinement_instruction="keep the flow"
                )

        importer.assert_not_called()
        flow.refresh_from_db()
        self.assertEqual(flow.data["guard"], "changed while refining")

    def test_action_body_edit_during_refinement_is_not_imported(self):
        action = System.objects.get(pk=self.system_id).classifiers.get(data__name="review request")

        def save_during_refinement(*args, **kwargs):
            action.data["body"] = "saved while refining"
            action.save(update_fields=["data"])
            return self._unchanged_refinement_result()

        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            side_effect=save_during_refinement,
        ), patch("model.experiment_pipeline.import_to_ai4mde") as importer:
            with self.assertRaises(RefinementConflictError):
                refine_selected_model(
                    None, selected_system_id=self.system_id, refinement_instruction="keep the flow"
                )

        importer.assert_not_called()
        action.refresh_from_db()
        self.assertEqual(action.data["body"], "saved while refining")

    def test_layout_only_edit_allows_direct_refinement(self):
        node = System.objects.get(pk=self.system_id).diagrams.first().nodes.first()
        node.data["position"] = {"x": 900, "y": 400}
        node.save(update_fields=["data"])

        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            return_value=self._unchanged_refinement_result(),
        ) as planner:
            refined = refine_selected_model(
                None, selected_system_id=self.system_id, refinement_instruction="keep the flow"
            )

        planner.assert_called_once()
        self.assertEqual(refined["parent_revision_id"], str(self.baseline.id))

    def test_layout_only_edit_during_refinement_does_not_conflict(self):
        node = System.objects.get(pk=self.system_id).diagrams.first().nodes.first()

        def move_during_refinement(*args, **kwargs):
            node.data["position"] = {"x": 901, "y": 401}
            node.save(update_fields=["data"])
            return self._unchanged_refinement_result()

        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            side_effect=move_during_refinement,
        ):
            refined = refine_selected_model(
                None, selected_system_id=self.system_id, refinement_instruction="keep the flow"
            )

        self.assertEqual(refined["parent_revision_id"], str(self.baseline.id))

    def test_saved_edit_during_refinement_is_not_imported_over(self):
        classifier = System.objects.get(pk=self.system_id).classifiers.get(data__name="review request")

        def save_during_refinement(*args, **kwargs):
            classifier.data["name"] = "validate request"
            classifier.save(update_fields=["data"])
            return self._unchanged_refinement_result()

        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            side_effect=save_during_refinement,
        ), patch("model.experiment_pipeline.import_to_ai4mde") as importer:
            with self.assertRaises(RefinementConflictError):
                refine_selected_model(
                    None, selected_system_id=self.system_id, refinement_instruction="keep the flow"
                )

        importer.assert_not_called()
        classifier.refresh_from_db()
        self.assertEqual(classifier.data["name"], "validate request")
        self.assertEqual(System.objects.get(pk=self.system_id).current_revision_id, self.baseline.id)

    def test_revision_change_during_refinement_is_not_imported_over(self):
        def sync_during_refinement(*args, **kwargs):
            create_system_revision(
                system_id=self.system_id,
                process_text=PROCESS_TEXT,
                pipeline_profile="semantic_deterministic",
                topology_artifact=TOPOLOGY,
                semantic_sketch_plan=SEMANTICS,
                activity_graph=GRAPH,
                ai4mde_export=self.exported,
                revision_origin=SystemRevision.REVISION_ORIGIN_HUMAN_SYNC,
                parent_revision_id=str(self.baseline.id),
            )
            return self._unchanged_refinement_result()

        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            side_effect=sync_during_refinement,
        ), patch("model.experiment_pipeline.import_to_ai4mde") as importer:
            with self.assertRaises(RefinementConflictError):
                refine_selected_model(
                    None, selected_system_id=self.system_id, refinement_instruction="keep the flow"
                )

        importer.assert_not_called()
        self.assertNotEqual(System.objects.get(pk=self.system_id).current_revision_id, self.baseline.id)

    def test_revision_history_exposes_original_process_text(self):
        synchronize_human_edit(system_id=self.system_id)

        history = get_system_revisions(self.system_id)

        self.assertEqual(history["process_text"], PROCESS_TEXT)

    def test_synchronize_human_edit_endpoint_creates_human_sync_revision(self):
        action_classifier = System.objects.get(pk=self.system_id).classifiers.get(
            data__name="review request"
        )
        action_classifier.data["name"] = "validate request"
        action_classifier.save(update_fields=["data"])

        response = self.client.post(
            "/api/v1/synchronize-human-edit",
            data={"system_id": self.system_id},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["revision_origin"], SystemRevision.REVISION_ORIGIN_HUMAN_SYNC)
        self.assertEqual(payload["revision_index"], 1)
        self.assertEqual(payload["parent_revision_id"], str(self.baseline.id))
        self.assertEqual(
            payload["semantic_sketch_plan"]["root_actions"],
            [
                {
                    "slot_id": "ROOT_START",
                    "actions": [
                        {"action": "receive request"},
                        {"action": "validate request"},
                        {"action": "archive request"},
                    ],
                }
            ],
        )
        self.assertFalse(payload["synchronization_diagnostics"]["reused_current_revision_artifacts"])

        system = System.objects.get(pk=self.system_id)
        self.assertEqual(system.current_revision_id, SystemRevision.objects.get(revision_index=1).id)

    def test_sync_uses_canonical_actions_and_later_refinement_uses_synced_artifacts(self):
        synchronized = synchronize_human_edit(system_id=self.system_id)

        self.assertEqual(synchronized["revision_origin"], SystemRevision.REVISION_ORIGIN_HUMAN_SYNC)
        self.assertEqual(synchronized["semantic_sketch_plan"], SEMANTICS)
        synced_revision = SystemRevision.objects.get(pk=synchronized["revision_id"])

        updated_semantics = {
            "root_actions": [
                {
                    "slot_id": "ROOT_START",
                    "actions": [*SEMANTICS["root_actions"][0]["actions"], {"action": "notify requester"}],
                }
            ],
            "branch_plans": [],
        }
        updated_graph = {
            "nodes": [*GRAPH["nodes"][:-1], {"id": "n6", "type": "action", "name": "notify requester"}, GRAPH["nodes"][-1]],
            "edges": [*GRAPH["edges"][:-1], {"source": "n4", "target": "n6", "type": "control"}, {"source": "n6", "target": "n5", "type": "control"}],
        }
        refinement_result = {
            "artifact_diff": {},
            "updated_artifacts": {
                "updated_topology_artifact": TOPOLOGY,
                "updated_semantic_sketch_plan": updated_semantics,
                "refinement_trace": {"user_instruction": "notify requester"},
            },
            "clean_graph": updated_graph,
        }
        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            return_value=refinement_result,
        ) as semantic_refine, patch(
            "model.experiment_pipeline.refine_activity_model"
        ) as legacy_refine:
            refined = refine_selected_model(
                None,
                selected_system_id=self.system_id,
                refinement_instruction="notify requester",
            )

        semantic_refine.assert_called_once_with(
            PROCESS_TEXT,
            current_topology_artifact=synced_revision.topology_artifact,
            current_semantic_sketch_plan=synced_revision.semantic_sketch_plan,
            refinement_instruction="notify requester",
        )
        legacy_refine.assert_not_called()
        self.assertEqual(refined["revision_origin"], SystemRevision.REVISION_ORIGIN_AI_REFINEMENT)
        self.assertEqual(refined["parent_revision_id"], str(synced_revision.id))

    def test_synchronized_system_rejects_explicit_legacy_refinement_profile(self):
        synchronize_human_edit(system_id=self.system_id)

        with patch("model.experiment_pipeline.refine_activity_model") as legacy_refine:
            with self.assertRaisesMessage(ValueError, "require pipeline_profile='semantic_deterministic'"):
                refine_selected_model(
                    PROCESS_TEXT,
                    selected_system_id=self.system_id,
                    refinement_instruction="rewrite graph",
                    pipeline_profile="stable",
                )

        legacy_refine.assert_not_called()

    def test_sync_rolls_back_revision_and_current_pointer_when_sidecar_write_fails(self):
        with patch(
            "model.experiment_pipeline.persist_semantic_generation_artifacts",
            side_effect=RuntimeError("sidecar write failed"),
        ):
            with self.assertRaisesMessage(RuntimeError, "sidecar write failed"):
                synchronize_human_edit(system_id=self.system_id)

        system = System.objects.get(pk=self.system_id)
        self.assertEqual(system.current_revision_id, self.baseline.id)
        self.assertEqual(system.revisions.count(), 1)
        self.assertFalse(SystemGenerationArtifacts.objects.filter(system=system).exists())

    def test_restore_reinstates_artifacts_used_by_later_semantic_refinement(self):
        synchronized = synchronize_human_edit(system_id=self.system_id)
        restored = restore_revision(system_id=self.system_id, revision_id=str(self.baseline.id))
        self.assertEqual(restored["topology_artifact"], TOPOLOGY)
        self.assertEqual(restored["semantic_sketch_plan"], SEMANTICS)

        refinement_result = {
            "artifact_diff": {},
            "updated_artifacts": {
                "updated_topology_artifact": TOPOLOGY,
                "updated_semantic_sketch_plan": SEMANTICS,
                "refinement_trace": {},
            },
            "clean_graph": GRAPH,
        }
        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            return_value=refinement_result,
        ) as semantic_refine:
            refine_selected_model(
                None,
                selected_system_id=self.system_id,
                refinement_instruction="keep restored flow",
            )

        semantic_refine.assert_called_once_with(
            PROCESS_TEXT,
            current_topology_artifact=TOPOLOGY,
            current_semantic_sketch_plan=SEMANTICS,
            refinement_instruction="keep restored flow",
        )
        self.assertNotEqual(synchronized["revision_id"], str(self.baseline.id))


class GeneratedLoopBaselineComparisonTests(TestCase):
    """Generated label-only Decisions must not make layout edits look semantic."""

    def setUp(self):
        user = get_user_model().objects.create_user(
            username="loop-baseline-user", password="test-password"
        )
        _, token = create_token(user.username, "test-password")
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        self.project = Project.objects.create(name="Loop baseline project")
        self.system_id = str(uuid4())
        self.graph = {
            "nodes": [
                {"id": "n1", "type": "initial"},
                {"id": "n2", "type": "action", "name": "receive"},
                {"id": "n3", "type": "decision", "label": "route?"},
                {"id": "n4", "type": "action", "name": "finish"},
                {"id": "n5", "type": "decision", "label": "retry?"},
                {"id": "n6", "type": "action", "name": "repeat"},
                {"id": "n7", "type": "action", "name": "exit"},
                {"id": "n8", "type": "final"},
            ],
            "edges": [
                {"source": "n1", "target": "n2", "type": "control"},
                {"source": "n2", "target": "n3", "type": "control"},
                {"source": "n3", "target": "n4", "type": "control", "label": "done"},
                {"source": "n3", "target": "n5", "type": "control", "label": "repeat"},
                {"source": "n5", "target": "n6", "type": "control", "label": "retry"},
                {"source": "n6", "target": "n5", "type": "control"},
                {"source": "n5", "target": "n7", "type": "control", "label": "exit"},
                {"source": "n4", "target": "n8", "type": "control"},
                {"source": "n7", "target": "n8", "type": "control"},
            ],
        }
        self.exported = convert_to_ai4mde(
            clean_model=self.graph,
            system_id=self.system_id,
            diagram_id=str(uuid4()),
            name="Generated loop",
            project_id=str(self.project.id),
        )
        import_to_ai4mde(self.project, self.exported)
        self.baseline = create_system_revision(
            system_id=self.system_id,
            process_text=PROCESS_TEXT,
            pipeline_profile="semantic_deterministic",
            topology_artifact=TOPOLOGY,
            semantic_sketch_plan=SEMANTICS,
            activity_graph=self.graph,
            ai4mde_export=self.exported,
            revision_origin=SystemRevision.REVISION_ORIGIN_BASELINE,
        )

    def _sync(self):
        return self.client.post(
            "/api/v1/synchronize-human-edit",
            data={"system_id": self.system_id},
            content_type="application/json",
        )

    def _refinement_result(self):
        return {
            "artifact_diff": {},
            "updated_artifacts": {
                "updated_topology_artifact": TOPOLOGY,
                "updated_semantic_sketch_plan": SEMANTICS,
                "refinement_trace": {},
            },
            "clean_graph": self.graph,
        }

    def test_generated_decision_defaults_and_unchanged_loop_reuse_artifacts(self):
        decisions = [
            item["data"] for item in self.exported[0]["classifiers"]
            if item["data"]["type"] == "decision"
        ]
        self.assertEqual(len(decisions), 2)
        self.assertTrue(all(item["name"] == item["label"] for item in decisions))
        self.assertTrue(all("name" not in node for node in self.graph["nodes"]
                            if node["type"] == "decision"))

        response = self._sync()

        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()["synchronization_diagnostics"]["reused_current_revision_artifacts"])
        self.assertEqual(response.json()["revision_index"], 1)

    def test_layout_only_loop_edit_reuses_artifacts_and_refinement_can_start(self):
        node = System.objects.get(pk=self.system_id).diagrams.first().nodes.first()
        node.data["position"] = {"x": 900, "y": 400}
        node.save(update_fields=["data"])
        current_export = ExportSingleSystem.model_validate(
            System.objects.get(pk=self.system_id)
        ).model_dump(mode="json")
        self.assertEqual(
            _native_process_snapshot(current_export),
            _native_process_snapshot(self.baseline.ai4mde_export),
        )

        response = self._sync()

        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()["synchronization_diagnostics"]["reused_current_revision_artifacts"])
        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            side_effect=RuntimeError("offline planner reached"),
        ) as planner:
            with self.assertRaisesMessage(RuntimeError, "offline planner reached"):
                refine_selected_model(
                    None, selected_system_id=self.system_id,
                    refinement_instruction="keep the loop",
                )
        planner.assert_called_once()

    def test_layout_only_loop_edit_allows_direct_refinement(self):
        node = System.objects.get(pk=self.system_id).diagrams.first().nodes.first()
        node.data["position"] = {"x": 901, "y": 401}
        node.save(update_fields=["data"])

        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            side_effect=RuntimeError("offline planner reached"),
        ) as planner:
            with self.assertRaisesMessage(RuntimeError, "offline planner reached"):
                refine_selected_model(
                    None, selected_system_id=self.system_id,
                    refinement_instruction="keep the loop",
                )
        planner.assert_called_once()

    def test_real_action_edit_still_requires_sync_and_does_not_bypass_loop_validation(self):
        action = System.objects.get(pk=self.system_id).classifiers.get(data__name="receive")
        action.data["name"] = "review"
        action.save(update_fields=["data"])
        with patch("model.experiment_pipeline._run_semantic_refinement_from_artifacts") as planner:
            response = self.client.post(
                "/api/v1/refine-model",
                data={"system_id": self.system_id, "instruction": "keep the loop"},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "refinement_conflict")
        planner.assert_not_called()

        response = self._sync()
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["issues"][0]["code"], "missing_structure_closure")
        self.assertEqual(System.objects.get(pk=self.system_id).current_revision_id, self.baseline.id)

    def test_real_flow_and_unsupported_body_edits_are_not_ignored(self):
        system = System.objects.get(pk=self.system_id)
        flow = system.relations.first()
        flow.data["guard"] = "approved"
        flow.save(update_fields=["data"])
        action = system.classifiers.get(data__name="receive")
        action.data["body"] = "manual code"
        action.save(update_fields=["data"])

        with patch("model.experiment_pipeline._run_semantic_refinement_from_artifacts") as planner:
            response = self.client.post(
                "/api/v1/refine-model",
                data={"system_id": self.system_id, "instruction": "keep the loop"},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 409)
        planner.assert_not_called()
        self.assertEqual(self._sync().status_code, 422)
        self.assertEqual(System.objects.get(pk=self.system_id).current_revision_id, self.baseline.id)

    def test_preimport_guard_rejects_process_edit_but_ignores_layout(self):
        action = System.objects.get(pk=self.system_id).classifiers.get(data__name="receive")

        def edit_during_refinement(*args, **kwargs):
            action.data["name"] = "review"
            action.save(update_fields=["data"])
            return self._refinement_result()

        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            side_effect=edit_during_refinement,
        ), patch("model.experiment_pipeline.import_to_ai4mde") as importer:
            with self.assertRaises(RefinementConflictError):
                refine_selected_model(
                    None, selected_system_id=self.system_id,
                    refinement_instruction="keep the loop",
                )
        importer.assert_not_called()

        action.data["name"] = "receive"
        action.save(update_fields=["data"])
        node = System.objects.get(pk=self.system_id).diagrams.first().nodes.first()

        def move_during_refinement(*args, **kwargs):
            node.data["position"] = {"x": 902, "y": 402}
            node.save(update_fields=["data"])
            return self._refinement_result()

        with patch(
            "model.experiment_pipeline._run_semantic_refinement_from_artifacts",
            side_effect=move_during_refinement,
        ), patch(
            "model.experiment_pipeline.import_to_ai4mde",
            side_effect=RuntimeError("offline import reached"),
        ) as importer:
            with self.assertRaisesMessage(RuntimeError, "offline import reached"):
                refine_selected_model(
                    None, selected_system_id=self.system_id,
                    refinement_instruction="keep the loop",
                )
        importer.assert_called_once()
