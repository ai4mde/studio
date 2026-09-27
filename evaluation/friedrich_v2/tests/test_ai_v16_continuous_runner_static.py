"""Synthetic/static tests for the v1.6 runner; never call a candidate API."""

from __future__ import annotations

import inspect
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from copy import deepcopy
from decimal import Decimal, localcontext
from pathlib import Path
from unittest.mock import patch

from evaluation.friedrich_v2 import ai_v16_continuous_contract_draft as contract
from evaluation.friedrich_v2 import analyze_ai_v16_continuous as analysis
from evaluation.friedrich_v2 import run_ai_v2_calibration as legacy
from evaluation.friedrich_v2 import run_ai_v2_calibration_v16_continuous as runner


class ContinuousContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = contract.load_schema_wrapper()["schema"]
        source = contract.SCHEMA_PATH.read_text(encoding="utf-8")
        cls.example = json.loads(legacy.extract_fenced_block(source, "Canonical result example", "json"))

    def sample(self, value: object) -> dict:
        result = deepcopy(self.example)
        result["overall_score"] = value
        if value == 1.0 and type(value) in (int, float):
            result.update(severity="none", main_error_type="none")
        return result

    def test_nonquarter_and_endpoints_are_valid(self) -> None:
        field = self.schema["properties"]["overall_score"]
        self.assertEqual((field["minimum"], field["maximum"]), (0.0, 1.0))
        self.assertNotIn("enum", field)
        for score in (0.83, 0.61, 0.37, 0.0, 1.0):
            with self.subTest(score=score):
                contract.validate_result(self.sample(score), "example-1", "candidate_1", self.schema)

    def test_invalid_values_are_rejected(self) -> None:
        for score in (-0.01, 1.01, True, False, float("nan"), float("inf"), float("-inf"), "0.83"):
            with self.subTest(score=score), self.assertRaises(ValueError):
                contract.validate_result(self.sample(score), "example-1", "candidate_1", self.schema)

    def test_no_fixed_severity_lookup(self) -> None:
        for score in (0.83, 0.61, 0.37, 0.75, 0.5, 0.25):
            contract.validate_result(self.sample(score), "example-1", "candidate_1", self.schema)
        with self.assertRaises(ValueError):
            candidate = self.sample(0.83)
            candidate["severity"] = "none"
            contract.validate_result(candidate, "example-1", "candidate_1", self.schema)


