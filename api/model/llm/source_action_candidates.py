from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, Iterable, List, TypedDict


class SourceSpan(TypedDict):
    start: int
    end: int
    text: str


class SourceActionCandidate(TypedDict):
    source_action_id: str
    source_span: SourceSpan


# This vocabulary is deliberately limited to common, externally observable
# business operations. It is a candidate harvester, not a general parser.
_ACTION_VERBS = {
    "accept",
    "accepts",
    "add",
    "adds",
    "approve",
    "approves",
    "archive",
    "archives",
    "assign",
    "assigns",
    "cancel",
    "cancels",
    "check",
    "checks",
    "close",
    "closes",
    "collect",
    "collects",
    "complete",
    "completes",
    "create",
    "creates",
    "deliver",
    "delivers",
    "determine",
    "determines",
    "examine",
    "examines",
    "fill",
    "fills",
    "finalize",
    "finalizes",
    "formulate",
    "formulates",
    "generate",
    "generates",
    "hand",
    "hands",
    "inform",
    "informs",
    "issue",
    "issues",
    "notify",
    "notifies",
    "prepare",
    "prepares",
    "print",
    "prints",
    "produce",
    "produces",
    "provide",
    "provides",
    "receive",
    "receives",
    "record",
    "records",
    "register",
    "registers",
    "reject",
    "rejects",
    "request",
    "requests",
    "retrieve",
    "retrieves",
    "review",
    "reviews",
    "route",
    "routes",
    "schedule",
    "schedules",
    "send",
    "sends",
    "store",
    "stores",
    "transcribe",
    "transcribes",
    "transmit",
    "transmits",
    "type",
    "types",
    "update",
    "updates",
    "validate",
    "validates",
    "verify",
    "verifies",
}

_VERB_PATTERN = "|".join(sorted(_ACTION_VERBS, key=len, reverse=True))
_ACTION_AT_START = re.compile(
    rf"^(?:(?:then|subsequently|finally)\s+)?(?P<verb>{_VERB_PATTERN})\b",
    re.IGNORECASE,
)
_ACTION_WITH_SUBJECT = re.compile(
    rf"\b(?P<verb>{_VERB_PATTERN})\b",
    re.IGNORECASE,
)
_PASSIVE_ACTION = re.compile(
    r"^(?:the|a|an)\s+"
    r"(?P<object>[A-Za-z][A-Za-z'-]*(?:\s+[A-Za-z][A-Za-z'-]*){0,3})\s+"
    r"(?:is|are|was|were)\s+(?:received|archived|stored|reviewed)$",
    re.IGNORECASE,
)
_SENTENCE = re.compile(r"[^.!?]+(?:[.!?]+|$)", re.MULTILINE)
_CLAUSE_SEPARATOR = re.compile(r"\s*(?:,|;|\band\b)\s*", re.IGNORECASE)
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")

_CONDITION_PREFIXES = (
    "after ",
    "as long as ",
    "as soon as ",
    "before ",
    "during ",
    "if ",
    "once ",
    "unless ",
    "until ",
    "when ",
    "whenever ",
    "while ",
)
_MAIN_CLAUSE_PREFIXES = ("after ", "once ")
_COREFERENCE_WORDS = {
    "he",
    "her",
    "hers",
    "him",
    "his",
    "it",
    "its",
    "previous",
    "she",
    "that",
    "their",
    "theirs",
    "them",
    "these",
    "they",
    "this",
    "those",
}
_NON_ACTOR_SUBJECTS = {"he", "it", "she", "that", "they", "this", "we", "you"}
_EXPLICIT_OBJECT_OPENERS = {"a", "all", "an", "each", "every", "new", "one", "the", "two"}
_LATER_AUXILIARY = re.compile(r"\b(?:are|has|have|is|may|was|were|will)\b", re.IGNORECASE)


def _trimmed_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and (text[end - 1].isspace() or text[end - 1] in ".!?;,:"):
        end -= 1
    return start, end


def _contains_coreference(text: str) -> bool:
    return bool(_COREFERENCE_WORDS.intersection(word.lower() for word in _WORD.findall(text)))


def _has_explicit_subject(prefix: str) -> bool:
    words = [word.lower() for word in _WORD.findall(prefix)]
    if not words or words[-1] in _NON_ACTOR_SUBJECTS:
        return False
    return not any(word in {"may", "might", "could", "not", "never"} for word in words)


def _candidate_action_span(
    process_text: str,
    *,
    clause_start: int,
    clause_end: int,
    inherited_subject: bool,
) -> tuple[int, int] | None:
    start, end = _trimmed_span(process_text, clause_start, clause_end)
    if start >= end:
        return None
    clause = process_text[start:end]
    if clause.lower().startswith(_CONDITION_PREFIXES):
        return None

    passive_match = _PASSIVE_ACTION.fullmatch(clause)
    if passive_match is not None and not _contains_coreference(clause):
        return start + passive_match.start("object"), end

    leading_match = _ACTION_AT_START.match(clause)
    if leading_match is not None:
        if not inherited_subject:
            return None
        action_start = start + leading_match.start("verb")
    else:
        action_match = _ACTION_WITH_SUBJECT.search(clause)
        if action_match is None or not _has_explicit_subject(clause[: action_match.start("verb")]):
            return None
        action_start = start + action_match.start("verb")

    action_text = process_text[action_start:end]
    if _contains_coreference(action_text):
        return None
    action_words = _WORD.findall(action_text)
    if len(action_words) < 3 or action_words[1].lower() not in _EXPLICIT_OBJECT_OPENERS:
        return None
    verb_end = action_start + len(action_words[0])
    if _LATER_AUXILIARY.search(process_text[verb_end:end]):
        return None
    return action_start, end


