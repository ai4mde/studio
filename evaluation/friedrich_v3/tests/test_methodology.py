from __future__ import annotations

import unittest
from pathlib import Path

from evaluation.friedrich_v3.action import (
    ACTION_SIMILARITY_THRESHOLD, ActionMatch, ActionResult,
    COMPATIBILITY_FILENAME, COMPATIBILITY_VERSION, compatibility_veto, evaluate_actions,
    REFERENCE_RELATIVE_DELTA,
)
from evaluation.friedrich_v3.core import Counts, EvalEdge, EvalGraph, EvalNode
from evaluation.friedrich_v3.flow import evaluate_flow
from evaluation.friedrich_v3.human_review import build_review_rows, build_sensitivity_results
from evaluation.friedrich_v3.runner import _optional_mean, _validate_run_shape
from evaluation.friedrich_v3.structure import evaluate_structure


class MatrixSimilarity:
    def __init__(self, values: list[list[float]]) -> None:
        self.values = values

    def matrix(self, reference, generated):
        return self.values


class ExactSimilarity:
    def matrix(self, reference, generated):
        return [[1.0 if left == right else 0.0 for right in generated] for left in reference]


def graph(nodes, edges):
    return EvalGraph(
        tuple(EvalNode(node_id, node_type, label) for node_id, node_type, label in nodes),
        tuple(EvalEdge(edge[0], edge[1], edge[2] if len(edge) > 2 else None)
              for edge in edges),
    )


def actions(reference, generated, similarity=None):
    return evaluate_actions(
        "case", "candidate_1", reference, generated,
        similarity or ExactSimilarity(), ACTION_SIMILARITY_THRESHOLD,
    )


def anchored_actions(reference, generated, pairs):
    matches = tuple(
        ActionMatch("case", "candidate_1", reference_id, generated_id, 1.0)
        for reference_id, generated_id in pairs
    )
    return ActionResult("case", "candidate_1", matches, Counts(), ())


