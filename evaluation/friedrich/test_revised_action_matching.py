from __future__ import annotations

import unittest

from .eval_graph import EvalEdge, EvalGraph, EvalNode
from .revised_action_matching import apply_revised_matching


def _graph(prefix: str) -> EvalGraph:
    return EvalGraph(
        nodes=(
            EvalNode(f"{prefix}a", "action", "anchor"),
            EvalNode(f"{prefix}f", "fork"),
            EvalNode(f"{prefix}1", "action", "notify"),
            EvalNode(f"{prefix}2", "action", "notify"),
        ),
        edges=(
            EvalEdge(f"{prefix}a", f"{prefix}f"),
            EvalEdge(f"{prefix}f", f"{prefix}1"),
            EvalEdge(f"{prefix}f", f"{prefix}2"),
        ),
    )


def _linear_graph(prefix: str, target_ids: tuple[str, ...]) -> EvalGraph:
    nodes = [EvalNode(f"{prefix}a", "action", "anchor")]
    edges = []
    previous = f"{prefix}a"
    for index, target_id in enumerate(target_ids):
        if index:
            routing_id = f"{prefix}d{index}"
            nodes.append(EvalNode(routing_id, "decision"))
            edges.append(EvalEdge(previous, routing_id))
            previous = routing_id
        nodes.append(EvalNode(target_id, "action", "target"))
        edges.append(EvalEdge(previous, target_id))
        previous = target_id
    return EvalGraph(nodes=tuple(nodes), edges=tuple(edges))


