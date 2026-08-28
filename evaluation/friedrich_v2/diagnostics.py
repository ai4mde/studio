from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass

from .action import ActionResult
from .core import AutomaticItem, EvalEdge, EvalGraph, evaluation_item_id, reachable, strongly_connected_components
from .flow import _precedence
from .structure import _anchor_map, _nearest_common, extract_structure_facts


@dataclass(frozen=True, slots=True)
class RedundancyCandidate:
    case_id: str
    candidate_id: str
    node_id: str
    node_type: str
    confidence: str
    reason: str
    behaviorally_neutral: bool


@dataclass(frozen=True, slots=True)
class ValidityResult:
    status: str
    diagnostic_count: int
    items: tuple[AutomaticItem, ...]


def _can_reach_any(graph: EvalGraph, source: str, targets: set[str]) -> bool:
    return source in targets or bool(reachable(graph, source) & targets)


def _nearest_action_outcomes(graph: EvalGraph, decision_id: str, anchors: dict[str, str]) -> dict[str, tuple[str, ...]]:
    edge_labels = {(edge.source, edge.target): edge.label for edge in graph.edges}
    result: dict[str, tuple[str, ...]] = {}
    for successor in graph.outgoing[decision_id]:
        guard = edge_labels.get((decision_id, successor))
        if not guard:
            continue
        queue, seen, outcomes = deque([successor]), set(), set()
        while queue and not outcomes:
            for _ in range(len(queue)):
                current = queue.popleft()
                if current in seen:
                    continue
                seen.add(current)
                if current in anchors:
                    outcomes.add(anchors[current])
                else:
                    queue.extend(graph.outgoing[current])
        result[guard] = tuple(sorted(outcomes))
    return result


