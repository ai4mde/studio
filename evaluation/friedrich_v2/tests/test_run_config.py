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
    FORMAL_EXCLUDED_CASE_REASONS,
    FORMAL_SUPPORTED_CASE_IDS,
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
PREFLIGHT = V2 / "config" / "v2_preflight_stable_final_20260831.json"
HISTORICAL_PREFLIGHT = V2 / "config" / "v2_preflight_20260830.json"
HISTORICAL_CORRECTED_PREFLIGHT = V2 / "config" / "v2_preflight_post_action_fix_20260831.json"
HISTORICAL_FORMAL = V2 / "config" / "v2_formal_47x3.template.json"
FORMAL = V2 / "config" / "v2_formal_40x3_20260901.json"
CONTROLLED_V1 = V2 / "config" / "v1_controlled_40x3_20260901.json"


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
        with self.assertRaisesRegex(ValueError, "evaluation_version"):
            load_run_config(HISTORICAL_PREFLIGHT, SOURCE)

    def test_historical_v1_configuration_is_byte_identical(self):
        import hashlib

        path = V2 / "config" / "small_validation_config.json"
        self.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "48d6657593c25227655f1a42d4871dea98a5002eef8ec01f094a8ae050279908",
        )

    def test_corrected_action_preflight_remains_readable_historical_evidence(self):
        payload = json.loads(HISTORICAL_CORRECTED_PREFLIGHT.read_text(encoding="utf-8"))
        self.assertEqual(
            hashlib.sha256(HISTORICAL_CORRECTED_PREFLIGHT.read_bytes()).hexdigest(),
            "0e6966d0e56ee6551347f3f15cc15014cf7b6c78240e9cefbdf4749eb9985fbb",
        )
        self.assertEqual(payload["generator_commit"], "56e82629f7cf45358049cb3b8bd2c34e5ac12684")
        self.assertEqual(payload["generator_branch"], "feature/final-v2-integration")
        with self.assertRaisesRegex(ValueError, "evaluation_version"):
            load_run_config(HISTORICAL_CORRECTED_PREFLIGHT, SOURCE)

    def test_preflight_and_supported_formal_case_sets_are_exact(self):
        preflight = load_run_config(PREFLIGHT, SOURCE)
        formal = load_run_config(FORMAL, SOURCE)
        controlled_v1 = load_run_config(CONTROLLED_V1, SOURCE)
        self.assertEqual(tuple(preflight["case_ids"]), PREFLIGHT_CASE_IDS)
        self.assertEqual(tuple(formal["case_ids"]), FORMAL_SUPPORTED_CASE_IDS)
        self.assertEqual(tuple(controlled_v1["case_ids"]), FORMAL_SUPPORTED_CASE_IDS)
        self.assertEqual(len(formal["case_ids"]), 40)
        self.assertEqual(len(set(formal["case_ids"])), 40)
        for config in (formal, controlled_v1):
            self.assertEqual(config["candidates_per_case"], 3)
            self.assertEqual(config["evaluation_support"]["formal_reporting_n"], 40)
            self.assertEqual(config["evaluation_support"]["formal_candidate_slots"], 120)
            self.assertEqual(
                [item["case_id"] for item in config["evaluation_support"]["excluded_cases"]],
                list(FORMAL_EXCLUDED_CASE_REASONS),
            )
            self.assertTrue(set(FORMAL_EXCLUDED_CASE_REASONS).isdisjoint(config["case_ids"]))
        self.assertEqual(preflight["preflight"]["status"], "ready_for_generation")
        self.assertEqual(formal["preflight"]["status"], "ready_for_generation")
        self.assertEqual(controlled_v1["preflight"]["status"], "ready_for_generation")

    def test_generator_identities_are_separately_allowlisted(self):
        final_v2 = load_run_config(FORMAL, SOURCE)
        controlled_v1 = load_run_config(CONTROLLED_V1, SOURCE)
        self.assertEqual(final_v2["evaluation_version"], "Revised Generator V2 / Final V2")
        self.assertEqual(final_v2["generator_commit"], "4be4c5b7b30aaff0433d4406056a0cf5c8fc63a9")
        self.assertEqual(final_v2["generator_branch"], "feature/final-v2-stable")
        self.assertEqual(controlled_v1["evaluation_version"], "Initial Stable Generator V1")
        self.assertEqual(controlled_v1["generator_commit"], "8b3cdab756622cab7ecd1ed143b4a736d14f46ed")
        self.assertEqual(controlled_v1["generator_branch"], "feature/thesis-ui-isolation")

    def test_cross_version_generator_identities_are_rejected(self):
        final_v2 = _payload(FORMAL)
        controlled_v1 = _payload(CONTROLLED_V1)

        mislabeled_v1 = deepcopy(controlled_v1)
        for field in ("evaluation_version", "generator_commit", "generator_branch", "generator_worktree"):
            mislabeled_v1[field] = final_v2[field]
        mislabeled_v1["generation"]["system_commit"] = final_v2["generator_commit"]
        with self.assertRaisesRegex(ValueError, "V1 evaluation_version differs"):
            _load_mutation(mislabeled_v1)

        mislabeled_v2 = deepcopy(final_v2)
        for field in ("evaluation_version", "generator_commit", "generator_branch", "generator_worktree"):
            mislabeled_v2[field] = controlled_v1[field]
        mislabeled_v2["generation"]["system_commit"] = controlled_v1["generator_commit"]
        with self.assertRaisesRegex(ValueError, "V2 evaluation_version differs"):
            _load_mutation(mislabeled_v2)

        mislabeled_repository = deepcopy(controlled_v1)
        mislabeled_repository["generation"]["repository_identity"] = (
            final_v2["generation"]["repository_identity"]
        )
        with self.assertRaisesRegex(ValueError, "V1 generator repository identity differs"):
            _load_mutation(mislabeled_repository)

    def test_controlled_v1_and_final_v2_share_frozen_protocol(self):
        final_v2 = load_run_config(FORMAL, SOURCE)
        controlled_v1 = load_run_config(CONTROLLED_V1, SOURCE)
        self.assertEqual(controlled_v1["case_ids"], final_v2["case_ids"])
        self.assertEqual(controlled_v1["evaluation_support"], final_v2["evaluation_support"])
        self.assertEqual(controlled_v1["candidates_per_case"], final_v2["candidates_per_case"])
        self.assertEqual(controlled_v1["generation"]["candidate_count"], 3)
        self.assertEqual(
            controlled_v1["generation"]["maximum_attempts_per_candidate"],
            final_v2["generation"]["maximum_attempts_per_candidate"],
        )
        self.assertEqual(
            controlled_v1["generation"]["candidate_retry_policy"],
            final_v2["generation"]["candidate_retry_policy"],
        )
        for field in (
            "action_model", "action_model_revision", "action_threshold", "human_review_seed",
            "failure_policy", "aggregation_policy",
        ):
            self.assertEqual(controlled_v1["evaluation"][field], final_v2["evaluation"][field])

    def test_historical_formal_and_stability_configs_are_unchanged(self):
        expected = {
            HISTORICAL_FORMAL: "bb423b4a3a2ba3c383c5739900c993f6f45ff2027664e00247b5aa948afcafd1",
            V2 / "config" / "v2_stability_47x1_20260831.json": (
                "9f53b958457aad525ae04034e4ed6d1341b7f3617db8eaf1ec09539ebb7d0d96"
            ),
        }
        self.assertEqual(
            {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in expected},
            expected,
        )

    def test_superseded_generator_commit_and_branch_are_rejected_for_new_runs(self):
        payload = _payload()
        payload["generator_commit"] = "56e82629f7cf45358049cb3b8bd2c34e5ac12684"
        payload["generation"]["system_commit"] = payload["generator_commit"]
        with self.assertRaisesRegex(ValueError, "generator commit differs"):
            _load_mutation(payload)

        payload = _payload()
        payload["generator_branch"] = "feature/final-v2-integration"
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
        for path in (FORMAL, CONTROLLED_V1):
            with self.subTest(path=path.name):
                payload = _payload(path)
                payload["case_ids"] = payload["case_ids"][:-1]
                with self.assertRaisesRegex(ValueError, "40 supported formal cases"):
                    _load_mutation(payload)

    def test_excluded_cases_and_changed_support_provenance_are_rejected(self):
        payload = _payload(FORMAL)
        payload["case_ids"][0] = "1-3"
        with self.assertRaisesRegex(ValueError, "40 supported formal cases"):
            _load_mutation(payload)

        payload = _payload(FORMAL)
        payload["evaluation_support"]["formal_reporting_n"] = 47
        with self.assertRaisesRegex(ValueError, "evaluation-support provenance"):
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
            (FORMAL, 40, "final_baseline"),
            (CONTROLLED_V1, 40, "final_baseline"),
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
            config_path = root / "evaluation/friedrich_v2/config/v2_preflight_stable_final_20260831.json"
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
