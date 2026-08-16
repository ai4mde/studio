from __future__ import annotations

from collections import Counter
import csv
import json
from pathlib import Path
import unittest


class FinalUntouchedValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = Path(__file__).resolve().parent / "final_untouched_validation"
        cls.raw = json.loads(
            (cls.base / "untouched_raw_results.json").read_text(encoding="utf-8")
        )
        with (cls.base / "final_manual_review.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            cls.review = list(csv.DictReader(handle))

    def test_sample_is_untouched(self) -> None:
        self.assertEqual(self.raw["scope"]["overlap"], [])
        self.assertEqual(
            self.raw["scope"]["selected_cases"],
            ["9-3", "6-1", "2-1", "9-4", "5-3"],
        )

    def test_review_counts(self) -> None:
        self.assertEqual(len(self.review), 59)
        self.assertEqual(
            Counter(row["manual_classification"] for row in self.review),
            {
                "correct_match": 33,
                "false_match": 14,
                "missed_true_match": 9,
                "granularity_mismatch": 2,
                "unresolved_ambiguous": 1,
            },
        )
        self.assertEqual(
            sum(row["matcher_selected"] == "yes" for row in self.review), 48
        )

    def test_every_selected_match_was_reviewed_once(self) -> None:
        raw_selected = {
            (case["case_id"], row["reference_id"], row["generated_id"])
            for case in self.raw["cases"]
            for row in case["selected_matches"]
        }
        reviewed = {
            (row["case_id"], row["reference_id"], row["generated_id"])
            for row in self.review
            if row["matcher_selected"] == "yes"
        }
        self.assertEqual(raw_selected, reviewed)

    def test_every_topology_decision_has_real_ambiguity(self) -> None:
        decisions = self.raw["topology_decisions"]
        self.assertEqual(len(decisions), 5)
        for decision in decisions:
            self.assertTrue(decision["ambiguity_sides"])
            self.assertTrue(
                decision["reference_candidate_count"] > 1
                or decision["generated_competitor_count"] > 1
            )
            self.assertGreaterEqual(decision["semantic_similarity"], 0.44)

    def test_one_to_one_output(self) -> None:
        for case in self.raw["cases"]:
            references = [row["reference_id"] for row in case["selected_matches"]]
            generated = [row["generated_id"] for row in case["selected_matches"]]
            self.assertEqual(len(references), len(set(references)))
            self.assertEqual(len(generated), len(set(generated)))


if __name__ == "__main__":
    unittest.main()
