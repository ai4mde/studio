from __future__ import annotations

# Responsibility:
# - compare a realized ActivityGraph against a TopologyPlan
# - report coarse planner/realizer drift for diagnostics only
#
# Must NOT:
# - mutate either artifact
# - repair missing topology
# - act as the canonical hard validator for either layer

from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Set

from .topology_analysis import _adjacency, _reverse_adjacency, _reachable


SketchAlignmentReport = Dict[str, Any]


def _main_flow_step_name(entry: Any) -> Optional[str]:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        action = entry.get("action")
        if action is not None:
            return str(action)
    return None


def _main_flow_step_id(entry: Any) -> Optional[str]:
    if isinstance(entry, dict):
        step_id = entry.get("step_id")
        if step_id is not None:
            text = str(step_id).strip()
            return text or None
    return None


def _build_step_lookup(main_flow: Iterable[Any]) -> Dict[str, str]:
    step_lookup: Dict[str, str] = {}
    for entry in main_flow:
        step_id = _main_flow_step_id(entry)
        action_name = _main_flow_step_name(entry)
        if step_id and action_name:
            step_lookup[step_id] = action_name
    return step_lookup


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


def _find_action_id_by_origin_step_id(
    nodes: Iterable[Dict[str, Any]],
    step_id: Optional[str],
) -> Optional[str]:
    if not step_id:
        return None
    expected = str(step_id).strip()
    if not expected:
        return None
    for node in nodes:
        if str(node.get("type", "")) != "action":
            continue
        if str(node.get("origin_step_id", "")).strip() == expected:
            return str(node.get("id", ""))
    return None


def _has_backward_edge(edges: Iterable[Dict[str, Any]], reachable_map: Dict[str, Set[str]]) -> bool:
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source and target and source in reachable_map.get(target, set()):
            return True
    return False


def _has_backward_edge_to_target(
    edges: Iterable[Dict[str, Any]],
    reachable_map: Dict[str, Set[str]],
    target_id: Optional[str],
) -> bool:
    if not target_id:
        return False
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if target != target_id:
            continue
        if source and source in reachable_map.get(target, set()):
            return True
    return False


