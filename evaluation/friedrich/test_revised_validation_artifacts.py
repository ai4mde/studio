from __future__ import annotations

import json
from pathlib import Path
import unittest


class RevisedValidationArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = (
            Path(__file__).resolve().parent
            / "development"
            / "revised_validation"
            / "development_comparison.json"
        )
        cls.report = json.loads(path.read_text(encoding="utf-8"))

    def test_scope_excludes_protected_held_out_cases(self) -> None:
        self.assertEqual(
            self.report["scope"]["development_cases"],
            ["3-2", "3-6", "5-4", "10-6", "10-8"],
        )
        self.assertEqual(self.report["scope"]["protected_held_out_cases_used"], [])

    def test_frozen_method_and_expected_results(self) -> None:
        self.assertEqual(self.report["method"]["semantic_threshold"], 0.44)
        self.assertIsNone(self.report["method"]["operation_threshold"])
        self.assertEqual(self.report["previous"]["correct_matches"], 14)
        self.assertEqual(self.report["revised"]["correct_matches"], 17)
        self.assertEqual(self.report["revised"]["false_matches"], 6)
        self.assertEqual(self.report["revised"]["missed_matches"], 1)

    def test_selected_pairs_are_one_to_one(self) -> None:
        selected = self.report["selected_matches"]
        references = [(row["case_id"], row["reference_id"]) for row in selected]
        generated = [(row["case_id"], row["generated_id"]) for row in selected]
        self.assertEqual(len(references), len(set(references)))
        self.assertEqual(len(generated), len(set(generated)))

    def test_topology_decisions_have_inspectable_evidence(self) -> None:
        for decision in self.report["topology_decisions"]:
            self.assertTrue(decision["candidate_nodes"])
            self.assertTrue(decision["anchor_evidence"])
            self.assertGreaterEqual(decision["semantic_similarity"], 0.44)
            self.assertIn(decision["selected_candidate"], decision["candidate_nodes"])
            for evidence in decision["anchor_evidence"]:
                self.assertGreater(evidence["reference_distance"], 0)
                self.assertGreater(evidence["generated_distance"], 0)


if __name__ == "__main__":
    unittest.main()
