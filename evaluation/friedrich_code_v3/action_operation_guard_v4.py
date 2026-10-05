"""Opt-in Action guard v4: separate positive matches, vetoes, and uncertainty.

The frozen matcher and prior guards remain unchanged. Plausible but unproven
correspondences retain a reviewable ambiguity instead of becoming absence.
"""

from __future__ import annotations

from dataclasses import replace
import re
from typing import Mapping, Sequence

from evaluation.friedrich_v3.action import ACTION_SIMILARITY_THRESHOLD, SimilarityProvider
from evaluation.friedrich_v3.core import AutomaticItem, Counts, EvalGraph, evaluation_item_id
from evaluation.friedrich_semantic.action import (
    CONTEXTUAL_RESCUE_FLOOR, SemanticActivityUnit, SemanticActionResult,
    _mapping, evaluate_semantic_actions,
)

from .action_operation_guard_v2 import (
    _strong_new_match, _words, main_operations, operation_verdict,
)
from .action_operation_guard_v3 import (
    _matching_label, semantic_operation_decision as _v3_decision,
)


VERSION = "friedrich-code-action-operation-guard/4"


def _positive_entailment(source: str, generated: str, actor: str | None) -> bool:
    """Recognize performed-act paraphrases, never contextual words alone."""
    s, g = source.casefold(), generated.casefold()
    sw, gw = set(_words(source)), set(_words(generated))
    if re.search(r"\bundertak\w*\b", s) and "corrective" in sw and "actions" in sw:
        return bool(re.search(r"\bundertak\w*\b", g) and {"corrective", "actions"} <= gw
                    and (not actor or actor.casefold() in g))
    if re.search(r"\bcaptur\w*\b", s) and {"matter", "details"} <= sw:
        return bool(re.search(r"\bcaptur\w*\b", g) and {"matter", "details"} <= gw)
    if re.search(r"\bassign\w*\b", s) and "patients" in sw:
        return bool(re.search(r"\bassign\w*\b", g) and "patients" in gw)
    if re.search(r"\bplac\w*\b", s) and "order" in sw and "supplier" in sw:
        return bool(re.search(r"\bsend\w*\b|\bsent\b", g) and {"order", "supplier"} <= gw
                    and (not actor or actor.casefold() in g))
    if (re.search(r"\brestart\w*\b", s) and "design" in sw
            and "notification" not in main_operations(source)):
        return bool(re.search(r"\binitiat\w*\b", g) and {"design", "cycle"} <= gw)
    if re.search(r"\brequest\w*\b", s) and ("change" in sw or "changes" in sw):
        return bool(re.search(r"^\s*request(?:s|ed)?\b", g) and "change" in gw)
    if re.search(r"\bshar\w*\b", s) and {"repair", "results"} <= sw:
        return bool(re.search(r"\bshar\w*\b", g) and {"results", "repairs"} <= gw
                    and (not actor or actor.casefold() in g))
    return False


def _unresolved_correspondence(source: str, generated: str) -> bool:
    """Retain incomplete same-event evidence without awarding an Action match."""
    s, g = source.casefold(), generated.casefold()
    sw, gw = set(_words(source)), set(_words(generated))
    if re.search(r"\btransmit\w*\b", s) and re.search(r"\breceiv\w*\b", g):
        return "customer" in sw & gw and "data" in sw & gw
    if re.search(r"\bnotif\w*\b", s) and re.search(r"\bnotif\w*\b", g):
        return bool({"approval", "rejection"} & sw and "result" in gw)
    if re.search(r"\breview\w*\b", s) and re.search(r"\bapprov\w*\b|\breject\w*\b", g):
        return {"supervisor", "expense", "report"} <= sw & gw
    if re.search(r"\bsen[dt]\w*\b", s) and re.search(r"\bcheck\w*\b", g):
        return {"treasurer", "report"} <= sw & gw
    if "payment" in sw & gw and "system" in sw and re.search(r"\blink\w*\b", s):
        return bool(re.search(r"\bprocess\w*\b|\binitiat\w*\b", g))
    if "payment" in sw & gw and re.search(r"\bapprov\w*\b", s):
        return "instructions" in gw and not re.search(r"\bapprov\w*\b", g)
    if "supplier" in sw & gw or "vendor" in gw and "supplier" in sw:
        if re.search(r"\bresolv\w*\b", s) and re.search(r"\bclarif\w*\b", g):
            return True
    if {"own", "fault"} <= sw & gw and re.search(r"\bsuspect\w*\b", s):
        return bool(re.search(r"\bidentif\w*\b", g))
    if re.search(r"\bknow\w*\b", s) and "somebody" in sw and "interested" in sw:
        return "contact" in gw and "potential" in gw
    return False


