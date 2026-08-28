from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from evaluation.friedrich_v2.core import EvalEdge, EvalGraph, EvalNode
from evaluation.friedrich_v2.human_review import build_review_rows
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


class UnexpectedSimilarity:
    def matrix(self, reference, generated):
        raise AssertionError("Failed candidates must not reach metric evaluation")


def graph() -> EvalGraph:
    return EvalGraph(
        (EvalNode("a", "action", "first"), EvalNode("b", "action", "second")),
        (EvalEdge("a", "b"),),
    )


def attempt_records(count: int, success: bool) -> list[dict]:
    return [
        {
            "attempt_index": index,
            "attempt_status": "success" if success and index == count else "failed",
            **({"failure_reason": "no valid graph", "failure_stage": "validation"}
               if not (success and index == count) else {}),
        }
        for index in range(1, count + 1)
    ]


def candidate_record(candidate_id: str, count: int, success: bool) -> dict:
    return {
        "candidate_id": candidate_id,
        "generation_index": int(candidate_id.rsplit("_", 1)[1]),
        "generation_status": "success" if success else "failed",
        "attempt_count": count,
        "attempts": attempt_records(count, success),
        "generated_model_path": f"/unused/{candidate_id}.json" if success else None,
        "generated_model_sha256": "0" * 64 if success else None,
        "failure_reason": None if success else "no valid graph after 3 attempts",
        "failure_stage": None if success else "validation",
    }


def manifest(candidates: list[dict]) -> dict:
    return {
        "schema_version": "friedrich-v2-generated-manifest/v3",
        "cohort_id": "failure-policy-test",
        "cohort_stage": "development_validation",
        "condition": "ai_only_three_candidate_baseline",
        "expected_candidate_count": 3,
        "human_selection": False,
        "maximum_attempts_per_candidate": 3,
        "run_integrity_status": "valid",
        "generation_provenance": {
            "generated_system_commit": "commit",
            "pipeline_profile": "semantic_deterministic",
            "generation_configuration": "test",
            "model_identifier": "test-model",
            "runtime_environment": "test-runtime",
            "retry_failure_policy": "maximum 3 complete top-level attempts",
        },
        "cases": [{"case_id": "1-1", "candidates": candidates}],
    }


def input_candidate(candidate_id: str, success: bool, attempt_count: int) -> CandidateInput:
    attempts = tuple(attempt_records(attempt_count, success))
    return CandidateInput(
        candidate_id=candidate_id,
        generation_status="success" if success else "failed",
        attempt_count=attempt_count,
        attempts=attempts,
        graph=graph() if success else None,
        failure_reason=None if success else "no valid graph after 3 attempts",
        failure_stage=None if success else "validation",
    )


def case_inputs(success_count: int) -> list[CandidateInput]:
    return [
        input_candidate(
            f"candidate_{index}",
            success=index <= success_count,
            attempt_count=index if index <= success_count else 3,
        )
        for index in range(1, 4)
    ]


