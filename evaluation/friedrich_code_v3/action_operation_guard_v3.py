"""Opt-in Action guard v3: operation entailment with reviewable uncertainty.

This module leaves the frozen matcher and guard v2 unchanged. A semantic
normalization is used only inside this versioned Action evaluation: a condition
such as "if not available" is not negation of the performed back-order act.
"""

from __future__ import annotations

from dataclasses import replace
import re
from typing import Mapping, Sequence

from evaluation.friedrich_v3.action import ACTION_SIMILARITY_THRESHOLD, SimilarityProvider
from evaluation.friedrich_v3.core import AutomaticItem, EvalGraph, evaluation_item_id
from evaluation.friedrich_semantic.action import (
    CONTEXTUAL_RESCUE_FLOOR, SemanticActivityUnit, SemanticActionResult,
    evaluate_semantic_actions,
)

from .action_operation_guard_v2 import (
    _strong_new_match, _words, main_operations, operation_verdict,
)


VERSION = "friedrich-code-action-operation-guard/3"


def _operation(label: str) -> str | None:
    """Recognize the performed act, including a request embedded in a compound act."""
    value = label.casefold()
    if re.search(r"\bback[\s-]?order(?:ed|s|ing)?\b", value):
        if main_operations(label):  # E.g. "check back-ordered parts" performs a check.
            return "other_performed"
        return "back_order"
    if re.search(r"\b(?:ask|asks|asked|request|requests|requested)\b", value):
        if re.search(r"\b(?:correction|corrected|correct)\b", value):
            # "correct ... as requested" performs correction, while a clause
            # headed by request performs the request itself.
            if re.search(r"^\s*correct\b", value):
                return "correction_with_request_context"
            return "correction_request"
        if re.search(r"\b(?:information|clarification|details)\b", value):
            return "information_request"
    if re.search(r"\bclarif(?:y|ies|ied|ication)\b", value):
        if main_operations(label):
            return "other_performed"
        return "clarification"
    if re.search(r"^\s*(?:\w+\s+){0,6}report(?:s|ed)?\s+(?:a\s+)?vacancy\b", value):
        return "vacancy_report"
    return None


def semantic_operation_decision(source: str, generated: str) -> str:
    """Return positive, incompatible, ambiguous, or defer to the v2 guard."""
    source_op, generated_op = _operation(source), _operation(generated)
    source_words, generated_words = set(_words(source)), set(_words(generated))
    if source_op == generated_op == "back_order":
        return "positive" if "part" in source_words & generated_words else "incompatible"
    if source_op == "information_request" and generated_op == "clarification":
        # The same participant and business information must be identifiable.
        if "department" in source_words & generated_words and (
            "information" in source_words & generated_words or
            "details" in source_words & generated_words
        ):
            return "positive"
        return "ambiguous"
    if source_op == generated_op == "correction_request":
        return "positive" if "correction" in source_words & generated_words else "ambiguous"
    if source_op == "correction_request" and generated_op == "correction_with_request_context":
        return "ambiguous"
    if source_op == "vacancy_report" and generated_op == "clarification":
        return "incompatible"
    if source_op and generated_op and source_op != generated_op:
        return "incompatible"
    if operation_verdict(source, generated) == "incompatible":
        return "incompatible"
    return "defer"


def _matching_label(label: str) -> str:
    """Remove conditional negation from back-order labels for the inherited veto."""
    if _operation(label) == "back_order":
        return re.sub(r"\bif\s+not\s+available\b", "when unavailable", label,
                      flags=re.IGNORECASE)
    return label


class _V3Similarity:
    def __init__(self, delegate: SimilarityProvider, refs: Sequence[str], gens: Sequence[str],
                 meanings: Sequence[str], baseline_pairs: frozenset[tuple[int, int]]) -> None:
        self.delegate = delegate
        self.refs, self.gens, self.meanings = tuple(refs), tuple(gens), tuple(meanings)
        self.baseline_pairs = baseline_pairs

    def matrix(self, reference: Sequence[str], generated: Sequence[str]) -> list[list[float]]:
        scores = self.delegate.matrix(reference, generated)
        if tuple(reference) != self.refs or tuple(generated) != self.gens:
            return scores
        output: list[list[float]] = []
        for i, row in enumerate(scores):
            adjusted: list[float] = []
            for j, score in enumerate(row):
                decision = semantic_operation_decision(self.meanings[i], self.gens[j])
                eligible = (decision == "positive" or
                            (decision == "defer" and (
                                (i, j) in self.baseline_pairs or
                                _strong_new_match(self.meanings[i], self.gens[j]))))
                adjusted.append(score if eligible else -1.0)
            output.append(adjusted)
        return output


