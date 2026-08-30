from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional


ControlEvidenceReport = Dict[str, Any]

_CONTROL_KINDS = ("parallel", "synchronization", "exclusive", "loop", "optional")
_CLASSIFICATIONS = ("high_confidence", "supporting", "ambiguous")
_CLASSIFICATION_RANK = {name: index for index, name in enumerate(_CLASSIFICATIONS)}

_EXECUTABLE_VERB = re.compile(
    r"\b(?:add|approv|assign|check|conduct|continue|correct|create|distribut|examin|finish|formulat|"
    r"hand|happen|inform|initiat|issue|mark|meet|perform|plan|prepar|proceed|process|produc|put|"
    r"read|receiv|record|recheck|reject|repeat|request|resubmit|return|review|send|sent|store|"
    r"track|transcrib|updat|validat|write)\w*\b",
    re.IGNORECASE,
)
_STATE_ONLY = re.compile(
    r"\b(?:remain|remains|remained|idle|open|pending|unchanged|wait|waits|waiting)\b",
    re.IGNORECASE,
)
_COMPLETION = re.compile(
    r"\b(?:are|is|have|has|were|was)?\s*(?:completed?|finished?|done|ready|available|"
    r"received|finish(?:ed)?|taken\s+place|occurred)\b",
    re.IGNORECASE,
)
_OVERLAP_MARKERS = re.compile(
    r"\b(?:while|meanwhile|(?:in\s+the\s+)?meantime)\b",
    re.IGNORECASE,
)
_EXPLICIT_PARALLEL_MARKERS = re.compile(
    r"\b(?:at\s+the\s+same\s+time|simultaneously|concurrently|in\s+parallel)\b",
    re.IGNORECASE,
)
_SYNCHRONIZATION_START = re.compile(
    r"\b(?:as\s+soon\s+as|only\s+after|after|once|when)\b",
    re.IGNORECASE,
)
_REPETITION = re.compile(
    r"\b(?:retry|retries|retried|repeat|repeats|repeated|recheck|rechecks|rechecked|"
    r"resubmit|resubmits|resubmitted|rework|reworks|reworked)\w*\b",
    re.IGNORECASE,
)
_RETURN_CUE = re.compile(r"\b(?:sent\s+back|send\s+back|return(?:ed)?\s+to|go\s+back)\b", re.IGNORECASE)
_OPTIONAL_APPLICABILITY = re.compile(
    r"\b(?:if|when)\s+(?:it\s+is\s+)?(?:required|needed|necessary|applicable)\b",
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


def _sentence_for_offset(sentences: Iterable[Dict[str, Any]], offset: int) -> Optional[Dict[str, Any]]:
    for sentence in sentences:
        if sentence["start"] <= offset < sentence["end"]:
            return sentence
    return None


def _is_executable(value: str) -> bool:
    if not _EXECUTABLE_VERB.search(value):
        return False
    without_state = _STATE_ONLY.sub("", value)
    return bool(_EXECUTABLE_VERB.search(without_state))


def _clause_candidates(text: str, start: int, end: int) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    segment = text[start:end]
    for match in re.finditer(r"[^,;]+", segment):
        span = _trimmed_span(text, start + match.start(), start + match.end())
        if span is not None and _is_executable(span["text"]):
            candidates.append(span)
    return candidates


def _nearest_activity_before(
    text: str,
    sentences: List[Dict[str, Any]],
    offset: int,
) -> Optional[Dict[str, Any]]:
    sentence = _sentence_for_offset(sentences, offset)
    if sentence is not None:
        local = _clause_candidates(text, sentence["start"], offset)
        if local:
            return local[-1]
        sentence_index = sentences.index(sentence)
    else:
        sentence_index = len(sentences)
    for previous in reversed(sentences[:sentence_index]):
        candidates = _clause_candidates(text, previous["start"], previous["end"])
        if candidates:
            return candidates[-1]
    return None


def _nearest_activity_after(
    text: str,
    sentences: List[Dict[str, Any]],
    offset: int,
) -> Optional[Dict[str, Any]]:
    sentence = _sentence_for_offset(sentences, offset)
    if sentence is None:
        return None
    candidates = _clause_candidates(text, offset, sentence["end"])
    return candidates[0] if candidates else None


def _candidate(
    *,
    control_kind: str,
    classification: str,
    detector_id: str,
    source_span: Dict[str, Any],
    cue_span: Dict[str, Any],
    activity_spans: List[Dict[str, Any]],
    rationale: str,
    continuation_span: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    item: Dict[str, Any] = {
        "control_kind": control_kind,
        "classification": classification,
        "detector_id": detector_id,
        "source_span": source_span,
        "cue_span": cue_span,
        "activity_spans": activity_spans,
        "continuation_span": continuation_span,
        "rationale": rationale,
    }
    return item


def _parallel_candidates(text: str, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for marker in _OVERLAP_MARKERS.finditer(text):
        sentence = _sentence_for_offset(sentences, marker.start())
        if sentence is None:
            continue
        cue_span = _trimmed_span(text, marker.start(), marker.end())
        if cue_span is None:
            continue
        left = _nearest_activity_before(text, sentences, marker.start())
        right = _nearest_activity_after(text, sentences, marker.end())
        activities = [span for span in (left, right) if span is not None]
        activities = [span for index, span in enumerate(activities) if span not in activities[:index]]
        if len(activities) >= 2 and activities[0]["start"] != activities[1]["start"]:
            classification = "high_confidence"
            rationale = "temporal overlap connects two distinct executable activities"
        elif activities:
            marker_text = marker.group(0).lower()
            classification = "supporting" if marker_text in {"meanwhile", "in the meantime", "meantime"} else "ambiguous"
            rationale = "temporal overlap cue lacks two distinct executable activities"
        else:
            classification = "ambiguous"
            rationale = "temporal wording describes context without executable overlap"
        candidates.append(
            _candidate(
                control_kind="parallel",
                classification=classification,
                detector_id="temporal_overlap_activities",
                source_span=sentence,
                cue_span=cue_span,
                activity_spans=activities,
                rationale=rationale,
            )
        )

    for marker in _EXPLICIT_PARALLEL_MARKERS.finditer(text):
        sentence = _sentence_for_offset(sentences, marker.start())
        if sentence is None:
            continue
        cue_span = _trimmed_span(text, marker.start(), marker.end())
        if cue_span is None:
            continue
        activity_spans = _coordinated_activities_before_marker(text, sentence, marker.start())
        classification = "high_confidence" if len(activity_spans) >= 2 else "supporting"
        rationale = (
            "explicit concurrency marker applies to two distinct activities"
            if classification == "high_confidence"
            else "explicit concurrency marker lacks two identifiable activity spans"
        )
        candidates.append(
            _candidate(
                control_kind="parallel",
                classification=classification,
                detector_id="explicit_concurrency_activities",
                source_span=sentence,
                cue_span=cue_span,
                activity_spans=activity_spans,
                rationale=rationale,
            )
        )
    return candidates


def _coordinated_activities_before_marker(
    text: str,
    sentence: Dict[str, Any],
    marker_start: int,
) -> List[Dict[str, Any]]:
    prefix = text[sentence["start"] : marker_start]
    coordinated = re.search(
        r"(?P<left>[^,;]+?)\s+and\s+(?P<right>[^,;]+?)\s+"
        r"(?:(?:are|were)\s+\w+|happen\w*|occur\w*)\s*$",
        prefix,
        re.IGNORECASE,
    )
    if coordinated:
        spans = []
        for name in ("left", "right"):
            span = _trimmed_span(
                text,
                sentence["start"] + coordinated.start(name),
                sentence["start"] + coordinated.end(name),
            )
            if span is not None:
                spans.append(span)
        return spans
    clauses = _clause_candidates(text, sentence["start"], marker_start)
    return clauses[-2:] if len(clauses) >= 2 else clauses


def _coordination_spans(text: str, start: int, end: int) -> List[Dict[str, Any]]:
    value = text[start:end]
    both_match = re.search(
        r"\bboth\s+(.+?)\s+and\s+(.+?)(?=\s+(?:are|have|were|finish|complete)|$)",
        value,
        re.IGNORECASE,
    )
    ordinal_match = re.search(r"\b(first)\s+and\s+(second\s+\w+)", value, re.IGNORECASE)
    general_match = re.search(
        r"\b([^,;]{1,80}?)\s+and\s+([^,;]{1,80}?)(?=\s+(?:are|have|were|finish|complete)|$)",
        value,
        re.IGNORECASE,
    )
    match = both_match or ordinal_match or general_match
    if match is None:
        grouped_match = re.search(r"\b(?:both|all)\s+[^,;]+", value, re.IGNORECASE)
        if grouped_match is None:
            return []
        span = _trimmed_span(text, start + grouped_match.start(), start + grouped_match.end())
        return [span] if span is not None else []
    spans = []
    for group_index in (1, 2):
        span = _trimmed_span(text, start + match.start(group_index), start + match.end(group_index))
        if span is not None:
            spans.append(span)
    return spans


def _has_grouped_activity_barrier(value: str) -> bool:
    return bool(
        re.search(
            r"\b(?:both|all|two|multiple|several)\s+(?:required\s+)?"
            r"(?:activities|actions|checks|meetings|paths|tasks|workstreams)\b",
            value,
            re.IGNORECASE,
        )
    )


def _synchronization_candidates(text: str, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for marker in _SYNCHRONIZATION_START.finditer(text):
        sentence = _sentence_for_offset(sentences, marker.start())
        if sentence is None:
            continue
        sentence_text = text[sentence["start"] : sentence["end"]]
        local_marker_end = marker.end() - sentence["start"]
        comma_offset = sentence_text.find(",", local_marker_end)
        if comma_offset < 0:
            continue
        barrier_start = marker.end()
        barrier_end = sentence["start"] + comma_offset
        barrier_text = text[barrier_start:barrier_end]
        if not _COMPLETION.search(barrier_text):
            continue
        activity_spans = _coordination_spans(text, barrier_start, barrier_end)
        continuation = _trimmed_span(text, barrier_end + 1, sentence["end"])
        continuation_is_executable = continuation is not None and _is_executable(continuation["text"])
        has_multiple = len(activity_spans) >= 2 or _has_grouped_activity_barrier(barrier_text)
        if has_multiple and continuation_is_executable:
            classification = "high_confidence"
            rationale = "multiple required activities complete before an executable continuation"
        elif has_multiple:
            classification = "supporting"
            rationale = "multi-activity completion barrier lacks an identifiable continuation"
        else:
            classification = "ambiguous"
            rationale = "completion wording does not identify multiple required activities"
        cue_end_match = _COMPLETION.search(barrier_text)
        cue_end = barrier_start + cue_end_match.end() if cue_end_match is not None else marker.end()
        cue_span = _trimmed_span(text, marker.start(), cue_end)
        if cue_span is None:
            continue
        candidates.append(
            _candidate(
                control_kind="synchronization",
                classification=classification,
                detector_id="multi_activity_completion_barrier",
                source_span=sentence,
                cue_span=cue_span,
                activity_spans=activity_spans,
                continuation_span=continuation,
                rationale=rationale,
            )
        )
    return candidates


def _exclusive_candidates(text: str, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    paired_if = re.compile(r"\bif\b(.+?)[,;](.+?)\b(?:otherwise|else)\b[,;]?(.+)", re.IGNORECASE)
    either_or = re.compile(r"\beither\b(.+?)\bor\b(.+)", re.IGNORECASE)
    if_sentences: List[tuple[Dict[str, Any], re.Match[str]]] = []

    for sentence in sentences:
        value = sentence["text"]
        match = paired_if.search(value)
        if match:
            alternatives = []
            for group_index in (2, 3):
                span = _trimmed_span(
                    text,
                    sentence["start"] + match.start(group_index),
                    sentence["start"] + match.end(group_index),
                )
                if span is not None and _is_executable(span["text"]):
                    alternatives.append(span)
            classification = "high_confidence" if len(alternatives) == 2 else "supporting"
            cue_span = _trimmed_span(text, sentence["start"] + match.start(), sentence["start"] + match.end())
            if cue_span is not None:
                candidates.append(
                    _candidate(
                        control_kind="exclusive",
                        classification=classification,
                        detector_id="if_else_executable_alternatives",
                        source_span=sentence,
                        cue_span=cue_span,
                        activity_spans=alternatives,
                        rationale=(
                            "conditional construction contains two executable alternatives"
                            if classification == "high_confidence"
                            else "conditional construction lacks two executable alternatives"
                        ),
                    )
                )
            continue

        match = either_or.search(value)
        if match:
            alternatives = []
            for group_index in (1, 2):
                span = _trimmed_span(
                    text,
                    sentence["start"] + match.start(group_index),
                    sentence["start"] + match.end(group_index),
                )
                if span is not None and _is_executable(span["text"]):
                    alternatives.append(span)
            classification = "high_confidence" if len(alternatives) == 2 else "supporting"
            cue_span = _trimmed_span(text, sentence["start"] + match.start(), sentence["start"] + match.end())
            if cue_span is not None:
                candidates.append(
                    _candidate(
                        control_kind="exclusive",
                        classification=classification,
                        detector_id="either_or_executable_alternatives",
                        source_span=sentence,
                        cue_span=cue_span,
                        activity_spans=alternatives,
                        rationale=(
                            "either-or construction contains two executable alternatives"
                            if classification == "high_confidence"
                            else "either-or construction lacks two executable alternatives"
                        ),
                    )
                )

        simple_if = re.search(r"\bif\b(.+?)[,;](.+)", value, re.IGNORECASE)
        if simple_if:
            if_sentences.append((sentence, simple_if))

    for index in range(len(if_sentences) - 1):
        first_sentence, first = if_sentences[index]
        second_sentence, second = if_sentences[index + 1]
        first_condition = first.group(1).lower()
        second_condition = second.group(1).lower()
        condition_tokens = set(re.findall(r"[a-z]+", first_condition)) & set(re.findall(r"[a-z]+", second_condition))
        complementary = bool(condition_tokens) and ("not" in first_condition) != ("not" in second_condition)
        first_action = _trimmed_span(
            text,
            first_sentence["start"] + first.start(2),
            first_sentence["start"] + first.end(2),
        )
        second_action = _trimmed_span(
            text,
            second_sentence["start"] + second.start(2),
            second_sentence["start"] + second.end(2),
        )
        if not complementary or first_action is None or second_action is None:
            continue
        if not (_is_executable(first_action["text"]) and _is_executable(second_action["text"])):
            continue
        source_span = _trimmed_span(text, first_sentence["start"], second_sentence["end"])
        cue_span = _trimmed_span(
            text,
            first_sentence["start"] + first.start(),
            second_sentence["start"] + second.end(1),
        )
        if source_span is not None and cue_span is not None:
            candidates.append(
                _candidate(
                    control_kind="exclusive",
                    classification="high_confidence",
                    detector_id="complementary_if_executable_alternatives",
                    source_span=source_span,
                    cue_span=cue_span,
                    activity_spans=[first_action, second_action],
                    rationale="complementary conditions lead to distinct executable alternatives",
                )
            )
    return candidates


def _loop_candidates(text: str, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for sentence in sentences:
        value = sentence["text"]
        repetition = _REPETITION.search(value)
        return_cue = _RETURN_CUE.search(value)
        until = re.search(r"\buntil\b", value, re.IGNORECASE)
        again = re.search(r"\bagain\b", value, re.IGNORECASE)
        if repetition is None and return_cue is None and until is None and again is None:
            continue
        executable = _is_executable(value)
        has_body = repetition is not None and executable
        has_returned_body = return_cue is not None and (repetition is not None or again is not None)
        has_until_body = until is not None and executable and not re.search(r"\bwait\w*\s+until\b", value, re.IGNORECASE)
        if has_body or has_returned_body or has_until_body:
            classification = "high_confidence"
            rationale = "an identifiable executable activity is explicitly repeated or returned to"
        elif executable:
            classification = "supporting"
            rationale = "repetition cue is present but the repeated body is not fully resolved"
        else:
            classification = "ambiguous"
            rationale = "isolated repetition wording lacks an executable loop body"
        cue_match = repetition or return_cue or until or again
        cue_span = _trimmed_span(
            text,
            sentence["start"] + cue_match.start(),
            sentence["start"] + cue_match.end(),
        )
        if cue_span is None:
            continue
        activity_spans = _clause_candidates(text, sentence["start"], sentence["end"])
        candidates.append(
            _candidate(
                control_kind="loop",
                classification=classification,
                detector_id="explicit_repetition_body",
                source_span=sentence,
                cue_span=cue_span,
                activity_spans=activity_spans,
                rationale=rationale,
            )
        )
    return candidates


def _optional_candidates(text: str, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    patterns = (
        ("explicit_applicability_condition", _OPTIONAL_APPLICABILITY),
        ("new_subject_applicability", re.compile(r"\bfor\s+new\s+[^,.;]+", re.IGNORECASE)),
        (
            "required_subject_applicability",
            re.compile(r"\bfor\s+(?:each|any)\s+[^,.;]+\b(?:required|needed|necessary|applicable)\b", re.IGNORECASE),
        ),
        ("explicit_optional_modal", re.compile(r"\bmay\s+optionally\b", re.IGNORECASE)),
    )
    for sentence in sentences:
        value = sentence["text"]
        matched = False
        for detector_id, pattern in patterns:
            cue = pattern.search(value)
            if cue is None:
                continue
            matched = True
            cue_end = sentence["start"] + cue.end()
            activities = _clause_candidates(text, cue_end, sentence["end"])
            if not activities:
                activities = _clause_candidates(text, sentence["start"], sentence["end"])
            classification = "high_confidence" if activities else "supporting"
            cue_span = _trimmed_span(
                text,
                sentence["start"] + cue.start(),
                sentence["start"] + cue.end(),
            )
            if cue_span is None:
                continue
            candidates.append(
                _candidate(
                    control_kind="optional",
                    classification=classification,
                    detector_id=detector_id,
                    source_span=sentence,
                    cue_span=cue_span,
                    activity_spans=activities,
                    rationale=(
                        "an explicit applicability condition controls an executable activity"
                        if classification == "high_confidence"
                        else "applicability wording lacks an identifiable executable activity"
                    ),
                )
            )
        if matched:
            continue
        modal = re.search(r"\bmay(?:\s+not)?\b", value, re.IGNORECASE)
        if modal is not None and " or " not in value.lower():
            cue_span = _trimmed_span(
                text,
                sentence["start"] + modal.start(),
                sentence["start"] + modal.end(),
            )
            if cue_span is not None:
                candidates.append(
                    _candidate(
                        control_kind="optional",
                        classification="ambiguous",
                        detector_id="unqualified_modal_may",
                        source_span=sentence,
                        cue_span=cue_span,
                        activity_spans=_clause_candidates(text, sentence["start"], sentence["end"]),
                        rationale="unqualified modal wording does not establish optional execution",
                    )
                )
    return candidates


def _overlaps(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    return left["start"] < right["end"] and right["start"] < left["end"]


def _deduplicate(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    for candidate in sorted(
        candidates,
        key=lambda item: (
            item["control_kind"],
            _CLASSIFICATION_RANK[item["classification"]],
            item["source_span"]["start"],
            item["detector_id"],
        ),
    ):
        duplicate = next(
            (
                existing
                for existing in selected
                if existing["control_kind"] == candidate["control_kind"]
                and existing["detector_id"] == candidate["detector_id"]
                and _overlaps(existing["source_span"], candidate["source_span"])
            ),
            None,
        )
        if duplicate is None:
            selected.append(candidate)
    return sorted(
        selected,
        key=lambda item: (
            item["source_span"]["start"],
            item["control_kind"],
            item["detector_id"],
        ),
    )


def extract_control_evidence(process_text: str) -> ControlEvidenceReport:
    """Extract deterministic, source-grounded control evidence without enforcing topology."""
    text = str(process_text or "")
    sentences = _sentence_spans(text)
    candidates = [
        *_parallel_candidates(text, sentences),
        *_synchronization_candidates(text, sentences),
        *_exclusive_candidates(text, sentences),
        *_loop_candidates(text, sentences),
        *_optional_candidates(text, sentences),
    ]
    evidence = _deduplicate(candidates)
    for index, item in enumerate(evidence, start=1):
        item["evidence_id"] = f"CE{index}"

    summary: Dict[str, List[str]] = {}
    for classification in _CLASSIFICATIONS:
        kinds = {
            item["control_kind"]
            for item in evidence
            if item["classification"] == classification
        }
        summary[f"{classification}_control_kinds"] = [
            kind for kind in _CONTROL_KINDS if kind in kinds
        ]
    return {
        "schema_version": "1.0",
        "evidence": evidence,
        "summary": summary,
    }


__all__ = ["ControlEvidenceReport", "extract_control_evidence"]
