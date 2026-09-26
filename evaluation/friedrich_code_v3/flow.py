"""Fixed, cycle-safe Action precedence proxy for V3 Flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from evaluation.friedrich_v3.core import Counts, EvalEdge, EvalGraph, reachable, strongly_connected_components
from evaluation.friedrich_v3.flow import _transitive_reduction
from evaluation.friedrich_semantic.action import SemanticActivityUnit
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory

from .alignment import ActionAlignmentTable
from .scoring import component_summary


Pair = tuple[str, str]


@dataclass(frozen=True, slots=True)
class FlowInventoryV3:
    required_precedence: tuple[Pair, ...]
    unresolved_cycle_pairs: tuple[Pair, ...]
    removed_recurrence_edges: tuple[Pair, ...]


@dataclass(frozen=True, slots=True)
class FlowFactResult:
    source_unit_id: str
    target_unit_id: str
    status: str
    reason: str
    diagnostics: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FlowResultV3:
    counts: Counts
    facts: tuple[FlowFactResult, ...]
    inventory: FlowInventoryV3
    candidate_unresolved_count: int
    action_alignment_coverage: float
    unsupported_cycle_violation_count: int = 0
    source_supported_cycle_indeterminate_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "counts": component_summary(self.counts, len(self.inventory.required_precedence),
                                        self.candidate_unresolved_count),
            "facts": [
                {"source_unit_id": f.source_unit_id, "target_unit_id": f.target_unit_id,
                 "status": f.status, "reason": f.reason,
                 **({"diagnostics": dict(f.diagnostics)} if f.diagnostics else {})} for f in self.facts
            ],
            "fixed_required_precedence": [list(pair) for pair in self.inventory.required_precedence],
            "source_unresolved_cycle_pairs": [list(pair) for pair in self.inventory.unresolved_cycle_pairs],
            "removed_recurrence_edges": [list(pair) for pair in self.inventory.removed_recurrence_edges],
            "indeterminate_alignment_count": self.candidate_unresolved_count,
            "unsupported_cycle_violation_count": self.unsupported_cycle_violation_count,
            "source_supported_cycle_indeterminate_count": self.source_supported_cycle_indeterminate_count,
            "action_alignment_coverage": self.action_alignment_coverage,
        }


def _cyclic_components(graph: EvalGraph) -> tuple[frozenset[str], ...]:
    self_loops = {edge.source for edge in graph.edges if edge.source == edge.target}
    return tuple(
        c for c in strongly_connected_components(graph)
        if len(c) > 1 or bool(c & self_loops)
    )


def _trim_supported_returns(
    graph: EvalGraph, *, loop_target_nodes: frozenset[str]
) -> tuple[EvalGraph, tuple[Pair, ...]]:
    """Remove only uniquely identified SCC return edges for forward extraction."""
    if not loop_target_nodes:
        return graph, ()
    removed: set[Pair] = set()
    for component in _cyclic_components(graph):
        if not component & loop_target_nodes:
            continue
        entries = {
            edge.target for edge in graph.edges
            if edge.target in component and edge.source not in component
        }
        if len(entries) != 1:
            continue
        entry = next(iter(entries))
        returning = {
            (edge.source, edge.target) for edge in graph.edges
            if edge.source in component and edge.target == entry
        }
        # A self-loop at the sole entry is also an explicit recurrence edge.
        if not returning:
            continue
        candidate_edges = tuple(
            edge for edge in graph.edges if (edge.source, edge.target) not in returning
        )
        candidate = EvalGraph(graph.nodes, candidate_edges)
        if any(component & remaining and len(component & remaining) > 1
               for remaining in _cyclic_components(candidate)):
            continue
        removed.update(returning)
    trimmed = EvalGraph(
        graph.nodes, tuple(edge for edge in graph.edges if (edge.source, edge.target) not in removed)
    )
    return trimmed, tuple(sorted(removed))


def build_flow_inventory(
    reference: EvalGraph,
    units: Sequence[SemanticActivityUnit],
    control: Mapping[str, Any],
) -> FlowInventoryV3:
    node_to_units: dict[str, set[str]] = {}
    for unit in units:
        for reference_id in unit.reference_ids:
            node_to_units.setdefault(reference_id, set()).add(unit.unit_id)
    loop_targets = {
        unit for relation in control["control_relations"]
        if relation["status"] == "required" and relation["type"] == "loop_recurrence"
        for unit in relation.get("target_action_ids", [])
    }
    forward, removed = _trim_supported_returns(
        reference,
        loop_target_nodes=frozenset(node for node, owners in node_to_units.items()
                                    if owners & loop_targets),
    )
    unsafe_components = _cyclic_components(forward)
    unsafe_pairs: set[Pair] = set()
    for component in unsafe_components:
        ids = {unit for node in component for unit in node_to_units.get(node, ())}
        unsafe_pairs.update((a, b) for a in ids for b in ids if a != b)
    full: set[Pair] = set()
    action_nodes = sorted(node_to_units)
    closure = {node: reachable(forward, node) for node in action_nodes}
    for left in action_nodes:
        for right in action_nodes:
            if left == right:
                continue
            for left_unit in node_to_units[left]:
                for right_unit in node_to_units[right]:
                    if left_unit == right_unit:
                        continue
                    pair = (left_unit, right_unit)
                    if pair not in unsafe_pairs and right in closure[left] and left not in closure[right]:
                        full.add(pair)
    # A repeated semantic unit can have multiple reference occurrences. Do not
    # invent one strict direction when occurrences support both directions.
    mutual = {pair for pair in full if pair[::-1] in full}
    full -= mutual
    unsafe_pairs.update(mutual)
    return FlowInventoryV3(
        tuple(sorted(_transitive_reduction(full))),
        tuple(sorted(unsafe_pairs)),
        removed,
    )


def _boundary_nodes(
    unit_id: str, alignment: ActionAlignmentTable, graph: EvalGraph
) -> tuple[frozenset[str], frozenset[str], bool]:
    nodes = alignment.generated(unit_id)
    if not nodes:
        return frozenset(), frozenset(), False
    closure = {node: reachable(graph, node) for node in nodes}
    cyclic = any(a != b and a in closure[b] and b in closure[a] for a in nodes for b in nodes)
    starts = frozenset(node for node in nodes if not any(
        node in closure[other] for other in nodes if other != node
    ))
    ends = frozenset(node for node in nodes if not any(
        other in closure[node] for other in nodes if other != node
    ))
    return starts, ends, cyclic or not starts or not ends


def _strictly_before(
    left: str, right: str, alignment: ActionAlignmentTable, graph: EvalGraph
) -> tuple[bool, bool]:
    left_starts, left_ends, left_cycle = _boundary_nodes(left, alignment, graph)
    right_starts, right_ends, right_cycle = _boundary_nodes(right, alignment, graph)
    if left_cycle or right_cycle:
        return False, True
    if not left_ends or not right_starts:
        return False, False
    if left_ends & right_starts:
        return False, False
    closure = {node: reachable(graph, node) for node in left_ends | right_starts}
    uncertain = any(
        a in closure[b] and b in closure[a]
        for a in left_ends for b in right_starts
    )
    if uncertain:
        return False, True
    return all(b in closure[a] for a in left_ends for b in right_starts), False


def _loop_phase_witness(
    left: str, right: str, generated: EvalGraph, alignment: ActionAlignmentTable,
    reviewed: SemanticInventory | None,
) -> tuple[bool, Mapping[str, Any]]:
    """Look for one identifiable source phase and one candidate return boundary.

    Failure to identify the phase is evaluator indeterminacy, never a substitute
    FN. The source-only precedence inventory and Action mappings stay locked.
    """
    diagnostics: dict[str, Any] = {"reason_code": "FLOW_LOOP_PHASE_UNRESOLVED",
                                   "source_pair": [left, right]}
    if reviewed is None:
        diagnostics["unresolved_because"] = "reviewed occurrence metadata unavailable"
        return False, diagnostics
    occurrences = {
        unit: [item for item in reviewed.occurrences
               if item.semantic_unit_id == unit
               and item.provenance.review_state in {"accepted", "modified"}]
        for unit in (left, right)
    }
    diagnostics["source_occurrences"] = {
        unit: [{"occurrence_id": item.occurrence_id,
                "recurrence_role": item.recurrence_role,
                "loop_scope_ids": list(item.loop_scope_ids)} for item in values]
        for unit, values in occurrences.items()}
    if any(len(values) != 1 for values in occurrences.values()):
        diagnostics["unresolved_because"] = "source occurrence identity is not unique"
        return False, diagnostics
    left_occ, right_occ = occurrences[left][0], occurrences[right][0]
    if not left_occ.loop_scope_ids or left_occ.loop_scope_ids != right_occ.loop_scope_ids:
        diagnostics["unresolved_because"] = "source pair does not identify one shared loop scope"
        return False, diagnostics
    left_nodes, right_nodes = alignment.generated(left), alignment.generated(right)
    if len(left_nodes) != 1 or len(right_nodes) != 1 or left_nodes == right_nodes:
        diagnostics["unresolved_because"] = "accepted Action fragments do not identify unique occurrence nodes"
        return False, diagnostics
    left_node, right_node = next(iter(left_nodes)), next(iter(right_nodes))
    components = _cyclic_components(generated)
    containing = [component for component in components
                  if left_node in component and right_node in component]
    if len(containing) != 1:
        diagnostics["unresolved_because"] = "candidate pair has no unique shared cycle"
        return False, diagnostics
    cycle = containing[0]
    entries = {edge.target for edge in generated.edges
               if edge.target in cycle and edge.source not in cycle}
    if len(entries) != 1:
        diagnostics["unresolved_because"] = "candidate loop has no unique external entry"
        return False, diagnostics
    entry = next(iter(entries))
    returns = [edge for edge in generated.edges
               if edge.source in cycle and edge.target == entry]
    if len(returns) != 1:
        diagnostics["unresolved_because"] = "candidate recurrence return is not unique"
        return False, diagnostics
    returning = returns[0]
    phase_graph = EvalGraph(generated.nodes, tuple(edge for edge in generated.edges
                                                    if edge is not returning))
    if any(component & cycle for component in _cyclic_components(phase_graph)):
        diagnostics["unresolved_because"] = "removing the unique return leaves cyclic phase paths"
        return False, diagnostics
    diagnostics["candidate_phase_boundary"] = {
        "entry": entry, "return_source": returning.source,
        "left_generated_id": left_node, "right_generated_id": right_node}
    left_role, right_role = left_occ.recurrence_role, right_occ.recurrence_role
    if left_role in {"none", "initial", "loop_body"} and right_role in {"none", "initial", "loop_body"}:
        valid = right_node in reachable(phase_graph, left_node) and left_node not in reachable(phase_graph, right_node)
    elif left_role != "repeated" and right_role == "repeated":
        valid = (returning.source in reachable(phase_graph, left_node)
                 and right_node in reachable(phase_graph, entry))
    elif left_role == "repeated" and right_role == "repeated":
        valid = right_node in reachable(phase_graph, left_node) and left_node not in reachable(phase_graph, right_node)
    else:
        # A first visit cannot be placed after a repeated visit from the role
        # labels alone. Keep the frozen pair I until occurrence identity can be
        # established rather than treating SCC reachability as precedence.
        valid = False
    diagnostics["phase_witness_found"] = valid
    if not valid:
        diagnostics["unresolved_because"] = "unique candidate phase does not establish the frozen occurrence direction"
    return valid, diagnostics


def evaluate_flow_v3(
    inventory: FlowInventoryV3,
    generated: EvalGraph,
    alignment: ActionAlignmentTable,
    control: Mapping[str, Any] | None = None,
    reviewed: SemanticInventory | None = None,
) -> FlowResultV3:
    facts: list[FlowFactResult] = []
    tp = fn = fp = unresolved = cycle_violations = supported_cycle_indeterminate = 0
    control = control or {"control_nodes": (), "control_relations": ()}
    owner_by_id = {fact["fact_id"]: fact for fact in control.get("control_nodes", ())}
    supported_cycle_pairs: set[Pair] = set()
    for relation in control.get("control_relations", ()):
        if relation.get("status") != "required" or relation.get("type") != "loop_recurrence":
            continue
        owner = owner_by_id.get(relation.get("source_control_fact"), {})
        members = set(owner.get("anchor_action_ids", ())) | set(relation.get("target_action_ids", ()))
        supported_cycle_pairs.update((left, right) for left in members for right in members if left != right)
    units = {unit for pair in inventory.required_precedence for unit in pair}
    mapped = sum(bool(alignment.generated(unit)) for unit in units)
    for left, right in inventory.required_precedence:
        diagnostics: Mapping[str, Any] = {}
        if alignment.is_ambiguous(left) or alignment.is_ambiguous(right):
            status, reason = "indeterminate_alignment", "ambiguous accepted Action anchor"
            affected = [unit for unit in (left, right) if alignment.is_ambiguous(unit)]
            diagnostics = {"reason_code": "FLOW_ACTION_ANCHOR_UNRESOLVED",
                           "ambiguous_action_unit_ids": affected,
                           "plausible_generated_anchor_ids": {
                               unit: list(alignment.ambiguous_candidates.get(unit, ())) for unit in affected},
                           "accepted_generated_anchor_ids": {
                               unit: sorted(alignment.generated(unit)) for unit in (left, right)},
                           "structural_evidence_attempted": "locked accepted Action boundaries only"}
            unresolved += 1
        elif not alignment.generated(left) or not alignment.generated(right):
            status, reason = "FN", "required Action anchor missing"
            fn += 1
        else:
            left_nodes, right_nodes = alignment.generated(left), alignment.generated(right)
            closure = {node: reachable(generated, node) for node in left_nodes | right_nodes}
            cross_cycle = any(
                left_node != right_node and right_node in closure[left_node]
                and left_node in closure[right_node]
                for left_node in left_nodes for right_node in right_nodes
            )
            forward, forward_unsafe = _strictly_before(left, right, alignment, generated)
            reverse, reverse_unsafe = _strictly_before(right, left, alignment, generated)
            if cross_cycle:
                if (left, right) in supported_cycle_pairs:
                    witnessed, diagnostics = _loop_phase_witness(
                        left, right, generated, alignment, reviewed)
                    if witnessed:
                        status, reason = "TP", "frozen occurrence phase precedes target across identified loop boundary"
                        tp += 1
                    else:
                        status, reason = "indeterminate_alignment", "source-supported loop phase remains ambiguous after occurrence alignment"
                        unresolved += 1; supported_cycle_indeterminate += 1
                else:
                    status, reason = "FN+FP", "generated cycle reverses fixed source precedence"
                    fn += 1; fp += 1; cycle_violations += 1
            elif forward_unsafe or reverse_unsafe:
                status, reason = "indeterminate_alignment", "cyclic generated reachability cannot establish forward order"
                diagnostics = {"reason_code": "FLOW_INTERNAL_FRAGMENT_CYCLE_UNRESOLVED",
                               "accepted_generated_anchor_ids": {
                                   unit: sorted(alignment.generated(unit)) for unit in (left, right)},
                               "structural_evidence_attempted": "split-fragment boundary and both reachability directions"}
                unresolved += 1
            elif forward:
                status, reason = "TP", "accepted Action alignment preserves forward reachability"
                tp += 1
            elif reverse:
                status, reason = "FN+FP", "predefined required direction is reversed"
                fn += 1; fp += 1
            else:
                status, reason = "FN", "required forward precedence absent"
                fn += 1
        facts.append(FlowFactResult(left, right, status, reason, diagnostics))
    return FlowResultV3(
        Counts(tp, fp, fn), tuple(facts), inventory, unresolved,
        mapped / len(units) if units else 1.0, cycle_violations,
        supported_cycle_indeterminate,
    )