def find_model_validity_diagnostics(
    case_id: str, candidate_id: str, graph: EvalGraph,
    reference: EvalGraph | None = None, actions: ActionResult | None = None,
) -> ValidityResult:
    """Return deterministic diagnostics that do not alter Action/Flow/Structure counts."""
    findings: list[tuple[str, str, dict, dict, bool]] = []
    initials = {node.id for node in graph.nodes if node.type == "initial"}
    finals = {node.id for node in graph.nodes if node.type == "final"}
    if len(initials) != 1:
        findings.append(("initial_node_anomaly", f"Expected one initial node, found {len(initials)}.",
                         {"initial_nodes": sorted(initials)}, {}, False))
    if not finals:
        findings.append(("final_node_anomaly", "No final node is present.", {}, {}, False))
    reachable_from_initial = set(initials)
    for initial in initials:
        reachable_from_initial.update(reachable(graph, initial))
    for node in sorted(set(graph.by_id) - reachable_from_initial):
        findings.append(("unreachable_node", "Node is unreachable from every initial node.",
                         {"node_id": node}, {"node": graph.by_id[node].label}, False))
    for node in sorted(graph.nodes, key=lambda item: item.id):
        if not graph.outgoing[node.id] and node.type != "final":
            findings.append(("non_final_dead_end", "Non-final node has no outgoing control flow.",
                             {"node_id": node.id}, {"node_type": node.type, "label": node.label}, False))
        if finals and not _can_reach_any(graph, node.id, finals):
            findings.append(("no_final_reachability", "Node cannot reach any final node.",
                             {"node_id": node.id}, {"node_type": node.type, "label": node.label}, False))

    unseen = set(graph.by_id)
    components: list[set[str]] = []
    undirected = {node: set(graph.incoming[node]) | set(graph.outgoing[node]) for node in graph.by_id}
    while unseen:
        start = min(unseen)
        component, queue = {start}, deque([start])
        unseen.remove(start)
        while queue:
            current = queue.popleft()
            for neighbor in sorted(undirected[current] & unseen):
                unseen.remove(neighbor)
                component.add(neighbor)
                queue.append(neighbor)
        components.append(component)
    if len(components) > 1:
        findings.append(("disconnected_components", "Model contains disconnected components.",
                         {"component_count": len(components)}, {"components": [sorted(item) for item in components]}, False))

    for component in strongly_connected_components(graph):
        cyclic = len(component) > 1 or any(edge.source == edge.target and edge.source in component for edge in graph.edges)
        if cyclic and not any(target not in component for node in component for target in graph.outgoing[node]):
            findings.append(("cycle_without_exit", "Cycle has no outgoing path.",
                             {"nodes": sorted(component)}, {}, False))

    for node in sorted(graph.nodes, key=lambda item: item.id):
        incoming, outgoing = graph.incoming[node.id], graph.outgoing[node.id]
        if node.type == "decision" and (len(incoming) != 1 or len(outgoing) < 2):
            findings.append(("malformed_decision_degree", "Decision degree is not one-in/multiple-out.",
                             {"node_id": node.id}, {"incoming": incoming, "outgoing": outgoing}, False))
        if node.type == "merge" and (len(incoming) < 2 or len(outgoing) != 1):
            findings.append(("malformed_merge_degree", "Merge degree is not multiple-in/one-out.",
                             {"node_id": node.id}, {"incoming": incoming, "outgoing": outgoing}, False))
        if node.type == "fork" and (len(incoming) != 1 or len(outgoing) < 2):
            findings.append(("malformed_fork_degree", "Fork degree is not one-in/multiple-out.",
                             {"node_id": node.id}, {"incoming": incoming, "outgoing": outgoing}, False))
        if node.type == "join" and (len(incoming) < 2 or len(outgoing) != 1):
            findings.append(("malformed_join_degree", "Join degree is not multiple-in/one-out.",
                             {"node_id": node.id}, {"incoming": incoming, "outgoing": outgoing}, False))
        if node.type in {"decision", "fork"} and len(outgoing) >= 2:
            closure = _nearest_common(graph, outgoing, "merge" if node.type == "decision" else "join")
            for successor in outgoing:
                branch_nodes = set() if successor == closure else reachable(
                    graph, successor, {closure} if closure else set()
                ) | {successor}
                if not any(graph.by_id[item].type == "action" for item in branch_nodes):
                    findings.append(("actionless_branch", "Control branch contains no executable action.",
                                     {"node_id": node.id, "successor": successor}, {}, True))
            if node.type == "fork" and (closure is None or graph.by_id[closure].type != "join"):
                findings.append(("malformed_fork_join_pairing", "Fork has no reachable join.",
                                 {"node_id": node.id}, {}, False))

    edge_labels = {(edge.source, edge.target): edge.label for edge in graph.edges}
    for node in sorted((item for item in graph.nodes if item.type == "decision"), key=lambda item: item.id):
        outgoing = graph.outgoing[node.id]
        labels = [edge_labels.get((node.id, target)) for target in outgoing]
        missing = [target for target, label in zip(outgoing, labels) if not label]
        duplicates = sorted(label for label, count in Counter(label for label in labels if label).items() if count > 1)
        if missing:
            findings.append(("missing_exclusive_guard", "Exclusive branch guard is missing.",
                             {"node_id": node.id, "targets": missing}, {"guards": labels}, True))
        if duplicates:
            findings.append(("duplicate_or_conflicting_guard", "Exclusive guards are duplicated or conflicting.",
                             {"node_id": node.id, "guards": duplicates}, {"targets": outgoing}, True))
        if labels:
            findings.append(("guard_outcome_evidence", "Guard-to-outcome mapping retained for manual semantic verification.",
                             {"node_id": node.id},
                             {"branches": [{"guard": label, "target": target,
                                             "target_type": graph.by_id[target].type,
                                             "target_label": graph.by_id[target].label}
                                            for target, label in zip(outgoing, labels)]}, False))

    if reference is not None and actions is not None:
        reference_maps = [
            _nearest_action_outcomes(reference, node.id, {key: key for key in actions.reference_to_generated})
            for node in reference.nodes if node.type == "decision"
        ]
        generated_maps = [
            _nearest_action_outcomes(graph, node.id, actions.generated_to_reference)
            for node in graph.nodes if node.type == "decision"
        ]
        for generated_map in generated_maps:
            for reference_map in reference_maps:
                if generated_map and set(generated_map) == set(reference_map) and generated_map != reference_map:
                    findings.append(("suspicious_reversed_outcome_mapping",
                                     "The same normalized guards lead to different nearest matched action outcomes.",
                                     {}, {"reference_mapping": reference_map, "generated_mapping": generated_map}, True))
                    break

    labels = Counter(node.label for node in graph.nodes if node.type == "action" and node.label)
    for label, count in sorted(labels.items()):
        if count > 1:
            findings.append(("likely_duplicate_action", "Generated model repeats an exactly normalized action label.",
                             {"label": label, "count": count}, {}, True))

    items = tuple(
        AutomaticItem(
            case_id, candidate_id, "Model Validity",
            evaluation_item_id(case_id, candidate_id, "validity", kind, str(index)), "DIAGNOSTIC",
            {**payload, "diagnostic_type": kind,
             "review_triggers": [kind] if review else []}, evidence, rationale,
        )
        for index, (kind, rationale, payload, evidence, review) in enumerate(findings)
    )
    scored_count = sum(item.payload["diagnostic_type"] != "guard_outcome_evidence" for item in items)
    return ValidityResult("issues_detected" if scored_count else "pass", scored_count, items)


