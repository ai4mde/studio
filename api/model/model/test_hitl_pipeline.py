from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase

from llm.converter import convert_to_ai4mde
from metadata.models import (
    ProvisionalCandidate,
    Project,
    System,
    SystemGenerationArtifacts,
    SystemRevision,
    create_system_revision,
)
from model.experiment_pipeline import (
    import_to_ai4mde,
    refine_selected_model,
    restore_revision,
    run_pipeline,
    select_provisional_candidate,
    synchronize_human_edit,
)


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
        self.assertEqual(revision.candidate_index, 2)
        self.assertEqual(revision.candidate_count, 3)
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
