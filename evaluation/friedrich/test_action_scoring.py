from __future__ import annotations

import unittest

from .action_scoring import (
    GranularityMismatch,
    aggregate_action_scores,
    score_action_case,
)
from .eval_graph import EvalGraph, EvalNode


def _graph(prefix: str, labels: tuple[str | None, ...]) -> EvalGraph:
    return EvalGraph(
        nodes=tuple(
            EvalNode(id=f"{prefix}{index}", type="action", label=label)
            for index, label in enumerate(labels, 1)
        ),
        edges=(),
    )


def _row(
    pair_id: str,
    reference_id: str,
    generated_id: str,
    *,
    final: bool = True,
    **extra: object,
) -> dict[str, object]:
    return {
        "case_id": "x",
        "pair_id": pair_id,
        "reference_id": reference_id,
        "generated_id": generated_id,
        "final_prediction": final,
        **extra,
    }


class ActionScoringTests(unittest.TestCase):
    def test_perfect_match(self) -> None:
        score = score_action_case(
            "x",
            _graph("r", ("one", "two")),
            _graph("g", ("one", "two")),
            [_row("p1", "r1", "g1"), _row("p2", "r2", "g2")],
        )
        self.assertEqual((score.TP, score.FP, score.FN), (2, 0, 0))
        self.assertEqual((score.precision, score.recall, score.f1), (1.0, 1.0, 1.0))

    def test_extra_generated_action(self) -> None:
        score = score_action_case(
            "x", _graph("r", ("one",)), _graph("g", ("one", "extra")),
            [_row("p1", "r1", "g1")],
        )
        self.assertEqual((score.TP, score.FP, score.FN), (1, 1, 0))

    def test_missing_reference_action(self) -> None:
        score = score_action_case(
            "x", _graph("r", ("one", "missing")), _graph("g", ("one",)),
            [_row("p1", "r1", "g1")],
        )
        self.assertEqual((score.TP, score.FP, score.FN), (1, 0, 1))

    def test_unresolved_component_counts_nodes_not_candidate_edges(self) -> None:
        unresolved = {
            "final": False,
            "unresolved_ambiguity": True,
            "unresolved_component_id": "x:u1",
            "unresolved_reference_nodes": ["r1", "r2"],
            "unresolved_generated_nodes": ["g1", "g2"],
        }
        rows = [
            _row(f"p{i}{j}", f"r{i}", f"g{j}", **unresolved)
            for i in (1, 2) for j in (1, 2)
        ]
        score = score_action_case(
            "x", _graph("r", ("same", "same")), _graph("g", ("same", "same")), rows
        )
        self.assertEqual((score.TP, score.FP, score.FN), (0, 2, 2))
        self.assertEqual(score.unresolved_component_count, 1)
        self.assertEqual(score.unresolved_reference_node_count, 2)
        self.assertEqual(score.unresolved_generated_node_count, 2)

    def test_many_reference_to_one_generated_with_match(self) -> None:
        mismatch = GranularityMismatch(
            ("r1", "r2"), ("g1",), "many_reference_to_one_generated"
        )
        score = score_action_case(
            "x", _graph("r", ("plan", "conduct")), _graph("g", ("plan and conduct",)),
            [_row("p1", "r1", "g1")], granularity_mismatches=[mismatch],
        )
        self.assertEqual((score.TP, score.FP, score.FN), (1, 0, 1))
        self.assertEqual(score.granularity_mismatch_count, 1)

    def test_many_reference_to_one_generated_without_match(self) -> None:
        mismatch = GranularityMismatch(
            ("r1", "r2"), ("g1",), "many_reference_to_one_generated"
        )
        score = score_action_case(
            "x", _graph("r", ("plan", "conduct")), _graph("g", ("plan and conduct",)),
            [], granularity_mismatches=[mismatch],
        )
        self.assertEqual((score.TP, score.FP, score.FN), (0, 1, 2))

    def test_one_reference_to_many_generated(self) -> None:
        mismatch = GranularityMismatch(
            ("r1",), ("g1", "g2"), "one_reference_to_many_generated"
        )
        with_match = score_action_case(
            "x", _graph("r", ("plan and conduct",)), _graph("g", ("plan", "conduct")),
            [_row("p1", "r1", "g1")], granularity_mismatches=[mismatch],
        )
        without_match = score_action_case(
            "x", _graph("r", ("plan and conduct",)), _graph("g", ("plan", "conduct")),
            [], granularity_mismatches=[mismatch],
        )
        self.assertEqual((with_match.TP, with_match.FP, with_match.FN), (1, 1, 0))
        self.assertEqual((without_match.TP, without_match.FP, without_match.FN), (0, 2, 1))

    def test_invalid_granularity_direction_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported granularity direction"):
            GranularityMismatch(
                ("r1", "r2"),
                ("g1",),
                "unsupported",  # type: ignore[arg-type]
            )

    def test_empty_and_one_sided_cases(self) -> None:
        empty = score_action_case("x", _graph("r", ()), _graph("g", ()), [])
        reference_only = score_action_case(
            "x", _graph("r", ("one",)), _graph("g", ()), []
        )
        generated_only = score_action_case(
            "x", _graph("r", ()), _graph("g", ("one",)), []
        )
        self.assertTrue(empty.empty)
        self.assertEqual((empty.precision, empty.recall, empty.f1), (None, None, None))
        self.assertEqual(
            (reference_only.precision, reference_only.recall, reference_only.f1),
            (0.0, 0.0, 0.0),
        )
        self.assertEqual(
            (generated_only.precision, generated_only.recall, generated_only.f1),
            (0.0, 0.0, 0.0),
        )

    def test_unlabeled_action_is_not_removed(self) -> None:
        score = score_action_case(
            "x", _graph("r", (None,)), _graph("g", ("generated",)), []
        )
        self.assertEqual(score.reference_action_count, 1)
        self.assertEqual(score.unlabeled_action_count, 1)
        self.assertEqual((score.TP, score.FP, score.FN), (0, 1, 1))

    def test_non_action_nodes_are_excluded(self) -> None:
        reference = EvalGraph(
            nodes=(EvalNode("r1", "action", "one"), EvalNode("rd", "decision", "branch")),
            edges=(),
        )
        generated = EvalGraph(
            nodes=(EvalNode("g1", "action", "one"), EvalNode("gf", "final", "done")),
            edges=(),
        )
        score = score_action_case("x", reference, generated, [_row("p1", "r1", "g1")])
        self.assertEqual((score.reference_action_count, score.generated_action_count), (1, 1))

    def test_rejects_non_one_to_one_matches(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-one-to-one reference"):
            score_action_case(
                "x", _graph("r", ("one",)), _graph("g", ("one", "two")),
                [_row("p1", "r1", "g1"), _row("p2", "r1", "g2")],
            )

    def test_micro_and_macro_aggregation(self) -> None:
        perfect = score_action_case(
            "x", _graph("r", ("one",)), _graph("g", ("one",)),
            [_row("p1", "r1", "g1")],
        )
        missing = score_action_case(
            "x", _graph("r", ("one",)), _graph("g", ()), []
        )
        empty = score_action_case("x", _graph("r", ()), _graph("g", ()), [])
        aggregate = aggregate_action_scores([perfect, missing, empty])
        self.assertEqual((aggregate.micro_TP, aggregate.micro_FP, aggregate.micro_FN), (1, 0, 1))
        self.assertEqual(aggregate.micro_precision, 1.0)
        self.assertEqual(aggregate.micro_recall, 0.5)
        self.assertAlmostEqual(aggregate.micro_f1 or 0.0, 2 / 3)
        self.assertEqual(aggregate.macro_f1, 0.5)
        self.assertEqual(aggregate.empty_case_count, 1)
        self.assertEqual(aggregate.defined_macro_case_count, 2)


if __name__ == "__main__":
    unittest.main()
