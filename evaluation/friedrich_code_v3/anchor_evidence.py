"""Auditable Control-only anchors, kept separate from locked V2 Action scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from evaluation.friedrich_v3.action import (
    ACTION_SIMILARITY_THRESHOLD, REFERENCE_RELATIVE_DELTA,
    SimilarityProvider, compatibility_veto,
)
from evaluation.friedrich_v3.core import EvalGraph, normalize_label, reachable, strongly_connected_components
from evaluation.friedrich_semantic.action import (
    _best_source_evidence, _compound, _generated_source_supported, _passages, _tokens,
)
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory

from .alignment import ActionAlignmentTable
from .reference import reference_graph


@dataclass(frozen=True, slots=True)
class ControlAnchorEvidence:
    action: ActionAlignmentTable
    control_only_units: Mapping[str, frozenset[str]]
    occurrences: Mapping[str, frozenset[str]]
    indeterminate_units: frozenset[str]
    indeterminate_occurrences: frozenset[str]
    occurrence_evidence: Mapping[str, Mapping[str, Any]] | None = None

    def generated(self, unit_id: str) -> frozenset[str]:
        return self.action.generated(unit_id) | self.control_only_units.get(unit_id, frozenset())

    def is_ambiguous(self, unit_id: str) -> bool:
        # Text-only alternatives are tested against Control structure first.
        return self.action.is_ambiguous(unit_id)

    def occurrence_generated(self, occurrence_id: str) -> frozenset[str]:
        return self.occurrences.get(occurrence_id, frozenset())

    def occurrence_is_ambiguous(self, occurrence_id: str) -> bool:
        return occurrence_id in self.indeterminate_occurrences

    def to_dict(self) -> dict[str, Any]:
        return {
            "control_only_unit_to_generated": {
                key: sorted(value) for key, value in sorted(self.control_only_units.items())
            },
            "occurrence_to_generated": {
                key: sorted(value) for key, value in sorted(self.occurrences.items())
            },
            "indeterminate_unit_ids": sorted(self.indeterminate_units),
            "indeterminate_occurrence_ids": sorted(self.indeterminate_occurrences),
            "occurrence_evidence": dict(self.occurrence_evidence or {}),
            "action_mappings_unchanged": True,
        }


def build_control_anchor_evidence(
    reviewed: SemanticInventory, generated: EvalGraph, action: ActionAlignmentTable,
    similarity: SimilarityProvider, source_text: str,
    *, control: Mapping[str, Any] | None = None,
    reference_evidence: Mapping[str, Any] | None = None,
) -> ControlAnchorEvidence:
    """Reuse V2 compatibility, grounding and threshold for reviewed text-only units.

    A Control-only match cannot consume or replace an accepted Action mapping.
    Competing non-equivalent matches are indeterminate until structure resolves them.
    """
    eligible = [o for o in reviewed.occurrences if o.evidence_status == "text_only"
                and o.provenance.review_state in {"accepted", "modified"}]
    units = {u.semantic_unit_id: u for u in reviewed.units
             if u.provenance.review_state in {"accepted", "modified"}}
    eligible = [o for o in eligible if o.semantic_unit_id in units]
    generated_actions = sorted((n for n in generated.nodes if n.type == "action"), key=lambda n: n.id)
    labels = [n.label or "" for n in generated_actions]
    unit_ids = sorted({o.semantic_unit_id for o in eligible})
    meanings = [units[unit_id].canonical_meaning for unit_id in unit_ids]
    scores = similarity.matrix(meanings, labels) if meanings and labels else [[] for _ in meanings]
    if len(scores) != len(meanings) or any(len(row) != len(labels) for row in scores):
        raise ValueError("Similarity provider returned invalid Control anchor matrix")
    passages = _passages(source_text)
    _, source_scores, lexical_scores = _best_source_evidence(labels, passages, similarity)
    control_only: dict[str, frozenset[str]] = {}
    indeterminate_units: set[str] = set()
    occupied = {node for nodes in action.unit_to_generated.values() for node in nodes}
    for unit_id, meaning, row in zip(unit_ids, meanings, scores):
        candidates: list[tuple[float, str]] = []
        for index, node in enumerate(generated_actions):
            if not _generated_source_supported(source_scores[index], lexical_scores[index]):
                continue
            if row[index] < ACTION_SIMILARITY_THRESHOLD:
                continue
            if not compatibility_veto(meaning, node.label or "").compatible:
                continue
            if node.id in occupied and node.id not in action.generated(unit_id):
                if not _compound(node.label):
                    continue
                # A shared compound Action must contain the claimed component.
                meaning_tokens = set((normalize_label(meaning) or "").split())
                node_tokens = set((normalize_label(node.label) or "").split())
                if len(meaning_tokens & node_tokens) < 2:
                    continue
            candidates.append((row[index], node.id))
        if candidates:
            best = max(score for score, _ in candidates)
            candidates = [(score, node_id) for score, node_id in candidates
                          if score >= best - REFERENCE_RELATIVE_DELTA]
            operation = next(iter(_tokens(units[unit_id].operation.split()[0])), None)
            if operation:
                explicit = [(score, node_id) for score, node_id in candidates
                            if operation in _tokens(generated.by_id[node_id].label)]
                if explicit:
                    candidates = explicit
        if candidates:
            control_only[unit_id] = frozenset(node_id for _, node_id in candidates)
        if len(candidates) > 1:
            # No semantic winner is selected before structural matching.
            indeterminate_units.add(unit_id)

    occurrences: dict[str, frozenset[str]] = {}
    indeterminate_occurrences: set[str] = set()
    by_unit: dict[str, list[Any]] = {}
    for occurrence in eligible:
        by_unit.setdefault(occurrence.semantic_unit_id, []).append(occurrence)
    for unit_id, group in by_unit.items():
        mapped = control_only.get(unit_id, frozenset())
        if len(group) == 1:
            occurrences[group[0].occurrence_id] = mapped
            continue
        # One loop-carried Action can be observed on initial and repeat visits.
        if len(mapped) == 1:
            node = next(iter(mapped))
            for occurrence in group:
                occurrences[occurrence.occurrence_id] = (
                    mapped if occurrence.recurrence_role != "repeated"
                    or node in reachable(generated, node) else frozenset()
                )
        elif len(mapped) == 2 and {o.recurrence_role for o in group} == {"initial", "repeated"}:
            left, right = sorted(mapped)
            if right in reachable(generated, left) and left not in reachable(generated, right):
                order = (left, right)
            elif left in reachable(generated, right) and right not in reachable(generated, left):
                order = (right, left)
            else:
                order = ()
            if order:
                for occurrence in group:
                    occurrences[occurrence.occurrence_id] = frozenset({
                        order[0 if occurrence.recurrence_role == "initial" else 1]
                    })
            else:
                indeterminate_occurrences.update(o.occurrence_id for o in group)
        else:
            indeterminate_occurrences.update(o.occurrence_id for o in group)
    for occurrence in reviewed.occurrences:
        if occurrence.evidence_status == "text_and_reference" and occurrence.reference_node_ids:
            mapped = {
                generated_id for entry in action.entries
                if set(entry.reference_ids) & set(occurrence.reference_node_ids)
                for generated_id in entry.generated_ids
            }
            occurrences[occurrence.occurrence_id] = frozenset(mapped)
    # Reference-backed occurrences can share one semantic unit. Preserve their
    # initial/repeated identities instead of copying one unit-level mapping to
    # every visit without a candidate-side phase witness.
    for unit_id in {item.semantic_unit_id for item in reviewed.occurrences}:
        visits = [item for item in reviewed.occurrences
                  if item.semantic_unit_id == unit_id
                  and item.provenance.review_state in {"accepted", "modified"}]
        if len(visits) < 2 or not any(item.evidence_status == "text_and_reference" for item in visits):
            continue
        if {item.recurrence_role for item in visits} != {"initial", "repeated"}:
            continue
        candidates = set().union(*(occurrences.get(item.occurrence_id, frozenset()) for item in visits))
        if len(candidates) == 1:
            node = next(iter(candidates))
            if node not in reachable(generated, node):
                indeterminate_occurrences.update(item.occurrence_id for item in visits)
        elif len(candidates) == 2:
            first, second = sorted(candidates)
            if second in reachable(generated, first) and first not in reachable(generated, second):
                order = first, second
            elif first in reachable(generated, second) and second not in reachable(generated, first):
                order = second, first
            else:
                order = ()
            if order:
                for visit in visits:
                    selected = order[0 if visit.recurrence_role == "initial" else 1]
                    # Source-reference overlap is locked evidence. Candidate
                    # order can select among its possibilities, never replace
                    # a reference-backed occurrence with a different Action.
                    occurrences[visit.occurrence_id] &= frozenset({selected})
            else:
                indeterminate_occurrences.update(item.occurrence_id for item in visits)
        else:
            indeterminate_occurrences.update(item.occurrence_id for item in visits)
    for unit_id in {item.semantic_unit_id for item in reviewed.occurrences}:
        ordered = sorted((item for item in reviewed.occurrences
                          if item.semantic_unit_id == unit_id
                          and item.provenance.review_state in {"accepted", "modified"}),
                         key=lambda item: item.occurrence_index)
        for earlier, later in zip(ordered, ordered[1:]):
            if (earlier.loop_scope_ids or later.loop_scope_ids
                or earlier.branch_scope_ids or later.branch_scope_ids):
                continue
            first = occurrences.get(earlier.occurrence_id, frozenset())
            second = occurrences.get(later.occurrence_id, frozenset())
            if not first or not second:
                continue
            ordered_later = frozenset(
                node for node in second
                if any(node != previous and node in reachable(generated, previous)
                       and previous not in reachable(generated, node)
                       for previous in first)
            )
            occurrences[later.occurrence_id] = ordered_later
    evidence_log: dict[str, Mapping[str, Any]] = {}
    if control is not None and reference_evidence is not None:
        for occurrence in reviewed.occurrences:
            if occurrence.occurrence_id not in occurrences:
                continue
            passed: set[str] = set()
            details: dict[str, Any] = {}
            for node_id in occurrences[occurrence.occurrence_id]:
                valid, reasons = _occurrence_scope_matches(
                    occurrence, node_id, generated, action, control, reference_evidence, reviewed,
                )
                details[node_id] = reasons
                if valid:
                    passed.add(node_id)
            occurrences[occurrence.occurrence_id] = frozenset(passed)
            evidence_log[occurrence.occurrence_id] = details
        for unit_id in tuple(control_only):
            valid_occurrence_nodes = set().union(*(
                occurrences.get(item.occurrence_id, frozenset())
                for item in eligible if item.semantic_unit_id == unit_id
            ))
            retained = control_only[unit_id] & valid_occurrence_nodes
            if retained:
                control_only[unit_id] = retained
            else:
                del control_only[unit_id]
        for unit_id, group in by_unit.items():
            selected = [occurrences.get(item.occurrence_id, frozenset()) for item in group]
            if selected and all(len(nodes) == 1 for nodes in selected) and len({
                next(iter(nodes)) for nodes in selected}) == len(selected):
                indeterminate_occurrences.difference_update(
                    item.occurrence_id for item in group)
    return ControlAnchorEvidence(action, control_only, occurrences,
                                 frozenset(indeterminate_units), frozenset(indeterminate_occurrences), evidence_log)


def _occurrence_scope_matches(
    occurrence: Any, node_id: str, graph: EvalGraph, action: ActionAlignmentTable,
    control: Mapping[str, Any], reference: Mapping[str, Any],
    reviewed: SemanticInventory | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Require every frozen occurrence scope and boundary before Control credit."""
    reasons: list[str] = []
    known_loops = {item["scope_id"] for item in reference.get("loop_scopes", [])}
    known_branches = {item["scope_id"] for item in reference.get("branch_scopes", [])}
    if any(item not in known_loops for item in occurrence.loop_scope_ids):
        raise ValueError(f"unknown frozen occurrence loop scope: {occurrence.occurrence_id}")
    if any(item not in known_branches for item in occurrence.branch_scope_ids):
        raise ValueError(f"unknown frozen occurrence branch scope: {occurrence.occurrence_id}")
    reference_nodes = {str(item["node_id"]) for item in reference.get("nodes", [])}
    for boundary in occurrence.boundary_constraints:
        if any(item not in reference_nodes for item in boundary.reference_element_ids):
            raise ValueError(f"unknown frozen occurrence boundary: {occurrence.occurrence_id}")
    components = strongly_connected_components(graph)
    cycle = next((component for component in components if node_id in component and
                  (len(component) > 1 or node_id in graph.outgoing[node_id])), frozenset())
    if occurrence.loop_scope_ids or occurrence.recurrence_role == "repeated":
        if not cycle:
            reasons.append("required loop scope is absent")
    mode = next((mode for fact in control["control_nodes"] + control["control_relations"]
                 for mode in fact.get("control_anchor_evidence", [])
                 if mode.get("kind") == "occurrence_anchor_set"
                 and occurrence.occurrence_id in mode.get("occurrence_ids", [])), None)
    if mode:
        same_cycle, cycle_reasons = _same_design_cycle(
            node_id, graph, action, control, mode, cycle,
            require_return=occurrence.recurrence_role == "repeated" or bool(occurrence.branch_scope_ids),
        )
        if not same_cycle:
            reasons.extend(cycle_reasons)
    else:
        if reviewed is None and (occurrence.branch_scope_ids or occurrence.boundary_constraints):
            reasons.append("reviewed occurrence structure is unavailable")
        elif reviewed is not None:
            for scope_id in occurrence.loop_scope_ids:
                scope = next(item for item in reference.get("loop_scopes", [])
                             if item["scope_id"] == scope_id)
                peers = _reference_element_anchors(
                    tuple(str(item) for item in scope.get("member_node_ids", ())),
                    reviewed, action)
                peers.discard(node_id)
                if peers and not peers & cycle:
                    reasons.append(f"candidate loop does not contain source-scope peers {scope_id}")
            for scope_id in occurrence.branch_scope_ids:
                if not _candidate_branch_scope_matches(
                    scope_id, node_id, graph, action, reference, reviewed
                ):
                    reasons.append(f"candidate branch does not establish source scope {scope_id}")
            for boundary in occurrence.boundary_constraints:
                if not _candidate_boundary_matches(
                    boundary, node_id, graph, action, reference, reviewed, cycle
                ):
                    reasons.append("candidate does not establish frozen boundary "
                                   f"{boundary.boundary_type}:{boundary.side}")
    return not reasons, tuple(reasons)


