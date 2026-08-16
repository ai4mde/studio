from __future__ import annotations

from collections import Counter
import csv
import json
from pathlib import Path
import unittest


class UntouchedValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = Path(__file__).resolve().parent / "untouched_validation"
        cls.raw = json.loads(
            (cls.base / "untouched_raw_results.json").read_text(encoding="utf-8")
        )
        with (cls.base / "untouched_manual_review.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            cls.review = list(csv.DictReader(handle))

    def test_selection_is_untouched(self) -> None:
        scope = self.raw["scope"]
        self.assertEqual(scope["overlap"], [])
        self.assertEqual(
            scope["selected_cases"], ["8-1", "1-1", "2-2", "3-8", "10-9"]
        )

    def test_matcher_configuration_is_frozen(self) -> None:
        matcher = self.raw["frozen_matcher"]
        self.assertEqual(matcher["semantic_threshold"], 0.44)
        self.assertIsNone(matcher["operation_threshold"])

    def test_manual_review_counts(self) -> None:
        self.assertEqual(len(self.review), 35)
        self.assertEqual(
            Counter(row["manual_classification"] for row in self.review),
            {
                "correct_match": 25,
                "false_match": 5,
                "granularity_mismatch": 3,
                "missed_true_match": 2,
            },
        )
        self.assertEqual(
            sum(row["matcher_selected"] == "yes" for row in self.review), 33
        )

    def test_every_raw_selected_match_was_reviewed(self) -> None:
        raw_selected = {
            (case["case_id"], row["reference_id"], row["generated_id"])
            for case in self.raw["cases"]
            for row in case["selected_matches"]
        }
        reviewed_selected = {
            (row["case_id"], row["reference_id"], row["generated_id"])
            for row in self.review
            if row["matcher_selected"] == "yes"
        }
        self.assertEqual(raw_selected, reviewed_selected)

    def test_topology_audit_finding(self) -> None:
        decisions = self.raw["topology_decisions"]
        self.assertEqual(len(decisions), 9)
        self.assertEqual(
            sum(len(decision["candidate_nodes"]) == 1 for decision in decisions), 6
        )
        self.assertEqual(
            sum(len(decision["candidate_nodes"]) > 1 for decision in decisions), 3
        )


if __name__ == "__main__":
    unittest.main()
