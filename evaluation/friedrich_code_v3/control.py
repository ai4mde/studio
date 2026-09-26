"""Atomic Control Node and Control Relation scoring against frozen source facts."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping

from evaluation.friedrich_v3.core import Counts, EvalEdge, EvalGraph, normalize_label, reachable, strongly_connected_components

from .alignment import ActionAlignmentTable
from .anchor_evidence import ControlAnchorEvidence
from .scoring import component_summary


NODE_TYPES = {"Decision": "decision", "Merge": "merge", "Fork": "fork", "Join": "join"}


@dataclass(frozen=True, slots=True)
class ControlFactResult:
    fact_id: str
    fact_type: str
    status: str
    generated_node_id: str | None
    reason: str
    diagnostics: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ControlComponentResult:
    counts: Counts
    facts: tuple[ControlFactResult, ...]
    required_fact_count: int
    permitted_fact_count: int
    unresolved_source_fact_count: int
    candidate_abstention_count: int
    fp_abstention_count: int
    generated_relation_coverage: tuple[Mapping[str, Any], ...] = ()
    assignment_alternatives: Mapping[str, frozenset[str | None]] = field(default_factory=dict)
    unattributed_contradictions: tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "counts": component_summary(self.counts, self.required_fact_count,
                                        self.candidate_abstention_count),
            "required_fact_count": self.required_fact_count,
            "permitted_fact_count": self.permitted_fact_count,
            "unresolved_source_fact_count": self.unresolved_source_fact_count,
            "indeterminate_alignment_count": self.candidate_abstention_count,
            "fp_abstention_count": self.fp_abstention_count,
            "generated_relation_coverage": [dict(item) for item in self.generated_relation_coverage],
            "assignment_alternatives": {
                key: sorted(value, key=lambda item: "" if item is None else item)
                for key, value in sorted(self.assignment_alternatives.items())
            },
            "unattributed_contradictions": [dict(item) for item in self.unattributed_contradictions],
            "facts": [
                {"fact_id": f.fact_id, "fact_type": f.fact_type, "status": f.status,
                 "generated_node_id": f.generated_node_id, "reason": f.reason,
                 **({"diagnostics": dict(f.diagnostics)} if f.diagnostics else {})}
                for f in self.facts
            ],
        }


def normalize_generated_control(graph: EvalGraph) -> EvalGraph:
    """Contract only unlabeled, condition-free 1-in/1-out control gateways."""
    nodes = {node.id: node for node in graph.nodes}
    edges = list(graph.edges)
    while True:
        incoming = {node_id: [e for e in edges if e.target == node_id] for node_id in nodes}
        outgoing = {node_id: [e for e in edges if e.source == node_id] for node_id in nodes}
        redundant = next((
            node_id for node_id, node in sorted(nodes.items())
            if node.type in NODE_TYPES.values()
            and not normalize_label(node.label)
            and len(incoming[node_id]) == len(outgoing[node_id]) == 1
            and not normalize_label(incoming[node_id][0].label)
            and not normalize_label(outgoing[node_id][0].label)
            and incoming[node_id][0].source != outgoing[node_id][0].target
        ), None)
        if redundant is None:
            break
        before, after = incoming[redundant][0], outgoing[redundant][0]
        edges = [e for e in edges if e.source != redundant and e.target != redundant]
        if not any(e.source == before.source and e.target == after.target for e in edges):
            edges.append(EvalEdge(before.source, after.target))
        del nodes[redundant]
    return EvalGraph(tuple(nodes.values()), tuple(edges))


class _Context:
    def __init__(self, graph: EvalGraph, alignment: ActionAlignmentTable | ControlAnchorEvidence):
        self.graph = graph
        self.alignment = alignment
        self.nodes = graph.by_id
        self.outgoing = graph.outgoing
        self.incoming = graph.incoming
        self.closure = {node.id: reachable(graph, node.id) for node in graph.nodes}
        self.edges = {node.id: tuple(e for e in graph.edges if e.source == node.id) for node in graph.nodes}
        self.cycles = tuple(
            component for component in strongly_connected_components(graph)
            if len(component) > 1 or any(e.source == e.target and e.source in component for e in graph.edges)
        )

    def mapped(self, units: list[str] | tuple[str, ...]) -> set[str]:
        return set().union(*(self.alignment.generated(unit) for unit in units)) if units else set()

    def mapped_occurrences(self, occurrences: list[str] | tuple[str, ...]) -> set[str]:
        if not isinstance(self.alignment, ControlAnchorEvidence):
            return set()
        return set().union(*(self.alignment.occurrence_generated(item) for item in occurrences)) if occurrences else set()

    def downstream(self, start: str, units: list[str] | tuple[str, ...]) -> bool:
        targets = self.mapped(units)
        return bool(targets and targets & self.closure[start])

    def upstream(self, start: str, units: list[str] | tuple[str, ...]) -> bool:
        sources = self.mapped(units)
        return bool(sources and any(start in self.closure[source] for source in sources))

    def branch_edges(self, owner: str) -> tuple[EvalEdge, ...]:
        return self.edges.get(owner, ())

    def branch_reaches(self, edge: EvalEdge, units: list[str] | tuple[str, ...]) -> bool:
        return any(self.branch_reaches_unit(edge, unit) for unit in units)

    def _split_fragments(self, unit: str) -> tuple[str, ...]:
        action = self.alignment.action if isinstance(self.alignment, ControlAnchorEvidence) else self.alignment
        return next((entry.generated_ids for entry in action.entries
                     if entry.kind == "one_to_many" and unit in entry.unit_ids), ())

    def branch_reaches_unit(self, edge: EvalEdge, unit: str, *, before_join: bool = False) -> bool:
        """A split Action's first fragment and all fragments must stay on this branch."""
        targets = self.mapped([unit])
        if not targets:
            return False
        traversed: set[str] = set()
        queue = [edge.target]
        while queue:
            node = queue.pop()
            if node in traversed:
                continue
            traversed.add(node)
            if before_join and self.nodes[node].type in {"join", "merge"}:
                continue
            queue.extend(self.outgoing[node])
        fragments = self._split_fragments(unit)
        if not fragments:
            return bool(targets & traversed)
        fragment_set = set(fragments)
        first = {node for node in fragment_set if not any(
            node in self.closure[other] and other not in self.closure[node]
            for other in fragment_set if other != node)}
        return len(first) == 1 and bool(first & traversed and fragment_set <= traversed)

    def branch_reaches_before_join(self, edge: EvalEdge, units: list[str] | tuple[str, ...]) -> bool:
        return any(self.branch_reaches_unit(edge, unit, before_join=True) for unit in units)

    def same_cycle(self, left: str, right: str) -> bool:
        return any(left in component and right in component for component in self.cycles)


def _owner_relations(control: Mapping[str, Any], fact_id: str) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        r for r in control["control_relations"]
        if r["source_control_fact"] == fact_id and r["status"] == "required"
    )


