from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from statistics import fmean
from typing import Any, Iterable, Literal, Mapping

from .action_scoring import ActionCaseScore
from .eval_graph import EvalGraph


StructureType = Literal["exclusive_split", "parallel_region", "loop"]
Side = Literal["reference", "generated"]
_CONTROL_TYPES = frozenset({"decision", "merge", "fork", "join"})
_BOUNDARY_TYPES = frozenset({"initial", "final"})
_SUPPORTED_TYPES = _CONTROL_TYPES | _BOUNDARY_TYPES | {"action"}


KNOWN_UNSUPPORTED_REFERENCE_CASES: Mapping[str, str] = {
    "1-3": "active inclusive gateway semantics are outside EvalGraph",
    "10-2": "active inclusive gateway semantics are outside EvalGraph",
    "10-3": "active inclusive gateway semantics are outside EvalGraph",
    "1-4": "combined converging/diverging gateway requires explicit expansion",
    "8-3": "combined converging/diverging gateway requires explicit expansion",
    "9-2": "combined converging/diverging gateway requires explicit expansion",
    "7-1": "reference uses an incompatible Frapu BPMN XML schema",
}


@dataclass(frozen=True, order=True, slots=True)
class BranchSummary:
    heads: tuple[str, ...]
    tails: tuple[str, ...] = ()


@dataclass(frozen=True, order=True, slots=True)
class ControlStructureSummary:
    """Notation-neutral description of one process control structure."""

    structure_type: StructureType
    entry: str
    branches: tuple[BranchSummary, ...] = ()
    synchronization: str = "not_applicable"
    body_entry: tuple[str, ...] = ()
    back_source: tuple[str, ...] = ()
    repeat_target: tuple[str, ...] = ()
    exit: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class UnscorableStructure:
    structure_type: StructureType
    control_node_ids: tuple[str, ...]
    reason: str
    incident_to_unmatched_actions: bool
    incident_to_unresolved_actions: bool
    incident_to_granularity: bool


@dataclass(frozen=True, slots=True)
class StructureExtraction:
    summaries: tuple[ControlStructureSummary, ...]
    unscorable: tuple[UnscorableStructure, ...]
    structures_incident_to_unmatched_actions: int
    structures_incident_to_unresolved_actions: int
    granularity_incident_structure_count: int
    explicit_exclusive_merge_count: int
    uncontrolled_cycle_count: int

    @property
    def total_count(self) -> int:
        return len(self.summaries) + len(self.unscorable)