class RevisedMatcherTests(unittest.TestCase):
    @staticmethod
    def _row(
        pair_id: str,
        reference_id: str,
        generated_id: str,
        score: float,
        reference_label: str = "target",
        generated_label: str = "target",
    ) -> dict[str, object]:
        return {
            "pair_id": pair_id,
            "case_id": "x",
            "reference_id": reference_id,
            "reference_normalized": reference_label,
            "generated_id": generated_id,
            "generated_normalized": generated_label,
            "semantic_similarity": score,
        }

    @staticmethod
    def _prevent_anchor(row: dict[str, object]) -> dict[str, object]:
        row["reference_representation"] = {
            "operation_resolved": True,
            "canonical_operation": "reference operation",
        }
        row["generated_representation"] = {
            "operation_resolved": True,
            "canonical_operation": "generated operation",
        }
        return row

    def test_isolated_candidate_uses_assignment_not_topology(self) -> None:
        reference = _linear_graph("r", ("r1",))
        generated = _linear_graph("g", ("g1",))
        rows = [
            self._row("anchor", "ra", "ga", 0.99, "anchor", "anchor"),
            self._prevent_anchor(self._row("target", "r1", "g1", 0.80)),
        ]
        evaluated, decisions = apply_revised_matching(
            rows, {"x": reference}, {"x": generated}
        )
        target = next(row for row in evaluated if row["pair_id"] == "target")
        self.assertTrue(target["final_prediction"])
        self.assertEqual(target["selection_stage"], "global_assignment_invariant")
        self.assertEqual(decisions, [])

    def test_reference_side_ambiguity_can_invoke_topology(self) -> None:
        reference = EvalGraph(
            nodes=(EvalNode("ra", "action", "anchor"), EvalNode("r1", "action", "target")),
            edges=(EvalEdge("ra", "r1"),),
        )
        generated = EvalGraph(
            nodes=(
                EvalNode("ga", "action", "anchor"), EvalNode("g1", "action", "target"),
                EvalNode("gd", "decision"), EvalNode("g2", "action", "target"),
            ),
            edges=(EvalEdge("ga", "g1"), EvalEdge("ga", "gd"), EvalEdge("gd", "g2")),
        )
        rows = [
            self._row("anchor", "ra", "ga", 0.99, "anchor", "anchor"),
            self._prevent_anchor(self._row("near", "r1", "g1", 0.70)),
            self._prevent_anchor(self._row("far", "r1", "g2", 0.80)),
        ]
        evaluated, decisions = apply_revised_matching(rows, {"x": reference}, {"x": generated})
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["selected_candidate"], "g1")
        self.assertEqual(decisions[0]["ambiguity_sides"], ["reference"])
        self.assertEqual(decisions[0]["reference_candidate_count"], 2)
        self.assertTrue(next(row for row in evaluated if row["pair_id"] == "near")["final_prediction"])

    def test_generated_side_ambiguity_can_invoke_topology(self) -> None:
        reference = EvalGraph(
            nodes=(
                EvalNode("ra", "action", "anchor"), EvalNode("r1", "action", "target"),
                EvalNode("rd", "decision"), EvalNode("r2", "action", "target"),
            ),
            edges=(EvalEdge("ra", "r1"), EvalEdge("ra", "rd"), EvalEdge("rd", "r2")),
        )
        generated = EvalGraph(
            nodes=(EvalNode("ga", "action", "anchor"), EvalNode("g1", "action", "target")),
            edges=(EvalEdge("ga", "g1"),),
        )
        rows = [
            self._row("anchor", "ra", "ga", 0.99, "anchor", "anchor"),
            self._prevent_anchor(self._row("near", "r1", "g1", 0.70)),
            self._prevent_anchor(self._row("far", "r2", "g1", 0.80)),
        ]
        evaluated, decisions = apply_revised_matching(rows, {"x": reference}, {"x": generated})
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["reference_node"], "r1")
        self.assertEqual(decisions[0]["ambiguity_sides"], ["generated"])
        self.assertEqual(decisions[0]["generated_competitor_count"], 2)
        self.assertTrue(next(row for row in evaluated if row["pair_id"] == "near")["final_prediction"])

    def test_topology_tie_is_not_claimed_as_resolved(self) -> None:
        reference = EvalGraph(
            nodes=(EvalNode("ra", "action", "anchor"), EvalNode("r1", "action", "target")),
            edges=(EvalEdge("ra", "r1"),),
        )
        generated = EvalGraph(
            nodes=(
                EvalNode("ga", "action", "anchor"), EvalNode("g1", "action", "target"),
                EvalNode("g2", "action", "target"),
            ),
            edges=(EvalEdge("ga", "g1"), EvalEdge("ga", "g2")),
        )
        rows = [
            self._row("anchor", "ra", "ga", 0.99, "anchor", "anchor"),
            self._prevent_anchor(self._row("one", "r1", "g1", 0.70)),
            self._prevent_anchor(self._row("two", "r1", "g2", 0.70)),
        ]
        evaluated, decisions = apply_revised_matching(rows, {"x": reference}, {"x": generated})
        self.assertEqual(decisions, [])
        target_rows = [row for row in evaluated if row["reference_id"] == "r1"]
        self.assertFalse(any(row["final_prediction"] for row in target_rows))
        self.assertTrue(all(row["unresolved_ambiguity"] for row in target_rows))

    def test_exact_duplicate_component_remains_unresolved(self) -> None:
        graph = _graph("r")
        generated = _graph("g")
        rows = [
            self._prevent_anchor(self._row(f"p{i}{j}", f"r{i}", f"g{j}", 0.75))
            for i in (1, 2)
            for j in (1, 2)
        ]
        evaluated, decisions = apply_revised_matching(
            rows, {"x": graph}, {"x": generated}
        )
        self.assertEqual(decisions, [])
        self.assertFalse(any(row["final_prediction"] for row in evaluated))
        self.assertTrue(all(row["unresolved_ambiguity"] for row in evaluated))
        self.assertEqual(len({row["unresolved_component_id"] for row in evaluated}), 1)

    def test_numerically_indistinguishable_assignments_remain_unresolved(self) -> None:
        graph = _graph("r")
        generated = _graph("g")
        scores = {
            (1, 1): 0.7500001,
            (1, 2): 0.75,
            (2, 1): 0.75,
            (2, 2): 0.75,
        }
        rows = [
            self._prevent_anchor(
                self._row(f"p{i}{j}", f"r{i}", f"g{j}", scores[(i, j)])
            )
            for i in (1, 2)
            for j in (1, 2)
        ]
        evaluated, _ = apply_revised_matching(
            rows, {"x": graph}, {"x": generated}
        )
        self.assertFalse(any(row["final_prediction"] for row in evaluated))
        self.assertTrue(all(row["unresolved_ambiguity"] for row in evaluated))

    def test_mixed_component_keeps_only_assignment_invariant(self) -> None:
        reference = EvalGraph(
            nodes=tuple(EvalNode(f"r{i}", "action", "target") for i in (1, 2, 3)),
            edges=(),
        )
        generated = EvalGraph(
            nodes=tuple(EvalNode(f"g{i}", "action", "target") for i in (1, 2, 3)),
            edges=(),
        )
        rows = [
            self._prevent_anchor(self._row("fixed", "r1", "g1", 0.95)),
            self._prevent_anchor(self._row("bridge", "r1", "g2", 0.45)),
            self._prevent_anchor(self._row("a", "r2", "g2", 0.75)),
            self._prevent_anchor(self._row("b", "r2", "g3", 0.75)),
            self._prevent_anchor(self._row("c", "r3", "g2", 0.75)),
            self._prevent_anchor(self._row("d", "r3", "g3", 0.75)),
        ]
        evaluated, decisions = apply_revised_matching(
            rows, {"x": reference}, {"x": generated}
        )
        self.assertEqual(decisions, [])
        fixed = next(row for row in evaluated if row["pair_id"] == "fixed")
        self.assertTrue(fixed["final_prediction"])
        self.assertEqual(fixed["selection_stage"], "global_assignment_invariant")
        ambiguous = [row for row in evaluated if row["pair_id"] in {"a", "b", "c", "d"}]
        self.assertFalse(any(row["final_prediction"] for row in ambiguous))
        self.assertTrue(all(row["unresolved_ambiguity"] for row in ambiguous))

    def test_below_threshold_pair_cannot_be_rescued(self) -> None:
        reference = _graph("r")
        generated = _graph("g")
        rows = [
            {
                "pair_id": "anchor", "case_id": "x", "reference_id": "ra",
                "reference_normalized": "anchor", "generated_id": "ga",
                "generated_normalized": "anchor", "semantic_similarity": 0.99,
            },
            {
                "pair_id": "low", "case_id": "x", "reference_id": "r1",
                "reference_normalized": "notify", "generated_id": "g1",
                "generated_normalized": "notify", "semantic_similarity": 0.43,
            },
        ]
        evaluated, decisions = apply_revised_matching(
            rows, {"x": reference}, {"x": generated}
        )
        low = next(row for row in evaluated if row["pair_id"] == "low")
        self.assertFalse(low["candidate_after_compatibility"])
        self.assertFalse(low["final_prediction"])
        self.assertFalse(decisions)

    def test_conflict_pair_cannot_be_rescued(self) -> None:
        reference = _graph("r")
        generated = _graph("g")
        rows = [{
            "pair_id": "conflict", "case_id": "x", "reference_id": "r1",
            "reference_normalized": "create notice", "generated_id": "g1",
            "generated_normalized": "send notice", "semantic_similarity": 0.95,
        }]
        evaluated, _ = apply_revised_matching(rows, {"x": reference}, {"x": generated})
        self.assertFalse(evaluated[0]["operation_compatible"])
        self.assertFalse(evaluated[0]["final_prediction"])


if __name__ == "__main__":
    unittest.main()