class GenerationFailureTests(unittest.TestCase):
    def _load(self, payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return load_generated_manifest(path, {"1-1"}, verify_files=False)

    def test_success_is_valid_on_attempts_one_two_and_three(self):
        candidates = [
            candidate_record(f"candidate_{index}", index, True)
            for index in range(1, 4)
        ]
        loaded = self._load(manifest(candidates))
        self.assertEqual([item["attempt_count"] for item in loaded["cases"][0]["candidates"]], [1, 2, 3])

    def test_permanent_failure_after_three_attempts_needs_no_artifact(self):
        candidates = [
            candidate_record("candidate_1", 1, True),
            candidate_record("candidate_2", 2, True),
            candidate_record("candidate_3", 3, False),
        ]
        loaded = self._load(manifest(candidates))
        failed = loaded["cases"][0]["candidates"][2]
        self.assertIsNone(failed["generated_model_path"])
        self.assertIsNone(failed["generated_model_sha256"])

    def test_successful_candidate_requires_path_and_hash(self):
        candidates = [candidate_record(f"candidate_{index}", 1, True) for index in range(1, 4)]
        candidates[0]["generated_model_path"] = None
        with self.assertRaisesRegex(ManifestError, "requires path and hash"):
            self._load(manifest(candidates))

    def test_candidate_identity_is_preserved_across_attempts(self):
        candidates = [
            candidate_record("candidate_1", 1, True),
            candidate_record("candidate_2", 3, True),
            candidate_record("candidate_3", 1, True),
        ]
        loaded = self._load(manifest(candidates))
        candidate = loaded["cases"][0]["candidates"][1]
        self.assertEqual(candidate["candidate_id"], "candidate_2")
        self.assertEqual([item["attempt_index"] for item in candidate["attempts"]], [1, 2, 3])

    def test_invalid_run_integrity_is_rejected_before_evaluation(self):
        payload = manifest([candidate_record(f"candidate_{index}", 1, True) for index in range(1, 4)])
        payload["run_integrity_status"] = "invalid"
        with self.assertRaisesRegex(ManifestError, "infrastructure preflight"):
            self._load(payload)

    def test_failed_candidate_metrics_are_na_and_no_metric_items_are_created(self):
        rows, items, _ = evaluate_case_candidates(
            "1-1", graph(), case_inputs(2), ExactSimilarity(), 0.9
        )
        failed = next(row for row in rows if row["candidate_id"] == "candidate_3")
        self.assertEqual(len(rows), 3)
        self.assertIsNone(failed["action_tp"])
        self.assertIsNone(failed["flow_f1"])
        self.assertIsNone(failed["structure_f1"])
        failed_items = [item for item in items if item.candidate_id == "candidate_3"]
        self.assertEqual([(item.metric, item.label) for item in failed_items], [("Generation", "FAILED")])

    def test_all_failed_candidates_skip_similarity_and_api_style_retry_behavior(self):
        rows, items, _ = evaluate_case_candidates(
            "1-1", graph(), case_inputs(0), UnexpectedSimilarity(), 0.9
        )
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(items), 3)
        self.assertTrue(all(item.metric == "Generation" for item in items))

    def test_case_statuses_and_secondary_only_incomplete_scores(self):
        expected = {3: "complete", 2: "incomplete", 1: "incomplete", 0: "failed"}
        for success_count, status in expected.items():
            with self.subTest(success_count=success_count):
                rows, _, _ = evaluate_case_candidates(
                    "1-1", graph(), case_inputs(success_count),
                    ExactSimilarity() if success_count else UnexpectedSimilarity(), 0.9,
                )
                summary = build_case_summary(rows)[0]
                self.assertEqual(summary["case_status"], status)
                if status == "complete":
                    self.assertEqual(summary["action_f1_mean"], 1.0)
                else:
                    self.assertIsNone(summary["action_f1_mean"])
                if success_count:
                    self.assertEqual(summary["secondary_successful_action_f1_mean"], 1.0)
                else:
                    self.assertIsNone(summary["secondary_successful_action_f1_mean"])

    def test_reliability_denominators_attempt_breakdown_and_complete_case_macro(self):
        candidate_rows = []
        case_rows = []
        all_items = []
        for case_id, success_count in (("complete", 3), ("two", 2), ("one", 1), ("failed", 0)):
            rows, items, _ = evaluate_case_candidates(
                case_id, graph(), case_inputs(success_count),
                ExactSimilarity() if success_count else UnexpectedSimilarity(), 0.9,
            )
            if case_id != "complete":
                for row in rows:
                    if row["generation_status"] == "success":
                        row["action_f1"] = 0.2
            candidate_rows.extend(rows)
            case_rows.extend(build_case_summary(rows))
            all_items.extend(items)
        aggregate = build_aggregate_summary(
            candidate_rows, case_rows, 0, build_review_rows(all_items, 9), []
        )
        reliability = aggregate["generation_reliability"]
        self.assertEqual(reliability["expected_candidates"], 12)
        self.assertEqual(reliability["successful_candidates"], 6)
        self.assertEqual(reliability["failed_candidates"], 6)
        self.assertEqual(reliability["generation_success_rate"], 0.5)
        self.assertEqual(reliability["complete_cases"], 1)
        self.assertEqual(reliability["incomplete_cases"], 2)
        self.assertEqual(reliability["failed_cases"], 1)
        self.assertEqual(reliability["complete_case_rate"], 0.25)
        self.assertEqual(reliability["attempt_breakdown"], {
            "succeeded_on_attempt_1": 3,
            "succeeded_on_attempt_2": 2,
            "succeeded_on_attempt_3": 1,
            "failed_after_attempt_3": 6,
        })
        quality = aggregate["model_quality"]
        self.assertEqual(quality["primary_macro_denominator"], 1)
        self.assertEqual(quality["primary_complete_case_macro"]["action"]["f1"], 1.0)
        self.assertEqual(quality["secondary_successful_candidate_denominator"], 6)

    def test_generation_failure_creates_one_candidate_aware_review_row(self):
        _, items, _ = evaluate_case_candidates(
            "1-1", graph(), case_inputs(2), ExactSimilarity(), 0.9
        )
        review = [row for row in build_review_rows(items, 12) if row["metric"] == "Generation"]
        self.assertEqual(len(review), 1)
        self.assertEqual(review[0]["candidate_id"], "candidate_3")
        self.assertEqual(review[0]["review_trigger"], "generation_failure_audit")
        self.assertEqual(review[0]["generation_status"], "failed")
        self.assertEqual(review[0]["attempt_count"], "3")


if __name__ == "__main__":
    unittest.main()
