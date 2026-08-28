from __future__ import annotations

import unittest

from evaluation.friedrich_v2.action import evaluate_actions
from evaluation.friedrich_v2.adapters import activity_graph_to_eval_graph
from evaluation.friedrich_v2.core import EvalEdge, EvalGraph, EvalNode
from evaluation.friedrich_v2.diagnostics import find_redundant_control_nodes
from evaluation.friedrich_v2.flow import evaluate_flow
from evaluation.friedrich_v2.structure import evaluate_structure


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
        self.assertEqual({fact[0] for fact in result.reference_facts}, {"mode", "branch", "exclusive_convergence"})

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
        self.assertTrue(flow.unscorable and structure.unscorable)


if __name__ == "__main__":
    unittest.main()
