"""Opt-in Control Node role correction after the frozen and presence matchers.

Only a unique, locally evidenced logical role can replace an assignment.  Node
labels and adjacent branch *labels* may establish presence; branch destinations
and the correctness of the route are deliberately not consulted here.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from evaluation.friedrich_v3.core import Counts, EvalGraph, normalize_label

from .alignment import ActionAlignmentTable
from .anchor_evidence import ControlAnchorEvidence
from .control import NODE_TYPES, ControlComponentResult
from .control_node_presence_fallback_v2 import match_control_nodes_presence_fallback_v2


VERSION = "friedrich-code-control-node-role-assignment/4"

_ACTORS = {"supervisor", "treasurer", "employee", "customer", "supplier",
           "manager", "officer", "accounting", "department", "operator"}
_CANONICAL = {
    "approves": "approve", "approved": "approve", "approval": "approve",
    "rejects": "reject", "rejected": "reject", "rejection": "reject",
    "accepts": "accept", "accepted": "accept", "confirms": "accept",
    "confirmation": "accept", "confirm": "accept",
    "corrects": "correct", "corrected": "correct", "correction": "correct",
    "resubmits": "resubmit", "resubmitted": "resubmit",
    "checks": "check", "checked": "check", "reviews": "review",
    "receipts": "receipt", "matching": "match", "matches": "match",
    "returns": "return", "returned": "return", "goes": "return",
    "contracts": "contract", "documents": "document", "items": "item",
    "reports": "report", "decides": "decide",
}
_STOP = {"a", "an", "the", "if", "or", "and", "to", "from", "for", "with",
         "in", "on", "of", "is", "are", "until", "after", "before", "whether",
         "only", "either", "new", "again", "the", "decision", "branch",
         "based", "s", "?", "report?"}


def _tokens(label: str | None) -> set[str]:
    return {_CANONICAL.get(word, word) for word in (normalize_label(label) or "").split()
            if word not in _STOP}


def _first_actor(label: str | None) -> str | None:
    words = (normalize_label(label) or "").split()
    return words[0] if words and words[0] in _ACTORS else None


def _role_strength(source: Mapping[str, Any], node: Any, graph: EvalGraph) -> int:
    if node.type != NODE_TYPES[source["type"]]:
        return 0
    source_actor = _first_actor(source.get("purpose"))
    candidate_actor = _first_actor(node.label)
    if source_actor and candidate_actor and source_actor != candidate_actor:
        return 0
    source_words = _tokens(source.get("purpose"))
    node_words = _tokens(node.label)
    # The node's own control-outcome labels corroborate its declared role.
    # Their targets are never inspected by this presence matcher.
    local_words = set(node_words)
    if node.type in {"decision", "fork"}:
        for edge in graph.edges:
            if edge.source == node.id:
                local_words.update(_tokens(edge.label))
    elif node.type in {"merge", "join"}:
        for edge in graph.edges:
            if edge.target == node.id:
                local_words.update(_tokens(edge.label))
    shared = source_words & local_words
    if len(shared) < 2 or not (shared & node_words):
        return 0
    return len(shared) + (1 if source_actor and source_actor == candidate_actor else 0)


def match_control_nodes_role_assignment_v4(
    control: Mapping[str, Any], graph: EvalGraph,
    alignment: ActionAlignmentTable | ControlAnchorEvidence,
    *, reference: EvalGraph | None = None,
    reference_unit_nodes: Mapping[str, tuple[str, ...]] | None = None,
    reference_evidence: Mapping[str, Any] | None = None,
) -> tuple[ControlComponentResult, Mapping[str, str | None]]:
    baseline, old_assigned = match_control_nodes_presence_fallback_v2(
        control, graph, alignment, reference=reference,
        reference_unit_nodes=reference_unit_nodes,
        reference_evidence=reference_evidence,
    )
    if control["no_control"]:
        return baseline, old_assigned
    required = {item["fact_id"]: item for item in control["control_nodes"]
                if item["status"] == "required"}
    strengths = {
        fact_id: {node.id: score for node in graph.nodes
                  if (score := _role_strength(fact, node, graph)) >= 2}
        for fact_id, fact in required.items()
    }
    # Only a strictly best source role and a strictly best claimant for that
    # generated node can disambiguate an assignment.  Ties remain unresolved.
    proposed: dict[str, str] = {}
    for fact_id, options in strengths.items():
        if not options:
            continue
        ranked = sorted(options.items(), key=lambda item: (-item[1], item[0]))
        if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
            continue
        node_id, score = ranked[0]
        rivals = [values.get(node_id, 0) for other, values in strengths.items()
                  if other != fact_id]
        if rivals and max(rivals) >= score:
            continue
        proposed[fact_id] = node_id

    old_by_fact = {item.fact_id: item for item in baseline.facts}
    claimed = {item.generated_node_id: item.fact_id for item in baseline.facts
               if item.status == "TP" and item.generated_node_id}
    accepted: dict[str, str] = {}
    for fact_id, node_id in proposed.items():
        old = old_by_fact[fact_id]
        if old.status == "TP" and old.generated_node_id == node_id:
            continue
        current = claimed.get(node_id)
        if current is not None and current != fact_id:
            # An accepted owner with equally strong role evidence is not
            # displaced merely to improve case-wide assignment coverage.
            if strengths.get(current, {}).get(node_id, 0) >= strengths[fact_id][node_id]:
                continue
        accepted[fact_id] = node_id
    if not accepted:
        return baseline, old_assigned

    released = {claimed[node_id] for node_id in accepted.values()
                if node_id in claimed and claimed[node_id] not in accepted}
    # Exclude nodes already committed to another required role.  An old claim
    # displaced by a new assignment is no longer reserved by its old owner.
    reserved = {
        item.generated_node_id for item in baseline.facts
        if item.status == "TP" and item.generated_node_id
        and item.fact_id not in released and item.fact_id not in accepted
    } | set(accepted.values())
    facts = []
    assigned = dict(old_assigned)
    alternatives = dict(baseline.assignment_alternatives)
    for old in baseline.facts:
        if old.fact_id in accepted:
            node_id = accepted[old.fact_id]
            facts.append(replace(old, status="TP", generated_node_id=node_id,
                                 reason="unique type-correct local Control Node role",
                                 diagnostics={"reason_code": "CONTROL_NODE_UNIQUE_ROLE_V3",
                                              "role_strength": strengths[old.fact_id][node_id],
                                              "action_match_required": False,
                                              "routing_checked": False}))
            assigned[old.fact_id] = node_id
            alternatives[old.fact_id] = frozenset({node_id})
        elif old.fact_id in released:
            plausible = frozenset(node_id for node_id in strengths.get(old.fact_id, {})
                                  if node_id not in reserved)
            if len(plausible) > 1:
                facts.append(replace(
                    old, status="indeterminate_alignment", generated_node_id=None,
                    reason="multiple plausible nodes remain after wrong-role assignment released",
                    diagnostics={"reason_code": "CONTROL_NODE_RELEASED_ROLE_AMBIGUITY_V4",
                                 "plausible_generated_node_ids": sorted(plausible),
                                 "routing_checked": False},
                ))
                assigned[old.fact_id] = "indeterminate"
                alternatives[old.fact_id] = plausible
            else:
                facts.append(replace(old, status="FN", generated_node_id=None,
                                     reason="previously claimed node has a distinct source role",
                                     diagnostics={"reason_code": "CONTROL_NODE_WRONG_ROLE_RELEASED_V4"}))
                assigned[old.fact_id] = None
                alternatives[old.fact_id] = frozenset({None})
        else:
            facts.append(old)
    old_used = {item.generated_node_id for item in baseline.facts
                if item.status == "TP" and item.generated_node_id}
    new_used = {item.generated_node_id for item in facts
                if item.status == "TP" and item.generated_node_id}
    result = replace(
        baseline,
        facts=tuple(facts),
        counts=Counts(sum(item.status == "TP" for item in facts), baseline.counts.fp,
                      sum(item.status == "FN" for item in facts)),
        candidate_abstention_count=sum(item.status == "indeterminate_alignment"
                                       for item in facts),
        fp_abstention_count=baseline.fp_abstention_count + len(old_used) - len(new_used),
        assignment_alternatives=alternatives,
    )
    result.to_dict()
    return result, assigned
