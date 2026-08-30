from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from evaluation.friedrich_v2.generation import load_run_config, load_small_validation_config
from evaluation.friedrich_v2.manifests import load_source_manifest


ROOT = Path(__file__).resolve().parents[3]
V2 = ROOT / "evaluation" / "friedrich_v2"


class FrozenConfigurationTests(unittest.TestCase):
    def test_snapshot_hashes_match_executable_files(self):
        snapshot = json.loads((V2 / "evaluator_snapshot.json").read_text(encoding="utf-8"))
        actual = {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in snapshot["files"]
        }
        self.assertEqual(actual, snapshot["files"])
        snapshot_id = hashlib.sha256(
            json.dumps(actual, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self.assertEqual(snapshot_id, snapshot["snapshot_id"])

    def test_config_snapshot_source_and_selected_cases_resolve(self):
        config_path = V2 / "config" / "small_validation_config.json"
        config = load_small_validation_config(config_path)
        self.assertEqual(
            config["evaluation"]["evaluator_snapshot_id"],
            "2d8600a0c88c4806e163e2bf8770efeaeea43dcfd3af070031834e243b589225",
        )
        source_path = ROOT / config["source"]["source_manifest_path"]
        source = load_source_manifest(source_path, verify_files=True)
        self.assertEqual(
            hashlib.sha256(source_path.read_bytes()).hexdigest(),
            config["source"]["source_manifest_sha256"],
        )
        source_ids = {case["case_id"] for case in source["cases"]}
        self.assertTrue(set(config["small_validation"]["case_ids"]) <= source_ids)

    def test_v2_run_configs_reference_current_snapshot(self):
        source_path = V2 / "manifests" / "source_manifest.json"
        snapshot = json.loads((V2 / "evaluator_snapshot.json").read_text(encoding="utf-8"))
        for name in ("v2_preflight_20260830.json", "v2_formal_47x3.template.json"):
            config = load_run_config(V2 / "config" / name, source_path)
            self.assertEqual(config["evaluator_snapshot_id"], snapshot["snapshot_id"])


if __name__ == "__main__":
    unittest.main()