def _registered_node_role_supported(
    candidate_id: str, ctx: _Context, owned: tuple[Mapping[str, Any], ...],
    reference_evidence: Mapping[str, Any],
) -> bool:
    """Reject a Control point with a contrary registered structural role."""
    loops = [relation for relation in owned if relation["type"] == "loop_recurrence"]
    if loops and not any(candidate_id in component for component in ctx.cycles):
        for relation in loops:
            targets = relation.get("target_action_ids", [])
            mapped = ctx.mapped(targets)
            if (mapped and any(not ctx.mapped([unit]) for unit in targets)
                and any(candidate_id in ctx.closure[item] for item in mapped)
                and not any(item in ctx.closure[candidate_id] for item in mapped)):
                return False
    branches = [relation for relation in owned if relation["type"] == "decision_branch"]
    source_guards = {_guard_polarity(_guard_tokens(relation.get("guard_meaning")))
                     for relation in branches}
    source_temporal = any(re.search(r"\b(?:timeout|deadline|day|days|week|weeks|month|months|hour|hours)\b",
                                    relation.get("guard_meaning", "").casefold())
                          for relation in branches)
    candidate_temporal = bool(re.search(r"\b(?:timeout|deadline)s?\b",
                                        (ctx.nodes[candidate_id].label or "").casefold()))
    if ({"positive", "negative"} <= source_guards and not source_temporal
        and candidate_temporal):
        return False
    return True


def _anchor_context_score(
    fact: Mapping[str, Any], candidate_id: str, ctx: _Context,
    reference: EvalGraph | None,
    reference_unit_nodes: Mapping[str, tuple[str, ...]],
    owned: tuple[Mapping[str, Any], ...],
) -> int:
    """Compare structural Action context; Decision guard wording is excluded."""
    score = 0
    occurrences = fact.get("anchor_occurrence_ids", [])
    occurrence_nodes = ctx.mapped_occurrences(occurrences)
    if occurrence_nodes and any(
        item in ctx.closure[candidate_id] or candidate_id in ctx.closure[item]
        for item in occurrence_nodes
    ):
        score += 4
    reference_ids = [
        evidence_id.removeprefix("gateway:")
        for evidence_id in fact.get("reference_evidence_ids", [])
        if evidence_id.startswith("gateway:")
    ]
    if reference and reference_ids:
        ref_closure = {ref_id: reachable(reference, ref_id) for ref_id in reference_ids
                       if ref_id in reference.by_id}
        for unit in fact.get("anchor_action_ids", []):
            generated_nodes = ctx.alignment.generated(unit)
            ref_nodes = reference_unit_nodes.get(unit, ())
            if not generated_nodes or not ref_nodes:
                continue
            ref_after = any(any(node in reaches for node in ref_nodes) for reaches in ref_closure.values())
            ref_before = any(any(ref_id in reachable(reference, node) for ref_id in reference_ids)
                             for node in ref_nodes if node in reference.by_id)
            if ref_after and any(node in ctx.closure[candidate_id] for node in generated_nodes):
                score += 2
            if ref_before and any(candidate_id in ctx.closure[node] for node in generated_nodes):
                score += 2
    # Typed relation anchors distinguish consecutive decisions with the same
    # broad Action context. They remain relevant even when a reference gateway
    # supplies supplementary context.
    targets = [unit for relation in owned for unit in relation.get("target_action_ids", [])]
    incoming = [unit for relation in owned for unit in relation.get("incoming_action_ids", [])]
    if ctx.downstream(candidate_id, targets):
        score += 3
    if ctx.upstream(candidate_id, incoming):
        score += 2
    if not score:
        anchors = fact.get("anchor_action_ids", [])
        if ctx.downstream(candidate_id, anchors) or ctx.upstream(candidate_id, anchors):
            score += 1
    if score and fact.get("purpose") and ctx.nodes[candidate_id].label:
        # Source purpose may break a structural tie, but never establishes a
        # Control match without the required structure and anchor evidence.
        # Use surface content words here: guard inflection equivalence must
        # not flow into the separate case-wide Control Node assignment score.
        purpose_words = set((normalize_label(fact["purpose"]) or "").split()) - _GUARD_STOP
        candidate_words = set((normalize_label(ctx.nodes[candidate_id].label) or "").split()) - _GUARD_STOP
        score += len(purpose_words & candidate_words)
    return score


def _implicit_convergence(
    relation: Mapping[str, Any], ctx: _Context,
) -> bool:
    incoming = relation.get("incoming_action_ids", [])
    targets = ctx.mapped(relation.get("target_action_ids", []))
    if len(incoming) < 2 or not targets:
        return False
    source_sets = [ctx.mapped([unit]) for unit in incoming]
    if any(not source_set for source_set in source_sets):
        return False
    # Alternative branches must not be silently serialized.
    if relation.get("incoming_mode") == "alternative_branches":
        for left_index, left_set in enumerate(source_sets):
            for right_set in source_sets[left_index + 1:]:
                if any(right in ctx.closure[left] or left in ctx.closure[right]
                       for left in left_set for right in right_set):
                    return False
    return all(any(target in ctx.closure[source] for target in targets)
               for source_set in source_sets for source in source_set)


def _permitted_implicit(control: Mapping[str, Any], fact_id: str) -> bool:
    return any(
        rule["rule"] == "ALLOW_IMPLICIT_MERGE" and rule["scope"] == fact_id
        for rule in control.get("permitted_equivalences", [])
    )


def _gateway_evidence_supported(
    fact: Mapping[str, Any], candidate_id: str, ctx: _Context,
    owned: tuple[Mapping[str, Any], ...], reference_evidence: Mapping[str, Any],
) -> bool:
    modes = [mode for mode in fact.get("control_anchor_evidence", [])
             if mode.get("kind") == "gateway_guard"]
    if not modes:
        return False
    node = ctx.nodes[candidate_id]
    if node.type == "join":
        target_units = [u for relation in owned for u in relation.get("target_action_ids", [])]
        if len(ctx.incoming[candidate_id]) < 2 or not ctx.downstream(candidate_id, target_units):
            return False
        # The two meeting completions must be supported by separate incoming paths.
        paths = [_incoming_path_labels(ctx, incoming_id) for incoming_id in ctx.incoming[candidate_id]]
        first = {index for index, label in enumerate(paths)
                 if "first" in label and "intaker" in label and "meet" in label}
        second = {index for index, label in enumerate(paths)
                  if "second" in label and "intaker" in label and "meet" in label}
        return any(left != right for left in first for right in second)
    if node.type == "decision":
        branches = [r for r in owned if r["type"] == "decision_branch"]
        if not branches:
            return False
        # A bare gateway cannot supply predicate evidence: a labelled decision
        # or a source-compatible guard plus the required route is necessary.
        evidenced = 0
        for relation in branches:
            same_target_guard = any(
                other is not relation and other.get("target_action_ids") == relation.get("target_action_ids")
                for other in branches
            )
            valid, _, _ = _branch_relation(
                relation, candidate_id, ctx, reference_evidence,
                same_target_guard_required=same_target_guard, owned=owned,
            )
            evidenced += valid
        return evidenced == len(branches)
    return False


def _incoming_path_labels(ctx: _Context, start: str) -> str:
    seen: set[str] = set()
    queue = [start]
    labels: list[str] = []
    while queue:
        current = queue.pop()
        if current in seen:
            continue
        seen.add(current)
        labels.append(normalize_label(ctx.nodes[current].label) or "")
        if ctx.nodes[current].type != "fork":
            queue.extend(ctx.incoming[current])
    return " ".join(labels)


def _gateway_sync_relation_edges(
    relation: Mapping[str, Any], owner: str, ctx: _Context,
) -> tuple[str, ...]:
    if ctx.nodes[owner].type != "join" or len(ctx.incoming[owner]) < 2:
        return ()
    if not ctx.downstream(owner, relation.get("target_action_ids", [])):
        return ()
    modes = [mode for mode in relation.get("control_anchor_evidence", [])
             if mode.get("kind") == "gateway_guard"]
    if not modes:
        return ()
    roles = set(modes[0].get("required_structural_roles", []))
    expected = "first" if "first_intaker_meeting_completion" in roles else "second"
    return tuple(item for item in ctx.incoming[owner]
                 if expected in _incoming_path_labels(ctx, item)
                 and "intaker" in _incoming_path_labels(ctx, item)
                 and "meet" in _incoming_path_labels(ctx, item))


