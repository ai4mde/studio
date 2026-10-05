"""Versioned, Action-only semantic compatibility guard.

The frozen V3.2 entry point and the earlier v1 guard are deliberately unchanged.
This guard limits only clearly incompatible Action pairs before assignment; it
does not award matches, alter the similarity model, or change another dimension.
"""

from __future__ import annotations

from dataclasses import replace
import re
from typing import Literal, Mapping, Sequence

from evaluation.friedrich_v3.action import ACTION_SIMILARITY_THRESHOLD, SimilarityProvider
from evaluation.friedrich_v3.core import EvalGraph
from evaluation.friedrich_semantic.action import (
    SemanticActivityUnit, SemanticActionResult, evaluate_semantic_actions,
)


VERSION = "friedrich-code-action-operation-guard/2"
Verdict = Literal["compatible", "incompatible", "perspective_review", "semantic_review"]

# These are performed verbs, including inflections, rather than arbitrary
# operation-like words anywhere in a label. The first performed verb of each
# clause is its head; later modifiers such as "approved invoice" are ignored.
_VERBS: Mapping[str, str] = {
    "approve": "approval", "approves": "approval", "approved": "approval",
    "authorize": "approval", "authorizes": "approval", "authorized": "approval",
    "reject": "rejection", "rejects": "rejection", "rejected": "rejection",
    "deny": "rejection", "denies": "rejection", "denied": "rejection",
    "decline": "rejection", "declines": "rejection", "declined": "rejection",
    "receive": "reception", "receives": "reception", "received": "reception",
    "review": "inspection", "reviews": "inspection", "reviewed": "inspection",
    "examine": "inspection", "examines": "inspection", "examined": "inspection",
    "inspect": "inspection", "inspects": "inspection", "inspected": "inspection",
    "check": "inspection", "checks": "inspection", "checked": "inspection",
    "evaluate": "assessment", "evaluates": "assessment", "evaluated": "assessment",
    "assess": "assessment", "assesses": "assessment", "assessed": "assessment",
    "notify": "notification", "notifies": "notification", "notified": "notification",
    "inform": "notification", "informs": "notification", "informed": "notification",
    "send": "transmission", "sends": "transmission", "sent": "transmission",
    "transmit": "transmission", "transmits": "transmission", "transmitted": "transmission",
    "dispatch": "transmission", "dispatches": "transmission", "dispatched": "transmission",
    "forward": "transmission", "forwards": "transmission", "forwarded": "transmission",
    "return": "return", "returns": "return", "returned": "return",
    "communicate": "notification", "communicates": "notification", "communicated": "notification",
    "process": "processing", "processes": "processing", "processed": "processing",
    "create": "creation", "creates": "creation", "created": "creation",
    "generate": "creation", "generates": "creation", "generated": "creation",
    "produce": "creation", "produces": "creation", "produced": "creation",
    "identify": "identification", "identifies": "identification", "identified": "identification",
    "correct": "modification", "corrects": "modification", "corrected": "modification",
    "edit": "modification", "edits": "modification", "edited": "modification",
    "revise": "modification", "revises": "modification", "revised": "modification",
    "submit": "submission", "submits": "submission", "submitted": "submission",
    "resubmit": "submission", "resubmits": "submission", "resubmitted": "submission",
    "initiate": "initiation", "initiates": "initiation", "initiated": "initiation",
    "combine": "combination", "combines": "combination", "combined": "combination",
    "close": "completion", "closes": "completion", "closed": "completion",
    "complete": "completion", "completes": "completion", "completed": "completion",
    "terminate": "completion", "terminates": "completion", "terminated": "completion",
    "schedule": "scheduling", "schedules": "scheduling", "scheduled": "scheduling",
}
_NOMINAL_HEADS: Mapping[str, str] = {
    "approval": "approval", "authorization": "approval", "rejection": "rejection",
    "receipt": "reception", "reception": "reception",
}
_AUXILIARIES = frozenset({"is", "are", "was", "were", "be", "been", "being", "has", "have", "had"})
_ARTICLES = frozenset({"a", "an", "the"})
_MESSAGE_OBJECTS = frozenset({"notice", "notification", "message", "report", "comment", "response"})
_OBJECTS: Mapping[str, str] = {
    "report": "report", "reports": "report", "comment": "comment", "comments": "comment",
    "agreement": "agreement", "agreements": "agreement",
    "request": "request", "requests": "request",
    "contract": "contract", "contracts": "contract",
    "invoice": "invoice", "invoices": "invoice",
    "bill": "invoice", "billing": "invoice",
    "form": "form", "forms": "form",
    "claim": "claim", "claims": "claim",
    "notice": "notice", "notices": "notice", "notification": "notice",
    "document": "document", "documents": "document",
    "order": "order", "orders": "order",
    "design": "design", "designs": "design", "plan": "plan", "plans": "plan",
    "schedule": "schedule", "schedules": "schedule",
}
_RECIPIENT_END = frozenset({
    "after", "before", "when", "where", "who", "which", "that", "with", "for", "from", "if",
})
_ROLE_CHANGING_TERMS = frozenset({"service", "management", "team", "office", "unit"})
_ACTOR_ROLES = frozenset({"supervisor", "treasurer", "customer", "employee", "accounting", "supplier", "operator", "cis", "department"})


