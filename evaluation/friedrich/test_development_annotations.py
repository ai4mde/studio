from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import unittest

from .adapters import activity_graph_to_eval_graph, friedrich_reference_to_eval_graph
from .eval_graph import normalize_label
from .prototype import _extract_activity_graph
from .validate_action_matching_heldout import HELD_OUT_CASES, PILOT_CASES


DEVELOPMENT_CASES = frozenset({"3-2", "3-6", "5-4", "10-6", "10-8"})
DEVELOPMENT_SHA256 = "4e5ea31e8d18690edb9891a35d1ecb4d4de748460e0d5128d23b245e1d989c6e"


class DevelopmentAnnotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = Path(__file__).resolve().parent
        cls.path = cls.base / "development" / "action_matching_development_pairs.csv"
        with cls.path.open(encoding="utf-8", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))

    def test_frozen_checksum_and_composition(self) -> None:
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), DEVELOPMENT_SHA256)
        self.assertEqual(len(self.rows), 39)
        self.assertEqual(len({row["pair_id"] for row in self.rows}), 39)
        self.assertEqual({row["case_id"] for row in self.rows}, DEVELOPMENT_CASES)
        self.assertFalse(DEVELOPMENT_CASES & PILOT_CASES)
        self.assertFalse(DEVELOPMENT_CASES & set(HELD_OUT_CASES))
        self.assertEqual(
            Counter(row["annotation_category"] for row in self.rows),
            {
                "equivalent": 15,
                "different": 17,
                "granularity_mismatch": 2,
                "structurally_resolvable": 3,
                "unresolved_ambiguous": 2,
            },
        )

    def test_derived_fields_follow_annotation_policy(self) -> None:
        expected_binary = {
            "equivalent": "yes",
            "different": "no",
            "granularity_mismatch": "no",
            "structurally_resolvable": "yes",
            "unresolved_ambiguous": "excluded",
        }
        for row in self.rows:
            category = row["annotation_category"]
            self.assertEqual(row["binary_match"], expected_binary[category])
            self.assertEqual(
                row["operation_calibration_eligible"],
                "yes"
                if category in {"equivalent", "different"}
                and row["used_topology"] == "no"
                else "no",
            )
            self.assertEqual(
                bool(row["granularity_type"]), category == "granularity_mismatch"
            )
            if row["used_topology"] == "yes":
                self.assertTrue(row["topology_basis"])
            else:
                self.assertFalse(row["topology_basis"])

    def test_labels_and_ids_match_source_artifacts(self) -> None:
        catalog_path = Path(
            "/Users/queenie/Desktop/evaluation-data/friedrich_47_case_catalog.csv"
        )
        with catalog_path.open(encoding="utf-8", newline="") as handle:
            catalog = {row["case_id"]: row for row in csv.DictReader(handle)}

        actions: dict[str, tuple[dict[str, str | None], dict[str, str | None]]] = {}
        for case_id in DEVELOPMENT_CASES:
            item = catalog[case_id]
            reference = friedrich_reference_to_eval_graph(item["reference_model_path"])
            generated_path = Path(item["generated_artifact_output_path"]) / "run_1.json"
            artifact = json.loads(generated_path.read_text(encoding="utf-8"))
            generated = activity_graph_to_eval_graph(_extract_activity_graph(artifact))
            actions[case_id] = (
                {node.id: node.label for node in reference.nodes if node.type == "action"},
                {node.id: node.label for node in generated.nodes if node.type == "action"},
            )

        for row in self.rows:
            reference, generated = actions[row["case_id"]]
            self.assertEqual(reference[row["reference_id"]], row["reference_normalized"])
            self.assertEqual(generated[row["generated_id"]], row["generated_normalized"])
            self.assertEqual(normalize_label(row["reference_label"]), row["reference_normalized"])
            self.assertEqual(normalize_label(row["generated_label"]), row["generated_normalized"])


if __name__ == "__main__":
    unittest.main()
