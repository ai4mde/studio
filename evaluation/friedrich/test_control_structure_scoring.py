from __future__ import annotations

import unittest

from .action_scoring import GranularityMismatch, score_action_case
from .control_structure_scoring import (
    KNOWN_UNSUPPORTED_REFERENCE_CASES,
    aggregate_control_structure_scores,
    extract_control_structure_summaries,
    score_control_structure_case,
    unsupported_control_structure_case,
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
            "case_id": "x",
            "pair_id": f"m{index}",
            "reference_id": reference_id,
            "generated_id": generated_id,
            "final_prediction": True,
        }
        for index, (reference_id, generated_id) in enumerate(matches, 1)
    ]
    for index, (reference_ids, generated_ids) in enumerate(unresolved, 1):
        rows.append(
            {
                "case_id": "x",
                "pair_id": f"u{index}",
                "reference_id": reference_ids[0],
                "generated_id": generated_ids[0],
                "final_prediction": False,
                "unresolved_ambiguity": True,
                "unresolved_component_id": f"x:u{index}",
                "unresolved_reference_nodes": list(reference_ids),
                "unresolved_generated_nodes": list(generated_ids),
            }
        )
    return score_action_case(
        "x", reference, generated, rows, granularity_mismatches=granularity
    )


def _exclusive(prefix: str, *, merge: bool = False, branch_count: int = 2) -> EvalGraph:
    action_ids = tuple(chr(ord("A") + index) for index in range(branch_count + 1))
    nodes: list[tuple[str, str]] = [(f"{prefix}{action_id}", "action") for action_id in action_ids]
    nodes.append((f"{prefix}d", "decision"))
    edges: list[tuple[str, str]] = [(f"{prefix}A", f"{prefix}d")]
    for action_id in action_ids[1:]:
        edges.append((f"{prefix}d", f"{prefix}{action_id}"))
    if merge:
        nodes.extend(((f"{prefix}m", "merge"), (f"{prefix}Z", "action")))
        for action_id in action_ids[1:]:
            edges.append((f"{prefix}{action_id}", f"{prefix}m"))
        edges.append((f"{prefix}m", f"{prefix}Z"))
    return _graph(tuple(nodes), tuple(edges))


def _parallel(prefix: str, *, paired: bool = True) -> EvalGraph:
    nodes: list[tuple[str, str]] = [
        (f"{prefix}A", "action"),
        (f"{prefix}f", "fork"),
        (f"{prefix}B", "action"),
        (f"{prefix}C", "action"),
    ]
    edges: list[tuple[str, str]] = [
        (f"{prefix}A", f"{prefix}f"),
        (f"{prefix}f", f"{prefix}B"),
        (f"{prefix}f", f"{prefix}C"),
    ]
    if paired:
        nodes.extend(((f"{prefix}j", "join"), (f"{prefix}D", "action")))
        edges.extend(
            (
                (f"{prefix}B", f"{prefix}j"),
                (f"{prefix}C", f"{prefix}j"),
                (f"{prefix}j", f"{prefix}D"),
            )
        )
    return _graph(tuple(nodes), tuple(edges))


def _loop(prefix: str, exit_action: str = "C") -> EvalGraph:
    return _graph(
        (
            (f"{prefix}A", "action"),
            (f"{prefix}d", "decision"),
            (f"{prefix}B", "action"),
            (f"{prefix}{exit_action}", "action"),
        ),
        (
            (f"{prefix}A", f"{prefix}d"),
            (f"{prefix}d", f"{prefix}B"),
            (f"{prefix}B", f"{prefix}d"),
            (f"{prefix}d", f"{prefix}{exit_action}"),
        ),
    )


