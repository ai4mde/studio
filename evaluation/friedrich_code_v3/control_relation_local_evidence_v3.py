"""Versioned Control Relation evidence for guarded paths and loop behavior.

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
    NODE_TYPES, ControlComponentResult, ControlFactResult, _Context, _guard_hard_conflict,
    _guard_matches, _guard_tokens, _relation_coverage, score_control_relations,
)
from .control_node_role_assignment_v3 import _role_strength


VERSION = "friedrich-code-control-relation-local-evidence/3"
_OUTCOMES = {"approval", "rejection"}
_OUTCOME_GUARDS = {"approval": "approve", "rejection": "reject"}
_FILLER = {"a", "an", "the", "another", "respective", "to", "of", "for", "in",
           "and", "is", "are", "was", "were", "by", "from", "applicant", "employee"}


def _owner_guard_words(value: str | None) -> set[str]:
    """Normalize inflection for explicit guard evidence, never general label overlap."""
    canonical = {"inconsistencies": "inconsistency", "exhibitions": "exhibition",
                 "initiated": "initiate", "initiates": "initiate", "initiating": "initiate"}
    return {canonical.get(word, word) for word in _guard_tokens(value)}


def _compound_owner_has_guard_evidence(
    node: Any, relation: Mapping[str, Any], ctx: _Context,
) -> bool:
    """Require the source branch condition on the candidate's local branch.

    Shared actor/object words in an unrelated Decision do not establish an
    owner. Inspect only the node, its outgoing guards, and local branch work.
    """
    guard = _owner_guard_words(relation.get("guard_meaning"))
    if not guard:
        return False
    local = _owner_guard_words(node.label)
    for edge in ctx.branch_edges(node.id):
        local.update(_owner_guard_words(edge.label))
        for node_id in _branch_nodes(edge, ctx):
            local.update(_owner_guard_words(ctx.nodes[node_id].label))
    return guard <= local


def _guard_equivalent(edge: Any, relation: Mapping[str, Any], reference: Mapping[str, Any]) -> bool:
    source_words = _guard_tokens(relation.get("guard_meaning"))
    edge_words = _guard_tokens(edge.label)
    # Preserve the polarity of the *same predicate* before token containment.
    # This does not equate the polarity of unrelated expressions such as
    # "no objection" and "approval".
    negative = {"no", "not"}
    if ((source_words - negative) & (edge_words - negative)
        and bool(source_words & negative) != bool(edge_words & negative)):
        return False
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
    *, guard_words: set[str] | None = None,
) -> set[str]:
    """Find explicit branch continuation, without accepting an Action match.

    A performed operation and distinctive business-object wording must both
    agree. This evidence is used only for relation behavior, never Action TP.
    """
    unit = next((item for item in reviewed.units if item.semantic_unit_id == unit_id), None)
    if unit is None:
        return set()
    operation = _performed_operations(unit.canonical_meaning)
    subject = _guard_tokens(unit.business_object) - _FILLER
    recipient = _guard_tokens(unit.recipient_participant) if unit.recipient_participant else set()
    if not operation or not subject:
        return set()
    matches = set()
    for node_id in nodes:
        node = ctx.nodes[node_id]
        if node.type not in {"action", "decision"} or not (operation & _performed_operations(node.label or "")):
            continue
        if node.type == "decision":
            # A control node can be evidence of branch continuation only when
            # it expressly performs the source operation.  A question about
            # whether some other activity should happen is not enough.
            words = (normalize_label(node.label) or "").split()
            if not words or words[0] not in {"evaluate", "assess", "check", "review"}:
                continue
        # The guard can carry the business condition while the continuation
        # names only the performed act and recipient (e.g. concurrence ->
        # inform suppliers).  Both pieces must be on the same branch.
        node_words = _guard_tokens(node.label)
        # Do not turn a communication to one party into evidence of notice to
        # all named parties just because the guarded condition is the same.
        if "all" in recipient and "all" not in node_words:
            continue
        candidate = (node_words | (guard_words or set())) - _FILLER
        if subject <= candidate or (len(subject) >= 2 and len(subject & candidate) >= 2):
            matches.add(node_id)
    return matches


def _performed_operations(label: str) -> frozenset[str]:
    operations = main_operations(label)
    if operations:
        return operations
    words = (normalize_label(label) or "").split()
    # 'request' is absent from the Action guard's operation vocabulary; here
    # it is only local evidence when used as an early performed verb.
    if any(word in {"request", "requests"} for word in words[:2]):
        return frozenset({"request"})
    return frozenset()


def _contextual_guard(
    edge: Any, relation: Mapping[str, Any], owner: str, ctx: _Context,
    reference: Mapping[str, Any], reviewed: SemanticInventory,
) -> bool:
    if _guard_equivalent(edge, relation, reference):
        return True
    if _guard_hard_conflict(relation.get("guard_meaning"), edge.label):
        return False
    source_words = _guard_tokens(relation.get("guard_meaning"))
    edge_words = _guard_tokens(edge.label)
    owner_words = _guard_tokens(ctx.nodes[owner].label)
    if not source_words or not edge_words or not source_words <= owner_words:
        return False
    if not (source_words & edge_words):
        return False
    targets = relation.get("target_action_ids", [])
    if len(targets) != 1:
        return False
    # Require the uniquely routed source continuation, not a loose synonym
    # lookup between "requested" and "required" in arbitrary contexts.
    path = _branch_nodes(edge, ctx)
    return len(_local_target_nodes(targets[0], path, ctx, reviewed)) == 1


def _cycle_branch_nodes(edge: Any, owner: str, ctx: _Context) -> set[str]:
    seen: set[str] = set()
    pending = [edge.target]
    while pending:
        node_id = pending.pop()
        if node_id in seen or node_id == owner or ctx.nodes[node_id].type in {"merge", "join"}:
            continue
        seen.add(node_id)
        pending.extend(ctx.outgoing[node_id])
    return seen


def _loop_verdict(
    relation: Mapping[str, Any], owner: str, ctx: _Context,
    reviewed: SemanticInventory,
) -> tuple[str, str, Mapping[str, Any]]:
    if not ctx.cycles:
        return ("FN", "required recurrence is absent from the acyclic candidate graph",
                {"cycle_edge_count": 0, "candidate_graph_acyclic": True})
    cycle_edges = [edge for edge in ctx.branch_edges(owner)
                   if owner in ({edge.target} | ctx.closure[edge.target])]
    if not cycle_edges:
        return ("FN", "no recurrence path returns to the identified owner",
                {"cycle_edge_count": 0, "candidate_graph_acyclic": False})
    if len(cycle_edges) != 1:
        return ("indeterminate_alignment", "unique source-relevant recurrence path not established",
                {"cycle_edge_count": len(cycle_edges)})
    edge = cycle_edges[0]
    path = _cycle_branch_nodes(edge, owner, ctx)
    owner_words = _guard_tokens(ctx.nodes[owner].label)
    source_guard = _guard_tokens(relation.get("guard_meaning"))
    source_targets = relation.get("target_action_ids", [])
    units = {item.semantic_unit_id: item for item in reviewed.units}
    source_object_words = set().union(*(
        _guard_tokens(units[unit].business_object) for unit in source_targets if unit in units
    )) if source_targets else set()
    repeat_label = bool(_guard_tokens(edge.label) & {"retry", "repeat"})
    source_context = bool(source_guard & owner_words or source_object_words & owner_words)
    evidence = {"cycle_edge": f"{edge.source}->{edge.target}",
                "cycle_path_node_ids": sorted(path),
                "source_guard_supported_by_owner": bool(source_guard & owner_words),
                "accepted_action_match_used": False}
    if not repeat_label or not source_context:
        return "indeterminate_alignment", "retry label alone does not establish the source loop", evidence
    # A source-specific next-person/item iteration is not the same as a
    # correction cycle that resends work to the same participant.
    next_required = bool(source_guard & {"another", "next"}) or any(
        "next" in _guard_tokens(units[unit].canonical_meaning)
        for unit in source_targets if unit in units
    )
    if next_required and not any(
        "next" in _guard_tokens(ctx.nodes[node].label) for node in path
    ):
        return "FN", "correction retry does not route to the required next participant", evidence
    matched = set().union(*(
        _local_target_nodes(unit, path, ctx, reviewed) for unit in source_targets
    )) if source_targets else set()
    # A repeated act may have a distinct occurrence from its accepted initial
    # Action match.  Explicit 'repeat <same business object>' is relation-only
    # evidence and does not alter Action completeness.
    if not matched:
        for unit in source_targets:
            if unit not in units:
                continue
            object_words = _guard_tokens(units[unit].business_object) - _FILLER
            matched.update(node_id for node_id in path
                           if ctx.nodes[node_id].type == "action"
                           and "repeat" in _guard_tokens(ctx.nodes[node_id].label)
                           and object_words and object_words <= _guard_tokens(ctx.nodes[node_id].label))
    evidence["local_repeated_node_ids"] = sorted(matched)
    if len(matched) == 1 or (len(matched) > 1 and all(
        ctx.nodes[node].type == "action" for node in matched
    )):
        return "TP", "unique retry route repeats source-specific work and returns to check", evidence
    return "indeterminate_alignment", "source-specific repeated work is not established", evidence


def _loop_exit_verdict(
    relation: Mapping[str, Any], owner: str, ctx: _Context,
    alignment: ActionAlignmentTable | ControlAnchorEvidence,
) -> tuple[str, str, Mapping[str, Any]] | None:
    cycle_edges = [edge for edge in ctx.branch_edges(owner)
                   if owner in ({edge.target} | ctx.closure[edge.target])]
    exit_edges = [edge for edge in ctx.branch_edges(owner)
                  if owner not in ({edge.target} | ctx.closure[edge.target])]
    if len(cycle_edges) != 1 or len(exit_edges) != 1:
        return None
    edge = exit_edges[0]
    path = {edge.target} | ctx.closure[edge.target]
    evidence = {"exit_edge": f"{edge.source}->{edge.target}",
                "accepted_action_match_used": False}
    targets = relation.get("target_action_ids", [])
    if not targets and "beyond described scope" in (relation.get("terminal_outcome") or ""):
        if any(ctx.nodes[node].type == "final" for node in path):
            return ("indeterminate_alignment", "final may be a scope boundary or premature termination",
                    evidence)
    if len(targets) >= 2:
        first, later = targets[0], targets[1:]
        if not alignment.generated(first) and any(
            ctx.mapped([unit]) & path for unit in later
        ):
            return ("FN", "exit branch bypasses the required earlier continuation",
                    evidence)
    return None


def _verdict(
    relation: Mapping[str, Any], owner: str, ctx: _Context,
    reference: Mapping[str, Any], reviewed: SemanticInventory,
    control: Mapping[str, Any],
) -> tuple[str, str, Mapping[str, Any]]:
    edges = ctx.branch_edges(owner)
    kind = relation["type"]
    if kind == "loop_recurrence":
        return _loop_verdict(relation, owner, ctx, reviewed)
    guard_edges = [edge for edge in edges
                   if _contextual_guard(edge, relation, owner, ctx, reference, reviewed)]
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
    local = _local_target_nodes(target_id, path, ctx, reviewed,
                                guard_words=_guard_tokens(edge.label))
    other_local = {other.source + "->" + other.target: _local_target_nodes(
        target_id, _branch_nodes(other, ctx), ctx, reviewed,
        guard_words=_guard_tokens(other.label))
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


def score_control_relations_local_evidence_v3(
    control: Mapping[str, Any], graph: EvalGraph,
    alignment: ActionAlignmentTable | ControlAnchorEvidence,
    assigned_nodes: Mapping[str, str | None], reference_evidence: Mapping[str, Any],
    reviewed: SemanticInventory,
    *, owner_alternatives: Mapping[str, frozenset[str | None]] | None = None,
) -> ControlComponentResult:
    """Retain valid accepted-anchor outcomes; revisit explicit local Control evidence."""
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
        kind = relation["type"]
        incomplete_targets = bool(targets) and not all(
            accepted_action.generated(unit) for unit in targets)
        revisit_repeat = kind == "loop_recurrence" and fact.status in {
            "FN", "indeterminate_alignment"}
        revisit_exit = kind == "loop_exit" and fact.status in {
            "FN", "indeterminate_alignment"}
        if not incomplete_targets and not revisit_repeat and not revisit_exit:
            new_facts.append(fact)
            continue
        owner = assigned_nodes.get(relation["source_control_fact"])
        if kind == "loop_recurrence" and not ctx.cycles:
            new_facts.append(replace(
                fact, status="FN", generated_node_id=None,
                reason="required recurrence is absent from the acyclic candidate graph",
                diagnostics={**dict(fact.diagnostics),
                             "reason_code": "CONTROL_RELATION_ABSENT_LOOP_V3",
                             "candidate_graph_acyclic": True,
                             "accepted_action_match_used": False},
            ))
            continue
        if owner is None or owner == "implicit":
            source_owner = next((node for node in control["control_nodes"]
                                 if node["fact_id"] == relation["source_control_fact"]), None)
            if (owner is None and incomplete_targets and source_owner is not None
                and kind == "decision_branch"
                and any(node.type == NODE_TYPES[source_owner["type"]]
                        and _role_strength(source_owner, node, graph) >= 2
                        and len(ctx.branch_edges(node.id)) >= 2
                        and _compound_owner_has_guard_evidence(node, relation, ctx)
                        for node in graph.nodes)):
                new_facts.append(replace(
                    fact, status="indeterminate_alignment", generated_node_id=None,
                    reason="plausible compound Control owner, but relation role is not uniquely established",
                    diagnostics={"reason_code": "CONTROL_RELATION_COMPOUND_OWNER_UNRESOLVED_V3",
                                 "accepted_action_match_used": False},
                ))
                continue
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
            exit_result = (_loop_exit_verdict(relation, owner, ctx, accepted_action)
                           if kind == "loop_exit" else None)
            if exit_result is not None:
                status, reason, evidence = exit_result
            elif kind == "loop_exit":
                new_facts.append(fact)
                continue
            else:
                status, reason, evidence = _verdict(
                    relation, owner, ctx, reference_evidence, reviewed, control)
            generated = owner
        new_facts.append(replace(
            fact, status=status, generated_node_id=generated, reason=reason,
            diagnostics={**dict(fact.diagnostics), **evidence,
                         "reason_code": "CONTROL_RELATION_LOCAL_EVIDENCE_V3",
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
        and f.diagnostics.get("reason_code") != "CONTROL_RELATION_LOCAL_EVIDENCE_V3"}
    deduplicated: list[ControlFactResult] = []
    for fact in new_facts:
        if (fact.status == "FN+FP"
            and fact.diagnostics.get("reason_code") == "CONTROL_RELATION_LOCAL_EVIDENCE_V3"):
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
        if fact.status != "TP" or fact.diagnostics.get("reason_code") != "CONTROL_RELATION_LOCAL_EVIDENCE_V3":
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
