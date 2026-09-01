from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, replace
from typing import Any, Literal, Mapping, Sequence

from .action import ActionResult, _maximum_assignment
from .core import AutomaticItem, EvalGraph, evaluation_item_id, reachable, strongly_connected_components


RegionMode = Literal["exclusive", "parallel", "loop"]


@dataclass(frozen=True, slots=True)
class SoftCounts:
    tp: float = 0.0
    fp: float = 0.0
    fn: float = 0.0

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def f1(self) -> float:
        denominator = 2 * self.tp + self.fp + self.fn
        return 2 * self.tp / denominator if denominator else 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "tp": self.tp, "fp": self.fp, "fn": self.fn,
            "precision": self.precision, "recall": self.recall, "f1": self.f1,
        }


@dataclass(frozen=True, slots=True)
class RegionBranch:
    branch_id: str
    raw_action_footprint: frozenset[str]
    action_footprint: frozenset[str]
    guard: str | None


@dataclass(frozen=True, slots=True)
class StructureRegion:
    region_id: str
    mode: RegionMode
    parent_region_id: str | None
    parent_branch_id: str | None
    depth: int
    entry_anchor: str | None
    continuation_anchor: str | None
    raw_action_footprint: frozenset[str]
    action_footprint: frozenset[str]
    branches: tuple[RegionBranch, ...]
    closure: str | None
    loop_body: frozenset[str]
    loop_exit: frozenset[str]
    anchor_quality: str
    entry_boundary_comparable: bool | None
    continuation_boundary_comparable: bool | None


@dataclass(frozen=True, slots=True)
class RegionScore:
    reference_region_id: str | None
    generated_region_id: str | None
    reference_mode: str | None
    generated_mode: str | None
    component_scores: Mapping[str, float | None]
    similarity: float | None
    tp: float
    fp: float
    fn: float
    alignment_rationale: Mapping[str, Any]
    branch_matching: tuple[Mapping[str, Any], ...]
    review_triggers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StructureResult:
    case_id: str
    candidate_id: str
    reference_regions: tuple[StructureRegion, ...]
    generated_regions: tuple[StructureRegion, ...]
    region_scores: tuple[RegionScore, ...]
    counts: SoftCounts
    component_coverage: float | None
    region_coverage: float | None
    action_anchor_coverage: float
    anchor_limited_count: int
    anchor_limited_rate: float
    unscorable: tuple[str, ...]
    items: tuple[AutomaticItem, ...]

    @property
    def metric_defined(self) -> bool:
        return not self.unscorable and bool(self.reference_regions or self.generated_regions)


def _distance(graph: EvalGraph, source: str, target: str) -> int | None:
    queue = deque([(source, 0)])
    seen = {source}
    while queue:
        node, distance = queue.popleft()
        if node == target:
            return distance
        for following in graph.outgoing[node]:
            if following not in seen:
                seen.add(following)
                queue.append((following, distance + 1))
    return None


def _shortest_path(graph: EvalGraph, source: str, target: str) -> tuple[str, ...] | None:
    queue = deque([(source, (source,))])
    seen = {source}
    while queue:
        node, path = queue.popleft()
        if node == target:
            return path
        for following in graph.outgoing[node]:
            if following not in seen:
                seen.add(following)
                queue.append((following, (*path, following)))
    return None


def _control_neutral_corridor(graph: EvalGraph, source: str | None, target: str | None) -> bool:
    if source is None or target is None:
        return False
    path = _shortest_path(graph, source, target)
    if path is None:
        return False
    for node_id in path[1:-1]:
        node = graph.by_id[node_id]
        if node.type in {"decision", "fork", "unsupported_control"}:
            return False
        if node.type in {"merge", "join"} and (
            len(graph.incoming[node_id]) > 1 or len(graph.outgoing[node_id]) > 1
        ):
            return False
    return True


def _nearest_common(graph: EvalGraph, starts: Sequence[str]) -> str | None:
    if len(starts) < 2:
        return None
    reachable_sets = [{start, *reachable(graph, start)} for start in starts]
    common = set.intersection(*reachable_sets)
    if not common:
        return None
    return min(
        common,
        key=lambda node: (
            max(_distance(graph, start, node) or 0 for start in starts),
            sum(_distance(graph, start, node) or 0 for start in starts),
            node,
        ),
    )