def evaluate_semantic_actions_with_operation_guard_v3(
    case_id: str, candidate_id: str, reference: EvalGraph, generated: EvalGraph,
    similarity: SimilarityProvider, threshold: float = ACTION_SIMILARITY_THRESHOLD, *,
    source_text: str, reference_review_evidence: Sequence[Mapping[str, object]] = (),
    semantic_activity_units: Sequence[SemanticActivityUnit] | None = None,
) -> SemanticActionResult:
    refs = sorted((node for node in reference.nodes if node.type == "action"), key=lambda n: n.id)
    gens = sorted((node for node in generated.nodes if node.type == "action"), key=lambda n: n.id)
    units = {unit.reference_ids[0]: unit for unit in semantic_activity_units or ()
             if len(unit.reference_ids) == 1}
    baseline = evaluate_semantic_actions(
        case_id, candidate_id, reference, generated, similarity, threshold,
        source_text=source_text, reference_review_evidence=reference_review_evidence,
        semantic_activity_units=semantic_activity_units,
    )
    ref_index = {node.id: i for i, node in enumerate(refs)}
    gen_index = {node.id: j for j, node in enumerate(gens)}
    baseline_pairs = frozenset(
        (ref_index[ref_id], gen_index[gen_id])
        for mapping in baseline.accepted_mappings
        for ref_id in mapping.reference_ids for gen_id in mapping.generated_ids
    )
    normalized = EvalGraph(
        tuple(replace(node, label=_matching_label(node.label or ""))
              if node.type == "action" else node for node in generated.nodes),
        generated.edges,
    )
    normalized_gens = sorted((node for node in normalized.nodes if node.type == "action"),
                             key=lambda n: n.id)
    provider = _V3Similarity(
        similarity, [node.label or "" for node in refs],
        [node.label or "" for node in normalized_gens],
        [units[node.id].meaning if node.id in units else node.label or "" for node in refs],
        baseline_pairs,
    )
    result = evaluate_semantic_actions(
        case_id, candidate_id, reference, normalized, provider, threshold,
        source_text=source_text, reference_review_evidence=reference_review_evidence,
        semantic_activity_units=semantic_activity_units,
    )
    meanings = {unit.unit_id: unit.meaning for unit in result.semantic_activity_units}
    for mapping in result.accepted_mappings:
        if any(semantic_operation_decision(meanings[unit_id],
                   generated.by_id[node_id].label or "") in {"incompatible", "ambiguous"}
               for unit_id in mapping.unit_ids for node_id in mapping.generated_ids):
            raise ValueError(f"Action guard v3 accepted an unresolved or incompatible pair: {mapping.mapping_id}")
    restored_groups = tuple(replace(group, generated_labels=tuple(
        generated.by_id[node_id].label or "" for node_id in group.generated_ids))
        for group in result.generated_activity_groups)
    mapped = {unit_id for mapping in result.accepted_mappings for unit_id in mapping.unit_ids}
    scores = similarity.matrix([node.label or "" for node in refs],
                               [node.label or "" for node in gens])
    ambiguous = list(result.ambiguous_mappings)
    existing = {item.get("unit_id") for item in ambiguous}
    for i, ref in enumerate(refs):
        unit = units.get(ref.id)
        if unit is None or unit.unit_id in mapped or unit.unit_id in existing:
            continue
        candidates = [
            {"generated_id": gen.id, "label": gen.label, "similarity": scores[i][j]}
            for j, gen in enumerate(gens)
            if scores[i][j] >= CONTEXTUAL_RESCUE_FLOOR
            and semantic_operation_decision(unit.meaning, gen.label or "") == "ambiguous"
        ]
        if candidates:
            ambiguous.append({"unit_id": unit.unit_id,
                              "trigger": "unresolved_action_operation_correspondence",
                              "candidates": sorted(candidates, key=lambda x: (-x["similarity"], x["generated_id"]))})
    original_items = tuple(item for item in result.items if item.label != "AMBIGUOUS")
    ambiguous_items = tuple(AutomaticItem(
        case_id, candidate_id, "Action",
        evaluation_item_id(case_id, candidate_id, "semantic-action", "ambiguous", str(i)),
        "AMBIGUOUS", {"review_triggers": [item["trigger"]], **item}, {},
        "A plausible mapping was not accepted automatically.",
    ) for i, item in enumerate(ambiguous))
    review_flags = tuple(sorted(set(result.review_flags) |
                                {str(item["trigger"]) for item in ambiguous}))
    return replace(result, generated_activity_groups=restored_groups,
                   ambiguous_mappings=tuple(ambiguous),
                   items=original_items + ambiguous_items, review_flags=review_flags)