def _reference_element_anchors(
    reference_ids: list[str] | tuple[str, ...], reviewed: SemanticInventory,
    action: ActionAlignmentTable,
) -> set[str]:
    ids = set(reference_ids)
    return set().union(*(set(action.generated(occurrence.semantic_unit_id))
                         for occurrence in reviewed.occurrences
                         if ids & set(occurrence.reference_node_ids)
                         and occurrence.provenance.review_state in {"accepted", "modified"})) if ids else set()


def _path_before_join(graph: EvalGraph, start: str, target: str) -> bool:
    seen: set[str] = set()
    queue = [start]
    while queue:
        current = queue.pop()
        if current in seen:
            continue
        seen.add(current)
        if current == target:
            return True
        if graph.by_id[current].type in {"join", "merge"}:
            continue
        queue.extend(graph.outgoing[current])
    return False


def _candidate_branch_scope_matches(
    scope_id: str, node_id: str, graph: EvalGraph, action: ActionAlignmentTable,
    reference: Mapping[str, Any], reviewed: SemanticInventory,
) -> bool:
    scope = next(item for item in reference.get("branch_scopes", []) if item["scope_id"] == scope_id)
    branch_anchors = _reference_element_anchors(
        [str(scope["entry_target_id"])], reviewed, action)
    if not branch_anchors:
        return False
    gateway_type = "fork" if scope.get("gateway_type") == "Parallel" else "decision"
    for gateway in graph.nodes:
        if gateway.type != gateway_type or len(graph.outgoing[gateway.id]) < 2:
            continue
        matching = [edge for edge in graph.edges if edge.source == gateway.id
                    and _path_before_join(graph, edge.target, node_id)
                    and any(_path_before_join(graph, edge.target, anchor)
                            for anchor in branch_anchors)]
        if len(matching) != 1:
            continue
        if any(edge is not matching[0] and _path_before_join(graph, edge.target, node_id)
               for edge in graph.edges if edge.source == gateway.id):
            continue
        return True
    return False


