from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from .activity_model import ActivityModel
from .experimental_compiler import compile_activity_sketch
from .refinement_generator import _get_clean_model
from .semantic_analysis import analyze_semantic_graph
from .semantic_sketch_plan_model import SemanticSketchPlan
from .sketch_repair import repair_activity_sketch
from .topology_analysis import analyze_activity_graph
from .topology_artifact_model import TopologyArtifact
from .topology_to_sketch_compiler import compile_topology_and_semantics_to_activity_sketch


class HumanEditSynchronizationError(ValueError):
    def __init__(self, message: str, *, diagnostics: Dict[str, Any]) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics


@dataclass
class _StructureResult:
    topology_structure: Dict[str, Any]
    branch_plans: List[Dict[str, Any]]
    child_structures: List[Dict[str, Any]]
    child_branch_plans: List[Dict[str, Any]]
    next_node_id: Optional[str]


class _GraphCursor:
    def __init__(self, clean_graph: Dict[str, Any]) -> None:
        self.graph = ActivityModel.model_validate(clean_graph).model_dump(exclude_none=True)
        self.nodes = {
            str(node["id"]): dict(node)
            for node in self.graph.get("nodes") or []
            if isinstance(node, dict)
        }
        self.outgoing_edges: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.incoming_edges: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for edge in self.graph.get("edges") or []:
            if not isinstance(edge, dict) or str(edge.get("type") or "control") != "control":
                continue
            source = str(edge.get("source") or "")
            target = str(edge.get("target") or "")
            self.outgoing_edges[source].append(dict(edge))
            self.incoming_edges[target].append(dict(edge))

    def node(self, node_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if node_id is None:
            return None
        return self.nodes.get(str(node_id))

    def node_type(self, node_id: Optional[str]) -> str:
        node = self.node(node_id)
        if node is None:
            return ""
        return str(node.get("type") or "")

    def node_text(self, node_id: Optional[str]) -> str:
        node = self.node(node_id)
        if node is None:
            return ""
        return str(node.get("name") or node.get("label") or "").strip()

    def outgoing(self, node_id: Optional[str]) -> List[Dict[str, Any]]:
        if node_id is None:
            return []
        return list(self.outgoing_edges.get(str(node_id), []))

    def incoming(self, node_id: Optional[str]) -> List[Dict[str, Any]]:
        if node_id is None:
            return []
        return list(self.incoming_edges.get(str(node_id), []))

    def successors(self, node_id: Optional[str]) -> List[str]:
        return [str(edge.get("target") or "") for edge in self.outgoing(node_id)]

    def initial_nodes(self) -> List[str]:
        return [
            node_id
            for node_id, node in self.nodes.items()
            if str(node.get("type") or "") == "initial"
        ]

    def reachable_from(self, start_id: str) -> Set[str]:
        seen: Set[str] = set()
        queue = deque([start_id])
        while queue:
            node_id = queue.popleft()
            if node_id in seen:
                continue
            seen.add(node_id)
            for successor in self.successors(node_id):
                if successor not in seen:
                    queue.append(successor)
        return seen

    def distance(self, start_id: str) -> Dict[str, int]:
        distances = {start_id: 0}
        queue = deque([start_id])
        while queue:
            node_id = queue.popleft()
            for successor in self.successors(node_id):
                if successor in distances:
                    continue
                distances[successor] = distances[node_id] + 1
                queue.append(successor)
        return distances


def _canonicalize_graph(graph: Dict[str, Any]) -> Dict[str, Any]:
    validated = ActivityModel.model_validate(graph).model_dump(exclude_none=True)
    nodes = validated.get("nodes") or []
    edges = validated.get("edges") or []
    node_by_id = {str(node["id"]): node for node in nodes if isinstance(node, dict)}
    outgoing: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        outgoing[str(edge.get("source") or "")].append(edge)

    def node_sort_key(node_id: str) -> Tuple[str, str, str]:
        node = node_by_id[node_id]
        return (
            str(node.get("type") or ""),
            str(node.get("name") or ""),
            str(node.get("label") or ""),
        )

    start_ids = sorted(node_by_id.keys(), key=node_sort_key)
    ordered_ids: List[str] = []
    seen: Set[str] = set()
    queue = deque(start_ids)
    while queue:
        node_id = queue.popleft()
        if node_id in seen:
            continue
        seen.add(node_id)
        ordered_ids.append(node_id)
        sorted_edges = sorted(
            outgoing.get(node_id, []),
            key=lambda edge: (
                str(edge.get("label") or ""),
                str(edge.get("condition") or ""),
                node_sort_key(str(edge.get("target") or "")),
            ),
        )
        for edge in sorted_edges:
            target = str(edge.get("target") or "")
            if target and target not in seen:
                queue.append(target)

    for node_id in sorted(node_by_id.keys(), key=node_sort_key):
        if node_id not in seen:
            ordered_ids.append(node_id)
            seen.add(node_id)

    id_map = {
        original_id: f"n{index}"
        for index, original_id in enumerate(ordered_ids, start=1)
    }
    canonical_nodes = []
    for original_id in ordered_ids:
        node = node_by_id[original_id]
        canonical_node = {
            "id": id_map[original_id],
            "type": str(node.get("type") or ""),
        }
        if node.get("name"):
            canonical_node["name"] = str(node["name"])
        if node.get("label"):
            canonical_node["label"] = str(node["label"])
        canonical_nodes.append(canonical_node)

    canonical_edges = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if source not in id_map or target not in id_map:
            continue
        canonical_edge = {
            "source": id_map[source],
            "target": id_map[target],
            "type": str(edge.get("type") or "control"),
        }
        if edge.get("label"):
            canonical_edge["label"] = str(edge["label"])
        if edge.get("condition"):
            canonical_edge["condition"] = str(edge["condition"])
        canonical_edges.append(canonical_edge)
    canonical_edges.sort(
        key=lambda edge: (
            edge["source"],
            edge["target"],
            edge["type"],
            edge.get("label", ""),
            edge.get("condition", ""),
        )
    )
    return {
        "nodes": canonical_nodes,
        "edges": canonical_edges,
    }


def _make_sync_error(
    code: str,
    message: str,
    *,
    diagnostics: Dict[str, Any],
    details: Optional[Dict[str, Any]] = None,
) -> HumanEditSynchronizationError:
    error_diagnostics = dict(diagnostics)
    issues = list(error_diagnostics.get("issues") or [])
    issue = {"code": code, "message": message}
    if details:
        issue["details"] = details
    issues.append(issue)
    error_diagnostics["issues"] = issues
    error_diagnostics["summary"] = message
    return HumanEditSynchronizationError(message, diagnostics=error_diagnostics)


def _branch_label(edge: Dict[str, Any], index: int) -> str:
    label = str(edge.get("label") or edge.get("condition") or "").strip()
    if label:
        return label
    return f"branch_{index}"


def _unique_successor_or_none(cursor: _GraphCursor, node_id: str) -> Optional[str]:
    successors = cursor.successors(node_id)
    if not successors:
        return None
    if len(successors) > 1:
        return None
    return successors[0]


def _walk_actions_until_boundary(
    cursor: _GraphCursor,
    start_node_id: Optional[str],
    *,
    stop_node_ids: Set[str],
    diagnostics: Dict[str, Any],
) -> Tuple[List[str], Optional[str]]:
    current = start_node_id
    actions: List[str] = []
    seen: Set[str] = set()
    while current and current not in stop_node_ids:
        if current in seen:
            raise _make_sync_error(
                "cycle_detected",
                "Synchronization encountered a cycle outside a supported control structure.",
                diagnostics=diagnostics,
                details={"node_id": current},
            )
        seen.add(current)
        node_type = cursor.node_type(current)
        if node_type == "final":
            return actions, current
        if node_type in {"merge", "join"}:
            return actions, current
        if node_type in {"decision", "fork"}:
            return actions, current
        if node_type == "object":
            raise _make_sync_error(
                "unsupported_object_node",
                "Human edit synchronization does not support object nodes yet.",
                diagnostics=diagnostics,
                details={"node_id": current},
            )
        if node_type not in {"action", "initial"}:
            raise _make_sync_error(
                "unsupported_node_type",
                "Synchronization encountered a node type that is not supported by the semantic-deterministic artifacts.",
                diagnostics=diagnostics,
                details={"node_id": current, "type": node_type},
            )
        if node_type == "action":
            action_text = cursor.node_text(current)
            if not action_text:
                raise _make_sync_error(
                    "missing_action_text",
                    "Synchronization encountered an action node without text.",
                    diagnostics=diagnostics,
                    details={"node_id": current},
                )
            actions.append(action_text)
        next_node_id = _unique_successor_or_none(cursor, current)
        if next_node_id is None:
            return actions, None
        current = next_node_id
    return actions, current


def _choose_closure_node(
    cursor: _GraphCursor,
    branch_starts: List[str],
    *,
    expected_type: str,
) -> Optional[str]:
    reachable_sets = [cursor.reachable_from(start_id) for start_id in branch_starts]
    if not reachable_sets:
        return None
    common = set.intersection(*reachable_sets)
    candidates = [
        node_id
        for node_id in common
        if cursor.node_type(node_id) == expected_type
    ]
    if not candidates:
        return None
    distance_maps = [cursor.distance(start_id) for start_id in branch_starts]
    return min(
        candidates,
        key=lambda node_id: (
            sum(distance_map.get(node_id, 10**6) for distance_map in distance_maps),
            max(distance_map.get(node_id, 10**6) for distance_map in distance_maps),
            node_id,
        ),
    )


def _parse_structure(
    cursor: _GraphCursor,
    control_node_id: str,
    *,
    parent_id: str,
    parent_branch: Optional[str],
    predecessor_action: Optional[str],
    id_counter: List[int],
    diagnostics: Dict[str, Any],
) -> _StructureResult:
    node_type = cursor.node_type(control_node_id)
    if node_type == "decision":
        closure_type = "merge"
        structure_type = "decision"
    elif node_type == "fork":
        closure_type = "join"
        structure_type = "parallel"
    else:
        raise _make_sync_error(
            "unsupported_control_node",
            "Synchronization encountered a control node that cannot be derived into a canonical topology structure.",
            diagnostics=diagnostics,
            details={"node_id": control_node_id, "type": node_type},
        )

    outgoing = cursor.outgoing(control_node_id)
    if len(outgoing) < 2:
        raise _make_sync_error(
            "underconnected_control_node",
            "Control structures must have at least two outgoing branches.",
            diagnostics=diagnostics,
            details={"node_id": control_node_id, "type": node_type},
        )

    branch_starts = [str(edge.get("target") or "") for edge in outgoing]
    closure_node_id = _choose_closure_node(cursor, branch_starts, expected_type=closure_type)
    if closure_node_id is None:
        if node_type == "decision" and predecessor_action:
            predecessor_reachable = any(
                predecessor_action in cursor.reachable_from(branch_start)
                for branch_start in branch_starts
            )
            if predecessor_reachable:
                raise _make_sync_error(
                    "unsupported_loop_structure",
                    "Human edit synchronization does not yet support deriving loop structures from edited Studio state.",
                    diagnostics=diagnostics,
                    details={"node_id": control_node_id},
                )
        raise _make_sync_error(
            "missing_structure_closure",
            "Synchronization could not identify the required closure node for a control structure.",
            diagnostics=diagnostics,
            details={"node_id": control_node_id, "expected_closure_type": closure_type},
        )

    structure_id = f"T{id_counter[0]}"
    id_counter[0] += 1
    branch_plans: List[Dict[str, Any]] = []
    child_structures: List[Dict[str, Any]] = []
    child_branch_plans: List[Dict[str, Any]] = []
    branch_labels: List[str] = []

    for branch_index, edge in enumerate(outgoing, start=1):
        branch_label = _branch_label(edge, branch_index)
        if branch_label in branch_labels:
            raise _make_sync_error(
                "duplicate_branch_label",
                "Control structure branches must use unique labels.",
                diagnostics=diagnostics,
                details={"node_id": control_node_id, "branch_label": branch_label},
            )
        branch_labels.append(branch_label)
        branch_actions, terminal_node_id = _walk_actions_until_boundary(
            cursor,
            str(edge.get("target") or ""),
            stop_node_ids={closure_node_id},
            diagnostics=diagnostics,
        )
        if terminal_node_id == closure_node_id:
            branch_intent = "continue"
        elif cursor.node_type(terminal_node_id) == "final":
            branch_intent = "terminate"
        else:
            raise _make_sync_error(
                "unsupported_branch_exit",
                "Synchronization could not determine how a branch reconnects to the enclosing flow.",
                diagnostics=diagnostics,
                details={
                    "node_id": control_node_id,
                    "branch_label": branch_label,
                    "terminal_node_id": terminal_node_id,
                },
            )
        branch_plans.append(
            {
                "structure_id": structure_id,
                "branch": branch_label,
                "intent": branch_intent,
                "steps": [{"action": action} for action in branch_actions],
            }
        )

    next_node_id = _unique_successor_or_none(cursor, closure_node_id)
    if next_node_id is None and cursor.outgoing(closure_node_id):
        raise _make_sync_error(
            "ambiguous_structure_exit",
            "Synchronization found a structure closure with multiple outgoing continuations.",
            diagnostics=diagnostics,
            details={"node_id": closure_node_id},
        )

    return _StructureResult(
        topology_structure={
            "id": structure_id,
            "type": structure_type,
            "parent": parent_id,
            "parent_branch": parent_branch,
            "branches": branch_labels,
            "purpose": cursor.node_text(control_node_id) or None,
        },
        branch_plans=branch_plans,
        child_structures=child_structures,
        child_branch_plans=child_branch_plans,
        next_node_id=next_node_id,
    )


def _derive_topology_and_semantics_from_graph(
    clean_graph: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    cursor = _GraphCursor(clean_graph)
    topology_report = analyze_activity_graph(clean_graph)
    semantic_report = analyze_semantic_graph(clean_graph)
    diagnostics: Dict[str, Any] = {
        "issues": [],
        "topology_report": topology_report,
        "semantic_report": semantic_report,
    }

    hard_topology_codes = {
        "missing_initial",
        "multiple_initials",
        "missing_final",
        "disconnected_nodes",
        "dangling_entry_nodes",
        "dead_end_nodes",
        "decision_missing_branch",
        "merge_underconnected",
        "fork_underconnected",
        "join_underconnected",
    }
    blocking_topology_issues = [
        code
        for code in topology_report.get("issues") or []
        if code in hard_topology_codes
    ]
    blocking_semantic_issues = [
        issue
        for issue in semantic_report.get("issues") or []
        if str(issue.get("severity") or "") == "error"
    ]
    if blocking_topology_issues or blocking_semantic_issues:
        raise _make_sync_error(
            "graph_validation_failed",
            "The edited Studio model is not structurally valid enough to synchronize into semantic-deterministic artifacts.",
            diagnostics=diagnostics,
            details={
                "topology_issues": blocking_topology_issues,
                "semantic_issues": blocking_semantic_issues,
            },
        )

    initial_nodes = cursor.initial_nodes()
    if len(initial_nodes) != 1:
        raise _make_sync_error(
            "invalid_initial_count",
            "Synchronization requires exactly one initial node.",
            diagnostics=diagnostics,
            details={"initial_nodes": initial_nodes},
        )
    initial_successors = cursor.successors(initial_nodes[0])
    if len(initial_successors) != 1:
        raise _make_sync_error(
            "invalid_initial_outgoing",
            "Synchronization requires the initial node to have exactly one outgoing control flow edge.",
            diagnostics=diagnostics,
            details={"initial_node_id": initial_nodes[0], "successors": initial_successors},
        )

    id_counter = [1]
    topology_structures: List[Dict[str, Any]] = []
    branch_plans: List[Dict[str, Any]] = []
    root_actions: List[Dict[str, Any]] = []
    current_node_id = initial_successors[0]
    root_slot_id = "ROOT_START"
    predecessor_action_node_id: Optional[str] = None

    while current_node_id and cursor.node_type(current_node_id) != "final":
        root_segment_actions, terminal_node_id = _walk_actions_until_boundary(
            cursor,
            current_node_id,
            stop_node_ids=set(),
            diagnostics=diagnostics,
        )
        if len(root_segment_actions) != 1:
            raise _make_sync_error(
                "unsupported_root_action_segment",
                "Synchronization currently requires each root-scope segment between control structures to contain exactly one business action.",
                diagnostics=diagnostics,
                details={"root_slot_id": root_slot_id, "actions": root_segment_actions},
            )
        root_actions.append({"slot_id": root_slot_id, "action": root_segment_actions[0]})
        predecessor_action_node_id = None
        probe_node_id = current_node_id
        while probe_node_id and probe_node_id != terminal_node_id:
            if cursor.node_type(probe_node_id) == "action":
                predecessor_action_node_id = probe_node_id
            probe_node_id = _unique_successor_or_none(cursor, probe_node_id)

        if terminal_node_id is None or cursor.node_type(terminal_node_id) == "final":
            current_node_id = terminal_node_id
            break

        if cursor.node_type(terminal_node_id) not in {"decision", "fork"}:
            raise _make_sync_error(
                "unexpected_root_boundary",
                "Synchronization encountered an unsupported boundary node while deriving root-scope structure.",
                diagnostics=diagnostics,
                details={"node_id": terminal_node_id, "type": cursor.node_type(terminal_node_id)},
            )

        structure_result = _parse_structure(
            cursor,
            terminal_node_id,
            parent_id="ROOT",
            parent_branch=None,
            predecessor_action=predecessor_action_node_id,
            id_counter=id_counter,
            diagnostics=diagnostics,
        )
        topology_structures.append(structure_result.topology_structure)
        topology_structures.extend(structure_result.child_structures)
        branch_plans.extend(structure_result.branch_plans)
        branch_plans.extend(structure_result.child_branch_plans)
        root_slot_id = f"AFTER_{structure_result.topology_structure['id']}"
        current_node_id = structure_result.next_node_id
        if current_node_id is None:
            raise _make_sync_error(
                "missing_root_continuation",
                "Synchronization requires an explicit root-scope continuation action after a root control structure.",
                diagnostics=diagnostics,
                details={"structure_id": structure_result.topology_structure["id"]},
            )

    topology_artifact = TopologyArtifact.model_validate(
        {"structures": topology_structures}
    ).model_dump(mode="json")
    semantic_plan = SemanticSketchPlan.model_validate(
        {
            "root_actions": root_actions,
            "branch_plans": branch_plans,
        },
        context={"require_explicit_branch_steps": True},
    ).model_dump(mode="json")
    return topology_artifact, semantic_plan, diagnostics


def synchronize_persisted_human_edit(
    exported_current_model: Dict[str, Any] | List[Dict[str, Any]],
    *,
    current_revision: Optional[Any] = None,
) -> Dict[str, Any]:
    clean_graph = _get_clean_model(exported_current_model)
    clean_graph = ActivityModel.model_validate(clean_graph).model_dump(exclude_none=True)
    original_canonical = _canonicalize_graph(clean_graph)

    if current_revision is not None and current_revision.activity_graph:
        try:
            existing_canonical = _canonicalize_graph(current_revision.activity_graph)
        except Exception:  # noqa: BLE001
            existing_canonical = None
        if existing_canonical == original_canonical:
            topology_artifact = current_revision.topology_artifact
            semantic_plan = current_revision.semantic_sketch_plan
            if topology_artifact is None or semantic_plan is None:
                raise HumanEditSynchronizationError(
                    "The current revision does not contain semantic-deterministic artifacts to reuse.",
                    diagnostics={
                        "summary": "current revision artifacts missing",
                        "issues": [{"code": "missing_current_artifacts", "message": "Current revision lacks topology or semantic artifacts."}],
                    },
                )
            return {
                "activity_graph": clean_graph,
                "topology_artifact": topology_artifact,
                "semantic_sketch_plan": semantic_plan,
                "diagnostics": {
                    "summary": "edited Studio model matches the current canonical revision; existing artifacts were reused",
                    "issues": [],
                    "reused_current_revision_artifacts": True,
                },
            }

    topology_artifact, semantic_plan, diagnostics = _derive_topology_and_semantics_from_graph(clean_graph)

    deterministic_sketch = compile_topology_and_semantics_to_activity_sketch(
        topology_artifact,
        semantic_plan,
    )
    repaired_sketch, repair_report = repair_activity_sketch(deterministic_sketch)
    reconstructed_graph = compile_activity_sketch(repaired_sketch)
    reconstructed_canonical = _canonicalize_graph(reconstructed_graph)

    diagnostics["roundtrip_validation"] = {
        "deterministic_sketch": deterministic_sketch,
        "repair_report": repair_report,
        "reconstructed_graph": reconstructed_graph,
    }

    if reconstructed_canonical != original_canonical:
        raise HumanEditSynchronizationError(
            "The edited Studio model cannot be represented exactly by the current semantic-deterministic artifact contract.",
            diagnostics={
                **diagnostics,
                "summary": "round-trip validation failed",
                "issues": [
                    {
                        "code": "roundtrip_mismatch",
                        "message": "The reconstructed ActivityGraph does not match the edited Studio graph.",
                        "details": {
                            "original": original_canonical,
                            "reconstructed": reconstructed_canonical,
                        },
                    }
                ],
            },
        )

    return {
        "activity_graph": clean_graph,
        "topology_artifact": topology_artifact,
        "semantic_sketch_plan": semantic_plan,
        "diagnostics": {
            **diagnostics,
            "summary": "human edit synchronization succeeded",
            "issues": [],
            "reused_current_revision_artifacts": False,
        },
    }


__all__ = [
    "HumanEditSynchronizationError",
    "synchronize_persisted_human_edit",
]
