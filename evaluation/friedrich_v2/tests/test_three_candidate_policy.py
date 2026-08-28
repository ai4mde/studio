from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from evaluation.friedrich_v2.core import AutomaticItem, EvalEdge, EvalGraph, EvalNode
from evaluation.friedrich_v2.human_review import REVIEW_FIELDS, build_review_rows
from evaluation.friedrich_v2.manifests import ManifestError, load_generated_manifest
from evaluation.friedrich_v2.runner import (
    CandidateInput,
    build_aggregate_summary,
    build_case_summary,
    evaluate_case_candidates,
)


class ExactSimilarity:
    def matrix(self, reference, generated):
        return [[1.0 if left == right else 0.0 for right in generated] for left in reference]


def simple_graph() -> EvalGraph:
    return EvalGraph(
        (EvalNode("a", "action", "first"), EvalNode("b", "action", "second")),
        (EvalEdge("a", "b"),),
    )


def valid_manifest() -> dict:
    return {
        "schema_version": "friedrich-v2-generated-manifest/v3",
        "cohort_id": "test-cohort",
        "cohort_stage": "development_validation",
        "condition": "ai_only_three_candidate_baseline",
        "expected_candidate_count": 3,
        "human_selection": False,
        "maximum_attempts_per_candidate": 3,
        "run_integrity_status": "valid",
        "generation_provenance": {
            "generated_system_commit": "8b3cdab756622cab7ecd1ed143b4a736d14f46ed",
            "pipeline_profile": "semantic_deterministic",
            "generation_configuration": "test",
            "model_identifier": "test-model",
            "runtime_environment": {"python": "3.12.1"},
            "retry_failure_policy": "no external retry",
        },
        "cases": [{
            "case_id": "1-1",
            "candidates": [
                {
                    "candidate_id": f"candidate_{index}",
                    "generation_index": index,
                    "generation_status": "success",
                    "attempt_count": 1,
                    "attempts": [{"attempt_index": 1, "attempt_status": "success"}],
                    "generated_model_path": f"/unused/candidate_{index}.json",
                    "generated_model_sha256": "0" * 64,
                    "failure_reason": None,
                    "failure_stage": None,
                }
                for index in range(1, 4)
            ],
        }],
    }


def candidate_row(case_id: str, candidate_id: str, value: float, tp: int = 1) -> dict:
    row = {
        "case_id": case_id, "candidate_id": candidate_id, "generation_status": "success",
        "attempt_count": 1, "failure_reason": None, "failure_stage": None,
    }
    for metric in ("action", "flow", "structure"):
        row.update({
            f"{metric}_tp": tp, f"{metric}_fp": 0, f"{metric}_fn": 0,
            f"{metric}_precision": value, f"{metric}_recall": value, f"{metric}_f1": value,
        })
    row.update({
        "flow_coverage": value, "structure_coverage": value,
        "redundant_control_node_count": 0, "unscorable_count": 0,
        "unscorable_status": "scorable",
    })
    return row