def _anchor_set_supported(
    fact: Mapping[str, Any], candidate_id: str, ctx: _Context,
    owned: tuple[Mapping[str, Any], ...],
) -> bool:
    sets = [mode for mode in fact.get("control_anchor_evidence", [])
            if mode.get("kind") == "anchor_set"]
    if not sets:
        return True
    options: list[set[tuple[str, str]]] = []
    for anchor_set in sets:
        units = anchor_set["semantic_unit_ids"]
        matched = [edge for edge in ctx.branch_edges(candidate_id)
                   if all(ctx.branch_reaches_before_join(edge, [unit]) for unit in units)]
        if not matched:
            return False
        options.append({(edge.source, edge.target) for edge in matched})
    def assign(index: int, used: set[tuple[str, str]]) -> bool:
        if index == len(options):
            return True
        return any(assign(index + 1, used | {edge}) for edge in options[index] - used)
    return assign(0, set())


def _case_wide_assignment(
    options: Mapping[str, tuple[tuple[int, str], ...]],
) -> Mapping[str, frozenset[str | None]]:
    """Maximize matched facts, then structural evidence, over the entire case.

    Every optimal assignment is retained for ambiguity detection. Sorting IDs
    makes the result invariant to inventory and generated-node order.
    """
    fact_ids = tuple(sorted(options))
    if not fact_ids:
        return {}
    node_ids = tuple(sorted({node_id for rows in options.values() for _, node_id in rows
                             if node_id != "implicit"}))
    columns = (*node_ids, *(f"implicit:{fact_id}" for fact_id in fact_ids),
               *(f"unmatched:{fact_id}" for fact_id in fact_ids))
    maximum_score = sum(max((score for score, _ in options[fact_id]), default=0)
                        for fact_id in fact_ids)
    priority = maximum_score + 1
    utility: list[dict[str, int]] = []
    for fact_id in fact_ids:
        row = {node_id if node_id != "implicit" else f"implicit:{fact_id}": priority + score
               for score, node_id in options[fact_id]}
        row[f"unmatched:{fact_id}"] = 0
        utility.append(row)
    forbidden = (len(fact_ids) + 1) * (priority + maximum_score + 1)

    def solve(forced: tuple[int, str] | None = None) -> int:
        """Rectangular Hungarian assignment, with a unique unmatched slot per fact."""
        n, m = len(fact_ids), len(columns)
        cost = [[0] * (m + 1)]
        for index, row in enumerate(utility):
            cost.append([0] + [
                forbidden if column not in row or (forced is not None and forced[0] == index
                                                  and forced[1] != column)
                else priority + maximum_score - row[column]
                for column in columns
            ])
        u, v, p, way = [0] * (n + 1), [0] * (m + 1), [0] * (m + 1), [0] * (m + 1)
        for index in range(1, n + 1):
            p[0] = index
            column = 0
            min_value = [forbidden + 1] * (m + 1)
            used = [False] * (m + 1)
            while True:
                used[column] = True
                row_index = p[column]
                delta, next_column = forbidden + 1, 0
                for candidate in range(1, m + 1):
                    if used[candidate]:
                        continue
                    reduced = cost[row_index][candidate] - u[row_index] - v[candidate]
                    if reduced < min_value[candidate]:
                        min_value[candidate], way[candidate] = reduced, column
                    if min_value[candidate] < delta:
                        delta, next_column = min_value[candidate], candidate
                for candidate in range(m + 1):
                    if used[candidate]:
                        u[p[candidate]] += delta
                        v[candidate] -= delta
                    else:
                        min_value[candidate] -= delta
                column = next_column
                if p[column] == 0:
                    break
            while True:
                previous = way[column]
                p[column] = p[previous]
                column = previous
                if column == 0:
                    break
        assigned_columns = ["" for _ in range(n)]
        for column in range(1, m + 1):
            if p[column]:
                assigned_columns[p[column] - 1] = columns[column - 1]
        if any(column not in row for column, row in zip(assigned_columns, utility)):
            return -forbidden
        return sum(row[column] for row, column in zip(utility, assigned_columns))

    optimum = solve()
    possible: dict[str, frozenset[str | None]] = {}
    for index, fact_id in enumerate(fact_ids):
        choices: set[str | None] = set()
        for column in sorted(utility[index]):
            if solve((index, column)) != optimum:
                continue
            if column == f"unmatched:{fact_id}":
                choices.add(None)
            elif column == f"implicit:{fact_id}":
                choices.add("implicit")
            else:
                choices.add(column)
        possible[fact_id] = frozenset(choices)
    return possible


