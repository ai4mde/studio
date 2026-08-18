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

_WEAK_LOOP_CUE_PATTERNS = (
    ("again", r"\bagain\b"),
    ("re-check", r"\bre[- ]?check(?:s|ed|ing)?\b"),
    ("repeat", r"\brepeat(?:s|ed|ing)?\b"),
    ("retry", r"\bretr(?:y|ies|ied|ying)\b"),
    ("resubmit", r"\bre[- ]?submit(?:s|ted|ting)?\b"),
    ("return", r"\breturn(?:s|ed|ing)?\b"),
    ("sent back", r"\bsent\s+back\b"),
)

_FAILURE_SIGNAL_PATTERNS = (
    ("failure", r"\b(?:fail(?:s|ed|ure)?|error(?:s)?|incorrect(?:ly)?)\b"),
    ("incomplete", r"\b(?:incomplete|not\s+complete|missing)\b"),
    ("invalid", r"\b(?:invalid|not\s+valid)\b"),
    ("rejection", r"\b(?:reject(?:s|ed|ion)?|not\s+approve(?:d)?)\b"),
    ("change_required", r"\b(?:ask(?:s|ed)?\s+for\s+(?:a\s+)?change|change\s+required)\b"),
    ("negative_response", r"\bnegative\s+(?:response|result|outcome)\b"),
    ("not_ok", r"\bnot\s+ok\b"),
    ("no_response", r"\bno\s+response\b"),
    ("correction_required", r"\b(?:ask(?:s|ed)?\s+for\s+corrections?|return(?:s|ed)?\b[^.]{0,100}\bfor\s+corrections?)\b"),
    ("otherwise_retry", r"\botherwise\b"),
    ("until_condition", r"\buntil\b"),
)

_CORRECTIVE_OPERATION_PATTERNS = (
    ("correct", r"\bcorrect(?:s|ed|ing|ion|ions)?\b"),
    ("update", r"\bupdat(?:e|es|ed|ing)\b"),
    ("revise", r"\brevis(?:e|es|ed|ing|ion)\b"),
    ("repair", r"\brepair(?:s|ed|ing)?\b"),
    ("resolve", r"\bresolv(?:e|es|ed|ing)\b"),
    ("rework", r"\brework(?:s|ed|ing)?\b"),
    ("retry_operation", r"\bretr(?:y|ies|ied|ying)\b\s+[a-z]"),
    ("review_comments", r"\breview(?:s|ed|ing)?\b[^.]{0,80}\bcomments?\b"),
    ("choose_different", r"\bchoose(?:s|n)?\s+(?:a\s+)?different\b"),
    ("new_cycle_work", r"\b(?:create\s+(?:a\s+)?new|initiate\s+another)\b[^.]{0,100}\b(?:plan|cycle)\b"),
    ("another_activity", r"\banother\b[^.]{0,80}\b(?:activity|repair|attempt|cycle)\b"),
    ("repeat_operation", r"\brepeat(?:s|ed|ing)?\b"),
    ("reminder", r"\breminder\b"),
)

_RETURN_TARGET_PATTERNS = (
    ("returned_to", r"\breturn(?:s|ed|ing)?\s+(?:it\s+)?to\b"),
    ("sent_back_to", r"\bsent\s+back\s+to\b"),
    ("send_back_to", r"\bsend(?:s|ing)?\s+(?:it\s+)?back\s+to\b"),
    ("go_back_to", r"\b(?:go|goes|went)\s+back\s+to\b"),
    ("restart", r"\b(?:restart|restarts|restarted|re-enter|re-enters)\b"),
    ("previous_stage", r"\b(?:back\s+to|to)\s+(?:the\s+)?(?:previous|first|earlier|beginning)\b"),
    ("operation_again", r"\b(?:check|review|generate|perform|execute|submit)\w*\b[^.]{0,80}\bagain\b"),
    ("request_again", r"\b(?:ask|request)\w*\b[^.]{0,80}\bagain\b"),
    ("another_activity", r"\banother\b[^.]{0,80}\b(?:activity|repair|attempt|cycle)\b"),
    ("choose_different", r"\bchoose(?:s|n)?\s+(?:a\s+)?different\b"),
    ("retry_until", r"\bretr(?:y|ies|ied|ying)\b[^.]{0,100}\buntil\b"),
    ("corrective_operation_until", r"\b(?:correct|update|revise|repair|resolve|rework)\w*\b[^.]{0,100}\buntil\b"),
    ("repeated_until", r"\b(?:repeat\w*|another\s+reminder|and\s+so\s+on)\b[^.]{0,120}\buntil\b"),
    ("return_for_correction", r"\breturn\w*\s+to\b[^.]{0,100}\bcorrections?\b[^.]{0,100}\bagain\b"),
)

_SUCCESS_EXIT_PATTERNS = (
    ("success", r"\b(?:success|succeeds?|successful(?:ly)?)\b"),
    ("complete", r"\b(?:complete|completed|valid|approved|passes?|finished)\b"),
    ("continuation", r"\b(?:continue|continues|proceed|proceeds|ends?|finished)\b"),
    ("otherwise", r"\botherwise\b"),
    ("all_handled", r"\b(?:all|every)\b[^.]{0,100}\b(?:handled|processed|reserved|ordered|complete|completed|correct)\b"),
    ("selected", r"\bafter\b[^.]{0,100}\bselected\b"),
    ("marked_ok", r"\b(?:marked\s+as\s+)?ok\b"),
    ("received", r"\buntil\b[^.]{0,100}\breceived\b"),
)