class ActionMethodologyTests(unittest.TestCase):
    def test_compatibility_version_names_existing_taxonomy(self):
        self.assertEqual(COMPATIBILITY_VERSION, "action-compatibility-v3")
        self.assertEqual(REFERENCE_RELATIVE_DELTA, 0.10)
        self.assertTrue(Path("evaluation/friedrich_v3", COMPATIBILITY_FILENAME).is_file())

    def test_valid_paraphrase_remains_eligible(self):
        reference = graph([("r", "action", "inspect application")], [])
        generated = graph([("g", "action", "review application")], [])
        result = actions(reference, generated, MatrixSimilarity([[0.8]]))
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (1, 0, 0))

    def test_explicit_operation_and_object_conflicts_are_vetoed(self):
        for left, right, reason in (
            ("send application", "receive application", "incompatible_primary_operations"),
            ("approve request", "reject request", "incompatible_primary_operations"),
            ("review application", "review invoice", "explicit_concrete_object_conflict"),
            ("approve request", "not approve request", "explicit_polarity_conflict"),
            ("check recommendation", "repeat recommendation", "incompatible_primary_operations"),
            ("reject claim", "inform claimant of rejection", "incompatible_primary_operations"),
            ("determine nursing officer", "conduct full inquiry", "incompatible_primary_operations"),
            ("hand out cards", "produce registration cards", "incompatible_primary_operations"),
            ("record notice", "receive patient notice", "incompatible_primary_operations"),
            ("meeting with first intaker", "pass registration cards", "explicit_concrete_object_conflict"),
            ("reject claim", "send simple forms", "incompatible_primary_operations"),
            ("write recommendation", "repeat recommendation", "incompatible_primary_operations"),
            ("assign intakers", "pass cards", "incompatible_primary_operations"),
            ("assign intakers", "produce cards", "incompatible_primary_operations"),
            ("reject claim", "register claim", "incompatible_primary_operations"),
            ("register claim", "send forms", "incompatible_primary_operations"),
            ("plan meeting", "perform meeting", "incompatible_primary_operations"),
            ("write recommendation", "perform recommendation repetition", "incompatible_primary_operations"),
            ("determine nursing officer", "put connect doctor to nursing officer", "incompatible_primary_operations"),
            ("store assignment", "store inquiry information", "explicit_concrete_object_conflict"),
            ("record notice", "record information on registration form", "explicit_concrete_object_conflict"),
        ):
            with self.subTest(left=left, right=right):
                decision = compatibility_veto(left, right)
                self.assertFalse(decision.compatible)
                self.assertIn(reason, decision.reason)

    def test_same_operation_families_remain_compatible(self):
        for left, right in (
            ("reject claim", "reject claim"),
            ("send forms", "send simple forms"),
            ("write recommendation", "write settlement recommendation"),
            ("assign intakers", "assign patients to intakers"),
            ("register claim", "register claim in system"),
            ("determine treatment", "place patient on list for treatment formulation"),
        ):
            with self.subTest(left=left, right=right):
                self.assertTrue(compatibility_veto(left, right).compatible)

    def test_vetoed_high_similarity_pair_cannot_displace_valid_pairs(self):
        reference = graph(
            [("reject", "action", "reject claim"), ("send", "action", "send relevant forms")],
            [],
        )
        generated = graph(
            [("forms", "action", "send simple forms"), ("rejected", "action", "reject claim")],
            [],
        )
        result = actions(reference, generated, MatrixSimilarity([[0.99, 0.60], [0.80, 0.10]]))
        self.assertEqual(result.reference_to_generated, {"reject": "rejected", "send": "forms"})

    def test_reference_relative_filter_does_not_fill_a_weak_vacancy(self):
        reference = graph([
            ("strong", "action", "handle primary task"),
            ("weak", "action", "handle secondary task"),
        ], [])
        generated = graph([
            ("assigned", "action", "process primary task"),
            ("vacancy", "action", "process remaining task"),
        ], [])
        result = actions(reference, generated, MatrixSimilarity([
            [0.90, 0.50],
            [0.85, 0.60],
        ]))
        self.assertEqual(result.reference_to_generated, {"strong": "assigned"})

    def test_reference_relative_filter_preserves_assign_over_inform(self):
        reference = graph([("assign", "action", "assign intakers")], [])
        generated = graph([
            ("assigned", "action", "assign patients to intakers"),
            ("informed", "action", "inform second intaker"),
        ], [])
        result = actions(reference, generated, MatrixSimilarity([[0.7376, 0.6260]]))
        self.assertEqual(result.reference_to_generated, {"assign": "assigned"})
        self.assertNotIn("informed", result.generated_to_reference)

    def test_assignment_does_not_require_generated_side_mutual_best(self):
        reference = graph([
            ("r1", "action", "handle first case"),
            ("r2", "action", "handle second case"),
        ], [])
        generated = graph([
            ("g1", "action", "process first case"),
            ("g2", "action", "process second case"),
        ], [])
        result = actions(reference, generated, MatrixSimilarity([
            [0.90, 0.85],
            [0.95, 0.88],
        ]))
        self.assertEqual(result.reference_to_generated, {"r1": "g2", "r2": "g1"})

    def test_below_threshold_limitation_is_not_recorded_as_delta_rejection(self):
        reference = graph([("r", "action", "compose file")], [])
        generated = graph([("g", "action", "compile file with claim documentation")], [])
        result = actions(reference, generated, MatrixSimilarity([[0.43]]))
        missing = next(item for item in result.items if item.label == "FN")
        self.assertEqual(missing.evidence["matching_filter"]["stage"], "below_similarity_threshold")
        self.assertEqual(missing.evidence["matching_filter"]["delta_ref"], 0.10)

    def test_tuning_and_heldout_valid_paraphrases_remain_available(self):
        pairs = (
            ("store sct file", "store sct file awaiting report"),
            ("retrieve sct file", "retrieve sct file upon report"),
            ("initiate search", "initiate search for missing files"),
            ("update patient file", "add medical file"),
            ("assign intakers", "assign patients to intakers"),
            ("write recommendation", "write settlement recommendation"),
            ("send relevant forms", "send simple forms"),
            ("send relevant forms", "send complex forms"),
            ("collect mail", "collect mail daily"),
            ("register mail", "register mail in register"),
            ("check mail compliance", "quality check mail"),
            ("search report database", "search police report"),
            ("calculate claim estimate", "calculate initial estimate"),
            ("notify claimant", "inform claimant of outcome"),
        )
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                result = actions(
                    graph([("r", "action", left)], []),
                    graph([("g", "action", right)], []),
                    MatrixSimilarity([[0.80]]),
                )
                self.assertEqual(result.reference_to_generated, {"r": "g"})

    def test_frozen_3_6_reject_does_not_take_forms(self):
        reference = graph(
            [("a_reject", "action", "reject claim"),
             ("b_send", "action", "send relevant forms"),
             ("c_register", "action", "register claim")],
            [],
        )
        generated = graph([
            ("a_inform", "action", "inform claimant of rejection"),
            ("b_simple", "action", "send simple forms"),
            ("c_complex", "action", "send complex forms"),
            ("d_register", "action", "register claim in system"),
        ], [])
        result = actions(reference, generated, MatrixSimilarity([
            [0.8044, 0.4776, 0.40, 0.4786],
            [0.10, 0.6287, 0.5933, 0.10],
            [0.10, 0.6422, 0.50, 0.8642],
        ]))
        self.assertNotIn("a_reject", result.reference_to_generated)
        self.assertEqual(result.reference_to_generated["b_send"], "b_simple")
        self.assertEqual(result.reference_to_generated["c_register"], "d_register")

    def test_frozen_3_3_candidate_3_preserves_write_match(self):
        reference = graph([
            ("a_write", "action", "write recommendation"),
            ("b_check", "action", "check recommendation"),
        ], [])
        generated = graph([
            ("a_written", "action", "write settlement recommendation"),
            ("b_repeat", "action", "repeat recommendation"),
        ], [])
        result = actions(reference, generated, MatrixSimilarity([
            [0.4504, 0.5491],
            [0.10, 0.4945],
        ]))
        self.assertEqual(result.reference_to_generated, {"a_write": "a_written"})

    def test_frozen_4_1_candidate_3_preserves_assign_match(self):
        reference = graph([
            ("a_assign", "action", "assign intakers"),
            ("b_plan", "action", "plan meeting first intaker"),
            ("c_meeting", "action", "meeting with first intaker"),
        ], [])
        generated = graph([
            ("a_assigned", "action", "assign patients to intakers"),
            ("b_cards", "action", "pass registration cards to intakers"),
            ("c_produced", "action", "produce registration cards for intakers"),
            ("d_planned", "action", "have first intaker plan a meeting with patient"),
            ("e_performed", "action", "perform first meeting using checklist"),
        ], [])
        result = actions(reference, generated, MatrixSimilarity([
            [0.7376, 0.6260, 0.6092, 0.10, 0.10],
            [0.10, 0.10, 0.10, 0.9105, 0.4526],
            [0.6262, 0.5650, 0.10, 0.8471, 0.80],
        ]))
        self.assertEqual(result.reference_to_generated, {
            "a_assign": "a_assigned",
            "b_plan": "d_planned",
            "c_meeting": "e_performed",
        })

    def test_unknown_context_dependent_language_is_not_vetoed(self):
        self.assertTrue(compatibility_veto("handle case", "process case").compatible)

    def test_ordered_duplicate_occurrences_use_occurrence_order(self):
        reference = graph(
            [("r1", "action", "check"), ("x", "action", "middle"), ("r2", "action", "check")],
            [("r1", "x"), ("x", "r2")],
        )
        generated = graph(
            [("g2", "action", "check"), ("y", "action", "middle"), ("g1", "action", "check")],
            [("g2", "y"), ("y", "g1")],
        )
        result = actions(reference, generated)
        self.assertEqual(result.reference_to_generated["r1"], "g2")
        self.assertEqual(result.reference_to_generated["r2"], "g1")
        self.assertFalse(any(match.occurrence_ambiguous for match in result.matches))

    def test_parallel_duplicate_occurrences_remain_ambiguous(self):
        reference = graph(
            [("f", "fork", None), ("r1", "action", "check"), ("r2", "action", "check")],
            [("f", "r1"), ("f", "r2")],
        )
        generated = graph(
            [("f", "fork", None), ("g1", "action", "check"), ("g2", "action", "check")],
            [("f", "g1"), ("f", "g2")],
        )
        result = actions(reference, generated)
        self.assertTrue(all(match.occurrence_ambiguous for match in result.matches))

    def test_possible_split_preserves_raw_one_to_one_counts(self):
        reference = graph([("r", "action", "receive and retrieve application")], [])
        generated = graph(
            [("g1", "action", "receive application"), ("g2", "action", "retrieve application")],
            [("g1", "g2")],
        )
        result = actions(reference, generated, MatrixSimilarity([[0.9, 0.8]]))
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (1, 1, 0))
        self.assertTrue(any("possible_split_action" in item.payload.get("review_triggers", [])
                            for item in result.items))

    def test_possible_merge_preserves_raw_one_to_one_counts(self):
        reference = graph(
            [("r1", "action", "receive application"), ("r2", "action", "retrieve application")],
            [("r1", "r2")],
        )
        generated = graph([("g", "action", "receive and retrieve application")], [])
        result = actions(reference, generated, MatrixSimilarity([[0.9], [0.8]]))
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (1, 0, 1))
        self.assertTrue(any("possible_merge_action" in item.payload.get("review_triggers", [])
                            for item in result.items))


