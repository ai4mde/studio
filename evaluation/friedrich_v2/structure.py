from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from typing import Any

from .action import ActionResult
from .core import AutomaticItem, Counts, EvalGraph, evaluation_item_id, reachable, strongly_connected_components


Fact = tuple[str, str, tuple[str, ...]]


class StructureCounts(Counts):
    """Apply the frozen perfect-match convention to two empty fact sets."""

    @property
    def precision(self) -> float:
        return 1.0 if self.tp == self.fp == self.fn == 0 else super().precision

    @property
    def recall(self) -> float:
        return 1.0 if self.tp == self.fp == self.fn == 0 else super().recall

    @property
    def f1(self) -> float:
        return 1.0 if self.tp == self.fp == self.fn == 0 else super().f1


@dataclass(frozen=True, slots=True)
class StructureResult:
    case_id: str
    candidate_id: str
    reference_facts: tuple[Fact, ...]
    generated_facts: tuple[Fact, ...]
    counts: Counts
    coverage: float
    anchor_coverage: float
    anchor_limited_count: int
    anchor_limited_rate: float
    unscorable: tuple[str, ...]
    items: tuple[AutomaticItem, ...]


def _distances(graph: EvalGraph, start: str) -> dict[str, int]:
    distances = {start: 0}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for target in graph.outgoing[node]:
            if target not in distances:
                distances[target] = distances[node] + 1
                queue.append(target)
    return distances


def _nearest_common(graph: EvalGraph, starts: tuple[str, ...], preferred: str) -> str | None:
    maps = [_distances(graph, start) for start in starts]
    common = set.intersection(*(set(item) for item in maps)) if maps else set()
    candidates = [node for node in common if graph.by_id[node].type == preferred]
    if not candidates:
        candidates = list(common)
    return min(candidates, key=lambda node: (max(item[node] for item in maps), sum(item[node] for item in maps), node), default=None)


def _anchor_map(actions: ActionResult, generated: bool) -> dict[str, str]:
    return actions.generated_to_reference if generated else {key: key for key in actions.reference_to_generated}


def _nearest_anchor(graph: EvalGraph, start: str, anchors: dict[str, str], reverse: bool = False) -> str:
    adjacency = graph.incoming if reverse else graph.outgoing
    queue = deque([(start, 0)])
    seen = {start}
    found: list[tuple[int, str]] = []
    while queue:
        node, distance = queue.popleft()
        if node in anchors and (node != start or not reverse):
            found.append((distance, anchors[node]))
            continue
        for target in adjacency[node]:
            if target not in seen:
                seen.add(target)
                queue.append((target, distance + 1))
    return min(found, default=(0, "END" if not reverse else "START"))[1]


def _branch_signature(graph: EvalGraph, start: str, closure: str | None, anchors: dict[str, str]) -> tuple[str, ...]:
    if closure is not None and start == closure:
        return ("EMPTY",)
    allowed = reachable(graph, start, {closure} if closure else set()) | {start}
    return tuple(sorted({anchors[node] for node in allowed if node in anchors})) or ("EMPTY",)


def extract_structure_facts(graph: EvalGraph, anchors: dict[str, str]) -> tuple[list[Fact], list[str], int]:
    facts: list[Fact] = []
    unscorable = [f"{node.id}:{node.semantic_type}" for node in graph.nodes if node.type == "unsupported_control"]
    if unscorable:
        return facts, unscorable, len(unscorable)
    regions = 0
    cyclic_nodes: set[str] = set()
    for component in strongly_connected_components(graph):
        is_cycle = len(component) > 1 or any(edge.source == edge.target and edge.source in component for edge in graph.edges)
        if not is_cycle:
            continue
        cyclic_nodes.update(component)
        controllers = [
            node for node in component
            if any(target in component for target in graph.outgoing[node])
            and any(target not in component for target in graph.outgoing[node])
        ]
        if len(controllers) != 1:
            unscorable.append("ambiguous_loop:" + ",".join(sorted(component)))
            continue
        controller = controllers[0]
        entry = _nearest_anchor(graph, controller, anchors, reverse=True)
        exits = [target for target in graph.outgoing[controller] if target not in component]
        exit_anchor = _nearest_anchor(graph, exits[0], anchors) if exits else "END"
        key = f"{entry}->{exit_anchor}"
        body = tuple(sorted({anchors[node] for node in component if node in anchors})) or ("EMPTY",)
        facts.extend([("mode", entry, ("loop",)), ("loop_body", key, body), ("loop_exit", key, (exit_anchor,))])
        regions += 1
    for node in sorted(graph.nodes, key=lambda item: item.id):
        if node.id in cyclic_nodes or node.type not in {"decision", "fork"} or len(graph.outgoing[node.id]) < 2:
            continue
        successors = graph.outgoing[node.id]
        preferred = "merge" if node.type == "decision" else "join"
        closure = _nearest_common(graph, successors, preferred)
        entry = _nearest_anchor(graph, node.id, anchors, reverse=True)
        continuation = _nearest_anchor(graph, closure, anchors) if closure else "END"
        key = f"{entry}->{continuation}"
        mode = "exclusive" if node.type == "decision" else "parallel"
        facts.append(("mode", entry, (mode,)))
        for signature in sorted(_branch_signature(graph, successor, closure, anchors) for successor in successors):
            facts.append(("branch", key, (mode,) + signature))
        if closure:
            kind = "exclusive_convergence" if mode == "exclusive" else "parallel_synchronization"
            facts.append((kind, key, (continuation,)))
        regions += 1
    return facts, unscorable, regions


