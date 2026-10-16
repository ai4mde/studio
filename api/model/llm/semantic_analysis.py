from __future__ import annotations

# Responsibility:
# - provide topology-aware semantic diagnostics over ActivityGraph payloads
# - classify issues with severity and suggested follow-up action
# - support observability and optional future refinement passes
#
# Must NOT:
# - mutate graphs
# - silently repair topology
# - replace structural validation

from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Set

from .keyword_hints import KeywordHints
from .topology_analysis import _adjacency, _reachable, _reverse_adjacency, analyze_activity_graph


SemanticIssue = Dict[str, Any]
SemanticGraphReport = Dict[str, Any]

ISSUE_POLICY: Dict[str, Dict[str, str]] = {
    "merge_underconnected": {"severity": "warning", "recommended_action": "refine"},
    "unnecessary_merge": {"severity": "warning", "recommended_action": "refine"},
    "retry_loop_with_merge": {"severity": "warning", "recommended_action": "refine"},
    "orphan_merge": {"severity": "warning", "recommended_action": "repair"},
    "decision_unlabeled_branch": {"severity": "warning", "recommended_action": "repair"},
    "decision_not_question_like": {"severity": "warning", "recommended_action": "repair"},
    "missing_loop_exit": {"severity": "error", "recommended_action": "refine"},
    "invalid_loop_back_target": {"severity": "error", "recommended_action": "regenerate"},
    "dead_end_path": {"severity": "error", "recommended_action": "refine"},
    "unreachable_nodes": {"severity": "error", "recommended_action": "refine"},
    "fork_without_join": {"severity": "warning", "recommended_action": "refine"},
    "join_without_fork": {"severity": "warning", "recommended_action": "refine"},
}


def _make_issue(code: str, *, message: str, node_id: Optional[str] = None) -> SemanticIssue:
    policy = ISSUE_POLICY.get(code, {"severity": "warning", "recommended_action": "warn"})
    issue: SemanticIssue = {
        "code": code,
        "severity": policy["severity"],
        "recommended_action": policy["recommended_action"],
        "message": message,
    }
    if node_id:
        issue["node_id"] = node_id
    return issue


def _has_backward_edge_to(node_id: str, incoming: Dict[str, List[str]], reachable_map: Dict[str, Set[str]]) -> bool:
    for source in incoming.get(node_id, []):
        if source in reachable_map.get(node_id, set()):
            return True
    return False


def _decision_outgoing_labels(outgoing_edges: Iterable[Dict[str, Any]]) -> List[str]:
    return [str(edge.get("label", "")).strip() for edge in outgoing_edges]


def _is_question_like(text: Optional[str]) -> bool:
    return bool(str(text or "").strip().endswith("?"))