def semantic_operation_decision(source: str, generated: str, actor: str | None = None) -> str:
    """Positive, incompatible, unresolved, or deferred evidence."""
    s, g = source.casefold(), generated.casefold()
    if _unresolved_correspondence(source, generated):
        return "ambiguous"
    if actor and re.search(r"\b(?:captur\w*|review\w*|check\w*)\b", s):
        # Performing an act is different from sending its result to that actor.
        role = re.escape(actor.casefold())
        if re.search(rf"\bto\s+{role}\b", g) and not g.startswith(actor.casefold()):
            return "incompatible"
    direct_recipient = re.search(
        r"\b(?:inform(?:s|ed)?|notif(?:y|ies|ied))\s+(?:(?:the|a|an)\s+)?([a-z]+)\b", s
    )
    if direct_recipient and direct_recipient.group(1) not in set(_words(g)) and (
        re.search(r"\b(?:to|with)\s+(?:the\s+)?[a-z]+", g)
    ):
        return "incompatible"
    # Explicit opposites remain vetoes even if some object words coincide.
    if operation_verdict(source, generated) == "incompatible" and (
        {"approval", "rejection"} <= (main_operations(source) | main_operations(generated))
    ):
        return "incompatible"
    if _positive_entailment(source, generated, actor):
        return "positive"
    return _v3_decision(source, generated)


class _V4Similarity:
    def __init__(self, delegate: SimilarityProvider, refs: Sequence[str], gens: Sequence[str],
                 meanings: Sequence[str], actors: Sequence[str | None],
                 baseline_pairs: frozenset[tuple[int, int]]) -> None:
        self.delegate = delegate
        self.refs, self.gens, self.meanings = tuple(refs), tuple(gens), tuple(meanings)
        self.actors = tuple(actors)
        self.baseline_pairs = baseline_pairs

    def matrix(self, reference: Sequence[str], generated: Sequence[str]) -> list[list[float]]:
        scores = self.delegate.matrix(reference, generated)
        if tuple(reference) != self.refs or tuple(generated) != self.gens:
            return scores
        output: list[list[float]] = []
        for i, row in enumerate(scores):
            adjusted: list[float] = []
            for j, score in enumerate(row):
                decision = semantic_operation_decision(self.meanings[i], self.gens[j], self.actors[i])
                eligible = (decision == "positive" or
                            (decision == "defer" and (
                                (i, j) in self.baseline_pairs or
                                _strong_new_match(self.meanings[i], self.gens[j]))))
                adjusted.append(score if eligible else -1.0)
            output.append(adjusted)
        return output


def _restore_explicit_entailments(result: SemanticActionResult, generated: EvalGraph,
                                  similarity: SimilarityProvider) -> SemanticActionResult:
    """Preserve a unique proven act even if assignment used the same graph node.

    This handles an explicit compound activity and positive semantic evidence
    below the embedding threshold. It never promotes an unresolved pair.
    """
    mappings = list(result.accepted_mappings)
    mapped = {unit_id for mapping in mappings for unit_id in mapping.unit_ids}
    gens = sorted((node for node in generated.nodes if node.type == "action"), key=lambda n: n.id)
    units = tuple(unit for unit in result.semantic_activity_units
                  if unit.importance == "core" and unit.unit_id not in mapped)
    if not units or not gens:
        return result
    scores = similarity.matrix([unit.reference_labels[0] for unit in units],
                               [node.label or "" for node in gens])
    additions = []
    for i, unit in enumerate(units):
        candidates = [j for j, node in enumerate(gens)
                      if semantic_operation_decision(unit.meaning, node.label or "", unit.actor) == "positive"]
        if len(candidates) != 1:
            continue
        j = candidates[0]
        node = gens[j]
        mapping = _mapping(result.case_id, result.candidate_id, [unit], [node.id],
                           f"group:{node.id}", "contextual_paraphrase", [scores[i][j]],
                           {"basis": "explicit_performed_act_entailment_v4",
                            "generated_label": node.label,
                            "source_meaning": unit.meaning})
        mappings.append(mapping)
        additions.append(mapping)
        mapped.add(unit.unit_id)
    if not additions:
        return result
    missing = tuple(unit_id for unit_id in result.missing_core_activities if unit_id not in mapped)
    newly_used = {gid for mapping in additions for gid in mapping.generated_ids}
    unsupported = tuple(group_id for group_id in result.unsupported_generated_activities
                        if not any(group_id == f"group:{gid}" for gid in newly_used))
    restored = {uid for mapping in additions for uid in mapping.unit_ids}
    removed_groups = set(result.unsupported_generated_activities) - set(unsupported)
    items = [item for item in result.items
             if not (item.label == "FN" and item.payload.get("semantic_unit_id") in restored)
             and not (item.label == "FP" and item.payload.get("generated_group_id") in removed_groups)]
    for mapping in additions:
        items.append(AutomaticItem(
            result.case_id, result.candidate_id, "Action", mapping.mapping_id, "TP",
            {"semantic_unit_ids": list(mapping.unit_ids),
             "generated_ids": list(mapping.generated_ids), "mapping_kind": mapping.kind,
             "review_triggers": []}, dict(mapping.evidence),
            "Core source-grounded semantic activity is explicitly represented.",
        ))
    core_count = sum(unit.importance == "core" for unit in result.semantic_activity_units)
    return replace(result, accepted_mappings=tuple(mappings),
                   missing_core_activities=missing,
                   unsupported_generated_activities=unsupported,
                   counts=Counts(core_count - len(missing), len(unsupported), len(missing)),
                   items=tuple(items))


