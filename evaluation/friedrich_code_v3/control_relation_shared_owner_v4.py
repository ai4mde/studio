"""Narrow relation evidence for an explicitly shared, quantified Decision owner.

All ordinary Control Relation scoring remains in local-evidence v3. This wrapper
only revisits an indeterminate terminal branch owned by a uniquely established
shared Decision, using the owner's local guard and the branch's visible end.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from evaluation.friedrich_v3.core import Counts, EvalGraph
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory

from .alignment import ActionAlignmentTable
from .anchor_evidence import ControlAnchorEvidence
from .control import ControlComponentResult, _Context, _relation_coverage
from .control_node_shared_roles_v5 import _numbers, _role_evidence, _words
from .control_relation_local_evidence_v3 import (
    _branch_nodes, score_control_relations_local_evidence_v3,
)


VERSION = "friedrich-code-control-relation-shared-owner/4"
_OUTCOME_FILLER = {
    "a", "an", "the", "current", "process", "request", "branch", "end",
    "ends", "before", "success", "only", "work", "without", "day", "time",
    "after", "within", "by", "at", "not", "no", "is", "are",
}
_TERMINAL_ACTS = {"stop", "end", "terminate", "cancel"}


def _shared_owner(
    source_id: str, owner: str, control: Mapping[str, Any], graph: EvalGraph,
    assigned_nodes: Mapping[str, str | None],
) -> bool:
    source = next((fact for fact in control["control_nodes"]
                   if fact["fact_id"] == source_id and fact["status"] == "required"), None)
    if source is None or owner not in graph.by_id:
        return False
    peers = [fact for fact in control["control_nodes"]
             if fact["status"] == "required" and fact["fact_id"] != source_id
             and assigned_nodes.get(fact["fact_id"]) == owner]
    return len(peers) == 1 and _role_evidence(
        peers[0], source, graph.by_id[owner], graph, control) is not None


def _explicit_terminal_branch(
    relation: Mapping[str, Any], owner: str, control: Mapping[str, Any],
    graph: EvalGraph, ctx: _Context, reviewed: SemanticInventory,
    accepted: ActionAlignmentTable,
) -> tuple[str, dict[str, Any]] | None:
    condition = _numbers(relation.get("guard_meaning"))
    if len(condition) != 1 or not condition <= _numbers(graph.by_id[owner].label):
        return None
    targets = relation.get("target_action_ids", ())
    units = {unit.semantic_unit_id: unit for unit in reviewed.units}
    if not targets or any(unit not in units or not (_words(units[unit].canonical_meaning)
                                            & _TERMINAL_ACTS) for unit in targets):
        return None
    # The source's same-condition branch can supply the explicit outcome name
    # for a separate termination fact. No other owner's relation is consulted.
    siblings = [item for item in control["control_relations"]
                if item["status"] == "required"
                and item["source_control_fact"] == relation["source_control_fact"]
                and item.get("guard_meaning") == relation.get("guard_meaning")]
    outcomes = set().union(*(
        _words(item.get("terminal_outcome")) - _OUTCOME_FILLER for item in siblings
        if item["type"] == "decision_branch"
    ))
    edges = [edge for edge in ctx.branch_edges(owner)
             if edge.label and outcomes & (_words(edge.label) - _OUTCOME_FILLER)
             and not ({"not", "no"} & _words(edge.label))]
    if len(edges) != 1:
        return None
    edge = edges[0]
    path = _branch_nodes(edge, ctx)
    if not any(ctx.nodes[node_id].type == "final" for node_id in path):
        return None
    excluded = relation.get("excluded_action_ids", ())
    if any(not accepted.generated(unit) for unit in excluded):
        return None
    if excluded and set().union(*(accepted.generated(unit) for unit in excluded)) & path:
        return None
    return (f"{edge.source}->{edge.target}",
            {"source_condition_numbers": sorted(condition),
             "outcome_edge_label": edge.label,
             "terminal_node_ids": sorted(node_id for node_id in path
                                         if ctx.nodes[node_id].type == "final"),
             "excluded_action_ids_checked": list(excluded),
             "accepted_action_match_used_for_target": False})


def score_control_relations_shared_owner_v4(
    control: Mapping[str, Any], graph: EvalGraph,
    alignment: ActionAlignmentTable | ControlAnchorEvidence,
    assigned_nodes: Mapping[str, str | None], reference_evidence: Mapping[str, Any],
    reviewed: SemanticInventory,
    *, owner_alternatives: Mapping[str, frozenset[str | None]] | None = None,
) -> ControlComponentResult:
    baseline = score_control_relations_local_evidence_v3(
        control, graph, alignment, assigned_nodes, reference_evidence, reviewed,
        owner_alternatives=owner_alternatives,
    )
    if control["no_control"]:
        return baseline
    required = {item["fact_id"]: item for item in control["control_relations"]
                if item["status"] == "required"}
    ctx = _Context(graph, alignment)
    accepted = alignment.action if isinstance(alignment, ControlAnchorEvidence) else alignment
    replacements = {}
    for fact in baseline.facts:
        relation = required.get(fact.fact_id)
        if (fact.status != "indeterminate_alignment" or relation is None
            or relation["type"] not in {"decision_branch", "termination"}):
            continue
        owner = assigned_nodes.get(relation["source_control_fact"])
        if owner in {None, "implicit", "indeterminate"} or not _shared_owner(
            relation["source_control_fact"], owner, control, graph, assigned_nodes
        ):
            continue
        observed = _explicit_terminal_branch(
            relation, owner, control, graph, ctx, reviewed, accepted)
        if observed is None:
            continue
        edge_id, evidence = observed
        replacements[fact.fact_id] = replace(
            fact, status="TP", generated_node_id=owner,
            reason="explicit shared-owner terminal branch reaches final without excluded work",
            diagnostics={"reason_code": "CONTROL_RELATION_SHARED_OWNER_TERMINAL_V4",
                         "guarded_edge": edge_id,
                         "routing_checked": True,
                         **evidence},
        )
    if not replacements:
        return baseline
    facts = tuple(replacements.get(fact.fact_id, fact) for fact in baseline.facts)
    coverage = list(_relation_coverage(control, graph, ctx, assigned_nodes,
                                       reference_evidence, facts))
    for fact in replacements.values():
        edge_id = fact.diagnostics["guarded_edge"]
        for index, atom in enumerate(coverage):
            if (atom["role"] == "outgoing_control"
                and f"{atom['source']}->{atom['target']}" == edge_id):
                coverage[index] = {**atom, "status": "MATCHED",
                                   "source_fact_ids": sorted(set(atom["source_fact_ids"]) | {fact.fact_id})}
    result = replace(
        baseline,
        counts=Counts(sum(f.status == "TP" for f in facts), baseline.counts.fp,
                      sum(f.status in {"FN", "FN+FP"} for f in facts)),
        facts=facts,
        candidate_abstention_count=sum(f.status == "indeterminate_alignment" for f in facts),
        fp_abstention_count=sum(item["status"] == "FP_ABSTAIN" for item in coverage),
        generated_relation_coverage=tuple(coverage),
    )
    result.to_dict()
    return result