def _contract(graph: EvalGraph, node_id: str) -> EvalGraph:
    incoming = [edge for edge in graph.edges if edge.target == node_id]
    outgoing = [edge for edge in graph.edges if edge.source == node_id]
    retained = [edge for edge in graph.edges if edge.source != node_id and edge.target != node_id]
    existing = {(edge.source, edge.target, edge.label) for edge in retained}
    for left in incoming:
        for right in outgoing:
            candidate = (left.source, right.target, left.label or right.label)
            if candidate not in existing and candidate[0] != candidate[1]:
                retained.append(EvalEdge(*candidate))
                existing.add(candidate)
    return EvalGraph(tuple(node for node in graph.nodes if node.id != node_id), tuple(retained))


def find_redundant_control_nodes(
    case_id: str, candidate_id: str, generated: EvalGraph, actions: ActionResult
) -> tuple[tuple[RedundancyCandidate, ...], tuple[AutomaticItem, ...]]:
    action_ids = {node.id for node in generated.nodes if node.type == "action"}
    baseline_flow = _precedence(generated, action_ids)
    anchors = _anchor_map(actions, True)
    baseline_structure, baseline_unscorable, _ = extract_structure_facts(generated, anchors)
    candidates: list[RedundancyCandidate] = []
    items: list[AutomaticItem] = []
    incoming, outgoing = generated.incoming, generated.outgoing
    for node in sorted(generated.nodes, key=lambda item: item.id):
        if node.type not in {"merge", "join", "decision", "fork"}:
            continue
        degree_one = len(incoming[node.id]) == 1 and len(outgoing[node.id]) == 1
        if node.type == "merge" and degree_one:
            confidence, reason = "High", "Merge has one incoming and one outgoing control flow."
        elif degree_one or (node.type == "join" and len(incoming[node.id]) == 1) or (node.type == "fork" and len(outgoing[node.id]) == 1):
            confidence, reason = "Low", "Degenerate gateway shape is ambiguous across UML/BPMN notation."
        else:
            continue
        contracted = _contract(generated, node.id)
        structure, unscorable, _ = extract_structure_facts(contracted, anchors)
        neutral = (
            _precedence(contracted, action_ids) == baseline_flow
            and structure == baseline_structure
            and unscorable == baseline_unscorable
        )
        if not neutral:
            continue
        candidate = RedundancyCandidate(
            case_id, candidate_id, node.id, node.type, confidence, reason, True
        )
        candidates.append(candidate)
        items.append(AutomaticItem(
            case_id, candidate_id, "Redundant Control Nodes",
            evaluation_item_id(case_id, candidate_id, "redundancy", node.id), "CANDIDATE",
            {"node_id": node.id, "node_type": node.type, "confidence": confidence},
            {"incoming": incoming[node.id], "outgoing": outgoing[node.id],
             "neighbors": {neighbor: {"type": generated.by_id[neighbor].type, "label": generated.by_id[neighbor].label}
                           for neighbor in sorted(set(incoming[node.id]) | set(outgoing[node.id]))}},
            reason + " Contraction preserves action reachability and extracted Structure facts; Human Review is still required.",
        ))
    return tuple(candidates), tuple(items)