def analyze_semantic_graph(
    graph: Dict[str, Any],
    *,
    sketch: Optional[Dict[str, Any]] = None,
    keyword_hints: Optional[KeywordHints] = None,
) -> SemanticGraphReport:
    topology = analyze_activity_graph(graph)
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []

    node_types = {
        str(node.get("id", "")): str(node.get("type", ""))
        for node in nodes
        if isinstance(node, dict)
    }
    type_counts = Counter(node_types.values())
    neighbors, outgoing_edges = _adjacency(edges)
    incoming = _reverse_adjacency(edges)
    initial_nodes = [node_id for node_id, node_type in node_types.items() if node_type == "initial"]
    reachable_map = {node_id: _reachable([node_id], neighbors) for node_id in node_types}
    globally_reachable = _reachable(initial_nodes, neighbors)

    issues: List[SemanticIssue] = []

    if topology["details"]["disconnected_nodes"]:
        issues.append(
            _make_issue(
                "unreachable_nodes",
                message="Some nodes are unreachable from the initial node.",
            )
        )

    if topology["details"]["dead_end_nodes"]:
        issues.append(
            _make_issue(
                "dead_end_path",
                message="One or more non-final nodes terminate control flow unexpectedly.",
            )
        )

    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id", ""))
        node_type = str(node.get("type", ""))
        outgoing = outgoing_edges.get(node_id, [])
        incoming_sources = incoming.get(node_id, [])

        if node_type == "decision":
            labels = _decision_outgoing_labels(outgoing)
            if outgoing and any(not label for label in labels):
                issues.append(
                    _make_issue(
                        "decision_unlabeled_branch",
                        message="Decision branches should normally use labels.",
                        node_id=node_id,
                    )
                )
            decision_text = str(node.get("label") or node.get("name") or "").strip()
            if decision_text and not _is_question_like(decision_text):
                issues.append(
                    _make_issue(
                        "decision_not_question_like",
                        message="Decision nodes should normally use short question-style text ending with '?'.",
                        node_id=node_id,
                    )
                )

        elif node_type == "merge":
            incoming_count = len(incoming_sources)
            outgoing_count = len(outgoing)
            if incoming_count < 2:
                issues.append(
                    _make_issue(
                        "merge_underconnected",
                        message="Merge node has fewer than two incoming branches.",
                        node_id=node_id,
                    )
                )
            if incoming_count == 0 or outgoing_count == 0:
                issues.append(
                    _make_issue(
                        "orphan_merge",
                        message="Merge node is missing incoming or outgoing connectivity.",
                        node_id=node_id,
                    )
                )
            if incoming_count >= 2 and outgoing_count == 1 and type_counts.get("decision", 0) == 0:
                issues.append(
                    _make_issue(
                        "unnecessary_merge",
                        message="Merge node appears without corresponding branching semantics.",
                        node_id=node_id,
                    )
                )

        elif node_type == "fork" and type_counts.get("join", 0) == 0:
            issues.append(
                _make_issue(
                    "fork_without_join",
                    message="Fork structure appears without a corresponding join.",
                    node_id=node_id,
                )
            )
        elif node_type == "join" and type_counts.get("fork", 0) == 0:
            issues.append(
                _make_issue(
                    "join_without_fork",
                    message="Join structure appears without a corresponding fork.",
                    node_id=node_id,
                )
            )

    for block in (sketch or {}).get("control_blocks") or []:
        if not isinstance(block, dict) or str(block.get("type", "")) != "loop":
            continue
        exit_step = str(block.get("exit_to_step_id") or "").strip()
        loop_back_step = str(block.get("loop_back_to_step_id") or "").strip()
        requires_merge = bool(block.get("requires_merge", False))

        exit_nodes = [
            str(node.get("id", ""))
            for node in nodes
            if isinstance(node, dict) and str(node.get("origin_step_id", "")).strip() == exit_step
        ]
        if exit_step and not exit_nodes:
            issues.append(
                _make_issue(
                    "missing_loop_exit",
                    message="Loop sketch expects an exit target that is not realized in the graph.",
                )
            )

        back_nodes = [
            str(node.get("id", ""))
            for node in nodes
            if isinstance(node, dict) and str(node.get("origin_step_id", "")).strip() == loop_back_step
        ]
        if loop_back_step:
            if not back_nodes:
                issues.append(
                    _make_issue(
                        "invalid_loop_back_target",
                        message="Loop sketch references a loop-back step that is not realized in the graph.",
                    )
                )
            elif not any(_has_backward_edge_to(node_id, incoming, reachable_map) for node_id in back_nodes):
                issues.append(
                    _make_issue(
                        "invalid_loop_back_target",
                        message="Loop sketch loop-back target exists but no backward edge returns to it.",
                    )
                )
        if not requires_merge and type_counts.get("merge", 0) > 0:
            issues.append(
                _make_issue(
                    "retry_loop_with_merge",
                    message="Simple retry loops should normally use a backward branch and exit path without an explicit merge.",
                )
            )

    if keyword_hints and keyword_hints.get("flags", {}).get("retry_semantics"):
        has_backward_edge = any(
            source in reachable_map.get(target, set())
            for target, incoming_sources in incoming.items()
            for source in incoming_sources
        )
        if not has_backward_edge:
            issues.append(
                _make_issue(
                    "missing_loop_exit",
                    message="Retry-oriented text suggests loop semantics, but the graph lacks a clear backward path.",
                )
            )

    deduped_issues: List[SemanticIssue] = []
    seen = set()
    for issue in issues:
        signature = (issue["code"], issue.get("node_id"))
        if signature in seen:
            continue
        seen.add(signature)
        deduped_issues.append(issue)

    severity_counts = Counter(issue["severity"] for issue in deduped_issues)
    action_counts = Counter(issue["recommended_action"] for issue in deduped_issues)
    summary = (
        "semantic topology appears coherent"
        if not deduped_issues
        else "semantic issues detected: " + ", ".join(issue["code"] for issue in deduped_issues)
    )

    return {
        "summary": summary,
        "issues": deduped_issues,
        "metrics": {
            "issue_count": len(deduped_issues),
            "warning_count": severity_counts.get("warning", 0),
            "error_count": severity_counts.get("error", 0),
            "refine_recommendations": action_counts.get("refine", 0),
            "repair_recommendations": action_counts.get("repair", 0),
            "regenerate_recommendations": action_counts.get("regenerate", 0),
            "reachable_node_count": len(globally_reachable),
            "merge_count": type_counts.get("merge", 0),
            "decision_count": type_counts.get("decision", 0),
            "fork_count": type_counts.get("fork", 0),
            "join_count": type_counts.get("join", 0),
        },
        "details": {
            "topology_summary": topology["summary"],
            "topology_issues": topology["issues"],
        },
    }


__all__ = ["SemanticGraphReport", "SemanticIssue", "analyze_semantic_graph"]
