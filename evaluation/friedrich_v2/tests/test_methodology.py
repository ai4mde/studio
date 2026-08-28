from __future__ import annotations

import unittest
import json
from pathlib import Path

from evaluation.friedrich_v2.action import evaluate_actions
from evaluation.friedrich_v2.adapters import activity_graph_to_eval_graph
from evaluation.friedrich_v2.core import EvalEdge, EvalGraph, EvalNode
from evaluation.friedrich_v2.diagnostics import find_model_validity_diagnostics, find_redundant_control_nodes
from evaluation.friedrich_v2.flow import evaluate_flow
from evaluation.friedrich_v2.human_review import build_review_rows
from evaluation.friedrich_v2.structure import evaluate_structure, extract_structure_facts


def graph(nodes, edges):
    return EvalGraph(
        tuple(EvalNode(node_id, node_type, label) for node_id, node_type, label in nodes),
        tuple(EvalEdge(source, target) for source, target in edges),
    )


class ExactSimilarity:
    def matrix(self, reference, generated):
        return [[1.0 if left == right else 0.0 for right in generated] for left in reference]


class MatrixSimilarity:
    def __init__(self, values):
        self.values = values

    def matrix(self, reference, generated):
        return self.values


class MethodologyTests(unittest.TestCase):
    @staticmethod
    def guarded_choice(*, reversed_outcomes=False, missing_guard=False, duplicate_guard=False, generated=False):
        prefix = "g" if generated else ""
        nodes = (
            EvalNode(prefix + "A", "action", "check insurance"), EvalNode(prefix + "d", "decision"),
            EvalNode(prefix + "Y", "action", "continue"), EvalNode(prefix + "N", "action", "reject"),
            EvalNode(prefix + "m", "merge"), EvalNode(prefix + "D", "action", "finish"),
        )
        insured_target = prefix + ("N" if reversed_outcomes else "Y")
        uninsured_target = prefix + ("Y" if reversed_outcomes else "N")
        second_guard = "insured" if duplicate_guard else "not insured"
        edges = (
            EvalEdge(prefix + "A", prefix + "d"),
            EvalEdge(prefix + "d", insured_target, None if missing_guard else "insured"),
            EvalEdge(prefix + "d", uninsured_target, second_guard),
            EvalEdge(prefix + "Y", prefix + "m"), EvalEdge(prefix + "N", prefix + "m"),
            EvalEdge(prefix + "m", prefix + "D"),
        )
        return EvalGraph(nodes, edges)

    def test_action_maximizes_cardinality_before_similarity(self):
        reference = graph([("r1", "action", "one"), ("r2", "action", "two")], [])
        generated = graph([("g1", "action", "alpha"), ("g2", "action", "beta")], [])
        result = evaluate_actions(
            "case", "candidate_1", reference, generated,
            MatrixSimilarity([[0.99, 0.45], [0.45, 0.1]]), 0.44,
        )
        self.assertEqual({(m.reference_id, m.generated_id) for m in result.matches}, {("r1", "g2"), ("r2", "g1")})

    def test_duplicate_occurrences_follow_precedence_order(self):
        reference = graph([("r1", "action", "check"), ("r2", "action", "check")], [("r1", "r2")])
        generated = graph([("g1", "action", "check"), ("g2", "action", "check")], [("g1", "g2")])
        result = evaluate_actions("case", "candidate_1", reference, generated, MatrixSimilarity([[1, 1], [1, 1]]), 0.44)
        self.assertEqual([(m.reference_id, m.generated_id) for m in result.matches], [("r1", "g1"), ("r2", "g2")])
        self.assertFalse(any(match.occurrence_ambiguous for match in result.matches))

    def test_parallel_duplicate_occurrences_are_marked_ambiguous(self):
        reference = graph([("r1", "action", "check"), ("r2", "action", "check")], [])
        generated = graph([("g1", "action", "check"), ("g2", "action", "check")], [])
        result = evaluate_actions("case", "candidate_1", reference, generated, MatrixSimilarity([[1, 1], [1, 1]]), 0.44)
        self.assertTrue(all(match.occurrence_ambiguous for match in result.matches))

    def test_longer_semantic_paraphrase_is_not_rejected_lexically(self):
        reference = graph([("r", "action", "retrieve sct file")], [])
        generated = graph([("g", "action", "receive request and retrieve the sct file")], [])
        result = evaluate_actions("case", "candidate_1", reference, generated, MatrixSimilarity([[0.78]]), 0.44)
        self.assertEqual(result.counts.tp, 1)

    def test_possible_split_is_review_only(self):
        reference = graph([("r", "action", "review request")], [])
        generated = graph([("g1", "action", "review request"), ("g2", "action", "check request")], [])
        result = evaluate_actions("case", "candidate_1", reference, generated, MatrixSimilarity([[0.9, 0.7]]), 0.44,
                                  source_text="Review and check the request.")
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (1, 1, 0))
        rows = build_review_rows(result.items, 7)
        self.assertTrue(any("possible_split_action" in row["review_trigger"] for row in rows))

    def test_action_uses_global_one_to_one_assignment(self):
        reference = graph([("r1", "action", "one"), ("r2", "action", "two")], [])
        generated = graph([("g1", "action", "alpha"), ("g2", "action", "beta")], [])
        result = evaluate_actions("case", "candidate_1", reference, generated, MatrixSimilarity([[0.9, 0.8], [0.85, 0.1]]), 0.2)
        self.assertEqual({(m.reference_id, m.generated_id) for m in result.matches}, {("r1", "g2"), ("r2", "g1")})
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (2, 0, 0))

    def test_unmatched_action_does_not_create_flow_error(self):
        reference = graph([("A", "action", "a"), ("B", "action", "b")], [("A", "B")])
        generated = graph([("a", "action", "a"), ("x", "action", "extra"), ("b", "action", "b")], [("a", "x"), ("x", "b")])
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        flow = evaluate_flow("case", "candidate_1", reference, generated, actions)
        self.assertEqual(flow.counts.tp, 1)
        self.assertEqual((flow.counts.fp, flow.counts.fn), (0, 0))
        self.assertEqual(actions.counts.fp, 1)

    def test_parallel_siblings_are_not_precedence(self):
        nodes = [("A", "action", "a"), ("f", "fork", None), ("B", "action", "b"),
                 ("C", "action", "c"), ("j", "join", None), ("D", "action", "d")]
        edges = [("A", "f"), ("f", "B"), ("f", "C"), ("B", "j"), ("C", "j"), ("j", "D")]
        reference = graph(nodes, edges)
        generated = graph([("g" + value, kind, label) for value, kind, label in nodes],
                          [("g" + left, "g" + right) for left, right in edges])
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        result = evaluate_flow("case", "candidate_1", reference, generated, actions)
        self.assertNotIn(("B", "C"), result.reference_facts)
        self.assertNotIn(("C", "B"), result.reference_facts)
        self.assertEqual((result.counts.fp, result.counts.fn), (0, 0))

    def test_structure_scores_atomic_exclusive_facts(self):
        nodes = [("A", "action", "a"), ("d", "decision", None), ("B", "action", "b"),
                 ("C", "action", "c"), ("m", "merge", None), ("D", "action", "after")]
        edges = [("A", "d"), ("d", "B"), ("d", "C"), ("B", "m"), ("C", "m"), ("m", "D")]
        reference = graph(nodes, edges)
        generated = graph([("g" + value, kind, label) for value, kind, label in nodes],
                          [("g" + left, "g" + right) for left, right in edges])
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        result = evaluate_structure("case", "candidate_1", reference, generated, actions)
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (4, 0, 0))
        self.assertEqual((result.counts.precision, result.counts.recall, result.counts.f1), (1.0, 1.0, 1.0))
        self.assertEqual({fact[0] for fact in result.reference_facts}, {"mode", "branch", "exclusive_convergence"})

    def test_direct_decision_branch_to_merge_is_empty(self):
        model = graph(
            [("A", "action", "before"), ("d", "decision", None), ("B", "action", "branch"),
             ("m", "merge", None), ("C", "action", "after"), ("n", "decision", None),
             ("D", "action", "later"), ("m2", "merge", None)],
            [("A", "d"), ("d", "m"), ("d", "B"), ("B", "m"), ("m", "C"),
             ("C", "n"), ("n", "D"), ("n", "m2"), ("D", "m2")],
        )
        facts, _, _ = extract_structure_facts(model, {node.id: node.id for node in model.nodes if node.type == "action"})
        first_branches = [fact for fact in facts if fact[0] == "branch" and fact[1] == "A->C"]
        self.assertIn(("branch", "A->C", ("exclusive", "EMPTY")), first_branches)
        self.assertIn(("branch", "A->C", ("exclusive", "B")), first_branches)
        self.assertFalse(any("D" in fact[2] for fact in first_branches))

    def test_direct_fork_branch_to_join_is_empty(self):
        model = graph(
            [("A", "action", "before"), ("f", "fork", None), ("B", "action", "branch"),
             ("j", "join", None), ("C", "action", "after")],
            [("A", "f"), ("f", "j"), ("f", "B"), ("B", "j"), ("j", "C")],
        )
        facts, _, _ = extract_structure_facts(model, {"A": "A", "B": "B", "C": "C"})
        self.assertIn(("branch", "A->C", ("parallel", "EMPTY")), facts)
        self.assertIn(("branch", "A->C", ("parallel", "B")), facts)

    def test_frozen_3_2_reference_has_empty_exclusive_branch_without_leakage(self):
        manifest = json.loads((Path(__file__).parents[1] / "manifests" / "source_manifest.json").read_text())
        case = next(item for item in manifest["cases"] if item["case_id"] == "3-2")
        from evaluation.friedrich_v2.adapters import friedrich_reference_to_eval_graph
        model = friedrich_reference_to_eval_graph(case["reference_model_path"])
        facts, _, _ = extract_structure_facts(model, {node.id: node.id for node in model.nodes if node.type == "action"})
        branches = [fact for fact in facts if fact[0] == "branch" and fact[1] == "121->160"]
        self.assertIn(("branch", "121->160", ("exclusive", "EMPTY")), branches)
        self.assertFalse(any("160" in fact[2] for fact in branches))

    def test_structure_empty_reference_and_generated_are_perfect(self):
        reference = graph([("A", "action", "a"), ("B", "action", "b")], [("A", "B")])
        generated = graph([("a", "action", "a"), ("b", "action", "b")], [("a", "b")])
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        result = evaluate_structure("case", "candidate_1", reference, generated, actions)
        self.assertEqual((result.reference_facts, result.generated_facts), ((), ()))
        self.assertEqual((result.counts.precision, result.counts.recall, result.counts.f1), (1.0, 1.0, 1.0))

    def test_structure_empty_reference_and_nonempty_generated_are_false_positives(self):
        reference = graph([("A", "action", "a"), ("B", "action", "b")], [("A", "B")])
        generated = graph(
            [("a", "action", "a"), ("d", "decision", None), ("m", "merge", None), ("b", "action", "b")],
            [("a", "d"), ("d", "b"), ("d", "m"), ("m", "b")],
        )
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        result = evaluate_structure("case", "candidate_1", reference, generated, actions)
        self.assertFalse(result.reference_facts)
        self.assertGreater(result.counts.fp, 0)
        self.assertEqual(result.counts.fn, 0)
        self.assertEqual((result.counts.precision, result.counts.recall, result.counts.f1), (0.0, 0.0, 0.0))

    def test_structure_nonempty_reference_and_empty_generated_are_false_negatives(self):
        reference = graph(
            [("A", "action", "a"), ("d", "decision", None), ("m", "merge", None), ("B", "action", "b")],
            [("A", "d"), ("d", "B"), ("d", "m"), ("m", "B")],
        )
        generated = graph([("a", "action", "a"), ("b", "action", "b")], [("a", "b")])
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        result = evaluate_structure("case", "candidate_1", reference, generated, actions)
        self.assertFalse(result.generated_facts)
        self.assertGreater(result.counts.fn, 0)
        self.assertEqual(result.counts.fp, 0)
        self.assertEqual((result.counts.precision, result.counts.recall, result.counts.f1), (0.0, 0.0, 0.0))

    def test_loop_has_mode_body_and_exit(self):
        nodes = [("A", "action", "start"), ("d", "decision", None),
                 ("B", "action", "repeat"), ("C", "action", "exit")]
        edges = [("A", "d"), ("d", "B"), ("B", "d"), ("d", "C")]
        reference = graph(nodes, edges)
        generated = graph([(value.lower(), kind, label) for value, kind, label in nodes],
                          [(left.lower(), right.lower()) for left, right in edges])
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        result = evaluate_structure("case", "candidate_1", reference, generated, actions)
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (3, 0, 0))
        self.assertEqual({fact[0] for fact in result.reference_facts}, {"mode", "loop_body", "loop_exit"})

    def test_missing_executable_loop_remains_structure_error(self):
        reference = graph([("A", "action", "start"), ("d", "decision", None), ("B", "action", "retry"),
                           ("C", "action", "finish")], [("A", "d"), ("d", "B"), ("B", "d"), ("d", "C")])
        generated = graph([("a", "action", "start"), ("b", "action", "retry"), ("c", "action", "finish")],
                          [("a", "b"), ("b", "c")])
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        result = evaluate_structure("case", "candidate_1", reference, generated, actions)
        self.assertGreater(result.counts.fn, 0)

    def test_flow_reports_low_reference_fact_and_action_anchor_coverage(self):
        reference = graph([("A", "action", "a"), ("B", "action", "b"), ("C", "action", "c")],
                          [("A", "B"), ("B", "C")])
        generated = graph([("a", "action", "a")], [])
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        result = evaluate_flow("case", "candidate_1", reference, generated, actions)
        self.assertEqual(result.coverage, 0.0)
        self.assertAlmostEqual(result.action_anchor_coverage, 1 / 3)

    def test_ambiguous_anchors_are_reported_in_flow_and_structure(self):
        nodes = [("A", "action", "start"), ("f", "fork", None), ("B1", "action", "check"),
                 ("B2", "action", "check"), ("j", "join", None), ("C", "action", "finish")]
        edges = [("A", "f"), ("f", "B1"), ("f", "B2"), ("B1", "j"), ("B2", "j"), ("j", "C")]
        reference = graph(nodes, edges)
        generated = graph([("g" + i, t, label) for i, t, label in nodes], [("g" + a, "g" + b) for a, b in edges])
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        flow = evaluate_flow("case", "candidate_1", reference, generated, actions)
        structure = evaluate_structure("case", "candidate_1", reference, generated, actions)
        self.assertGreater(flow.occurrence_ambiguous_fact_count, 0)
        self.assertGreater(structure.anchor_limited_count, 0)

    def test_validity_reports_unreachable_and_non_final_dead_end(self):
        model = graph([("i", "initial", None), ("a", "action", "work"), ("f", "final", None),
                       ("x", "action", "orphan")], [("i", "a"), ("a", "f")])
        result = find_model_validity_diagnostics("case", "candidate_1", model)
        kinds = {item.payload["diagnostic_type"] for item in result.items}
        self.assertIn("unreachable_node", kinds)
        self.assertIn("non_final_dead_end", kinds)

    def test_guard_reversal_is_flagged_for_review_not_scored(self):
        reference = EvalGraph(
            (EvalNode("A", "action", "check"), EvalNode("d", "decision"), EvalNode("Y", "action", "accept"),
             EvalNode("N", "action", "reject")),
            (EvalEdge("A", "d"), EvalEdge("d", "Y", "insured"), EvalEdge("d", "N", "not insured")),
        )
        generated = EvalGraph(
            (EvalNode("a", "action", "check"), EvalNode("d", "decision"), EvalNode("y", "action", "accept"),
             EvalNode("n", "action", "reject")),
            (EvalEdge("a", "d"), EvalEdge("d", "n", "insured"), EvalEdge("d", "y", "not insured")),
        )
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        result = find_model_validity_diagnostics("case", "candidate_1", generated, reference, actions)
        self.assertIn("suspicious_reversed_outcome_mapping",
                      {item.payload["diagnostic_type"] for item in result.items})

    def test_correct_guard_outcomes_receive_raw_structure_credit(self):
        reference = self.guarded_choice()
        generated = self.guarded_choice(generated=True)
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        result = evaluate_structure("case", "candidate_1", reference, generated, actions)
        self.assertEqual(result.counts.f1, 1.0)
        self.assertEqual(sum(fact[0] == "guard_outcome" for fact in result.reference_facts), 2)

    def test_reversed_guard_outcomes_cannot_receive_perfect_raw_structure_credit(self):
        reference = self.guarded_choice()
        generated = self.guarded_choice(generated=True, reversed_outcomes=True)
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        result = evaluate_structure("case", "candidate_1", reference, generated, actions)
        self.assertLess(result.counts.f1, 1.0)
        self.assertGreater(result.counts.fp, 0)
        self.assertGreater(result.counts.fn, 0)

    def test_missing_guard_remains_unscored_and_diagnostic(self):
        reference = self.guarded_choice()
        generated = self.guarded_choice(generated=True, missing_guard=True)
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        structure = evaluate_structure("case", "candidate_1", reference, generated, actions)
        diagnostics = find_model_validity_diagnostics("case", "candidate_1", generated, reference, actions)
        self.assertEqual(structure.counts.f1, 1.0)
        self.assertFalse(any(fact[0] == "guard_outcome" for fact in structure.reference_facts))
        self.assertIn("missing_exclusive_guard", {item.payload["diagnostic_type"] for item in diagnostics.items})

    def test_ambiguous_duplicate_guards_remain_review_evidence(self):
        reference = self.guarded_choice()
        generated = self.guarded_choice(generated=True, duplicate_guard=True)
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        structure = evaluate_structure("case", "candidate_1", reference, generated, actions)
        diagnostics = find_model_validity_diagnostics("case", "candidate_1", generated, reference, actions)
        self.assertEqual(structure.counts.f1, 1.0)
        self.assertFalse(any(fact[0] == "guard_outcome" for fact in structure.reference_facts))
        self.assertIn("duplicate_or_conflicting_guard",
                      {item.payload["diagnostic_type"] for item in diagnostics.items})

    def test_task_vs_control_node_is_review_only(self):
        reference = graph([("r", "action", "approve request")], [])
        generated = EvalGraph(
            (EvalNode("d", "decision", "approve request"), EvalNode("f1", "final"), EvalNode("f2", "final")),
            (EvalEdge("d", "f1", "yes"), EvalEdge("d", "f2", "no")),
        )
        result = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (0, 0, 1))
        rows = build_review_rows(result.items, 7)
        self.assertTrue(any("task_vs_control_node" in row["review_trigger"] for row in rows))

    def test_source_scope_ambiguity_is_review_only(self):
        reference = graph([("r", "action", "receive application")], [])
        generated = graph([], [])
        result = evaluate_actions(
            "case", "candidate_1", reference, generated, ExactSimilarity(), 0.9,
            source_text="When the application arrives, receive application.",
        )
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (0, 0, 1))
        rows = build_review_rows(result.items, 7)
        self.assertTrue(any("source_scope_ambiguity" in row["review_trigger"] for row in rows))

    def test_unscorable_flow_preserves_full_action_anchor_coverage(self):
        reference = graph([("A", "action", "a"), ("B", "action", "b")], [("A", "B")])
        generated = EvalGraph(
            (EvalNode("a", "action", "a"), EvalNode("u", "unsupported_control", semantic_type="Inclusive"),
             EvalNode("b", "action", "b")),
            (EvalEdge("a", "u"), EvalEdge("u", "b")),
        )
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        result = evaluate_flow("case", "candidate_1", reference, generated, actions)
        self.assertTrue(result.unscorable)
        self.assertEqual(result.action_anchor_coverage, 1.0)

    def test_unscorable_flow_preserves_zero_action_anchor_coverage(self):
        reference = graph([("A", "action", "a")], [])
        generated = EvalGraph(
            (EvalNode("u", "unsupported_control", semantic_type="Inclusive"), EvalNode("f", "final")),
            (EvalEdge("u", "f"),),
        )
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        result = evaluate_flow("case", "candidate_1", reference, generated, actions)
        self.assertTrue(result.unscorable)
        self.assertEqual(result.action_anchor_coverage, 0.0)

    def test_neutral_merge_is_diagnostic_only(self):
        reference = graph([("A", "action", "a"), ("B", "action", "b")], [("A", "B")])
        generated = graph([("a", "action", "a"), ("m", "merge", None), ("b", "action", "b")], [("a", "m"), ("m", "b")])
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        structure = evaluate_structure("case", "candidate_1", reference, generated, actions)
        candidates, _ = find_redundant_control_nodes("case", "candidate_1", generated, actions)
        self.assertEqual((structure.counts.fp, structure.counts.fn), (0, 0))
        self.assertEqual([(item.node_id, item.confidence) for item in candidates], [("m", "High")])

    def test_generated_adapter_rejects_unknown_node_type(self):
        with self.assertRaisesRegex(ValueError, "Unsupported generated node type"):
            activity_graph_to_eval_graph({"nodes": [{"id": "x", "type": "mystery"}], "edges": []})

    def test_unsupported_control_is_unscorable_not_structure_error(self):
        reference = graph([("A", "action", "a"), ("B", "action", "b")], [("A", "B")])
        generated = EvalGraph(
            (EvalNode("a", "action", "a"), EvalNode("g", "unsupported_control", semantic_type="Inclusive"),
             EvalNode("b", "action", "b")),
            (EvalEdge("a", "g"), EvalEdge("g", "b")),
        )
        actions = evaluate_actions("case", "candidate_1", reference, generated, ExactSimilarity(), 0.9)
        flow = evaluate_flow("case", "candidate_1", reference, generated, actions)
        structure = evaluate_structure("case", "candidate_1", reference, generated, actions)
        self.assertEqual(actions.counts.tp, 2)
        self.assertEqual((flow.counts.fp, flow.counts.fn, flow.coverage), (0, 0, 0.0))
        self.assertEqual((structure.counts.fp, structure.counts.fn, structure.coverage), (0, 0, 0.0))
        self.assertEqual((structure.counts.precision, structure.counts.recall, structure.counts.f1), (0.0, 0.0, 0.0))
        self.assertTrue(flow.unscorable and structure.unscorable)


if __name__ == "__main__":
    unittest.main()
