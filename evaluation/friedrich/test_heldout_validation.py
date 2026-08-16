from __future__ import annotations

from collections import Counter, defaultdict
import csv
from pathlib import Path
import unittest

from .action_matching import PROVISIONAL_THRESHOLD
from .validate_action_matching_heldout import HELD_OUT_CASES, PILOT_CASES


class HeldOutValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = Path(__file__).resolve().parent / "heldout_validation"
        cls.candidates = cls._read("heldout_candidate_matrix.csv")
        cls.reviewed = cls._read("heldout_reviewed_matches.csv")
        cls.missed = cls._read("heldout_missed_matches.csv")

    @classmethod
    def _read(cls, filename: str) -> list[dict[str, str]]:
        with (cls.base / filename).open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_held_out_cases_do_not_overlap_pilot(self) -> None:
        self.assertEqual(len(HELD_OUT_CASES), 5)
        self.assertFalse(set(HELD_OUT_CASES) & PILOT_CASES)

    def test_complete_candidate_matrices_have_expected_size(self) -> None:
        counts = Counter(row["case_id"] for row in self.candidates)
        self.assertEqual(
            counts,
            {"3-1": 42, "3-4": 4, "8-2": 25, "10-7": 64, "1-2": 48},
        )

    def test_reviewed_matches_are_one_to_one_and_traceable(self) -> None:
        candidates = {
            (row["case_id"], row["reference_id"], row["generated_id"]): row
            for row in self.candidates
        }
        reference_ids: dict[str, set[str]] = defaultdict(set)
        generated_ids: dict[str, set[str]] = defaultdict(set)
        allowed_topology = {
            "nearest_matched_predecessor",
            "nearest_matched_successor",
        }
        for row in self.reviewed:
            key = (row["case_id"], row["reference_id"], row["generated_id"])
            self.assertIn(key, candidates)
            self.assertEqual(
                float(row["cosine_similarity"]),
                float(candidates[key]["cosine_similarity"]),
            )
            self.assertGreaterEqual(float(row["cosine_similarity"]), PROVISIONAL_THRESHOLD)
            self.assertNotIn(row["reference_id"], reference_ids[row["case_id"]])
            self.assertNotIn(row["generated_id"], generated_ids[row["case_id"]])
            reference_ids[row["case_id"]].add(row["reference_id"])
            generated_ids[row["case_id"]].add(row["generated_id"])
            if row["topology_used"] == "yes":
                self.assertTrue(set(row["topology_basis"].split("|")) <= allowed_topology)
            else:
                self.assertEqual(row["topology_basis"], "")

    def test_manual_assessment_counts_are_fixed(self) -> None:
        self.assertEqual(
            Counter(row["human_assessment"] for row in self.reviewed),
            {"correct_match": 15, "false_match": 4, "granularity_mismatch": 1},
        )
        self.assertEqual(len(self.missed), 4)
        self.assertTrue(
            all(float(row["cosine_similarity"]) < PROVISIONAL_THRESHOLD for row in self.missed)
        )

    def test_no_operation_candidate_was_rejected_above_threshold(self) -> None:
        rejected = [
            row
            for row in self.candidates
            if row["threshold_prediction"] == "True"
            and row["operation_compatible"] == "False"
        ]
        self.assertEqual(rejected, [])


if __name__ == "__main__":
    unittest.main()