def _until(graph: EvalGraph, start: str, stop: str | None) -> set[str]:
    seen: set[str] = set()
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node == stop or node in seen:
            continue
        seen.add(node)
        queue.extend(graph.outgoing[node])
    return seen


def _nearest_action_before(graph: EvalGraph, node_id: str) -> str | None:
    reverse = graph.incoming
    queue = deque(reverse[node_id])
    seen: set[str] = set()
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        if graph.by_id[node].type == "action":
            return node
        queue.extend(reverse[node])
    return None


def _nearest_action_after(graph: EvalGraph, node_id: str | None) -> str | None:
    if node_id is None:
        return None
    queue = deque([node_id])
    seen: set[str] = set()
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        if graph.by_id[node].type == "action":
            return node
        queue.extend(graph.outgoing[node])
    return None


def _map_set(values: set[str], anchors: Mapping[str, str]) -> frozenset[str]:
    return frozenset(anchors[value] for value in values if value in anchors)


def extract_regions(graph: EvalGraph, anchors: Mapping[str, str]) -> tuple[StructureRegion, ...]:
    action_ids = {node.id for node in graph.nodes if node.type == "action"}
    cyclic_components = [
        component for component in strongly_connected_components(graph)
        if len(component) > 1 or any(edge.source == edge.target and edge.source in component for edge in graph.edges)
    ]
    cyclic_nodes = set().union(*cyclic_components) if cyclic_components else set()
    regions: list[StructureRegion] = []

    for control in sorted(graph.nodes, key=lambda node: node.id):
        if control.type not in {"decision", "fork"} or control.id in cyclic_nodes:
            continue
        starts = graph.outgoing[control.id]
        if len(starts) < 2:
            continue
        continuation = _nearest_common(graph, starts)
        branches: list[RegionBranch] = []
        footprint: set[str] = set()
        for start in starts:
            branch_nodes = _until(graph, start, continuation)
            raw = branch_nodes & action_ids
            footprint.update(raw)
            edge = next((edge for edge in graph.edges if edge.source == control.id and edge.target == start), None)
            branches.append(RegionBranch(start, frozenset(raw), _map_set(raw, anchors), edge.label if edge else None))
        mode: RegionMode = "exclusive" if control.type == "decision" else "parallel"
        continuation_type = graph.by_id[continuation].type if continuation else None
        if mode == "parallel":
            closure = (
                "synchronized"
                if continuation is not None
                and (continuation_type == "join" or len(graph.incoming[continuation]) > 1)
                else "unsynchronized"
            )
        else:
            closure = "closed" if continuation is not None else "open"
        entry = _nearest_action_before(graph, control.id)
        after = _nearest_action_after(graph, continuation)
        mapped = _map_set(footprint, anchors)
        entry_comparable = (
            _control_neutral_corridor(graph, entry, control.id) if entry is not None else None
        )
        continuation_comparable = (
            _control_neutral_corridor(graph, continuation, after)
            if continuation is not None and after is not None else None
        )
        regions.append(StructureRegion(
            control.id, mode, None, None, 0,
            anchors.get(entry) if entry else None,
            anchors.get(after) if after else None,
            frozenset(footprint), mapped, tuple(branches),
            closure, frozenset(), frozenset(),
            "complete" if len(mapped) == len(footprint) else "anchor_limited",
            entry_comparable, continuation_comparable,
        ))

    for index, component in enumerate(sorted(cyclic_components, key=lambda value: sorted(value))):
        raw_body = set(component) & action_ids
        if not raw_body:
            continue
        incoming = {
            edge.source for edge in graph.edges
            if edge.target in component and edge.source not in component
        }
        outgoing = {
            edge.target for edge in graph.edges
            if edge.source in component and edge.target not in component
        }
        exit_boundaries = sorted(
            (target, action) for target in outgoing
            for action in [_nearest_action_after(graph, target)]
            if action is not None
        )
        raw_exit = {action for _, action in exit_boundaries}
        controls = sorted(node for node in component if graph.by_id[node].type in {"decision", "fork"})
        entry_raw = next((
            action for source in sorted(incoming)
            for action in [_nearest_action_after(graph, source)]
            if action in raw_body
        ), None)
        if entry_raw is None:
            entry_raw = _nearest_action_before(graph, controls[0]) if controls else None
        region_id = "loop:" + ",".join(sorted(component))
        mapped_body = _map_set(raw_body, anchors)
        continuation_raw = next(iter(raw_exit)) if len(raw_exit) == 1 else None
        entry_comparable = (
            _control_neutral_corridor(
                graph, entry_raw, controls[0] if controls else next(iter(sorted(component)), None)
            )
            if entry_raw is not None else None
        )
        continuation_comparable = (
            all(_control_neutral_corridor(graph, target, action)
                for target, action in exit_boundaries if action == continuation_raw)
            if continuation_raw is not None else None
        )
        regions.append(StructureRegion(
            region_id, "loop", None, None, 0,
            anchors.get(entry_raw) if entry_raw else None,
            anchors.get(continuation_raw) if continuation_raw else None,
            frozenset(raw_body), mapped_body, (),
            None, mapped_body, _map_set(raw_exit, anchors),
            "complete" if len(mapped_body) == len(raw_body) else "anchor_limited",
            entry_comparable, continuation_comparable,
        ))

    # Infer hierarchy from strict raw footprint containment. The smallest
    # containing region is the parent; branch ownership follows containment.
    enriched: list[StructureRegion] = []
    for region in regions:
        parents = [
            candidate for candidate in regions
            if region.region_id != candidate.region_id
            and region.raw_action_footprint
            and (
                region.raw_action_footprint < candidate.raw_action_footprint
                or (
                    region.raw_action_footprint == candidate.raw_action_footprint
                    and region.region_id in graph.by_id
                    and candidate.region_id in graph.by_id
                    and region.region_id in reachable(graph, candidate.region_id)
                    and candidate.region_id not in reachable(graph, region.region_id)
                )
            )
        ]
        parent = min(parents, key=lambda item: (len(item.raw_action_footprint), item.region_id), default=None)
        branch_id = None
        if parent:
            branch = next((
                branch for branch in parent.branches
                if region.raw_action_footprint <= branch.raw_action_footprint
            ), None)
            branch_id = branch.branch_id if branch else None
        enriched.append(replace(region, parent_region_id=parent.region_id if parent else None,
                                parent_branch_id=branch_id))
    by_id = {region.region_id: region for region in enriched}
    result: list[StructureRegion] = []
    for region in enriched:
        depth, parent_id = 0, region.parent_region_id
        seen: set[str] = set()
        while parent_id and parent_id not in seen:
            seen.add(parent_id)
            depth += 1
            parent_id = by_id[parent_id].parent_region_id
        result.append(replace(region, depth=depth))
    return tuple(sorted(result, key=lambda item: (item.depth, item.region_id)))


