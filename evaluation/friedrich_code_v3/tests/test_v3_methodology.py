from __future__ import annotations

import unittest

from evaluation.friedrich_v3.core import EvalEdge, EvalGraph, EvalNode
from evaluation.friedrich_semantic.action import SemanticActivityUnit
from evaluation.friedrich_code_v3.alignment import ActionAlignmentTable
from evaluation.friedrich_code_v3.control import (
    match_control_nodes, normalize_generated_control, score_control_relations,
)
from evaluation.friedrich_code_v3.flow import build_flow_inventory, evaluate_flow_v3
from evaluation.friedrich_code_v3.inventory import load_frozen_corpus
from evaluation.friedrich_code_v3.specification_audit import audit_action_anchor_coverage


def graph(nodes, edges):
    return EvalGraph(
        tuple(EvalNode(*node) for node in nodes),
        tuple(EvalEdge(*edge) for edge in edges),
    )


def alignment(**units):
    direct = {unit: frozenset(nodes) for unit, nodes in units.items()}
    inverse: dict[str, set[str]] = {}
    for unit, nodes in direct.items():
        for node in nodes:
            inverse.setdefault(node, set()).add(unit)
    return ActionAlignmentTable((), direct, {k: frozenset(v) for k, v in inverse.items()}, frozenset())


def flow_unit(unit, node):
    return SemanticActivityUnit(unit, unit, (node,), (unit,), "core", "mandatory", None,
                                unit, 0, 1.0, 1.0)


def fact_node(fact_id, kind, anchors=()):
    return {"fact_id": fact_id, "type": kind, "status": "required",
            "anchor_action_ids": list(anchors), "reference_evidence_ids": []}


def fact_relation(fact_id, kind, owner, target=(), incoming=(), guard=None, excluded=()):
    return {"fact_id": fact_id, "type": kind, "status": "required",
            "source_control_fact": owner, "target_action_ids": list(target),
            "incoming_action_ids": list(incoming), "guard_meaning": guard,
            "excluded_action_ids": list(excluded), "reference_evidence_ids": []}


class FrozenIdentityTests(unittest.TestCase):
    def test_corpus_identity_and_10_9_action(self):
        corpus = load_frozen_corpus()
        self.assertEqual(corpus.corpus_sha256,
                         "5f9765bda2ea5d9d9f4a78603207bb0a2ed6532fd0c935149c275595c7d5be8a")
        case = corpus.load_case("10-9")
        self.assertIn("SU-10-9-08", {u["semantic_unit_id"] for u in case.reviewed_action["units"]})
        self.assertIn("SO-10-9-08", {o["occurrence_id"] for o in case.reviewed_action["occurrences"]})

    def test_v3_1_reanchors_9_1_deadline_from_ambiguous_unit(self):
        corpus = load_frozen_corpus()
        findings = audit_action_anchor_coverage(corpus)
        self.assertFalse(any(item.case_id == "9-1" and item.fact_id == "CF-9-1-N04"
                             and item.reason == "researcher_ambiguous" for item in findings))


class FlowMethodTests(unittest.TestCase):
    def setUp(self):
        self.reference = graph(
            [("ra", "action"), ("rg", "decision"), ("rb", "action")],
            [("ra", "rg"), ("rg", "rb")],
        )
        self.inventory = build_flow_inventory(
            self.reference, (flow_unit("A", "ra"), flow_unit("B", "rb")),
            {"control_relations": []},
        )

    def test_intermediate_action_preserves_fixed_precedence(self):
        generated = graph(
            [("a", "action"), ("x", "action"), ("b", "action")],
            [("a", "x"), ("x", "b")],
        )
        result = evaluate_flow_v3(self.inventory, generated, alignment(A=("a",), B=("b",)))
        self.assertEqual(self.inventory.required_precedence, (("A", "B"),))
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (1, 0, 0))

    def test_reversal_is_one_fn_and_one_fp(self):
        generated = graph([("a", "action"), ("b", "action")], [("b", "a")])
        result = evaluate_flow_v3(self.inventory, generated, alignment(A=("a",), B=("b",)))
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (0, 1, 1))

    def test_generated_cycle_violates_fixed_source_direction(self):
        generated = graph([("a", "action"), ("b", "action")], [("a", "b"), ("b", "a")])
        result = evaluate_flow_v3(self.inventory, generated, alignment(A=("a",), B=("b",)))
        self.assertEqual((result.counts.tp, result.counts.fp, result.counts.fn), (0, 1, 1))
        self.assertEqual(result.candidate_unresolved_count, 0)
        self.assertEqual(result.unsupported_cycle_violation_count, 1)

    def test_source_supported_loop_removes_only_forward_extraction_return(self):
        reference = graph(
            [("i", "initial"), ("a", "action"), ("d", "decision"),
             ("b", "action"), ("c", "action")],
            [("i", "a"), ("a", "d"), ("d", "b", "repeat"), ("b", "a"),
             ("d", "c", "done")],
        )
        inventory = build_flow_inventory(
            reference, (flow_unit("A", "a"), flow_unit("B", "b"), flow_unit("C", "c")),
            {"control_relations": [{"type": "loop_recurrence", "status": "required",
                                    "target_action_ids": ["A"]}]},
        )
        self.assertIn(("b", "a"), inventory.removed_recurrence_edges)
        self.assertIn(("A", "B"), inventory.required_precedence)
        self.assertNotIn(("B", "A"), inventory.required_precedence)