def _resolve_step_reference(
    block: Dict[str, Any],
    *,
    text_key: str,
    step_id_key: str,
    step_lookup: Dict[str, str],
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    step_id = block.get(step_id_key)
    if step_id is not None:
        normalized_step_id = str(step_id).strip()
        if normalized_step_id:
            return step_lookup.get(normalized_step_id), normalized_step_id, "step_id"
    text_value = block.get(text_key)
    if text_value is not None:
        normalized_text = str(text_value).strip()
        if normalized_text:
            return normalized_text, None, "text"
    return None, None, None


def _resolve_graph_action_reference(
    nodes: Iterable[Dict[str, Any]],
    *,
    action_name: Optional[str],
    step_id: Optional[str],
) -> tuple[Optional[str], str]:
    if step_id:
        action_id = _find_action_id_by_origin_step_id(nodes, step_id)
        if action_id is not None:
            return action_id, "origin_step_id"

    if action_name:
        action_id = _find_action_id_by_name(nodes, action_name)
        if action_id is not None:
            return action_id, "name_fallback"

    return None, "unresolved"


def _planner_binding_strength(
    *,
    step_reference_count: int,
    resolved_by_origin_step_id: int,
    resolved_by_name_fallback: int,
    unresolved_step_ids: int,
) -> str:
    if step_reference_count <= 0:
        return "weak"
    if unresolved_step_ids == 0 and resolved_by_origin_step_id == step_reference_count:
        return "strong"
    if resolved_by_origin_step_id > 0 or (resolved_by_name_fallback > 0 and unresolved_step_ids == 0):
        return "partial"
    return "weak"


def validate_graph_against_sketch(sketch: Optional[Dict[str, Any]], graph: Dict[str, Any]) -> SketchAlignmentReport:
    """
    Run lightweight alignment checks between a TopologyPlan and a realized ActivityGraph.

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
    step_lookup = _build_step_lookup(sketch.get("main_flow") or [])
    action_nodes = [
        node
        for node in nodes
        if isinstance(node, dict) and str(node.get("type", "")) == "action"
    ]
    traceable_action_nodes = [
        node for node in action_nodes if str(node.get("origin_step_id", "")).strip()
    ]
    declared_block_ids = [
        str(block_id).strip()
        for block in control_blocks
        if (block_id := block.get("block_id")) is not None and str(block_id).strip()
    ]
    declared_block_id_set = set(declared_block_ids)
    realized_block_ids = {
        str(node.get("origin_block_id", "")).strip()
        for node in nodes
        if isinstance(node, dict) and str(node.get("origin_block_id", "")).strip()
    }
    decision_node_ids_by_block: Dict[str, List[str]] = {}
    unbound_decision_node_ids: List[str] = []
    for node in nodes:
        if not isinstance(node, dict) or str(node.get("type", "")) != "decision":
            continue
        node_id = str(node.get("id", "")).strip()
        origin_block_id = str(node.get("origin_block_id", "")).strip()
        if origin_block_id:
            decision_node_ids_by_block.setdefault(origin_block_id, []).append(node_id)
        elif node_id:
            unbound_decision_node_ids.append(node_id)
    consumed_unbound_decision_count = 0

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

    resolution_counters: Counter[str] = Counter()
    unresolved_step_ids: Set[str] = set()
    main_flow_ids: List[str] = []
    main_flow_resolution_modes: Dict[str, str] = {}
    expected_reconnects = 0
    realized_reconnects = 0
    expected_loop_backs = 0
    realized_loop_backs = 0
    expected_merges = 0
    realized_merges = 0
    unresolved_child_block_ids: Set[str] = set()
    for entry in sketch.get("main_flow") or []:
        action_name = _main_flow_step_name(entry)
        step_id = _main_flow_step_id(entry)
        action_id, resolution_mode = _resolve_graph_action_reference(
            nodes,
            action_name=action_name,
            step_id=step_id,
        )
        if step_id:
            resolution_counters[resolution_mode] += 1
            main_flow_resolution_modes[step_id] = resolution_mode
            if resolution_mode == "unresolved":
                unresolved_step_ids.add(step_id)
        if action_id is not None:
            main_flow_ids.append(action_id)

    issues: List[str] = []
    block_reports: List[Dict[str, Any]] = []

    for index, block in enumerate(control_blocks, start=1):
        block_type = str(block.get("type", ""))
        block_id = block.get("block_id")
        requires_merge = bool(block.get("requires_merge", False))
        entry_after, entry_after_step_id, _ = _resolve_step_reference(
            block,
            text_key="entry_after",
            step_id_key="entry_after_step_id",
            step_lookup=step_lookup,
        )
        exit_to, exit_to_step_id, _ = _resolve_step_reference(
            block,
            text_key="exit_to",
            step_id_key="exit_to_step_id",
            step_lookup=step_lookup,
        )
        loop_back_to, loop_back_to_step_id, _ = _resolve_step_reference(
            block,
            text_key="loop_back_to",
            step_id_key="loop_back_to_step_id",
            step_lookup=step_lookup,
        )
        branches = block.get("branches") or []
        branch_count = len(branches)
        child_block_ids = sorted(
            {
                str(child_block_id).strip()
                for branch in branches
                if isinstance(branch, dict)
                for child_block_id in (branch.get("child_block_ids") or [])
                if str(child_block_id).strip()
            }
        )

        block_issues: List[str] = []
        expected_closure = None
        matched_decision_node_ids: List[str] = []
        decision_resolution_mode = "not_applicable"

        if block_type == "decision":
            normalized_block_id = str(block_id or "").strip()
            matched_decision_node_ids = decision_node_ids_by_block.get(normalized_block_id, [])
            if matched_decision_node_ids:
                decision_resolution_mode = "origin_block_id"
            elif consumed_unbound_decision_count < len(unbound_decision_node_ids):
                matched_decision_node_ids = [unbound_decision_node_ids[consumed_unbound_decision_count]]
                consumed_unbound_decision_count += 1
                decision_resolution_mode = "unbound_decision_fallback"
            else:
                decision_resolution_mode = "unresolved"
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
            if loop_back_to_step_id and loop_back_to is None:
                block_issues.append("loop_back_to_step_id_not_found")
            elif loop_back_to and _find_action_id_by_name(nodes, loop_back_to) is None:
                block_issues.append("loop_back_to_action_not_found")
            if requires_merge:
                block_issues.append("loop_requires_merge_semantics")

        if expected_closure is None and requires_merge:
            expected_closure = "merge" if block_type == "decision" else "join" if block_type == "parallel" else None

        entry_after_id, entry_after_resolution_mode = _resolve_graph_action_reference(
            nodes,
            action_name=entry_after,
            step_id=entry_after_step_id,
        )
        exit_to_id, exit_to_resolution_mode = _resolve_graph_action_reference(
            nodes,
            action_name=exit_to,
            step_id=exit_to_step_id,
        )
        loop_back_to_id, loop_back_to_resolution_mode = _resolve_graph_action_reference(
            nodes,
            action_name=loop_back_to,
            step_id=loop_back_to_step_id,
        )

        for step_id, mode in (
            (entry_after_step_id, entry_after_resolution_mode),
            (exit_to_step_id, exit_to_resolution_mode),
            (loop_back_to_step_id, loop_back_to_resolution_mode),
        ):
            if step_id:
                resolution_counters[mode] += 1
                if mode == "unresolved":
                    unresolved_step_ids.add(step_id)

        if entry_after_step_id and entry_after is None:
            block_issues.append("entry_after_step_id_not_found")
        elif entry_after and entry_after_id is None:
            block_issues.append("entry_after_action_not_found")
        if exit_to_step_id and exit_to is None:
            block_issues.append("exit_to_step_id_not_found")
        elif exit_to and exit_to_id is None:
            block_issues.append("exit_to_action_not_found")
        if loop_back_to_step_id and loop_back_to is None:
            block_issues.append("loop_back_to_step_id_not_found")
        elif loop_back_to and loop_back_to_id is None:
            block_issues.append("loop_back_to_action_not_found")
        for child_block_id in child_block_ids:
            if child_block_id not in declared_block_id_set:
                block_issues.append("child_block_id_not_found")
                unresolved_child_block_ids.add(child_block_id)
            elif child_block_id not in realized_block_ids:
                block_issues.append("child_block_not_realized")
                unresolved_child_block_ids.add(child_block_id)

        if entry_after_id and exit_to_id and exit_to_id not in reachable_map.get(entry_after_id, set()):
            block_issues.append("exit_to_not_reachable_from_entry")
        reconnect_realized = False
        if entry_after_id and exit_to_id:
            expected_reconnects += 1
            reconnect_realized = exit_to_id in reachable_map.get(entry_after_id, set())
            if reconnect_realized:
                realized_reconnects += 1

        if exit_to_id and branch_count > 0:
            returning_branches = [branch for branch in branches if branch.get("returns_to_main_flow")]
            if returning_branches and exit_to_id not in main_flow_ids:
                block_issues.append("exit_to_not_in_realized_main_flow")

        loop_back_realized = False
        if loop_back_to_id:
            expected_loop_backs += 1
            loop_back_realized = _has_backward_edge_to_target(edges, reachable_map, loop_back_to_id)
            if loop_back_realized:
                realized_loop_backs += 1
            elif block_type == "loop":
                block_issues.append("loop_back_edge_not_realized")

        closure_realized = False
        if expected_closure is not None:
            expected_merges += 1
            closure_realized = (
                expected_closure == "merge" and type_counts.get("merge", 0) > 0
            ) or (
                expected_closure == "join" and type_counts.get("join", 0) > 0
            )
            if closure_realized:
                realized_merges += 1

        if block_issues:
            issues.extend(block_issues)

        block_reports.append(
            {
                "block_index": index,
                "block_id": block_id,
                "type": block_type,
                "entry_after": entry_after,
                "entry_after_step_id": entry_after_step_id,
                "exit_to": exit_to,
                "exit_to_step_id": exit_to_step_id,
                "loop_back_to": loop_back_to,
                "loop_back_to_step_id": loop_back_to_step_id,
                "child_block_ids": child_block_ids,
                "entry_after_resolution_mode": entry_after_resolution_mode,
                "exit_to_resolution_mode": exit_to_resolution_mode,
                "loop_back_to_resolution_mode": loop_back_to_resolution_mode,
                "reconnect_realized": reconnect_realized,
                "loop_back_realized": loop_back_realized,
                "closure_realized": closure_realized,
                "expected_branch_count": branch_count,
                "expected_closure": expected_closure,
                "matched_decision_node_ids": matched_decision_node_ids,
                "decision_resolution_mode": decision_resolution_mode,
                "issues": block_issues,
            }
        )

    deduped_issues = list(dict.fromkeys(issues))
    unresolved_block_ids = sorted(
        block_id for block_id in declared_block_ids if block_id not in realized_block_ids
    )
    traceability_coverage = (
        len(traceable_action_nodes) / len(action_nodes)
        if action_nodes
        else 0.0
    )
    planner_binding_strength = _planner_binding_strength(
        step_reference_count=sum(resolution_counters.values()),
        resolved_by_origin_step_id=resolution_counters["origin_step_id"],
        resolved_by_name_fallback=resolution_counters["name_fallback"],
        unresolved_step_ids=len(unresolved_step_ids),
    )
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
            "resolved_main_flow_step_ids": len(step_lookup),
            "traceability_coverage": traceability_coverage,
            "traceable_action_nodes": len(traceable_action_nodes),
            "action_node_count": len(action_nodes),
            "resolved_by_origin_step_id": resolution_counters["origin_step_id"],
            "resolved_by_name_fallback": resolution_counters["name_fallback"],
            "unresolved_step_ids": sorted(unresolved_step_ids),
            "unresolved_block_ids": unresolved_block_ids,
            "unresolved_child_block_ids": sorted(unresolved_child_block_ids),
            "planner_binding_strength": planner_binding_strength,
            "expected_reconnects": expected_reconnects,
            "realized_reconnects": realized_reconnects,
            "expected_loop_backs": expected_loop_backs,
            "realized_loop_backs": realized_loop_backs,
            "expected_merges": expected_merges,
            "realized_merges": realized_merges,
        },
        "details": {
            "main_flow_ids": main_flow_ids,
            "main_flow_resolution_modes": main_flow_resolution_modes,
            "step_lookup": step_lookup,
            "block_reports": block_reports,
        },
    }


__all__ = ["SketchAlignmentReport", "validate_graph_against_sketch"]