def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    if not left and not right:
        return 1.0
    return len(left & right) / len(left | right) if left | right else 0.0


def _branch_score(
    reference: tuple[RegionBranch, ...], generated: tuple[RegionBranch, ...]
) -> tuple[float | None, tuple[Mapping[str, Any], ...]]:
    if not reference and not generated:
        return None, ()
    if not reference or not generated:
        return 0.0, ()
    weights = [[_jaccard(left.action_footprint, right.action_footprint) for right in generated]
               for left in reference]
    pairs = _maximum_assignment(weights)
    details = tuple({
        "reference_branch": reference[i].branch_id,
        "generated_branch": generated[j].branch_id,
        "jaccard": weights[i][j],
    } for i, j in pairs)
    return sum(weights[i][j] for i, j in pairs) / max(len(reference), len(generated)), details


def _alignment_score(reference: StructureRegion, generated: StructureRegion) -> tuple[int, float, int]:
    boundary = int(
        reference.entry_boundary_comparable is True
        and generated.entry_boundary_comparable is True
        and
        reference.entry_anchor is not None
        and reference.entry_anchor == generated.entry_anchor
    ) + int(
        reference.continuation_boundary_comparable is True
        and generated.continuation_boundary_comparable is True
        and
        reference.continuation_anchor is not None
        and reference.continuation_anchor == generated.continuation_anchor
    )
    return boundary, _jaccard(reference.action_footprint, generated.action_footprint), int(reference.depth == generated.depth)


