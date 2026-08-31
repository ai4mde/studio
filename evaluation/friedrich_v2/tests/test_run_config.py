from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from evaluation.friedrich_v2.generation import (
    CohortInfrastructureError,
    PREFLIGHT_CASE_IDS,
    _load_or_create_state,
    build_generated_manifest,
    load_run_config,
    verify_generation_worktree,
)
from evaluation.friedrich_v2.runner import _validate_generated_manifest_for_run
from evaluation.friedrich_v2.runner import run as run_evaluation


ROOT = Path(__file__).resolve().parents[3]
V2 = ROOT / "evaluation" / "friedrich_v2"
SOURCE = V2 / "manifests" / "source_manifest.json"
PREFLIGHT = V2 / "config" / "v2_preflight_post_action_fix_20260831.json"
HISTORICAL_PREFLIGHT = V2 / "config" / "v2_preflight_20260830.json"
FORMAL = V2 / "config" / "v2_formal_47x3.template.json"


def _payload(path: Path = PREFLIGHT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_mutation(payload: dict) -> dict:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "run.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return load_run_config(path, SOURCE)


def _terminal_state(config: dict) -> dict:
    cases = {}
    for case_id in config["case_ids"]:
        cases[case_id] = {}
        for index in range(1, 4):
            candidate_id = f"candidate_{index}"
            cases[case_id][candidate_id] = {
                "candidate_id": candidate_id,
                "generation_status": "success",
                "attempts": [{"attempt_index": 1, "attempt_status": "success"}],
                "generated_model_path": f"/cohort/{case_id}/{candidate_id}/activity_graph.json",
                "generated_model_sha256": "0" * 64,
                "failure_reason": None,
                "failure_stage": None,
            }
    return {"cases": cases}


class VersionedRunConfigurationTests(unittest.TestCase):
    def test_superseded_preflight_remains_readable_historical_evidence(self):
        payload = json.loads(HISTORICAL_PREFLIGHT.read_text(encoding="utf-8"))
        self.assertEqual(
            hashlib.sha256(HISTORICAL_PREFLIGHT.read_bytes()).hexdigest(),
            "1e6bd8b463f18f5a578a0abe11d7c47df7f239f65d247342582f1aff22098126",
        )
        self.assertEqual(payload["generator_commit"], "6c835b99e7d73e62bc95ed40be0795329114609b")
        self.assertEqual(payload["generator_branch"], "codex/final-v2-integration")
        with self.assertRaisesRegex(ValueError, "generator commit differs"):
            load_run_config(HISTORICAL_PREFLIGHT, SOURCE)

    def test_historical_v1_configuration_is_byte_identical(self):
        import hashlib

        path = V2 / "config" / "small_validation_config.json"
        self.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "48d6657593c25227655f1a42d4871dea98a5002eef8ec01f094a8ae050279908",
        )

    def test_preflight_and_formal_case_sets_are_exact(self):
        preflight = load_run_config(PREFLIGHT, SOURCE)
        formal = load_run_config(FORMAL, SOURCE)
        self.assertEqual(tuple(preflight["case_ids"]), PREFLIGHT_CASE_IDS)
        self.assertEqual(len(formal["case_ids"]), 47)
        self.assertEqual(len(set(formal["case_ids"])), 47)
        self.assertEqual(preflight["preflight"]["status"], "ready_for_generation")
        self.assertEqual(formal["preflight"]["status"], "planned_not_authorized")

    def test_superseded_generator_commit_and_branch_are_rejected_for_new_runs(self):
        payload = _payload()
        payload["generator_commit"] = "6c835b99e7d73e62bc95ed40be0795329114609b"
        payload["generation"]["system_commit"] = payload["generator_commit"]
        with self.assertRaisesRegex(ValueError, "generator commit differs"):
            _load_mutation(payload)

        payload = _payload()
        payload["generator_branch"] = "codex/final-v2-integration"
        with self.assertRaisesRegex(ValueError, "generator branch differs"):
            _load_mutation(payload)

    def test_generator_worktree_identity_is_frozen(self):
        payload = _payload()
        payload["generator_worktree"] = "/tmp/different-worktree"
        with self.assertRaisesRegex(ValueError, "generator worktree differs"):
            _load_mutation(payload)

    def test_arbitrary_preflight_subset_is_rejected(self):
        payload = _payload()
        payload["case_ids"] = ["3-1", "3-3", "4-1"]
        with self.assertRaisesRegex(ValueError, "five frozen developmental cases"):
            _load_mutation(payload)

    def test_incomplete_formal_case_set_is_rejected(self):
        payload = _payload(FORMAL)
        payload["case_ids"] = payload["case_ids"][:-1]
        with self.assertRaisesRegex(ValueError, "all 47 source cases"):
            _load_mutation(payload)

    def test_frozen_generation_and_evaluation_values_cannot_change(self):
        mutations = (
            (("candidates_per_case",), 2, "3 candidates"),
            (("generation", "maximum_attempts_per_candidate"), 4, "maximum_attempts"),
            (("generation", "candidate_retry_policy"), "retry forever", "retry/failure policy"),
            (("evaluation", "action_model"), "different", "action_model"),
            (("evaluation", "action_model_revision"), "different", "action_model_revision"),
            (("evaluation", "action_threshold"), 0.9, "action_threshold"),
            (("evaluation", "human_review_seed"), 1, "human_review_seed"),
        )
        for keys, value, message in mutations:
            with self.subTest(keys=keys):
                payload = _payload()
                target = payload
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                with self.assertRaisesRegex(ValueError, message):
                    _load_mutation(payload)

    def test_historical_and_cross_run_output_roots_are_rejected(self):
        payload = _payload()
        payload["artifacts"]["output_root"] = (
            "evaluation/friedrich_v2/cohorts/small_validation_20260828"
        )
        with self.assertRaisesRegex(ValueError, "historical V1"):
            _load_mutation(payload)

        payload = _payload()
        payload["artifacts"]["results_output_root"] = (
            "evaluation/friedrich_v2/results/v2_formal_47x3"
        )
        with self.assertRaisesRegex(ValueError, "run_type=preflight"):
            _load_mutation(payload)

    def test_non_empty_generation_output_is_rejected(self):
        config = load_run_config(PREFLIGHT, SOURCE)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "cohort"
            output.mkdir()
            (output / "existing.txt").write_text("preserve", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "not empty"):
                _load_or_create_state(output, config, PREFLIGHT)

    def test_worktree_commit_mismatch_fails_before_generation(self):
        completed = SimpleNamespace(stdout="wrong-commit\n")
        with patch("evaluation.friedrich_v2.generation.subprocess.run", return_value=completed):
            with self.assertRaisesRegex(CohortInfrastructureError, "expected"):
                verify_generation_worktree("/tmp/worktree", "expected-commit")

    def test_manifest_shapes_and_stages(self):
        for path, expected_cases, expected_stage in (
            (PREFLIGHT, 5, "development_validation"),
            (FORMAL, 47, "final_baseline"),
        ):
            with self.subTest(path=path.name):
                config = load_run_config(path, SOURCE)
                manifest = build_generated_manifest(config, _terminal_state(config))
                self.assertEqual(len(manifest["cases"]), expected_cases)
                self.assertEqual(sum(len(case["candidates"]) for case in manifest["cases"]), expected_cases * 3)
                self.assertEqual(manifest["cohort_stage"], expected_stage)
                _validate_generated_manifest_for_run(config, manifest)

    def test_generated_manifest_identity_mismatch_is_rejected(self):
        config = load_run_config(PREFLIGHT, SOURCE)
        manifest = build_generated_manifest(config, _terminal_state(config))
        changed = deepcopy(manifest)
        changed["generation_provenance"]["generated_system_commit"] = "wrong"
        with self.assertRaisesRegex(ValueError, "commit differs"):
            _validate_generated_manifest_for_run(config, changed)

    def test_scoring_output_cannot_override_configured_result_root(self):
        payload = _payload()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "evaluation/friedrich_v2/config/v2_preflight_post_action_fix_20260831.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(json.dumps(payload), encoding="utf-8")
            args = SimpleNamespace(
                output_dir=str(root / "wrong-results"),
                source_manifest=str(SOURCE),
                generated_manifest=str(root / "not-read.json"),
                run_config=str(config_path),
                small_validation_config=None,
                action_model=payload["evaluation"]["action_model"],
                action_model_revision=payload["evaluation"]["action_model_revision"],
                action_threshold=payload["evaluation"]["action_threshold"],
                model_cache=str(root / "cache"),
                review_seed=payload["evaluation"]["human_review_seed"],
                review_file=None,
            )
            with self.assertRaisesRegex(ValueError, "Result output directory differs"):
                run_evaluation(args)


if __name__ == "__main__":
    unittest.main()