def _anchor_limited_facts(graph: EvalGraph, anchors: dict[str, str], uncertain: frozenset[str]) -> set[Fact]:
    limited: set[Fact] = set()
    for component in strongly_connected_components(graph):
        cyclic = len(component) > 1 or any(edge.source == edge.target and edge.source in component for edge in graph.edges)
        if not cyclic:
            continue
        controllers = [
            node for node in component
            if any(target in component for target in graph.outgoing[node])
            and any(target not in component for target in graph.outgoing[node])
        ]
        if len(controllers) != 1:
            continue
        controller = controllers[0]
        entry = _nearest_anchor(graph, controller, anchors, reverse=True)
        exits = [target for target in graph.outgoing[controller] if target not in component]
        exit_anchor = _nearest_anchor(graph, exits[0], anchors) if exits else "END"
        key = f"{entry}->{exit_anchor}"
        body = tuple(sorted({anchors[node] for node in component if node in anchors})) or ("EMPTY",)
        if any(graph.by_id[node].type == "action" and node not in anchors for node in component) or set(body) & uncertain:
            limited.update({("loop_body", key, body), ("loop_exit", key, (exit_anchor,))})
        if entry in uncertain:
            limited.add(("mode", entry, ("loop",)))
    cyclic_nodes = set().union(*(
        component for component in strongly_connected_components(graph)
        if len(component) > 1 or any(edge.source == edge.target and edge.source in component for edge in graph.edges)
    )) if graph.nodes else set()
    for node in sorted(graph.nodes, key=lambda item: item.id):
        if node.id in cyclic_nodes or node.type not in {"decision", "fork"} or len(graph.outgoing[node.id]) < 2:
            continue
        successors = graph.outgoing[node.id]
        mode = "exclusive" if node.type == "decision" else "parallel"
        closure = _nearest_common(graph, successors, "merge" if mode == "exclusive" else "join")
        entry = _nearest_anchor(graph, node.id, anchors, reverse=True)
        continuation = _nearest_anchor(graph, closure, anchors) if closure else "END"
        key = f"{entry}->{continuation}"
        if entry in uncertain:
            limited.add(("mode", entry, (mode,)))
        for successor in successors:
            signature = _branch_signature(graph, successor, closure, anchors)
            allowed = set() if successor == closure else reachable(graph, successor, {closure} if closure else set()) | {successor}
            if any(graph.by_id[item].type == "action" and item not in anchors for item in allowed) or set(signature) & uncertain:
                limited.add(("branch", key, (mode,) + signature))
        if closure and continuation in uncertain:
            kind = "exclusive_convergence" if mode == "exclusive" else "parallel_synchronization"
            limited.add((kind, key, (continuation,)))
    return limited


def _guard_outcome_regions(
    graph: EvalGraph, anchors: dict[str, str]
) -> dict[str, list[dict[str, tuple[str, ...]]]]:
    """Return only complete, uniquely guarded exclusive regions."""
    edge_labels = {(edge.source, edge.target): edge.label for edge in graph.edges}
    regions: dict[str, list[dict[str, tuple[str, ...]]]] = {}
    for node in sorted(graph.nodes, key=lambda item: item.id):
        successors = graph.outgoing[node.id]
        if node.type != "decision" or len(successors) < 2:
            continue
        labels = [edge_labels.get((node.id, successor)) for successor in successors]
        if any(not label for label in labels) or len(set(labels)) != len(labels):
            continue
        closure = _nearest_common(graph, successors, "merge")
        entry = _nearest_anchor(graph, node.id, anchors, reverse=True)
        mapping = {
            str(label): _branch_signature(graph, successor, closure, anchors)
            for successor, label in zip(successors, labels)
        }
        regions.setdefault(entry, []).append(mapping)
    return regions


def _comparable_guard_facts(
    reference: EvalGraph,
    generated: EvalGraph,
    reference_anchors: dict[str, str],
    generated_anchors: dict[str, str],
) -> tuple[list[Fact], list[Fact]]:
    """Score guard outcomes only when the two region vocabularies are unambiguous."""
    reference_regions = _guard_outcome_regions(reference, reference_anchors)
    generated_regions = _guard_outcome_regions(generated, generated_anchors)
    reference_facts: list[Fact] = []
    generated_facts: list[Fact] = []
    for entry in sorted(set(reference_regions) & set(generated_regions)):
        ref_candidates = reference_regions[entry]
        gen_candidates = generated_regions[entry]
        if len(ref_candidates) != 1 or len(gen_candidates) != 1:
            continue
        ref_mapping, gen_mapping = ref_candidates[0], gen_candidates[0]
        if set(ref_mapping) != set(gen_mapping):
            continue
        for guard in sorted(ref_mapping):
            reference_facts.append(("guard_outcome", entry, (guard,) + ref_mapping[guard]))
            generated_facts.append(("guard_outcome", entry, (guard,) + gen_mapping[guard]))
    return reference_facts, generated_facts