_BOUNDED_ITERATION_PATTERNS = (
    r"\b(?:procedure|process|activity|operation|step|region)\b[^.]{0,100}\brepeat(?:s|ed|ing)?\b[^.]{0,100}\b(?:for|over)\s+(?:each|every|all)\b",
    r"\brepeat(?:s|ed|ing)?\b[^.]{0,120}\b(?:for|over)\s+(?:each|every|all)\b",
    r"\b(?:for|over)\s+(?:each|every|all)\b[^.]{0,120}\brepeat(?:s|ed|ing)?\b",
    r"\b(?:process|perform|handle|check)\w*\b[^.]{0,120}\buntil\s+all\b",
)

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
    "inspect",
    "order",
    "prepar",
    "process",
    "provision",
    "readi",
    "record",
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
        ("while_with_independent_activities", _has_while_clause_concurrency),
        ("multiple_activities_in_arbitrary_order", _has_arbitrary_order_concurrency),
        ("multiple_outputs_synchronized_before_continuation", _has_multi_output_synchronization),
    )
    for label, detector in compound_checks:
        if detector(text) and label not in evidence:
            evidence.append(label)
    return evidence


def _sentences(process_text: str) -> List[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", process_text.strip())
        if sentence.strip()
    ]


def _matched_signal_labels(text: str, patterns: tuple[tuple[str, str], ...]) -> List[str]:
    return [label for label, pattern in patterns if re.search(pattern, text, re.IGNORECASE)]


def _evidence_window(sentences: List[str], index: int, *, radius: int = 2) -> str:
    start = max(0, index - radius)
    end = min(len(sentences), index + radius + 1)
    return " ".join(sentences[start:end])


def extract_loop_evidence(process_text: str) -> Dict[str, Any]:
    """Extract conservative evidence contracts; weak repetition vocabulary is never sufficient."""
    sentences = _sentences(process_text)
    normalized_text = _normalize_process_text(process_text)
    weak_cues = _matched_signal_labels(normalized_text, _WEAK_LOOP_CUE_PATTERNS)
    candidates: List[Dict[str, Any]] = []

    for index, sentence in enumerate(sentences):
        if not any(re.search(pattern, sentence, re.IGNORECASE) for pattern in _BOUNDED_ITERATION_PATTERNS):
            continue
        window = _evidence_window(sentences, index, radius=1)
        unit_match = re.search(r"\b(?:for|over)\s+(each|every|all)\s+([a-z][a-z -]{0,50})", sentence, re.IGNORECASE)
        iteration_unit = " ".join(unit_match.groups()).strip() if unit_match else "bounded collection"
        completion = _matched_signal_labels(window, _SUCCESS_EXIT_PATTERNS) or ["explicit bounded repetition"]
        candidates.append(
            {
                "kind": "bounded_iteration",
                "source_fragment": window,
                "repeated_operation": sentence,
                "iteration_unit": iteration_unit,
                "completion_evidence": completion,
            }
        )

    for index, sentence in enumerate(sentences):
        local_failure = _matched_signal_labels(sentence, _FAILURE_SIGNAL_PATTERNS)
        if not local_failure:
            continue
        window = _evidence_window(sentences, index)
        corrective = _matched_signal_labels(window, _CORRECTIVE_OPERATION_PATTERNS)
        return_target = _matched_signal_labels(window, _RETURN_TARGET_PATTERNS)
        success_exit = _matched_signal_labels(window, _SUCCESS_EXIT_PATTERNS)
        if not (corrective and return_target and success_exit):
            continue
        candidates.append(
            {
                "kind": "retry_cycle",
                "source_fragment": window,
                "retry_condition": local_failure,
                "corrective_operation": corrective,
                "return_or_reexecution_evidence": return_target,
                "successful_exit_evidence": success_exit,
            }
        )

    deduplicated: List[Dict[str, Any]] = []
    seen = set()
    for candidate in candidates:
        key = (candidate["kind"], candidate["source_fragment"])
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(candidate)

    return {
        "high_confidence": bool(deduplicated),
        "weak_cues": weak_cues,
        "candidates": deduplicated,
    }


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
    loop_evidence = extract_loop_evidence(process_text)
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
    if loop_evidence["high_confidence"]:
        hints.append(
            {
                "kind": "possible_loop",
                "confidence": "high",
                "evidence": loop_evidence["candidates"],
                "guidance": "Model the supported repeated region with a backward path and a distinct exit path.",
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
            "possible_loop": bool(loop_evidence["high_confidence"]),
            "possible_parallelism": bool(parallel_terms),
            "retry_semantics": bool(retry_terms),
            "approval_flow": bool(approval_terms),
            "exit_condition": bool(exit_terms),
        },
        "evidence": {
            "decision_terms": decision_terms,
            "loop_terms": loop_terms,
            "loop_evidence": loop_evidence,
            "retry_terms": retry_terms,
            "parallel_terms": parallel_terms,
            "approval_terms": approval_terms,
            "exit_terms": exit_terms,
        },
        "hints": hints,
    }


__all__ = ["KeywordHints", "extract_keyword_hints", "extract_loop_evidence", "extract_parallel_evidence"]
