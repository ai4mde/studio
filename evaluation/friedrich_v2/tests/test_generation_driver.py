from __future__ import annotations

from collections import deque
import json
from pathlib import Path
import tempfile
import unittest

from evaluation.friedrich_v2.action import (
    ACTION_MODEL_NAME,
    ACTION_MODEL_REVISION,
    ACTION_SIMILARITY_THRESHOLD,
)
from evaluation.friedrich_v2.generation import (
    CohortInfrastructureError,
    GenerationInvocationError,
    build_generated_manifest,
    generate_candidate_slots,
    load_small_validation_config,
    run,
)
from evaluation.friedrich_v2.manifests import load_generated_manifest


def graph() -> dict:
    return {
        "nodes": [
            {"id": "start", "type": "initial", "name": None},
            {"id": "work", "type": "action", "name": "work"},
            {"id": "end", "type": "final", "name": None},
        ],
        "edges": [
            {"source": "start", "target": "work", "type": "control"},
            {"source": "work", "target": "end", "type": "control"},
        ],
    }


def response() -> dict:
    return {
        "mode": "baseline",
        "pipeline_profile": "semantic_deterministic",
        "use_experimental_compiler": False,
        "enable_sketch_review_agent": False,
        "enable_prompted_sketch_repair_agent": False,
        "enable_graph_repair_agent": False,
        "systems": [{
            "activity_graph": graph(),
            "topology_artifact": {"structures": []},
            "semantic_sketch_plan": {"steps": []},
            "executed_stages": ["Topology Artifact", "Semantic Planner", "Deterministic Compiler"],
            "import_error": None,
        }],
    }


def config() -> dict:
    return {
        "schema_version": "friedrich-v2-small-validation-config/v1",
        "cohort_id": "small-validation-test",
        "source": {},
        "generation": {
            "system_commit": "8b3cdab756622cab7ecd1ed143b4a736d14f46ed",
            "endpoint": "http://api.ai4mde.localhost/api/v1/generate-model",
            "mode": "baseline",
            "pipeline_profile": "semantic_deterministic",
            "response_mode": "full",
            "candidate_count": 3,
            "maximum_attempts_per_candidate": 3,
            "accept_first_valid_graph": True,
            "use_experimental_compiler": False,
            "enable_sketch_review_agent": False,
            "enable_prompted_sketch_repair_agent": False,
            "enable_graph_repair_agent": False,
            "human_selection": False,
            "topology_model": "gpt-4o",
            "semantic_model": "gpt-4o",
            "candidate_retry_policy": "maximum 3 complete top-level attempts; accept first valid graph",
            "request_timeout_seconds": 300,
        },
        "runtime": {"python": "3.12.1", "openai_sdk": "1.47.0"},
        "evaluation": {
            "action_model": ACTION_MODEL_NAME,
            "action_model_revision": ACTION_MODEL_REVISION,
            "action_threshold": ACTION_SIMILARITY_THRESHOLD,
        },
        "small_validation": {"case_ids": ["3-1", "3-6", "3-2", "3-3", "4-1"]},
        "preflight": {"status": "ready_for_generation"},
    }


