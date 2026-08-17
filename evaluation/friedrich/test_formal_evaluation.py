from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from . import formal_evaluation
from .action_scoring import score_action_case
from .control_flow_scoring import score_control_flow_case
from .control_structure_scoring import score_control_structure_case
from .eval_graph import EvalGraph, EvalNode
from .formal_evaluation import (
    EXPECTED_CASE_IDS,
    FORMAL_MANIFEST_SHA256,
    GENERATED_ARTIFACT_MANIFEST_SHA256,
    METRIC_STATUSES,
    UNSUPPORTED_CASES,
    FormalEvaluationError,
    PreflightResult,
    _case_record,
    _strict_generated_graph,
    _verify_execution_repository,
    build_dataset_summary,
    preflight_case,
    sha256_file,
    unsupported_case_record,
    validate_manifest_documents,
)


def _artifact(case_id: str, node_type: str = "action") -> dict[str, object]:
    return {
        "case_id": case_id,
        "run_number": 1,
        "request_configuration": {
            "pipeline_profile": "semantic_deterministic",
            "use_experimental_compiler": False,
            "mode": "baseline",
        },
        "generation_status": "completed",
        "api_status_code": 200,
        "nodes": [{"id": "n1", "type": node_type, "name": "do work"}],
        "edges": [],
    }


class FormalEvaluationPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = Path(__file__).resolve().parent / "formal_inputs" / "v1"
        cls.formal_path = cls.base / "formal_manifest.json"
        cls.artifact_path = cls.base / "generated_artifact_manifest.json"
        cls.formal = json.loads(cls.formal_path.read_text(encoding="utf-8"))
        cls.artifacts = json.loads(cls.artifact_path.read_text(encoding="utf-8"))

    def test_manifest_has_exact_frozen_denominator(self) -> None:
        cases, artifacts = validate_manifest_documents(self.formal, self.artifacts)
        self.assertEqual(len(cases), 47)
        self.assertEqual(len(artifacts), 47)
        self.assertEqual(set(cases), EXPECTED_CASE_IDS)
        self.assertEqual(sum(bool(item["action_supported"]) for item in cases.values()), 40)
        self.assertEqual(
            {case_id for case_id, item in cases.items() if not item["action_supported"]},
            set(UNSUPPORTED_CASES),
        )

    def test_every_generated_selection_is_run_one(self) -> None:
        self.assertTrue(
            all(Path(item["generated_path"]).name == "run_1.json" for item in self.formal["cases"])
        )
        self.assertTrue(
            all(
                Path(item["generated_artifact_path"]).name == "run_1.json"
                for item in self.artifacts["artifacts"]
            )
        )

    def test_duplicate_case_id_fails_manifest_validation(self) -> None:
        formal = deepcopy(self.formal)
        formal["cases"][-1] = deepcopy(formal["cases"][0])
        with self.assertRaisesRegex(FormalEvaluationError, "duplicate case IDs"):
            validate_manifest_documents(formal, self.artifacts)

    def test_manifest_policy_metadata_is_fixed(self) -> None:
        formal = deepcopy(self.formal)
        formal["generated_selection_rule"] = "best of three"
        with self.assertRaisesRegex(FormalEvaluationError, "generated_selection_rule"):
            validate_manifest_documents(formal, self.artifacts)

    def test_unknown_generated_node_type_fails_fast(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run_1.json"
            path.write_text(json.dumps(_artifact("x", "mystery")), encoding="utf-8")
            with self.assertRaisesRegex(FormalEvaluationError, "unknown generated node type"):
                _strict_generated_graph(path, "x")

    def test_artifact_hash_mismatch_fails_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "reference.xml"
            generated = root / "run_1.json"
            reference.write_text("<root />", encoding="utf-8")
            generated.write_text(json.dumps(_artifact("x")), encoding="utf-8")
            entry = {
                "case_id": "x",
                "reference_path": str(reference),
                "reference_sha256": sha256_file(reference),
                "generated_path": str(generated),
                "generated_sha256": "0" * 64,
                "action_supported": True,
            }
            with self.assertRaisesRegex(FormalEvaluationError, "generated hash mismatch"):
                preflight_case(entry)

    def test_supported_reference_parse_failure_is_not_silent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "reference.xml"
            generated = root / "run_1.json"
            reference.write_text("not xml", encoding="utf-8")
            generated.write_text(json.dumps(_artifact("x")), encoding="utf-8")
            entry = {
                "case_id": "x",
                "reference_path": str(reference),
                "reference_sha256": sha256_file(reference),
                "generated_path": str(generated),
                "generated_sha256": sha256_file(generated),
                "action_supported": True,
            }
            with self.assertRaisesRegex(FormalEvaluationError, "reference adapter failed"):
                preflight_case(entry)

    def test_unsupported_cases_remain_visible_and_unscored(self) -> None:
        records = [
            unsupported_case_record(case_id, reason)
            for case_id, reason in sorted(UNSUPPORTED_CASES.items())
        ]
        self.assertEqual(len(records), 7)
        for record in records:
            self.assertEqual(record["action_status"], "unsupported")
            self.assertEqual(record["flow_status"], "unsupported")
            self.assertEqual(record["control_structure_status"], "unsupported")
            self.assertIsNone(record["action"])
            self.assertFalse(record["included_in_action_aggregate"])
            self.assertTrue(record["status_reason"])

    def test_metric_status_vocabulary_is_fixed(self) -> None:
        self.assertEqual(
            METRIC_STATUSES,
            {
                "scored",
                "unsupported",
                "reference_parse_failure",
                "generated_artifact_failure",
                "evaluation_error",
            },
        )

    def test_dataset_aggregation_excludes_unsupported_records(self) -> None:
        reference = EvalGraph(nodes=(EvalNode("r", "action", "work"),), edges=())
        generated = EvalGraph(nodes=(EvalNode("g", "action", "work"),), edges=())
        action = score_action_case(
            "x",
            reference,
            generated,
            [{"case_id": "x", "reference_id": "r", "generated_id": "g", "final_prediction": True}],
        )
        flow = score_control_flow_case("x", reference, generated, action)
        structure = score_control_structure_case("x", reference, generated, action)
        case_record = _case_record("x", action, flow, structure)
        self.assertEqual(case_record["action"]["unresolved_reference_count"], 0)
        self.assertIn(
            "unmatched_or_unresolved_incident_diagnostics", case_record["flow"]
        )
        scored_records = [
            {
                "case_id": f"s{index}",
                "action_status": "scored",
                "flow_status": "scored",
                "control_structure_status": "scored",
            }
            for index in range(40)
        ]
        unsupported_records = [
            unsupported_case_record(case_id, reason)
            for case_id, reason in sorted(UNSUPPORTED_CASES.items())
        ]
        summary = build_dataset_summary(
            scored_records + unsupported_records,
            [action] * 40,
            [flow] * 40,
            [structure] * 40,
            {"test": True},
        )
        self.assertEqual(summary["dataset_total_cases"], 47)
        self.assertEqual(summary["supported_cases"], 40)
        self.assertEqual(summary["unsupported_cases"], 7)
        self.assertEqual(summary["action"]["micro_TP"], 40)
        self.assertEqual(summary["action"]["micro_f1"], 1.0)
        self.assertIsNone(summary["control_flow"]["micro_f1"])
        self.assertIsNone(summary["control_structure"]["micro_f1"])

    def test_manifest_files_have_stable_hashes(self) -> None:
        self.assertEqual(
            hashlib.sha256(self.formal_path.read_bytes()).hexdigest(),
            FORMAL_MANIFEST_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(self.artifact_path.read_bytes()).hexdigest(),
            GENERATED_ARTIFACT_MANIFEST_SHA256,
        )

    def test_preflight_mode_never_calls_formal_execution(self) -> None:
        preflight = PreflightResult(
            cases=(),
            formal_manifest_sha256=FORMAL_MANIFEST_SHA256,
            generated_artifact_manifest_sha256=GENERATED_ARTIFACT_MANIFEST_SHA256,
        )
        with (
            patch.object(formal_evaluation, "run_preflight", return_value=preflight),
            patch.object(formal_evaluation, "execute_formal") as execute,
            patch.object(sys, "argv", ["formal_evaluation", "--preflight-only"]),
            redirect_stdout(StringIO()),
        ):
            formal_evaluation.main()
        execute.assert_not_called()

    def test_formal_execution_rejects_dirty_repository(self) -> None:
        with patch.object(
            formal_evaluation,
            "_git_value",
            side_effect=["feature/friedrich-evaluation", "?? unexpected-file"],
        ):
            with self.assertRaisesRegex(FormalEvaluationError, "clean worktree"):
                _verify_execution_repository(Path("/repository"))


if __name__ == "__main__":
    unittest.main()
