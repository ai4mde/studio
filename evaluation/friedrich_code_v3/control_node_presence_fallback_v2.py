"""Opt-in Control Node presence correction for uniquely identifiable Joins.

Join presence is assessed from type and the two source-relevant forked streams.
The timing and correctness of synchronization remain Control Relation matters.
The earlier presence fallback and frozen V3.2 matcher remain unchanged.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from evaluation.friedrich_v3.core import Counts, EvalGraph, reachable

from .alignment import ActionAlignmentTable
from .anchor_evidence import ControlAnchorEvidence
from .control import ControlComponentResult
from .control_node_presence_fallback_v1 import (
    _meaning_words, match_control_nodes_presence_fallback_v1,
)


VERSION = "friedrich-code-control-node-presence-fallback/2"


def _incoming_stream(graph: EvalGraph, predecessor: str) -> tuple[set[str], set[str]]:
    """Read one incoming stream back to its Fork, without testing its timing."""
    seen: set[str] = set()
    frontier = [predecessor]
    words: set[str] = set()
    forks: set[str] = set()
    while frontier:
        current = frontier.pop()
        if current in seen:
            continue
        seen.add(current)
        node = graph.by_id[current]
        if node.type == "fork":
            forks.add(current)
            continue
        if node.type == "action":
            words.update(_meaning_words(node.label))
        frontier.extend(graph.incoming[current])
    return words, forks


def _structural_join_role(
    fact: Mapping[str, Any], node_id: str, graph: EvalGraph,
    reference: EvalGraph, reference_unit_nodes: Mapping[str, tuple[str, ...]],
    reference_join_id: str,
) -> Mapping[str, Any] | None:
    incoming = graph.incoming[node_id]
    if len(incoming) != 2:
        return None
    streams = [_incoming_stream(graph, predecessor) for predecessor in incoming]
    common_forks = set.intersection(*(forks for _, forks in streams))
    if len(common_forks) != 1:
        return None
    source_labels: dict[str, set[str]] = {}
    for unit_id in fact.get("anchor_action_ids", ()):  # Include only pre-Join acts.
        nodes = reference_unit_nodes.get(unit_id, ())
        upstream = [node_id for node_id in nodes
                    if reference_join_id in reachable(reference, node_id)]
        if upstream:
            source_labels[unit_id] = set().union(*(
                _meaning_words(reference.by_id[item].label) for item in upstream
            ))
    if len(source_labels) < 2:
        return None
    support = [set(unit for unit, words in source_labels.items()
                   if len(words & stream_words) >= 2)
               for stream_words, _ in streams]
    if any(not options for options in support):
        return None
    # Different source activities must identify at least two distinct streams.
    if not any(left != right for left in support[0] for right in set().union(*support[1:])):
        return None
    return {
        "reason_code": "CONTROL_NODE_UNIQUE_FORK_STREAM_JOIN_PRESENCE",
        "common_fork_id": next(iter(common_forks)),
        "incoming_stream_source_action_support": [sorted(items) for items in support],
        "action_match_required": False,
        "synchronization_timing_checked": False,
        "routing_correctness_checked": False,
    }


def match_control_nodes_presence_fallback_v2(
    control: Mapping[str, Any], graph: EvalGraph,
    alignment: ActionAlignmentTable | ControlAnchorEvidence,
    *, reference: EvalGraph | None = None,
    reference_unit_nodes: Mapping[str, tuple[str, ...]] | None = None,
    reference_evidence: Mapping[str, Any] | None = None,
) -> tuple[ControlComponentResult, Mapping[str, str | None]]:
    kwargs = dict(reference=reference, reference_unit_nodes=reference_unit_nodes,
                  reference_evidence=reference_evidence)
    baseline, old_assigned = match_control_nodes_presence_fallback_v1(
        control, graph, alignment, **kwargs)
    required_joins = [fact for fact in control["control_nodes"]
                      if fact["status"] == "required" and fact["type"] == "Join"]
    reference_joins = [node.id for node in reference.nodes if node.type == "join"] if reference else []
    if len(required_joins) != 1 or len(reference_joins) != 1 or reference_unit_nodes is None:
        return baseline, old_assigned
    fact = required_joins[0]
    old = next(item for item in baseline.facts if item.fact_id == fact["fact_id"])
    if old.status not in {"FN", "indeterminate_alignment"}:
        return baseline, old_assigned
    prior_choices = baseline.assignment_alternatives.get(fact["fact_id"], frozenset())
    if len({item for item in prior_choices if item not in {None, "implicit"}}) > 1:
        return baseline, old_assigned
    used = {item.generated_node_id for item in baseline.facts
            if item.status == "TP" and item.generated_node_id}
    options = [
        (node.id, evidence) for node in graph.nodes
        if node.type == "join" and node.id not in used
        if (evidence := _structural_join_role(
            fact, node.id, graph, reference, reference_unit_nodes, reference_joins[0]))
    ]
    if not options:
        return baseline, old_assigned
    assigned = dict(old_assigned)
    alternatives = dict(baseline.assignment_alternatives)
    if len(options) > 1:
        node_ids = frozenset(node_id for node_id, _ in options)
        if old.status == "indeterminate_alignment":
            return baseline, old_assigned
        new = replace(old, status="indeterminate_alignment", generated_node_id=None,
                      reason="multiple plausible fork-stream Join nodes",
                      diagnostics={"reason_code": "CONTROL_NODE_JOIN_ROLE_AMBIGUITY",
                                   "plausible_generated_node_ids": sorted(node_ids)})
        counts = Counts(baseline.counts.tp, baseline.counts.fp,
                        baseline.counts.fn - 1)
        abstention = baseline.candidate_abstention_count + 1
        assigned[fact["fact_id"]] = "indeterminate"
        alternatives[fact["fact_id"]] = node_ids
    else:
        node_id, evidence = options[0]
        new = replace(old, status="TP", generated_node_id=node_id,
                      reason="unique Join for the source-relevant forked streams",
                      diagnostics=evidence)
        counts = Counts(baseline.counts.tp + 1, baseline.counts.fp,
                        baseline.counts.fn - int(old.status == "FN"))
        abstention = baseline.candidate_abstention_count - int(
            old.status == "indeterminate_alignment")
        assigned[fact["fact_id"]] = node_id
        alternatives[fact["fact_id"]] = frozenset({node_id})
    result = replace(
        baseline, counts=counts,
        facts=tuple(new if item.fact_id == old.fact_id else item for item in baseline.facts),
        candidate_abstention_count=abstention,
        fp_abstention_count=baseline.fp_abstention_count - int(new.status == "TP"),
        assignment_alternatives=alternatives,
    )
    result.to_dict()
    return result, assigned