class RunnerShapeTests(unittest.TestCase):
    @staticmethod
    def config(case_count, candidates_per_case):
        return {
            "case_ids": [f"case_{index}" for index in range(1, case_count + 1)],
            "expected_case_count": case_count,
            "candidates_per_case": candidates_per_case,
            "expected_candidate_count": case_count * candidates_per_case,
        }

    @staticmethod
    def generated(config):
        return {
            case_id: {
                "candidates": [
                    {
                        "candidate_id": f"candidate_{index}",
                        "generation_status": "success",
                    }
                    for index in range(1, config["candidates_per_case"] + 1)
                ]
            }
            for case_id in config["case_ids"]
        }

    def test_preflight_shape_accepts_five_cases_and_fifteen_candidates(self):
        config = self.config(5, 3)
        _validate_run_shape(config, self.generated(config))

    def test_formal_shape_accepts_forty_cases_and_one_hundred_twenty_candidates(self):
        config = self.config(40, 3)
        _validate_run_shape(config, self.generated(config))

    def test_incorrect_total_candidate_count_fails_clearly(self):
        config = self.config(5, 3)
        config["expected_candidate_count"] = 14
        with self.assertRaisesRegex(ValueError, "cases times candidates per case"):
            _validate_run_shape(config, self.generated(self.config(5, 3)))

    def test_incorrect_per_case_candidate_count_fails_clearly(self):
        config = self.config(5, 3)
        generated = self.generated(config)
        generated["case_3"]["candidates"].pop()
        with self.assertRaisesRegex(ValueError, "Expected 3 candidates for case case_3"):
            _validate_run_shape(config, generated)

    def test_duplicate_and_missing_candidate_ids_fail_clearly(self):
        config = self.config(5, 3)
        duplicate = self.generated(config)
        duplicate["case_2"]["candidates"][2]["candidate_id"] = "candidate_2"
        with self.assertRaisesRegex(ValueError, "Duplicate candidate IDs for case case_2"):
            _validate_run_shape(config, duplicate)

        missing = self.generated(config)
        missing["case_2"]["candidates"][2]["candidate_id"] = ""
        with self.assertRaisesRegex(ValueError, "Candidate IDs for case case_2"):
            _validate_run_shape(config, missing)