def match_control_nodes(
    control: Mapping[str, Any], graph: EvalGraph, alignment: ActionAlignmentTable | ControlAnchorEvidence,
    *, reference: EvalGraph | None = None,
    reference_unit_nodes: Mapping[str, tuple[str, ...]] | None = None,
    reference_evidence: Mapping[str, Any] | None = None,
) -> tuple[ControlComponentResult, Mapping[str, str | None]]:
    ctx = _Context(graph, alignment)
    reference_unit_nodes = reference_unit_nodes or {}
    results_by_id: dict[str, ControlFactResult] = {}
    assigned: dict[str, str | None] = {}
    used: set[str] = set()
    options: dict[str, tuple[tuple[int, str], ...]] = {}
    unresolved_anchor_issues: dict[str, tuple[str, ...]] = {}
    attempted_evidence: dict[str, tuple[Mapping[str, Any], ...]] = {}
    assignment_alternatives: dict[str, frozenset[str | None]] = {}
    required = [n for n in control["control_nodes"] if n["status"] == "required"]
    permitted = sum(n["status"] == "permitted" for n in control["control_nodes"])
    unresolved = sum(n["status"] == "unresolved" for n in control["control_nodes"])
    for fact in required:
        fact_id = fact["fact_id"]
        owned = _owner_relations(control, fact_id)
        own_anchors = set(fact.get("anchor_action_ids", []))
        anchors = set(own_anchors)
        anchors.update(unit for relation in owned for key in ("incoming_action_ids", "target_action_ids")
                       for unit in relation.get(key, []))
        occurrence_ids = list(fact.get("anchor_occurrence_ids", []))
        occurrence_ids.extend(item for mode in fact.get("control_anchor_evidence", [])
                              if mode.get("kind") == "occurrence_anchor_set"
                              for item in mode.get("occurrence_ids", []))
        occurrence_ambiguous = isinstance(alignment, ControlAnchorEvidence) and any(
            alignment.occurrence_is_ambiguous(item) for item in occurrence_ids)
        if occurrence_ids and isinstance(alignment, ControlAnchorEvidence) and any(
            not alignment.occurrence_generated(item) for item in occurrence_ids
        ) and not occurrence_ambiguous:
            assigned[fact_id] = None
            results_by_id[fact_id] = ControlFactResult(fact_id, fact["type"], "FN", None,
                                                       "required source occurrence is missing")
            continue
        ambiguous_own = tuple(sorted(unit for unit in own_anchors if alignment.is_ambiguous(unit)))
        unresolved_anchor_issues[fact_id] = ambiguous_own
        possibilities: list[tuple[int, str]] = []
        attempts: list[Mapping[str, Any]] = []
        aligned_targets = [
            unit for relation in owned for unit in relation.get("target_action_ids", [])
            if alignment.generated(unit)
        ]
        for node in graph.nodes:
            if node.type != NODE_TYPES[fact["type"]]:
                continue
            if node.type in {"decision", "fork"} and len(ctx.outgoing[node.id]) < 2:
                continue
            if node.type in {"join", "merge"} and len(ctx.incoming[node.id]) < 2:
                continue
            if not _registered_node_role_supported(node.id, ctx, owned,
                                                  reference_evidence or {}):
                continue
            if aligned_targets and not ctx.downstream(node.id, aligned_targets):
                continue
            if occurrence_ids:
                occurrence_sets = [ctx.mapped_occurrences([item]) for item in occurrence_ids]
                if any(not members for members in occurrence_sets):
                    continue
                occurrence_nodes = set().union(*occurrence_sets)
                if not any(
                    item in ctx.closure[node.id] or node.id in ctx.closure[item]
                    for item in occurrence_nodes
                ):
                    continue
            context = _anchor_context_score(fact, node.id, ctx, reference, reference_unit_nodes, owned)
            gateway = _gateway_evidence_supported(fact, node.id, ctx, owned,
                                                   reference_evidence or {})
            anchor_set = _anchor_set_supported(fact, node.id, ctx, owned)
            attempts.append({"generated_node_id": node.id, "context_evidence_score": context,
                             "gateway_evidence": gateway, "anchor_set_evidence": anchor_set,
                             "occurrence_evidence": bool(occurrence_ids)})
            if anchors and not context and not gateway:
                continue
            if fact.get("control_anchor_evidence") and not gateway and not anchor_set:
                continue
            if any(mode.get("kind") == "gateway_guard" for mode in fact.get("control_anchor_evidence", [])) and not gateway:
                continue
            possibilities.append((context, node.id))
        attempted_evidence[fact_id] = tuple(attempts)
        if fact["type"] == "Merge" and _permitted_implicit(control, fact_id):
            if any(_implicit_convergence(relation, ctx) for relation in owned
                   if relation["type"] == "convergence"):
                possibilities.append((1, "implicit"))
        if not possibilities and (ambiguous_own or occurrence_ambiguous):
            action = alignment.action if isinstance(alignment, ControlAnchorEvidence) else alignment
            results_by_id[fact_id] = ControlFactResult(
                fact_id, fact["type"], "indeterminate_alignment", None,
                "Action anchor alignment remains ambiguous after registered evidence checks",
                {"reason_code": "CONTROL_NODE_ANCHOR_AMBIGUITY_AFTER_EVIDENCE",
                 "ambiguous_action_unit_ids": list(ambiguous_own),
                 "plausible_generated_anchor_ids": {
                     unit: list(action.ambiguous_candidates.get(unit, ())) for unit in ambiguous_own},
                 "accepted_generated_anchor_ids": {
                     unit: sorted(action.generated(unit)) for unit in sorted(anchors)},
                 "occurrence_ambiguous": occurrence_ambiguous,
                 "structural_evidence_attempted": list(attempts)})
            assigned[fact_id] = "indeterminate"
            assignment_alternatives[fact_id] = frozenset()
            continue
        options[fact_id] = tuple(possibilities)
    global_choices = _case_wide_assignment(options)
    for fact in required:
        fact_id = fact["fact_id"]
        if fact_id in results_by_id:
            continue
        choices = global_choices[fact_id]
        assignment_alternatives[fact_id] = choices
        if len(choices) > 1:
            assigned[fact_id] = "indeterminate"
            results_by_id[fact_id] = ControlFactResult(
                fact_id, fact["type"], "indeterminate_alignment", None,
                "multiple equally optimal case-wide Control assignments",
                {"reason_code": "CONTROL_NODE_OPTIMAL_ASSIGNMENT_TIE",
                 "owner_control_alternatives": sorted(choices, key=lambda item: "" if item is None else item),
                 "ambiguous_action_unit_ids": list(unresolved_anchor_issues.get(fact_id, ())),
                 "structural_evidence_attempted": list(attempted_evidence.get(fact_id, ()))},
            )
        else:
            chosen = next(iter(choices))
            assigned[fact_id] = chosen
            if chosen is None:
                results_by_id[fact_id] = ControlFactResult(
                    fact_id, fact["type"], "FN", None, "required logical control node not matched",
                )
            else:
                if chosen != "implicit":
                    used.add(chosen)
                results_by_id[fact_id] = ControlFactResult(
                    fact_id, fact["type"], "TP", None if chosen == "implicit" else chosen,
                    "source-equivalent implicit convergence" if chosen == "implicit"
                    else "case-wide logical type and structural context match",
                )
    results = [results_by_id[fact["fact_id"]] for fact in required]
    abstained = sum(f.status == "indeterminate_alignment" for f in results)
    # Only affirmative no-control cases provide exhaustive absence of controls.
    unmatched = [node for node in graph.nodes
                 if node.type in set(NODE_TYPES.values()) | {"unsupported_control"} and node.id not in used]
    fp = len(unmatched) if control["no_control"] else 0
    if control["no_control"]:
        results.extend(ControlFactResult(f"generated:{node.id}", node.type, "FP", node.id,
                                         "affirmative no-control source scope") for node in unmatched)
    return ControlComponentResult(
        Counts(sum(f.status == "TP" for f in results), fp, sum(f.status == "FN" for f in results)),
        tuple(results), len(required), permitted, unresolved, abstained,
        0 if control["no_control"] else len(unmatched),
        assignment_alternatives=assignment_alternatives,
    ), assigned


_GUARD_LEMMAS = {
    "rejects": "reject", "rejected": "reject", "rejection": "reject",
    "opposes": "oppose", "opposed": "oppose", "opposition": "oppose",
    "approves": "approve", "approved": "approve", "approval": "approve",
    "accepts": "accept", "accepted": "accept", "acceptance": "accept",
    "denies": "deny", "denied": "deny", "denial": "deny",
    "fails": "fail", "failed": "fail", "failure": "fail",
    "confirms": "confirm", "confirmed": "confirm", "confirmation": "confirm",
    "succeeds": "success", "succeeded": "success", "successful": "success",
    "completed": "complete", "completes": "complete", "completion": "complete",
    "corrective": "correct", "correction": "correct", "corrections": "correct",
    "dismounts": "dismount", "dismounted": "dismount", "dismounting": "dismount",
    "actions": "action", "requests": "request", "requested": "request",
    "changes": "change", "received": "receive", "receives": "receive",
    "restoration": "restore", "restored": "restore", "restoring": "restore",
    "automatic": "automatic", "auto": "automatic",
    "analyzable": "analyze", "analysable": "analyze", "analyzes": "analyze",
    "implementation": "implement", "implemented": "implement", "implements": "implement",
    "performs": "perform", "performed": "perform", "performing": "perform",
    "measures": "measure", "measured": "measure", "measurement": "measure",
    "expires": "expire", "expired": "expire", "timeout": "expire",
    "interested": "interest", "uninterested": "not_interest",
    "mismatched": "mismatch", "matching": "match", "matches": "match",
    "minor": "minor", "non": "not", "un": "not",
    "two": "2", "seven": "7", "days": "day",
}
_GUARD_STOP = {"the", "a", "an", "is", "are", "of", "to", "by", "at", "in", "or", "and", "but"}


