from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


ControlRequirement = Dict[str, Any]

_PARALLEL_MARKER = re.compile(
    r"\b(?:simultaneously|in\s+parallel|at\s+the\s+same\s+time)\b",
    re.IGNORECASE,
)
_ACTION_WORD = (
    r"approv(?:e|es|ed|ing)|archiv(?:e|es|ed|ing)|assign(?:s|ed|ing)?|"
    r"carry\s+out|check(?:s|ed|ing)?|conduct(?:s|ed|ing)?|continu(?:e|es|ed|ing)|"
    r"correct(?:s|ed|ing)?|creat(?:e|es|ed|ing)|execut(?:e|es|ed|ing)|"
    r"inform(?:s|ed|ing)?|perform(?:s|ed|ing)?|prepar(?:e|es|ed|ing)|"
    r"process(?:es|ed|ing)?|recheck(?:s|ed|ing)?|reject(?:s|ed|ing)?|"
    r"repeat(?:s|ed|ing)?|review(?:s|ed|ing)?|send(?:s|ing)?|sent|"
    r"stor(?:e|es|ed|ing)|updat(?:e|es|ed|ing)|validat(?:e|es|ed|ing)"
)
_ACTION = re.compile(rf"\b(?:{_ACTION_WORD})\b", re.IGNORECASE)
_BASE_ACTION_WORD = (
    r"approve|archive|assign|carry\s+out|check|conduct|continue|correct|create|execute|"
    r"inform|perform|prepare|process|recheck|reject|repeat|review|send|store|update|validate"
)
_ACTIVE_ACTION_WORD = (
    r"approves?|archives?|assigns?|carries\s+out|checks?|conducts?|continues?|corrects?|"
    r"creates?|executes?|informs?|performs?|prepares?|process(?:es)?|rechecks?|rejects?|"
    r"repeats?|reviews?|sends?|stores?|updates?|validates?"
)
_PASSIVE = re.compile(
    rf"^(?P<subject>.+?)\s+(?:is|are|was|were|be|been|gets?|got)\s+(?:{_ACTION_WORD})\b",
    re.IGNORECASE,
)
_ACTIVE = re.compile(
    rf"^(?P<subject>.+?)\s+(?:{_ACTIVE_ACTION_WORD})\b",
    re.IGNORECASE,
)
_IMPERATIVE = re.compile(rf"^(?:please\s+)?(?:{_BASE_ACTION_WORD})\b", re.IGNORECASE)
_OPTIONAL_IMPERATIVE = re.compile(
    r"^(?:perform|execute|conduct|carry\s+out)\b",
    re.IGNORECASE,
)
_NON_BINDING_SUBJECT = re.compile(
    r"^(?:it|they|he|she|this|that|these|those|which|who)\b",
    re.IGNORECASE,
)
_SUBORDINATE_REPORTING = re.compile(
    r"\b(?:whether|that|if|when|where|why|how)\b",
    re.IGNORECASE,
)
_COREFERENTIAL_BODY = re.compile(
    r"^(?:(?:it|this|that|these|those|them)\b|"
    r"(?:the\s+)?(?:previous|prior|former|same|above|aforementioned)\b)",
    re.IGNORECASE,
)
_LOOP = re.compile(
    r"\b(?P<cue>repeat|retry|recheck)\b\s+(?P<body>.+?)\s+\buntil\b\s+(?P<exit>[^.;!?]+)",
    re.IGNORECASE,
)
_BEHAVIORAL_EXIT = re.compile(
    r"\b(?:accept(?:ed|able)?|approv(?:e|ed|al)?|complete(?:d)?|correct(?:ed)?|"
    r"finish(?:ed)?|pass(?:es|ed)?|ready|resolv(?:e|ed)|succeed(?:s|ed)?|"
    r"success(?:ful)?|valid(?:ated)?|no\s+(?:errors?|issues?|defects?))\b",
    re.IGNORECASE,
)
_TEMPORAL_EXIT = re.compile(
    r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"january|february|march|april|may|june|july|august|september|october|"
    r"november|december|deadline|noon|midnight|\d{1,2}(?::\d{2})?)\b",
    re.IGNORECASE,
)


def _trimmed_span(text: str, start: int, end: int) -> Optional[Dict[str, Any]]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    if start >= end:
        return None
    return {"start": start, "end": end, "text": text[start:end]}


def _sentence_spans(text: str) -> List[Dict[str, Any]]:
    spans: List[Dict[str, Any]] = []
    for match in re.finditer(r"[^.!?]+(?:[.!?]+|$)", text):
        span = _trimmed_span(text, match.start(), match.end())
        if span is not None:
            spans.append(span)
    return spans


