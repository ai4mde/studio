from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import fmean
from typing import Any, Iterable, Literal, Mapping

from .eval_graph import EvalGraph


GranularityDirection = Literal[
    "one_reference_to_many_generated",
    "many_reference_to_one_generated",
]


@dataclass(frozen=True, slots=True)
class GranularityMismatch:
    reference_ids: tuple[str, ...]
    generated_ids: tuple[str, ...]
    direction: GranularityDirection

    def __post_init__(self) -> None:
        allowed_directions = {
            "one_reference_to_many_generated",
            "many_reference_to_one_generated",
        }
        if self.direction not in allowed_directions:
            raise ValueError(f"Unsupported granularity direction: {self.direction}")
        if not self.reference_ids or not self.generated_ids:
            raise ValueError("Granularity evidence must identify nodes on both sides")
        if len(set(self.reference_ids)) != len(self.reference_ids):
            raise ValueError("Granularity reference ids must be unique")
        if len(set(self.generated_ids)) != len(self.generated_ids):
            raise ValueError("Granularity generated ids must be unique")
        if self.direction == "one_reference_to_many_generated":
            if len(self.reference_ids) != 1 or len(self.generated_ids) < 2:
                raise ValueError("Direction requires one reference and many generated actions")
        elif len(self.reference_ids) < 2 or len(self.generated_ids) != 1:
            raise ValueError("Direction requires many reference and one generated action")


@dataclass(frozen=True, slots=True)
class ActionCaseScore:
    case_id: str
    reference_action_count: int
    generated_action_count: int
    TP: int
    FP: int
    FN: int
    precision: float | None
    recall: float | None
    f1: float | None
    empty: bool
    matched_reference_ids: tuple[str, ...]
    matched_generated_ids: tuple[str, ...]
    unmatched_reference_ids: tuple[str, ...]
    unmatched_generated_ids: tuple[str, ...]
    accepted_pairs: tuple[tuple[str, str], ...]
    unresolved_component_count: int
    unresolved_reference_node_count: int
    unresolved_generated_node_count: int
    unresolved_reference_ids: tuple[str, ...]
    unresolved_generated_ids: tuple[str, ...]
    granularity_mismatch_count: int
    granularity_mismatches: tuple[GranularityMismatch, ...]
    unlabeled_action_count: int
    unlabeled_reference_action_count: int
    unlabeled_generated_action_count: int

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["accepted_pairs"] = [
            {"reference_id": reference_id, "generated_id": generated_id}
            for reference_id, generated_id in self.accepted_pairs
        ]
        return result


@dataclass(frozen=True, slots=True)
class ActionDatasetScore:
    case_count: int
    empty_case_count: int
    defined_macro_case_count: int
    total_reference_actions: int
    total_generated_actions: int
    micro_TP: int
    micro_FP: int
    micro_FN: int
    micro_precision: float | None
    micro_recall: float | None
    micro_f1: float | None
    macro_f1: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value == 1
    if isinstance(value, str):
        return value.strip().casefold() in {"true", "yes", "1"}
    return False


def _metrics(
    TP: int, FP: int, FN: int, *, empty: bool
) -> tuple[float | None, float | None, float | None]:
    if empty:
        return None, None, None
    precision = TP / (TP + FP) if TP + FP else 0.0
    recall = TP / (TP + FN) if TP + FN else 0.0
    denominator = 2 * TP + FP + FN
    f1 = 2 * TP / denominator if denominator else 0.0
    return precision, recall, f1


