from __future__ import annotations

import unittest
from pathlib import Path

from .calibrate_action_similarity import (
    classification_metrics,
    load_calibration_rows,
    threshold_plateaus,
)


class ActionSimilarityCalibrationTests(unittest.TestCase):
    def test_frozen_pilot_has_expected_text_only_subset(self) -> None:
        pilot = Path(__file__).resolve().parent / "action_matching_pilot_pairs.csv"
        rows = load_calibration_rows(pilot)

        self.assertEqual(len(rows), 29)
        self.assertEqual(
            sum(row["annotation_category"] == "equivalent" for row in rows), 19
        )
        self.assertEqual(
            sum(row["annotation_category"] == "different" for row in rows), 10
        )
        self.assertTrue(all(row["used_topology"] == "no" for row in rows))

    def test_classification_metrics_use_inclusive_threshold(self) -> None:
        rows = [
            {"annotation_category": "equivalent", "cosine_similarity": 0.8},
            {"annotation_category": "equivalent", "cosine_similarity": 0.6},
            {"annotation_category": "different", "cosine_similarity": 0.7},
            {"annotation_category": "different", "cosine_similarity": 0.2},
        ]
        metrics = classification_metrics(rows, 0.7)
        self.assertEqual(
            {key: metrics[key] for key in ("tp", "fp", "fn", "tn")},
            {"tp": 1, "fp": 1, "fn": 1, "tn": 1},
        )

    def test_threshold_plateaus_cover_every_distinct_prediction(self) -> None:
        rows = [
            {"annotation_category": "different", "cosine_similarity": 0.2},
            {"annotation_category": "equivalent", "cosine_similarity": 0.8},
        ]
        plateaus = threshold_plateaus(rows)
        self.assertEqual(len(plateaus), 3)
        self.assertEqual([row["tp"] + row["fp"] for row in plateaus], [2, 1, 0])


if __name__ == "__main__":
    unittest.main()
