from __future__ import annotations

import pytest

from llm.control_evidence import extract_control_evidence


def _matches(report: dict, kind: str, classification: str) -> list[dict]:
    return [
        item
        for item in report["evidence"]
        if item["control_kind"] == kind
        and item["classification"] == classification
    ]


def _assert_original_spans(text: str, report: dict) -> None:
    for evidence in report["evidence"]:
        spans = [
            evidence["source_span"],
            evidence["cue_span"],
            *evidence["activity_spans"],
        ]
        if evidence["continuation_span"] is not None:
            spans.append(evidence["continuation_span"])
        for span in spans:
            assert text[span["start"] : span["end"]] == span["text"]


@pytest.mark.parametrize(
    "text",
    [
        "A and B happen at the same time.",
        "A is processed while B is reviewed.",
        "Meanwhile, B is performed while A continues.",
        "A is processed. In the meantime, B is reviewed.",
        "A is processed, and meantime B is reviewed.",
    ],
)
def test_extracts_high_confidence_parallel_from_two_overlapping_activities(
    text: str,
) -> None:
    report = extract_control_evidence(text)

    assert _matches(report, "parallel", "high_confidence")
    _assert_original_spans(text, report)


@pytest.mark.parametrize(
    ("text", "expected_classification"),
    [
        ("While the file remains open, A is performed.", "ambiguous"),
        ("Meanwhile, the system remains idle.", "ambiguous"),
    ],
)
def test_temporal_context_without_two_activities_is_not_high_confidence_parallel(
    text: str,
    expected_classification: str,
) -> None:
    report = extract_control_evidence(text)

    assert not _matches(report, "parallel", "high_confidence")
    assert _matches(report, "parallel", expected_classification)


def test_single_activity_with_strong_temporal_cue_is_supporting_only() -> None:
    report = extract_control_evidence("In the meantime, B is processed.")

    assert not _matches(report, "parallel", "high_confidence")
    assert _matches(report, "parallel", "supporting")


@pytest.mark.parametrize(
    "text",
    [
        "During this period, the system waits.",
        "A is processed. B is reviewed.",
        "Two clerks process the request.",
    ],
)
def test_non_concurrent_wording_does_not_create_parallel_evidence(text: str) -> None:
    report = extract_control_evidence(text)

    assert not _matches(report, "parallel", "high_confidence")


@pytest.mark.parametrize(
    "text",
    [
        "After both A and B are completed, continue with C.",
        "Once both activities finish, proceed.",
        "Only after all checks complete, perform C.",
    ],
)
def test_extracts_high_confidence_synchronization_barriers(text: str) -> None:
    report = extract_control_evidence(text)

    matches = _matches(report, "synchronization", "high_confidence")
    assert matches
    assert matches[0]["continuation_span"] is not None


@pytest.mark.parametrize(
    "text",
    [
        "A is completed and B is reviewed.",
        "Once all files are ready, distribute the list.",
    ],
)
def test_actions_or_objects_without_activity_completion_barrier_are_not_synchronization(
    text: str,
) -> None:
    report = extract_control_evidence(text)

    assert not _matches(report, "synchronization", "high_confidence")


@pytest.mark.parametrize(
    "text",
    [
        "If the request is valid, approve it; otherwise, reject it.",
        "Either approve the request or reject it.",
    ],
)
def test_extracts_high_confidence_exclusive_alternatives(text: str) -> None:
    assert _matches(extract_control_evidence(text), "exclusive", "high_confidence")


def test_contextual_if_is_not_high_confidence_exclusive() -> None:
    report = extract_control_evidence(
        "If the file remains open, the status is visible."
    )

    assert not _matches(report, "exclusive", "high_confidence")


@pytest.mark.parametrize(
    "text",
    [
        "Repeat the check until it passes.",
        "Retry the review and recheck the result.",
        "The file is sent back for correction and checked again.",
    ],
)
def test_extracts_high_confidence_loop_with_identifiable_body(text: str) -> None:
    assert _matches(extract_control_evidence(text), "loop", "high_confidence")


def test_isolated_again_is_ambiguous_loop_evidence() -> None:
    report = extract_control_evidence("Again, the status is visible.")

    assert not _matches(report, "loop", "high_confidence")
    assert _matches(report, "loop", "ambiguous")


@pytest.mark.parametrize(
    "text",
    [
        "For new patients, create a new file.",
        "If required, perform the review.",
        "When necessary, conduct the examination.",
    ],
)
def test_extracts_high_confidence_optional_applicability(text: str) -> None:
    assert _matches(extract_control_evidence(text), "optional", "high_confidence")


@pytest.mark.parametrize(
    "text",
    [
        "If the file is open, the status is visible.",
        "The request may not be valid.",
    ],
)
def test_context_or_unqualified_modal_is_not_high_confidence_optional(text: str) -> None:
    assert not _matches(
        extract_control_evidence(text), "optional", "high_confidence"
    )


def test_report_is_deterministic_qualitative_and_source_grounded() -> None:
    text = "  A is processed while B is reviewed.\nIf required, perform C."

    first = extract_control_evidence(text)
    second = extract_control_evidence(text)

    assert first == second
    assert first["schema_version"] == "1.0"
    assert [item["evidence_id"] for item in first["evidence"]] == ["CE1", "CE2"]
    assert all(
        item["classification"] in {"high_confidence", "supporting", "ambiguous"}
        for item in first["evidence"]
    )
    assert all("confidence" not in item for item in first["evidence"])
    assert first["evidence"] == sorted(
        first["evidence"],
        key=lambda item: (
            item["source_span"]["start"],
            item["control_kind"],
            item["detector_id"],
        ),
    )
    _assert_original_spans(text, first)


def test_report_uses_only_approved_control_kinds_and_summary_order() -> None:
    text = (
        "A is processed while B is reviewed. "
        "After both A and B are completed, continue with C. "
        "Either approve or reject it. Repeat the check until accepted. "
        "If required, perform an audit."
    )

    report = extract_control_evidence(text)

    assert {item["control_kind"] for item in report["evidence"]} <= {
        "parallel",
        "synchronization",
        "exclusive",
        "loop",
        "optional",
    }
    assert report["summary"]["high_confidence_control_kinds"] == [
        "parallel",
        "synchronization",
        "exclusive",
        "loop",
        "optional",
    ]
