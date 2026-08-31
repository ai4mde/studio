from __future__ import annotations

import ast
from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from evaluation.friedrich_v2.generation import (
    CohortInfrastructureError,
    GenerationInvocationError,
)
from evaluation.friedrich_v2.generation_stability import (
    CANDIDATE_ID,
    build_manifest,
    generate,
    load_config,
)
from evaluation.friedrich_v2.manifests import load_source_manifest


ROOT = Path(__file__).resolve().parents[3]
V2 = ROOT / "evaluation" / "friedrich_v2"
CONFIG = V2 / "config" / "v2_stability_47x1_20260831.json"
SOURCE = V2 / "manifests" / "source_manifest.json"
SNAPSHOT = V2 / "generation_stability_snapshot.json"


def _graph() -> dict:
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


def _response() -> dict:
    return {
        "mode": "baseline",
        "pipeline_profile": "semantic_deterministic",
        "use_experimental_compiler": False,
        "enable_sketch_review_agent": False,
        "enable_prompted_sketch_repair_agent": False,
        "enable_graph_repair_agent": False,
        "systems": [{
            "activity_graph": _graph(),
            "topology_artifact": {"structures": []},
            "semantic_sketch_plan": {"steps": []},
            "ai4mde": [{"id": "imported-system"}],
            "technical_validity": {"status": "accepted"},
            "executed_stages": ["Topology Artifact", "Semantic Planner", "Deterministic Compiler"],
            "import_error": None,
        }],
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


def _source_cases() -> dict[str, dict]:
    source = load_source_manifest(SOURCE, verify_files=True)
    return {case["case_id"]: case for case in source["cases"]}


def _load_mutation(payload: dict) -> dict:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "config.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return load_config(path, SOURCE, SNAPSHOT)


class GenerationStabilityConfigurationTests(unittest.TestCase):
    def test_exact_frozen_47x1_identity_loads(self):
        config = load_config(CONFIG, SOURCE, SNAPSHOT)
        self.assertEqual(config["run_type"], "generation_stability_47x1")
        self.assertEqual(len(config["case_ids"]), 47)
        self.assertEqual(len(set(config["case_ids"])), 47)
        self.assertEqual(config["candidates_per_case"], 1)
        self.assertEqual(config["generation"]["maximum_attempts_per_candidate"], 3)
        self.assertEqual(config["generator"]["commit"], "4be4c5b7b30aaff0433d4406056a0cf5c8fc63a9")

    def test_subset_and_candidate_count_are_rejected(self):
        payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        subset = deepcopy(payload)
        subset["case_ids"] = subset["case_ids"][:-1]
        with self.assertRaisesRegex(ValueError, "exactly all 47"):
            _load_mutation(subset)
        count = deepcopy(payload)
        count["candidates_per_case"] = 3
        with self.assertRaisesRegex(ValueError, "exactly 1 candidate"):
            _load_mutation(count)

    def test_generator_identity_and_retry_policy_are_rejected_if_changed(self):
        payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        identity = deepcopy(payload)
        identity["generator"]["commit"] = "8b3cdab756622cab7ecd1ed143b4a736d14f46ed"
        with self.assertRaisesRegex(ValueError, "generator identity"):
            _load_mutation(identity)
        retry = deepcopy(payload)
        retry["generation"]["maximum_attempts_per_candidate"] = 4
        with self.assertRaisesRegex(ValueError, "retry policy"):
            _load_mutation(retry)

    def test_existing_configs_remain_byte_identical(self):
        expected = {
            "config/small_validation_config.json": "48d6657593c25227655f1a42d4871dea98a5002eef8ec01f094a8ae050279908",
            "config/v2_preflight_post_action_fix_20260831.json": "0e6966d0e56ee6551347f3f15cc15014cf7b6c78240e9cefbdf4749eb9985fbb",
        }
        actual = {
            name: hashlib.sha256((V2 / name).read_bytes()).hexdigest()
            for name in expected
        }
        self.assertEqual(actual, expected)

    def test_orchestrator_has_no_scoring_or_human_review_dependency(self):
        path = V2 / "generation_stability.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        forbidden = {"action", "flow", "structure", "runner", "human_review"}
        self.assertTrue(forbidden.isdisjoint({name.rsplit(".", 1)[-1] for name in imports}))


class GenerationStabilityDriverTests(unittest.TestCase):
    def test_47x1_artifacts_manifest_and_terminal_resume(self):
        config = load_config(CONFIG, SOURCE, SNAPSHOT)
        fake = FakeGenerator([_response() for _ in range(47)])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "cohort"
            state = generate(
                config=config,
                config_path=CONFIG,
                source_cases=_source_cases(),
                output_root=output,
                generator=fake,
            )
            self.assertEqual(len(fake.calls), 47)
            self.assertEqual(set(state["cases"]), set(config["case_ids"]))
            self.assertTrue(all(case["generation_status"] == "success" for case in state["cases"].values()))
            self.assertTrue(all(case["candidate_id"] == CANDIDATE_ID for case in state["cases"].values()))
            first = output / "cases" / config["case_ids"][0] / CANDIDATE_ID
            for name in (
                "process_text.txt", "raw_generation_response.json", "activity_graph.json",
                "topology_artifact.json", "semantic_sketch_plan.json", "ai4mde_export.json",
                "technical_status.json",
            ):
                self.assertTrue((first / name).is_file(), name)
            manifest = build_manifest(config, state)
            self.assertTrue(manifest["generation_only"])
            self.assertEqual(manifest["scoring_status"], "not_run_by_design")
            self.assertEqual(manifest["human_review_status"], "not_run_by_design")
            self.assertEqual(sum(len(case["candidates"]) for case in manifest["cases"]), 47)

            hashes_before = {
                path.relative_to(output): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in output.rglob("*") if path.is_file()
            }
            resumed = FakeGenerator([])
            resumed_state = generate(
                config=config,
                config_path=CONFIG,
                source_cases=_source_cases(),
                output_root=output,
                generator=resumed,
            )
            hashes_after = {
                path.relative_to(output): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in output.rglob("*") if path.is_file()
            }
            self.assertEqual(resumed.calls, [])
            self.assertEqual(resumed_state, state)
            self.assertEqual(hashes_after, hashes_before)

    def test_candidate_failure_is_terminal_and_next_cases_continue(self):
        config = load_config(CONFIG, SOURCE, SNAPSHOT)
        failures = [GenerationInvocationError("technical failure", stage="compiler") for _ in range(3)]
        fake = FakeGenerator([*failures, *[_response() for _ in range(46)]])
        with tempfile.TemporaryDirectory() as directory:
            state = generate(
                config=config,
                config_path=CONFIG,
                source_cases=_source_cases(),
                output_root=Path(directory) / "cohort",
                generator=fake,
            )
            first = state["cases"][config["case_ids"][0]]
            self.assertEqual(first["generation_status"], "failed")
            self.assertEqual(first["attempt_count"], 3)
            self.assertTrue(Path(first["process_text_path"]).is_file())
            self.assertEqual(len(first["process_text_sha256"]), 64)
        self.assertEqual(len(fake.calls), 49)
        self.assertTrue(all(
            state["cases"][case_id]["generation_status"] == "success"
            for case_id in config["case_ids"][1:]
        ))

    def test_import_failure_is_technical_and_infrastructure_failure_stops(self):
        config = load_config(CONFIG, SOURCE, SNAPSHOT)
        invalid_import = _response()
        invalid_import["systems"][0]["import_error"] = "invalid reference"
        fake = FakeGenerator([invalid_import, _response(), *[_response() for _ in range(46)]])
        with tempfile.TemporaryDirectory() as directory:
            state = generate(
                config=config,
                config_path=CONFIG,
                source_cases=_source_cases(),
                output_root=Path(directory) / "cohort",
                generator=fake,
            )
            first = state["cases"][config["case_ids"][0]]
            self.assertEqual([attempt["attempt_status"] for attempt in first["attempts"]], ["failed", "success"])
            self.assertEqual(first["import_status"], "passed")
            self.assertTrue(Path(first["attempts"][0]["evidence"]["raw_response_path"]).is_file())

        infrastructure = FakeGenerator([CohortInfrastructureError("configuration mismatch")])
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(CohortInfrastructureError, "configuration mismatch"):
                generate(
                    config=config,
                    config_path=CONFIG,
                    source_cases=_source_cases(),
                    output_root=Path(directory) / "cohort",
                    generator=infrastructure,
                )
            checkpoint = json.loads(
                (Path(directory) / "cohort" / "generation_state.json").read_text(encoding="utf-8")
            )
            self.assertEqual(checkpoint["cases"][config["case_ids"][0]]["generation_status"], "pending")


if __name__ == "__main__":
    unittest.main()