def score_action_case(
    case_id: str,
    reference_graph: EvalGraph,
    generated_graph: EvalGraph,
    matcher_rows: Iterable[Mapping[str, Any]],
    *,
    granularity_mismatches: Iterable[GranularityMismatch] = (),
) -> ActionCaseScore:
    """Score one case from frozen matcher rows without revisiting their decisions."""
    reference_actions = {
        node.id: node for node in reference_graph.nodes if node.type == "action"
    }
    generated_actions = {
        node.id: node for node in generated_graph.nodes if node.type == "action"
    }
    rows = [row for row in matcher_rows if str(row.get("case_id")) == case_id]

    accepted_pairs = sorted(
        (
            str(row["reference_id"]),
            str(row["generated_id"]),
        )
        for row in rows
        if _truthy(row.get("final_prediction"))
    )
    matched_reference = [pair[0] for pair in accepted_pairs]
    matched_generated = [pair[1] for pair in accepted_pairs]
    if len(matched_reference) != len(set(matched_reference)):
        raise ValueError(f"Case {case_id} has non-one-to-one reference matches")
    if len(matched_generated) != len(set(matched_generated)):
        raise ValueError(f"Case {case_id} has non-one-to-one generated matches")
    unknown_reference = set(matched_reference) - set(reference_actions)
    unknown_generated = set(matched_generated) - set(generated_actions)
    if unknown_reference or unknown_generated:
        raise ValueError(
            f"Case {case_id} accepted matches reference non-action or unknown nodes: "
            f"reference={sorted(unknown_reference)}, generated={sorted(unknown_generated)}"
        )

    unmatched_reference = sorted(set(reference_actions) - set(matched_reference))
    unmatched_generated = sorted(set(generated_actions) - set(matched_generated))

    unresolved_components: dict[str, tuple[set[str], set[str]]] = {}
    for row in rows:
        if not _truthy(row.get("unresolved_ambiguity")):
            continue
        component_id = str(row.get("unresolved_component_id") or "")
        if not component_id:
            raise ValueError(f"Case {case_id} has unresolved rows without a component id")
        reference_ids = {str(value) for value in row.get("unresolved_reference_nodes", [])}
        generated_ids = {str(value) for value in row.get("unresolved_generated_nodes", [])}
        previous = unresolved_components.setdefault(component_id, (set(), set()))
        previous[0].update(reference_ids)
        previous[1].update(generated_ids)

    unresolved_reference = sorted(
        {node_id for component in unresolved_components.values() for node_id in component[0]}
    )
    unresolved_generated = sorted(
        {node_id for component in unresolved_components.values() for node_id in component[1]}
    )
    if not set(unresolved_reference) <= set(unmatched_reference):
        raise ValueError(f"Case {case_id} has matched reference nodes marked unresolved")
    if not set(unresolved_generated) <= set(unmatched_generated):
        raise ValueError(f"Case {case_id} has matched generated nodes marked unresolved")
    if not set(unresolved_reference) <= set(reference_actions):
        raise ValueError(f"Case {case_id} has unresolved non-action reference nodes")
    if not set(unresolved_generated) <= set(generated_actions):
        raise ValueError(f"Case {case_id} has unresolved non-action generated nodes")

    granularity = tuple(granularity_mismatches)
    for mismatch in granularity:
        if not set(mismatch.reference_ids) <= set(reference_actions):
            raise ValueError(f"Case {case_id} has unknown granularity reference nodes")
        if not set(mismatch.generated_ids) <= set(generated_actions):
            raise ValueError(f"Case {case_id} has unknown granularity generated nodes")

    TP = len(accepted_pairs)
    FP = len(unmatched_generated)
    FN = len(unmatched_reference)
    if TP + FN != len(reference_actions) or TP + FP != len(generated_actions):
        raise AssertionError(f"Case {case_id} violates Action scoring accounting")
    empty = not reference_actions and not generated_actions
    precision, recall, f1 = _metrics(TP, FP, FN, empty=empty)
    unlabeled_reference = sum(node.label is None for node in reference_actions.values())
    unlabeled_generated = sum(node.label is None for node in generated_actions.values())

    return ActionCaseScore(
        case_id=case_id,
        reference_action_count=len(reference_actions),
        generated_action_count=len(generated_actions),
        TP=TP,
        FP=FP,
        FN=FN,
        precision=precision,
        recall=recall,
        f1=f1,
        empty=empty,
        matched_reference_ids=tuple(sorted(matched_reference)),
        matched_generated_ids=tuple(sorted(matched_generated)),
        unmatched_reference_ids=tuple(unmatched_reference),
        unmatched_generated_ids=tuple(unmatched_generated),
        accepted_pairs=tuple(accepted_pairs),
        unresolved_component_count=len(unresolved_components),
        unresolved_reference_node_count=len(unresolved_reference),
        unresolved_generated_node_count=len(unresolved_generated),
        unresolved_reference_ids=tuple(unresolved_reference),
        unresolved_generated_ids=tuple(unresolved_generated),
        granularity_mismatch_count=len(granularity),
        granularity_mismatches=granularity,
        unlabeled_action_count=unlabeled_reference + unlabeled_generated,
        unlabeled_reference_action_count=unlabeled_reference,
        unlabeled_generated_action_count=unlabeled_generated,
    )


def aggregate_action_scores(
    case_scores: Iterable[ActionCaseScore],
) -> ActionDatasetScore:
    scores = tuple(case_scores)
    micro_TP = sum(score.TP for score in scores)
    micro_FP = sum(score.FP for score in scores)
    micro_FN = sum(score.FN for score in scores)
    empty = not any(
        score.reference_action_count or score.generated_action_count for score in scores
    )
    micro_precision, micro_recall, micro_f1 = _metrics(
        micro_TP, micro_FP, micro_FN, empty=empty
    )
    defined_f1 = [score.f1 for score in scores if score.f1 is not None]
    return ActionDatasetScore(
        case_count=len(scores),
        empty_case_count=sum(score.empty for score in scores),
        defined_macro_case_count=len(defined_f1),
        total_reference_actions=sum(score.reference_action_count for score in scores),
        total_generated_actions=sum(score.generated_action_count for score in scores),
        micro_TP=micro_TP,
        micro_FP=micro_FP,
        micro_FN=micro_FN,
        micro_precision=micro_precision,
        micro_recall=micro_recall,
        micro_f1=micro_f1,
        macro_f1=fmean(defined_f1) if defined_f1 else None,
    )
