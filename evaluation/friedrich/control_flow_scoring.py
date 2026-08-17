from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from statistics import fmean
from typing import Any, Iterable, Literal

from .action_scoring import ActionCaseScore
from .eval_graph import EvalGraph


FlowNamespace = Literal["ref", "gen"]
_ROUTING_TYPES = frozenset({"decision", "merge", "fork", "join"})
_BOUNDARY_TYPES = frozenset({"initial", "final"})
_SUPPORTED_TYPES = _ROUTING_TYPES | _BOUNDARY_TYPES | {"action"}


@dataclass(frozen=True, order=True, slots=True)
class FlowNode:
    namespace: FlowNamespace
    node_id: str


@dataclass(frozen=True, order=True, slots=True)
class FlowRelation:
    source: FlowNode
    target: FlowNode


@dataclass(frozen=True, slots=True)
class ControlFlowCaseScore:
    case_id: str
    reference_flow_count: int
    generated_flow_count: int
    TP: int
    FP: int
    FN: int
    precision: float | None
    recall: float | None
    f1: float | None
    empty: bool
    reference_flow_relations: tuple[FlowRelation, ...]
    generated_flow_relations: tuple[FlowRelation, ...]
    matched_flow_relations: tuple[FlowRelation, ...]
    unmatched_reference_flow_relations: tuple[FlowRelation, ...]
    unmatched_generated_flow_relations: tuple[FlowRelation, ...]
    flows_incident_to_unmatched_reference_actions: tuple[FlowRelation, ...]
    flows_incident_to_unmatched_generated_actions: tuple[FlowRelation, ...]
    flows_incident_to_unresolved_reference_actions: tuple[FlowRelation, ...]
    flows_incident_to_unresolved_generated_actions: tuple[FlowRelation, ...]
    granularity_incident_flow_count: int
    granularity_incident_reference_flow_relations: tuple[FlowRelation, ...]
    granularity_incident_generated_flow_relations: tuple[FlowRelation, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ControlFlowDatasetScore:
    case_count: int
    empty_flow_case_count: int
    defined_macro_case_count: int
    total_reference_flows: int
    total_generated_flows: int
    micro_TP: int
    micro_FP: int
    micro_FN: int
    micro_precision: float | None
    micro_recall: float | None
    micro_f1: float | None
    macro_f1: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def project_action_flows(graph: EvalGraph) -> frozenset[tuple[str, str]]:
    """Project directed paths to first-reached Action adjacency relations."""
    nodes = {node.id: node for node in graph.nodes}
    unsupported = sorted(
        (node.id, str(node.type))
        for node in graph.nodes
        if node.type not in _SUPPORTED_TYPES
    )
    if unsupported:
        raise ValueError(f"Unsupported EvalGraph node types: {unsupported}")

    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in graph.edges:
        outgoing[edge.source].append(edge.target)
    for targets in outgoing.values():
        targets.sort()

    relations: set[tuple[str, str]] = set()
    for source in sorted(node.id for node in graph.nodes if node.type == "action"):
        pending = deque(outgoing.get(source, ()))
        visited_routing: set[str] = set()
        while pending:
            target = pending.popleft()
            node = nodes[target]
            if node.type == "action":
                relations.add((source, target))
                continue
            if node.type in _BOUNDARY_TYPES:
                continue
            if node.type not in _ROUTING_TYPES:
                raise ValueError(
                    f"Unsupported node {target!r} encountered during flow projection"
                )
            if target in visited_routing:
                continue
            visited_routing.add(target)
            pending.extend(outgoing.get(target, ()))
    return frozenset(relations)


def _native_relation(
    relation: tuple[str, str], namespace: FlowNamespace
) -> FlowRelation:
    return FlowRelation(
        FlowNode(namespace, relation[0]),
        FlowNode(namespace, relation[1]),
    )


def _incident(
    relations: Iterable[FlowRelation], node_ids: set[str], namespace: FlowNamespace
) -> tuple[FlowRelation, ...]:
    return tuple(
        sorted(
            relation
            for relation in relations
            if (
                relation.source.namespace == namespace
                and relation.source.node_id in node_ids
            )
            or (
                relation.target.namespace == namespace
                and relation.target.node_id in node_ids
            )
        )
    )


def _metrics(
    TP: int, FP: int, FN: int, *, empty: bool
) -> tuple[float | None, float | None, float | None]:
    if empty:
        return None, None, None
    precision = TP / (TP + FP) if TP + FP else 0.0
    recall = TP / (TP + FN) if TP + FN else 0.0
    denominator = 2 * TP + FP + FN
    f1 = 2 * TP / denominator if denominator else 0.0
    return precision, recall, f1


def score_control_flow_case(
    case_id: str,
    reference_graph: EvalGraph,
    generated_graph: EvalGraph,
    action_score: ActionCaseScore,
) -> ControlFlowCaseScore:
    """Score immediate Action adjacency using frozen Action correspondences."""
    if action_score.case_id != case_id:
        raise ValueError("Action score case id does not match the Control-flow case")

    reference_action_ids = {
        node.id for node in reference_graph.nodes if node.type == "action"
    }
    generated_action_ids = {
        node.id for node in generated_graph.nodes if node.type == "action"
    }
    matched_reference = set(action_score.matched_reference_ids)
    matched_generated = set(action_score.matched_generated_ids)
    unmatched_reference = set(action_score.unmatched_reference_ids)
    unmatched_generated = set(action_score.unmatched_generated_ids)
    if matched_reference | unmatched_reference != reference_action_ids:
        raise ValueError("Frozen Action score does not partition reference Actions")
    if matched_generated | unmatched_generated != generated_action_ids:
        raise ValueError("Frozen Action score does not partition generated Actions")
    if matched_reference & unmatched_reference or matched_generated & unmatched_generated:
        raise ValueError("Frozen Action matched and unmatched partitions overlap")

    generated_to_reference = {
        generated_id: reference_id
        for reference_id, generated_id in action_score.accepted_pairs
    }
    if set(generated_to_reference) != matched_generated:
        raise ValueError("Frozen accepted pairs disagree with matched generated Actions")
    if set(generated_to_reference.values()) != matched_reference:
        raise ValueError("Frozen accepted pairs disagree with matched reference Actions")

    reference_native = project_action_flows(reference_graph)
    generated_native = project_action_flows(generated_graph)
    reference_flows = {
        _native_relation(relation, "ref") for relation in reference_native
    }

    def map_generated(node_id: str) -> FlowNode:
        if node_id in generated_to_reference:
            return FlowNode("ref", generated_to_reference[node_id])
        return FlowNode("gen", node_id)

    generated_flows = {
        FlowRelation(map_generated(source), map_generated(target))
        for source, target in generated_native
    }
    generated_raw = {
        _native_relation(relation, "gen") for relation in generated_native
    }

    matched_flows = tuple(sorted(reference_flows & generated_flows))
    unmatched_reference_flows = tuple(sorted(reference_flows - generated_flows))
    unmatched_generated_flows = tuple(sorted(generated_flows - reference_flows))
    TP = len(matched_flows)
    FP = len(unmatched_generated_flows)
    FN = len(unmatched_reference_flows)
    if TP + FN != len(reference_flows) or TP + FP != len(generated_flows):
        raise AssertionError(f"Case {case_id} violates Control-flow accounting")

    unresolved_reference = set(action_score.unresolved_reference_ids)
    unresolved_generated = set(action_score.unresolved_generated_ids)
    if not unresolved_reference <= unmatched_reference:
        raise ValueError("Resolved reference Actions cannot be marked unresolved")
    if not unresolved_generated <= unmatched_generated:
        raise ValueError("Resolved generated Actions cannot be marked unresolved")

    reference_granularity_ids = {
        node_id
        for mismatch in action_score.granularity_mismatches
        for node_id in mismatch.reference_ids
    }
    generated_granularity_ids = {
        node_id
        for mismatch in action_score.granularity_mismatches
        for node_id in mismatch.generated_ids
    }
    reference_granularity_flows = _incident(
        reference_flows, reference_granularity_ids, "ref"
    )
    generated_granularity_flows = _incident(
        generated_raw, generated_granularity_ids, "gen"
    )

    empty = not reference_flows and not generated_flows
    precision, recall, f1 = _metrics(TP, FP, FN, empty=empty)
    return ControlFlowCaseScore(
        case_id=case_id,
        reference_flow_count=len(reference_flows),
        generated_flow_count=len(generated_flows),
        TP=TP,
        FP=FP,
        FN=FN,
        precision=precision,
        recall=recall,
        f1=f1,
        empty=empty,
        reference_flow_relations=tuple(sorted(reference_flows)),
        generated_flow_relations=tuple(sorted(generated_flows)),
        matched_flow_relations=matched_flows,
        unmatched_reference_flow_relations=unmatched_reference_flows,
        unmatched_generated_flow_relations=unmatched_generated_flows,
        flows_incident_to_unmatched_reference_actions=_incident(
            reference_flows, unmatched_reference, "ref"
        ),
        flows_incident_to_unmatched_generated_actions=_incident(
            generated_raw, unmatched_generated, "gen"
        ),
        flows_incident_to_unresolved_reference_actions=_incident(
            reference_flows, unresolved_reference, "ref"
        ),
        flows_incident_to_unresolved_generated_actions=_incident(
            generated_raw, unresolved_generated, "gen"
        ),
        granularity_incident_flow_count=(
            len(reference_granularity_flows) + len(generated_granularity_flows)
        ),
        granularity_incident_reference_flow_relations=reference_granularity_flows,
        granularity_incident_generated_flow_relations=generated_granularity_flows,
    )


def aggregate_control_flow_scores(
    case_scores: Iterable[ControlFlowCaseScore],
) -> ControlFlowDatasetScore:
    scores = tuple(case_scores)
    micro_TP = sum(score.TP for score in scores)
    micro_FP = sum(score.FP for score in scores)
    micro_FN = sum(score.FN for score in scores)
    empty = not any(
        score.reference_flow_count or score.generated_flow_count for score in scores
    )
    micro_precision, micro_recall, micro_f1 = _metrics(
        micro_TP, micro_FP, micro_FN, empty=empty
    )
    defined_f1 = [score.f1 for score in scores if score.f1 is not None]
    return ControlFlowDatasetScore(
        case_count=len(scores),
        empty_flow_case_count=sum(score.empty for score in scores),
        defined_macro_case_count=len(defined_f1),
        total_reference_flows=sum(score.reference_flow_count for score in scores),
        total_generated_flows=sum(score.generated_flow_count for score in scores),
        micro_TP=micro_TP,
        micro_FP=micro_FP,
        micro_FN=micro_FN,
        micro_precision=micro_precision,
        micro_recall=micro_recall,
        micro_f1=micro_f1,
        macro_f1=fmean(defined_f1) if defined_f1 else None,
    )
