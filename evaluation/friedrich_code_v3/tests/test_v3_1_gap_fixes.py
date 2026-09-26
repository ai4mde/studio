"""Synthetic evidence tests for frozen V3.1 contract completion."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
import unittest

from evaluation.friedrich_v3.core import EvalEdge, EvalGraph, EvalNode
from evaluation.friedrich_code_v3.alignment import ActionAlignmentTable, AlignmentEntry
from evaluation.friedrich_code_v3.anchor_evidence import (
    _occurrence_scope_matches, build_control_anchor_evidence,
)
from evaluation.friedrich_code_v3.control import match_control_nodes, score_control_relations
from evaluation.friedrich_code_v3.flow import FlowInventoryV3, evaluate_flow_v3


def graph(nodes, edges):
    return EvalGraph(tuple(EvalNode(*node) for node in nodes),
                     tuple(EvalEdge(*edge) for edge in edges))


def aligned(mapping, *, ambiguous=(), candidates=None, split=()):
    entries = tuple(AlignmentEntry(f"m:{unit}", "one_to_many" if unit in split else "one_to_one",
                                   (unit,), (unit,), tuple(ids), {}, ())
                    for unit, ids in mapping.items())
    return ActionAlignmentTable(entries, {unit: frozenset(ids) for unit, ids in mapping.items()},
                                {}, frozenset(ambiguous), candidates or {})


def control(nodes, relations):
    return {"control_nodes": nodes, "control_relations": relations,
            "permitted_equivalences": [], "no_control": False, "unresolved_facts": []}


def node(fact_id="N", anchors=(), evidence=(), kind="Decision"):
    return {"fact_id": fact_id, "type": kind, "status": "required",
            "anchor_action_ids": list(anchors), "control_anchor_evidence": list(evidence)}


def relation(fact_id, kind, owner="N", target=(), incoming=(), guard=None, evidence=()):
    return {"fact_id": fact_id, "type": kind, "status": "required",
            "source_control_fact": owner, "target_action_ids": list(target),
            "incoming_action_ids": list(incoming), "guard_meaning": guard,
            "reference_evidence_ids": [], "control_anchor_evidence": list(evidence)}


class ControlEvidenceCompletionTests(unittest.TestCase):
    def test_compound_risk_guards_require_each_source_predicate(self):
        data = control([node()], [
            relation("SMALL_LOW", "decision_branch", target=("APPROVE",),
                     guard="small and low risk"),
            relation("HIGH", "decision_branch", target=("DENY",), guard="high risk"),
        ])
        candidate_nodes = [("d", "decision", "determine outcome based on risk and amount?"),
                           ("a", "action", "approve loan"),
                           ("r", "action", "deny loan")]
        anchor = aligned({"APPROVE": ("a",), "DENY": ("r",)})
        generic = graph(candidate_nodes, [("d", "a", "approved"),
                                          ("d", "r", "denied")])
        result = score_control_relations(data, generic, anchor, {"N": "d"}, {})
        self.assertEqual({fact.fact_id: fact.status for fact in result.facts},
                         {"SMALL_LOW": "FN+FP", "HIGH": "FN+FP"})
        explicit = graph(candidate_nodes, [("d", "a", "small and low risk approved"),
                                           ("d", "r", "high risk denied")])
        result = score_control_relations(data, explicit, anchor, {"N": "d"}, {})
        self.assertEqual({fact.fact_id: fact.status for fact in result.facts},
                         {"SMALL_LOW": "TP", "HIGH": "TP"})

    def test_incomplete_return_does_not_turn_approval_decision_into_loop(self):
        data = control([node(anchors=("SUBMIT", "CORRECT", "POST"))], [
            relation("REPEAT", "loop_recurrence", target=("CORRECT", "SUBMIT"),
                     guard="rejected and correction requested"),
            relation("EXIT", "loop_exit", target=("POST",), guard="approved"),
        ])
        candidate = graph(
            [("s", "action", "submit"), ("d", "decision", "repeat correction?"),
             ("c", "action", "correct"), ("a", "decision", "approve?"),
             ("p", "action", "post"), ("x", "final")],
            [("s", "d"), ("d", "c", "retry"), ("d", "p", "approved"),
             ("c", "a"), ("a", "p", "approved"), ("a", "x", "rejected")],
        )
        anchor = aligned({"SUBMIT": ("s",), "POST": ("p",)})
        nodes, _ = match_control_nodes(data, candidate, anchor)
        self.assertEqual(nodes.facts[0].status, "FN")

    def test_approval_owner_excludes_temporal_deadline_gateway(self):
        data = control([node(anchors=("APPROVE", "REJECT"))], [
            relation("YES", "decision_branch", target=("APPROVE",), guard="approved"),
            relation("NO", "decision_branch", target=("REJECT",), guard="rejected"),
        ])
        candidate = graph(
            [("d", "decision", "approve or reject?"),
             ("t", "decision", "handle timeouts and deadlines?"),
             ("a", "action", "reimburse"), ("r", "action", "reject"),
             ("p", "action", "send progress email")],
            [("d", "r", "rejected"), ("d", "t", "approved"),
             ("t", "a", "completed_in_time"),
             ("t", "p", "approval_in_progress")],
        )
        anchor = aligned({"APPROVE": ("a",), "REJECT": ("r",)})
        nodes, assigned = match_control_nodes(data, candidate, anchor)
        self.assertEqual(assigned["N"], "d")
        self.assertEqual(nodes.assignment_alternatives["N"], frozenset({"d"}))

    def test_distinct_deadline_nodes_cannot_share_one_gateway(self):
        seven = node("SEVEN", anchors=("PROGRESS",))
        seven["purpose"] = "Send progress email after seven days"
        thirty = node("THIRTY", anchors=("CANCEL",))
        thirty["purpose"] = "Cancel request after thirty days"
        data = control([seven, thirty], [
            relation("R7", "decision_branch", "SEVEN", target=("PROGRESS",),
                     guard="unfinished at day 7"),
            relation("R30", "decision_branch", "THIRTY", target=("CANCEL",),
                     guard="unfinished at day 30"),
        ])
        candidate = graph(
            [("d", "decision", "7-day and 30-day deadlines?"),
             ("p", "action", "send progress email"),
             ("c", "action", "cancel request")],
            [("d", "p", "unfinished at day 7"),
             ("d", "c", "unfinished at day 30")],
        )
        nodes, assigned = match_control_nodes(
            data, candidate, aligned({"PROGRESS": ("p",), "CANCEL": ("c",)}))
        self.assertLessEqual(nodes.counts.tp, 1)
        self.assertEqual(nodes.counts.tp + nodes.counts.fn +
                         nodes.candidate_abstention_count, 2)
        self.assertLessEqual(sum(value == "d" for value in assigned.values()), 1)

    def test_separate_seven_and_thirty_day_gateways_keep_distinct_roles(self):
        seven = node("SEVEN", anchors=("PROGRESS",))
        seven["purpose"] = "Send progress email after seven days"
        thirty = node("THIRTY", anchors=("CANCEL",))
        thirty["purpose"] = "Cancel request after thirty days"
        data = control([seven, thirty], [
            relation("R7", "decision_branch", "SEVEN", target=("PROGRESS",),
                     guard="unfinished at day 7"),
            relation("R30", "decision_branch", "THIRTY", target=("CANCEL",),
                     guard="unfinished at day 30"),
        ])
        candidate = graph(
            [("d7", "decision", "unfinished at day 7?"),
             ("d30", "decision", "unfinished at day 30?"),
             ("p", "action", "send progress email"),
             ("c", "action", "cancel request"), ("x", "final")],
            [("d7", "p", "unfinished at day 7"), ("d7", "d30", "continue"),
             ("d30", "c", "unfinished at day 30"), ("d30", "x", "finished")],
        )
        anchor = aligned({"PROGRESS": ("p",), "CANCEL": ("c",)})
        nodes, assigned = match_control_nodes(data, candidate, anchor)
        self.assertEqual(assigned, {"SEVEN": "d7", "THIRTY": "d30"})
        self.assertEqual(nodes.counts.tp, 2)

    def test_approval_in_progress_is_not_completed_approval(self):
        data = control([node()], [relation("R", "decision_branch", target=("A",),
                                        guard="approved")])
        candidate = graph([("d", "decision", "approval state?"),
                           ("a", "action", "reimburse"), ("x", "final")],
                          [("d", "a", "approval_in_progress"),
                           ("d", "x", "rejected")])
        result = score_control_relations(data, candidate, aligned({"A": ("a",)}),
                                         {"N": "d"}, {})
        self.assertEqual(result.facts[0].status, "FN+FP")

    def test_frozen_guard_inflections_preserve_matching_branch_outcome(self):
        pairs = (("reject", "rejected", "reject order"),
                 ("reject", "rejects", "reject order"),
                 ("oppose", "opposed", "oppose dismissal"),
                 ("approve", "approved", "approve request"),
                 ("fail", "failure", "report failure"),
                 ("confirm", "confirmation", "confirm request"))
        for source_guard, generated_guard, outcome in pairs:
            with self.subTest(source_guard=source_guard, generated_guard=generated_guard):
                data = control([node()], [relation("R", "decision_branch", target=("A",),
                                                guard=source_guard)])
                candidate = graph([("d", "decision"), ("a", "action", outcome),
                                   ("x", "final")],
                                  [("d", "a", generated_guard), ("d", "x", "opposite")])
                scored = score_control_relations(data, candidate,
                                                 aligned({"A": ("a",)}), {"N": "d"}, {})
                self.assertEqual(scored.facts[0].status, "TP")

    def test_guard_normalization_preserves_polarity_time_and_comparison(self):
        contradictory = (("approved", "not approved"),
                         ("rejected", "accepted"),
                         ("before deadline", "after deadline"),
                         ("amount < 200", "amount >= 200"),
                         ("approval required", "approval optional"),
                         ("success", "failure"))
        for source_guard, generated_guard in contradictory:
            with self.subTest(source_guard=source_guard, generated_guard=generated_guard):
                data = control([node()], [relation("R", "decision_branch", target=("A",),
                                                guard=source_guard)])
                candidate = graph([("d", "decision"), ("a", "action"), ("x", "final")],
                                  [("d", "a", generated_guard), ("d", "x", source_guard)])
                scored = score_control_relations(data, candidate,
                                                 aligned({"A": ("a",)}), {"N": "d"}, {})
                self.assertEqual(scored.facts[0].status, "FN+FP")

    def test_inclusive_threshold_needs_correct_boundary_or_binary_complement(self):
        data = control([node()], [relation("R", "decision_branch", target=("A",),
                                        guard="amount at least 200")])
        nodes = [("d", "decision", "amount under 200 for automatic approval or supervisor?"),
                 ("a", "action", "send to supervisor"), ("x", "action", "approve automatically")]
        anchor = aligned({"A": ("a",)})
        complementary = graph(nodes, [("d", "a", "needs supervisor"),
                                      ("d", "x", "auto approved")])
        self.assertEqual(score_control_relations(data, complementary, anchor,
                                                 {"N": "d"}, {}).facts[0].status, "TP")
        exclusive = graph([("d", "decision", "amount over 200 for supervisor?"),
                           nodes[1], nodes[2]],
                          [("d", "a", "needs supervisor"), ("d", "x", "auto approved")])
        self.assertEqual(score_control_relations(data, exclusive, anchor,
                                                 {"N": "d"}, {}).facts[0].status, "FN+FP")

    def test_matching_guard_on_wrong_branch_target_cannot_be_tp(self):
        data = control([node()], [relation("R", "decision_branch", target=("A",), guard="reject")])
        candidate = graph([("d", "decision"), ("a", "action", "reject order"),
                           ("x", "action", "other outcome")],
                          [("d", "a", "accepted"), ("d", "x", "rejected")])
        scored = score_control_relations(data, candidate, aligned({"A": ("a",)}), {"N": "d"}, {})
        self.assertEqual(scored.facts[0].status, "FN+FP")

    def test_binary_request_acceptance_uses_denied_opposite_and_accepted_outcome(self):
        data = control([node()], [relation("R", "decision_branch", target=("A",),
                                        guard="request accepted")])
        nodes = [("d", "decision", "MSP either denies the request or performs the measurement?"),
                 ("a", "action", "MSP performs the measurement"),
                 ("x", "action", "MSP denies the request")]
        for accepted_label in ("measured", "performed"):
            with self.subTest(accepted_label=accepted_label):
                candidate = graph(nodes, [("d", "a", accepted_label), ("d", "x", "denied")])
                scored = score_control_relations(data, candidate, aligned({"A": ("a",)}),
                                                 {"N": "d"}, {})
                self.assertEqual(scored.facts[0].status, "TP")
        wrong_target = graph(nodes, [("d", "a", "denied"), ("d", "x", "measured")])
        scored = score_control_relations(data, wrong_target, aligned({"A": ("a",)}),
                                         {"N": "d"}, {})
        self.assertEqual(scored.facts[0].status, "FN+FP")

    def test_approved_branch_can_confirm_only_its_accepted_action(self):
        data = control([node()], [relation("R", "decision_branch", target=("A",),
                                        guard="confirmed")])
        nodes = [("d", "decision", "approve or reject invoice?"),
                 ("a", "action", "confirm invoice with payment advice"),
                 ("x", "action", "reject invoice")]
        good = graph(nodes, [("d", "a", "approved"), ("d", "x", "rejected")])
        bad = graph(nodes, [("d", "a", "rejected"), ("d", "x", "approved")])
        anchor = aligned({"A": ("a",)})
        self.assertEqual(score_control_relations(data, good, anchor, {"N": "d"}, {}).facts[0].status,
                         "TP")
        self.assertEqual(score_control_relations(data, bad, anchor, {"N": "d"}, {}).facts[0].status,
                         "FN+FP")

    def test_ambiguous_abbreviated_guard_without_accepted_outcome_stays_i(self):
        data = control([node()], [relation("R", "decision_branch", target=("A",),
                                        guard="approved request")])
        candidate = graph([("d", "decision"), ("a", "action"), ("x", "final")],
                          [("d", "a", "approved"), ("d", "x", "rejected")])
        anchor = aligned({}, ambiguous=("A",), candidates={"A": ("a",)})
        scored = score_control_relations(data, candidate, anchor, {"N": "d"}, {})
        self.assertEqual(scored.facts[0].status, "indeterminate_alignment")

    def test_explicit_missed_deadline_guard_matches_same_clock_and_polarity(self):
        data = control([node(evidence=({"kind": "gateway_guard"},))],
                       [relation("R", "decision_branch", target=("A",),
                                 guard="misses 2:30 pm")])
        candidate = graph([("d", "decision"), ("a", "action"), ("x", "final")],
                          [("d", "a", "not_completed_by_230pm"),
                           ("d", "x", "completed_by_230pm")])
        anchor = aligned({"A": ("a",)})
        nodes, owners = match_control_nodes(data, candidate, anchor)
        self.assertEqual(nodes.facts[0].status, "TP")
        self.assertEqual(score_control_relations(data, candidate, anchor, owners, {}).facts[0].status,
                         "TP")

    def test_abbreviated_guard_requires_qualifier_on_same_accepted_outcome(self):
        data = control([node(evidence=({"kind": "gateway_guard"},))],
                       [relation("R", "decision_branch", target=("A",),
                                 guard="preliminarily confirmed")])
        matching = graph([("d", "decision"), ("a", "action", "preliminarily confirmed"),
                          ("x", "final")], [("d", "a", "confirmed"), ("d", "x", "rejected")])
        wrong = graph([("d", "decision"), ("a", "action", "preliminarily confirmed"),
                       ("x", "final")], [("d", "a", "rejected"), ("d", "x", "confirmed")])
        anchor = aligned({"A": ("a",)})
        self.assertEqual(score_control_relations(data, matching, anchor, {"N": "d"}, {}).facts[0].status,
                         "TP")
        self.assertEqual(score_control_relations(data, wrong, anchor, {"N": "d"}, {}).facts[0].status,
                         "FN+FP")

    def test_ambiguous_action_does_not_block_registered_gateway(self):
        data = control([node(anchors=("A",), evidence=({"kind": "gateway_guard"},))],
                       [relation("R", "decision_branch", target=("B",), guard="yes")])
        candidate = graph([("d", "decision"), ("b", "action"), ("x", "final")],
                          [("d", "b", "yes"), ("d", "x", "no")])
        anchor = aligned({"B": ("b",)}, ambiguous=("A",), candidates={"A": ("b",)})
        nodes, assigned = match_control_nodes(data, candidate, anchor)
        self.assertEqual((nodes.counts.tp, nodes.candidate_abstention_count), (1, 0))
        self.assertEqual(assigned["N"], "d")
        scored = score_control_relations(data, candidate, anchor, assigned, {},
                                         owner_alternatives=nodes.assignment_alternatives)
        self.assertEqual(scored.counts.tp, 1)
        self.assertEqual(anchor.generated("A"), frozenset())

    def test_ambiguous_action_without_other_evidence_remains_i(self):
        data = control([node(anchors=("A",))], [])
        candidate = graph([("d", "decision"), ("x", "final"), ("y", "final")],
                          [("d", "x"), ("d", "y")])
        result, _ = match_control_nodes(data, candidate,
                                        aligned({}, ambiguous=("A",), candidates={"A": ("x",)}))
        self.assertEqual(result.facts[0].status, "indeterminate_alignment")
        self.assertEqual(result.facts[0].diagnostics["reason_code"],
                         "CONTROL_NODE_ANCHOR_AMBIGUITY_AFTER_EVIDENCE")
        self.assertIsNone(result.to_dict()["counts"]["f1"])

    def test_one_ambiguous_relation_does_not_contaminate_node_or_sibling(self):
        data = control([node()], [
            relation("R1", "decision_branch", target=("A",), guard="yes"),
            relation("R2", "decision_branch", target=("B",), guard="no"),
        ])
        candidate = graph([("d", "decision"), ("b", "action"), ("x", "final")],
                          [("d", "x", "yes"), ("d", "b", "no")])
        anchor = aligned({"B": ("b",)}, ambiguous=("A",), candidates={"A": ("x",)})
        nodes, assigned = match_control_nodes(data, candidate, anchor)
        self.assertEqual(nodes.facts[0].status, "TP")
        scored = score_control_relations(data, candidate, anchor, assigned, {})
        self.assertEqual({f.fact_id: f.status for f in scored.facts},
                         {"R1": "indeterminate_alignment", "R2": "TP"})

    def test_invariant_relation_survives_owner_assignment_tie(self):
        data = control([node(anchors=("A",))],
                       [relation("R", "decision_branch", target=("A",), guard="yes")])
        candidate = graph([("d1", "decision"), ("d2", "decision"),
                           ("a", "action"), ("x", "final")],
                          [("d1", "a", "yes"), ("d1", "x", "no"),
                           ("d2", "a", "yes"), ("d2", "x", "no")])
        anchor = aligned({"A": ("a",)})
        nodes, assigned = match_control_nodes(data, candidate, anchor)
        self.assertEqual(nodes.facts[0].status, "indeterminate_alignment")
        scored = score_control_relations(data, candidate, anchor, assigned, {},
                                         owner_alternatives=nodes.assignment_alternatives)
        self.assertEqual(scored.facts[0].status, "TP")

    def test_owner_assignment_with_different_outcomes_remains_i(self):
        data = control([node(anchors=("A",))],
                       [relation("R", "decision_branch", target=("A",), guard="yes")])
        candidate = graph([("d1", "decision"), ("d2", "decision"),
                           ("a", "action"), ("x", "final")],
                          [("d1", "a", "yes"), ("d1", "x", "no"),
                           ("d2", "a", "no"), ("d2", "x", "yes")])
        anchor = aligned({"A": ("a",)})
        nodes, assigned = match_control_nodes(data, candidate, anchor)
        self.assertEqual(nodes.facts[0].status, "indeterminate_alignment")
        scored = score_control_relations(data, candidate, anchor, assigned, {},
                                         owner_alternatives=nodes.assignment_alternatives)
        self.assertEqual(scored.facts[0].status, "indeterminate_alignment")

    def test_split_first_fragment_and_all_fragments_stay_on_branch(self):
        data = control([node()], [relation("R", "decision_branch", target=("A",), guard="yes")])
        anchor = aligned({"A": ("a1", "a2")}, split=("A",))
        misplaced = graph([("d", "decision"), ("a1", "action"), ("a2", "action"),
                           ("m", "merge")],
                          [("d", "a1", "no"), ("d", "a2", "yes"),
                           ("a1", "m"), ("a2", "m")])
        result = score_control_relations(data, misplaced, anchor, {"N": "d"}, {})
        self.assertEqual(result.facts[0].status, "FN+FP")
        preserved = graph([("d", "decision"), ("a1", "action"), ("a2", "action"),
                           ("x", "final")],
                          [("d", "a1", "yes"), ("a1", "a2"), ("d", "x", "no")])
        self.assertEqual(score_control_relations(data, preserved, anchor, {"N": "d"}, {}).facts[0].status,
                         "TP")

    def test_all_registered_anchor_sets_must_be_on_required_branch(self):
        sets = ({"kind": "anchor_set", "semantic_unit_ids": ["A"]},
                {"kind": "anchor_set", "semantic_unit_ids": ["B"]})
        data = control([node(kind="Fork")], [relation("R", "parallel_launch", target=("A",),
                                                    evidence=sets)])
        candidate = graph([("f", "fork"), ("a", "action"), ("b", "action")],
                          [("f", "a"), ("f", "b")])
        scored = score_control_relations(data, candidate, aligned({"A": ("a",), "B": ("b",)}),
                                         {"N": "f"}, {})
        self.assertEqual(scored.facts[0].status, "FN")

    def test_compound_action_does_not_invent_two_fork_branches(self):
        sets = ({"kind": "anchor_set", "semantic_unit_ids": ["A"]},
                {"kind": "anchor_set", "semantic_unit_ids": ["B"]})
        data = control([node(kind="Fork", evidence=sets)], [])
        candidate = graph([("f", "fork"), ("c", "action"), ("x", "final")],
                          [("f", "c"), ("f", "x")])
        anchor = aligned({"A": ("c",), "B": ("c",)})
        nodes, _ = match_control_nodes(data, candidate, anchor)
        self.assertEqual(nodes.facts[0].status, "FN")

    def test_fork_branch_assignment_is_order_invariant(self):
        relations = [relation("R1", "parallel_launch", target=("A",)),
                     relation("R2", "parallel_launch", target=("B",))]
        candidate = graph([("f", "fork"), ("a1", "action"), ("a2", "action"),
                           ("b", "action"), ("j", "join")],
                          [("f", "a1"), ("f", "a2"), ("a1", "j"),
                           ("a2", "b"), ("b", "j")])
        anchor = aligned({"A": ("a1", "a2"), "B": ("b",)})
        outcomes = []
        for sequence in (relations, list(reversed(relations))):
            result = score_control_relations(control([node(kind="Fork")], sequence),
                                             candidate, anchor, {"N": "f"}, {})
            outcomes.append({fact.fact_id: fact.status for fact in result.facts})
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[0], {"R1": "TP", "R2": "TP"})

    def test_join_branch_assignment_is_order_invariant(self):
        relations = [relation("R1", "synchronization", incoming=("A",), target=("T",)),
                     relation("R2", "synchronization", incoming=("B",), target=("T",))]
        candidate = graph([("f", "fork"), ("a1", "action"), ("a2", "action"),
                           ("b", "action"), ("j", "join"), ("t", "action")],
                          [("f", "a1"), ("f", "a2"), ("a1", "j"),
                           ("a2", "b"), ("b", "j"), ("j", "t")])
        anchor = aligned({"A": ("a1", "a2"), "B": ("b",), "T": ("t",)})
        outcomes = []
        for sequence in (relations, list(reversed(relations))):
            result = score_control_relations(control([node(kind="Join")], sequence),
                                             candidate, anchor, {"N": "j"}, {})
            outcomes.append({fact.fact_id: fact.status for fact in result.facts})
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[0], {"R1": "TP", "R2": "TP"})

    def test_unattributed_scored_contradiction_has_explicit_ledger_record(self):
        data = control([node()], [relation("R", "decision_branch", target=("A",), guard="yes")])
        candidate = graph([("d", "decision"), ("a", "action"), ("x", "final")],
                          [("d", "a", "no"), ("d", "x", "yes")])
        scored = score_control_relations(data, candidate, aligned({"A": ("a",)}), {"N": "d"}, {})
        self.assertEqual(scored.facts[0].status, "FN+FP")
        attributed = {fid for item in scored.generated_relation_coverage
                      if item["status"] == "CONTRADICTION_ACCOUNTED"
                      for fid in item["source_fact_ids"]}
        self.assertTrue("R" in attributed or any(
            item["source_fact_id"] == "R" for item in scored.unattributed_contradictions))
        self.assertTrue(all(item["status"] in {"MATCHED", "CONTRADICTION_ACCOUNTED", "FP_ABSTAIN"}
                            for item in scored.generated_relation_coverage))


def occurrence(unit="A", *, role="initial", branch=(), loop=(), boundaries=(), ref=(), index=1):
    return SimpleNamespace(occurrence_id=f"O{index}", semantic_unit_id=unit,
                           recurrence_role=role, branch_scope_ids=tuple(branch),
                           loop_scope_ids=tuple(loop), boundary_constraints=tuple(boundaries),
                           reference_node_ids=tuple(ref), occurrence_index=index,
                           provenance=SimpleNamespace(review_state="accepted"))


class OccurrenceAndFlowCompletionTests(unittest.TestCase):
    def test_reference_backed_repeated_occurrences_preserve_locked_reference_identity(self):
        class FlatSimilarity:
            def matrix(self, reference, generated):
                return [[0.9 for _ in generated] for _ in reference]
        first = occurrence("A", role="initial", ref=("ref1",), index=1)
        second = occurrence("A", role="repeated", ref=("ref2",), index=2)
        first.evidence_status = second.evidence_status = "text_and_reference"
        reviewed = SimpleNamespace(units=(), occurrences=(first, second))
        entries = (AlignmentEntry("m1", "one_to_one", ("A",), ("ref1",), ("a",), {}, ()),
                   AlignmentEntry("m2", "one_to_one", ("A",), ("ref2",), ("b",), {}, ()))
        action = ActionAlignmentTable(entries, {"A": frozenset({"a", "b"})},
                                      {}, frozenset())
        matching = graph([("a", "action"), ("b", "action")], [("a", "b")])
        reversed_order = graph([("a", "action"), ("b", "action")], [("b", "a")])
        valid = build_control_anchor_evidence(reviewed, matching, action,
                                              FlatSimilarity(), "source")
        invalid = build_control_anchor_evidence(reviewed, reversed_order, action,
                                                FlatSimilarity(), "source")
        self.assertEqual(valid.occurrence_generated("O1"), frozenset({"a"}))
        self.assertEqual(valid.occurrence_generated("O2"), frozenset({"b"}))
        self.assertFalse(invalid.occurrence_generated("O1"))
        self.assertFalse(invalid.occurrence_generated("O2"))

    def test_unique_loop_phase_witness_is_tp(self):
        candidate = graph([("s", "initial"), ("a", "action"), ("b", "action")],
                          [("s", "a"), ("a", "b"), ("b", "a")])
        data = control([node(anchors=("B",))],
                       [relation("R", "loop_recurrence", target=("A",))])
        reviewed = SimpleNamespace(occurrences=(occurrence("A", loop=("L",)),
                                               occurrence("B", role="loop_body", loop=("L",), index=2)))
        result = evaluate_flow_v3(FlowInventoryV3((("A", "B"),), (), ()), candidate,
                                  aligned({"A": ("a",), "B": ("b",)}), data, reviewed)
        self.assertEqual(result.facts[0].status, "TP")
        self.assertEqual(result.counts.tp, 1)

    def test_nonunique_return_keeps_loop_phase_indeterminate(self):
        candidate = graph([("s", "initial"), ("a", "action"), ("b", "action"),
                           ("c", "action")],
                          [("s", "a"), ("a", "b"), ("b", "a"),
                           ("b", "c"), ("c", "a")])
        data = control([node(anchors=("B",))],
                       [relation("R", "loop_recurrence", target=("A",))])
        reviewed = SimpleNamespace(occurrences=(occurrence("A", loop=("L",)),
                                               occurrence("B", role="loop_body", loop=("L",), index=2)))
        result = evaluate_flow_v3(FlowInventoryV3((("A", "B"),), (), ()), candidate,
                                  aligned({"A": ("a",), "B": ("b",)}), data, reviewed)
        self.assertEqual(result.facts[0].status, "indeterminate_alignment")
        self.assertEqual(result.facts[0].diagnostics["reason_code"], "FLOW_LOOP_PHASE_UNRESOLVED")

    def test_repeated_to_initial_role_is_not_inferred_from_cycle_reachability(self):
        candidate = graph([("s", "initial"), ("a", "action"), ("b", "action")],
                          [("s", "a"), ("a", "b"), ("b", "a")])
        data = control([node(anchors=("B",))],
                       [relation("R", "loop_recurrence", target=("A",))])
        reviewed = SimpleNamespace(occurrences=(occurrence("A", role="repeated", loop=("L",)),
                                               occurrence("B", role="initial", loop=("L",), index=2)))
        result = evaluate_flow_v3(FlowInventoryV3((("A", "B"),), (), ()), candidate,
                                  aligned({"A": ("a",), "B": ("b",)}), data, reviewed)
        self.assertEqual(result.facts[0].status, "indeterminate_alignment")

    def test_unsupported_cycle_remains_fn_plus_fp(self):
        candidate = graph([("a", "action"), ("b", "action")],
                          [("a", "b"), ("b", "a")])
        result = evaluate_flow_v3(FlowInventoryV3((("A", "B"),), (), ()), candidate,
                                  aligned({"A": ("a",), "B": ("b",)}), control([], []))
        self.assertEqual(result.facts[0].status, "FN+FP")
        self.assertEqual((result.counts.fp, result.counts.fn), (1, 1))

    def test_general_branch_scope_uses_candidate_side_route(self):
        scoped = occurrence("X", branch=("branch:g:r",))
        reviewed = SimpleNamespace(occurrences=(occurrence("E", ref=("r",)), scoped))
        reference = {"nodes": [{"node_id": "r", "node_type": "Task"}],
                     "branch_scopes": [{"scope_id": "branch:g:r", "gateway_id": "g",
                                        "entry_target_id": "r", "gateway_type": "ExclusiveDataBased"}],
                     "loop_scopes": []}
        candidate = graph([("d", "decision"), ("e", "action"), ("x", "action"),
                           ("y", "action")],
                          [("d", "e"), ("e", "x"), ("d", "y")])
        anchor = aligned({"E": ("e",)})
        self.assertTrue(_occurrence_scope_matches(scoped, "x", candidate, anchor,
                        control([], []), reference, reviewed)[0])
        self.assertFalse(_occurrence_scope_matches(scoped, "y", candidate, anchor,
                         control([], []), reference, reviewed)[0])

    def test_general_boundary_requires_actual_order(self):
        boundary = SimpleNamespace(boundary_type="observable_order", side="before",
                                   reference_element_ids=("r",))
        scoped = occurrence("X", boundaries=(boundary,))
        reviewed = SimpleNamespace(occurrences=(occurrence("E", ref=("r",)), scoped))
        reference = {"nodes": [{"node_id": "r", "node_type": "Task"}],
                     "branch_scopes": [], "loop_scopes": []}
        anchor = aligned({"E": ("e",)})
        before = graph([("x", "action"), ("e", "action")], [("x", "e")])
        after = graph([("x", "action"), ("e", "action")], [("e", "x")])
        self.assertTrue(_occurrence_scope_matches(scoped, "x", before, anchor,
                        control([], []), reference, reviewed)[0])
        self.assertFalse(_occurrence_scope_matches(scoped, "x", after, anchor,
                         control([], []), reference, reviewed)[0])


if __name__ == "__main__":
    unittest.main()
