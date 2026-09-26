from __future__ import annotations

import tempfile
import random
import unittest
from pathlib import Path

from evaluation.friedrich_v3.core import Counts, EvalEdge, EvalGraph, EvalNode
from evaluation.friedrich_code_v3.alignment import ActionAlignmentTable, AlignmentEntry
from evaluation.friedrich_code_v3.anchor_evidence import build_control_anchor_evidence, _occurrence_scope_matches
from evaluation.friedrich_code_v3.control import _case_wide_assignment, match_control_nodes, score_control_relations
from evaluation.friedrich_code_v3.evaluator import evaluate_candidate_file_v3
from evaluation.friedrich_code_v3.flow import FlowInventoryV3, evaluate_flow_v3
from evaluation.friedrich_code_v3.flow_inventory_store import load_fixed_flow_inventory
from evaluation.friedrich_code_v3.inventory import load_frozen_corpus
from evaluation.friedrich_code_v3.scoring import component_summary
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory


def alignment(**items: tuple[str, ...]) -> ActionAlignmentTable:
    return ActionAlignmentTable((), {key: frozenset(value) for key, value in items.items()},
                                {}, frozenset())


class V31ContractTests(unittest.TestCase):
    def test_frozen_source_denominators_and_unresolved_questions(self):
        corpus = load_frozen_corpus()
        self.assertEqual(len(corpus.case_ids), 40)
        cases = [corpus.load_case(case_id).control for case_id in corpus.case_ids]
        self.assertEqual(sum(f["status"] == "required" for case in cases
                             for f in case["control_nodes"]), 95)
        self.assertEqual(sum(f["status"] == "required" for case in cases
                             for f in case["control_relations"]), 196)
        self.assertEqual(sum(len(case["unresolved_facts"]) for case in cases), 11)
        self.assertEqual(sum(bool(case["no_control"]) for case in cases), 6)
        for case_id in corpus.case_ids:
            self.assertIsNotNone(load_fixed_flow_inventory(case_id, corpus))

    def test_fixed_denominator_and_null_metrics_for_indeterminate(self):
        value = component_summary(Counts(2, 1, 1), 4, 1)
        self.assertEqual(value["required_denominator"], 4)
        self.assertEqual(value["determinate_coverage"], .75)
        self.assertEqual(value["recall_interval"], [.5, .75])
        self.assertIsNone(value["f1"])
        with self.assertRaises(ValueError):
            component_summary(Counts(2, 0, 1), 5, 1)

    def test_missing_anchor_is_fn_while_ambiguous_alignment_is_indeterminate(self):
        graph = EvalGraph((EvalNode("a", "action", "A"),), ())
        inventory = FlowInventoryV3((("A", "B"),), (), ())
        missing = evaluate_flow_v3(inventory, graph, alignment(A=("a",)))
        self.assertEqual(missing.facts[0].status, "FN")
        self.assertEqual(missing.to_dict()["counts"]["required_denominator"], 1)
        ambiguous = ActionAlignmentTable((), {"A": frozenset({"a"})}, {}, frozenset({"B"}))
        result = evaluate_flow_v3(inventory, graph, ambiguous)
        self.assertEqual(result.facts[0].status, "indeterminate_alignment")
        self.assertEqual(result.to_dict()["counts"]["required_denominator"], 1)
        self.assertIsNone(result.to_dict()["counts"]["recall"])

    def test_internal_split_cycle_remains_alignment_indeterminate(self):
        graph = EvalGraph(
            (EvalNode("a1", "action"), EvalNode("a2", "action"), EvalNode("b", "action")),
            (EvalEdge("a1", "a2"), EvalEdge("a2", "a1"), EvalEdge("a2", "b")),
        )
        inventory = FlowInventoryV3((("A", "B"),), (), ())
        result = evaluate_flow_v3(inventory, graph, alignment(A=("a1", "a2"), B=("b",)))
        self.assertEqual(result.facts[0].status, "indeterminate_alignment")
        self.assertEqual(result.unsupported_cycle_violation_count, 0)

    def test_source_supported_recurrence_keeps_cross_cycle_indeterminate(self):
        graph = EvalGraph((EvalNode("a", "action"), EvalNode("b", "action")),
                          (EvalEdge("a", "b"), EvalEdge("b", "a")))
        control = {
            "control_nodes": [{"fact_id": "N", "anchor_action_ids": ["B"]}],
            "control_relations": [{"status": "required", "type": "loop_recurrence",
                                   "source_control_fact": "N", "target_action_ids": ["A"]}],
        }
        result = evaluate_flow_v3(FlowInventoryV3((("A", "B"),), (), ()),
                                  graph, alignment(A=("a",), B=("b",)), control)
        self.assertEqual(result.facts[0].status, "indeterminate_alignment")
        self.assertEqual(result.source_supported_cycle_indeterminate_count, 1)

    def test_unresolved_facts_never_enter_control_denominator(self):
        control = {
            "control_nodes": [
                {"fact_id": "N1", "status": "required", "type": "Decision", "anchor_action_ids": ["A"]},
                {"fact_id": "N2", "status": "unresolved", "type": "Merge", "anchor_action_ids": []},
            ],
            "control_relations": [], "permitted_equivalences": [], "unresolved_facts": [
                {"question": "Frozen source question", "status": "unresolved"}
            ], "no_control": False,
        }
        graph = EvalGraph((EvalNode("a", "action", "A"),), ())
        nodes, assigned = match_control_nodes(control, graph, alignment(A=("a",)))
        relations = score_control_relations(control, graph, alignment(A=("a",)), assigned, {})
        self.assertEqual((nodes.required_fact_count, nodes.unresolved_source_fact_count), (1, 1))
        self.assertEqual(nodes.to_dict()["counts"]["required_denominator"], 1)
        self.assertEqual((nodes.counts.fn, relations.counts.fn), (1, 0))

    def test_malformed_candidate_is_flagged_without_scores(self):
        class UnusedSimilarity:
            def matrix(self, reference, generated):
                raise AssertionError("similarity must not run for malformed candidate")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "activity_graph.json"
            path.write_text('{"nodes": [{"id": "a", "type": "action"}], "edges": [{"source": "a", "target": "missing"}]}')
            result = evaluate_candidate_file_v3("4-1", "malformed", path, UnusedSimilarity())
        self.assertEqual(result["candidate_status"], "MALFORMED")
        self.assertIsNone(result["component_scores"])
        self.assertNotIn("Action", result)
        self.assertIn("Action", result["source_denominators"])

    def test_text_only_repeated_occurrence_requires_a_cycle(self):
        class FlatSimilarity:
            def matrix(self, reference, generated):
                return [[0.9 for _ in generated] for _ in reference]
        case = load_frozen_corpus().load_case("9-6")
        reviewed = SemanticInventory.from_dict(case.reviewed_action)
        action = alignment()
        node = EvalNode("combine", "action", "combine revised electrical and physical designs")
        linear = build_control_anchor_evidence(
            reviewed, EvalGraph((node,), ()), action, FlatSimilarity(), case.source_text,
        )
        self.assertEqual(linear.occurrence_generated("SO-9-6-23"), frozenset({"combine"}))
        self.assertFalse(linear.occurrence_generated("SO-9-6-24"))
        cyclic = build_control_anchor_evidence(
            reviewed, EvalGraph((node,), (EvalEdge("combine", "combine"),)),
            action, FlatSimilarity(), case.source_text,
        )
        self.assertEqual(cyclic.occurrence_generated("SO-9-6-24"), frozenset({"combine"}))
        self.assertEqual(action.unit_to_generated, {})
        scoped = build_control_anchor_evidence(
            reviewed, EvalGraph((node,), ()), action, FlatSimilarity(), case.source_text,
            control=case.control, reference_evidence=case.reference_evidence,
        )
        self.assertFalse(scoped.generated("SU-9-6-13"))

    def test_full_9_6_occurrence_scope_and_same_design_cycle(self):
        case = load_frozen_corpus().load_case("9-6")
        reviewed = SemanticInventory.from_dict(case.reviewed_action)
        by_id = {o.occurrence_id: o for o in reviewed.occurrences}
        nodes = tuple(EvalNode(node_id, kind, label) for node_id, kind, label in (
            ("f", "fork", None), ("e", "action", "revise electrical design"),
            ("p", "action", "revise physical design"), ("j", "join", None),
            ("c", "action", "combine revised designs"), ("t", "action", "test combined design"),
            ("d", "decision", "combined design passes?"), ("r", "merge", None),
            ("x", "final", None),
        ))
        edges = tuple(EvalEdge(*pair) for pair in (
            ("f", "e"), ("f", "p"), ("e", "j"), ("p", "j"),
            ("j", "c"), ("c", "t"), ("t", "d"), ("d", "r"),
            ("r", "f"), ("d", "x"),
        ))
        graph = EvalGraph(nodes, edges)
        aligned = alignment(**{"SU-9-6-06": ("e",), "SU-9-6-11": ("p",),
                               "SU-9-6-03": ("e",), "SU-9-6-08": ("p",)})
        for occurrence_id in ("SO-9-6-23", "SO-9-6-24"):
            valid, reasons = _occurrence_scope_matches(
                by_id[occurrence_id], "c", graph, aligned, case.control, case.reference_evidence,
            )
            self.assertTrue(valid, reasons)
        missing_return = EvalGraph(nodes, tuple(edge for edge in edges if (edge.source, edge.target) != ("r", "f")))
        valid, reasons = _occurrence_scope_matches(
            by_id["SO-9-6-24"], "c", missing_return, aligned, case.control, case.reference_evidence,
        )
        self.assertFalse(valid)
        self.assertTrue(any("loop" in reason or "cycle" in reason for reason in reasons))

    def test_distinct_9_1_occurrences_keep_source_order(self):
        class FlatSimilarity:
            def matrix(self, reference, generated):
                return [[0.9 for _ in generated] for _ in reference]
        case = load_frozen_corpus().load_case("9-1")
        reviewed = SemanticInventory.from_dict(case.reviewed_action)
        entry = AlignmentEntry("locked", "one_to_one", ("SU-9-1-03",),
                               ("16733388",), ("second",), {}, ())
        action = ActionAlignmentTable((entry,), {"SU-9-1-03": frozenset({"second"})},
                                      {"second": frozenset({"SU-9-1-03"})}, frozenset())
        nodes = (EvalNode("first", "action", "check CRM system for newly filed returns"),
                 EvalNode("second", "action", "check CRM system for newly filed returns"))
        forward = build_control_anchor_evidence(
            reviewed, EvalGraph(nodes, (EvalEdge("first", "second"),)),
            action, FlatSimilarity(), case.source_text,
        )
        self.assertEqual(forward.occurrence_generated("SO-9-1-09"), frozenset({"second"}))
        reverse = build_control_anchor_evidence(
            reviewed, EvalGraph(nodes, (EvalEdge("second", "first"),)),
            action, FlatSimilarity(), case.source_text,
        )
        self.assertFalse(reverse.occurrence_generated("SO-9-1-09"))

    def test_bare_gateway_cannot_satisfy_gateway_guard_evidence(self):
        control = {
            "control_nodes": [{
                "fact_id": "N", "type": "Decision", "status": "required",
                "anchor_action_ids": ["A"],
                "control_anchor_evidence": [{"kind": "gateway_guard", "source_predicate": "parts missing"}],
            }],
            "control_relations": [{
                "fact_id": "R", "type": "decision_branch", "status": "required",
                "source_control_fact": "N", "target_action_ids": ["A"],
                "guard_meaning": "parts missing", "reference_evidence_ids": [],
            }],
            "permitted_equivalences": [], "no_control": False,
        }
        graph = EvalGraph(
            (EvalNode("d", "decision"), EvalNode("a", "action", "procure missing parts"),
             EvalNode("x", "final")),
            (EvalEdge("d", "a"), EvalEdge("d", "x")),
        )
        result, _ = match_control_nodes(control, graph, alignment())
        self.assertEqual(result.counts.fn, 1)

    def test_gateway_requires_all_registered_routes(self):
        control = {
            "control_nodes": [{"fact_id": "N", "type": "Decision", "status": "required",
                               "anchor_action_ids": [], "control_anchor_evidence": [
                                   {"kind": "gateway_guard", "source_predicate": "route by result"}]}],
            "control_relations": [
                {"fact_id": "R1", "type": "decision_branch", "status": "required",
                 "source_control_fact": "N", "target_action_ids": ["A"],
                 "guard_meaning": "yes", "reference_evidence_ids": []},
                {"fact_id": "R2", "type": "decision_branch", "status": "required",
                 "source_control_fact": "N", "target_action_ids": ["B"],
                 "guard_meaning": "no", "reference_evidence_ids": []},
            ], "permitted_equivalences": [], "no_control": False,
        }
        graph = EvalGraph(
            (EvalNode("d", "decision", "route by result"), EvalNode("a", "action", "A"),
             EvalNode("x", "final")),
            (EvalEdge("d", "a", "yes"), EvalEdge("d", "x", "no")),
        )
        result, _ = match_control_nodes(control, graph, alignment(A=("a",)))
        self.assertEqual(result.counts.fn, 1)

    def test_tied_control_nodes_are_indeterminate_not_arbitrarily_matched(self):
        control = {
            "control_nodes": [{"fact_id": "N", "type": "Decision", "status": "required",
                               "anchor_action_ids": ["A"], "reference_evidence_ids": []}],
            "control_relations": [], "permitted_equivalences": [], "no_control": False,
        }
        graph = EvalGraph(
            (EvalNode("d1", "decision"), EvalNode("d2", "decision"),
             EvalNode("a", "action", "A"), EvalNode("x", "final")),
            (EvalEdge("d1", "a"), EvalEdge("d1", "x"),
             EvalEdge("d2", "a"), EvalEdge("d2", "x")),
        )
        result, _ = match_control_nodes(control, graph, alignment(A=("a",)))
        self.assertEqual(result.counts.tp, 0)
        self.assertEqual(result.candidate_abstention_count, 1)
        self.assertIsNone(result.to_dict()["counts"]["precision"])

    def test_case_wide_assignment_is_one_to_one_and_inventory_order_invariant(self):
        options = {"N1": ((3, "d1"), (3, "d2")), "N2": ((4, "d1"),)}
        expected = {"N1": frozenset({"d2"}), "N2": frozenset({"d1"})}
        self.assertEqual(_case_wide_assignment(options), expected)
        self.assertEqual(_case_wide_assignment(dict(reversed(list(options.items())))), expected)

    def test_case_wide_assignment_agrees_with_small_exact_enumeration(self):
        rng = random.Random(310)
        for _ in range(40):
            options = {f"N{i}": tuple((rng.randrange(5), f"d{j}") for j in range(4)
                                      if rng.randrange(3)) for i in range(4)}
            optimum = (-1, -1)
            possible = {key: set() for key in options}
            names = tuple(sorted(options))

            def visit(index, used, score, choices):
                nonlocal optimum
                if index == len(names):
                    objective = (sum(item is not None for item in choices), score)
                    if objective > optimum:
                        optimum = objective
                        for values in possible.values():
                            values.clear()
                    if objective == optimum:
                        for key, value in zip(names, choices):
                            possible[key].add(value)
                    return
                visit(index + 1, used, score, (*choices, None))
                for value, node in options[names[index]]:
                    if node not in used:
                        visit(index + 1, used | {node}, score + value, (*choices, node))

            visit(0, set(), 0, ())
            self.assertEqual(_case_wide_assignment(options),
                             {key: frozenset(values) for key, values in possible.items()})

    def test_no_control_scores_generated_node_and_branch_relations_as_fp(self):
        control = {"control_nodes": [], "control_relations": [],
                   "permitted_equivalences": [], "no_control": True}
        graph = EvalGraph(
            (EvalNode("d", "decision", "optional route"),
             EvalNode("a", "action", "A"), EvalNode("b", "action", "B")),
            (EvalEdge("d", "a", "yes"), EvalEdge("d", "b", "no")),
        )
        nodes, assigned = match_control_nodes(control, graph, alignment())
        relations = score_control_relations(control, graph, alignment(), assigned, {})
        self.assertEqual(nodes.counts.fp, 1)
        self.assertEqual(relations.counts.fp, 2)
        self.assertEqual((nodes.required_fact_count, relations.required_fact_count), (0, 0))

    def test_non_exhaustive_generated_relation_coverage_is_complete(self):
        control = {"control_nodes": [], "control_relations": [],
                   "permitted_equivalences": [], "no_control": False}
        graph = EvalGraph(
            (EvalNode("d", "decision"), EvalNode("a", "action"),
             EvalNode("b", "action"), EvalNode("m", "merge")),
            (EvalEdge("d", "a"), EvalEdge("d", "b"),
             EvalEdge("a", "m"), EvalEdge("b", "m")),
        )
        result = score_control_relations(control, graph, alignment(), {}, {})
        self.assertEqual(result.counts.fp, 0)
        self.assertEqual(result.fp_abstention_count, 4)
        self.assertEqual(len(result.generated_relation_coverage), 4)
        self.assertTrue(all(item["status"] == "FP_ABSTAIN"
                            for item in result.generated_relation_coverage))

    def test_non_exhaustive_action_only_cycle_has_control_abstention_coverage(self):
        control = {"control_nodes": [], "control_relations": [],
                   "permitted_equivalences": [], "no_control": False}
        graph = EvalGraph((EvalNode("a", "action"), EvalNode("b", "action")),
                          (EvalEdge("a", "b"), EvalEdge("b", "a")))
        result = score_control_relations(control, graph, alignment(), {}, {})
        self.assertEqual(result.counts.fp, 0)
        self.assertEqual(result.fp_abstention_count, 2)
        self.assertEqual({item["role"] for item in result.generated_relation_coverage},
                         {"cycle_control"})


if __name__ == "__main__":
    unittest.main()
