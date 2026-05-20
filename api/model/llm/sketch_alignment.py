from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Set

from .topology_analysis import _adjacency, _reverse_adjacency, _reachable


SketchAlignmentReport = Dict[str, Any]


def _normalize_action_name(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _find_action_id_by_name(nodes: Iterable[Dict[str, Any]], action_name: Optional[str]) -> Optional[str]:
    if not action_name:
        return None
    expected = _normalize_action_name(action_name)
    for node in nodes:
        if str(node.get("type", "")) != "action":
            continue
        if _normalize_action_name(node.get("name")) == expected:
            return str(node.get("id", ""))
    return None


def _has_backward_edge(edges: Iterable[Dict[str, Any]], reachable_map: Dict[str, Set[str]]) -> bool:
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source and target and source in reachable_map.get(target, set()):
            return True
    return False


def validate_graph_against_sketch(sketch: Optional[Dict[str, Any]], graph: Dict[str, Any]) -> SketchAlignmentReport:
    """
    Run lightweight alignment checks between a topology sketch and a realized graph.

    These checks are heuristic and diagnostic-only. They are intended to reveal
    planner/decoder drift rather than enforce hard failures in generation.
    """
    if not sketch:
        return {
            "issues": [],
            "summary": "no sketch provided",
            "metrics": {"control_block_count": 0},
            "details": {"block_reports": []},
        }

    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    control_blocks = sketch.get("control_blocks") or []

    node_types = {
        str(node.get("id", "")): str(node.get("type", ""))
        for node in nodes
        if isinstance(node, dict)
    }
    type_counts = Counter(node_types.values())
    neighbors, _ = _adjacency(edges)
    incoming = _reverse_adjacency(edges)

    reachable_map: Dict[str, Set[str]] = {
        node_id: _reachable([node_id], neighbors)
        for node_id in node_types
    }
    has_backward_edge = _has_backward_edge(edges, reachable_map)

    main_flow_ids = [
        action_id
        for action_name in sketch.get("main_flow") or []
        if (action_id := _find_action_id_by_name(nodes, action_name)) is not None
    ]

    issues: List[str] = []
    block_reports: List[Dict[str, Any]] = []

    for index, block in enumerate(control_blocks, start=1):
        block_type = str(block.get("type", ""))
        requires_merge = bool(block.get("requires_merge", False))
        exit_to = block.get("exit_to")
        loop_back_to = block.get("loop_back_to")
        entry_after = block.get("entry_after")
        branches = block.get("branches") or []
        branch_count = len(branches)

        block_issues: List[str] = []
        expected_closure = None

        if block_type == "decision":
            if type_counts.get("decision", 0) < index:
                block_issues.append("missing_decision_node")
            if branch_count >= 2 and type_counts.get("decision", 0) == 0:
                block_issues.append("decision_branching_not_realized")
            if requires_merge and type_counts.get("merge", 0) == 0:
                block_issues.append("missing_merge_for_decision")
                expected_closure = "merge"
        elif block_type == "parallel":
            if type_counts.get("fork", 0) == 0:
                block_issues.append("missing_fork_for_parallel")
            if requires_merge and type_counts.get("join", 0) == 0:
                block_issues.append("missing_join_for_parallel")
                expected_closure = "join"
        elif block_type == "loop":
            if not has_backward_edge:
                block_issues.append("loop_missing_backward_edge")
            if branch_count > 0 and type_counts.get("decision", 0) == 0:
                block_issues.append("loop_missing_decision_structure")
            if loop_back_to and _find_action_id_by_name(nodes, loop_back_to) is None:
                block_issues.append("loop_back_to_action_not_found")
            if requires_merge:
                block_issues.append("loop_requires_merge_semantics")

        if expected_closure is None and requires_merge:
            expected_closure = "merge" if block_type == "decision" else "join" if block_type == "parallel" else None

        entry_after_id = _find_action_id_by_name(nodes, entry_after)
        exit_to_id = _find_action_id_by_name(nodes, exit_to)

        if entry_after and entry_after_id is None:
            block_issues.append("entry_after_action_not_found")
        if exit_to and exit_to_id is None:
            block_issues.append("exit_to_action_not_found")

        if entry_after_id and exit_to_id and exit_to_id not in reachable_map.get(entry_after_id, set()):
            block_issues.append("exit_to_not_reachable_from_entry")

        if exit_to_id and branch_count > 0:
            returning_branches = [branch for branch in branches if branch.get("returns_to_main_flow")]
            if returning_branches and exit_to_id not in main_flow_ids:
                block_issues.append("exit_to_not_in_realized_main_flow")

        if block_issues:
            issues.extend(block_issues)

        block_reports.append(
            {
                "block_index": index,
                "type": block_type,
                "entry_after": entry_after,
                "exit_to": exit_to,
                "loop_back_to": loop_back_to,
                "expected_branch_count": branch_count,
                "expected_closure": expected_closure,
                "issues": block_issues,
            }
        )

    deduped_issues = list(dict.fromkeys(issues))
    summary = (
        "graph preserves the sketch topology at a coarse level"
        if not deduped_issues
        else "graph deviates from sketch topology: " + ", ".join(deduped_issues)
    )

    return {
        "issues": deduped_issues,
        "summary": summary,
        "metrics": {
            "control_block_count": len(control_blocks),
            "decision_count": type_counts.get("decision", 0),
            "merge_count": type_counts.get("merge", 0),
            "fork_count": type_counts.get("fork", 0),
            "join_count": type_counts.get("join", 0),
            "has_backward_edge": has_backward_edge,
            "matched_main_flow_actions": len(main_flow_ids),
        },
        "details": {
            "main_flow_ids": main_flow_ids,
            "block_reports": block_reports,
        },
    }


__all__ = ["SketchAlignmentReport", "validate_graph_against_sketch"]
