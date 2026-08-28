from __future__ import annotations

from dataclasses import dataclass

from .action import ActionResult
from .core import AutomaticItem, Counts, EvalGraph, evaluation_item_id, reachable


Relation = tuple[str, str]


@dataclass(frozen=True, slots=True)
class FlowResult:
    case_id: str
    candidate_id: str
    reference_facts: tuple[Relation, ...]
    generated_facts: tuple[Relation, ...]
    counts: Counts
    coverage: float
    unscorable: tuple[str, ...]
    items: tuple[AutomaticItem, ...]


def _same_cycle(graph: EvalGraph, source: str, target: str) -> bool:
    return target in reachable(graph, source) and source in reachable(graph, target)


def _precedence(graph: EvalGraph, action_ids: set[str]) -> set[Relation]:
    facts = {
        (source, target)
        for source in action_ids
        for target in action_ids
        if source != target and target in reachable(graph, source) and not _same_cycle(graph, source, target)
    }
    return facts


def _transitive_reduction(relations: set[Relation]) -> set[Relation]:
    reduced = set(relations)
    nodes = {node for relation in relations for node in relation}
    for source, target in sorted(relations):
        if any((source, middle) in relations and (middle, target) in relations for middle in nodes - {source, target}):
            reduced.discard((source, target))
    return reduced


def evaluate_flow(
    case_id: str, candidate_id: str, reference: EvalGraph, generated: EvalGraph, actions: ActionResult
) -> FlowResult:
    unsupported = [
        f"{side}:{node.id}:{node.semantic_type}"
        for side, graph in (("reference", reference), ("generated", generated))
        for node in graph.nodes if node.type == "unsupported_control"
    ]
    if unsupported:
        items = tuple(
            AutomaticItem(case_id, candidate_id, "Flow",
                evaluation_item_id(case_id, candidate_id, "flow", "unscorable", str(index)), "UNSCORABLE",
                {"unsupported_control": reason}, {"control": reason},
                "Flow semantics cannot be preserved through an unsupported control construct.")
            for index, reason in enumerate(unsupported)
        )
        return FlowResult(case_id, candidate_id, (), (), Counts(), 0.0, tuple(unsupported), items)
    ref_matched = set(actions.reference_to_generated)
    gen_matched = set(actions.generated_to_reference)
    all_ref = {node.id for node in reference.nodes if node.type == "action"}
    all_ref_facts = _transitive_reduction(_precedence(reference, all_ref))
    ref_facts = _transitive_reduction(_precedence(reference, ref_matched))
    generated_raw = _transitive_reduction(_precedence(generated, gen_matched))
    gen_to_ref = actions.generated_to_reference
    gen_facts = {(gen_to_ref[a], gen_to_ref[b]) for a, b in generated_raw}
    tp, fn, fp = ref_facts & gen_facts, ref_facts - gen_facts, gen_facts - ref_facts
    items: list[AutomaticItem] = []
    for label, facts, rationale in (
        ("TP", tp, "Required matched-action precedence is preserved."),
        ("FN", fn, "Required matched-action precedence is missing."),
        ("FP", fp, "Generated model imposes unsupported matched-action precedence."),
    ):
        for source, target in sorted(facts):
            items.append(AutomaticItem(case_id, candidate_id, "Flow",
                evaluation_item_id(case_id, candidate_id, "flow", label.lower(), source, target), label,
                {"source_reference_action": source, "target_reference_action": target},
                {"reference_relation": [source, target], "source_label": reference.by_id[source].label,
                 "target_label": reference.by_id[target].label}, rationale))
    coverage = min(1.0, len(ref_facts) / len(all_ref_facts)) if all_ref_facts else 1.0
    return FlowResult(
        case_id, candidate_id, tuple(sorted(ref_facts)), tuple(sorted(gen_facts)),
        Counts(len(tp), len(fp), len(fn)), coverage, (), tuple(items),
    )
