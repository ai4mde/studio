from __future__ import annotations

from dataclasses import dataclass

from .action import ActionResult
from .core import AutomaticItem, EvalEdge, EvalGraph, evaluation_item_id
from .flow import _precedence
from .structure import _anchor_map, extract_structure_facts


@dataclass(frozen=True, slots=True)
class RedundancyCandidate:
    case_id: str
    candidate_id: str
    node_id: str
    node_type: str
    confidence: str
    reason: str
    behaviorally_neutral: bool


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
