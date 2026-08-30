from __future__ import annotations

import pytest

from llm.control_completeness_guard import extract_control_requirements


def _kinds(text: str) -> list[str]:
    return [item["required_topology_kind"] for item in extract_control_requirements(text)]


@pytest.mark.parametrize(
    "text",
    [
        "The clerk reviews the request and the manager checks the record simultaneously.",
        "The clerk reviews the request and the manager checks the record in parallel.",
        "The clerk reviews the request and the manager checks the record at the same time.",
    ],
)
def test_explicit_two_action_parallel_is_binding(text: str) -> None:
    assert _kinds(text) == ["parallel"]


@pytest.mark.parametrize(
    "text",
    [
        "If the request is valid, the clerk approves it; otherwise, the clerk rejects it.",
        "If the request is valid, the clerk approves it; else, the clerk rejects it.",
        "If required, perform the audit.",
        "If necessary, conduct the review.",
    ],
)
def test_explicit_actionable_decision_is_binding(text: str) -> None:
    assert _kinds(text) == ["decision"]


@pytest.mark.parametrize(
    "text",
    [
        "Repeat the check until it passes.",
        "Retry the review until it is approved.",
        "Recheck the record until it is valid.",
    ],
)
def test_explicit_body_and_behavioral_exit_loop_is_binding(text: str) -> None:
    assert _kinds(text) == ["loop"]


@pytest.mark.parametrize(
    "text",
    [
        "Alice and Bob are informed at the same time.",
        "The file and report are processed simultaneously.",
        "A is processed while B is reviewed.",
        "Meanwhile, B is reviewed.",
        "In the meantime, B is reviewed.",
        "During this period, B is reviewed.",
        "A is reviewed. B is checked at the same time.",
        "Two clerks review the request simultaneously.",
        "The clerk reviews it and it is archived simultaneously.",
        "The simultaneously processed files and reviewed reports are archived.",
        "The clerk reviews and checks the file simultaneously.",
        "The clerk reviews the request and the manager checks whether they occurred at the same time.",
        "The clerk reviews the schedule and the manager checks that both meetings start at the same time.",
    ],
)
def test_ambiguous_parallel_wording_is_non_binding(text: str) -> None:
    assert "parallel" not in _kinds(text)


@pytest.mark.parametrize(
    "text",
    [
        "Either approve the request or reject it.",
        "If the file is open, the status is visible; otherwise, the status is hidden.",
        "The clerk notes that, if required, perform the audit.",
        "If required, display the current status.",
        "If the request is valid, approve it. If the request is not valid, reject it.",
    ],
)
def test_ambiguous_decision_wording_is_non_binding(text: str) -> None:
    assert "decision" not in _kinds(text)


@pytest.mark.parametrize(
    "text",
    [
        "Repeat.",
        "Recheck.",
        "Check the record again.",
        "Wait until approved.",
        "The office remains open until Friday.",
        "Retry it until approved.",
        "Repeat this check until it passes.",
        "Repeat the previous step until it is approved.",
        "Do not repeat the check until it passes.",
        "You should not repeat the check until it passes.",
        "Until approved, the request remains pending.",
    ],
)
def test_incomplete_or_temporal_loop_wording_is_non_binding(text: str) -> None:
    assert "loop" not in _kinds(text)


def test_standalone_synchronization_is_non_binding() -> None:
    assert extract_control_requirements(
        "After both A and B are completed, continue with C."
    ) == []


def test_requirements_are_deterministic_minimal_and_source_grounded() -> None:
    text = (
        "  The clerk reviews A and the manager checks B simultaneously.\n"
        "If required, perform C. Repeat the check until it passes."
    )

    first = extract_control_requirements(text)
    second = extract_control_requirements(text)

    assert first == second
    assert [item["requirement_id"] for item in first] == ["MCG1", "MCG2", "MCG3"]
    assert [item["required_topology_kind"] for item in first] == [
        "parallel",
        "decision",
        "loop",
    ]
    assert all(
        set(item) == {
            "requirement_id",
            "detector_id",
            "source_span",
            "required_topology_kind",
        }
        for item in first
    )
    assert all(
        text[item["source_span"]["start"] : item["source_span"]["end"]]
        == item["source_span"]["text"]
        for item in first
    )