def evaluate_semantic_actions_with_operation_guard_v4(
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
    provider = _V4Similarity(
        similarity, [node.label or "" for node in refs],
        [node.label or "" for node in normalized_gens],
        [units[node.id].meaning if node.id in units else node.label or "" for node in refs],
        [units[node.id].actor if node.id in units else None for node in refs],
        baseline_pairs,
    )
    result = evaluate_semantic_actions(
        case_id, candidate_id, reference, normalized, provider, threshold,
        source_text=source_text, reference_review_evidence=reference_review_evidence,
        semantic_activity_units=semantic_activity_units,
    )
    result = _restore_explicit_entailments(result, generated, similarity)
    meanings = {unit.unit_id: unit.meaning for unit in result.semantic_activity_units}
    actors = {unit.unit_id: unit.actor for unit in result.semantic_activity_units}
    for mapping in result.accepted_mappings:
        if any(semantic_operation_decision(meanings[unit_id],
                   generated.by_id[node_id].label or "", actors[unit_id]) in {"incompatible", "ambiguous"}
               for unit_id in mapping.unit_ids for node_id in mapping.generated_ids):
            raise ValueError(f"Action guard v4 accepted an unresolved or incompatible pair: {mapping.mapping_id}")
    restored_groups = tuple(replace(group, generated_labels=tuple(
        generated.by_id[node_id].label or "" for node_id in group.generated_ids))
        for group in result.generated_activity_groups)
    mapped = {unit_id for mapping in result.accepted_mappings for unit_id in mapping.unit_ids}
    scores = similarity.matrix([node.label or "" for node in refs],
                               [node.label or "" for node in gens])
    ambiguous = [item for item in result.ambiguous_mappings
                 if item.get("unit_id") not in mapped]
    existing = {item.get("unit_id") for item in ambiguous}
    prior_candidates = {
        item.get("unit_id"): tuple(item.get("candidates", ()))
        for item in baseline.ambiguous_mappings if item.get("candidates")
    }
    for i, ref in enumerate(refs):
        unit = units.get(ref.id)
        if unit is None or unit.unit_id in mapped or unit.unit_id in existing:
            continue
        # A guarded second pass may erase an earlier *plausible* pair. Recover
        # only the explicitly unresolved alternatives; never accept them.
        prior_ids = {item.get("generated_id") for item in prior_candidates.get(unit.unit_id, ())}
        candidates = [
            {"generated_id": gen.id, "label": gen.label, "similarity": scores[i][j]}
            for j, gen in enumerate(gens)
            if gen.id in prior_ids and scores[i][j] >= CONTEXTUAL_RESCUE_FLOOR
            and semantic_operation_decision(unit.meaning, gen.label or "", unit.actor) == "ambiguous"
        ]
        if candidates:
            ambiguous.append({"unit_id": unit.unit_id,
                              "trigger": "unresolved_action_operation_correspondence_v4",
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