def _words(label: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z]+", label.casefold()))


def main_operations(label: str) -> frozenset[str]:
    """Find performed clause heads, avoiding nouns and result adjectives."""
    words = _words(label)
    heads: set[str] = set()
    for _clause_start, clause in _clauses(words):
        for index, word in enumerate(clause):
            if word not in _VERBS:
                continue
            # "A final schedule of dates is sent" and "the process is
            # complete" use operation-like nouns as subjects. A later
            # subordinate auxiliary must not hide an earlier real predicate
            # ("informs the intaker that a copy was received").
            if word in {"schedule", "process"} and index + 1 < len(clause) and clause[index + 1] in {"of", *_AUXILIARIES}:
                continue
            family = "return" if _VERBS[word] == "transmission" and "back" in clause else _VERBS[word]
            heads.add(family)
            break
    if heads:
        return frozenset(heads)
    if re.search(r"\b(?:is|are|was|were) considered (?:to be )?complete\b", label.casefold()):
        return frozenset({"completion"})
    # A nominal activity such as "supervisor approval of the request" may
    # lack a finite verb. Do not treat a modifier such as "approved copy" as
    # a performed approval action.
    for index, word in enumerate(words):
        if word in _NOMINAL_HEADS and (index + 1 == len(words) or words[index + 1] == "of"):
            return frozenset({_NOMINAL_HEADS[word]})
    return frozenset()


def _clauses(words: Sequence[str]) -> list[tuple[int, tuple[str, ...]]]:
    result: list[tuple[int, tuple[str, ...]]] = []
    start = 0
    for index, word in enumerate(words):
        if word == "and":
            result.append((start, tuple(words[start:index])))
            start = index + 1
    result.append((start, tuple(words[start:])))
    return result


def _objects(label: str) -> frozenset[str]:
    words = _words(label)
    return frozenset(
        _OBJECTS[word] for index, word in enumerate(words) if word in _OBJECTS
        and not (word == "schedule" and "scheduling" in main_operations(label) and index == 0)
    )


def _direct_objects_by_operation(label: str) -> dict[str, frozenset[str]]:
    """Distinguish creating a design from creating a plan *for* a design."""
    found: dict[str, set[str]] = {}
    for _start, clause in _clauses(_words(label)):
        for index, word in enumerate(clause):
            if word not in _VERBS or (
                word in {"schedule", "process"} and index + 1 < len(clause)
                and clause[index + 1] in {"of", *_AUXILIARIES}
            ):
                continue
            family = "return" if _VERBS[word] == "transmission" and "back" in clause else _VERBS[word]
            direct: set[str] = set()
            for token in clause[index + 1:]:
                if token in {"to", "for", "from", "with", "using", "after", "before", "by", "of", "in", "on"}:
                    break
                if token in _OBJECTS:
                    direct.add(_OBJECTS[token])
            found.setdefault(family, set()).update(direct)
            break
    return {family: frozenset(objects) for family, objects in found.items()}


def _recipients(label: str) -> tuple[frozenset[str], ...]:
    words = _words(label)
    destinations: list[frozenset[str]] = []
    for position, word in enumerate(words):
        if word != "to":
            continue
        index = position + 1
        while index < len(words) and words[index] in _ARTICLES:
            index += 1
        result: list[str] = []
        while index < len(words) and words[index] not in _RECIPIENT_END:
            if words[index] == "and":
                if index + 1 < len(words) and words[index + 1] in _VERBS:
                    break
                if result:
                    destinations.append(frozenset(result) - {"department"})
                result = []
            else:
                result.append(words[index])
            index += 1
        if result:
            destinations.append(frozenset(result) - {"department"})
    return tuple(destinations)


def _receiver_subject(label: str) -> frozenset[str]:
    words = _words(label)
    for index, word in enumerate(words):
        if _VERBS.get(word) == "reception":
            subject = words[:index]
            return frozenset(word for word in subject if word not in _ARTICLES and word not in _AUXILIARIES)
    return frozenset()