@dataclass(frozen=True, slots=True)
class ControlStructureCaseScore:
    case_id: str
    unsupported: bool
    unsupported_reason: str | None
    reference_structure_count: int
    generated_structure_count: int
    scorable_reference_structure_count: int
    scorable_generated_structure_count: int
    unscorable_reference_structure_count: int
    unscorable_generated_structure_count: int
    TP: int
    FP: int
    FN: int
    precision: float | None
    recall: float | None
    f1: float | None
    empty: bool
    structure_coverage: float | None
    reference_summaries: tuple[ControlStructureSummary, ...]
    generated_summaries: tuple[ControlStructureSummary, ...]
    matched_summaries: tuple[ControlStructureSummary, ...]
    unmatched_reference_summaries: tuple[ControlStructureSummary, ...]
    unmatched_generated_summaries: tuple[ControlStructureSummary, ...]
    unscorable_reference_structures: tuple[UnscorableStructure, ...]
    unscorable_generated_structures: tuple[UnscorableStructure, ...]
    structures_incident_to_unmatched_actions: int
    structures_incident_to_unresolved_actions: int
    granularity_incident_structure_count: int
    subtype_diagnostics: Mapping[str, Mapping[str, int]]
    explicit_exclusive_merge_count: int
    uncontrolled_cycle_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ControlStructureDatasetScore:
    case_count: int
    supported_case_count: int
    unsupported_case_count: int
    unsupported_cases: tuple[str, ...]
    empty_structure_case_count: int
    defined_macro_case_count: int
    total_reference_structures: int
    total_generated_structures: int
    total_scorable_reference_structures: int
    total_scorable_generated_structures: int
    total_unscorable_reference_structures: int
    total_unscorable_generated_structures: int
    structure_coverage: float | None
    micro_TP: int
    micro_FP: int
    micro_FN: int
    micro_precision: float | None
    micro_recall: float | None
    micro_f1: float | None
    macro_f1: float | None
    subtype_diagnostics: Mapping[str, Mapping[str, int]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class _AnchorResult:
    anchors: tuple[str, ...]
    visited: frozenset[str]


@dataclass(frozen=True, slots=True)
class _StructureCandidate:
    structure_type: StructureType
    control_node_ids: tuple[str, ...]
    summary: ControlStructureSummary | None
    reason: str
    visited: frozenset[str]
    uncontrolled_cycle: bool = False


class _ExtractionContext:
    def __init__(
        self,
        graph: EvalGraph,
        action_score: ActionCaseScore,
        side: Side,
    ) -> None:
        self.graph = graph
        self.nodes = {node.id: node for node in graph.nodes}
        unsupported = sorted(
            (node.id, str(node.type))
            for node in graph.nodes
            if node.type not in _SUPPORTED_TYPES
        )
        if unsupported:
            raise ValueError(f"Unsupported EvalGraph node types: {unsupported}")

        self.outgoing: dict[str, list[str]] = defaultdict(list)
        self.incoming: dict[str, list[str]] = defaultdict(list)
        for edge in graph.edges:
            self.outgoing[edge.source].append(edge.target)
            self.incoming[edge.target].append(edge.source)
        for adjacency in (self.outgoing, self.incoming):
            for values in adjacency.values():
                values.sort()

        generated_to_reference = {
            generated_id: reference_id
            for reference_id, generated_id in action_score.accepted_pairs
        }
        if side == "reference":
            self.anchor_by_action = {
                node_id: f"ref:{node_id}"
                for node_id in action_score.matched_reference_ids
            }
            self.unmatched = set(action_score.unmatched_reference_ids)
            self.unresolved = set(action_score.unresolved_reference_ids)
            self.granularity = {
                node_id
                for mismatch in action_score.granularity_mismatches
                for node_id in mismatch.reference_ids
            }
        else:
            self.anchor_by_action = {
                generated_id: f"ref:{reference_id}"
                for generated_id, reference_id in generated_to_reference.items()
            }
            self.unmatched = set(action_score.unmatched_generated_ids)
            self.unresolved = set(action_score.unresolved_generated_ids)
            self.granularity = {
                node_id
                for mismatch in action_score.granularity_mismatches
                for node_id in mismatch.generated_ids
            }

    def first_anchors(
        self,
        starts: Iterable[str],
        *,
        reverse: bool = False,
        blocked: frozenset[str] = frozenset(),
        allowed: frozenset[str] | None = None,
    ) -> _AnchorResult:
        adjacency = self.incoming if reverse else self.outgoing
        pending = deque(sorted(set(starts)))
        visited: set[str] = set()
        anchors: set[str] = set()
        while pending:
            node_id = pending.popleft()
            if node_id in visited or node_id in blocked:
                continue
            if allowed is not None and node_id not in allowed:
                continue
            visited.add(node_id)
            node = self.nodes[node_id]
            if node.type == "action" and node_id in self.anchor_by_action:
                anchors.add(self.anchor_by_action[node_id])
                continue
            if node.type == "initial":
                anchors.add("INITIAL")
                continue
            if node.type == "final":
                anchors.add("FINAL")
                continue
            pending.extend(adjacency.get(node_id, ()))
        return _AnchorResult(tuple(sorted(anchors)), frozenset(visited))

    def incident_flags(self, visited: Iterable[str]) -> tuple[bool, bool, bool]:
        node_ids = set(visited)
        return (
            bool(node_ids & self.unmatched),
            bool(node_ids & self.unresolved),
            bool(node_ids & self.granularity),
        )


def _strongly_connected_components(context: _ExtractionContext) -> list[set[str]]:
    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    result: list[set[str]] = []

    def visit(node_id: str) -> None:
        nonlocal index
        indices[node_id] = index
        lowlinks[node_id] = index
        index += 1
        stack.append(node_id)
        on_stack.add(node_id)
        for target in context.outgoing.get(node_id, ()):
            if target not in indices:
                visit(target)
                lowlinks[node_id] = min(lowlinks[node_id], lowlinks[target])
            elif target in on_stack:
                lowlinks[node_id] = min(lowlinks[node_id], indices[target])
        if lowlinks[node_id] != indices[node_id]:
            return
        component: set[str] = set()
        while True:
            member = stack.pop()
            on_stack.remove(member)
            component.add(member)
            if member == node_id:
                break
        result.append(component)

    for node_id in sorted(context.nodes):
        if node_id not in indices:
            visit(node_id)
    return result


def _extract_loops(
    context: _ExtractionContext,
) -> tuple[list[_StructureCandidate], set[str], set[str]]:
    candidates: list[_StructureCandidate] = []
    controller_ids: set[str] = set()
    cyclic_nodes: set[str] = set()
    for component in _strongly_connected_components(context):
        cyclic = len(component) > 1 or any(
            node_id in context.outgoing.get(node_id, ()) for node_id in component
        )
        if not cyclic:
            continue
        cyclic_nodes.update(component)
        controllers = []
        for node_id in sorted(component):
            if context.nodes[node_id].type != "decision":
                continue
            inside = [
                target
                for target in context.outgoing.get(node_id, ())
                if target in component
            ]
            outside = [
                target
                for target in context.outgoing.get(node_id, ())
                if target not in component
            ]
            if inside and outside:
                controllers.append((node_id, inside, outside))

        if len(controllers) != 1:
            candidates.append(
                _StructureCandidate(
                    structure_type="loop",
                    control_node_ids=tuple(sorted(component & set(context.nodes))),
                    summary=None,
                    reason=(
                        "uncontrolled_cycle"
                        if not controllers
                        else "multiple_plausible_loop_controllers"
                    ),
                    visited=frozenset(component),
                    uncontrolled_cycle=not controllers,
                )
            )
            continue

        controller, continuation_starts, exit_starts = controllers[0]
        controller_ids.add(controller)
        blocked = frozenset({controller})
        allowed = frozenset(component)
        external_predecessors = [
            source
            for member in component
            for source in context.incoming.get(member, ())
            if source not in component
        ]
        entry = context.first_anchors(external_predecessors, reverse=True)
        if not external_predecessors:
            entry = _AnchorResult((), frozenset(component))

        component_entries = [
            member
            for member in component
            if any(
                source not in component
                for source in context.incoming.get(member, ())
            )
        ]
        body_starts = [
            target
            for member in component_entries
            for target in (
                continuation_starts
                if member == controller
                else (member,)
            )
        ]
        body = context.first_anchors(
            body_starts, blocked=blocked, allowed=allowed
        )
        repeat = context.first_anchors(
            continuation_starts, blocked=blocked, allowed=allowed
        )
        back = context.first_anchors(
            [
                source
                for source in context.incoming.get(controller, ())
                if source in component
            ],
            reverse=True,
            blocked=blocked,
            allowed=allowed,
        )
        exit_result = context.first_anchors(exit_starts, blocked=blocked)
        visited = frozenset(
            set(component)
            | set(entry.visited)
            | set(body.visited)
            | set(repeat.visited)
            | set(back.visited)
            | set(exit_result.visited)
        )
        required = {
            "entry": entry.anchors,
            "body_entry": body.anchors,
            "back_source": back.anchors,
            "repeat_target": repeat.anchors,
            "exit": exit_result.anchors,
        }
        invalid = [name for name, anchors in required.items() if not anchors]
        if len(entry.anchors) != 1:
            invalid.append("entry_not_unique")
        if invalid:
            candidates.append(
                _StructureCandidate(
                    "loop",
                    (controller,),
                    None,
                    "missing_or_ambiguous_loop_anchors:" + ",".join(sorted(set(invalid))),
                    visited,
                )
            )
            continue
        candidates.append(
            _StructureCandidate(
                "loop",
                (controller,),
                ControlStructureSummary(
                    structure_type="loop",
                    entry=entry.anchors[0],
                    body_entry=body.anchors,
                    back_source=back.anchors,
                    repeat_target=repeat.anchors,
                    exit=exit_result.anchors,
                ),
                "",
                visited,
            )
        )
    return candidates, controller_ids, cyclic_nodes


def _extract_exclusive_splits(
    context: _ExtractionContext,
    cyclic_nodes: set[str],
) -> list[_StructureCandidate]:
    candidates: list[_StructureCandidate] = []
    for node in sorted(context.graph.nodes, key=lambda item: item.id):
        if node.type != "decision" or node.id in cyclic_nodes:
            continue
        successors = context.outgoing.get(node.id, ())
        if len(successors) < 2:
            continue
        entry = context.first_anchors(
            context.incoming.get(node.id, ()),
            reverse=True,
            blocked=frozenset({node.id}),
        )
        branch_results = [
            context.first_anchors((successor,), blocked=frozenset({node.id}))
            for successor in successors
        ]
        visited = frozenset(
            set(entry.visited)
            | {node.id}
            | {
                member
                for result in branch_results
                for member in result.visited
            }
        )
        missing = [index for index, result in enumerate(branch_results) if not result.anchors]
        if len(entry.anchors) != 1 or missing:
            reason = (
                "exclusive_entry_not_unique"
                if len(entry.anchors) != 1
                else "exclusive_branch_without_anchor:" + ",".join(map(str, missing))
            )
            candidates.append(
                _StructureCandidate("exclusive_split", (node.id,), None, reason, visited)
            )
            continue
        branches = tuple(
            sorted(BranchSummary(result.anchors) for result in branch_results)
        )
        candidates.append(
            _StructureCandidate(
                "exclusive_split",
                (node.id,),
                ControlStructureSummary(
                    structure_type="exclusive_split",
                    entry=entry.anchors[0],
                    branches=branches,
                ),
                "",
                visited,
            )
        )
    return candidates


def _join_distances(
    context: _ExtractionContext, start: str, blocked_fork: str
) -> dict[str, int]:
    queue = deque([(start, 0)])
    distances: dict[str, int] = {}
    visited: set[str] = set()
    while queue:
        node_id, distance = queue.popleft()
        if node_id in visited or node_id == blocked_fork:
            continue
        visited.add(node_id)
        node = context.nodes[node_id]
        if node.type == "final":
            continue
        if node.type == "join":
            distances.setdefault(node_id, distance)
        queue.extend((target, distance + 1) for target in context.outgoing.get(node_id, ()))
    return distances


def _nodes_before_join(
    context: _ExtractionContext, start: str, join_id: str, fork_id: str
) -> frozenset[str]:
    pending = deque([start])
    visited: set[str] = set()
    while pending:
        node_id = pending.popleft()
        if node_id in visited or node_id in {join_id, fork_id}:
            continue
        visited.add(node_id)
        if context.nodes[node_id].type == "final":
            continue
        pending.extend(context.outgoing.get(node_id, ()))
    return frozenset(visited)


def _extract_parallel_regions(
    context: _ExtractionContext,
) -> list[_StructureCandidate]:
    forks = [node.id for node in context.graph.nodes if node.type == "fork"]
    joins = {node.id for node in context.graph.nodes if node.type == "join"}
    proposals: dict[str, str | None] = {}
    ambiguous_forks: set[str] = set()
    for fork_id in sorted(forks):
        successors = context.outgoing.get(fork_id, ())
        if len(successors) < 2:
            proposals[fork_id] = None
            continue
        per_branch = [
            _join_distances(context, successor, fork_id) for successor in successors
        ]
        common = set.intersection(*(set(item) for item in per_branch)) if per_branch else set()
        if not common:
            proposals[fork_id] = None
            continue
        ranked = sorted(
            (
                max(item[join_id] for item in per_branch),
                sum(item[join_id] for item in per_branch),
                join_id,
            )
            for join_id in common
        )
        if len(ranked) > 1 and ranked[0][:2] == ranked[1][:2]:
            ambiguous_forks.add(fork_id)
            proposals[fork_id] = None
        else:
            proposals[fork_id] = ranked[0][2]

    proposed_join_counts = Counter(
        join_id for join_id in proposals.values() if join_id is not None
    )
    shared_joins = {
        join_id for join_id, count in proposed_join_counts.items() if count > 1
    }
    paired_joins: set[str] = set()
    considered_joins = set(proposed_join_counts)
    candidates: list[_StructureCandidate] = []
    for fork_id in sorted(forks):
        successors = context.outgoing.get(fork_id, ())
        join_id = proposals[fork_id]
        entry = context.first_anchors(
            context.incoming.get(fork_id, ()),
            reverse=True,
            blocked=frozenset({fork_id}),
        )
        visited: set[str] = {fork_id} | set(entry.visited)
        if fork_id in ambiguous_forks or join_id in shared_joins:
            candidates.append(
                _StructureCandidate(
                    "parallel_region",
                    tuple(sorted({fork_id} | ({join_id} if join_id else set()))),
                    None,
                    "ambiguous_fork_join_pairing",
                    frozenset(visited),
                )
            )
            continue
        if len(successors) < 2 or len(entry.anchors) != 1:
            candidates.append(
                _StructureCandidate(
                    "parallel_region", (fork_id,), None,
                    "parallel_entry_or_cardinality_invalid", frozenset(visited)
                )
            )
            continue

        branches: list[BranchSummary] = []
        missing_anchor = False
        for successor in successors:
            if join_id is None:
                head = context.first_anchors(
                    (successor,), blocked=frozenset({fork_id})
                )
                visited.update(head.visited)
                if not head.anchors:
                    missing_anchor = True
                branches.append(BranchSummary(head.anchors))
                continue

            branch_nodes = _nodes_before_join(context, successor, join_id, fork_id)
            head = context.first_anchors(
                (successor,),
                blocked=frozenset({fork_id, join_id}),
                allowed=branch_nodes,
            )
            incoming_to_join = [
                source
                for source in context.incoming.get(join_id, ())
                if source in branch_nodes
            ]
            tail = context.first_anchors(
                incoming_to_join,
                reverse=True,
                blocked=frozenset({fork_id, join_id}),
                allowed=branch_nodes,
            )
            visited.update(branch_nodes)
            visited.update(head.visited)
            visited.update(tail.visited)
            if not head.anchors or not tail.anchors:
                missing_anchor = True
            branches.append(BranchSummary(head.anchors, tail.anchors))

        if missing_anchor:
            candidates.append(
                _StructureCandidate(
                    "parallel_region",
                    tuple(sorted({fork_id} | ({join_id} if join_id else set()))),
                    None,
                    "parallel_branch_without_anchor",
                    frozenset(visited),
                )
            )
            continue
        if join_id is not None:
            paired_joins.add(join_id)
            visited.add(join_id)
        candidates.append(
            _StructureCandidate(
                "parallel_region",
                tuple(sorted({fork_id} | ({join_id} if join_id else set()))),
                ControlStructureSummary(
                    structure_type="parallel_region",
                    entry=entry.anchors[0],
                    branches=tuple(sorted(branches)),
                    synchronization="paired" if join_id else "none",
                ),
                "",
                frozenset(visited),
            )
        )

    for join_id in sorted(joins - paired_joins - considered_joins):
        branch_results = [
            context.first_anchors(
                (source,), reverse=True, blocked=frozenset({join_id})
            )
            for source in context.incoming.get(join_id, ())
        ]
        visited = frozenset(
            {join_id}
            | {member for result in branch_results for member in result.visited}
        )
        if len(branch_results) < 2 or any(not result.anchors for result in branch_results):
            candidates.append(
                _StructureCandidate(
                    "parallel_region", (join_id,), None,
                    "orphan_join_without_branch_anchors", visited
                )
            )
            continue
        candidates.append(
            _StructureCandidate(
                "parallel_region",
                (join_id,),
                ControlStructureSummary(
                    structure_type="parallel_region",
                    entry="ORPHAN",
                    branches=tuple(
                        sorted(BranchSummary((), result.anchors) for result in branch_results)
                    ),
                    synchronization="orphan",
                ),
                "",
                visited,
            )
        )
    return candidates


def extract_control_structure_summaries(
    graph: EvalGraph,
    action_score: ActionCaseScore,
    *,
    side: Side,
) -> StructureExtraction:
    context = _ExtractionContext(graph, action_score, side)
    loop_candidates, _, cyclic_nodes = _extract_loops(context)
    candidates = (
        loop_candidates
        + _extract_exclusive_splits(context, cyclic_nodes)
        + _extract_parallel_regions(context)
    )
    summaries: list[ControlStructureSummary] = []
    unscorable: list[UnscorableStructure] = []
    unmatched_count = 0
    unresolved_count = 0
    granularity_count = 0
    uncontrolled_count = 0
    for candidate in candidates:
        incident_unmatched, incident_unresolved, incident_granularity = (
            context.incident_flags(candidate.visited)
        )
        unmatched_count += incident_unmatched
        unresolved_count += incident_unresolved
        granularity_count += incident_granularity
        uncontrolled_count += candidate.uncontrolled_cycle
        if candidate.summary is not None:
            summaries.append(candidate.summary)
        else:
            unscorable.append(
                UnscorableStructure(
                    structure_type=candidate.structure_type,
                    control_node_ids=candidate.control_node_ids,
                    reason=candidate.reason,
                    incident_to_unmatched_actions=incident_unmatched,
                    incident_to_unresolved_actions=incident_unresolved,
                    incident_to_granularity=incident_granularity,
                )
            )
    return StructureExtraction(
        summaries=tuple(sorted(summaries)),
        unscorable=tuple(unscorable),
        structures_incident_to_unmatched_actions=unmatched_count,
        structures_incident_to_unresolved_actions=unresolved_count,
        granularity_incident_structure_count=granularity_count,
        explicit_exclusive_merge_count=sum(
            node.type == "merge" for node in graph.nodes
        ),
        uncontrolled_cycle_count=uncontrolled_count,
    )


def _multiset_difference(
    left: Counter[ControlStructureSummary],
    right: Counter[ControlStructureSummary],
) -> tuple[ControlStructureSummary, ...]:
    result: list[ControlStructureSummary] = []
    for summary in sorted(left):
        result.extend([summary] * max(left[summary] - right[summary], 0))
    return tuple(result)


def _subtype_diagnostics(
    reference: Counter[ControlStructureSummary],
    generated: Counter[ControlStructureSummary],
) -> dict[str, dict[str, int]]:
    diagnostics: dict[str, dict[str, int]] = {}
    for structure_type in ("exclusive_split", "parallel_region", "loop"):
        reference_sub = Counter(
            {item: count for item, count in reference.items() if item.structure_type == structure_type}
        )
        generated_sub = Counter(
            {item: count for item, count in generated.items() if item.structure_type == structure_type}
        )
        TP = sum((reference_sub & generated_sub).values())
        diagnostics[structure_type] = {
            "reference": sum(reference_sub.values()),
            "generated": sum(generated_sub.values()),
            "TP": TP,
            "FP": sum(generated_sub.values()) - TP,
            "FN": sum(reference_sub.values()) - TP,
        }
    return diagnostics


def _metrics(
    TP: int, FP: int, FN: int, *, empty: bool
) -> tuple[float | None, float | None, float | None]:
    if empty:
        return None, None, None
    precision = TP / (TP + FP) if TP + FP else 0.0
    recall = TP / (TP + FN) if TP + FN else 0.0
    denominator = 2 * TP + FP + FN
    return precision, recall, 2 * TP / denominator if denominator else 0.0


def unsupported_control_structure_case(
    case_id: str, reason: str
) -> ControlStructureCaseScore:
    return ControlStructureCaseScore(
        case_id=case_id,
        unsupported=True,
        unsupported_reason=reason,
        reference_structure_count=0,
        generated_structure_count=0,
        scorable_reference_structure_count=0,
        scorable_generated_structure_count=0,
        unscorable_reference_structure_count=0,
        unscorable_generated_structure_count=0,
        TP=0,
        FP=0,
        FN=0,
        precision=None,
        recall=None,
        f1=None,
        empty=True,
        structure_coverage=None,
        reference_summaries=(),
        generated_summaries=(),
        matched_summaries=(),
        unmatched_reference_summaries=(),
        unmatched_generated_summaries=(),
        unscorable_reference_structures=(),
        unscorable_generated_structures=(),
        structures_incident_to_unmatched_actions=0,
        structures_incident_to_unresolved_actions=0,
        granularity_incident_structure_count=0,
        subtype_diagnostics={},
        explicit_exclusive_merge_count=0,
        uncontrolled_cycle_count=0,
    )


def score_control_structure_case(
    case_id: str,
    reference_graph: EvalGraph,
    generated_graph: EvalGraph,
    action_score: ActionCaseScore,
) -> ControlStructureCaseScore:
    if case_id in KNOWN_UNSUPPORTED_REFERENCE_CASES:
        return unsupported_control_structure_case(
            case_id, KNOWN_UNSUPPORTED_REFERENCE_CASES[case_id]
        )
    if action_score.case_id != case_id:
        raise ValueError("Action score case id does not match Control-structure case")
    reference = extract_control_structure_summaries(
        reference_graph, action_score, side="reference"
    )
    generated = extract_control_structure_summaries(
        generated_graph, action_score, side="generated"
    )
    reference_counter = Counter(reference.summaries)
    generated_counter = Counter(generated.summaries)
    matched_counter = reference_counter & generated_counter
    matched = tuple(
        summary
        for summary in sorted(matched_counter)
        for _ in range(matched_counter[summary])
    )
    unmatched_reference = _multiset_difference(reference_counter, generated_counter)
    unmatched_generated = _multiset_difference(generated_counter, reference_counter)
    TP = len(matched)
    FP = len(unmatched_generated)
    FN = len(unmatched_reference)
    if TP + FN != len(reference.summaries) or TP + FP != len(generated.summaries):
        raise AssertionError(f"Case {case_id} violates Control-structure accounting")
    total = reference.total_count + generated.total_count
    scorable = len(reference.summaries) + len(generated.summaries)
    coverage = scorable / total if total else 1.0
    empty = not reference.summaries and not generated.summaries
    precision, recall, f1 = _metrics(TP, FP, FN, empty=empty)
    subtype = _subtype_diagnostics(reference_counter, generated_counter)
    return ControlStructureCaseScore(
        case_id=case_id,
        unsupported=False,
        unsupported_reason=None,
        reference_structure_count=reference.total_count,
        generated_structure_count=generated.total_count,
        scorable_reference_structure_count=len(reference.summaries),
        scorable_generated_structure_count=len(generated.summaries),
        unscorable_reference_structure_count=len(reference.unscorable),
        unscorable_generated_structure_count=len(generated.unscorable),
        TP=TP,
        FP=FP,
        FN=FN,
        precision=precision,
        recall=recall,
        f1=f1,
        empty=empty,
        structure_coverage=coverage,
        reference_summaries=reference.summaries,
        generated_summaries=generated.summaries,
        matched_summaries=matched,
        unmatched_reference_summaries=unmatched_reference,
        unmatched_generated_summaries=unmatched_generated,
        unscorable_reference_structures=reference.unscorable,
        unscorable_generated_structures=generated.unscorable,
        structures_incident_to_unmatched_actions=(
            reference.structures_incident_to_unmatched_actions
            + generated.structures_incident_to_unmatched_actions
        ),
        structures_incident_to_unresolved_actions=(
            reference.structures_incident_to_unresolved_actions
            + generated.structures_incident_to_unresolved_actions
        ),
        granularity_incident_structure_count=(
            reference.granularity_incident_structure_count
            + generated.granularity_incident_structure_count
        ),
        subtype_diagnostics=subtype,
        explicit_exclusive_merge_count=(
            reference.explicit_exclusive_merge_count
            + generated.explicit_exclusive_merge_count
        ),
        uncontrolled_cycle_count=(
            reference.uncontrolled_cycle_count + generated.uncontrolled_cycle_count
        ),
    )


def aggregate_control_structure_scores(
    case_scores: Iterable[ControlStructureCaseScore],
) -> ControlStructureDatasetScore:
    scores = tuple(case_scores)
    supported = tuple(score for score in scores if not score.unsupported)
    micro_TP = sum(score.TP for score in supported)
    micro_FP = sum(score.FP for score in supported)
    micro_FN = sum(score.FN for score in supported)
    empty = not any(
        score.scorable_reference_structure_count
        or score.scorable_generated_structure_count
        for score in supported
    )
    micro_precision, micro_recall, micro_f1 = _metrics(
        micro_TP, micro_FP, micro_FN, empty=empty
    )
    defined_f1 = [score.f1 for score in supported if score.f1 is not None]
    total = sum(
        score.reference_structure_count + score.generated_structure_count
        for score in supported
    )
    scorable = sum(
        score.scorable_reference_structure_count
        + score.scorable_generated_structure_count
        for score in supported
    )
    subtype: dict[str, dict[str, int]] = {}
    for structure_type in ("exclusive_split", "parallel_region", "loop"):
        subtype[structure_type] = {
            key: sum(
                score.subtype_diagnostics.get(structure_type, {}).get(key, 0)
                for score in supported
            )
            for key in ("reference", "generated", "TP", "FP", "FN")
        }
    return ControlStructureDatasetScore(
        case_count=len(scores),
        supported_case_count=len(supported),
        unsupported_case_count=len(scores) - len(supported),
        unsupported_cases=tuple(
            sorted(score.case_id for score in scores if score.unsupported)
        ),
        empty_structure_case_count=sum(score.empty for score in supported),
        defined_macro_case_count=len(defined_f1),
        total_reference_structures=sum(
            score.reference_structure_count for score in supported
        ),
        total_generated_structures=sum(
            score.generated_structure_count for score in supported
        ),
        total_scorable_reference_structures=sum(
            score.scorable_reference_structure_count for score in supported
        ),
        total_scorable_generated_structures=sum(
            score.scorable_generated_structure_count for score in supported
        ),
        total_unscorable_reference_structures=sum(
            score.unscorable_reference_structure_count for score in supported
        ),
        total_unscorable_generated_structures=sum(
            score.unscorable_generated_structure_count for score in supported
        ),
        structure_coverage=scorable / total if total else 1.0,
        micro_TP=micro_TP,
        micro_FP=micro_FP,
        micro_FN=micro_FN,
        micro_precision=micro_precision,
        micro_recall=micro_recall,
        micro_f1=micro_f1,
        macro_f1=fmean(defined_f1) if defined_f1 else None,
        subtype_diagnostics=subtype,
    )
