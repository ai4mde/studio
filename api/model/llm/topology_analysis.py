from __future__ import annotations

# Responsibility:
# - provide lightweight diagnostic analysis over ActivityGraph topology
# - report coarse structural issues for experiments and architecture audits
#
# Must NOT:
# - mutate ActivityGraph payloads
# - act as the canonical hard validator
# - repair topology

from collections import Counter, defaultdict, deque
from typing import Any, Dict, Iterable, List, Set, Tuple


TopologyReport = Dict[str, Any]


def _adjacency(edges: Iterable[Dict[str, Any]]) -> Tuple[dict[str, list[str]], dict[str, list[Dict[str, Any]]]]:
    neighbors: dict[str, list[str]] = defaultdict(list)
    edge_index: dict[str, list[Dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        neighbors[source].append(target)
        edge_index[source].append(edge)
    return neighbors, edge_index


def _reverse_adjacency(edges: Iterable[Dict[str, Any]]) -> dict[str, list[str]]:
    incoming: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        incoming[target].append(source)
    return incoming


def _reachable(start_nodes: List[str], neighbors: dict[str, list[str]]) -> Set[str]:
    if not start_nodes:
        return set()
    seen: Set[str] = set()
    queue = deque(start_nodes)
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        for nxt in neighbors.get(node, []):
            if nxt not in seen:
                queue.append(nxt)
    return seen


def _issue_summary(issues: List[str]) -> str:
    if not issues:
        return "topology appears structurally coherent"
    if len(issues) == 1:
        return f"topology issue detected: {issues[0]}"
    return "topology unstable: " + ", ".join(issues)


def _decision_has_unmerged_nonterminal_convergence(
    decision_id: str,
    *,
    neighbors: dict[str, list[str]],
    node_types: Dict[str, str],
) -> bool:
    branch_starts = list(dict.fromkeys(neighbors.get(decision_id, [])))
    if len(branch_starts) < 2:
        return False
    reachable_sets = [_reachable([branch_start], neighbors) for branch_start in branch_starts]
    common = set.intersection(*reachable_sets)
    if decision_id in common:
        return False
    if any(node_types.get(node_id) == "merge" for node_id in common):
        return False
    return any(node_types.get(node_id) != "final" for node_id in common)


def analyze_activity_graph(graph: Dict[str, Any]) -> TopologyReport:
    """
    Run lightweight topology checks on an ActivityGraph.

    These checks are heuristic and intentionally inexpensive. They are meant
    for experiment reporting, not as hard validation rules inside generation.
    """
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []

    node_ids = [str(node.get("id", "")) for node in nodes if isinstance(node, dict)]
    node_types = {str(node.get("id", "")): str(node.get("type", "")) for node in nodes if isinstance(node, dict)}
    type_counts = Counter(node_types.values())

    neighbors, outgoing_edges = _adjacency(edges)
    incoming_neighbors = _reverse_adjacency(edges)

    out_degree = {node_id: len(neighbors.get(node_id, [])) for node_id in node_ids}
    in_degree = {node_id: len(incoming_neighbors.get(node_id, [])) for node_id in node_ids}

    issues: List[str] = []

    initial_nodes = [node_id for node_id, node_type in node_types.items() if node_type == "initial"]
    final_nodes = [node_id for node_id, node_type in node_types.items() if node_type == "final"]

    if len(initial_nodes) == 0:
        issues.append("missing_initial")
    elif len(initial_nodes) > 1:
        issues.append("multiple_initials")

    if len(final_nodes) == 0:
        issues.append("missing_final")

    reachable = _reachable(initial_nodes, neighbors)
    disconnected_nodes = sorted(node_id for node_id in node_ids if node_id not in reachable)
    if disconnected_nodes:
        issues.append("disconnected_nodes")

    dangling_nodes = sorted(
        node_id
        for node_id in node_ids
        if in_degree.get(node_id, 0) == 0 and node_types.get(node_id) != "initial"
    )
    if dangling_nodes:
        issues.append("dangling_entry_nodes")

    dead_end_nodes = sorted(
        node_id
        for node_id in node_ids
        if out_degree.get(node_id, 0) == 0 and node_types.get(node_id) != "final"
    )
    if dead_end_nodes:
        issues.append("dead_end_nodes")

    for node_id, node_type in node_types.items():
        if node_type == "decision":
            outgoing = outgoing_edges.get(node_id, [])
            if len(outgoing) < 2:
                issues.append("decision_missing_branch")
            unlabeled = [edge for edge in outgoing if not str(edge.get("label") or "").strip()]
            if outgoing and unlabeled:
                issues.append("decision_unlabeled_branch")
        elif node_type == "merge":
            if in_degree.get(node_id, 0) < 2:
                issues.append("merge_underconnected")
        elif node_type == "fork":
            if out_degree.get(node_id, 0) < 2:
                issues.append("fork_underconnected")
        elif node_type == "join":
            if in_degree.get(node_id, 0) < 2:
                issues.append("join_underconnected")

    if any(
        _decision_has_unmerged_nonterminal_convergence(
            node_id,
            neighbors=neighbors,
            node_types=node_types,
        )
        for node_id, node_type in node_types.items()
        if node_type == "decision"
    ):
        issues.append("possible_missing_merge")
    if type_counts.get("fork", 0) > type_counts.get("join", 0):
        issues.append("possible_missing_join")

    deduped_issues = list(dict.fromkeys(issues))

    return {
        "issues": deduped_issues,
        "summary": _issue_summary(deduped_issues),
        "metrics": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "type_counts": dict(type_counts),
            "initial_count": len(initial_nodes),
            "final_count": len(final_nodes),
            "disconnected_node_count": len(disconnected_nodes),
            "dangling_entry_count": len(dangling_nodes),
            "dead_end_count": len(dead_end_nodes),
            "decision_count": type_counts.get("decision", 0),
            "merge_count": type_counts.get("merge", 0),
            "fork_count": type_counts.get("fork", 0),
            "join_count": type_counts.get("join", 0),
        },
        "details": {
            "disconnected_nodes": disconnected_nodes,
            "dangling_entry_nodes": dangling_nodes,
            "dead_end_nodes": dead_end_nodes,
        },
    }


__all__ = ["TopologyReport", "analyze_activity_graph"]