class ThreeCandidatePolicyTests(unittest.TestCase):
    def _load(self, payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return load_generated_manifest(path, {"1-1"}, verify_files=False)

    def test_exactly_three_candidates_are_required(self):
        self.assertEqual(len(self._load(valid_manifest())["cases"][0]["candidates"]), 3)

    def test_duplicate_candidate_ids_are_rejected(self):
        payload = valid_manifest()
        payload["cases"][0]["candidates"][2]["candidate_id"] = "candidate_2"
        with self.assertRaisesRegex(ManifestError, "duplicate or missing"):
            self._load(payload)

    def test_missing_candidate_is_rejected(self):
        payload = valid_manifest()
        payload["cases"][0]["candidates"].pop()
        with self.assertRaisesRegex(ManifestError, "exactly 3"):
            self._load(payload)

    def test_legacy_one_candidate_manifest_is_rejected(self):
        for schema in ("friedrich-v2-generated-manifest/v1", "friedrich-v2-generated-manifest/v2"):
            with self.subTest(schema=schema):
                payload = valid_manifest()
                payload["schema_version"] = schema
                payload["cases"] = [{"case_id": "1-1", "generated_model_path": "/old.json", "generated_model_sha256": "0" * 64}]
                with self.assertRaisesRegex(ManifestError, "V2 generated-input manifest"):
                    self._load(payload)

    def test_runner_evaluates_three_candidates_and_ids_do_not_collide(self):
        reference = simple_graph()
        generated = [
            CandidateInput(f"candidate_{index}", "success", 1,
                ({"attempt_index": 1, "attempt_status": "success"},), simple_graph())
            for index in range(1, 4)
        ]
        rows, items, _ = evaluate_case_candidates("1-1", reference, generated, ExactSimilarity(), 0.9)
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["candidate_id"] for row in rows}, {"candidate_1", "candidate_2", "candidate_3"})
        self.assertEqual({item.candidate_id for item in items}, {"candidate_1", "candidate_2", "candidate_3"})
        self.assertEqual(len({item.item_id for item in items}), len(items))

    def test_case_summary_calculates_mean_min_and_max(self):
        rows = [
            candidate_row("1-1", "candidate_1", 0.6),
            candidate_row("1-1", "candidate_2", 0.8),
            candidate_row("1-1", "candidate_3", 0.7),
        ]
        summary = build_case_summary(rows)[0]
        self.assertAlmostEqual(summary["flow_f1_mean"], 0.7)
        self.assertEqual(summary["flow_f1_min"], 0.6)
        self.assertEqual(summary["flow_f1_max"], 0.8)

    def test_aggregate_separates_case_and_candidate_counts(self):
        rows = [
            candidate_row(case_id, f"candidate_{index}", value)
            for case_id, value in (("1-1", 0.6), ("1-2", 0.8))
            for index in range(1, 4)
        ]
        cases = build_case_summary(rows)
        aggregate = build_aggregate_summary(rows, cases, 0, [], [])
        self.assertEqual(aggregate["case_count"], 2)
        self.assertEqual(aggregate["candidate_count"], 6)
        self.assertAlmostEqual(aggregate["model_quality"]["primary_complete_case_macro"]["flow"]["f1"], 0.7)

    def test_human_review_preserves_candidate_identity_and_sampling_is_deterministic(self):
        items = [
            AutomaticItem("1-1", f"candidate_{candidate}", "Flow",
                f"1-1:candidate_{candidate}:flow:tp:{index}", "TP", {}, {}, "preserved")
            for candidate in range(1, 4)
            for index in range(10)
        ]
        first = build_review_rows(items, seed=17)
        second = build_review_rows(items, seed=17)
        self.assertEqual(first, second)
        self.assertEqual({row["candidate_id"] for row in first}, {"candidate_1", "candidate_2", "candidate_3"})

    def test_review_adjustment_is_applied_to_only_one_candidate_before_aggregation(self):
        rows = [candidate_row("1-1", f"candidate_{index}", 1.0) for index in range(1, 4)]
        review = {field: "" for field in REVIEW_FIELDS}
        review.update({
            "case_id": "1-1", "candidate_id": "candidate_1", "metric": "Action",
            "item_id": "1-1:candidate_1:action:match:a:a", "automatic_label": "TP",
            "review_trigger": "seeded_tp_audit", "reviewer_verdict": "overturn",
        })
        aggregate = build_aggregate_summary(rows, build_case_summary(rows), 0, [], [review])
        adjusted = aggregate["review_adjusted_sensitivity"]
        self.assertAlmostEqual(adjusted["primary_complete_case_macro"]["action"]["f1"], 2 / 3)
        self.assertEqual(adjusted["secondary_successful_candidate_output_micro_aggregate"]["action"]["tp"], 2)


if __name__ == "__main__":
    unittest.main()