def _different_explicit_recipients(source: str, generated: str, src_ops: frozenset[str], gen_ops: frozenset[str]) -> bool:
    source_recipients = ((_receiver_subject(source),) if "reception" in src_ops
                         else _recipients(source))
    generated_recipients = ((_receiver_subject(generated),) if "reception" in gen_ops
                            else _recipients(generated))
    source_recipients = tuple(value for value in source_recipients if value)
    generated_recipients = tuple(value for value in generated_recipients if value)
    if not source_recipients or not generated_recipients:
        return False
    for source_recipient in source_recipients:
        for generated_recipient in generated_recipients:
            if source_recipient == generated_recipient:
                return False
            differing = source_recipient ^ generated_recipient
            if not differing & _ROLE_CHANGING_TERMS and (
                source_recipient <= generated_recipient or generated_recipient <= source_recipient
            ):
                return False
    return True


def _explicit_actor(label: str) -> frozenset[str]:
    words = _words(label)
    for index, word in enumerate(words):
        if word in _VERBS and not (
            word in {"schedule", "process"} and index + 1 < len(words)
            and words[index + 1] in {"of", *_AUXILIARIES}
        ):
            return frozenset(words[:index]) & _ACTOR_ROLES
    return frozenset()


def _revised_creation_paraphrase(source: str, generated: str,
                                 source_ops: frozenset[str], generated_ops: frozenset[str]) -> bool:
    """Creating a revised artifact may be expressed as revising that artifact."""
    if "creation" not in source_ops or "modification" not in generated_ops:
        return False
    if not set(_words(source)) & {"revised", "updated"}:
        return False
    source_object = _direct_objects_by_operation(source).get("creation", frozenset())
    generated_object = _direct_objects_by_operation(generated).get("modification", frozenset())
    return bool(source_object & generated_object)


def _strong_new_match(source: str, generated: str) -> bool:
    """Require positive evidence before an assignment newly freed by a veto."""
    source_ops, generated_ops = main_operations(source), main_operations(generated)
    if not source_ops or not generated_ops or operation_verdict(source, generated) == "incompatible":
        return False
    if (not source_ops & generated_ops
        and operation_verdict(source, generated) != "perspective_review"
        and not _revised_creation_paraphrase(source, generated, source_ops, generated_ops)):
        return False
    source_objects, generated_objects = _objects(source), _objects(generated)
    if source_objects and not source_objects & generated_objects:
        return False
    source_actor, generated_actor = _explicit_actor(source), _explicit_actor(generated)
    if source_actor and generated_actor and source_actor.isdisjoint(generated_actor):
        return False
    source_recipient = _recipients(source)
    if source_recipient and not _recipients(generated):
        return False
    return True


def operation_verdict(source_meaning: str, generated_label: str) -> Verdict:
    """Veto only explicit operation or argument conflicts; defer unknowns."""
    source_ops = main_operations(source_meaning)
    generated_ops = main_operations(generated_label)
    if not source_ops or not generated_ops:
        return "compatible"
    if {"approval", "rejection"} <= (source_ops | generated_ops) and not source_ops & generated_ops:
        return "incompatible"
    source_objects, generated_objects = _objects(source_meaning), _objects(generated_label)
    if source_objects and generated_objects and source_objects.isdisjoint(generated_objects):
        return "incompatible"
    if _different_explicit_recipients(source_meaning, generated_label, source_ops, generated_ops):
        return "incompatible"
    if source_ops & generated_ops:
        source_direct = _direct_objects_by_operation(source_meaning)
        generated_direct = _direct_objects_by_operation(generated_label)
        common = source_ops & generated_ops
        if common and all(
            source_direct.get(family) and generated_direct.get(family)
            and source_direct[family].isdisjoint(generated_direct[family])
            for family in common
        ):
            return "incompatible"
        return "compatible"
    source_words, generated_words = set(_words(source_meaning)), set(_words(generated_label))
    if source_ops == frozenset({"rejection"}) and generated_ops == frozenset({"notification"}) and (
        generated_words & {"reject", "rejects", "rejected", "denied", "declined"}
    ):
        return "semantic_review"
    if source_ops == frozenset({"completion"}) and generated_ops == frozenset({"transmission"}) and (
        generated_words & {"complete", "completed"}
    ):
        return "semantic_review"
    if _revised_creation_paraphrase(source_meaning, generated_label, source_ops, generated_ops):
        return "compatible"
    if (source_ops == frozenset({"submission"}) and generated_ops == frozenset({"reception"})) or (
        generated_ops == frozenset({"submission"}) and source_ops == frozenset({"reception"})
    ):
        if source_objects & generated_objects:
            return "perspective_review"
    if source_ops == frozenset({"transmission"}) and generated_ops == frozenset({"notification"}):
        return "compatible" if source_words & _MESSAGE_OBJECTS else "incompatible"
    if generated_ops == frozenset({"transmission"}) and source_ops == frozenset({"notification"}):
        return "compatible" if generated_words & _MESSAGE_OBJECTS else "incompatible"
    if ("reception" in source_ops and generated_ops & {"notification", "transmission"}) or (
        "reception" in generated_ops and source_ops & {"notification", "transmission"}
    ):
        if (source_words | generated_words) & _MESSAGE_OBJECTS:
            return "perspective_review"
    return "incompatible"