class FakeGenerator:
    def __init__(self, outcomes):
        self.outcomes = deque(outcomes)
        self.calls = []

    def generate(self, process_text, request_payload):
        self.calls.append((process_text, dict(request_payload)))
        outcome = self.outcomes.popleft()
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class GenerationDriverTests(unittest.TestCase):
    def _fixture(self, directory: Path):
        source_cases = {}
        for case_id in config()["small_validation"]["case_ids"]:
            text_path = directory / f"{case_id}.txt"
            text_path.write_text(f"process {case_id}", encoding="utf-8")
            source_cases[case_id] = {"case_id": case_id, "process_text_path": str(text_path)}
        config_path = directory / "config.json"
        config_path.write_text(json.dumps(config()), encoding="utf-8")
        return config_path, source_cases

    def test_frozen_config_values_and_secret_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path, _ = self._fixture(Path(directory))
            loaded = load_small_validation_config(config_path)
            self.assertEqual(loaded["evaluation"]["action_threshold"], 0.44)
            unsafe = config()
            unsafe["generation"]["api_key"] = "must-not-appear"
            config_path.write_text(json.dumps(unsafe), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "secret fields"):
                load_small_validation_config(config_path)

    def test_candidate_scoped_attempts_preserve_identity_and_successes(self):
        failures = [
            GenerationInvocationError("temporary failure", stage="topology"),
            GenerationInvocationError("temporary failure", stage="semantic"),
        ]
        permanent = [GenerationInvocationError("invalid graph", stage="validation") for _ in range(3)]
        # The pattern is repeated for five cases: success on 1, success on 3, permanent failure.
        outcomes = []
        for _ in range(5):
            outcomes.extend([response(), *failures, response(), *permanent])
        fake = FakeGenerator(outcomes)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path, source_cases = self._fixture(root)
            output = root / "cohort"
            state = generate_candidate_slots(
                config=config(), config_path=config_path, source_cases=source_cases,
                output_root=output, generator=fake,
            )
            for case_id in config()["small_validation"]["case_ids"]:
                candidates = state["cases"][case_id]
                self.assertEqual(candidates["candidate_1"]["generation_status"], "success")
                self.assertEqual(len(candidates["candidate_1"]["attempts"]), 1)
                self.assertEqual(candidates["candidate_2"]["generation_status"], "success")
                self.assertEqual(len(candidates["candidate_2"]["attempts"]), 3)
                self.assertEqual(candidates["candidate_3"]["generation_status"], "failed")
                self.assertEqual(len(candidates["candidate_3"]["attempts"]), 3)
                self.assertIsNone(candidates["candidate_3"]["generated_model_path"])
            self.assertEqual(len(fake.calls), 35)
            self.assertTrue(all("process_text" not in payload for _, payload in fake.calls))
            self.assertTrue(all(payload["mode"] == "baseline" for _, payload in fake.calls))

            manifest = build_generated_manifest(config(), state)
            manifest_path = output / "generated_manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            loaded = load_generated_manifest(
                manifest_path, set(config()["small_validation"]["case_ids"]), verify_files=True
            )
            self.assertEqual(len(loaded["cases"]), 5)

            # A resume never invokes already-terminal candidate slots.
            resumed = FakeGenerator([])
            second = generate_candidate_slots(
                config=config(), config_path=config_path, source_cases=source_cases,
                output_root=output, generator=resumed,
            )
            self.assertEqual(second, state)
            self.assertEqual(resumed.calls, [])

    def test_invalid_activity_graph_consumes_one_attempt(self):
        invalid = response()
        invalid["systems"][0]["activity_graph"] = {"nodes": [], "edges": "invalid"}
        outcomes = []
        for _ in range(5):
            outcomes.extend([invalid, response(), response(), response()])
        fake = FakeGenerator(outcomes)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path, source_cases = self._fixture(root)
            state = generate_candidate_slots(
                config=config(), config_path=config_path, source_cases=source_cases,
                output_root=root / "cohort", generator=fake,
            )
            for case_id in config()["small_validation"]["case_ids"]:
                first = state["cases"][case_id]["candidate_1"]
                self.assertEqual([item["attempt_status"] for item in first["attempts"]], ["failed", "success"])
                self.assertEqual(first["candidate_id"], "candidate_1")

    def test_backend_configuration_mismatch_stops_the_cohort(self):
        mismatched = response()
        mismatched["pipeline_profile"] = "stable"
        fake = FakeGenerator([mismatched])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path, source_cases = self._fixture(root)
            with self.assertRaisesRegex(CohortInfrastructureError, "frozen request settings"):
                generate_candidate_slots(
                    config=config(), config_path=config_path, source_cases=source_cases,
                    output_root=root / "cohort", generator=fake,
                )

    def test_real_frozen_config_and_source_build_five_case_manifest_with_mocks(self):
        repository = Path(__file__).resolve().parents[3]
        config_path = repository / "evaluation/friedrich_v2/config/small_validation_config.json"
        source_path = repository / "evaluation/friedrich_v2/manifests/source_manifest.json"
        fake = FakeGenerator([response() for _ in range(15)])
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = run(config_path, source_path, Path(directory) / "cohort", fake)
            loaded = load_generated_manifest(
                manifest_path, {"3-1", "3-6", "3-2", "3-3", "4-1"}, verify_files=True
            )
            self.assertEqual(len(loaded["cases"]), 5)
            self.assertEqual(len(fake.calls), 15)

    def test_v2_preflight_config_builds_fifteen_slots_without_api(self):
        repository = Path(__file__).resolve().parents[3]
        source_path = repository / "evaluation/friedrich_v2/manifests/source_manifest.json"
        template_path = repository / "evaluation/friedrich_v2/config/v2_preflight_20260830.json"
        fake = FakeGenerator([response() for _ in range(15)])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "evaluation/friedrich_v2/config/v2_preflight_20260830.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_bytes(template_path.read_bytes())
            output = root / "evaluation/friedrich_v2/cohorts/v2_preflight_20260830"
            manifest_path = run(config_path, source_path, output, fake)
            loaded = load_generated_manifest(
                manifest_path, {"3-1", "3-6", "3-2", "3-3", "4-1"}, verify_files=True
            )
            self.assertEqual(len(loaded["cases"]), 5)
            self.assertEqual(sum(len(case["candidates"]) for case in loaded["cases"]), 15)
            self.assertEqual(loaded["generation_provenance"]["generated_system_commit"],
                             "6c835b99e7d73e62bc95ed40be0795329114609b")
            self.assertEqual(len(fake.calls), 15)


if __name__ == "__main__":
    unittest.main()