class RosterAndBoundaryTests(unittest.TestCase):
    def test_approved_drafts_and_exact_frozen_roster(self) -> None:
        runner.verify_approved_draft_hashes()
        actual = runner.verified_artifacts()
        self.assertEqual(len(actual), 18)
        self.assertEqual(tuple((x["case_id"], x["candidate_id"]) for x in actual), runner.EXPECTED_PAIRS)
        changed = deepcopy(actual)
        changed[0]["activity_graph_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            runner.assert_same_roster(changed, actual)
        changed = deepcopy(actual)
        changed[0]["case_id"] = "substituted"
        with self.assertRaises(ValueError):
            runner.assert_same_roster(changed, actual)

    def test_request_has_only_approved_candidate_inputs(self) -> None:
        developer, template = runner.load_prompt()
        old = runner.ROOT.joinpath("ai_evaluator_v2_prompt_revision_5_draft.md").read_text(encoding="utf-8")
        self.assertEqual(template, legacy.extract_fenced_block(old, "Exact candidate-level user prompt template", "text"))
        process, graph, rendering = "Synthetic process", '{"nodes":[],"edges":[]}', "Synthetic rendering"
        user = legacy.instantiate_user_prompt(template, "synthetic-case", "candidate_1", process, graph, rendering)
        with patch.object(legacy, "post_response", side_effect=AssertionError("API must not be called")):
            payload = runner.build_payload(developer, user, contract.load_schema_wrapper())
            record = runner.input_record("synthetic-case", "candidate_1", process, graph, rendering, user, developer)
        self.assertEqual(record["input_components"], runner.INPUT_COMPONENTS)
        self.assertEqual(payload["model"], runner.MODEL)
        self.assertEqual(payload["reasoning"], {"effort": "medium"})
        self.assertIs(payload["store"], False)
        self.assertEqual([item["role"] for item in payload["input"]], ["developer", "user"])
        self.assertEqual(payload["input"][1]["content"][0]["text"], user)
        self.assertEqual(user.count("Synthetic process"), 1)
        self.assertNotIn("human_label", user)
        self.assertNotIn("Code V3.1 results", user)
        self.assertNotIn("previous AI scores", user)

    def test_label_loader_is_outside_execution_path(self) -> None:
        run_source = inspect.getsource(runner.cmd_run)
        compare_source = inspect.getsource(runner.cmd_compare)
        self.assertNotIn("HUMAN_LABELS_PATH", run_source)
        self.assertNotIn("load_human_labels", run_source)
        self.assertLess(compare_source.index("validate_exact_result"), compare_source.index("analysis.load_human_labels"))
        self.assertLess(compare_source.index("technical_status"), compare_source.index("analysis.load_human_labels"))

    def test_exact_decimal_score_survives_jsonl_serialization(self) -> None:
        score = Decimal("0.371234567890123456789")
        source = '{"case_id":"synthetic","candidate_id":"candidate_1","overall_score":0.371234567890123456789}'
        self.assertEqual(runner.parse_score_decimal(source), score)
        encoded = runner.serialize_result(json.loads(source), score)
        self.assertEqual(runner.parse_score_decimal(encoded), score)
        for source in ('{"overall_score":true}', '{"overall_score":"0.83"}', '{"overall_score":1.01}'):
            with self.assertRaises(ValueError):
                runner.parse_score_decimal(source)

    def test_exact_endpoint_check_avoids_float_rounding(self) -> None:
        schema = contract.load_schema_wrapper()["schema"]
        source = contract.SCHEMA_PATH.read_text(encoding="utf-8")
        result = json.loads(legacy.extract_fenced_block(source, "Canonical result example", "json"))
        result["overall_score"] = 1.0  # Python float rounding of a JSON value below 1.
        exact = Decimal("0.99999999999999999999999999999999999999999")
        runner.validate_exact_result(result, exact, "example-1", "candidate_1", schema)
        with self.assertRaises(ValueError):
            runner.validate_exact_result(result, Decimal("1"), "example-1", "candidate_1", schema)


class ContinuousAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pairs = (("s-1", "candidate_1"), ("s-1", "candidate_2"), ("s-2", "candidate_1"))
        self.ai = dict(zip(self.pairs, map(Decimal, ("0.68", "0.37", "0.83"))))
        self.human = dict(zip(self.pairs, map(Decimal, ("0.75", "0.50", "1.00"))))

    def test_error_formulas_and_order(self) -> None:
        rows, metrics = analysis.calculate(self.pairs, self.ai, self.human)
        self.assertEqual([row["signed_difference"] for row in rows], list(map(Decimal, ("-0.07", "-0.13", "-0.17"))))
        self.assertEqual([row["absolute_error"] for row in rows], list(map(Decimal, ("0.07", "0.13", "0.17"))))
        with localcontext() as context:
            context.prec = 50
            self.assertEqual(metrics["mean_absolute_error"], Decimal("0.37") / 3)
        self.assertEqual(metrics["median_absolute_error"], Decimal("0.13"))
        self.assertEqual(metrics["maximum_absolute_error"], Decimal("0.17"))
        self.assertEqual(metrics["maximum_error_candidates"], [{"case_id": "s-2", "candidate_id": "candidate_1"}])
        self.assertEqual(analysis.review_order(rows)[0]["candidate_id"], "candidate_1")
        self.assertEqual(analysis.review_order(rows)[0]["case_id"], "s-2")
        self.assertIsNone(metrics["acceptance_threshold"])

    def test_long_decimal_difference_is_not_truncated(self) -> None:
        pair = (("synthetic", "candidate_1"),)
        score = Decimal("0.37123456789012345678901234567890123456789")
        rows, metrics = analysis.calculate(pair, {pair[0]: score}, {pair[0]: Decimal("0.50")})
        self.assertEqual(rows[0]["signed_difference"], Decimal("-0.12876543210987654321098765432109876543211"))
        self.assertEqual(metrics["mean_absolute_error"], rows[0]["signed_difference"].copy_abs())

    def test_tie_aware_spearman(self) -> None:
        human = list(map(Decimal, ("1", "1", "2", "3")))
        ai = list(map(Decimal, ("1", "2", "2", "3")))
        self.assertEqual(analysis.average_ranks(human), list(map(Decimal, ("1.5", "1.5", "3", "4"))))
        self.assertAlmostEqual(float(analysis.spearman_tie_aware(human, ai)), 5 / 6)
        self.assertEqual(analysis.spearman_tie_aware(list(map(Decimal, ("1", "2", "3"))), list(map(Decimal, ("3", "2", "1")))), Decimal("-1"))
        self.assertIsNone(analysis.spearman_tie_aware([Decimal("1")] * 3, list(map(Decimal, ("1", "2", "3")))))

    def test_synthetic_scatter_has_one_point_per_candidate(self) -> None:
        rows, _ = analysis.calculate(self.pairs, self.ai, self.human)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "synthetic.svg"
            analysis.write_scatter_svg(target, rows)
            image = ET.parse(target).getroot()
            circles = image.findall("{http://www.w3.org/2000/svg}circle")
            self.assertEqual(len(circles), 3)


if __name__ == "__main__":
    unittest.main()