class _GuardedSimilarity:
    def __init__(self, delegate: SimilarityProvider, references: Sequence[str], generated: Sequence[str],
                 meanings: Sequence[str], baseline_pairs: frozenset[tuple[int, int]]) -> None:
        self.delegate = delegate
        self.references = tuple(references)
        self.generated = tuple(generated)
        self.meanings = tuple(meanings)
        self.baseline_pairs = baseline_pairs

    def matrix(self, reference: Sequence[str], generated: Sequence[str]) -> list[list[float]]:
        scores = self.delegate.matrix(reference, generated)
        if tuple(reference) != self.references or tuple(generated) != self.generated:
            return scores
        return [
            [score if (operation_verdict(meaning, label) != "incompatible"
                       and ((i, j) in self.baseline_pairs or _strong_new_match(meaning, label))) else -1.0
             for j, (score, label) in enumerate(zip(row, self.generated))]
            for i, (meaning, row) in enumerate(zip(self.meanings, scores))
        ]


def evaluate_semantic_actions_with_operation_guard_v2(
    case_id: str, candidate_id: str, reference: EvalGraph, generated: EvalGraph,
    similarity: SimilarityProvider, threshold: float = ACTION_SIMILARITY_THRESHOLD, *,
    source_text: str, reference_review_evidence: Sequence[Mapping[str, object]] = (),
    semantic_activity_units: Sequence[SemanticActivityUnit] | None = None,
) -> SemanticActionResult:
    """Run a new Action-only matcher, keeping frozen V3.2 and v1 unchanged."""
    refs = sorted((node for node in reference.nodes if node.type == "action"), key=lambda node: node.id)
    gens = sorted((node for node in generated.nodes if node.type == "action"), key=lambda node: node.id)
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
        (ref_index[reference_id], gen_index[generated_id])
        for mapping in baseline.accepted_mappings
        for reference_id in mapping.reference_ids for generated_id in mapping.generated_ids
    )
    guarded = _GuardedSimilarity(
        similarity, [node.label or "" for node in refs], [node.label or "" for node in gens],
        [units[node.id].meaning if node.id in units else node.label or "" for node in refs],
        baseline_pairs,
    )
    result = evaluate_semantic_actions(
        case_id, candidate_id, reference, generated, guarded, threshold,
        source_text=source_text, reference_review_evidence=reference_review_evidence,
        semantic_activity_units=semantic_activity_units,
    )
    meanings = {unit.unit_id: unit.meaning for unit in result.semantic_activity_units}
    mappings = []
    extra_review_flags: set[str] = set()
    for mapping in result.accepted_mappings:
        verdicts = [operation_verdict(meanings[unit_id], generated.by_id[node_id].label or "")
                    for unit_id in mapping.unit_ids for node_id in mapping.generated_ids]
        if verdicts and all(verdict == "incompatible" for verdict in verdicts):
            raise ValueError(f"Action operation guard v2 bypassed: {mapping.mapping_id}")
        if "perspective_review" in verdicts:
            extra_review_flags.add("sender_receiver_perspective_requires_review")
            mapping = replace(mapping, review_triggers=tuple(sorted(set(mapping.review_triggers) | {
                "sender_receiver_perspective_requires_review",
            })))
        if "semantic_review" in verdicts:
            extra_review_flags.add("action_operation_entailment_requires_review")
            mapping = replace(mapping, review_triggers=tuple(sorted(set(mapping.review_triggers) | {
                "action_operation_entailment_requires_review",
            })))
        mappings.append(mapping)
    return replace(
        result, accepted_mappings=tuple(mappings),
        review_flags=tuple(sorted(set(result.review_flags) | extra_review_flags)),
    )
