from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

import numpy as np
from scipy.optimize import linear_sum_assignment

from .action_matching import PROVISIONAL_THRESHOLD, operation_compatibility
from .eval_graph import EvalGraph


@dataclass(frozen=True, slots=True)
class AnchorEvidence:
    direction: str
    reference_anchor: str
    generated_anchor: str
    reference_distance: int
    generated_distance: int


def _nearest_action_anchors(
    graph: EvalGraph,
    start: str,
    anchor_ids: set[str],
    *,
    reverse: bool,
) -> dict[str, int]:
    adjacency: dict[str, list[str]] = defaultdict(list)
    action_ids = {node.id for node in graph.nodes if node.type == "action"}
    for edge in graph.edges:
        source, target = (edge.target, edge.source) if reverse else (edge.source, edge.target)
        adjacency[source].append(target)

    queue = deque((node_id, 1) for node_id in sorted(adjacency.get(start, [])))
    visited = {start}
    found: dict[str, int] = {}
    nearest_distance: int | None = None
    while queue:
        node_id, distance = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)
        if nearest_distance is not None and distance > nearest_distance:
            break
        if node_id in anchor_ids:
            found[node_id] = distance
            nearest_distance = distance
            continue
        # Anchors may only be reached through routing/control nodes. An
        # unmatched action is itself the nearest action boundary.
        if node_id in action_ids:
            continue
        for adjacent in sorted(adjacency.get(node_id, [])):
            queue.append((adjacent, distance + 1))
    return found


def _topology_rank(
    reference_id: str,
    generated_id: str,
    reference_graph: EvalGraph,
    generated_graph: EvalGraph,
    locked: Mapping[str, str],
) -> tuple[tuple[int, int], list[AnchorEvidence]]:
    reference_anchors = set(locked)
    generated_anchors = set(locked.values())
    evidence: list[AnchorEvidence] = []
    distance_difference = 0
    for direction, reverse in (("predecessor", True), ("successor", False)):
        reference_nearest = _nearest_action_anchors(
            reference_graph, reference_id, reference_anchors, reverse=reverse
        )
        generated_nearest = _nearest_action_anchors(
            generated_graph, generated_id, generated_anchors, reverse=reverse
        )
        for reference_anchor, reference_distance in sorted(reference_nearest.items()):
            generated_anchor = locked[reference_anchor]
            if generated_anchor not in generated_nearest:
                continue
            generated_distance = generated_nearest[generated_anchor]
            evidence.append(
                AnchorEvidence(
                    direction=direction,
                    reference_anchor=reference_anchor,
                    generated_anchor=generated_anchor,
                    reference_distance=reference_distance,
                    generated_distance=generated_distance,
                )
            )
            distance_difference += abs(reference_distance - generated_distance)
    return (len(evidence), -distance_difference), evidence


def _unique_best(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[key])].append(row)
    result: dict[str, dict[str, Any]] = {}
    for node_id, options in grouped.items():
        ordered = sorted(
            options,
            key=lambda row: (-float(row["semantic_similarity"]), str(row["pair_id"])),
        )
        if len(ordered) == 1 or not np.isclose(
            float(ordered[0]["semantic_similarity"]),
            float(ordered[1]["semantic_similarity"]),
        ):
            result[node_id] = ordered[0]
    return result


def _lock_unambiguous(
    candidates: list[dict[str, Any]], locked: dict[str, str]
) -> None:
    while True:
        remaining = [
            row
            for row in candidates
            if str(row["reference_id"]) not in locked
            and str(row["generated_id"]) not in set(locked.values())
        ]
        best_reference = _unique_best(remaining, "reference_id")
        best_generated = _unique_best(remaining, "generated_id")
        mutual = [
            row
            for reference_id, row in best_reference.items()
            if best_generated.get(str(row["generated_id"])) is row
            and reference_id not in locked
            and _operation_anchor_agrees(row)
        ]
        if not mutual:
            return
        for row in sorted(
            mutual,
            key=lambda item: (-float(item["semantic_similarity"]), str(item["pair_id"])),
        ):
            reference_id = str(row["reference_id"])
            generated_id = str(row["generated_id"])
            if reference_id in locked or generated_id in locked.values():
                continue
            locked[reference_id] = generated_id
            row["selection_stage"] = "unambiguous_semantic_anchor"


def _operation_anchor_agrees(row: Mapping[str, Any]) -> bool:
    """Require exact resolved operations only for high-confidence anchor seeding."""
    reference = row.get("reference_representation")
    generated = row.get("generated_representation")
    if not isinstance(reference, Mapping) or not isinstance(generated, Mapping):
        return True
    if not reference.get("operation_resolved") or not generated.get("operation_resolved"):
        return False
    return reference.get("canonical_operation") == generated.get("canonical_operation")