def _guard_tokens(value: str | None) -> set[str]:
    words = (normalize_label(value) or "").split()
    return {_GUARD_LEMMAS.get(word, word) for word in words if word not in _GUARD_STOP}


def _guard_comparator(value: str | None) -> str | None:
    raw = (value or "").casefold()
    symbol = re.search(r"<=|>=|<|>", raw)
    if symbol:
        return symbol.group()
    words = _guard_tokens(raw)
    if "least" in words or ("equal" in words and "over" in words):
        return ">="
    if "most" in words or ("equal" in words and "under" in words):
        return "<="
    if "before" in words or "less" in words or "under" in words or "below" in words:
        return "<"
    if "after" in words or "greater" in words or "over" in words or "above" in words:
        return ">"
    return None


def _guard_polarity(words: set[str]) -> str | None:
    if "approve" in words and "progress" in words:
        return None
    if "not" in words or "no" in words or "not_interest" in words:
        return "negative"
    positive = {"accept", "approve", "confirm", "success", "complete", "feasible", "interest", "pass"}
    negative = {"reject", "oppose", "deny", "fail", "infeasible", "problem", "cancel", "expire"}
    if words & positive and not words & negative:
        return "positive"
    if words & negative and not words & positive:
        return "negative"
    return None


def _guard_modality(words: set[str]) -> str | None:
    if words & {"must", "require", "requires", "required", "mandatory"}:
        return "required"
    if words & {"may", "optional"}:
        return "optional"
    return None


def _guard_hard_conflict(source: str | None, candidate: str | None) -> bool:
    left, right = _guard_tokens(source), _guard_tokens(candidate)
    if not left or not right:
        return False
    if ("approve" in left and "progress" not in left
        and "approve" in right and "progress" in right):
        return True
    left_comparison, right_comparison = _guard_comparator(source), _guard_comparator(candidate)
    if left_comparison and right_comparison and left_comparison != right_comparison:
        return True
    left_numbers = {item for item in left if item.isdigit()}
    right_numbers = {item for item in right if item.isdigit()}
    if left_numbers and right_numbers and left_numbers != right_numbers:
        return True
    left_polarity, right_polarity = _guard_polarity(left), _guard_polarity(right)
    if left_polarity and right_polarity and left_polarity != right_polarity:
        return True
    left_modality, right_modality = _guard_modality(left), _guard_modality(right)
    if left_modality and right_modality and left_modality != right_modality:
        return True
    return False