def evaluate_structure(
    case_id: str, candidate_id: str, reference: EvalGraph, generated: EvalGraph, actions: ActionResult
) -> StructureResult:
    reference_anchors = _anchor_map(actions, False)
    generated_anchors = _anchor_map(actions, True)
    ref_facts, ref_unscorable, ref_regions = extract_structure_facts(reference, reference_anchors)
    gen_facts, gen_unscorable, _ = extract_structure_facts(generated, generated_anchors)
    unscorable = [f"reference:{item}" for item in ref_unscorable] + [f"generated:{item}" for item in gen_unscorable]
    if unscorable:
        items = tuple(
            AutomaticItem(case_id, candidate_id, "Structure",
                evaluation_item_id(case_id, candidate_id, "structure", "unscorable", str(index)), "UNSCORABLE",
                {"reason": reason}, {}, "Control behavior could not be represented without semantic loss.")
            for index, reason in enumerate(unscorable)
        )
        return StructureResult(
            case_id, candidate_id, tuple(sorted(ref_facts)), tuple(sorted(gen_facts)),
            Counts(), 0.0, 0.0, 0, 0.0, tuple(unscorable), items,
        )
    ref_guard_facts, gen_guard_facts = _comparable_guard_facts(
        reference, generated, reference_anchors, generated_anchors
    )
    ref_facts.extend(ref_guard_facts)
    gen_facts.extend(gen_guard_facts)
    ref_counter, gen_counter = Counter(ref_facts), Counter(gen_facts)
    common = ref_counter & gen_counter
    items: list[AutomaticItem] = []
    def evidence(fact: Fact) -> dict[str, Any]:
        tokens = set(fact[2])
        tokens.update(fact[1].split("->"))
        return {
            "fact": fact,
            "reference_action_labels": {
                token: reference.by_id[token].label
                for token in sorted(tokens)
                if token in reference.by_id and reference.by_id[token].type == "action"
            },
        }
    anchor_limited_count = 0
    total_fact_occurrences = sum(ref_counter.values()) + sum(gen_counter.values()) - sum(common.values())
    uncertain_anchors = actions.contested_reference_ids | actions.review_pending_reference_ids
    ref_limited = _anchor_limited_facts(reference, reference_anchors, uncertain_anchors)
    gen_limited = _anchor_limited_facts(generated, generated_anchors, uncertain_anchors)
    ref_limited.update(fact for fact in ref_guard_facts if set(fact[2][1:]) & uncertain_anchors)
    gen_limited.update(fact for fact in gen_guard_facts if set(fact[2][1:]) & uncertain_anchors)
    for label, counter, rationale in (
        ("TP", common, "Required behavioral Structure fact is preserved."),
        ("FN", ref_counter - gen_counter, "Required reference behavioral Structure fact is missing."),
        ("FP", gen_counter - ref_counter, "Generated model adds an unsupported behavioral Structure fact."),
    ):
        for fact, count in sorted(counter.items()):
            for occurrence in range(count):
                anchor_limited = fact in (ref_limited | gen_limited) if label == "TP" else fact in (ref_limited if label == "FN" else gen_limited)
                if anchor_limited:
                    anchor_limited_count += 1
                items.append(AutomaticItem(case_id, candidate_id, "Structure",
                    evaluation_item_id(case_id, candidate_id, "structure", label.lower(), str(len(items))), label,
                    {"fact": fact, "occurrence": occurrence, "anchor_limited": anchor_limited,
                     "review_triggers": ["anchor_limited_structure_fact"] if anchor_limited else [],
                     "review_cluster_concept": {"structure_region": fact[1]}},
                    evidence(fact), rationale))
    tp = sum(common.values())
    counts = StructureCounts(tp, sum(gen_counter.values()) - tp, sum(ref_counter.values()) - tp)
    coverage = ref_regions / (ref_regions + len(ref_unscorable)) if ref_regions + len(ref_unscorable) else 1.0
    all_reference_actions = sum(node.type == "action" for node in reference.nodes)
    anchor_coverage = len(actions.reference_to_generated) / all_reference_actions if all_reference_actions else 1.0
    return StructureResult(
        case_id, candidate_id, tuple(sorted(ref_facts)), tuple(sorted(gen_facts)),
        counts, coverage, anchor_coverage, anchor_limited_count,
        anchor_limited_count / total_fact_occurrences if total_fact_occurrences else 0.0,
        tuple(unscorable), tuple(items),
    )