def _apply_topology(
    candidates: list[dict[str, Any]],
    reference_graph: EvalGraph,
    generated_graph: EvalGraph,
    locked: dict[str, str],
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    while True:
        remaining = [
            row
            for row in candidates
            if str(row["reference_id"]) not in locked
            and str(row["generated_id"]) not in locked.values()
        ]
        if not remaining or not locked:
            break
        by_reference: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_generated: dict[str, list[dict[str, Any]]] = defaultdict(list)
        ranks: dict[str, tuple[tuple[int, int, float], list[AnchorEvidence]]] = {}
        for row in remaining:
            reference_id = str(row["reference_id"])
            generated_id = str(row["generated_id"])
            topology_rank, evidence = _topology_rank(
                reference_id,
                generated_id,
                reference_graph,
                generated_graph,
                locked,
            )
            ranks[str(row["pair_id"])] = (
                (*topology_rank, float(row["semantic_similarity"])),
                evidence,
            )
            by_reference[reference_id].append(row)
            by_generated[generated_id].append(row)

        def unique_top(options: list[dict[str, Any]]) -> dict[str, Any] | None:
            ordered = sorted(
                options,
                key=lambda row: (ranks[str(row["pair_id"])][0], str(row["pair_id"])),
                reverse=True,
            )
            if not ordered or ranks[str(ordered[0]["pair_id"])][0][0] == 0:
                return None
            if len(ordered) > 1 and ranks[str(ordered[0]["pair_id"])][0] == ranks[str(ordered[1]["pair_id"])][0]:
                return None
            return ordered[0]

        reference_winners = {
            node_id: winner
            for node_id, options in by_reference.items()
            if (winner := unique_top(options)) is not None
        }
        generated_winners = {
            node_id: winner
            for node_id, options in by_generated.items()
            if (winner := unique_top(options)) is not None
        }
        mutual = [
            row
            for row in reference_winners.values()
            if generated_winners.get(str(row["generated_id"])) is row
            and (
                len(by_reference[str(row["reference_id"])]) > 1
                or len(by_generated[str(row["generated_id"])]) > 1
            )
        ]
        if not mutual:
            break
        for row in sorted(mutual, key=lambda item: str(item["pair_id"])):
            reference_id = str(row["reference_id"])
            generated_id = str(row["generated_id"])
            if reference_id in locked or generated_id in locked.values():
                continue
            rank, evidence = ranks[str(row["pair_id"])]
            reference_options = by_reference[reference_id]
            generated_competitors = by_generated[generated_id]
            alternatives = [
                option
                for option in reference_options
                if option is not row
            ]
            ambiguity_sides = []
            if len(reference_options) > 1:
                ambiguity_sides.append("reference")
            if len(generated_competitors) > 1:
                ambiguity_sides.append("generated")
            decision = {
                "reference_node": reference_id,
                "selected_candidate": generated_id,
                "ambiguity_sides": ambiguity_sides,
                "reference_candidate_count": len(reference_options),
                "candidate_nodes": sorted(
                    str(item["generated_id"]) for item in reference_options
                ),
                "generated_competitor_count": len(generated_competitors),
                "competing_reference_nodes": sorted(
                    str(item["reference_id"]) for item in generated_competitors
                ),
                "anchor_evidence": [asdict(item) for item in evidence],
                "anchor_count": rank[0],
                "path_distance_difference": -rank[1],
                "semantic_similarity": rank[2],
                "rejected_alternatives": [
                    {
                        "generated_node": str(option["generated_id"]),
                        "rank": ranks[str(option["pair_id"])][0],
                    }
                    for option in sorted(alternatives, key=lambda item: str(item["generated_id"]))
                ],
            }
            decisions.append(decision)
            locked[reference_id] = generated_id
            row["selection_stage"] = "topology_tie_break"
            row["topology_evidence"] = decision
    return decisions


def _candidate_components(
    candidates: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    by_reference: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_generated: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_reference[str(row["reference_id"])].append(row)
        by_generated[str(row["generated_id"])].append(row)

    unseen = {str(row["pair_id"]): row for row in candidates}
    components: list[list[dict[str, Any]]] = []
    while unseen:
        first = unseen[min(unseen)]
        queue = deque([first])
        component: dict[str, dict[str, Any]] = {}
        while queue:
            row = queue.popleft()
            pair_id = str(row["pair_id"])
            if pair_id in component:
                continue
            component[pair_id] = row
            unseen.pop(pair_id, None)
            queue.extend(by_reference[str(row["reference_id"])])
            queue.extend(by_generated[str(row["generated_id"])])
        components.append([component[pair_id] for pair_id in sorted(component)])
    return components


def _maximum_assignment(
    candidates: list[dict[str, Any]],
    forbidden_pair_id: str | None = None,
) -> tuple[list[dict[str, Any]], float]:
    reference_ids = sorted({str(row["reference_id"]) for row in candidates})
    generated_ids = sorted({str(row["generated_id"]) for row in candidates})
    reference_index = {value: index for index, value in enumerate(reference_ids)}
    generated_index = {value: index for index, value in enumerate(generated_ids)}
    weights = np.full((len(reference_ids), len(generated_ids)), -1_000_000.0)
    pairs: dict[tuple[int, int], dict[str, Any]] = {}
    for row in sorted(candidates, key=lambda item: str(item["pair_id"])):
        position = (
            reference_index[str(row["reference_id"])],
            generated_index[str(row["generated_id"])],
        )
        if str(row["pair_id"]) == forbidden_pair_id:
            continue
        weights[position] = float(row["semantic_similarity"])
        pairs[position] = row
    reference_positions, generated_positions = linear_sum_assignment(weights, maximize=True)
    selected = [
        pairs[(reference_position, generated_position)]
        for reference_position, generated_position in zip(
            reference_positions, generated_positions
        )
        if weights[reference_position, generated_position] >= 0
        and (reference_position, generated_position) in pairs
    ]
    return selected, sum(float(row["semantic_similarity"]) for row in selected)


def _assign_remaining(candidates: list[dict[str, Any]], locked: dict[str, str]) -> None:
    remaining = [
        row
        for row in candidates
        if str(row["reference_id"]) not in locked
        and str(row["generated_id"]) not in locked.values()
    ]
    for component_index, component in enumerate(_candidate_components(remaining), 1):
        selected, optimum = _maximum_assignment(component)
        invariant: list[dict[str, Any]] = []
        for row in selected:
            _, alternative = _maximum_assignment(
                component, forbidden_pair_id=str(row["pair_id"])
            )
            if not np.isclose(alternative, optimum, rtol=1e-5, atol=1e-8):
                invariant.append(row)

        invariant_reference = {str(row["reference_id"]) for row in invariant}
        invariant_generated = {str(row["generated_id"]) for row in invariant}
        for row in invariant:
            locked[str(row["reference_id"])] = str(row["generated_id"])
            row["selection_stage"] = "global_assignment_invariant"

        residual = [
            row
            for row in component
            if str(row["reference_id"]) not in invariant_reference
            and str(row["generated_id"]) not in invariant_generated
        ]
        if not residual:
            continue
        reference_nodes = sorted({str(row["reference_id"]) for row in residual})
        generated_nodes = sorted({str(row["generated_id"]) for row in residual})
        candidate_pairs = sorted(str(row["pair_id"]) for row in residual)
        component_id = f"{component[0]['case_id']}:assignment-unresolved-{component_index}"
        for row in residual:
            row.update(
                {
                    "unresolved_ambiguity": True,
                    "unresolved_component_id": component_id,
                    "unresolved_reason": (
                        "multiple_numerically_equivalent_optimal_assignments"
                    ),
                    "unresolved_reference_nodes": reference_nodes,
                    "unresolved_generated_nodes": generated_nodes,
                    "unresolved_candidate_pairs": candidate_pairs,
                }
            )


def apply_revised_matching(
    rows: Iterable[dict[str, Any]],
    reference_graphs: Mapping[str, EvalGraph],
    generated_graphs: Mapping[str, EvalGraph],
    threshold: float = PROVISIONAL_THRESHOLD,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply the frozen semantic guard, local topology tie-break, and assignment."""
    evaluated: list[dict[str, Any]] = []
    for source in rows:
        row = dict(source)
        compatibility = operation_compatibility(
            str(row["reference_normalized"]), str(row["generated_normalized"])
        )
        row.update(
            {
                "semantic_candidate": float(row["semantic_similarity"]) >= threshold,
                "operation_compatible": compatibility.compatible,
                "compatibility_reason": compatibility.reason,
                "operation_threshold": None,
                "operation_threshold_pass": None,
                "candidate_after_compatibility": (
                    float(row["semantic_similarity"]) >= threshold
                    and compatibility.compatible
                ),
                "selection_stage": "",
                "topology_evidence": None,
                "unresolved_ambiguity": False,
                "unresolved_component_id": "",
                "unresolved_reason": "",
                "unresolved_reference_nodes": [],
                "unresolved_generated_nodes": [],
                "unresolved_candidate_pairs": [],
                "final_prediction": False,
            }
        )
        evaluated.append(row)

    decisions: list[dict[str, Any]] = []
    for case_id in sorted({str(row["case_id"]) for row in evaluated}):
        candidates = [
            row
            for row in evaluated
            if str(row["case_id"]) == case_id and row["candidate_after_compatibility"]
        ]
        locked: dict[str, str] = {}
        _lock_unambiguous(candidates, locked)
        case_decisions = _apply_topology(
            candidates, reference_graphs[case_id], generated_graphs[case_id], locked
        )
        for decision in case_decisions:
            decision["case_id"] = case_id
        decisions.extend(case_decisions)
        _assign_remaining(candidates, locked)
        for row in candidates:
            row["final_prediction"] = locked.get(str(row["reference_id"])) == str(row["generated_id"])
    return evaluated, decisions
