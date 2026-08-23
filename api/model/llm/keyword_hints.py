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

_PARALLEL_CUE_PATTERNS = (
    ("simultaneously", r"\bsimultaneously\b"),
    ("in_parallel", r"\bin\s+parallel\b"),
    ("concurrently", r"\bconcurrently\b"),
    ("concurrent_activities", r"\b(?:two|three|multiple|several|\d+)\s+concurrent\s+(?:activities|tasks|operations)\b"),
    ("at_the_same_time", r"\bat\s+the\s+same\s+time\b"),
    ("in_the_meantime", r"\bin\s+the\s+meantime\b"),
    ("meantime", r"\bmeantime\b"),
    ("meanwhile", r"\bmeanwhile\b"),
    ("while", r"\bwhile\b"),
)

_EXECUTABLE_ACTIVITY_STEMS = (
    "accept",
    "add",
    "adjust",
    "analy",
    "assembl",
    "assign",
    "back-order",
    "calculat",
    "captur",
    "check",
    "collect",
    "communicat",
    "compil",
    "comput",
    "configur",
    "conduct",
    "creat",
    "deliver",
    "determin",
    "distribut",
    "do",
    "enable",
    "enter",
    "execut",
    "fetch",
    "formulat",
    "gather",
    "hand",
    "import",
    "inform",
    "inspect",
    "investigat",
    "mail",
    "notif",
    "order",
    "perform",
    "plan",
    "post",
    "prepar",
    "process",
    "provision",
    "put",
    "readi",
    "receiv",
    "record",
    "repair",
    "report",
    "repeat",
    "review",
    "reserv",
    "send",
    "sign",
    "start",
    "store",
    "test",
    "track",
    "transmit",
    "type",
    "undertak",
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


_WORKSTREAM_STOPWORDS = {
    "a", "all", "an", "and", "are", "as", "at", "be", "before", "both", "by", "each",
    "for", "from", "has", "have", "in", "is", "it", "of", "on", "or", "the", "then", "this",
    "same", "to", "two", "when", "while", "with",
}


def _workstream_tokens(value: str) -> set[str]:
    tokens: set[str] = set()
    for raw_token in re.findall(r"[a-z][a-z-]*", value.lower()):
        token = raw_token
        for suffix in ("ing", "ed", "es", "s"):
            if token.endswith(suffix) and len(token) > len(suffix) + 3:
                token = token[: -len(suffix)]
                break
        if token not in _WORKSTREAM_STOPWORDS and len(token) > 2:
            tokens.add(token)
    return tokens


def _distinct_executable_workstreams(first: str, second: str) -> bool:
    if not (_has_executable_activity(first) and _has_executable_activity(second)):
        return False
    first_tokens = _workstream_tokens(first)
    second_tokens = _workstream_tokens(second)
    return bool(first_tokens - second_tokens and second_tokens - first_tokens)


def _candidate_activity_clauses(text: str) -> List[str]:
    normalized = " ".join(text.split()).strip(" ,")
    raw_clauses = re.split(
        r"[.;]|,\s*(?:and\s+)?|\b(?:first|second|third)\s+activity\b|\b(?:i|ii|iii)\)",
        normalized,
        flags=re.IGNORECASE,
    )
    clauses = [clause.strip(" ,:-") for clause in raw_clauses if _has_executable_activity(clause)]
    distinct: List[str] = []
    for clause in clauses:
        if any(_workstream_tokens(clause) == _workstream_tokens(existing) for existing in distinct):
            continue
        distinct.append(clause)
    return distinct


def _nearest_executable_sentence(sentences: List[str], index: int) -> str:
    for previous_index in range(index - 1, max(-1, index - 3), -1):
        if _has_executable_activity(sentences[previous_index]):
            return sentences[previous_index]
    return ""


def _resolve_anaphoric_workstream(sentences: List[str], index: int, workstream: str) -> str:
    if not re.match(r"\s*(?:this|that|it)\s+(?:procedure|process|activity|work)\b", workstream, re.IGNORECASE):
        return workstream
    for previous_index in range(index - 2, max(-1, index - 6), -1):
        candidate = sentences[previous_index]
        if re.match(r"\s*(?:if|otherwise|this|that|it)\b", candidate, re.IGNORECASE):
            continue
        if _has_executable_activity(candidate):
            return f"{candidate} {workstream}"
    return workstream


def _synchronization_matches(window: str) -> List[str]:
    patterns = (
        r"\b(?:after|once|when|as\s+soon\s+as)\b[^.]{0,180}\b(?:both|all|two|three|first\s+and\s+second)\b[^.]{0,120}\b(?:complet\w*|finish\w*|done|ready|taken\s+place)\b",
        r"\bif\b[^.]{0,180}\b(?:all|every)\b[^.]{0,160}\band\b[^.]{0,120}\b(?:complet\w*|finish\w*|done|ready)\b",
        r"\bmeetings?\s+of\s+the\s+first\s+and\s+second\b[^.]{0,160}\b(?:taken\s+place|complet\w*|finish\w*)\b",
    )
    return [match.group(0).strip() for pattern in patterns for match in re.finditer(pattern, window, re.IGNORECASE)]


def _synchronization_evidence(sentences: List[str], index: int) -> List[str]:
    return _synchronization_matches(" ".join(sentences[index : min(len(sentences), index + 4)]))


def _post_split_synchronization_evidence(sentences: List[str], index: int, offset: int) -> List[str]:
    post_cue_window = " ".join(
        [sentences[index][offset:], *sentences[index + 1 : min(len(sentences), index + 4)]]
    )
    evidence = _synchronization_matches(post_cue_window)
    if _has_multi_output_synchronization(_normalize_process_text(post_cue_window)):
        evidence.append("multiple_outputs_synchronized_before_continuation")
    if index + 1 < len(sentences):
        continuation = sentences[index + 1]
        if re.match(r"\s*(?:afterwards|subsequently|after\s+that|thereafter)\b", continuation, re.IGNORECASE) and _has_executable_activity(continuation):
            evidence.append(f"shared_continuation: {continuation}")
    return evidence


def _all_synchronization_evidence(sentences: List[str]) -> List[str]:
    return _synchronization_matches(" ".join(sentences))


def _named_workstreams_for_synchronization(sentences: List[str], index: int) -> tuple[str, str] | None:
    synchronization_sentence = sentences[index]
    named_pair = re.search(
        r"\b(?:meetings?|activities|tasks|work)\s+of\s+the\s+(first)\s+and\s+(second)\s+([a-z][a-z-]*)",
        synchronization_sentence,
        re.IGNORECASE,
    )
    if named_pair is None:
        return None

    first_name = f"{named_pair.group(1)} {named_pair.group(3)}".lower()
    second_name = f"{named_pair.group(2)} {named_pair.group(3)}".lower()
    preceding = sentences[max(0, index - 12) : index]
    first_workstream = next(
        (sentence for sentence in reversed(preceding) if first_name in sentence.lower() and _has_executable_activity(sentence)),
        "",
    )
    second_workstream = next(
        (sentence for sentence in reversed(preceding) if second_name in sentence.lower() and _has_executable_activity(sentence)),
        "",
    )
    if not _distinct_executable_workstreams(first_workstream, second_workstream):
        return None
    return first_workstream, second_workstream


def _parallel_candidate(
    *,
    source_fragment: str,
    workstream_a: str,
    workstream_b: str,
    concurrency_cue: str,
    synchronization_evidence: List[str],
) -> Dict[str, Any] | None:
    if not _distinct_executable_workstreams(workstream_a, workstream_b):
        return None
    return {
        "source_fragment": " ".join(source_fragment.split()),
        "workstream_a": " ".join(workstream_a.split()).strip(" ,"),
        "workstream_b": " ".join(workstream_b.split()).strip(" ,"),
        "concurrency_cue": concurrency_cue,
        "expected_scope": "local scope containing both workstreams before any shared continuation",
        "synchronization_evidence": synchronization_evidence,
    }


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


def _arbitrary_order_workstreams(text: str) -> tuple[str, str] | None:
    match = re.search(
        r"\bfirst\s+activity\s+([^.;]+?)\s+and\s+(?:the\s+)?second\s+([^.;]+)",
        text,
        re.IGNORECASE,
    )
    if match is None or not _distinct_executable_workstreams(match.group(1), match.group(2)):
        return None
    return match.group(1), match.group(2)


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


def extract_parallel_evidence_contract(process_text: str) -> Dict[str, Any]:
    """Extract scoped parallel-split evidence without inferring synchronization."""
    sentences = _sentences(process_text)
    normalized_text = _normalize_process_text(process_text)
    weak_cues = _matched_signal_labels(normalized_text, _PARALLEL_CUE_PATTERNS)
    candidates: List[Dict[str, Any]] = []

    for index, sentence in enumerate(sentences):
        synchronization = _synchronization_evidence(sentences, index)

        named_workstreams = _named_workstreams_for_synchronization(sentences, index)
        if synchronization and named_workstreams:
            candidate = _parallel_candidate(
                source_fragment=" ".join((*named_workstreams, sentence)),
                workstream_a=named_workstreams[0],
                workstream_b=named_workstreams[1],
                concurrency_cue="shared_completion_dependency",
                synchronization_evidence=synchronization,
            )
            if candidate:
                candidates.append(candidate)

        for cue, marker_pattern in _PARALLEL_CUE_PATTERNS:
            if cue == "while":
                continue
            for match in re.finditer(marker_pattern, sentence, re.IGNORECASE):
                marker_synchronization = _post_split_synchronization_evidence(sentences, index, match.end())
                if cue == "concurrent_activities":
                    following = " ".join(sentences[index + 1 : min(len(sentences), index + 3)])
                    source_after_cue = " ".join((sentence[match.end() :], following))
                    clauses = _candidate_activity_clauses(source_after_cue)
                    if len(clauses) < 2:
                        continue
                    candidate = _parallel_candidate(
                        source_fragment=f"{sentence} {following}",
                        workstream_a=clauses[0],
                        workstream_b=clauses[1],
                        concurrency_cue=cue,
                        synchronization_evidence=marker_synchronization,
                    )
                    if candidate:
                        candidates.append(candidate)
                    continue
                left = sentence[: match.start()].strip(" ,") or _nearest_executable_sentence(sentences, index)
                left = _resolve_anaphoric_workstream(sentences, index, left)
                right = sentence[match.end() :].strip(" ,:-")
                clauses = _candidate_activity_clauses(right if not left else f"{left}. {right}")
                if left and right and _distinct_executable_workstreams(left, right):
                    workstream_a, workstream_b = left, right
                elif len(clauses) >= 2:
                    workstream_a, workstream_b = clauses[0], clauses[1]
                else:
                    continue
                fragment = " ".join(
                    part for part in (_nearest_executable_sentence(sentences, index), sentence) if part
                )
                candidate = _parallel_candidate(
                    source_fragment=fragment or sentence,
                    workstream_a=workstream_a,
                    workstream_b=workstream_b,
                    concurrency_cue=cue,
                    synchronization_evidence=marker_synchronization,
                )
                if candidate:
                    candidates.append(candidate)

        for match in re.finditer(r"\bwhile\s+([^,.;]+),\s*([^.;]+)", sentence, re.IGNORECASE):
            candidate = _parallel_candidate(
                source_fragment=sentence,
                workstream_a=match.group(1),
                workstream_b=match.group(2),
                concurrency_cue="while",
                synchronization_evidence=_post_split_synchronization_evidence(sentences, index, match.start()),
            )
            if candidate:
                candidates.append(candidate)

    compound_checks = (
        ("multiple_activities_in_arbitrary_order", _has_arbitrary_order_concurrency),
        ("multiple_outputs_synchronized_before_continuation", _has_multi_output_synchronization),
    )
    for cue, detector in compound_checks:
        if candidates:
            break
        if not detector(normalized_text):
            continue
        named_workstreams = _arbitrary_order_workstreams(process_text) if cue == "multiple_activities_in_arbitrary_order" else None
        if named_workstreams:
            workstream_a, workstream_b = named_workstreams
        else:
            clauses = _candidate_activity_clauses(process_text)
            if len(clauses) < 2:
                continue
            workstream_a, workstream_b = clauses[0], clauses[1]
        synchronization = _all_synchronization_evidence(sentences)
        if cue == "multiple_outputs_synchronized_before_continuation":
            synchronization.append(cue)
        candidate = _parallel_candidate(
            source_fragment=process_text,
            workstream_a=workstream_a,
            workstream_b=workstream_b,
            concurrency_cue=cue,
            synchronization_evidence=synchronization,
        )
        if candidate:
            candidates.append(candidate)

    deduplicated: List[Dict[str, Any]] = []
    seen: set[tuple[str, frozenset[frozenset[str]]]] = set()
    for candidate in candidates:
        key = (
            candidate["concurrency_cue"],
            frozenset(
                {
                    frozenset(_workstream_tokens(candidate["workstream_a"])),
                    frozenset(_workstream_tokens(candidate["workstream_b"])),
                }
            ),
        )
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(candidate)

    return {
        "high_confidence": bool(deduplicated),
        "weak_cues": weak_cues,
        "candidates": deduplicated,
    }


def extract_parallel_evidence(process_text: str) -> List[str]:
    """Return backward-compatible labels for high-confidence parallel evidence."""
    contract = extract_parallel_evidence_contract(process_text)
    return list(dict.fromkeys(candidate["concurrency_cue"] for candidate in contract["candidates"]))


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


__all__ = [
    "KeywordHints",
    "extract_keyword_hints",
    "extract_loop_evidence",
    "extract_parallel_evidence",
    "extract_parallel_evidence_contract",
]
