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


def _normalize_process_text(process_text: str) -> str:
    return " ".join(process_text.lower().split())


def _contains_any(text: str, phrases: List[str]) -> List[str]:
    matches: List[str] = []
    for phrase in phrases:
        pattern = r"\b" + re.escape(phrase) + r"\b"
        if re.search(pattern, text):
            matches.append(phrase)
    return matches


def extract_keyword_hints(process_text: str) -> KeywordHints:
    text = _normalize_process_text(process_text)

    decision_terms = _contains_any(
        text,
        ["if", "otherwise", "else", "whether", "approved", "rejected", "yes", "no"],
    )
    loop_terms = _contains_any(text, STRONG_LOOP_PHRASES)
    retry_terms = _contains_any(text, RETRY_SEMANTIC_PHRASES)
    parallel_terms = _contains_any(
        text,
        ["simultaneously", "in parallel", "concurrently", "at the same time", "meanwhile"],
    )
    approval_terms = _contains_any(
        text,
        ["approve", "approved", "reject", "rejected", "accept", "decline"],
    )
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


__all__ = ["KeywordHints", "extract_keyword_hints"]