def _align_regions(
    reference: tuple[StructureRegion, ...], generated: tuple[StructureRegion, ...]
) -> tuple[list[tuple[StructureRegion, StructureRegion, tuple[int, float, int, bool]]],
           list[StructureRegion], list[StructureRegion]]:
    matched: list[tuple[StructureRegion, StructureRegion, tuple[int, float, int, bool]]] = []
    used_generated: set[str] = set()
    parent_map: dict[str, str] = {}
    reference_by_id = {region.region_id: region for region in reference}
    generated_by_id = {region.region_id: region for region in generated}

    def branch_scope_compatible(ref: StructureRegion, gen: StructureRegion) -> bool:
        if ref.parent_region_id is None or gen.parent_region_id is None:
            return ref.parent_region_id is None and gen.parent_region_id is None
        ref_parent = reference_by_id[ref.parent_region_id]
        gen_parent = generated_by_id[gen.parent_region_id]
        ref_branch = next((branch for branch in ref_parent.branches
                           if branch.branch_id == ref.parent_branch_id), None)
        gen_branch = next((branch for branch in gen_parent.branches
                           if branch.branch_id == gen.parent_branch_id), None)
        if ref_branch is None or gen_branch is None:
            return ref.parent_branch_id is None and gen.parent_branch_id is None
        return _jaccard(ref_branch.action_footprint, gen_branch.action_footprint) > 0.0

    for ref in reference:
        candidates = [
            gen for gen in generated
            if gen.region_id not in used_generated
            and (
                (ref.parent_region_id is None and gen.parent_region_id is None)
                or parent_map.get(ref.parent_region_id or "") == gen.parent_region_id
            )
            and branch_scope_compatible(ref, gen)
        ]
        scored = [(gen, _alignment_score(ref, gen)) for gen in candidates]
        scored = [item for item in scored if item[1][0] > 0 or item[1][1] > 0.0]
        if not scored:
            continue
        gen, base_rationale = max(
            scored, key=lambda item: (item[1], tuple(-ord(c) for c in item[0].region_id))
        )
        rationale = (*base_rationale, sum(score == base_rationale for _, score in scored) > 1)
        matched.append((ref, gen, rationale))
        used_generated.add(gen.region_id)
        parent_map[ref.region_id] = gen.region_id
    matched_ref = {item[0].region_id for item in matched}
    return (
        matched,
        [region for region in reference if region.region_id not in matched_ref],
        [region for region in generated if region.region_id not in used_generated],
    )