class ControlStructureScoringTests(unittest.TestCase):
    def test_correct_exclusive_split_ignores_branch_labels(self) -> None:
        reference = _graph(
            (("A", "action"), ("d", "decision"), ("B", "action"), ("C", "action")),
            (("A", "d"), ("d", "B", "yes"), ("d", "C", "no")),
        )
        generated = _graph(
            (("a", "action"), ("x", "decision"), ("b", "action"), ("c", "action")),
            (("a", "x"), ("x", "b", "approved"), ("x", "c", "rejected")),
        )
        score = score_control_structure_case(
            "x",
            reference,
            generated,
            _action_score(reference, generated, (("A", "a"), ("B", "b"), ("C", "c"))),
        )
        self.assertEqual((score.TP, score.FP, score.FN), (1, 0, 0))
        self.assertEqual(score.f1, 1.0)

    def test_exclusive_and_parallel_do_not_match(self) -> None:
        reference = _exclusive("r")
        generated = _parallel("g", paired=False)
        matches = (("rA", "gA"), ("rB", "gB"), ("rC", "gC"))
        score = score_control_structure_case(
            "x", reference, generated, _action_score(reference, generated, matches)
        )
        self.assertEqual((score.TP, score.FP, score.FN), (0, 1, 1))

    def test_missing_and_extra_exclusive_branches_mismatch_once(self) -> None:
        reference = _graph(
            (
                ("rA", "action"),
                ("rd", "decision"),
                ("rB", "action"),
                ("rC", "action"),
                ("rZ", "final"),
            ),
            (("rA", "rd"), ("rd", "rB"), ("rd", "rC"), ("rB", "rZ"), ("rC", "rZ")),
        )
        missing = _graph(
            (("gA", "action"), ("gd", "decision"), ("gB", "action"), ("gZ", "final")),
            (("gA", "gd"), ("gd", "gB"), ("gB", "gZ")),
        )
        extra_reference = _exclusive("r", branch_count=2)
        extra = _graph(
            (
                ("hA", "action"),
                ("hd", "decision"),
                ("hB", "action"),
                ("hC", "action"),
                ("hD", "action"),
            ),
            (("hA", "hd"), ("hd", "hB"), ("hd", "hC"), ("hd", "hD"), ("hD", "hC")),
        )
        missing_score = score_control_structure_case(
            "x",
            reference,
            missing,
            _action_score(reference, missing, (("rA", "gA"), ("rB", "gB"))),
        )
        extra_matches = (("rA", "hA"), ("rB", "hB"), ("rC", "hC"))
        extra_score = score_control_structure_case(
            "x",
            extra_reference,
            extra,
            _action_score(extra_reference, extra, extra_matches),
        )
        self.assertEqual((missing_score.TP, missing_score.FP, missing_score.FN), (0, 0, 1))
        self.assertEqual((extra_score.TP, extra_score.FP, extra_score.FN), (0, 1, 1))

    def test_branch_grouping_and_cardinality_are_preserved(self) -> None:
        reference = _graph(
            (
                ("A", "action"), ("d", "decision"), ("B", "action"),
                ("C", "action"), ("D", "action"),
            ),
            (("A", "d"), ("d", "B"), ("B", "C"), ("d", "D")),
        )
        generated = _graph(
            (
                ("a", "action"), ("x", "decision"), ("b", "action"),
                ("c", "action"), ("z", "action"),
            ),
            (("a", "x"), ("x", "b"), ("x", "c"), ("x", "z")),
        )
        matches = (("A", "a"), ("B", "b"), ("C", "c"), ("D", "z"))
        score = score_control_structure_case(
            "x", reference, generated, _action_score(reference, generated, matches)
        )
        self.assertEqual((score.TP, score.FP, score.FN), (0, 1, 1))

    def test_explicit_and_implicit_exclusive_merge_are_equivalent(self) -> None:
        reference = _exclusive("r", merge=True)
        generated = _exclusive("g", merge=False)
        matches = (("rA", "gA"), ("rB", "gB"), ("rC", "gC"))
        score = score_control_structure_case(
            "x", reference, generated, _action_score(reference, generated, matches)
        )
        self.assertEqual((score.TP, score.FP, score.FN), (1, 0, 0))
        self.assertEqual(score.explicit_exclusive_merge_count, 1)

    def test_correct_paired_parallel_region(self) -> None:
        reference = _parallel("r")
        generated = _parallel("g")
        matches = tuple((f"r{x}", f"g{x}") for x in "ABCD")
        score = score_control_structure_case(
            "x", reference, generated, _action_score(reference, generated, matches)
        )
        self.assertEqual((score.TP, score.FP, score.FN), (1, 0, 0))
        self.assertEqual(score.reference_summaries[0].synchronization, "paired")

    def test_fork_without_join_is_valid_but_missing_join_mismatches(self) -> None:
        split_reference = _parallel("r", paired=False)
        split_generated = _parallel("g", paired=False)
        split_matches = (("rA", "gA"), ("rB", "gB"), ("rC", "gC"))
        split_score = score_control_structure_case(
            "x",
            split_reference,
            split_generated,
            _action_score(split_reference, split_generated, split_matches),
        )
        paired_reference = _parallel("p", paired=True)
        unpaired_generated = _parallel("u", paired=False)
        mismatch_matches = (("pA", "uA"), ("pB", "uB"), ("pC", "uC"))
        mismatch = score_control_structure_case(
            "x",
            paired_reference,
            unpaired_generated,
            _action_score(paired_reference, unpaired_generated, mismatch_matches),
        )
        self.assertEqual(split_score.TP, 1)
        self.assertEqual((mismatch.TP, mismatch.FP, mismatch.FN), (0, 1, 1))

    def test_orphan_join_is_an_extra_parallel_structure(self) -> None:
        reference = _graph((("A", "action"), ("B", "action"), ("C", "action")), ())
        generated = _graph(
            (
                ("a", "action"), ("b", "action"), ("j", "join"),
                ("c", "action"),
            ),
            (("a", "j"), ("b", "j"), ("j", "c")),
        )
        matches = (("A", "a"), ("B", "b"), ("C", "c"))
        score = score_control_structure_case(
            "x", reference, generated, _action_score(reference, generated, matches)
        )
        self.assertEqual((score.TP, score.FP, score.FN), (0, 1, 0))
        self.assertEqual(score.generated_summaries[0].synchronization, "orphan")

    def test_correct_loop_controller(self) -> None:
        reference = _loop("r")
        generated = _loop("g")
        matches = (("rA", "gA"), ("rB", "gB"), ("rC", "gC"))
        score = score_control_structure_case(
            "x", reference, generated, _action_score(reference, generated, matches)
        )
        self.assertEqual((score.TP, score.FP, score.FN), (1, 0, 0))
        self.assertEqual(score.reference_summaries[0].structure_type, "loop")

    def test_uncontrolled_cycle_is_unscorable_and_does_not_hide_reference_fn(self) -> None:
        reference = _loop("r")
        generated = _graph(
            (("gA", "action"), ("gB", "action"), ("gC", "action")),
            (("gA", "gB"), ("gB", "gB"), ("gB", "gC")),
        )
        matches = (("rA", "gA"), ("rB", "gB"), ("rC", "gC"))
        score = score_control_structure_case(
            "x", reference, generated, _action_score(reference, generated, matches)
        )
        self.assertEqual((score.TP, score.FP, score.FN), (0, 0, 1))
        self.assertEqual(score.unscorable_generated_structure_count, 1)
        self.assertEqual(score.uncontrolled_cycle_count, 1)

    def test_wrong_loop_exit_changes_summary_once(self) -> None:
        reference = _graph(
            (
                ("A", "action"), ("d", "decision"), ("B", "action"),
                ("C", "action"), ("X", "action"),
            ),
            (("A", "d"), ("d", "B"), ("B", "d"), ("d", "C")),
        )
        generated = _graph(
            (
                ("a", "action"), ("q", "decision"), ("b", "action"),
                ("c", "action"), ("x", "action"),
            ),
            (("a", "q"), ("q", "b"), ("b", "q"), ("q", "x")),
        )
        matches = (("A", "a"), ("B", "b"), ("C", "c"), ("X", "x"))
        score = score_control_structure_case(
            "x", reference, generated, _action_score(reference, generated, matches)
        )
        self.assertEqual((score.TP, score.FP, score.FN), (0, 1, 1))

    def test_unmatched_and_unresolved_anchors_are_reported_unscorable(self) -> None:
        reference = _exclusive("r")
        generated = _exclusive("g")
        unmatched_score = score_control_structure_case(
            "x",
            reference,
            generated,
            _action_score(reference, generated, (("rA", "gA"),)),
        )
        unresolved_action = _action_score(
            reference,
            generated,
            (("rA", "gA"), ("rC", "gC")),
            unresolved=((("rB",), ("gB",)),),
        )
        unresolved_score = score_control_structure_case(
            "x", reference, generated, unresolved_action
        )
        self.assertEqual(unmatched_score.unscorable_reference_structure_count, 1)
        self.assertEqual(unmatched_score.unscorable_generated_structure_count, 1)
        self.assertEqual(unmatched_score.structure_coverage, 0.0)
        self.assertGreater(unresolved_score.structures_incident_to_unresolved_actions, 0)

    def test_granularity_is_diagnostic_only(self) -> None:
        reference = _graph(
            (
                ("A", "action"), ("d", "decision"), ("B", "action"),
                ("C", "action"), ("D", "action"),
            ),
            (("A", "d"), ("d", "B"), ("d", "C")),
        )
        generated = _exclusive("g")
        mismatch = GranularityMismatch(
            ("B", "D"), ("gB",), "many_reference_to_one_generated"
        )
        matches = (("A", "gA"), ("B", "gB"), ("C", "gC"))
        score = score_control_structure_case(
            "x",
            reference,
            generated,
            _action_score(reference, generated, matches, granularity=(mismatch,)),
        )
        self.assertEqual((score.TP, score.FP, score.FN), (1, 0, 0))
        self.assertEqual(score.granularity_incident_structure_count, 2)

    def test_duplicate_summaries_use_multiset_accounting(self) -> None:
        reference = _graph(
            (
                ("A", "action"), ("d1", "decision"), ("d2", "decision"),
                ("B", "action"), ("C", "action"),
            ),
            (("A", "d1"), ("A", "d2"), ("d1", "B"), ("d1", "C"), ("d2", "B"), ("d2", "C")),
        )
        generated = _exclusive("g")
        matches = (("A", "gA"), ("B", "gB"), ("C", "gC"))
        score = score_control_structure_case(
            "x", reference, generated, _action_score(reference, generated, matches)
        )
        self.assertEqual(score.reference_structure_count, 2)
        self.assertEqual((score.TP, score.FP, score.FN), (1, 0, 1))

    def test_empty_one_sided_and_dataset_aggregation(self) -> None:
        reference = _graph((("A", "action"),), ())
        generated = _graph((("a", "action"),), ())
        empty = score_control_structure_case(
            "x", reference, generated, _action_score(reference, generated, (("A", "a"),))
        )
        structured_reference = _exclusive("r")
        plain_generated = _graph(
            (("gA", "action"), ("gB", "action"), ("gC", "action")), ()
        )
        one_sided = score_control_structure_case(
            "x",
            structured_reference,
            plain_generated,
            _action_score(
                structured_reference,
                plain_generated,
                (("rA", "gA"), ("rB", "gB"), ("rC", "gC")),
            ),
        )
        unsupported = unsupported_control_structure_case("1-3", "inclusive")
        aggregate = aggregate_control_structure_scores((empty, one_sided, unsupported))
        self.assertEqual((empty.precision, empty.recall, empty.f1), (None, None, None))
        self.assertEqual((one_sided.precision, one_sided.recall, one_sided.f1), (0.0, 0.0, 0.0))
        self.assertEqual(aggregate.unsupported_case_count, 1)
        self.assertEqual(aggregate.micro_FN, 1)

    def test_known_unsupported_cases_are_explicit(self) -> None:
        self.assertEqual(
            set(KNOWN_UNSUPPORTED_REFERENCE_CASES),
            {"1-3", "10-2", "10-3", "1-4", "8-3", "9-2", "7-1"},
        )
        unsupported = unsupported_control_structure_case(
            "7-1", KNOWN_UNSUPPORTED_REFERENCE_CASES["7-1"]
        )
        self.assertTrue(unsupported.unsupported)
        self.assertIsNone(unsupported.structure_coverage)
        graph = _graph((), ())
        automatic = score_control_structure_case(
            "1-3", graph, graph, _action_score(graph, graph, ())
        )
        self.assertTrue(automatic.unsupported)
        self.assertEqual(
            automatic.unsupported_reason,
            KNOWN_UNSUPPORTED_REFERENCE_CASES["1-3"],
        )


if __name__ == "__main__":
    unittest.main()