class ControlMethodTests(unittest.TestCase):
    def test_decision_node_tp_even_when_guard_relations_wrong(self):
        control = {
            "control_nodes": [fact_node("N", "Decision", ("A",))],
            "control_relations": [
                fact_relation("R1", "decision_branch", "N", ("B",), guard="yes"),
                fact_relation("R2", "decision_branch", "N", ("C",), guard="no"),
            ],
            "permitted_equivalences": [], "no_control": False,
        }
        generated = graph(
            [("a", "action"), ("d", "decision"), ("b", "action"), ("c", "action")],
            [("a", "d"), ("d", "b", "no"), ("d", "c", "yes")],
        )
        align = alignment(A=("a",), B=("b",), C=("c",))
        nodes, assigned = match_control_nodes(control, generated, align)
        relations = score_control_relations(control, generated, align, assigned, {})
        self.assertEqual((nodes.counts.tp, nodes.counts.fn), (1, 0))
        self.assertEqual((relations.counts.tp, relations.counts.fp, relations.counts.fn), (0, 2, 2))

    def test_same_target_different_guard_are_distinct(self):
        control = {
            "control_nodes": [fact_node("N", "Decision", ("A",))],
            "control_relations": [
                fact_relation("R1", "decision_branch", "N", ("B",), guard="simple"),
                fact_relation("R2", "decision_branch", "N", ("B",), guard="complex"),
            ],
            "permitted_equivalences": [], "no_control": False,
        }
        generated = graph(
            [("a", "action"), ("d", "decision"), ("x", "merge"), ("y", "merge"), ("b", "action")],
            [("a", "d"), ("d", "x", "simple"), ("d", "y", "complex"),
             ("x", "b"), ("y", "b")],
        )
        align = alignment(A=("a",), B=("b",))
        nodes, assigned = match_control_nodes(control, generated, align)
        relations = score_control_relations(control, generated, align, assigned, {})
        self.assertEqual(nodes.counts.tp, 1)
        self.assertEqual((relations.counts.tp, relations.counts.fp, relations.counts.fn), (2, 0, 0))

    def test_implicit_merge_allowed_but_implicit_join_not_inferred(self):
        control = {
            "control_nodes": [fact_node("M", "Merge", ("A", "B", "T")),
                              fact_node("J", "Join", ("A", "B", "T"))],
            "control_relations": [
                {**fact_relation("R", "convergence", "M", ("T",), ("A", "B")),
                 "incoming_mode": "alternative_branches"},
            ],
            "permitted_equivalences": [{"rule": "ALLOW_IMPLICIT_MERGE", "scope": "M"}],
            "no_control": False,
        }
        generated = graph(
            [("a", "action"), ("b", "action"), ("t", "action")],
            [("a", "t"), ("b", "t")],
        )
        align = alignment(A=("a",), B=("b",), T=("t",))
        nodes, assigned = match_control_nodes(control, generated, align)
        relations = score_control_relations(control, generated, align, assigned, {})
        self.assertEqual(assigned["M"], "implicit")
        self.assertIsNone(assigned["J"])
        self.assertEqual((nodes.counts.tp, nodes.counts.fn), (1, 1))
        self.assertEqual(relations.counts.tp, 1)

    def test_parallel_serialization_is_control_fn_without_flow_fp(self):
        reference = graph(
            [("ra", "action"), ("rf", "fork"), ("rb", "action"),
             ("rc", "action"), ("rj", "join"), ("rd", "action")],
            [("ra", "rf"), ("rf", "rb"), ("rf", "rc"),
             ("rb", "rj"), ("rc", "rj"), ("rj", "rd")],
        )
        control = {
            "control_nodes": [fact_node("F", "Fork", ("A", "B", "C")),
                              fact_node("J", "Join", ("B", "C", "D"))],
            "control_relations": [
                fact_relation("L1", "parallel_launch", "F", ("B",)),
                fact_relation("L2", "parallel_launch", "F", ("C",)),
                fact_relation("S1", "synchronization", "J", ("D",), ("B",)),
                fact_relation("S2", "synchronization", "J", ("D",), ("C",)),
            ],
            "permitted_equivalences": [], "no_control": False,
        }
        generated = graph(
            [("a", "action"), ("b", "action"), ("c", "action"), ("d", "action")],
            [("a", "b"), ("b", "c"), ("c", "d")],
        )
        align = alignment(A=("a",), B=("b",), C=("c",), D=("d",))
        flow_inventory = build_flow_inventory(reference,
            tuple(flow_unit(unit, node) for unit, node in (("A", "ra"), ("B", "rb"),
                                                           ("C", "rc"), ("D", "rd"))), control)
        flow = evaluate_flow_v3(flow_inventory, generated, align)
        nodes, assigned = match_control_nodes(control, generated, align)
        relations = score_control_relations(control, generated, align, assigned, {})
        self.assertEqual(flow.counts.fp, 0)
        self.assertEqual(nodes.counts.fn, 2)
        self.assertEqual(relations.counts.fn, 4)

    def test_no_control_scope_counts_nonredundant_generated_control_fp(self):
        control = {"control_nodes": [], "control_relations": [],
                   "permitted_equivalences": [], "no_control": True}
        generated = graph(
            [("a", "action"), ("m", "merge"), ("b", "action"),
             ("d", "decision"), ("c", "action")],
            [("a", "m"), ("m", "b"), ("b", "d"), ("d", "c", "yes"),
             ("d", "b", "no")],
        )
        normalized = normalize_generated_control(generated)
        nodes, _ = match_control_nodes(control, normalized, alignment())
        self.assertNotIn("m", normalized.by_id)
        self.assertEqual(nodes.counts.fp, 1)


if __name__ == "__main__":
    unittest.main()
