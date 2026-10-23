"""Offline regression checks for evidence isolation and real-mode prerequisites."""
import importlib.util
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "runner", Path(__file__).with_name("run_business_logic_gates.py"))
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class EvidenceRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.metadata = self.root / "metadata.json"
        self.fixture = self.root / "fixture.json"
        self.metadata.write_text("{}")
        self.fixture.write_text("{}")

    def run_until_dependencies(self, mode):
        args = ["runner", "--metadata", str(self.metadata), "--case-data", str(self.fixture),
                "--mode", mode, "--output", str(self.root / mode)]
        # Stop before Docker/npm: this deliberately failed run must still be isolated.
        with patch.object(runner.sys, "argv", args), \
                patch.object(runner, "source_hashes", return_value={"runner": "current"}), \
                patch.object(runner.subprocess, "run", side_effect=RuntimeError("dependency probe")) as process, \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(), 1)
        return process

    def test_first_and_repeated_failures_do_not_overwrite_evidence(self):
        self.run_until_dependencies("fake")
        first, = (self.root / "fake").glob("run_*/manifest.json")
        original = first.read_bytes()
        self.run_until_dependencies("fake")
        self.assertEqual(first.read_bytes(), original)
        self.assertEqual(len(list((self.root / "fake").glob("run_*/manifest.json"))), 2)
        self.assertTrue(all(p.is_dir() and p.name.startswith("run_") for p in (self.root / "fake").iterdir()))
        self.assertEqual(json.loads(original)["status"], "fail")

    def write_prerequisite(self, location, source="current"):
        path = self.root / "fake" / location / "manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"status": "pass", "fingerprint": {
            "source": {"runner": source}, "metadata": runner.sha(self.metadata),
            "case_data": runner.sha(self.fixture), "compose": runner.sha(runner.COMPOSE_FILE),
            "validation_scope": "full"}}))
        return path

    def test_real_accepts_matching_nested_and_legacy_root_manifests(self):
        for location in ("run_prior", ""):
            with self.subTest(location=location):
                prior = self.write_prerequisite(location)
                process = self.run_until_dependencies("real")
                process.assert_called_once()
                prior.unlink()

    def test_real_rejects_evidence_from_an_older_runner_before_any_command(self):
        self.write_prerequisite("run_prior", source="old")
        process = self.run_until_dependencies("real")
        process.assert_not_called()
        manifest, = (self.root / "real").glob("run_*/manifest.json")
        self.assertIn("exactly these sources and inputs", json.loads(manifest.read_text())["error"])


if __name__ == "__main__":
    unittest.main()