def _action_clause_kind(value: str) -> Optional[str]:
    clause = value.strip(" \t\r\n,;:-")
    if not clause or not _ACTION.search(clause):
        return None
    if _IMPERATIVE.match(clause):
        return "imperative"
    predicate = _PASSIVE.match(clause) or _ACTIVE.match(clause)
    if predicate is None:
        return None
    subject = predicate.group("subject").strip()
    if not subject or _NON_BINDING_SUBJECT.match(subject):
        return None
    return "subjected"


def _independent_action_clause(value: str) -> bool:
    return _action_clause_kind(value) is not None


def _parallel_requirement(sentence: Dict[str, Any]) -> bool:
    value = sentence["text"]
    marker = _PARALLEL_MARKER.search(value)
    if marker is None:
        return False
    before_marker = value[: marker.start()].strip(" \t\r\n,;:.-")
    after_marker = value[marker.end() :].strip(" \t\r\n,;:.-")
    if before_marker and after_marker:
        return False
    without_marker = value[: marker.start()] + " " + value[marker.end() :]
    clauses = [
        part
        for part in re.split(r"\s*;\s*|\s*,\s*and\s+|\s+and\s+", without_marker)
        if part.strip()
    ]
    if len(clauses) != 2 or any(_SUBORDINATE_REPORTING.search(clause) for clause in clauses):
        return False
    action_kinds = [kind for clause in clauses if (kind := _action_clause_kind(clause))]
    if len(action_kinds) != 2:
        return False
    if all(kind == "subjected" for kind in action_kinds):
        return True
    return all(kind == "imperative" for kind in action_kinds) and bool(
        _IMPERATIVE.match(without_marker.strip(" \t\r\n,;:-"))
    )


def _decision_requirement(sentence: Dict[str, Any]) -> bool:
    value = sentence["text"].strip()
    optional = re.match(
        r"^if\s+(?:required|necessary)\s*,\s*(?P<action>.+)$",
        value,
        re.IGNORECASE,
    )
    if optional is not None:
        return bool(_OPTIONAL_IMPERATIVE.match(optional.group("action").strip()))

    paired = re.match(
        r"^if\b(?P<condition>.+?)[,;]\s*(?P<first>.+?)"
        r"(?:[.;]\s*|\s+)(?:otherwise|else)\s*[,;:]?\s*(?P<second>.+)$",
        value,
        re.IGNORECASE,
    )
    if paired is None or not paired.group("condition").strip():
        return False
    return _independent_action_clause(paired.group("first")) and _independent_action_clause(
        paired.group("second")
    )


def _loop_requirement(sentence: Dict[str, Any]) -> bool:
    match = _LOOP.search(sentence["text"])
    if match is None:
        return False
    if re.search(r"\b(?:not|never|without)\b", sentence["text"][: match.start("cue")], re.IGNORECASE):
        return False
    body = match.group("body").strip(" \t\r\n,;:-")
    exit_condition = match.group("exit").strip(" \t\r\n,;:-")
    if not body or not exit_condition:
        return False
    if _COREFERENTIAL_BODY.search(body):
        return False
    if _TEMPORAL_EXIT.search(exit_condition):
        return False
    return bool(_BEHAVIORAL_EXIT.search(exit_condition))


def extract_control_requirements(process_text: str) -> List[ControlRequirement]:
    """Return only mechanically explicit topology-presence requirements."""

    detected: List[tuple[int, str, str, Dict[str, Any]]] = []
    for sentence in _sentence_spans(process_text):
        if _parallel_requirement(sentence):
            detected.append((sentence["start"], "parallel", "explicit_local_parallel", sentence))
        if _decision_requirement(sentence):
            detected.append((sentence["start"], "decision", "explicit_local_decision", sentence))
        if _loop_requirement(sentence):
            detected.append((sentence["start"], "loop", "explicit_body_until_exit", sentence))

    unique: List[tuple[int, str, str, Dict[str, Any]]] = []
    seen: set[tuple[str, int, int]] = set()
    for item in sorted(detected, key=lambda value: (value[0], value[1], value[2])):
        key = (item[1], item[3]["start"], item[3]["end"])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return [
        {
            "requirement_id": f"MCG{index}",
            "detector_id": detector_id,
            "source_span": source_span,
            "required_topology_kind": topology_kind,
        }
        for index, (_, topology_kind, detector_id, source_span) in enumerate(unique, start=1)
    ]


__all__ = ["ControlRequirement", "extract_control_requirements"]
