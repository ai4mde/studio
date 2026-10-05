"""Opt-in, evidence-gated sharing of one generated Decision by two source roles.

The v4 matcher remains unchanged. Sharing is allowed only for a unique pair of
compatible quantified Decisions whose conditions and distinct outcomes are
explicit in one generated node's own label and outgoing guard labels. No
downstream route, Action score, or Relation score is used to establish presence.
"""

from __future__ import annotations

from dataclasses import replace
import re
from typing import Any, Mapping

from evaluation.friedrich_v3.core import Counts, EvalGraph, normalize_label

from .alignment import ActionAlignmentTable
from .anchor_evidence import ControlAnchorEvidence
from .control import ControlComponentResult
from .control_node_role_assignment_v4 import match_control_nodes_role_assignment_v4


VERSION = "friedrich-code-control-node-shared-roles/5"

_NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12", "twenty": "20", "thirty": "30",
    "sixty": "60", "ninety": "90",
}
_LEMMAS = {
    "cancelled": "cancel", "canceled": "cancel", "cancellation": "cancel",
    "completed": "complete", "completion": "complete", "finished": "finish",
    "resubmission": "resubmit", "resubmitted": "resubmit",
}
_ROLE_FILLER = {
    "a", "an", "the", "if", "not", "and", "or", "to", "for", "in",
    "after", "before", "within", "by", "at", "day", "days", "time",
    "request", "send", "email", "require", "complete", "finish",
    "outcome", "decision", "branch", "unfinished",
}


def _words(value: str | None) -> set[str]:
    return {_LEMMAS.get(_NUMBER_WORDS.get(word, word), _NUMBER_WORDS.get(word, word))
            for word in (normalize_label(value) or "").split()}


def _numbers(value: str | None) -> set[str]:
    return {word for word in _words(value) if re.fullmatch(r"\d+", word)}


def _role_evidence(
    first: Mapping[str, Any], second: Mapping[str, Any], node: Any,
    graph: EvalGraph, control: Mapping[str, Any],
) -> dict[str, Any] | None:
    if (first["type"] != "Decision" or second["type"] != "Decision"
        or node.type != "decision"
        or not first.get("anchor_action_ids")
        or set(first["anchor_action_ids"]) != set(second.get("anchor_action_ids", ()))):
        return None
    first_condition = _numbers(first.get("purpose"))
    second_condition = _numbers(second.get("purpose"))
    if (len(first_condition) != 1 or len(second_condition) != 1
        or first_condition == second_condition
        or not (first_condition | second_condition) <= _numbers(node.label)):
        return None
    edges = [edge for edge in graph.edges if edge.source == node.id and edge.label]
    if len(edges) < 3:
        return None
    first_role = (_words(first.get("purpose")) - _ROLE_FILLER
                  - first_condition - _words(second.get("purpose")))
    second_role = (_words(second.get("purpose")) - _ROLE_FILLER
                   - second_condition - _words(first.get("purpose")))
    first_edges = [edge for edge in edges if first_role & (_words(edge.label) - _ROLE_FILLER)]
    second_edges = [edge for edge in edges if second_role & (_words(edge.label) - _ROLE_FILLER)]
    if not any(left != right for left in first_edges for right in second_edges):
        return None
    # If both source roles specify a completed/finished outcome, the shared
    # node must explicitly offer that outcome as well. This checks a guard,
    # never the destination or whether the subsequent route is correct.
    source_relations = control["control_relations"]
    completed = all(any(
        relation["status"] == "required"
        and relation["type"] == "decision_branch"
        and relation["source_control_fact"] == fact["fact_id"]
        and {"complete", "finish"} & _words(relation.get("terminal_outcome"))
        for relation in source_relations) for fact in (first, second))
    if completed and not any({"complete", "finish"} & _words(edge.label)
                             for edge in edges):
        return None
    return {
        "source_condition_numbers": {
            first["fact_id"]: sorted(first_condition),
            second["fact_id"]: sorted(second_condition),
        },
        "distinct_outcome_edges": {
            first["fact_id"]: sorted(f"{edge.source}->{edge.target}" for edge in first_edges),
            second["fact_id"]: sorted(f"{edge.source}->{edge.target}" for edge in second_edges),
        },
        "shared_completed_outcome_present": completed,
    }


def match_control_nodes_shared_roles_v5(
    control: Mapping[str, Any], graph: EvalGraph,
    alignment: ActionAlignmentTable | ControlAnchorEvidence,
    *, reference: EvalGraph | None = None,
    reference_unit_nodes: Mapping[str, tuple[str, ...]] | None = None,
    reference_evidence: Mapping[str, Any] | None = None,
) -> tuple[ControlComponentResult, Mapping[str, str | None]]:
    baseline, old_assigned = match_control_nodes_role_assignment_v4(
        control, graph, alignment, reference=reference,
        reference_unit_nodes=reference_unit_nodes,
        reference_evidence=reference_evidence,
    )
    if control["no_control"]:
        return baseline, old_assigned
    required = {fact["fact_id"]: fact for fact in control["control_nodes"]
                if fact["status"] == "required"}
    by_fact = {fact.fact_id: fact for fact in baseline.facts}
    assigned = dict(old_assigned)
    alternatives = dict(baseline.assignment_alternatives)
    replacements = {}
    for missing_id, missing in required.items():
        old = by_fact[missing_id]
        if old.status not in {"FN", "indeterminate_alignment"}:
            continue
        possibilities = []
        for present_id, present in required.items():
            if present_id == missing_id or by_fact[present_id].status != "TP":
                continue
            node_id = assigned.get(present_id)
            if node_id not in graph.by_id:
                continue
            # At most two source roles may claim one generated node.
            if sum(assigned.get(fid) == node_id for fid in required) != 1:
                continue
            evidence = _role_evidence(present, missing, graph.by_id[node_id], graph, control)
            if evidence is None:
                continue
            # A second equally supported generated node would make the
            # many-to-one assignment ambiguous, even if currently unclaimed.
            if sum(_role_evidence(present, missing, candidate, graph, control) is not None
                   for candidate in graph.nodes if candidate.type == "decision") != 1:
                continue
            possibilities.append((present_id, node_id, evidence))
        if len(possibilities) != 1:
            continue
        present_id, node_id, evidence = possibilities[0]
        replacements[missing_id] = replace(
            old, status="TP", generated_node_id=node_id,
            reason="unique generated Decision explicitly represents two compatible source roles",
            diagnostics={"reason_code": "CONTROL_NODE_EXPLICIT_SHARED_ROLE_V5",
                         "shared_with_source_fact": present_id,
                         "action_match_required": False,
                         "routing_checked": False,
                         **evidence},
        )
        assigned[missing_id] = node_id
        alternatives[missing_id] = frozenset({node_id})
    if not replacements:
        return baseline, old_assigned
    facts = tuple(replacements.get(fact.fact_id, fact) for fact in baseline.facts)
    result = replace(
        baseline,
        facts=facts,
        counts=Counts(sum(fact.status == "TP" for fact in facts), baseline.counts.fp,
                      sum(fact.status == "FN" for fact in facts)),
        candidate_abstention_count=sum(fact.status == "indeterminate_alignment" for fact in facts),
        assignment_alternatives=alternatives,
    )
    result.to_dict()
    return result, assigned
