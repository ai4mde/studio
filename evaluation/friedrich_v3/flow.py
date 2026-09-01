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
    action_anchor_coverage: float
    occurrence_ambiguous_fact_count: int
    occurrence_ambiguous_fact_rate: float
    contested_fact_count: int
    contested_fact_rate: float
    review_pending_fact_count: int
    review_pending_fact_rate: float
    unscorable: tuple[str, ...]
    items: tuple[AutomaticItem, ...]

    @property
    def metric_defined(self) -> bool:
        return not self.unscorable and bool(self.reference_facts or self.generated_facts)


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
    ref_matched = set(actions.reference_to_generated)
    all_ref = {node.id for node in reference.nodes if node.type == "action"}
    action_anchor_coverage = len(ref_matched) / len(all_ref) if all_ref else 1.0
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
        return FlowResult(case_id, candidate_id, (), (), Counts(), 0.0, action_anchor_coverage,
                          0, 0.0, 0, 0.0, 0, 0.0, tuple(unsupported), items)
    gen_matched = set(actions.generated_to_reference)
    full_ref_precedence = _precedence(reference, all_ref)
    all_ref_facts = _transitive_reduction(full_ref_precedence)
    # Projection precedes reduction so unmatched intermediate Actions remain
    # traversable and can induce a required relation between matched anchors.
    ref_facts = _transitive_reduction({
        fact for fact in full_ref_precedence
        if fact[0] in ref_matched and fact[1] in ref_matched
    })
    generated_precedence = _precedence(generated, gen_matched)
    generated_raw = _transitive_reduction(generated_precedence)
    gen_to_ref = actions.generated_to_reference
    gen_facts = {(gen_to_ref[a], gen_to_ref[b]) for a, b in generated_raw}
    ref_to_gen = actions.reference_to_generated
    tp = {
        (source, target) for source, target in ref_facts
        if (ref_to_gen[source], ref_to_gen[target]) in generated_precedence
    }
    fn = ref_facts - tp
    # Generated nonredundant precedence is unsupported only when the full
    # reference strict reachability does not support that direction.
    fp = {fact for fact in gen_facts if fact not in full_ref_precedence}
    items: list[AutomaticItem] = []
    for label, facts, rationale in (
        ("TP", tp, "Required matched-action precedence is preserved."),
        ("FN", fn, "Required matched-action precedence is missing."),
        ("FP", fp, "Generated model imposes unsupported matched-action precedence."),
    ):
        for source, target in sorted(facts):
            ambiguous = bool({source, target} & actions.occurrence_ambiguous_reference_ids)
            contested = bool({source, target} & actions.contested_reference_ids)
            review_pending = bool({source, target} & actions.review_pending_reference_ids)
            triggers = []
            if ambiguous or contested or review_pending:
                triggers.append("anchor_limited_flow_relation")
            uncertain_anchors = sorted(
                {source, target}
                & (actions.occurrence_ambiguous_reference_ids
                   | actions.contested_reference_ids
                   | actions.review_pending_reference_ids)
            )
            items.append(AutomaticItem(case_id, candidate_id, "Flow",
                evaluation_item_id(case_id, candidate_id, "flow", label.lower(), source, target), label,
                {"source_reference_action": source, "target_reference_action": target,
                 "review_triggers": triggers, "occurrence_ambiguous": ambiguous,
                 "contested": contested, "review_pending": review_pending,
                 "review_cluster_concept": {"uncertain_action_anchors": uncertain_anchors}},
                {"reference_relation": [source, target], "source_label": reference.by_id[source].label,
                 "target_label": reference.by_id[target].label}, rationale))
    comparable_base = {
        fact for fact in all_ref_facts
        if fact[0] in ref_matched and fact[1] in ref_matched
    }
    coverage = len(comparable_base) / len(all_ref_facts) if all_ref_facts else 1.0
    scored_facts = ref_facts | gen_facts
    denominator = len(scored_facts)
    def dependent_count(anchor_ids: frozenset[str]) -> int:
        return sum(bool({source, target} & anchor_ids) for source, target in scored_facts)
    ambiguous_count = dependent_count(actions.occurrence_ambiguous_reference_ids)
    contested_count = dependent_count(actions.contested_reference_ids)
    review_count = dependent_count(actions.review_pending_reference_ids)
    return FlowResult(
        case_id, candidate_id, tuple(sorted(ref_facts)), tuple(sorted(gen_facts)),
        Counts(len(tp), len(fp), len(fn)), coverage, action_anchor_coverage,
        ambiguous_count, ambiguous_count / denominator if denominator else 0.0,
        contested_count, contested_count / denominator if denominator else 0.0,
        review_count, review_count / denominator if denominator else 0.0,
        (), tuple(items),
    )