def _deadline_guard(value: str | None) -> tuple[int, int, str | None] | None:
    """Canonicalize an explicit missed-deadline predicate, including clock syntax."""
    if not value:
        return None
    normalized = value.casefold().replace("_", " ").replace("-", " ")
    missed = bool(re.search(r"\bmiss\w*\b|\bnot\s+(?:completed?|finished?|done)\b|\boverdue\b|\blate\b", normalized))
    if not missed:
        return None
    clock = re.search(r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b|\b(\d{1,4})\s*(am|pm)\b", normalized)
    if clock is None:
        return None
    if clock.group(1) is not None:
        return int(clock.group(1)), int(clock.group(2)), clock.group(3)
    compact = clock.group(4)
    hour, minute = (int(compact[:-2]), int(compact[-2:])) if len(compact) > 2 else (int(compact), 0)
    return hour, minute, clock.group(5)


def _guard_matches(edge: EvalEdge, fact: Mapping[str, Any], reference: Mapping[str, Any]) -> bool:
    label = normalize_label(edge.label)
    guard = normalize_label(fact.get("guard_meaning"))
    if not label or not guard:
        return False
    if _guard_hard_conflict(fact.get("guard_meaning"), edge.label):
        return False
    source_comparison = _guard_comparator(fact.get("guard_meaning"))
    if source_comparison and source_comparison != _guard_comparator(edge.label):
        return False
    if label == guard:
        return True
    accepted = {guard}
    for evidence_id in fact.get("reference_evidence_ids", []):
        if not evidence_id.startswith("branch:"):
            continue
        for branch in reference.get("branch_scopes", []):
            if branch.get("scope_id") == evidence_id:
                accepted.update(
                    normalize_label(value) for key, value in branch.items()
                    if "label" in key and isinstance(value, str)
                )
                source_id, target_id = evidence_id.split(":")[1:]
                accepted.update(
                    normalize_label(raw.get("label")) for raw in reference.get("edges", [])
                    if str(raw.get("source_id")) == source_id
                    and str(raw.get("target_id")) == target_id
                )
    if label in accepted:
        return True
    source_deadline = _deadline_guard(fact.get("guard_meaning"))
    if source_deadline is not None and source_deadline == _deadline_guard(edge.label):
        return True
    # Exact content-token containment handles grammatical wording only; there
    # is no learned or new semantic similarity threshold for guard matching.
    tokens = _guard_tokens(guard)
    return bool(tokens and tokens <= _guard_tokens(label))


def _guard_context_matches(
    edge: EvalEdge, fact: Mapping[str, Any], reference: Mapping[str, Any],
    ctx: _Context, owner: str,
) -> bool:
    if _guard_matches(edge, fact, reference):
        return True
    if _guard_hard_conflict(fact.get("guard_meaning"), edge.label):
        return False
    guard_words = _guard_tokens(fact.get("guard_meaning"))
    edge_words = _guard_tokens(edge.label)
    if not guard_words or not edge_words:
        return False
    targets = ctx.mapped(fact.get("target_action_ids", []))
    branch_actions = {node for node in targets if node == edge.target or node in ctx.closure[edge.target]}
    if not branch_actions:
        return False
    owner_words = _guard_tokens(ctx.nodes[owner].label)
    predicate_words = owner_words | edge_words
    # A neighbouring Action that explicitly checks a predicate may supply
    # its subject and time scope. Ordinary upstream work cannot do so.
    for incoming in ctx.incoming[owner]:
        node = ctx.nodes[incoming]
        label = normalize_label(node.label) or ""
        if node.type == "action" and any(word in label.split() for word in ("check", "checks", "verify", "verifies")):
            predicate_words.update(_guard_tokens(node.label))
    source_numbers = {word for word in guard_words if word.isdigit()}
    if source_numbers and not source_numbers <= predicate_words:
        return False
    source_comparison = _guard_comparator(fact.get("guard_meaning"))
    if source_comparison:
        edge_comparison = _guard_comparator(edge.label)
        owner_comparison = _guard_comparator(ctx.nodes[owner].label)
        if edge_comparison and edge_comparison != source_comparison:
            return False
        complement = {"<": ">=", "<=": ">", ">": "<=", ">=": "<"}
        if (source_comparison not in {edge_comparison, owner_comparison}
            and not (len(ctx.branch_edges(owner)) == 2
                     and owner_comparison == complement[source_comparison]
                     and not edge_comparison)):
            return False
    # Qualifiers that distinguish two source branches must be on the actual
    # candidate predicate, not inferred solely from an Action on its path.
    hard_modifiers = guard_words & {"huge", "technical", "small", "low", "high"}
    if hard_modifiers and not hard_modifiers <= predicate_words:
        return False
    branch_words = set().union(*(_guard_tokens(ctx.nodes[node].label) for node in branch_actions))
    # A binary request decision can encode acceptance by performing the
    # accepted Action while naming denial on the opposite branch. Require the
    # candidate edge itself to name that Action outcome; a bare "yes" or an
    # unrelated label does not establish which request was accepted.
    if ({"request", "accept"} <= guard_words
        and {"request", "deny"} <= owner_words
        and len(ctx.branch_edges(owner)) == 2
        and any("deny" in _guard_tokens(other.label)
                for other in ctx.branch_edges(owner) if other is not edge)
        and edge_words & branch_words & {"perform", "measure"}):
        return True
    # A positive decision word can name the same branch as an accepted Action
    # whose own label spells out the frozen guard. Require a binary explicit
    # opposite and the accepted Action on this edge, so "approved" cannot
    # stand in for an unrelated confirmation downstream.
    if (_guard_polarity(guard_words) == _guard_polarity(edge_words) == "positive"
        and len(ctx.branch_edges(owner)) == 2
        and any(_guard_polarity(_guard_tokens(other.label)) == "negative"
                for other in ctx.branch_edges(owner) if other is not edge)
        and guard_words & branch_words
        and edge_words & owner_words):
        return True
    # The guard's words may be split across the edge, gateway, and accepted
    # branch outcome; an opaque unrelated edge is not semantic evidence.
    # An eventual downstream Action does not turn every upstream gateway into
    # the owner of its guard. The candidate predicate must carry some guard
    # content; the accepted Action is corroboration, not a substitute.
    shared = guard_words & predicate_words
    if not shared:
        return False
    source_polarity = _guard_polarity(guard_words)
    edge_polarity = _guard_polarity(edge_words)
    if source_polarity == "positive" and edge_polarity is None and not any(
        _guard_polarity(_guard_tokens(other.label)) == "negative"
        for other in ctx.branch_edges(owner) if other is not edge
    ):
        return False
    if source_polarity and edge_polarity and source_polarity != edge_polarity:
        return False
    return True


def _relation_branch_reaches(
    edge: EvalEdge, relation: Mapping[str, Any], ctx: _Context,
    *, before_join: bool = False,
) -> bool:
    units = relation.get("target_action_ids", [])
    check = ctx.branch_reaches_before_join if before_join else ctx.branch_reaches
    if relation.get("target_mode") in {"both_required_any_order", "both_required_parallel_restart"}:
        return bool(units) and all(check(edge, [unit]) for unit in units)
    return check(edge, units)


def _branch_relation(
    relation: Mapping[str, Any], owner: str, ctx: _Context,
    reference: Mapping[str, Any], *, same_target_guard_required: bool,
    owned: tuple[Mapping[str, Any], ...] = (),
) -> tuple[bool, bool, str]:
    edges = ctx.branch_edges(owner)
    target = relation.get("target_action_ids", [])
    target_edges = [edge for edge in edges if _relation_branch_reaches(edge, relation, ctx)]
    guard_edges = [edge for edge in edges
                   if _guard_context_matches(edge, relation, reference, ctx, owner)
                   and not (not _guard_matches(edge, relation, reference)
                            and any(other is not relation and other.get("type") == "decision_branch"
                                    and _guard_matches(edge, other, reference) for other in owned))]
    if same_target_guard_required:
        guard_edges = [edge for edge in guard_edges
                       if _guard_matches(edge, relation, reference)]
    if relation["type"] == "parallel_launch":
        return bool(target_edges), False, "parallel launch target on a distinct Fork branch"
    exact = [edge for edge in target_edges if edge in guard_edges]
    if exact:
        return True, False, "guard and target preserved on one outgoing branch"
    if (len(target_edges) == 1 and not same_target_guard_required and not guard_edges
        and not normalize_label(target_edges[0].label)):
        # A unique Action outcome can evidence an unlabeled branch. Same-target
        # guarded relations cannot use this inference.
        return True, False, "unique branch outcome evidenced by its aligned Action"
    contradictory = bool((target_edges and guard_edges) or guard_edges or target_edges)
    return False, contradictory, "guard or branch target differs from frozen fact"


def _relation_outcome(
    relation: Mapping[str, Any], owner: str | None, ctx: _Context,
    reference: Mapping[str, Any], owned: tuple[Mapping[str, Any], ...],
) -> tuple[bool, bool, str]:
    kind = relation["type"]
    if owner is None:
        return False, False, "owning Control Node is absent"
    if kind in {"decision_branch", "parallel_launch"}:
        if owner == "implicit":
            return False, False, "branch requires an explicit Decision or Fork"
        same_target_guard = any(
            other is not relation and other["type"] == "decision_branch"
            and other.get("target_action_ids") == relation.get("target_action_ids")
            for other in owned
        )
        return _branch_relation(relation, owner, ctx, reference,
                                same_target_guard_required=same_target_guard, owned=owned)
    if kind == "convergence":
        if owner == "implicit":
            valid = _implicit_convergence(relation, ctx)
            return valid, False, "implicit alternative-branch convergence"
        valid = (
            all(ctx.upstream(owner, [unit]) for unit in relation.get("incoming_action_ids", []))
            and ctx.downstream(owner, relation.get("target_action_ids", []))
        )
        return valid, False, "incoming branches converge before target Action"
    if kind == "synchronization":
        if owner == "implicit" or ctx.nodes[owner].type != "join":
            return False, False, "synchronization requires an AND-Join"
        valid = (
            all(ctx.upstream(owner, [unit]) for unit in relation.get("incoming_action_ids", []))
            and ctx.downstream(owner, relation.get("target_action_ids", []))
        )
        return valid, False, "required incoming branches synchronize at Join"
    if kind in {"loop_recurrence", "loop_exit", "termination"}:
        if owner == "implicit":
            return False, False, "relation requires an explicit control point"
        edges = ctx.branch_edges(owner)
        target_edges = [edge for edge in edges if _relation_branch_reaches(edge, relation, ctx)]
        guard_edges = [edge for edge in edges
                       if _guard_context_matches(edge, relation, reference, ctx, owner)]
        candidates = [edge for edge in target_edges if edge in guard_edges] or target_edges
        if not candidates:
            return False, bool(guard_edges), "guarded route to required target is absent"
        if kind == "loop_recurrence":
            valid = any(any(ctx.same_cycle(owner, target) for target in ctx.mapped(relation["target_action_ids"]))
                        for _edge in candidates)
            return valid, bool(not valid and edges), "repeatable return to frozen target Action"
        if kind == "loop_exit":
            valid = any(owner in component for component in ctx.cycles) and any(any(not ctx.same_cycle(owner, target)
                            for target in ctx.mapped(relation["target_action_ids"]))
                        for _edge in candidates)
            return valid, False, "guarded exit leaves repeatable loop"
        excluded = ctx.mapped(relation.get("excluded_action_ids", []))
        required_on_branch = relation.get("required_on_branch_action_ids", [])
        valid = any(
            not (excluded & ({edge.target} | ctx.closure[edge.target]))
            and all(ctx.branch_reaches(edge, [unit]) for unit in required_on_branch)
            for edge in candidates
        )
        return valid, bool(not valid and candidates), "branch-local termination and exclusions"
    raise ValueError(f"unsupported frozen Control Relation type: {kind}")


def _generated_relation_atoms(graph: EvalGraph) -> tuple[tuple[str, EvalEdge], ...]:
    """Enumerate logical generated relation slots, including branch and join roles."""
    atoms: list[tuple[str, EvalEdge]] = []
    cycles = tuple(component for component in strongly_connected_components(graph)
                   if len(component) > 1 or any(edge.source == edge.target
                                                for edge in graph.edges if edge.source in component))
    for edge in graph.edges:
        source_type = graph.by_id[edge.source].type
        target_type = graph.by_id[edge.target].type
        if source_type in {"decision", "fork", "unsupported_control"}:
            atoms.append(("outgoing_control", edge))
        if target_type in {"merge", "join", "unsupported_control"}:
            atoms.append(("incoming_control", edge))
        if any(edge.source in component and edge.target in component for component in cycles):
            atoms.append(("cycle_control", edge))
    return tuple(sorted(atoms, key=lambda item: (item[0], item[1].source,
                                                item[1].target, item[1].label or "")))


def _relation_claims_atom(
    relation: Mapping[str, Any], owner: str, role: str, edge: EvalEdge,
    ctx: _Context, reference: Mapping[str, Any],
) -> bool:
    kind = relation["type"]
    if role == "cycle_control" and kind == "loop_recurrence":
        cycle = next((component for component in ctx.cycles
                      if owner in component and edge.source in component
                      and edge.target in component), None)
        return bool(cycle and all(ctx.mapped([unit]) & cycle
                                  for unit in relation.get("target_action_ids", [])))
    if kind in {"decision_branch", "parallel_launch", "loop_recurrence", "loop_exit", "termination"}:
        if role != "outgoing_control" or edge.source != owner:
            return False
        targets = relation.get("target_action_ids", [])
        if kind == "parallel_launch":
            return ctx.branch_reaches_before_join(edge, targets)
        if targets and not _relation_branch_reaches(edge, relation, ctx):
            return False
        if kind == "decision_branch":
            guard = _guard_context_matches(edge, relation, reference, ctx, owner)
            return guard or (not any(_guard_context_matches(item, relation, reference, ctx, owner)
                                     for item in ctx.branch_edges(owner))
                             and sum(_relation_branch_reaches(item, relation, ctx)
                                     for item in ctx.branch_edges(owner)) == 1)
        if relation.get("guard_meaning"):
            guard_edges = [item for item in ctx.branch_edges(owner)
                           if _guard_context_matches(item, relation, reference, ctx, owner)]
            return not guard_edges or edge in guard_edges
        return True
    if kind in {"convergence", "synchronization"}:
        if role != "incoming_control" or edge.target != owner:
            return False
        incoming = relation.get("incoming_action_ids", [])
        return bool(incoming) and any(
            edge.source in ctx.mapped([unit]) or ctx.upstream(edge.source, [unit])
            for unit in incoming
        )
    return False


def _relation_coverage(
    control: Mapping[str, Any], graph: EvalGraph, ctx: _Context,
    assigned_nodes: Mapping[str, str | None], reference: Mapping[str, Any],
    results: tuple[ControlFactResult, ...],
) -> tuple[Mapping[str, Any], ...]:
    by_id = {item.fact_id: item for item in results}
    coverage: list[Mapping[str, Any]] = []
    for role, edge in _generated_relation_atoms(graph):
        matched: list[str] = []
        contradictions: list[str] = []
        for relation in control["control_relations"]:
            if relation["status"] != "required":
                continue
            owner = assigned_nodes.get(relation["source_control_fact"])
            if owner in {None, "implicit", "indeterminate"}:
                continue
            if not _relation_claims_atom(relation, owner, role, edge, ctx, reference):
                continue
            outcome = by_id.get(relation["fact_id"])
            if outcome and outcome.status == "TP":
                matched.append(relation["fact_id"])
            elif outcome and outcome.status == "FN+FP":
                contradictions.append(relation["fact_id"])
        status = ("MATCHED" if matched else "CONTRADICTION_ACCOUNTED" if contradictions
                  else "FP" if control["no_control"] else "FP_ABSTAIN")
        coverage.append({
            "generated_relation_id": f"{role}:{edge.source}->{edge.target}:{edge.label or ''}",
            "role": role, "source": edge.source, "target": edge.target,
            "guard_label": edge.label, "status": status,
            "source_fact_ids": sorted(matched or contradictions),
        })
    return tuple(coverage)


def _distinct_branch_choices(
    required: list[Mapping[str, Any]], assigned_nodes: Mapping[str, str | None],
    ctx: _Context,
) -> Mapping[str, frozenset[str | None]]:
    """Assign frozen independent Fork/Join branches without inventory-order greed."""
    groups: dict[tuple[str, str], dict[str, tuple[tuple[int, str], ...]]] = {}
    for relation in required:
        kind = relation["type"]
        if kind not in {"parallel_launch", "synchronization"}:
            continue
        owner = assigned_nodes.get(relation["source_control_fact"])
        if owner in {None, "implicit", "indeterminate"}:
            continue
        edges: list[EvalEdge] = []
        if kind == "parallel_launch":
            sets = [mode["semantic_unit_ids"] for mode in relation.get("control_anchor_evidence", [])
                    if mode.get("kind") == "anchor_set"]
            edges = [edge for edge in ctx.branch_edges(owner)
                     if (all(all(ctx.branch_reaches_before_join(edge, [unit]) for unit in group)
                             for group in sets) if sets else
                         ctx.branch_reaches_before_join(edge, relation.get("target_action_ids", [])))]
        elif kind == "synchronization":
            modes = [mode for mode in relation.get("control_anchor_evidence", [])
                     if mode.get("kind") == "gateway_guard"]
            if modes:
                allowed = set(_gateway_sync_relation_edges(relation, owner, ctx))
                edges = [edge for edge in ctx.graph.edges if edge.target == owner
                         and edge.source in allowed]
            elif len(relation.get("incoming_action_ids", [])) == 1:
                unit = relation["incoming_action_ids"][0]
                edges = [edge for edge in ctx.graph.edges if edge.target == owner
                         and (edge.source in ctx.mapped([unit])
                              or ctx.upstream(edge.source, [unit]))
                         and ctx.downstream(owner, relation.get("target_action_ids", []))]
        if edges or kind == "parallel_launch" or (kind == "synchronization" and
                (len(relation.get("incoming_action_ids", [])) == 1 or modes)):
            groups.setdefault((owner, kind), {})[relation["fact_id"]] = tuple(
                (0, f"{edge.source}->{edge.target}:{edge.label or ''}") for edge in edges)
    result: dict[str, frozenset[str | None]] = {}
    for options in groups.values():
        result.update(_case_wide_assignment(options))
    return result


def score_control_relations(
    control: Mapping[str, Any], graph: EvalGraph, alignment: ActionAlignmentTable | ControlAnchorEvidence,
    assigned_nodes: Mapping[str, str | None], reference_evidence: Mapping[str, Any],
    *, owner_alternatives: Mapping[str, frozenset[str | None]] | None = None,
) -> ControlComponentResult:
    ctx = _Context(graph, alignment)
    results: list[ControlFactResult] = []
    required = [r for r in control["control_relations"] if r["status"] == "required"]
    permitted = sum(r["status"] == "permitted" for r in control["control_relations"])
    unresolved = sum(r["status"] == "unresolved" for r in control["control_relations"])
    if control["no_control"]:
        extra = _generated_relation_atoms(graph)
        facts = tuple(ControlFactResult(
            f"generated:{role}:{edge.source}->{edge.target}", "generated_control_relation", "FP",
            edge.source, "affirmative no-control source scope",
        ) for role, edge in extra)
        return ControlComponentResult(Counts(0, len(extra), 0), facts, 0, permitted,
                                      unresolved, 0, 0,
                                      _relation_coverage(control, graph, ctx, assigned_nodes,
                                                         reference_evidence, facts))
    fp_keys: set[tuple[str, str]] = set()
    owner_alternatives = owner_alternatives or {}
    branch_choices = _distinct_branch_choices(required, assigned_nodes, ctx)
    abstained = 0
    for relation in required:
        fact_id = relation["fact_id"]
        owner_id = relation["source_control_fact"]
        anchors = set(relation.get("target_action_ids", []))
        anchors.update(relation.get("incoming_action_ids", []))
        anchors.update(relation.get("excluded_action_ids", []))
        anchors.update(relation.get("required_on_branch_action_ids", []))
        evidence = relation.get("control_anchor_evidence", [])
        occurrence_ids = [item for mode in evidence if mode.get("kind") == "occurrence_anchor_set"
                          for item in mode.get("occurrence_ids", [])]
        occurrence_ambiguous = isinstance(alignment, ControlAnchorEvidence) and any(
            alignment.occurrence_is_ambiguous(item) for item in occurrence_ids)
        if occurrence_ids and isinstance(alignment, ControlAnchorEvidence) and any(
            not alignment.occurrence_generated(item) for item in occurrence_ids
        ) and not occurrence_ambiguous:
            results.append(ControlFactResult(fact_id, relation["type"], "FN", None,
                                             "required source occurrence is missing"))
            continue
        ambiguous_units = tuple(sorted(unit for unit in anchors if alignment.is_ambiguous(unit)))
        action = alignment.action if isinstance(alignment, ControlAnchorEvidence) else alignment
        owned = _owner_relations(control, owner_id)
        owner = assigned_nodes.get(owner_id)
        diagnostic = {
            "ambiguous_action_unit_ids": list(ambiguous_units),
            "plausible_generated_anchor_ids": {
                unit: list(action.ambiguous_candidates.get(unit, ())) for unit in ambiguous_units},
            "accepted_generated_anchor_ids": {
                unit: sorted(action.generated(unit)) for unit in sorted(anchors)},
            "occurrence_evidence_attempted": list(occurrence_ids),
            "guard_evidence_attempted": relation.get("guard_meaning"),
            "anchor_set_evidence_attempted": [mode for mode in evidence
                                               if mode.get("kind") == "anchor_set"],
            "gateway_evidence_attempted": [mode for mode in evidence
                                            if mode.get("kind") == "gateway_guard"],
        }
        if owner == "indeterminate":
            alternatives = owner_alternatives.get(owner_id, frozenset())
            diagnostic["owner_control_alternatives"] = sorted(
                alternatives, key=lambda item: "" if item is None else item)
            ordered_alternatives = sorted(alternatives, key=lambda item: "" if item is None else item)
            outcomes = [_relation_outcome(relation, candidate_owner, ctx, reference_evidence, owned)
                        for candidate_owner in ordered_alternatives]
            diagnostic["owner_outcomes_attempted"] = [
                {"owner": candidate_owner, "valid": outcome[0],
                 "contradictory": outcome[1], "reason": outcome[2]}
                for candidate_owner, outcome in zip(ordered_alternatives, outcomes)]
            independent_branch = relation["type"] not in {"parallel_launch", "synchronization"}
            if outcomes and independent_branch and all(item[0] for item in outcomes) and not ambiguous_units and not occurrence_ambiguous:
                valid, contradictory, reason = True, False, "relation invariant across optimal owner assignments"
            elif outcomes and all(not item[0] and not item[1] for item in outcomes) and not ambiguous_units and not occurrence_ambiguous:
                valid, contradictory, reason = False, False, "required relation absent under every optimal owner assignment"
            else:
                abstained += 1
                diagnostic["reason_code"] = "CONTROL_RELATION_OWNER_ASSIGNMENT_UNRESOLVED"
                results.append(ControlFactResult(fact_id, relation["type"], "indeterminate_alignment", None,
                                                 "owning Control Node alignment remains indeterminate after relation checks",
                                                 diagnostic))
                continue
        elif fact_id in branch_choices:
            choices = branch_choices[fact_id]
            diagnostic["branch_assignment_alternatives"] = sorted(
                choices, key=lambda item: "" if item is None else item)
            if None in choices and len(choices) > 1:
                abstained += 1
                diagnostic["reason_code"] = "CONTROL_RELATION_BRANCH_ASSIGNMENT_UNRESOLVED"
                results.append(ControlFactResult(fact_id, relation["type"], "indeterminate_alignment", owner,
                                                 "distinct branch assignment is not invariant", diagnostic))
                continue
            valid = None not in choices
            contradictory = False
            reason = ("distinct parallel launch branch" if relation["type"] == "parallel_launch"
                      else "distinct incoming branch synchronizes at Join") if valid else (
                      "required distinct parallel launch absent" if relation["type"] == "parallel_launch"
                      else "required incoming synchronization branch absent")
        else:
            valid, contradictory, reason = _relation_outcome(
                relation, owner, ctx, reference_evidence, owned
            )
        unresolved_required_exclusion = bool(
            set(ambiguous_units) & set(relation.get("excluded_action_ids", [])))
        unresolved_required_target = bool(
            relation.get("target_mode") in {"both_required_any_order", "both_required_parallel_restart"}
            and set(ambiguous_units) & set(relation.get("target_action_ids", [])))
        if (not valid or unresolved_required_exclusion or unresolved_required_target) and (
            ambiguous_units or occurrence_ambiguous):
            abstained += 1
            diagnostic["reason_code"] = "CONTROL_RELATION_ANCHOR_AMBIGUITY_AFTER_EVIDENCE"
            diagnostic["structural_evidence_attempted"] = reason
            results.append(ControlFactResult(fact_id, relation["type"], "indeterminate_alignment", owner
                                             if owner != "indeterminate" else None,
                                             "Action anchor alignment remains ambiguous after registered evidence checks",
                                             diagnostic))
            continue
        if valid:
            results.append(ControlFactResult(fact_id, relation["type"], "TP",
                                             None if owner == "indeterminate" else owner, reason,
                                             diagnostic if owner == "indeterminate" else {}))
        elif contradictory:
            # One local substitute contributes one FP, even if several frozen
            # branch facts share a generated routing point.
            key = (owner_id, relation.get("guard_meaning") or relation["type"])
            if key not in fp_keys:
                fp_keys.add(key)
                status = "FN+FP"
            else:
                status = "FN"
            results.append(ControlFactResult(fact_id, relation["type"], status,
                                             None if owner == "indeterminate" else owner, reason))
        else:
            results.append(ControlFactResult(fact_id, relation["type"], "FN",
                                             None if owner == "indeterminate" else owner, reason,
                                             diagnostic if owner == "indeterminate" else {}))
    coverage = _relation_coverage(control, graph, ctx, assigned_nodes,
                                  reference_evidence, tuple(results))
    attributed = {fact_id for item in coverage if item["status"] == "CONTRADICTION_ACCOUNTED"
                  for fact_id in item["source_fact_ids"]}
    unattributed = tuple({
        "source_fact_id": fact.fact_id,
        "owner_generated_node_id": fact.generated_node_id,
        "reason": fact.reason,
        "attribution": "no single generated relation atom represents this scored local contradiction",
    } for fact in results if fact.status == "FN+FP" and fact.fact_id not in attributed)
    return ControlComponentResult(
        Counts(sum(f.status == "TP" for f in results), len(fp_keys),
               sum(f.status in {"FN", "FN+FP"} for f in results)),
        tuple(results), len(required), permitted, unresolved, abstained,
        sum(item["status"] == "FP_ABSTAIN" for item in coverage), coverage,
        unattributed_contradictions=unattributed,
    )
