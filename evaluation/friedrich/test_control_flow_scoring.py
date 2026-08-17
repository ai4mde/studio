from __future__ import annotations

import unittest

from .action_scoring import GranularityMismatch, score_action_case
from .control_flow_scoring import (
    aggregate_control_flow_scores,
    project_action_flows,
    score_control_flow_case,
)
from .eval_graph import EvalEdge, EvalGraph, EvalNode


def _graph(
    nodes: tuple[tuple[str, str], ...],
    edges: tuple[tuple[str, str] | tuple[str, str, str], ...],
) -> EvalGraph:
    return EvalGraph(
        nodes=tuple(
            EvalNode(node_id, node_type, node_id if node_type == "action" else None)  # type: ignore[arg-type]
            for node_id, node_type in nodes
        ),
        edges=tuple(
            EvalEdge(edge[0], edge[1], edge[2] if len(edge) == 3 else None)
            for edge in edges
        ),
    )


def _action_score(
    reference: EvalGraph,
    generated: EvalGraph,
    matches: tuple[tuple[str, str], ...],
    *,
    unresolved: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (),
    granularity: tuple[GranularityMismatch, ...] = (),
):
    rows: list[dict[str, object]] = [
        {
            "case_id": "x", "pair_id": f"m{index}",
            "reference_id": reference_id, "generated_id": generated_id,
            "final_prediction": True,
        }
        for index, (reference_id, generated_id) in enumerate(matches, 1)
    ]
    for index, (reference_ids, generated_ids) in enumerate(unresolved, 1):
        rows.append(
            {
                "case_id": "x", "pair_id": f"u{index}",
                "reference_id": reference_ids[0], "generated_id": generated_ids[0],
                "final_prediction": False, "unresolved_ambiguity": True,
                "unresolved_component_id": f"x:u{index}",
                "unresolved_reference_nodes": list(reference_ids),
                "unresolved_generated_nodes": list(generated_ids),
            }
        )
    return score_action_case(
        "x", reference, generated, rows, granularity_mismatches=granularity
    )