def _establishes_explicit_subject(process_text: str, start: int, end: int) -> bool:
    start, end = _trimmed_span(process_text, start, end)
    if start >= end:
        return False
    clause = process_text[start:end]
    action_match = _ACTION_WITH_SUBJECT.search(clause)
    return bool(
        action_match is not None
        and action_match.start("verb") > 0
        and _has_explicit_subject(clause[: action_match.start("verb")])
    )


def harvest_source_action_candidates(process_text: str) -> List[SourceActionCandidate]:
    """Return a stable, precision-first inventory of explicit business actions."""

    spans: List[tuple[int, int]] = []
    for sentence_match in _SENTENCE.finditer(process_text):
        sentence_start, sentence_end = sentence_match.span()
        sentence_text = process_text[sentence_start:sentence_end].lstrip().lower()
        if sentence_text.startswith(_CONDITION_PREFIXES):
            if not sentence_text.startswith(_MAIN_CLAUSE_PREFIXES):
                continue
            prefix_end = process_text.find(",", sentence_start, sentence_end)
            if prefix_end < 0:
                continue
            sentence_start = prefix_end + 1
        clause_start = sentence_start
        inherited_subject = False
        for separator in _CLAUSE_SEPARATOR.finditer(process_text, sentence_start, sentence_end):
            candidate_span = _candidate_action_span(
                process_text,
                clause_start=clause_start,
                clause_end=separator.start(),
                inherited_subject=inherited_subject,
            )
            if candidate_span is not None:
                spans.append(candidate_span)
                inherited_subject = True
            elif _establishes_explicit_subject(process_text, clause_start, separator.start()):
                inherited_subject = True
            clause_start = separator.end()
        candidate_span = _candidate_action_span(
            process_text,
            clause_start=clause_start,
            clause_end=sentence_end,
            inherited_subject=inherited_subject,
        )
        if candidate_span is not None:
            spans.append(candidate_span)

    ordered_spans = sorted(set(spans))
    return [
        {
            "source_action_id": f"SA{index}",
            "source_span": {
                "start": start,
                "end": end,
                "text": process_text[start:end],
            },
        }
        for index, (start, end) in enumerate(ordered_spans, start=1)
    ]


def _semantic_steps(semantic_plan: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for root_action in semantic_plan.get("root_actions", []):
        if isinstance(root_action, dict):
            for step in root_action.get("actions", []):
                if isinstance(step, dict):
                    yield step
    for branch_plan in semantic_plan.get("branch_plans", []):
        if isinstance(branch_plan, dict):
            for step in branch_plan.get("steps", []):
                if isinstance(step, dict):
                    yield step


def calculate_source_action_coverage(
    candidates: List[SourceActionCandidate],
    semantic_plan: Dict[str, Any],
) -> Dict[str, Any]:
    """Report ID coverage without validating or changing the semantic plan."""

    candidate_ids = [candidate["source_action_id"] for candidate in candidates]
    candidate_id_set = set(candidate_ids)
    references: List[str] = []
    for step in _semantic_steps(semantic_plan):
        raw_ids = step.get("source_action_ids", [])
        if isinstance(raw_ids, list):
            references.extend(item.strip() for item in raw_ids if isinstance(item, str) and item.strip())

    reference_counts = Counter(references)
    covered_ids = [source_id for source_id in candidate_ids if reference_counts[source_id] > 0]
    uncovered_ids = [source_id for source_id in candidate_ids if reference_counts[source_id] == 0]
    unknown_ids = sorted(source_id for source_id in reference_counts if source_id not in candidate_id_set)
    duplicate_coverage = [
        {"source_action_id": source_id, "reference_count": reference_counts[source_id]}
        for source_id in candidate_ids
        if reference_counts[source_id] > 1
    ]
    coverage_ratio = len(covered_ids) / len(candidate_ids) if candidate_ids else 1.0
    warnings: List[str] = []
    if uncovered_ids:
        warnings.append(f"Uncovered source action candidates: {', '.join(uncovered_ids)}")
    if unknown_ids:
        warnings.append(f"Unknown source action IDs referenced by semantic plan: {', '.join(unknown_ids)}")
    return {
        "candidate_source_action_ids": candidate_ids,
        "covered_source_action_ids": covered_ids,
        "uncovered_source_action_ids": uncovered_ids,
        "unknown_source_action_ids": unknown_ids,
        "duplicate_coverage": duplicate_coverage,
        "coverage_ratio": coverage_ratio,
        "warnings": warnings,
    }


__all__ = [
    "SourceActionCandidate",
    "SourceSpan",
    "calculate_source_action_coverage",
    "harvest_source_action_candidates",
]
