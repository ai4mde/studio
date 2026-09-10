from __future__ import annotations

# Responsibility:
# - extract lightweight business-process keyword hints from ProcessText
# - provide soft symbolic guidance for sketch/topology planning
#
# Must NOT:
# - generate graphs directly
# - become a hard rule engine
# - replace planner reasoning

import re
from typing import Any, Dict, List


KeywordHints = Dict[str, Any]

STRONG_LOOP_PHRASES = [
    "again",
    "retry",
    "retries",
    "repeat",
    "repeats",
    "until",
    "keep trying",
    "repeatedly",
    "return to",
    "go back",
]

RETRY_SEMANTIC_PHRASES = [
    "retry",
    "retries",
    "again",
    "resubmit",
    "resubmits",
    "re-submit",
    "re-submits",
    "correct",
    "corrects",
    "fix",
    "fixes",
    "update",
    "updates",
    "modify",
    "modifies",
    "provide missing documents",
    "provide additional information",
]

EXPLICIT_PARALLEL_PHRASES = [
    "simultaneously",
    "in parallel",
    "concurrently",
    "at the same time",
    "independently",
    "after both",
    "once both",
    "when both",
    "all branches",
]

_EXECUTABLE_ACTIVITY_STEMS = (
    "analy",
    "assembl",
    "back-order",
    "calculat",
    "check",
    "configur",
    "deliver",
    "do",
    "enable",
    "execut",
    "fetch",
    "gather",
    "hand",
    "inspect",
    "order",
    "prepar",
    "process",
    "provision",
    "readi",
    "record",
    "distribut",
    "repair",
    "repeat",
    "review",
    "reserv",
    "sign",
    "start",
    "test",
    "validat",
)

_SYNCHRONIZATION_STATES = ("ready", "complete", "completed", "finish", "finished", "done", "available")


def _normalize_process_text(process_text: str) -> str:
    return " ".join(process_text.lower().split())


def _contains_any(text: str, phrases: List[str]) -> List[str]:
    matches: List[str] = []
    for phrase in phrases:
        pattern = r"\b" + re.escape(phrase) + r"\b"
        if re.search(pattern, text):
            matches.append(phrase)
    return matches


def _has_executable_activity(clause: str) -> bool:
    words = re.findall(r"[a-z][a-z-]*", clause.lower())
    return any(word.startswith(stem) for word in words for stem in _EXECUTABLE_ACTIVITY_STEMS)


def _count_executable_clauses(text: str) -> int:
    clauses = re.split(r"[.;]|,\s*(?:and\s+)?|\bwhereas\b", text.lower())
    return sum(1 for clause in clauses if _has_executable_activity(clause))


def _has_temporal_marker_concurrency(text: str, marker_pattern: str) -> bool:
    for match in re.finditer(marker_pattern, text):
        left = text[max(0, match.start() - 300) : match.start()]
        right = text[match.end() : match.end() + 300]
        left_sentences = [sentence for sentence in re.split(r"[.!?]", left) if sentence.strip()]
        left_context = left_sentences[-1] if left_sentences else ""
        right_context = re.split(r"[.!?]", right)[0]
        if _has_executable_activity(left_context) and _has_executable_activity(right_context):
            return True
    return False


def _has_in_the_meantime_concurrency(text: str) -> bool:
    return _has_temporal_marker_concurrency(text, r"\bin the meantime\b")


def _has_meanwhile_concurrency(text: str) -> bool:
    return _has_temporal_marker_concurrency(text, r"\bmeanwhile\b")


def _has_bare_meantime_concurrency(text: str) -> bool:
    for match in re.finditer(r"\b(?:and\s+)?meantime\b", text):
        left = text[max(0, match.start() - 300) : match.start()]
        right = text[match.end() : match.end() + 500]
        left_sentences = [sentence for sentence in re.split(r"[.!?]", left) if sentence.strip()]
        left_context = left_sentences[-1] if left_sentences else ""
        right_sentences = [sentence for sentence in re.split(r"[.!?]", right) if sentence.strip()]
        right_activity = right_sentences[0] if right_sentences else ""
        later_context = ".".join(right_sentences[1:3])
        has_shared_continuation = bool(
            re.search(
                r"\b(?:afterwards|afterward|after|once|when|then)\b",
                later_context,
            )
        )
        if (
            _has_executable_activity(left_context)
            and _has_executable_activity(right_activity)
            and has_shared_continuation
        ):
            return True
    return False


def _has_while_clause_concurrency(text: str) -> bool:
    for match in re.finditer(r"\bwhile\s+([^,.;]+),\s*([^.;]+)", text):
        if _has_executable_activity(match.group(1)) and _has_executable_activity(match.group(2)):
            return True
    return False


def _has_arbitrary_order_concurrency(text: str) -> bool:
    activity_group = re.search(
        r"\b(?:two|three|multiple|several|\d+)\s+(?:named\s+)?(?:activities|tasks|operations|checks|repairs)\b"
        r"[^.]{0,120}\b(?:executed|performed|carried out|completed)\b[^.]{0,80}\b(?:an?\s+)?arbitrary order\b",
        text,
    )
    if activity_group is None:
        return False
    following_text = text[activity_group.end() : activity_group.end() + 500]
    names_multiple_activities = (
        ("first activity" in following_text and "second activity" in following_text)
        or _count_executable_clauses(following_text) >= 2
    )
    has_shared_continuation = bool(
        re.search(r"\b(?:after|once|when)\b[^.]{0,100}\b(?:activities|tasks|operations|checks|repairs|both|all)\b", following_text)
    )
    return names_multiple_activities and has_shared_continuation