class ControlFlowScoringTests(unittest.TestCase):
    def test_perfect_sequence(self) -> None:
        reference = _graph(
            (("A", "action"), ("B", "action"), ("C", "action")),
            (("A", "B"), ("B", "C")),
        )
        generated = _graph(
            (("a", "action"), ("b", "action"), ("c", "action")),
            (("a", "b"), ("b", "c")),
        )
        score = score_control_flow_case(
            "x", reference, generated,
            _action_score(reference, generated, (("A", "a"), ("B", "b"), ("C", "c"))),
        )
        self.assertEqual((score.TP, score.FP, score.FN), (2, 0, 0))
        self.assertEqual((score.precision, score.recall, score.f1), (1.0, 1.0, 1.0))

    def test_extra_and_missing_relations(self) -> None:
        reference = _graph(
            (("A", "action"), ("B", "action"), ("C", "action")),
            (("A", "B"), ("B", "C")),
        )
        extra = _graph(
            (("a", "action"), ("b", "action"), ("c", "action")),
            (("a", "b"), ("b", "c"), ("a", "c")),
        )
        missing = _graph(
            (("a", "action"), ("b", "action"), ("c", "action")),
            (("a", "b"),),
        )
        matches = (("A", "a"), ("B", "b"), ("C", "c"))
        extra_score = score_control_flow_case(
            "x", reference, extra, _action_score(reference, extra, matches)
        )
        missing_score = score_control_flow_case(
            "x", reference, missing, _action_score(reference, missing, matches)
        )
        self.assertEqual((extra_score.TP, extra_score.FP, extra_score.FN), (2, 1, 0))
        self.assertEqual((missing_score.TP, missing_score.FP, missing_score.FN), (1, 0, 1))

    def test_decision_projection_ignores_branch_labels(self) -> None:
        graph = _graph(
            (("A", "action"), ("d", "decision"), ("B", "action"), ("C", "action")),
            (("A", "d"), ("d", "B", "yes"), ("d", "C", "no")),
        )
        differently_labeled = _graph(
            (("a", "action"), ("d2", "decision"), ("b", "action"), ("c", "action")),
            (("a", "d2"), ("d2", "b", "approved"), ("d2", "c", "rejected")),
        )
        self.assertEqual(project_action_flows(graph), frozenset({("A", "B"), ("A", "C")}))
        score = score_control_flow_case(
            "x", graph, differently_labeled,
            _action_score(graph, differently_labeled, (("A", "a"), ("B", "b"), ("C", "c"))),
        )
        self.assertEqual(score.f1, 1.0)

    def test_explicit_merge_equals_direct_reconvergence(self) -> None:
        reference = _graph(
            (("B", "action"), ("C", "action"), ("m", "merge"), ("D", "action")),
            (("B", "m"), ("C", "m"), ("m", "D")),
        )
        generated = _graph(
            (("b", "action"), ("c", "action"), ("d", "action")),
            (("b", "d"), ("c", "d")),
        )
        score = score_control_flow_case(
            "x", reference, generated,
            _action_score(reference, generated, (("B", "b"), ("C", "c"), ("D", "d"))),
        )
        self.assertEqual((score.TP, score.FP, score.FN), (2, 0, 0))

    def test_loop_back_edge_and_self_loop_are_preserved(self) -> None:
        loop = _graph(
            (("A", "action"), ("B", "action"), ("d", "decision")),
            (("A", "B"), ("B", "d"), ("d", "A")),
        )
        self_loop = _graph(
            (("A", "action"), ("d", "decision")),
            (("A", "d"), ("d", "A")),
        )
        self.assertEqual(project_action_flows(loop), frozenset({("A", "B"), ("B", "A")}))
        self.assertEqual(project_action_flows(self_loop), frozenset({("A", "A")}))

    def test_missing_loop_back_edge_is_fn(self) -> None:
        reference = _graph(
            (("A", "action"), ("B", "action"), ("d", "decision")),
            (("A", "B"), ("B", "d"), ("d", "A")),
        )
        generated = _graph(
            (("a", "action"), ("b", "action")), (("a", "b"),)
        )
        score = score_control_flow_case(
            "x", reference, generated,
            _action_score(reference, generated, (("A", "a"), ("B", "b"))),
        )
        self.assertEqual((score.TP, score.FP, score.FN), (1, 0, 1))

    def test_parallel_and_exclusive_structures_can_be_flow_equivalent(self) -> None:
        parallel = _graph(
            (
                ("A", "action"), ("f", "fork"), ("B", "action"),
                ("C", "action"), ("j", "join"), ("D", "action"),
            ),
            (("A", "f"), ("f", "B"), ("f", "C"), ("B", "j"), ("C", "j"), ("j", "D")),
        )
        exclusive = _graph(
            (
                ("a", "action"), ("d", "decision"), ("b", "action"),
                ("c", "action"), ("m", "merge"), ("z", "action"),
            ),
            (("a", "d"), ("d", "b"), ("d", "c"), ("b", "m"), ("c", "m"), ("m", "z")),
        )
        expected = frozenset({("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")})
        self.assertEqual(project_action_flows(parallel), expected)
        score = score_control_flow_case(
            "x", parallel, exclusive,
            _action_score(parallel, exclusive, (("A", "a"), ("B", "b"), ("C", "c"), ("D", "z"))),
        )
        self.assertEqual(score.f1, 1.0)

    def test_unmatched_intermediate_action_is_not_bridged(self) -> None:
        reference = _graph(
            (("A", "action"), ("B", "action"), ("C", "action")),
            (("A", "B"), ("B", "C")),
        )
        generated = _graph(
            (("a", "action"), ("c", "action")), (("a", "c"),)
        )
        score = score_control_flow_case(
            "x", reference, generated,
            _action_score(reference, generated, (("A", "a"), ("C", "c"))),
        )
        self.assertEqual((score.TP, score.FP, score.FN), (0, 1, 2))
        self.assertEqual(len(score.flows_incident_to_unmatched_reference_actions), 2)

    def test_unresolved_incident_flows_receive_no_extra_penalty(self) -> None:
        reference = _graph(
            (("A", "action"), ("B", "action"), ("C", "action")),
            (("A", "B"), ("B", "C")),
        )
        generated = _graph(
            (("a", "action"), ("x", "action"), ("c", "action")),
            (("a", "x"), ("x", "c")),
        )
        action_score = _action_score(
            reference, generated, (("A", "a"), ("C", "c")),
            unresolved=((("B",), ("x",)),),
        )
        score = score_control_flow_case("x", reference, generated, action_score)
        self.assertEqual((score.TP, score.FP, score.FN), (0, 2, 2))
        self.assertEqual(len(score.flows_incident_to_unresolved_reference_actions), 2)
        self.assertEqual(len(score.flows_incident_to_unresolved_generated_actions), 2)

    def test_granularity_is_diagnostic_only(self) -> None:
        reference = _graph(
            (("A", "action"), ("B", "action"), ("C", "action"), ("D", "action")),
            (("A", "B"), ("B", "C")),
        )
        generated = _graph(
            (("a", "action"), ("x", "action"), ("c", "action")),
            (("a", "x"), ("x", "c")),
        )
        mismatch = GranularityMismatch(
            ("B", "D"), ("x",), "many_reference_to_one_generated"
        )
        score = score_control_flow_case(
            "x", reference, generated,
            _action_score(
                reference, generated, (("A", "a"), ("B", "x"), ("C", "c")),
                granularity=(mismatch,),
            ),
        )
        self.assertEqual((score.TP, score.FP, score.FN), (2, 0, 0))
        self.assertEqual(score.granularity_incident_flow_count, 4)

    def test_empty_and_one_sided_flow_sets(self) -> None:
        reference = _graph((("A", "action"),), ())
        generated = _graph((("a", "action"),), ())
        empty = score_control_flow_case(
            "x", reference, generated,
            _action_score(reference, generated, (("A", "a"),)),
        )
        generated_with_flow = _graph(
            (("a", "action"), ("b", "action")), (("a", "b"),)
        )
        one_sided = score_control_flow_case(
            "x", reference, generated_with_flow,
            _action_score(reference, generated_with_flow, (("A", "a"),)),
        )
        self.assertEqual((empty.precision, empty.recall, empty.f1), (None, None, None))
        self.assertEqual((one_sided.precision, one_sided.recall, one_sided.f1), (0.0, 0.0, 0.0))

    def test_routing_cycle_terminates(self) -> None:
        graph = _graph(
            (("A", "action"), ("d", "decision"), ("m", "merge")),
            (("A", "d"), ("d", "m"), ("m", "d")),
        )
        self.assertEqual(project_action_flows(graph), frozenset())

    def test_initial_and_final_nodes_are_boundaries(self) -> None:
        graph = _graph(
            (
                ("A", "action"),
                ("end", "final"),
                ("start", "initial"),
                ("B", "action"),
            ),
            (("A", "end"), ("end", "start"), ("start", "B")),
        )
        self.assertEqual(project_action_flows(graph), frozenset())

    def test_unsupported_node_type_fails_explicitly(self) -> None:
        unsupported = object.__new__(EvalNode)
        object.__setattr__(unsupported, "id", "object")
        object.__setattr__(unsupported, "type", "object")
        object.__setattr__(unsupported, "label", None)
        graph = EvalGraph(
            nodes=(EvalNode("A", "action", "A"), unsupported),
            edges=(EvalEdge("A", "object"),),
        )
        with self.assertRaisesRegex(ValueError, "Unsupported EvalGraph node types"):
            project_action_flows(graph)

    def test_micro_and_macro_aggregation(self) -> None:
        reference = _graph(
            (("A", "action"), ("B", "action")), (("A", "B"),)
        )
        generated = _graph(
            (("a", "action"), ("b", "action")), (("a", "b"),)
        )
        perfect = score_control_flow_case(
            "x", reference, generated,
            _action_score(reference, generated, (("A", "a"), ("B", "b"))),
        )
        missing = score_control_flow_case(
            "x", reference, _graph((("a", "action"), ("b", "action")), ()),
            _action_score(reference, _graph((("a", "action"), ("b", "action")), ()), (("A", "a"), ("B", "b"))),
        )
        empty_reference = _graph((("A", "action"),), ())
        empty_generated = _graph((("a", "action"),), ())
        empty = score_control_flow_case(
            "x", empty_reference, empty_generated,
            _action_score(empty_reference, empty_generated, (("A", "a"),)),
        )
        aggregate = aggregate_control_flow_scores((perfect, missing, empty))
        self.assertEqual((aggregate.micro_TP, aggregate.micro_FP, aggregate.micro_FN), (1, 0, 1))
        self.assertAlmostEqual(aggregate.micro_f1 or 0.0, 2 / 3)
        self.assertEqual(aggregate.macro_f1, 0.5)
        self.assertEqual(aggregate.empty_flow_case_count, 1)


if __name__ == "__main__":
    unittest.main()