def _candidate_boundary_matches(
    boundary: Any, node_id: str, graph: EvalGraph, action: ActionAlignmentTable,
    reference: Mapping[str, Any], reviewed: SemanticInventory,
    cycle: frozenset[str],
) -> bool:
    anchors = _reference_element_anchors(
        boundary.reference_element_ids, reviewed, action)
    side = boundary.side
    if anchors:
        if side == "before":
            return any(anchor != node_id and anchor in reachable(graph, node_id)
                       and node_id not in reachable(graph, anchor) for anchor in anchors)
        if side == "after":
            return any(anchor != node_id and node_id in reachable(graph, anchor)
                       and anchor not in reachable(graph, node_id) for anchor in anchors)
        if side == "internal":
            return bool(cycle and anchors & cycle)
    reference_nodes = {str(item["node_id"]): item for item in reference.get("nodes", [])}
    gateway_ids = [item for item in boundary.reference_element_ids
                   if reference_nodes[item].get("node_type") == "Gateway"]
    if boundary.boundary_type in {"loop", "recurrence"}:
        return bool(cycle)
    if not gateway_ids:
        return False
    expected = "fork" if boundary.boundary_type == "parallel" else "decision"
    for candidate in graph.nodes:
        if candidate.type != expected or len(graph.outgoing[candidate.id]) < 2:
            continue
        if side == "before" and candidate.id in reachable(graph, node_id):
            return True
        if side == "after" and node_id in reachable(graph, candidate.id):
            return True
        if side == "internal" and any(_path_before_join(graph, target, node_id)
                                      for target in graph.outgoing[candidate.id]):
            return True
    return False


