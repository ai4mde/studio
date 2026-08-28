from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from evaluation.friedrich_v2.adapters import friedrich_reference_to_eval_graph
from evaluation.friedrich_v2.core import AutomaticItem
from evaluation.friedrich_v2.human_review import REVIEW_FIELDS, build_review_rows, load_review_csv, write_review_csv
from evaluation.friedrich_v2.manifests import ManifestError, load_generated_manifest, load_source_manifest


class BoundaryTests(unittest.TestCase):
    def test_source_manifest_is_clean_and_complete(self):
        path = Path(__file__).parents[1] / "manifests" / "source_manifest.json"
        payload = load_source_manifest(path)
        self.assertEqual(len(payload["cases"]), 47)
        forbidden = {"run_status", "score", "checkpoint", "major_process_pattern"}
        self.assertFalse(forbidden & set().union(*(set(case) for case in payload["cases"])))

    def test_unresolved_generated_template_is_rejected(self):
        path = Path(__file__).parents[1] / "manifests" / "generated_manifest.template.json"
        with self.assertRaisesRegex(ManifestError, "unresolved"):
            load_generated_manifest(path, set(), verify_files=False)

    def test_process_editor_properties_and_unsupported_gateway(self):
        xml = """<model xmlns="http://frapu.net/xsd/ProcessEditor"><nodes>
          <node><property name="#id" value="a"/><property name="#type" value="x.Task"/><property name="text" value="Work"/></node>
          <node><property name="#id" value="g"/><property name="#type" value="x.InclusiveGateway"/></node>
          <node><property name="#id" value="b"/><property name="#type" value="x.Task"/><property name="text" value="Finish"/></node>
        </nodes><edges>
          <edge><property name="#sourceNode" value="a"/><property name="#targetNode" value="g"/></edge>
          <edge><property name="#sourceNode" value="g"/><property name="#targetNode" value="b"/></edge>
          <edge><property name="#sourceNode" value="g"/><property name="#targetNode" value="a"/></edge>
        </edges></model>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case.model"
            path.write_text(xml, encoding="utf-8")
            result = friedrich_reference_to_eval_graph(path)
        gateway = next(node for node in result.nodes if node.id == "g")
        self.assertEqual((gateway.type, gateway.semantic_type), ("unsupported_control", "InclusiveGateway"))
        self.assertEqual(next(node.label for node in result.nodes if node.id == "a"), "work")

    def test_review_queue_contains_errors_redundancy_and_seeded_tp(self):
        items = [
            AutomaticItem("1", "candidate_1", "Action", "1:candidate_1:fp", "FP", {}, {}, "error"),
            AutomaticItem("1", "candidate_1", "Redundant Control Nodes", "1:candidate_1:r", "CANDIDATE", {}, {}, "candidate"),
        ] + [AutomaticItem("1", "candidate_1", "Flow", f"1:candidate_1:tp-{i}", "TP", {}, {}, "ok") for i in range(10)]
        rows = build_review_rows(items, seed=7)
        triggers = [row["review_trigger"] for row in rows]
        self.assertIn("automatic_error", triggers)
        self.assertIn("redundancy_candidate", triggers)
        self.assertEqual(triggers.count("seeded_tp_audit"), 5)

    def test_review_schema_round_trip(self):
        row = {field: "" for field in REVIEW_FIELDS}
        row.update({"case_id": "1", "candidate_id": "candidate_1", "metric": "Action", "item_id": "x", "review_trigger": "automatic_error", "automatic_label": "FP"})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.csv"
            write_review_csv(path, [row])
            self.assertEqual(load_review_csv(path)[0]["item_id"], "x")


if __name__ == "__main__":
    unittest.main()