def evaluate_structure(
    case_id: str, candidate_id: str, reference: EvalGraph, generated: EvalGraph, actions: ActionResult
) -> StructureResult:
    all_reference_actions = {node.id for node in reference.nodes if node.type == "action"}
    anchor_coverage = (
        len(actions.reference_to_generated) / len(all_reference_actions)
        if all_reference_actions else 1.0
    )
    unsupported = [
        f"{side}:{node.id}:{node.semantic_type}"
        for side, graph in (("reference", reference), ("generated", generated))
        for node in graph.nodes if node.type == "unsupported_control"
    ]
    if unsupported:
        item = AutomaticItem(
            case_id, candidate_id, "Structure",
            evaluation_item_id(case_id, candidate_id, "structure", "unscorable"),
            "UNSCORABLE", {"review_triggers": ["unsupported_structure_region"]},
            {"unsupported_controls": unsupported},
            "Unsupported control semantics prevent deterministic region extraction.",
        )
        return StructureResult(case_id, candidate_id, (), (), (), SoftCounts(), 0.0, 0.0,
                               anchor_coverage, 0, 0.0, tuple(unsupported), (item,))

    reference_regions = extract_regions(reference, {value: value for value in actions.reference_to_generated})
    generated_regions = extract_regions(generated, actions.generated_to_reference)
    paired, missing, extra = _align_regions(reference_regions, generated_regions)
    scores: list[RegionScore] = []
    total_scorable = total_possible = anchor_limited = 0

    for ref, gen, alignment in paired:
        triggers: set[str] = set()
        if alignment[3]:
            triggers.add("ambiguous_structure_region")
        components: dict[str, float | None] = {"mode": float(ref.mode == gen.mode)}
        branch_matching: tuple[Mapping[str, Any], ...] = ()
        if ref.mode in {"exclusive", "parallel"}:
            branch, branch_matching = _branch_score(ref.branches, gen.branches)
            components["branch_semantics"] = branch
            components["closure_synchronization"] = float(ref.closure == gen.closure)
        else:
            components["loop_body"] = _jaccard(ref.loop_body, gen.loop_body) if ref.loop_body and gen.loop_body else None
            components["exit"] = _jaccard(ref.loop_exit, gen.loop_exit) if ref.loop_exit and gen.loop_exit else None

        ref_guards = [branch.guard for branch in ref.branches]
        gen_guards = [branch.guard for branch in gen.branches]
        guard_expected = any(ref_guards) or any(gen_guards)
        if guard_expected:
            if ref_guards and gen_guards and all(ref_guards) and all(gen_guards) and len(ref_guards) == len(gen_guards):
                guard_pairs = [
                    (detail["reference_branch"], detail["generated_branch"])
                    for detail in branch_matching
                ]
                ref_by_id = {branch.branch_id: branch for branch in ref.branches}
                gen_by_id = {branch.branch_id: branch for branch in gen.branches}
                components["guard"] = (
                    sum(ref_by_id[left].guard == gen_by_id[right].guard for left, right in guard_pairs)
                    / len(ref.branches)
                )
            else:
                components["guard"] = None
                triggers.add("guard_ambiguity")

        raw_anchor_limited = (
            len(ref.action_footprint) < len(ref.raw_action_footprint)
            or len(gen.action_footprint) < len(gen.raw_action_footprint)
        )
        if raw_anchor_limited:
            triggers.add("anchor_limited_structure_region")
            anchor_limited += 1
            for name in ("branch_semantics", "loop_body", "exit", "guard"):
                if name in components:
                    components[name] = None
        scorable = [value for value in components.values() if value is not None]
        total_scorable += len(scorable)
        total_possible += len(components)
        similarity = sum(scorable) / len(scorable) if scorable else None
        if similarity is None:
            triggers.add("ambiguous_structure_region")
            tp = fp = fn = 0.0
        else:
            tp, fp, fn = similarity, 1.0 - similarity, 1.0 - similarity
        scores.append(RegionScore(
            ref.region_id, gen.region_id, ref.mode, gen.mode, components, similarity,
            tp, fp, fn,
            {"boundary_agreement": alignment[0], "footprint_jaccard": alignment[1],
             "depth_agreement": bool(alignment[2]), "parent_region": ref.parent_region_id,
             "parent_branch": ref.parent_branch_id,
             "alignment_ambiguous": alignment[3]},
            branch_matching, tuple(sorted(triggers)),
        ))

    for ref in missing:
        scores.append(RegionScore(ref.region_id, None, ref.mode, None, {}, 0.0, 0.0, 0.0, 1.0,
                                  {"reason": "missing_reference_region"}, (),
                                  ("missing_structure_region",)))
    for gen in extra:
        scores.append(RegionScore(None, gen.region_id, None, gen.mode, {}, 0.0, 0.0, 1.0, 0.0,
                                  {"reason": "extra_generated_region"}, (),
                                  ("extra_structure_region",)))

    counts = SoftCounts(
        sum(score.tp for score in scores),
        sum(score.fp for score in scores),
        sum(score.fn for score in scores),
    )
    items: list[AutomaticItem] = []
    for index, score in enumerate(scores):
        if score.reference_region_id is None:
            label = "FP"
        elif score.generated_region_id is None:
            label = "FN"
        else:
            label = "SOFT"
        payload = {
            "reference_region_id": score.reference_region_id,
            "generated_region_id": score.generated_region_id,
            "reference_mode": score.reference_mode,
            "generated_mode": score.generated_mode,
            "component_scores": dict(score.component_scores),
            "region_similarity": score.similarity,
            "soft_counts": {"tp": score.tp, "fp": score.fp, "fn": score.fn},
            "review_triggers": list(score.review_triggers),
        }
        evidence = {
            "alignment_rationale": dict(score.alignment_rationale),
            "branch_matching": list(score.branch_matching),
        }
        items.append(AutomaticItem(
            case_id, candidate_id, "Structure",
            evaluation_item_id(case_id, candidate_id, "structure", "region", str(index)),
            label, payload, evidence,
            "Logical region scored once from the mean of deterministically scorable components.",
        ))

    paired_scorable = sum(
        score.reference_region_id is not None
        and score.generated_region_id is not None
        and score.similarity is not None
        for score in scores
    )
    region_coverage = paired_scorable / len(reference_regions) if reference_regions else None
    component_coverage = (
        total_scorable / total_possible
        if total_possible else (0.0 if reference_regions or generated_regions else None)
    )
    paired_count = len(paired)
    return StructureResult(
        case_id, candidate_id, reference_regions, generated_regions, tuple(scores), counts,
        component_coverage, region_coverage, anchor_coverage, anchor_limited,
        anchor_limited / paired_count if paired_count else 0.0, (), tuple(items),
    )
