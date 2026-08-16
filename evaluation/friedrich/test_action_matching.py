from __future__ import annotations

import unittest
import csv
from pathlib import Path

from .action_matching import (
    apply_one_to_one_matching,
    operation_compatibility,
    prediction_metrics,
)
from .calibrate_action_similarity import load_calibration_rows


class OperationCompatibilityTests(unittest.TestCase):
    def assert_compatible(self, reference: str, generated: str) -> None:
        self.assertTrue(operation_compatibility(reference, generated).compatible)

    def assert_incompatible(self, reference: str, generated: str) -> None:
        self.assertFalse(operation_compatibility(reference, generated).compatible)

    def test_rejects_high_confidence_operation_conflicts(self) -> None:
        self.assert_incompatible("send invoice", "receive invoice")
        self.assert_incompatible("approve vacation request", "reject request")
        self.assert_incompatible("create order", "send order to supplier")
        self.assert_incompatible("check recommendation", "revise recommendation")

    def test_preserves_reviewed_paraphrase_patterns(self) -> None:
        self.assert_compatible("update electrical design", "revise electrical design")
        self.assert_compatible("review quality", "recheck order quality")
        self.assert_compatible("register vacation request", "submit vacation request")
        self.assert_compatible("transfer data to pps", "enter data into pps")


class OneToOneMatchingTests(unittest.TestCase):
    def test_global_assignment_beats_greedy_first_match(self) -> None:
        rows = [
            self._row("P1", "r1", "g1", 0.90),
            self._row("P2", "r1", "g2", 0.80),
            self._row("P3", "r2", "g1", 0.85),
            self._row("P4", "r2", "g2", 0.45),
        ]
        evaluated = apply_one_to_one_matching(rows)
        selected = {row["pair_id"] for row in evaluated if row["final_prediction"]}
        self.assertEqual(selected, {"P2", "P3"})

    def test_each_node_is_selected_at_most_once(self) -> None:
        rows = [
            self._row("P1", "r1", "g1", 0.90),
            self._row("P2", "r1", "g2", 0.80),
            self._row("P3", "r2", "g1", 0.70),
        ]
        selected = [
            row for row in apply_one_to_one_matching(rows) if row["final_prediction"]
        ]
        self.assertEqual(len({row["reference_id"] for row in selected}), len(selected))
        self.assertEqual(len({row["generated_id"] for row in selected}), len(selected))

    def test_frozen_pilot_changes_only_the_two_known_operation_conflicts(self) -> None:
        base = Path(__file__).resolve().parent
        rows = load_calibration_rows(base / "action_matching_pilot_pairs.csv")
        with (base / "calibration" / "action_similarity_results.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            scores = {
                row["pair_id"]: float(row["cosine_similarity"])
                for row in csv.DictReader(handle)
            }
        evaluated = apply_one_to_one_matching(
            [{**row, "cosine_similarity": scores[row["pair_id"]]} for row in rows]
        )

        changed = {
            row["pair_id"]: row["decision_change_source"]
            for row in evaluated
            if row["threshold_prediction"] != row["final_prediction"]
        }
        self.assertEqual(
            changed,
            {
                "P018": "operation_compatibility",
                "P025": "operation_compatibility",
            },
        )
        self.assertEqual(
            prediction_metrics(evaluated, "final_prediction"),
            {
                "tp": 19,
                "fp": 0,
                "fn": 0,
                "tn": 10,
                "precision": 1.0,
                "recall": 1.0,
                "f1": 1.0,
                "accuracy": 1.0,
            },
        )

    @staticmethod
    def _row(pair_id: str, reference_id: str, generated_id: str, score: float):
        return {
            "pair_id": pair_id,
            "case_id": "case",
            "reference_id": reference_id,
            "generated_id": generated_id,
            "reference_normalized": "process request",
            "generated_normalized": "process request",
            "annotation_category": "equivalent",
            "cosine_similarity": score,
        }


if __name__ == "__main__":
    unittest.main()