def _has_multi_output_synchronization(text: str) -> bool:
    for match in re.finditer(r"\b(?:once|when|after)\s+([^.;]{0,180}),\s*([^.;]+)", text):
        synchronized_items = match.group(1)
        if synchronized_items.count(",") < 2 or " and " not in synchronized_items:
            continue
        if not any(re.search(rf"\b{state}\b", synchronized_items) for state in _SYNCHRONIZATION_STATES):
            continue
        preceding_text = text[max(0, match.start() - 500) : match.start()]
        if _count_executable_clauses(preceding_text) >= 2 and _has_executable_activity(match.group(2)):
            return True
    return False


def extract_parallel_evidence(process_text: str) -> List[str]:
    """Return conservative source signals that can support a proposed parallel block."""
    text = _normalize_process_text(process_text)
    evidence = _contains_any(text, EXPLICIT_PARALLEL_PHRASES)
    compound_checks = (
        ("in_the_meantime_with_independent_activities", _has_in_the_meantime_concurrency),
        ("meanwhile_with_independent_activities", _has_meanwhile_concurrency),
        ("bare_meantime_with_independent_activities_and_shared_continuation", _has_bare_meantime_concurrency),
        ("while_with_independent_activities", _has_while_clause_concurrency),
        ("multiple_activities_in_arbitrary_order", _has_arbitrary_order_concurrency),
        ("multiple_outputs_synchronized_before_continuation", _has_multi_output_synchronization),
    )
    for label, detector in compound_checks:
        if detector(text) and label not in evidence:
            evidence.append(label)
    return evidence


def _contains_disjunction_decision_evidence(text: str) -> bool:
    if " or " not in f" {text} ":
        return False

    words = re.findall(r"[a-z0-9]+", text)
    decision_stems = ("approv", "reject", "confirm", "accept", "declin", "deny")
    for word in words:
        if any(word.startswith(stem) for stem in decision_stems):
            return True
        if word.startswith("confirme"):
            return True
    return False


def extract_keyword_hints(process_text: str) -> KeywordHints:
    text = _normalize_process_text(process_text)

    decision_terms = _contains_any(
        text,
        ["if", "otherwise", "else", "whether", "approved", "rejected", "yes", "no"],
    )
    if _contains_disjunction_decision_evidence(text):
        for term in ["or", "reject_or_confirm"]:
            if term not in decision_terms:
                decision_terms.append(term)
    loop_terms = _contains_any(text, STRONG_LOOP_PHRASES)
    retry_terms = _contains_any(text, RETRY_SEMANTIC_PHRASES)
    parallel_terms = extract_parallel_evidence(process_text)
    approval_terms = _contains_any(
        text,
        ["approve", "approved", "reject", "rejected", "accept", "decline"],
    )
    if _contains_disjunction_decision_evidence(text) and "reject_or_confirm" not in approval_terms:
        approval_terms.append("reject_or_confirm")
    exit_terms = _contains_any(
        text,
        ["otherwise", "else", "until", "if not", "on success", "on failure", "unless"],
    )

    hints: List[Dict[str, Any]] = []

    if decision_terms:
        hints.append(
            {
                "kind": "possible_decision",
                "confidence": "high" if {"if", "otherwise"} & set(decision_terms) else "medium",
                "evidence": decision_terms,
                "guidance": "Expect a control split with at least one alternative path.",
            }
        )
    if loop_terms:
        hints.append(
            {
                "kind": "possible_loop",
                "confidence": "high",
                "evidence": loop_terms,
                "guidance": "Consider a retry or repetition structure with a backward path and an exit path.",
            }
        )
    if parallel_terms:
        hints.append(
            {
                "kind": "possible_parallelism",
                "confidence": "medium",
                "evidence": parallel_terms,
                "guidance": "Parallel split/join may be appropriate if multiple activities proceed concurrently.",
            }
        )
    if retry_terms:
        hints.append(
            {
                "kind": "retry_semantics",
                "confidence": "high",
                "evidence": retry_terms,
                "guidance": "Retry or correction semantics may be present; only infer an explicit loop when repeated or backward-flow language is stated.",
            }
        )
    if approval_terms:
        hints.append(
            {
                "kind": "approval_flow",
                "confidence": "medium",
                "evidence": approval_terms,
                "guidance": "Approval/rejection semantics often imply labeled decision branches and a clear continuation or termination.",
            }
        )
    if exit_terms:
        hints.append(
            {
                "kind": "exit_condition",
                "confidence": "medium",
                "evidence": exit_terms,
                "guidance": "Expect an explicit exit path or reconnection target rather than an open-ended loop.",
            }
        )

    return {
        "process_text": process_text,
        "flags": {
            "possible_decision": bool(decision_terms),
            "possible_loop": bool(loop_terms),
            "possible_parallelism": bool(parallel_terms),
            "retry_semantics": bool(retry_terms),
            "approval_flow": bool(approval_terms),
            "exit_condition": bool(exit_terms),
        },
        "evidence": {
            "decision_terms": decision_terms,
            "loop_terms": loop_terms,
            "retry_terms": retry_terms,
            "parallel_terms": parallel_terms,
            "approval_terms": approval_terms,
            "exit_terms": exit_terms,
        },
        "hints": hints,
    }


__all__ = ["KeywordHints", "extract_keyword_hints", "extract_parallel_evidence"]