class FlowMethodologyTests(unittest.TestCase):
    def test_generated_intermediate_preserves_required_order(self):
        reference = graph([("A", "action", "a"), ("B", "action", "b")], [("A", "B")])
        generated = graph(
            [("a", "action", "a"), ("x", "action", "extra"), ("b", "action", "b")],
            [("a", "x"), ("x", "b")],
        )
        result = evaluate_flow("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertEqual((result.counts.tp, result.counts.fn), (1, 0))

    def test_unmatched_reference_intermediate_is_preserved_before_reduction(self):
        reference = graph(
            [("A", "action", "a"), ("X", "action", "missing"), ("B", "action", "b")],
            [("A", "X"), ("X", "B")],
        )
        generated = graph([("a", "action", "a"), ("b", "action", "b")], [("a", "b")])
        result = evaluate_flow("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertEqual(result.reference_facts, (("A", "B"),))
        self.assertEqual(result.counts.tp, 1)

    def test_reversal_is_fn_and_fp(self):
        reference = graph([("A", "action", "a"), ("B", "action", "b")], [("A", "B")])
        generated = graph([("a", "action", "a"), ("b", "action", "b")], [("b", "a")])
        result = evaluate_flow("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (0, 1, 1))

    def test_parallel_and_exclusive_serialization_create_fp(self):
        for control_type in ("fork", "decision"):
            reference = graph(
                [("c", control_type, None), ("A", "action", "a"), ("B", "action", "b")],
                [("c", "A"), ("c", "B")],
            )
            generated = graph([("a", "action", "a"), ("b", "action", "b")], [("a", "b")])
            result = evaluate_flow("case", "candidate_1", reference, generated, actions(reference, generated))
            self.assertEqual(result.counts.fp, 1)

    def test_same_cycle_has_no_strict_precedence(self):
        reference = graph([("A", "action", "a"), ("B", "action", "b")], [("A", "B"), ("B", "A")])
        generated = graph([("a", "action", "a"), ("b", "action", "b")], [("a", "b"), ("b", "a")])
        result = evaluate_flow("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertEqual((result.reference_facts, result.generated_facts), ((), ()))

    def test_disconnected_required_relation_is_fn(self):
        reference = graph([("A", "action", "a"), ("B", "action", "b")], [("A", "B")])
        generated = graph([("a", "action", "a"), ("b", "action", "b")], [])
        result = evaluate_flow("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertEqual(result.counts.fn, 1)

    def test_empty_flow_is_reported_as_not_defined(self):
        reference = graph([("A", "action", "a")], [])
        generated = graph([("a", "action", "a")], [])
        result = evaluate_flow("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertFalse(result.metric_defined)


class StructureMethodologyTests(unittest.TestCase):
    @staticmethod
    def choice(control_type="decision", missing_third=False):
        nodes = [
            ("A", "action", "start"), ("d", control_type, None),
            ("B", "action", "left"), ("C", "action", "right"),
            ("E", "action", "third"), ("m", "merge" if control_type == "decision" else "join", None),
            ("D", "action", "finish"),
        ]
        edges = [("A", "d"), ("d", "B", "yes"), ("d", "C", "no"),
                 ("B", "m"), ("C", "m"), ("m", "D")]
        if not missing_third:
            edges.extend([("d", "E", "maybe"), ("E", "m")])
        return graph(nodes, edges)

    def test_exclusive_two_and_three_branch_regions_score_perfectly(self):
        for missing_third in (True, False):
            reference = self.choice(missing_third=missing_third)
            generated = self.choice(missing_third=missing_third)
            result = evaluate_structure("case", "candidate_1", reference, generated, actions(reference, generated))
            self.assertEqual(result.counts.f1, 1.0)

    def test_parallel_two_and_three_branch_regions_score_perfectly(self):
        for missing_third in (True, False):
            reference = self.choice("fork", missing_third)
            generated = self.choice("fork", missing_third)
            result = evaluate_structure("case", "candidate_1", reference, generated, actions(reference, generated))
            self.assertEqual(result.counts.f1, 1.0)

    def test_missing_branch_receives_bounded_partial_credit(self):
        reference = self.choice()
        generated = self.choice(missing_third=True)
        result = evaluate_structure("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertGreater(result.counts.f1, 0.0)
        self.assertLess(result.counts.f1, 1.0)

    def test_wrong_mode_scores_mode_as_incorrect_without_blocking_alignment(self):
        reference = self.choice("decision", True)
        generated = self.choice("fork", True)
        result = evaluate_structure("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertEqual(len(result.region_scores), 1)
        self.assertEqual(result.region_scores[0].component_scores["mode"], 0.0)
        self.assertGreater(result.counts.tp, 0.0)

    def test_missing_region_is_exactly_one_fn(self):
        reference = self.choice("fork", True)
        generated = graph(
            [("A", "action", "start"), ("B", "action", "left"),
             ("C", "action", "right"), ("D", "action", "finish")],
            [("A", "B"), ("B", "C"), ("C", "D")],
        )
        result = evaluate_structure("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (0.0, 0.0, 1.0))
        self.assertEqual(result.region_coverage, 0.0)
        self.assertEqual(result.component_coverage, 0.0)

    def test_extra_loop_is_exactly_one_fp(self):
        reference = graph([("A", "action", "start"), ("C", "action", "finish")], [("A", "C")])
        generated = graph(
            [("A", "action", "start"), ("d", "decision", None),
             ("B", "action", "retry"), ("C", "action", "finish")],
            [("A", "d"), ("d", "B"), ("B", "d"), ("d", "C")],
        )
        result = evaluate_structure("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertEqual(result.counts.fp, 1.0)

    def test_loop_has_mode_body_and_exit_components(self):
        loop = graph(
            [("A", "action", "start"), ("d", "decision", None),
             ("B", "action", "retry"), ("C", "action", "finish")],
            [("A", "d"), ("d", "B"), ("B", "d"), ("d", "C")],
        )
        result = evaluate_structure("case", "candidate_1", loop, loop, actions(loop, loop))
        self.assertEqual(result.counts.f1, 1.0)
        self.assertEqual(set(result.region_scores[0].component_scores), {"mode", "loop_body", "exit"})

    def test_unmatched_anchor_components_are_na_and_reviewed(self):
        reference = self.choice("decision", True)
        generated = graph(
            [("A", "action", "start"), ("d", "decision", None),
             ("B", "action", "left"), ("m", "merge", None), ("D", "action", "finish")],
            [("A", "d"), ("d", "B"), ("d", "m"), ("B", "m"), ("m", "D")],
        )
        result = evaluate_structure("case", "candidate_1", reference, generated, actions(reference, generated))
        paired = next(score for score in result.region_scores if score.generated_region_id)
        self.assertIsNone(paired.component_scores["branch_semantics"])
        self.assertIn("anchor_limited_structure_region", paired.review_triggers)

    def test_structure_review_is_one_region_centered_row(self):
        reference = self.choice()
        generated = self.choice(missing_third=True)
        structure = evaluate_structure("case", "candidate_1", reference, generated, actions(reference, generated))
        rows = build_review_rows(structure.items, 7)
        region_rows = [row for row in rows if row["metric"] == "Structure"]
        self.assertLessEqual(len(region_rows), len(structure.region_scores))

    def test_empty_structure_is_reported_as_not_defined(self):
        reference = graph([("A", "action", "a")], [])
        generated = graph([("a", "action", "a")], [])
        result = evaluate_structure("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertFalse(result.metric_defined)
        self.assertIsNone(result.component_coverage)
        self.assertIsNone(result.region_coverage)

    def test_control_neutral_boundary_shift_can_align(self):
        reference = self.choice("decision", True)
        generated = graph(
            [("A", "action", "start"), ("neutral", "merge", None), ("d", "decision", None),
             ("B", "action", "left"), ("C", "action", "right"),
             ("m", "merge", None), ("D", "action", "finish")],
            [("A", "neutral"), ("neutral", "d"), ("d", "B", "yes"), ("d", "C", "no"),
             ("B", "m"), ("C", "m"), ("m", "D")],
        )
        result = evaluate_structure("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertEqual(result.counts.f1, 1.0)

    def test_missing_entry_does_not_suppress_matching_continuation(self):
        reference = graph(
            [("rd", "decision", None), ("rb", "action", "reference retry"),
             ("exit", "action", "finish")],
            [("rd", "rb"), ("rb", "rd"), ("rd", "exit")],
        )
        generated = graph(
            [("gd", "decision", None), ("gb", "action", "generated retry"),
             ("exit_g", "action", "finish"),
             ("choice", "decision", None), ("overlap", "action", "reference retry"),
             ("other", "action", "other"), ("merge", "merge", None)],
            [("gd", "gb"), ("gb", "gd"), ("gd", "exit_g"),
             ("choice", "overlap"), ("choice", "other"),
             ("overlap", "merge"), ("other", "merge")],
        )
        action_result = anchored_actions(reference, generated, [("rb", "overlap"), ("exit", "exit_g")])
        result = evaluate_structure("case", "candidate_1", reference, generated, action_result)
        reference_loop = next(region for region in result.reference_regions if region.mode == "loop")
        generated_loop = next(region for region in result.generated_regions if region.mode == "loop")
        paired = next(score for score in result.region_scores
                      if score.reference_region_id == reference_loop.region_id)
        self.assertEqual(paired.generated_region_id, generated_loop.region_id)
        self.assertEqual(paired.alignment_rationale["boundary_agreement"], 1)
        self.assertFalse(any(score.generated_region_id == generated_loop.region_id
                             and score.reference_region_id is None for score in result.region_scores))

    def test_matching_entry_does_not_require_continuation(self):
        reference = graph(
            [("entry", "action", "start"), ("rd", "decision", None),
             ("rb", "action", "reference retry")],
            [("entry", "rd"), ("rd", "rb"), ("rb", "rd")],
        )
        generated = graph(
            [("entry_g", "action", "start"), ("gd", "decision", None),
             ("gb", "action", "generated retry")],
            [("entry_g", "gd"), ("gd", "gb"), ("gb", "gd")],
        )
        result = evaluate_structure(
            "case", "candidate_1", reference, generated,
            anchored_actions(reference, generated, [("entry", "entry_g")]),
        )
        paired = next(score for score in result.region_scores if score.reference_region_id)
        self.assertIsNotNone(paired.generated_region_id)
        self.assertEqual(paired.alignment_rationale["boundary_agreement"], 1)

    def test_parallel_synchronization_does_not_require_join_gateway_identity(self):
        reference = self.choice("fork", True)
        generated = graph(
            [("A", "action", "start"), ("d", "fork", None),
             ("B", "action", "left"), ("C", "action", "right"), ("D", "action", "finish")],
            [("A", "d"), ("d", "B"), ("d", "C"), ("B", "D"), ("C", "D")],
        )
        result = evaluate_structure("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertEqual(result.region_scores[0].component_scores["closure_synchronization"], 1.0)

    def test_missing_parallel_synchronization_loses_closure_credit(self):
        reference = self.choice("fork", True)
        generated = graph(
            [("A", "action", "start"), ("d", "fork", None),
             ("B", "action", "left"), ("C", "action", "right"), ("D", "action", "finish")],
            [("A", "d"), ("d", "B"), ("d", "C"), ("B", "D")],
        )
        result = evaluate_structure("case", "candidate_1", reference, generated, actions(reference, generated))
        paired = next(score for score in result.region_scores if score.generated_region_id)
        self.assertEqual(paired.component_scores["closure_synchronization"], 0.0)

    def test_nested_parallel_region_has_hierarchical_depth(self):
        nested = graph(
            [("A", "action", "start"), ("d", "decision", None), ("B", "action", "outer"),
             ("f", "fork", None), ("C", "action", "parallel one"), ("E", "action", "parallel two"),
             ("j", "join", None), ("m", "merge", None), ("D", "action", "finish")],
            [("A", "d"), ("d", "B"), ("d", "f"), ("f", "C"), ("f", "E"),
             ("C", "j"), ("E", "j"), ("j", "m"), ("B", "m"), ("m", "D")],
        )
        result = evaluate_structure("case", "candidate_1", nested, nested, actions(nested, nested))
        self.assertEqual(sorted(region.depth for region in result.reference_regions), [0, 1])
        self.assertEqual(result.counts.f1, 1.0)

    def test_same_footprint_nested_regions_use_control_containment(self):
        nested = graph(
            [("A", "action", "start"), ("d1", "decision", None), ("d2", "decision", None),
             ("B", "action", "left"), ("C", "action", "right"),
             ("m2", "merge", None), ("m1", "merge", None), ("D", "action", "finish")],
            [("A", "d1"), ("d1", "d2"), ("d1", "m1"), ("d2", "B"), ("d2", "C"),
             ("B", "m2"), ("C", "m2"), ("m2", "m1"), ("m1", "D")],
        )
        result = evaluate_structure("case", "candidate_1", nested, nested, actions(nested, nested))
        self.assertEqual(sorted(region.depth for region in result.reference_regions), [0, 1])

    def test_boundary_crossing_branching_control_is_not_neutral(self):
        nested = graph(
            [("A", "action", "start"), ("d1", "decision", None), ("d2", "decision", None),
             ("X", "action", "outside"), ("B", "action", "left"), ("C", "action", "right"),
             ("m", "merge", None), ("D", "action", "finish")],
            [("A", "d1"), ("d1", "d2"), ("d1", "X"), ("d2", "B"), ("d2", "C"),
             ("B", "m"), ("C", "m"), ("X", "m"), ("m", "D")],
        )
        result = evaluate_structure("case", "candidate_1", nested, nested, actions(nested, nested))
        child = next(region for region in result.reference_regions if region.region_id == "d2")
        self.assertFalse(child.entry_boundary_comparable)
        self.assertTrue(child.continuation_boundary_comparable)

    def test_unsafe_continuation_does_not_suppress_safe_entry(self):
        reference = self.choice("decision", True)
        generated = self.choice("decision", True)
        action_result = actions(reference, generated)
        reference_region = evaluate_structure(
            "case", "candidate_1", reference, generated, action_result
        ).reference_regions[0]
        self.assertTrue(reference_region.entry_boundary_comparable)
        self.assertTrue(reference_region.continuation_boundary_comparable)

        from dataclasses import replace
        from evaluation.friedrich_v3.structure import _alignment_score

        unsafe_generated = replace(reference_region, continuation_boundary_comparable=False)
        boundary, _, _ = _alignment_score(reference_region, unsafe_generated)
        self.assertEqual(boundary, 1)

    def test_unsafe_entry_does_not_suppress_safe_continuation(self):
        reference = self.choice("decision", True)
        region = evaluate_structure(
            "case", "candidate_1", reference, reference, actions(reference, reference)
        ).reference_regions[0]

        from dataclasses import replace
        from evaluation.friedrich_v3.structure import _alignment_score

        unsafe_generated = replace(region, entry_boundary_comparable=False)
        boundary, _, _ = _alignment_score(region, unsafe_generated)
        self.assertEqual(boundary, 1)

    def test_mixed_aligned_and_missing_regions_have_half_region_coverage(self):
        reference = graph([
            ("d1", "decision", None), ("a", "action", "a"), ("b", "action", "b"),
            ("m1", "merge", None), ("d2", "decision", None),
            ("c", "action", "c"), ("d", "action", "d"), ("m2", "merge", None),
        ], [
            ("d1", "a"), ("d1", "b"), ("a", "m1"), ("b", "m1"),
            ("d2", "c"), ("d2", "d"), ("c", "m2"), ("d", "m2"),
        ])
        generated = graph([
            ("g1", "decision", None), ("a_g", "action", "a"),
            ("b_g", "action", "b"), ("gm", "merge", None),
        ], [("g1", "a_g"), ("g1", "b_g"), ("a_g", "gm"), ("b_g", "gm")])
        result = evaluate_structure("case", "candidate_1", reference, generated,
                                    actions(reference, generated))
        self.assertEqual(result.region_coverage, 0.5)

    def test_partial_and_perfect_component_coverage(self):
        perfect = self.choice("decision", True)
        perfect_result = evaluate_structure(
            "case", "candidate_1", perfect, perfect, actions(perfect, perfect)
        )
        self.assertEqual(perfect_result.component_coverage, 1.0)

        generated = graph(
            [("A", "action", "start"), ("d", "decision", None),
             ("B", "action", "left"), ("m", "merge", None), ("D", "action", "finish")],
            [("A", "d"), ("d", "B"), ("d", "m"), ("B", "m"), ("m", "D")],
        )
        partial_result = evaluate_structure(
            "case", "candidate_1", perfect, generated, actions(perfect, generated)
        )
        self.assertEqual(partial_result.component_coverage, 0.5)

    def test_coverage_aggregate_ignores_na(self):
        self.assertEqual(_optional_mean([None, 0.5, 1.0]), 0.75)

    def test_exact_guards_are_a_scorable_component(self):
        guarded = self.choice("decision", True)
        result = evaluate_structure("case", "candidate_1", guarded, guarded, actions(guarded, guarded))
        self.assertEqual(result.region_scores[0].component_scores["guard"], 1.0)

    def test_noncomparable_guard_is_na_and_reviewed(self):
        reference = self.choice("decision", True)
        generated = graph(
            [("A", "action", "start"), ("d", "decision", None),
             ("B", "action", "left"), ("C", "action", "right"),
             ("m", "merge", None), ("D", "action", "finish")],
            [("A", "d"), ("d", "B", "yes"), ("d", "C"),
             ("B", "m"), ("C", "m"), ("m", "D")],
        )
        result = evaluate_structure("case", "candidate_1", reference, generated, actions(reference, generated))
        self.assertIsNone(result.region_scores[0].component_scores["guard"])
        self.assertIn("guard_ambiguity", result.region_scores[0].review_triggers)

    def test_nested_exclusive_regions_align_parent_first(self):
        nested = graph(
            [("A", "action", "start"), ("d1", "decision", None),
             ("B", "action", "outer left"), ("d2", "decision", None),
             ("C", "action", "inner left"), ("E", "action", "inner right"),
             ("m2", "merge", None), ("m1", "merge", None), ("D", "action", "finish")],
            [("A", "d1"), ("d1", "B"), ("d1", "d2"), ("d2", "C"), ("d2", "E"),
             ("C", "m2"), ("E", "m2"), ("m2", "m1"), ("B", "m1"), ("m1", "D")],
        )
        result = evaluate_structure("case", "candidate_1", nested, nested, actions(nested, nested))
        self.assertEqual(len(result.reference_regions), 2)
        self.assertEqual(result.counts.f1, 1.0)
        self.assertEqual(sorted(region.depth for region in result.reference_regions), [0, 1])


class HumanReviewMethodologyTests(unittest.TestCase):
    def test_hard_veto_does_not_itself_trigger_review(self):
        reference = graph([("r", "action", "approve request")], [])
        generated = graph([("g", "action", "reject request")], [])
        result = actions(reference, generated, MatrixSimilarity([[0.99]]))
        rows = build_review_rows(result.items, 7)
        self.assertFalse(any("compatibility" in row["review_trigger"] for row in rows))

    def test_review_generation_does_not_mutate_raw_counts(self):
        reference = graph([("r", "action", "receive and retrieve application")], [])
        generated = graph(
            [("g1", "action", "receive application"), ("g2", "action", "retrieve application")],
            [("g1", "g2")],
        )
        result = actions(reference, generated, MatrixSimilarity([[0.9, 0.8]]))
        before = result.counts
        build_review_rows(result.items, 7)
        self.assertEqual(result.counts, before)

    def test_sensitivity_counts_are_separate_and_do_not_synthesize_anchors(self):
        raw = [{
            "case_id": "case", "candidate_id": "candidate_1",
            "action_tp": 1, "action_fp": 1, "action_fn": 0,
            "flow_tp": 1, "flow_fp": 0, "flow_fn": 0,
            "structure_tp": 1.0, "structure_fp": 0.0, "structure_fn": 0.0,
        }]
        review = [{
            "case_id": "case", "candidate_id": "candidate_1", "metric": "Action",
            "final_verdict": "overturn", "sensitivity_tp_delta": "",
            "sensitivity_fp_delta": "-1", "sensitivity_fn_delta": "",
        }]
        sensitivity = build_sensitivity_results(raw, review)
        self.assertEqual(sensitivity["status"], "computed")
        self.assertFalse(sensitivity["many_to_many_anchors_synthesized"])
        self.assertEqual(sensitivity["candidate_counts"][0]["action_fp"], 0.0)


if __name__ == "__main__":
    unittest.main()