def _same_design_cycle(
    combine_id: str, graph: EvalGraph, action: ActionAlignmentTable,
    control: Mapping[str, Any], mode: Mapping[str, Any], cycle: frozenset[str],
    *, require_return: bool,
) -> tuple[bool, tuple[str, ...]]:
    """Check the frozen 9-6 role: both revised designs meet before each combination."""
    reasons: list[str] = []
    required_ids = set(mode["occurrence_ids"])
    linked = [fact for fact in control["control_relations"]
              if fact["status"] == "required"
              and any(item.get("kind") == "occurrence_anchor_set"
                      and required_ids & set(item.get("occurrence_ids", []))
                      for item in fact.get("control_anchor_evidence", []))]
    incoming_units = sorted({unit for fact in linked for unit in fact.get("incoming_action_ids", [])})
    if len(incoming_units) != 2:
        raise ValueError("frozen same-design-cycle mode requires two incoming design units")
    units = [action.generated(unit) for unit in incoming_units]
    if any(not values for values in units):
        reasons.append("revised-design Action alignment is missing")
        return False, tuple(reasons)
    joins = [node for node in graph.nodes if node.type == "join"
             and combine_id in reachable(graph, node.id)]
    matching_join = False
    for join in joins:
        incoming = graph.incoming[join.id]
        if len(incoming) < 2:
            continue
        choices = [
            {edge for edge in incoming if any(edge == mapped or edge in reachable(graph, mapped, {combine_id})
                                            for mapped in unit_nodes)}
            for unit_nodes in units
        ]
        if any(left != right for left in choices[0] for right in choices[1]):
            matching_join = True
            break
    if not matching_join:
        reasons.append("both revised designs do not reach distinct Join inputs before combination")
    if cycle:
        if any(not (nodes & cycle) for nodes in units):
            reasons.append("revised designs and combination are not in one repeatable cycle")
    elif any(role == "repeated" for role in mode.get("occurrence_roles", {}).values()):
        reasons.append("combined-design recurrence cycle is absent")
    if require_return and cycle:
        recurrence = [fact for fact in control["control_relations"]
                      if fact["status"] == "required" and fact["type"] == "loop_recurrence"
                      and fact.get("target_mode") == "both_required_parallel_restart"]
        if len(recurrence) != 1:
            raise ValueError("frozen same-design-cycle recurrence relation is missing")
        restart = [action.generated(unit) for unit in recurrence[0]["target_action_ids"]]
        decision_nodes = [node for node in graph.nodes if node.type == "decision" and node.id in cycle
                          and combine_id in reachable(graph, node.id)]
        observed_return = any(
            any(all(any(target in reachable(graph, edge.target, {decision.id}) or target == edge.target
                        for target in target_set) for target_set in restart)
                for edge in graph.edges if edge.source == decision.id)
            for decision in decision_nodes
        ) if all(restart) else False
        if not observed_return:
            reasons.append("combined-test failure branch does not restart both design paths")
    return not reasons, tuple(reasons)
