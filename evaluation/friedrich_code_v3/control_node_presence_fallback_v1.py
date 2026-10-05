"""Versioned, conservative semantic-presence fallback for Control Nodes.

The frozen V3.2 matcher is run unchanged first. Only source-derived nodes it
leaves as FN may be reconsidered using the node's type, its own label, and
adjacent branch labels. No downstream Action target or route outcome is used.
Control Relation scoring is deliberately outside this component.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from typing import Any, Mapping

from evaluation.friedrich_v3.core import Counts, EvalGraph

from .alignment import ActionAlignmentTable
from .anchor_evidence import ControlAnchorEvidence
from .control import (
    NODE_TYPES, ControlComponentResult, _guard_tokens, _owner_relations,
    match_control_nodes,
)


VERSION = "friedrich-code-control-node-presence-fallback/1"
_CANONICAL = {
    "approval": "approve", "authorization": "approve", "rejection": "reject",
    "confirmation": "confirm", "acceptance": "accept", "cancellation": "cancel",
    "files": "file", "parts": "part", "requests": "request", "branches": "branch",
}
_GENERIC = {
    "route", "select", "choose", "decision", "fork", "join", "merge", "branch",
    "process", "activity", "required", "source", "candidate", "logical", "control",
    "if", "when", "whether", "either", "every", "only", "versus", "then",
}
_ACTORS = {
    "supervisor", "employee", "customer", "supplier", "manager", "officer",
    "associate", "operator", "department", "system", "service",
}


def _meaning_words(value: str | None) -> set[str]:
    return {_CANONICAL.get(word, word) for word in _guard_tokens(value)} - _GENERIC


def _local_semantics(
    fact: Mapping[str, Any], candidate_id: str, control: Mapping[str, Any], graph: EvalGraph,
) -> Mapping[str, Any] | None:
    """Require distinctive local wording, without testing branch destinations."""
    node = graph.by_id[candidate_id]
    source_text = " ".join([
        fact.get("purpose") or "",
        *(span.get("exact_excerpt", "") for span in fact.get("source_spans", ())),
    ])
    source_words = _meaning_words(source_text)
    label_words = _meaning_words(node.label)
    shared = source_words & label_words
    owned = _owner_relations(control, fact["fact_id"])
    guards = [_meaning_words(relation.get("guard_meaning"))
              for relation in owned if relation.get("type") == "decision_branch"
              and relation.get("guard_meaning")]
    guard_words = set().union(*guards) if guards else set()
    # A shared actor or generic gateway word cannot by itself identify a
    # business decision. Require the subject matter as well as a predicate.
    domain_words = source_words - guard_words - _ACTORS
    label_support = (len(shared) >= 2 and bool(domain_words & label_words)
                     and (not guard_words or bool(guard_words & label_words)))
    local_edges = [edge for edge in graph.edges
                   if ((edge.source == candidate_id and node.type in {"decision", "fork"})
                       or (edge.target == candidate_id and node.type in {"merge", "join"}))]
    edge_words = [_meaning_words(edge.label) for edge in local_edges]
    # Branch labels may corroborate a partially labeled Decision. They are
    # read as claims only: their targets and route correctness are not tested.
    branch_support = (node.type == "decision" and bool(domain_words & label_words)
                      and bool(shared) and len(guards) >= 2 and
                      sum(any(guard & words for words in edge_words) for guard in guards) >= 2)
    if not (label_support or branch_support):
        return None
    return {
        "reason_code": "CONTROL_NODE_LOCAL_SEMANTIC_PRESENCE",
        "matched_source_words": sorted(shared),
        "label_support": label_support,
        "branch_label_support": branch_support,
        "action_anchor_or_downstream_target_required": False,
        "routing_or_termination_checked": False,
    }


def match_control_nodes_presence_fallback_v1(
    control: Mapping[str, Any], graph: EvalGraph,
    alignment: ActionAlignmentTable | ControlAnchorEvidence,
    *, reference: EvalGraph | None = None,
    reference_unit_nodes: Mapping[str, tuple[str, ...]] | None = None,
    reference_evidence: Mapping[str, Any] | None = None,
) -> tuple[ControlComponentResult, Mapping[str, str | None]]:
    """Keep frozen matches; recover only uniquely identified missed nodes."""
    baseline, old_assigned = match_control_nodes(
        control, graph, alignment, reference=reference,
        reference_unit_nodes=reference_unit_nodes,
        reference_evidence=reference_evidence,
    )
    required = {fact["fact_id"]: fact for fact in control["control_nodes"]
                if fact["status"] == "required"}
    used = {fact.generated_node_id for fact in baseline.facts
            if fact.status == "TP" and fact.generated_node_id is not None}
    options: dict[str, list[tuple[str, Mapping[str, Any]]]] = {}
    for old in baseline.facts:
        if old.status != "FN" or old.fact_id not in required:
            continue
        fact = required[old.fact_id]
        options[old.fact_id] = []
        for node in graph.nodes:
            if node.type != NODE_TYPES[fact["type"]] or node.id in used:
                continue
            evidence = _local_semantics(fact, node.id, control, graph)
            if evidence:
                options[old.fact_id].append((node.id, evidence))
    claimed = Counter(node_id for candidates in options.values()
                      for node_id, _ in candidates)
    facts = []
    assigned = dict(old_assigned)
    alternatives = dict(baseline.assignment_alternatives)
    converted_tp = converted_i = 0
    for old in baseline.facts:
        candidates = options.get(old.fact_id, ())
        if not candidates:
            facts.append(old)
            continue
        node_ids = frozenset(node_id for node_id, _ in candidates)
        if len(candidates) == 1 and claimed[candidates[0][0]] == 1:
            node_id, evidence = candidates[0]
            facts.append(replace(
                old, status="TP", generated_node_id=node_id,
                reason="unique type-correct node with local semantic role evidence",
                diagnostics=evidence,
            ))
            assigned[old.fact_id] = node_id
            alternatives[old.fact_id] = frozenset({node_id})
            converted_tp += 1
        else:
            facts.append(replace(
                old, status="indeterminate_alignment", generated_node_id=None,
                reason="multiple plausible local-semantic Control Node assignments",
                diagnostics={
                    "reason_code": "CONTROL_NODE_LOCAL_SEMANTIC_AMBIGUITY",
                    "plausible_generated_node_ids": sorted(node_ids),
                    "competing_required_facts": sorted(
                        fact_id for fact_id, rows in options.items()
                        if any(node_id in node_ids for node_id, _ in rows)),
                    "routing_or_termination_checked": False,
                },
            ))
            assigned[old.fact_id] = "indeterminate"
            alternatives[old.fact_id] = (node_ids | {None}
                                         if any(claimed[node_id] > 1 for node_id in node_ids)
                                         else node_ids)
            converted_i += 1
    if not converted_tp and not converted_i:
        return baseline, old_assigned
    if converted_tp > baseline.fp_abstention_count:
        raise ValueError("Recovered Control Nodes exceed unmatched generated-node count")
    result = replace(
        baseline,
        counts=Counts(baseline.counts.tp + converted_tp, baseline.counts.fp,
                      baseline.counts.fn - converted_tp - converted_i),
        facts=tuple(facts),
        candidate_abstention_count=baseline.candidate_abstention_count + converted_i,
        fp_abstention_count=baseline.fp_abstention_count - converted_tp,
        assignment_alternatives=alternatives,
    )
    result.to_dict()  # Verify the existing fixed-denominator scoring invariant.
    return result, assigned
