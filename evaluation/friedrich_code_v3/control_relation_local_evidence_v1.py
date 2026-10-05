"""Versioned Control Relation fallback for unmatched Action targets.

The frozen scorer remains authoritative whenever its relevant Action anchors
are accepted. This component only revisits relations whose target evidence is
unavailable; a reliable Control Node owner is still mandatory for a TP.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from evaluation.friedrich_v3.core import Counts, EvalGraph, normalize_label
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory

from .action_operation_guard_v2 import main_operations
from .alignment import ActionAlignmentTable
from .anchor_evidence import ControlAnchorEvidence
from .control import (
    ControlComponentResult, ControlFactResult, _Context, _guard_hard_conflict,
    _guard_matches, _guard_tokens, _relation_coverage, score_control_relations,
)


VERSION = "friedrich-code-control-relation-local-evidence/1"
_OUTCOMES = {"approval", "rejection"}
_OUTCOME_GUARDS = {"approval": "approve", "rejection": "reject"}
_FILLER = {"a", "an", "the", "another", "respective", "to", "of", "for", "in",
           "and", "is", "are", "was", "were", "by", "from", "applicant", "employee"}


def _guard_equivalent(edge: Any, relation: Mapping[str, Any], reference: Mapping[str, Any]) -> bool:
    if _guard_matches(edge, relation, reference):
        return True
    if _guard_hard_conflict(relation.get("guard_meaning"), edge.label):
        return False
    # "not previously advised" and "not advised" have the same explicit
    # polarity and predicate. No broader guard similarity is inferred.
    source = _guard_tokens(relation.get("guard_meaning")) - {"previously", "already"}
    candidate = _guard_tokens(edge.label) - {"previously", "already"}
    return bool(source and source == candidate and "not" in source)


def _branch_nodes(edge: Any, ctx: _Context) -> set[str]:
    # Stop before a shared Merge/Join so post-convergence work cannot be
    # mistaken for evidence of one particular branch.
    seen: set[str] = set()
    pending = [edge.target]
    while pending:
        node_id = pending.pop()
        if node_id in seen or ctx.nodes[node_id].type in {"merge", "join"}:
            continue
        seen.add(node_id)
        pending.extend(ctx.outgoing[node_id])
    return seen


def _local_target_nodes(
    unit_id: str, nodes: set[str], ctx: _Context, reviewed: SemanticInventory,
) -> set[str]:
    """Find explicit branch continuation, without accepting an Action match.

    A performed operation and distinctive business-object wording must both
    agree. This evidence is used only for relation behavior, never Action TP.
    """
    unit = next((item for item in reviewed.units if item.semantic_unit_id == unit_id), None)
    if unit is None:
        return set()
    operation = main_operations(unit.canonical_meaning)
    subject = _guard_tokens(unit.business_object) - _FILLER
    if not operation or not subject:
        return set()
    matches = set()
    for node_id in nodes:
        node = ctx.nodes[node_id]
        if node.type != "action" or not (operation & main_operations(node.label or "")):
            continue
        candidate = _guard_tokens(node.label) - _FILLER
        if subject <= candidate or (len(subject) >= 2 and len(subject & candidate) >= 2):
            matches.add(node_id)
    return matches


def _verdict(
    relation: Mapping[str, Any], owner: str, ctx: _Context,
    reference: Mapping[str, Any], reviewed: SemanticInventory,
    control: Mapping[str, Any],
) -> tuple[str, str, Mapping[str, Any]]:
    edges = ctx.branch_edges(owner)
    kind = relation["type"]
    guard_edges = [edge for edge in edges if _guard_equivalent(edge, relation, reference)]
    if kind not in {"decision_branch", "termination"} or len(guard_edges) != 1:
        return ("indeterminate_alignment", "unique explicit guarded path not established",
                {"guard_edge_count": len(guard_edges)})
    edge = guard_edges[0]
    path = _branch_nodes(edge, ctx)
    target_ids = relation.get("target_action_ids", [])
    if len(target_ids) != 1:
        return ("indeterminate_alignment", "single source target meaning not established",
                {"guarded_edge": f"{edge.source}->{edge.target}"})
    target_id = target_ids[0]
    local = _local_target_nodes(target_id, path, ctx, reviewed)
    other_local = {other.source + "->" + other.target: _local_target_nodes(
        target_id, _branch_nodes(other, ctx), ctx, reviewed)
        for other in edges if other != edge}
    evidence = {"guarded_edge": f"{edge.source}->{edge.target}",
                "local_continuation_node_ids": sorted(local),
                "other_branch_continuation_node_ids": {
                    key: sorted(value) for key, value in other_local.items()},
                "accepted_action_match_used": False}
    if kind == "decision_branch":
        # The correct guard cannot license a branch carrying a continuation
        # explicitly reserved for a different source guard, or work that a
        # same-guard termination fact explicitly excludes.
        for sibling in control["control_relations"]:
            if (sibling is relation or sibling["status"] != "required"
                or sibling["source_control_fact"] != relation["source_control_fact"]):
                continue
            sibling_guard = normalize_label(sibling.get("guard_meaning"))
            current_guard = normalize_label(relation.get("guard_meaning"))
            if sibling_guard == current_guard:
                if ctx.mapped(sibling.get("excluded_action_ids", [])) & path:
                    return "FN+FP", "excluded work occurs on this guarded branch", evidence
                continue
            if sibling_guard and any(
                _local_target_nodes(unit, path, ctx, reviewed)
                for unit in sibling.get("target_action_ids", [])
                if not (main_operations(next((item.canonical_meaning for item in reviewed.units
                                              if item.semantic_unit_id == unit), "")) & _OUTCOMES)
            ):
                return "FN+FP", "other source branch continuation occurs here", evidence
        unit = next((item for item in reviewed.units if item.semantic_unit_id == target_id), None)
        outcome = main_operations(unit.canonical_meaning) if unit else frozenset()
        owner_ops = main_operations(ctx.nodes[owner].label or "")
        owner_words = _guard_tokens(ctx.nodes[owner].label)
        operation_word = {_OUTCOME_GUARDS[item] for item in outcome & _OUTCOMES}
        explicit_outcome = (bool(operation_word)
                            and bool(outcome & owner_ops or operation_word & owner_words)
                            and bool(outcome & main_operations(edge.label or "")
                                     or operation_word & _guard_tokens(edge.label)))
        distinct_branches = (len(edges) >= 2 and all(normalize_label(other.label)
                            and not _guard_equivalent(other, relation, reference)
                            for other in edges if other != edge))
        if explicit_outcome and distinct_branches and any(
            ctx.nodes[node_id].type == "action" for node_id in path
        ) and not local and not any(other_local.values()):
            return "TP", "explicit decision outcome and unique continuing branch", evidence
        if len(local) == 1 and not any(other_local.values()):
            return "TP", "guard and explicit branch continuation agree", evidence
        if not local and any(other_local.values()):
            return "FN+FP", "required continuation is on a different branch", evidence
        return "indeterminate_alignment", "guarded continuation is not uniquely established", evidence
    # A termination claim needs a visible branch-local continuation, a final
    # endpoint, and absence of success-only work on that route.
    excluded = ctx.mapped(relation.get("excluded_action_ids", []))
    finals = {node.id for node in ctx.graph.nodes if node.type == "final"}
    full_path = {edge.target} | set(ctx.closure[edge.target])
    if len(local) == 1 and excluded & path:
        return "FN+FP", "excluded work occurs on the termination branch", evidence
    if len(local) == 1 and finals & full_path and not (excluded & full_path):
        return "TP", "guarded return reaches final without excluded work", evidence
    if not local and any(other_local.values()):
        return "FN+FP", "required termination continuation is on another branch", evidence
    return "indeterminate_alignment", "termination behavior is not uniquely observable", evidence


def score_control_relations_local_evidence_v1(
    control: Mapping[str, Any], graph: EvalGraph,
    alignment: ActionAlignmentTable | ControlAnchorEvidence,
    assigned_nodes: Mapping[str, str | None], reference_evidence: Mapping[str, Any],
    reviewed: SemanticInventory,
    *, owner_alternatives: Mapping[str, frozenset[str | None]] | None = None,
) -> ControlComponentResult:
    """Retain accepted-anchor outcomes; reconsider only unmatched-target facts."""
    baseline = score_control_relations(
        control, graph, alignment, assigned_nodes, reference_evidence,
        owner_alternatives=owner_alternatives)
    if control["no_control"]:
        return baseline
    required = {item["fact_id"]: item for item in control["control_relations"]
                if item["status"] == "required"}
    ctx = _Context(graph, alignment)
    accepted_action = alignment.action if isinstance(alignment, ControlAnchorEvidence) else alignment
    new_facts: list[ControlFactResult] = []
    for fact in baseline.facts:
        relation = required.get(fact.fact_id)
        if relation is None:
            new_facts.append(fact)
            continue
        targets = relation.get("target_action_ids", [])
        if not targets or all(accepted_action.generated(unit) for unit in targets):
            new_facts.append(fact)
            continue
        owner = assigned_nodes.get(relation["source_control_fact"])
        if owner is None or owner == "implicit":
            new_facts.append(fact)
            continue
        if owner == "indeterminate":
            status, reason, evidence = (
                "indeterminate_alignment", "Control Node owner is not uniquely identified",
                {"owner_alternatives": sorted(
                    owner_alternatives.get(relation["source_control_fact"], frozenset())
                    if owner_alternatives else (), key=lambda value: "" if value is None else value)})
            generated = None
        else:
            status, reason, evidence = _verdict(relation, owner, ctx, reference_evidence,
                                                reviewed, control)
            generated = owner
        new_facts.append(replace(
            fact, status=status, generated_node_id=generated, reason=reason,
            diagnostics={**dict(fact.diagnostics), **evidence,
                         "reason_code": "CONTROL_RELATION_LOCAL_EVIDENCE_V1",
                         "unmatched_target_action_ids": sorted(
                             unit for unit in targets if not accepted_action.generated(unit))},
        ))
    # A single logical owner/guard contradiction contributes at most one FP.
    # Keep every frozen accepted-target status, and demote only a newly added
    # duplicate contradiction to FN.
    seen_fp = {
        (required[f.fact_id]["source_control_fact"],
         required[f.fact_id].get("guard_meaning") or f.fact_type)
        for f in new_facts if f.status == "FN+FP"
        and f.diagnostics.get("reason_code") != "CONTROL_RELATION_LOCAL_EVIDENCE_V1"}
    deduplicated: list[ControlFactResult] = []
    for fact in new_facts:
        if (fact.status == "FN+FP"
            and fact.diagnostics.get("reason_code") == "CONTROL_RELATION_LOCAL_EVIDENCE_V1"):
            key = (required[fact.fact_id]["source_control_fact"],
                   required[fact.fact_id].get("guard_meaning") or fact.fact_type)
            if key in seen_fp:
                fact = replace(fact, status="FN")
            else:
                seen_fp.add(key)
        deduplicated.append(fact)
    facts = tuple(deduplicated)
    coverage = list(_relation_coverage(control, graph, ctx, assigned_nodes,
                                       reference_evidence, facts))
    # Frozen atom attribution uses accepted Action targets. Attribute a newly
    # established local relation to its explicit guard edge instead.
    for fact in facts:
        if fact.status != "TP" or fact.diagnostics.get("reason_code") != "CONTROL_RELATION_LOCAL_EVIDENCE_V1":
            continue
        edge_id = fact.diagnostics.get("guarded_edge")
        if not edge_id:
            continue
        for index, atom in enumerate(coverage):
            if (atom["role"] == "outgoing_control"
                and f"{atom['source']}->{atom['target']}" == edge_id):
                coverage[index] = {**atom, "status": "MATCHED",
                                   "source_fact_ids": sorted(set(atom["source_fact_ids"]) | {fact.fact_id})}
    coverage = tuple(coverage)
    attributed = {fact_id for item in coverage if item["status"] == "CONTRADICTION_ACCOUNTED"
                  for fact_id in item["source_fact_ids"]}
    unattributed = tuple({
        "source_fact_id": fact.fact_id, "owner_generated_node_id": fact.generated_node_id,
        "reason": fact.reason,
        "attribution": "no single generated relation atom represents this scored local contradiction",
    } for fact in facts if fact.status == "FN+FP" and fact.fact_id not in attributed)
    result = replace(
        baseline,
        counts=Counts(sum(f.status == "TP" for f in facts),
                      len({(required[f.fact_id]["source_control_fact"],
                            required[f.fact_id].get("guard_meaning") or f.fact_type)
                           for f in facts if f.status == "FN+FP"})
                      + sum(f.status == "FP" for f in facts),
                      sum(f.status in {"FN", "FN+FP"} for f in facts)),
        facts=facts,
        candidate_abstention_count=sum(f.status == "indeterminate_alignment" for f in facts),
        fp_abstention_count=sum(item["status"] == "FP_ABSTAIN" for item in coverage),
        generated_relation_coverage=coverage,
        unattributed_contradictions=unattributed,
    )
    result.to_dict()  # Enforce fixed-denominator and null-F1 contract.
    return result
