from __future__ import annotations

import json

import pytest
from unittest.mock import patch

from llm.topology_experiment import (
    TopologyArtifactGenerationError,
    _build_topology_correction_prompt,
    _has_explicit_sentence_level_disjunction,
    _normalize_text,
    _validate_topology_artifact_against_process_text,
    build_topology_experiment_prompt,
    generate_topology_artifact,
    parse_topology_artifact_json,
)
from llm.keyword_hints import (
    extract_keyword_hints,
    extract_loop_evidence,
    extract_parallel_evidence_contract,
)
from llm.topology_artifact_model import TopologyArtifact


def test_parse_topology_artifact_json_canonicalizes_retry_to_loop() -> None:
    raw_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "parallel",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["budget_review", "supplier_review"]
        },
        {
          "id": "T2",
          "type": "retry",
          "parent": "T1",
          "parent_branch": "budget_review",
          "branches": ["retry", "success"],
          "purpose": "repeat budget review until it succeeds"
        }
      ]
    }
    """

    artifact = parse_topology_artifact_json(raw_output)

    assert artifact["structures"][1]["type"] == "loop"


def test_parse_topology_artifact_json_keeps_existing_control_types() -> None:
    raw_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["approved", "rejected"]
        },
        {
          "id": "T2",
          "type": "parallel",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["track_a", "track_b"]
        },
        {
          "id": "T3",
          "type": "loop",
          "parent": "T2",
          "parent_branch": "track_a",
          "branches": ["retry", "success"]
        }
      ]
    }
    """

    artifact = parse_topology_artifact_json(raw_output)

    assert [structure["type"] for structure in artifact["structures"]] == [
        "decision",
        "parallel",
        "loop",
    ]


def test_build_topology_experiment_prompt_requires_explicit_evidence_for_control_structures() -> None:
    prompt = build_topology_experiment_prompt(
        "A request is submitted, reviewed, approved, and then archived.",
    )

    assert "Do not infer a decision from a single terminal status word such as `approved`, `rejected`, `archived`, `ready`, `blocked`" in prompt
    assert "If the process text is linear, keep the topology linear and return `structures: []`" in prompt
    assert "Create a loop only for a complete repetition contract" in prompt
    assert "Create a parallel block only when the text explicitly indicates concurrent work" in prompt
    assert "Compound concurrency evidence can include separate executable activities linked by `in the meantime`" in prompt
    assert "Treat `again`, `re-check`, `review again`, `retry`, and `resubmit` as weak cues only" in prompt


@pytest.mark.parametrize(
    "process_text",
    [
        "Finally, the order is checked again for quality.",
        "The clerk re-checks the completed record.",
        "The board reviews the approved invoice again under the four-eyes principle.",
        "The applicant resubmits the missing document.",
        "Operations reviews the request. Later, finance reviews the payment.",
    ],
)
def test_extract_loop_evidence_keeps_weak_repetition_wording_non_cyclic(process_text: str) -> None:
    evidence = extract_loop_evidence(process_text)

    assert evidence["high_confidence"] is False
    assert evidence["candidates"] == []


def test_extract_loop_evidence_accepts_bounded_iteration_with_region_unit_and_completion() -> None:
    evidence = extract_loop_evidence(
        "The storehouse checks availability and reserves or back-orders a part. "
        "This procedure is repeated for each item on the part list. "
        "When every item is handled, assembly begins."
    )

    assert evidence["high_confidence"] is True
    candidate = evidence["candidates"][0]
    assert candidate["kind"] == "bounded_iteration"
    assert candidate["iteration_unit"] == "each item on the part list"
    assert "procedure is repeated" in candidate["repeated_operation"]
    assert candidate["completion_evidence"]


def test_extract_loop_evidence_accepts_complete_retry_correction_contract() -> None:
    evidence = extract_loop_evidence(
        "The clerk checks the form. If it is incomplete, the applicant updates it and submits it again "
        "to the previous validation step. If it is complete, processing continues."
    )

    assert evidence["high_confidence"] is True
    candidate = evidence["candidates"][0]
    assert candidate["kind"] == "retry_cycle"
    assert candidate["retry_condition"] == ["incomplete"]
    assert candidate["corrective_operation"]
    assert candidate["return_or_reexecution_evidence"]
    assert candidate["successful_exit_evidence"]


def test_extract_loop_evidence_does_not_treat_check_each_item_once_as_iteration() -> None:
    evidence = extract_loop_evidence("The clerk checks each item once and archives the list.")

    assert evidence["high_confidence"] is False


@pytest.mark.parametrize(
    "process_text",
    [
        "If the claim is Not OK, it is sent back to the claims officer and the recommendation is repeated. If it is OK, processing proceeds.",
        "If no response is received, another reminder is sent and so on until the completed questionnaire is received.",
        "If receipts are missing, the report is sent back to the employee. A report returned to the employee for corrections must again go to the supervisor. If accepted, processing continues.",
        "The manager must ask for corrections again; otherwise, the manager approves the description.",
    ],
)
def test_extract_loop_evidence_preserves_existing_explicit_cycle_forms(process_text: str) -> None:
    assert extract_loop_evidence(process_text)["high_confidence"] is True


def _loop_artifact(*, purpose: str = "repeat form correction until complete") -> dict:
    return {
        "structures": [
            {
                "id": "T1",
                "type": "loop",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["retry", "success"],
                "purpose": purpose,
            }
        ]
    }


def test_validate_topology_rejects_missing_high_confidence_loop() -> None:
    process_text = (
        "If the form is incomplete, the applicant corrects it and sends it back to validation. "
        "If the form is complete, processing continues."
    )

    with pytest.raises(ValueError, match="missing loop structure for high-confidence repetition evidence"):
        _validate_topology_artifact_against_process_text(
            process_text=process_text,
            topology_artifact={"structures": []},
        )


def test_generate_topology_retries_for_missing_high_confidence_loop_with_narrow_diagnostics() -> None:
    process_text = (
        "If the form is incomplete, the applicant corrects it and sends it back to validation. "
        "If the form is complete, processing continues."
    )
    with patch(
        "llm.topology_experiment.call_openai",
        side_effect=['{"structures": []}', '''
        {"structures": [{"id": "T1", "type": "loop", "parent": "ROOT", "parent_branch": null,
        "branches": ["retry", "success"], "purpose": "correct the form until complete"}]}
        '''],
    ) as mocked_call:
        result = generate_topology_artifact(process_text)

    assert result["artifact"]["structures"][0]["type"] == "loop"
    assert len(result["planner_attempts"]) == 2
    retry_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "missing loop structure for high-confidence repetition evidence" in retry_prompt
    assert "corrective_operation" in retry_prompt
    assert "return_or_reexecution_evidence" in retry_prompt
    assert "successful_exit_evidence" in retry_prompt
    assert "root_scope_" not in str(result)


def test_generate_topology_does_not_retry_for_ambiguous_weak_loop_wording() -> None:
    with patch("llm.topology_experiment.call_openai", return_value='{"structures": []}') as mocked_call:
        result = generate_topology_artifact("Finally, the order is checked again for quality.")

    assert result["artifact"] == {"structures": []}
    assert len(result["planner_attempts"]) == 1
    assert mocked_call.call_count == 1


def test_generate_topology_retries_to_remove_loop_supported_only_by_weak_cue() -> None:
    invalid_output = '''
    {"structures": [{"id": "T1", "type": "loop", "parent": "ROOT", "parent_branch": null,
    "branches": ["retry", "success"], "purpose": "check order quality again"}]}
    '''
    with patch(
        "llm.topology_experiment.call_openai",
        side_effect=[invalid_output, '{"structures": []}'],
    ) as mocked_call:
        result = generate_topology_artifact("Finally, the order is checked again for quality.")

    assert result["artifact"] == {"structures": []}
    assert len(result["planner_attempts"]) == 2
    retry_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "only weak lexical loop cues" in retry_prompt
    assert "again" in retry_prompt


def test_topology_schema_is_unchanged_by_loop_evidence_diagnostics() -> None:
    structure_schema = TopologyArtifact.model_json_schema()["$defs"]["TopologyStructure"]

    assert set(structure_schema["properties"]) == {
        "id",
        "type",
        "parent",
        "parent_branch",
        "branches",
        "purpose",
    }


def test_generate_topology_artifact_rejects_unsupported_linear_decision_chain() -> None:
    raw_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["approved", "rejected"],
          "purpose": "approval decision"
        },
        {
          "id": "T2",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["ready", "blocked"],
          "purpose": "readiness decision"
        }
      ]
    }
    """

    with patch("llm.topology_experiment.call_openai", return_value=raw_output):
        with pytest.raises(TopologyArtifactGenerationError, match="unsupported control structures"):
            generate_topology_artifact(
                "A request is submitted, reviewed, approved, and then archived.",
                model="gpt-4o",
            )


def test_generate_topology_artifact_retries_after_validation_failure() -> None:
    invalid_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["approved", "rejected"],
          "purpose": "approval decision"
        }
      ]
    }
    """
    valid_output = """
    {
      "structures": []
    }
    """

    with patch("llm.topology_experiment.call_openai", side_effect=[invalid_output, valid_output]) as mocked_call:
        result = generate_topology_artifact(
            "A request is submitted, reviewed, approved, and then archived.",
            model="gpt-4o",
        )

    assert result["artifact"] == {"structures": []}
    assert len(result["planner_attempts"]) == 2
    retry_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "This is correction attempt 1." in retry_prompt
    assert "Unsupported structure ids" in retry_prompt
    assert "T1" in retry_prompt
    assert "missing explicit branching evidence" in retry_prompt


def test_generate_topology_artifact_retry_exhaustion_returns_clear_failure() -> None:
    invalid_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["approved", "rejected"],
          "purpose": "approval decision"
        }
      ]
    }
    """

    with patch("llm.topology_experiment.call_openai", side_effect=[invalid_output, invalid_output, invalid_output]):
        with pytest.raises(TopologyArtifactGenerationError, match="unsupported control structures") as exc_info:
            generate_topology_artifact(
                "A request is submitted, reviewed, approved, and then archived.",
                model="gpt-4o",
            )

    assert len(exc_info.value.debug_artifacts["topology_attempts"]) == 3
    assert "unsupported_structures" in exc_info.value.debug_artifacts["topology_validation_error"]


def test_build_topology_experiment_prompt_covers_sentence_level_disjunction_and_shared_post_branch_scope() -> None:
    prompt = build_topology_experiment_prompt(
        "An employee rejects the application or confirms it. Based on the outcome, the clerk sends the form. Once the form is returned, it is checked again.",
    )

    assert 'Treat a sentence-level exclusive disjunction such as "rejects ... or confirms ..."' in prompt
    assert "model the later control structure after convergence rather than duplicating it inside each branch" in prompt


@pytest.mark.parametrize(
    "process_text",
    [
        "An employee reject the application or confirm it.",
        "An employee rejects the application or confirms it.",
        "The application is rejected or confirmed by the employee.",
        "The GO rejects the application of the MSPN or the GO confirmes the application of the MSPN.",
    ],
)
def test_sentence_level_exclusive_disjunction_detector_handles_morphological_variants(process_text: str) -> None:
    assert _has_explicit_sentence_level_disjunction(_normalize_text(process_text)) is True


@pytest.mark.parametrize(
    "process_text",
    [
        "An employee reject the application or confirm it.",
        "An employee rejects the application or confirms it.",
        "The application is rejected or confirmed by the employee.",
        "The GO rejects the application of the MSPN or the GO confirmes the application of the MSPN.",
    ],
)
def test_extract_keyword_hints_detects_sentence_level_exclusive_disjunction_variants(process_text: str) -> None:
    hints = extract_keyword_hints(process_text)

    assert hints["flags"]["possible_decision"] is True
    assert hints["flags"]["approval_flow"] is True
    assert any(hint["kind"] == "possible_decision" for hint in hints["hints"])


def _parallel_artifact(*, parent: str = "ROOT", parent_branch: str | None = None, branches: list[str] | None = None) -> dict:
    return {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": parent,
                "parent_branch": parent_branch,
                "branches": branches or ["track_a", "track_b"],
                "purpose": "perform independent work before continuing",
            }
        ]
    }


@pytest.mark.parametrize(
    ("process_text", "artifact"),
    [
        (
            "The warehouse checks every part. In the meantime, engineering prepares the assembly area. "
            "When the preparation work is complete, engineering assembles the product.",
            _parallel_artifact(branches=["warehouse", "engineering"]),
        ),
        (
            "While finance reviews the budget, legal checks the contract. Once both reviews are complete, "
            "the manager signs the agreement.",
            _parallel_artifact(branches=["finance", "legal"]),
        ),
        (
            "The repair consists of two activities, which are executed in an arbitrary order. "
            "The first activity repairs the hardware and the second configures the software. "
            "After the activities, the system is tested.",
            _parallel_artifact(branches=["hardware", "software"]),
        ),
        (
            "The kitchen prepares the food, the sommelier fetches the wine, and the waiter readies the cart. "
            "Once the food, wine, and cart are ready, the waiter delivers the order.",
            _parallel_artifact(branches=["kitchen", "sommelier", "waiter"]),
        ),
        (
            "If the order is accepted, the warehouse checks every part. In the meantime, engineering prepares "
            "the assembly area. After both activities finish, the bicycle is assembled. Otherwise, the order ends.",
            {
                "structures": [
                    {
                        "id": "T1",
                        "type": "decision",
                        "parent": "ROOT",
                        "parent_branch": None,
                        "branches": ["accepted", "rejected"],
                        "purpose": "decide whether to accept the order",
                    },
                    {
                        "id": "T2",
                        "type": "parallel",
                        "parent": "T1",
                        "parent_branch": "accepted",
                        "branches": ["warehouse", "engineering"],
                        "purpose": "prepare the accepted order independently",
                    },
                ]
            },
        ),
        (
            "Procurement orders materials, facilities prepares the workspace, and security enables access. "
            "Once the materials, workspace, and access are ready, production starts.",
            _parallel_artifact(branches=["procurement", "facilities", "security"]),
        ),
    ],
)
def test_parallel_evidence_accepts_only_strong_compound_concurrency(
    process_text: str,
    artifact: dict,
) -> None:
    hints = extract_keyword_hints(process_text)

    assert hints["flags"]["possible_parallelism"] is True
    assert hints["evidence"]["parallel_terms"]
    assert _validate_topology_artifact_against_process_text(
        process_text=process_text,
        topology_artifact=artifact,
    ) == artifact


@pytest.mark.parametrize(
    "process_text",
    [
        "The clerk receives the request, then reviews it, and then archives it.",
        "The clerk either approves the request or rejects it.",
        "While the request is pending, the clerk records its status.",
        "The clerk may review the form fields in any order before submitting the form.",
        "The clerk checks the request again and repeats the correction until it succeeds.",
        "If the request is accepted, finance reviews it; otherwise, the clerk rejects it.",
        "The request remains pending; meanwhile, its status is unchanged.",
        "Both activities are listed in the process documentation.",
    ],
)
def test_parallel_evidence_rejects_sequential_contextual_or_exclusive_text(process_text: str) -> None:
    hints = extract_keyword_hints(process_text)

    assert hints["flags"]["possible_parallelism"] is False
    with pytest.raises(ValueError, match="missing explicit concurrency or join evidence"):
        _validate_topology_artifact_against_process_text(
            process_text=process_text,
            topology_artifact=_parallel_artifact(),
        )


@pytest.mark.parametrize(
    ("process_text", "expected_cue"),
    [
        (
            "Two concurrent activities are triggered, i.e. i) Finance reviews the invoice, and "
            "ii) Legal checks the contract.",
            "concurrent_activities",
        ),
        (
            "Finance reviews the invoice. Concurrently, legal checks the contract.",
            "concurrently",
        ),
        (
            "Finance reviews the invoice. Meantime, legal checks the contract.",
            "meantime",
        ),
        (
            "Finance reviews the invoice. In the meantime, legal checks the contract.",
            "in_the_meantime",
        ),
        (
            "While finance reviews the invoice, legal checks the contract.",
            "while",
        ),
    ],
)
def test_parallel_evidence_contract_requires_two_executable_workstreams(
    process_text: str,
    expected_cue: str,
) -> None:
    evidence = extract_parallel_evidence_contract(process_text)

    assert evidence["high_confidence"] is True
    assert any(candidate["concurrency_cue"] == expected_cue for candidate in evidence["candidates"])
    assert all(candidate["workstream_a"] and candidate["workstream_b"] for candidate in evidence["candidates"])


@pytest.mark.parametrize(
    "process_text",
    [
        "While the request is pending, the clerk records its status.",
        "The request remains pending; meanwhile, its status is unchanged.",
        "The clerk receives the request, then reviews it, and then archives it.",
        "The process lists review and approval activities.",
        "The clerk either approves the request or rejects it.",
        "The clerk may review the form fields in any order before submitting the form.",
        "Meanwhile, the system sends an asynchronous notification.",
        "The activities are concurrent in the process documentation.",
        "The clerk reviews the request. Meanwhile, the clerk continues reviewing the same request.",
    ],
)
def test_weak_parallel_cues_do_not_trigger_missing_parallel(process_text: str) -> None:
    evidence = extract_parallel_evidence_contract(process_text)

    assert evidence["high_confidence"] is False
    try:
        _validate_topology_artifact_against_process_text(
            process_text=process_text,
            topology_artifact={"structures": []},
        )
    except ValueError as exc:
        assert "MISSING_PARALLEL" not in str(exc)


def test_strong_parallel_evidence_rejects_missing_parallel_topology() -> None:
    process_text = (
        "Finance reviews the invoice. In the meantime, legal checks the contract. "
        "After both reviews are complete, the manager signs the agreement."
    )

    with pytest.raises(ValueError, match="MISSING_PARALLEL"):
        _validate_topology_artifact_against_process_text(
            process_text=process_text,
            topology_artifact={"structures": []},
        )


def test_strong_parallel_evidence_rejects_unrelated_parallel_scope() -> None:
    process_text = (
        "Finance reviews the invoice. Meanwhile, legal checks the contract. "
        "After both reviews are complete, the manager signs the agreement."
    )
    unrelated_parallel = _parallel_artifact(branches=["warehouse", "engineering"])

    with pytest.raises(ValueError, match="MISSING_PARALLEL"):
        _validate_topology_artifact_against_process_text(
            process_text=process_text,
            topology_artifact=unrelated_parallel,
        )


def test_parallel_split_and_synchronization_evidence_are_separate() -> None:
    split_only = extract_parallel_evidence_contract(
        "Finance reviews the invoice. Meanwhile, legal checks the contract."
    )
    synchronized = extract_parallel_evidence_contract(
        "Finance reviews the invoice. Meanwhile, legal checks the contract. "
        "After both reviews are complete, the manager signs the agreement."
    )

    assert split_only["high_confidence"] is True
    assert all(not candidate["synchronization_evidence"] for candidate in split_only["candidates"])
    assert synchronized["high_confidence"] is True
    assert any(candidate["synchronization_evidence"] for candidate in synchronized["candidates"])


def test_missing_parallel_uses_existing_topology_correction_loop() -> None:
    process_text = (
        "Finance reviews the invoice. Meanwhile, legal checks the contract. "
        "After both reviews are complete, the manager signs the agreement."
    )
    corrected_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "parallel",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["finance", "legal"],
          "purpose": "review the invoice and contract concurrently"
        }
      ]
    }
    """

    with patch(
        "llm.topology_experiment.call_openai",
        side_effect=['{"structures": []}', corrected_output],
    ) as mocked_call:
        result = generate_topology_artifact(process_text, model="gpt-4o")

    assert mocked_call.call_count == 2
    assert "MISSING_PARALLEL" in result["planner_attempts"][0]["validation_error"]
    assert result["planner_attempts"][1]["validation_error"] is None
    assert result["artifact"]["structures"][0]["type"] == "parallel"


def test_parallel_evidence_does_not_change_topology_schema() -> None:
    artifact = parse_topology_artifact_json(
        '{"structures":[{"id":"T1","type":"parallel","parent":"ROOT",'
        '"parent_branch":null,"branches":["finance","legal"],"purpose":"parallel review"}]}'
    )

    assert set(artifact["structures"][0]) == {
        "id",
        "type",
        "parent",
        "parent_branch",
        "branches",
        "purpose",
    }
    assert "root_scope_" not in str(artifact)


def test_generate_topology_artifact_preserves_supported_nested_parallel_on_first_attempt() -> None:
    process_text = (
        "If the order is accepted, the warehouse checks every part. In the meantime, engineering prepares "
        "the assembly area. After both activities finish, the bicycle is assembled. Otherwise, the order ends."
    )
    raw_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["accepted", "rejected"],
          "purpose": "decide whether to accept the order"
        },
        {
          "id": "T2",
          "type": "parallel",
          "parent": "T1",
          "parent_branch": "accepted",
          "branches": ["warehouse", "engineering"],
          "purpose": "prepare the accepted order independently"
        }
      ]
    }
    """

    with patch("llm.topology_experiment.call_openai", return_value=raw_output) as mocked_call:
        result = generate_topology_artifact(process_text, model="gpt-4o")

    assert len(result["planner_attempts"]) == 1
    assert result["planner_attempts"][0]["validation_error"] is None
    assert result["artifact"]["structures"][1]["type"] == "parallel"
    assert mocked_call.call_count == 1


@pytest.mark.parametrize(
    ("process_text", "branches"),
    [
        ("An employee reject the application or confirm it.", ["rejected", "confirmed"]),
        ("An employee rejects the application or confirms it.", ["rejected", "confirmed"]),
        ("The application is rejected or confirmed by the employee.", ["rejected", "confirmed"]),
        (
            "The GO rejects the application of the MSPN or the GO confirmes the application of the MSPN.",
            ["rejected", "confirmed"],
        ),
    ],
)
def test_validate_topology_artifact_accepts_supported_sentence_level_exclusive_decisions(
    process_text: str,
    branches: list[str],
) -> None:
    artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": branches,
                "purpose": "determine the application outcome",
            }
        ]
    }

    validated = _validate_topology_artifact_against_process_text(
        process_text=process_text,
        topology_artifact=artifact,
    )

    assert validated == artifact


@pytest.mark.parametrize(
    "process_text",
    [
        "An employee reject the application or confirm it.",
        "An employee rejects the application or confirms it.",
        "The application is rejected or confirmed by the employee.",
        "The GO rejects the application of the MSPN or the GO confirmes the application of the MSPN.",
    ],
)
def test_validate_topology_artifact_rejects_empty_topology_for_supported_sentence_level_disjunctions(
    process_text: str,
) -> None:
    with pytest.raises(ValueError, match="missing decision structure for explicit branching evidence"):
        _validate_topology_artifact_against_process_text(
            process_text=process_text,
            topology_artifact={"structures": []},
        )


def test_correction_prompt_does_not_tell_model_to_remove_supported_sentence_level_decision() -> None:
    process_text = "The GO rejects the application of the MSPN or the GO confirmes the application of the MSPN."
    parsed_output = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["rejected", "confirmed"],
                "purpose": "determine whether the application is rejected or confirmed",
            }
        ]
    }

    _validate_topology_artifact_against_process_text(
        process_text=process_text,
        topology_artifact=parsed_output,
    )
    retry_prompt = _build_topology_correction_prompt(
        base_prompt="base prompt",
        process_text=process_text,
        invalid_topology_output='{"structures":[]}',
        parsed_topology_output={"structures": []},
        validation_error=(
            "TopologyArtifact contains unsupported control structures for the current process text. "
            "unsupported_structures=[{'id': 'MISSING_DECISION', 'type': 'decision', "
            "'reason': 'missing decision structure for explicit branching evidence', 'branches': [], 'structure': None}]"
        ),
        correction_attempt=1,
    )

    assert "missing decision structure for explicit branching evidence" in retry_prompt
    assert "Do not repeat unsupported control structures." in retry_prompt
    assert "missing explicit branching evidence in process text" not in retry_prompt


def test_generate_topology_artifact_retries_when_sentence_level_exclusive_disjunction_is_omitted() -> None:
    invalid_output = """
    {
      "structures": []
    }
    """
    valid_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["rejected", "confirmed"],
          "purpose": "determine the application outcome"
        }
      ]
    }
    """

    with patch("llm.topology_experiment.call_openai", side_effect=[invalid_output, valid_output]) as mocked_call:
        result = generate_topology_artifact(
            "An employee rejects the application or confirms it.",
            model="gpt-4o",
        )

    assert result["artifact"] == {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["rejected", "confirmed"],
                "purpose": "determine the application outcome",
            }
        ]
    }
    retry_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "missing decision structure for explicit branching evidence" in retry_prompt


def test_generate_topology_artifact_retries_when_shared_post_branch_control_is_duplicated() -> None:
    process_text = (
        "A clerk evaluates the claim as simple or complex. "
        "Based on the outcome, the clerk sends the relevant form. "
        "Once the form is returned, the clerk checks it for completeness. "
        "If information is missing, the clerk asks for updates and checks the form again. "
        "Otherwise, the clerk registers the claim."
    )
    invalid_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["simple", "complex"],
          "purpose": "determine claim complexity"
        },
        {
          "id": "T2",
          "type": "loop",
          "parent": "T1",
          "parent_branch": "simple",
          "branches": ["retry", "complete"],
          "purpose": "check form completeness for simple claims"
        },
        {
          "id": "T3",
          "type": "loop",
          "parent": "T1",
          "parent_branch": "complex",
          "branches": ["retry", "complete"],
          "purpose": "check form completeness for complex claims"
        }
      ]
    }
    """
    valid_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["simple", "complex"],
          "purpose": "determine claim complexity"
        },
        {
          "id": "T2",
          "type": "loop",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["retry", "complete"],
          "purpose": "check form completeness until the claim can be registered"
        }
      ]
    }
    """

    with patch("llm.topology_experiment.call_openai", side_effect=[invalid_output, valid_output]) as mocked_call:
        result = generate_topology_artifact(
            process_text,
            model="gpt-4o",
        )

    assert result["artifact"] == {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["simple", "complex"],
                "purpose": "determine claim complexity",
            },
            {
                "id": "T2",
                "type": "loop",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["retry", "complete"],
                "purpose": "check form completeness until the claim can be registered",
            },
        ]
    }
    retry_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "duplicate branch-local structures suggest a shared post-branch control region" in retry_prompt


def test_validate_topology_artifact_accepts_shared_post_branch_control_inside_outer_branch() -> None:
    process_text = (
        "When a claim is received, it is first checked whether the claimant is insured by the organization. "
        "If not, the claimant is informed that the claim must be rejected. Otherwise, the severity of the claim is evaluated. "
        "Based on the outcome (simple or complex claims), relevant forms are sent to the claimant. "
        "Once the forms are returned, they are checked for completeness. "
        "If the forms provide all relevant details, the claim is registered. "
        "Otherwise, the claimant is informed to update the forms. "
        "Upon reception of the updated forms, they are checked again."
    )
    artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["insured", "rejected"],
                "purpose": "determine whether the claimant is insured",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "T1",
                "parent_branch": "insured",
                "branches": ["simple_claim", "complex_claim"],
                "purpose": "evaluate the severity of the claim",
            },
            {
                "id": "T3",
                "type": "decision",
                "parent": "T1",
                "parent_branch": "insured",
                "branches": ["complete", "incomplete"],
                "purpose": "check returned forms for completeness",
            },
            {
                "id": "T4",
                "type": "loop",
                "parent": "T3",
                "parent_branch": "incomplete",
                "branches": ["retry", "success"],
                "purpose": "request updates and check the forms again until complete",
            },
        ]
    }

    validated = _validate_topology_artifact_against_process_text(
        process_text=process_text,
        topology_artifact=artifact,
    )

    assert validated == artifact


def test_validate_topology_artifact_rejects_shared_post_branch_control_attached_to_only_one_sibling_branch() -> None:
    process_text = (
        "When a claim is received, it is first checked whether the claimant is insured by the organization. "
        "If not, the claimant is informed that the claim must be rejected. Otherwise, the severity of the claim is evaluated. "
        "Based on the outcome (simple or complex claims), relevant forms are sent to the claimant. "
        "Once the forms are returned, they are checked for completeness. "
        "If the forms provide all relevant details, the claim is registered. "
        "Otherwise, the claimant is informed to update the forms. "
        "Upon reception of the updated forms, they are checked again."
    )
    artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["insured", "rejected"],
                "purpose": "determine whether the claimant is insured",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "T1",
                "parent_branch": "insured",
                "branches": ["simple_claim", "complex_claim"],
                "purpose": "evaluate the severity of the claim",
            },
            {
                "id": "T3",
                "type": "decision",
                "parent": "T2",
                "parent_branch": "complex_claim",
                "branches": ["complete", "incomplete"],
                "purpose": "check returned forms for completeness",
            },
            {
                "id": "T4",
                "type": "loop",
                "parent": "T3",
                "parent_branch": "incomplete",
                "branches": ["retry", "success"],
                "purpose": "request updates and check the forms again until complete",
            },
        ]
    }

    with pytest.raises(ValueError, match="shared post-branch continuation is attached to only one sibling branch"):
        _validate_topology_artifact_against_process_text(
            process_text=process_text,
            topology_artifact=artifact,
        )


def test_validate_topology_artifact_rejects_shared_post_branch_control_promoted_to_root() -> None:
    process_text = (
        "When a claim is received, it is first checked whether the claimant is insured by the organization. "
        "If not, the claimant is informed that the claim must be rejected. Otherwise, the severity of the claim is evaluated. "
        "Based on the outcome (simple or complex claims), relevant forms are sent to the claimant. "
        "Once the forms are returned, they are checked for completeness. "
        "If the forms provide all relevant details, the claim is registered. "
        "Otherwise, the claimant is informed to update the forms. "
        "Upon reception of the updated forms, they are checked again."
    )
    artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["insured", "rejected"],
                "purpose": "determine whether the claimant is insured",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "T1",
                "parent_branch": "insured",
                "branches": ["simple_claim", "complex_claim"],
                "purpose": "evaluate the severity of the claim",
            },
            {
                "id": "T3",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["complete", "incomplete"],
                "purpose": "check returned forms for completeness",
            },
            {
                "id": "T4",
                "type": "loop",
                "parent": "T3",
                "parent_branch": "incomplete",
                "branches": ["retry", "success"],
                "purpose": "request updates and check the forms again until complete",
            },
        ]
    }

    with pytest.raises(ValueError, match="shared post-branch continuation was promoted outside the required outer branch scope"):
        _validate_topology_artifact_against_process_text(
            process_text=process_text,
            topology_artifact=artifact,
        )


def test_validate_topology_artifact_rejects_missing_inner_decision_before_shared_post_branch_control() -> None:
    process_text = (
        "When a claim is received, it is first checked whether the claimant is insured by the organization. "
        "If not, the claimant is informed that the claim must be rejected. Otherwise, the severity of the claim is evaluated. "
        "Based on the outcome (simple or complex claims), relevant forms are sent to the claimant. "
        "Once the forms are returned, they are checked for completeness. "
        "If the forms provide all relevant details, the claim is registered. "
        "Otherwise, the claimant is informed to update the forms. "
        "Upon reception of the updated forms, they are checked again."
    )
    artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["insured", "rejected"],
                "purpose": "determine whether the claimant is insured",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "T1",
                "parent_branch": "insured",
                "branches": ["complete", "incomplete"],
                "purpose": "check returned forms for completeness",
            },
            {
                "id": "T3",
                "type": "loop",
                "parent": "T2",
                "parent_branch": "incomplete",
                "branches": ["retry", "success"],
                "purpose": "request updates and check the forms again until complete",
            },
        ]
    }

    with pytest.raises(ValueError, match="missing nested sibling decision before shared post-branch continuation"):
        _validate_topology_artifact_against_process_text(
            process_text=process_text,
            topology_artifact=artifact,
        )


def test_validate_topology_artifact_rejects_missing_shared_post_branch_decision_after_inner_split() -> None:
    process_text = (
        "When a claim is received, it is first checked whether the claimant is insured by the organization. "
        "If not, the claimant is informed that the claim must be rejected. Otherwise, the severity of the claim is evaluated. "
        "Based on the outcome (simple or complex claims), relevant forms are sent to the claimant. "
        "Once the forms are returned, they are checked for completeness. "
        "If the forms provide all relevant details, the claim is registered. "
        "Otherwise, the claimant is informed to update the forms. "
        "Upon reception of the updated forms, they are checked again."
    )
    artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["insured", "rejected"],
                "purpose": "determine whether the claimant is insured",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "T1",
                "parent_branch": "insured",
                "branches": ["simple", "complex"],
                "purpose": "evaluate the severity of the claim",
            },
            {
                "id": "T3",
                "type": "loop",
                "parent": "T1",
                "parent_branch": "insured",
                "branches": ["retry", "success"],
                "purpose": "request updates and check the forms again until complete",
            },
        ]
    }

    with pytest.raises(ValueError, match="missing shared post-branch decision after the sibling decision"):
        _validate_topology_artifact_against_process_text(
            process_text=process_text,
            topology_artifact=artifact,
        )


def test_generate_topology_artifact_retry_feedback_keeps_shared_post_branch_continuation_inside_outer_branch() -> None:
    process_text = (
        "When a claim is received, it is first checked whether the claimant is insured by the organization. "
        "If not, the claimant is informed that the claim must be rejected. Otherwise, the severity of the claim is evaluated. "
        "Based on the outcome (simple or complex claims), relevant forms are sent to the claimant. "
        "Once the forms are returned, they are checked for completeness. "
        "If the forms provide all relevant details, the claim is registered. "
        "Otherwise, the claimant is informed to update the forms. "
        "Upon reception of the updated forms, they are checked again."
    )
    invalid_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["insured", "rejected"],
          "purpose": "determine whether the claimant is insured"
        },
        {
          "id": "T2",
          "type": "decision",
          "parent": "T1",
          "parent_branch": "insured",
          "branches": ["simple_claim", "complex_claim"],
          "purpose": "evaluate the severity of the claim"
        },
        {
          "id": "T3",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["complete", "incomplete"],
          "purpose": "check returned forms for completeness"
        }
      ]
    }
    """
    valid_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["insured", "rejected"],
          "purpose": "determine whether the claimant is insured"
        },
        {
          "id": "T2",
          "type": "decision",
          "parent": "T1",
          "parent_branch": "insured",
          "branches": ["simple_claim", "complex_claim"],
          "purpose": "evaluate the severity of the claim"
        },
        {
          "id": "T3",
          "type": "decision",
          "parent": "T1",
          "parent_branch": "insured",
          "branches": ["complete", "incomplete"],
          "purpose": "check returned forms for completeness"
        },
        {
          "id": "T4",
          "type": "loop",
          "parent": "T3",
          "parent_branch": "incomplete",
          "branches": ["retry", "success"],
          "purpose": "request updates and check the forms again until complete"
        }
      ]
    }
    """

    with patch("llm.topology_experiment.call_openai", side_effect=[invalid_output, valid_output]) as mocked_call:
        result = generate_topology_artifact(process_text, model="gpt-4o")

    assert len(result["artifact"]["structures"]) == 4
    retry_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "shared post-branch continuation was promoted outside the required outer branch scope" in retry_prompt
    assert "Keep the earlier sibling decision" in retry_prompt
    assert "same parent and parent_branch" in retry_prompt
    assert "not one of that decision's branch handles" in retry_prompt
    assert "Preserve the existing earlier sibling decision exactly as a separate structure" in retry_prompt
    assert "Do not delete it, replace it, or collapse its sibling branches" in retry_prompt
    assert "Move only the later shared continuation structure" in retry_prompt
    assert "Keep the later shared structure ordered after the preserved earlier decision" in retry_prompt
    assert '"id": "T2"' in retry_prompt
    assert '"id": "T3"' in retry_prompt


def test_generate_topology_artifact_retry_feedback_requires_shared_post_branch_decision_before_loop() -> None:
    process_text = (
        "When a claim is received, it is first checked whether the claimant is insured by the organization. "
        "If not, the claimant is informed that the claim must be rejected. Otherwise, the severity of the claim is evaluated. "
        "Based on the outcome (simple or complex claims), relevant forms are sent to the claimant. "
        "Once the forms are returned, they are checked for completeness. "
        "If the forms provide all relevant details, the claim is registered. "
        "Otherwise, the claimant is informed to update the forms. "
        "Upon reception of the updated forms, they are checked again."
    )
    invalid_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["insured", "rejected"],
          "purpose": "determine whether the claimant is insured"
        },
        {
          "id": "T2",
          "type": "decision",
          "parent": "T1",
          "parent_branch": "insured",
          "branches": ["simple_claim", "complex_claim"],
          "purpose": "evaluate the severity of the claim"
        },
        {
          "id": "T3",
          "type": "loop",
          "parent": "T1",
          "parent_branch": "insured",
          "branches": ["retry", "success"],
          "purpose": "request updates and check the forms again until complete"
        }
      ]
    }
    """
    valid_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["insured", "rejected"],
          "purpose": "determine whether the claimant is insured"
        },
        {
          "id": "T2",
          "type": "decision",
          "parent": "T1",
          "parent_branch": "insured",
          "branches": ["simple_claim", "complex_claim"],
          "purpose": "evaluate the severity of the claim"
        },
        {
          "id": "T3",
          "type": "decision",
          "parent": "T1",
          "parent_branch": "insured",
          "branches": ["complete", "incomplete"],
          "purpose": "check returned forms for completeness"
        },
        {
          "id": "T4",
          "type": "loop",
          "parent": "T3",
          "parent_branch": "incomplete",
          "branches": ["retry", "success"],
          "purpose": "request updates and check the forms again until complete"
        }
      ]
    }
    """

    with patch("llm.topology_experiment.call_openai", side_effect=[invalid_output, valid_output]) as mocked_call:
        result = generate_topology_artifact(process_text, model="gpt-4o")

    assert len(result["artifact"]["structures"]) == 4
    retry_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "missing shared post-branch decision after the sibling decision" in retry_prompt
    assert "If the later shared continuation itself contains an if/otherwise-style split" in retry_prompt
    assert "model that shared continuation as a decision first" in retry_prompt
    assert "place any retry or recheck loop inside the retry/incomplete branch of that shared decision" in retry_prompt
    assert "not one of that decision's branch handles" in retry_prompt


def test_generate_topology_artifact_retry_feedback_preserves_existing_branch_introducing_decision() -> None:
    process_text = (
        "When a claim is received, it is first checked whether the claimant is insured by the organization. "
        "If not, the claimant is informed that the claim must be rejected. Otherwise, the severity of the claim is evaluated. "
        "Based on the outcome (simple or complex claims), relevant forms are sent to the claimant. "
        "Once the forms are returned, they are checked for completeness. "
        "If the forms provide all relevant details, the claim is registered. "
        "Otherwise, the claimant is informed to update the forms. "
        "Upon reception of the updated forms, they are checked again."
    )
    invalid_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["insured", "rejected"],
          "purpose": "determine whether the claimant is insured"
        },
        {
          "id": "T2",
          "type": "decision",
          "parent": "T1",
          "parent_branch": "insured",
          "branches": ["simple_claim", "complex_claim"],
          "purpose": "evaluate the severity of the claim"
        },
        {
          "id": "T3",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["complete", "incomplete"],
          "purpose": "check returned forms for completeness"
        },
        {
          "id": "T4",
          "type": "loop",
          "parent": "T3",
          "parent_branch": "incomplete",
          "branches": ["retry", "success"],
          "purpose": "request updates and check the forms again until complete"
        }
      ]
    }
    """
    valid_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["insured", "rejected"],
          "purpose": "determine whether the claimant is insured"
        },
        {
          "id": "T2",
          "type": "decision",
          "parent": "T1",
          "parent_branch": "insured",
          "branches": ["simple_claim", "complex_claim"],
          "purpose": "evaluate the severity of the claim"
        },
        {
          "id": "T3",
          "type": "decision",
          "parent": "T1",
          "parent_branch": "insured",
          "branches": ["complete", "incomplete"],
          "purpose": "check returned forms for completeness"
        },
        {
          "id": "T4",
          "type": "loop",
          "parent": "T3",
          "parent_branch": "incomplete",
          "branches": ["retry", "success"],
          "purpose": "request updates and check the forms again until complete"
        }
      ]
    }
    """

    with patch("llm.topology_experiment.call_openai", side_effect=[invalid_output, valid_output]) as mocked_call:
        result = generate_topology_artifact(process_text, model="gpt-4o")

    structures = result["artifact"]["structures"]
    assert structures[1] == {
        "id": "T2",
        "type": "decision",
        "parent": "T1",
        "parent_branch": "insured",
        "branches": ["simple_claim", "complex_claim"],
        "purpose": "evaluate the severity of the claim",
    }
    assert structures[2]["id"] == "T3"
    assert structures[2]["parent"] == "T1"
    assert structures[2]["parent_branch"] == "insured"
    assert structures[3]["id"] == "T4"
    assert structures[3]["parent"] == "T3"
    assert structures[3]["parent_branch"] == "incomplete"

    retry_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "Preserve the existing earlier sibling decision exactly as a separate structure" in retry_prompt
    assert "Do not delete it, replace it, or collapse its sibling branches" in retry_prompt
    assert "Move only the later shared continuation structure" in retry_prompt
    assert "Reuse the preserved earlier decision's parent and parent_branch for the relocated later structure" in retry_prompt
    assert "Keep the later shared structure ordered after the preserved earlier decision" in retry_prompt
    assert '"id": "T2"' in retry_prompt
    assert '"id": "T3"' in retry_prompt


@pytest.mark.parametrize(
    ("process_text", "raw_output", "expected_types", "expected_parents"),
    [
        (
            "If the request is approved, it proceeds. Otherwise, it is rejected.",
            """
            {
              "structures": [
                {
                  "id": "T1",
                  "type": "decision",
                  "parent": "ROOT",
                  "parent_branch": null,
                  "branches": ["approved", "rejected"],
                  "purpose": "determine whether the request proceeds"
                }
              ]
            }
            """,
            ["decision"],
            ["ROOT"],
        ),
        (
            "If the request is approved, the analyst reworks the package until it passes review. Otherwise, the request is rejected.",
            """
            {
              "structures": [
                {
                  "id": "T1",
                  "type": "decision",
                  "parent": "ROOT",
                  "parent_branch": null,
                  "branches": ["approved", "rejected"],
                  "purpose": "determine whether the request is approved"
                },
                {
                  "id": "T2",
                  "type": "loop",
                  "parent": "T1",
                  "parent_branch": "approved",
                  "branches": ["retry", "success"],
                  "purpose": "repeat rework until the package passes review"
                }
              ]
            }
            """,
            ["decision", "loop"],
            ["ROOT", "T1"],
        ),
        (
            "If the request is approved, the team prepares the package. Otherwise, the team records the rejection. After the decision, the team retries the audit update until it succeeds.",
            """
            {
              "structures": [
                {
                  "id": "T1",
                  "type": "decision",
                  "parent": "ROOT",
                  "parent_branch": null,
                  "branches": ["approved", "rejected"],
                  "purpose": "determine request outcome"
                },
                {
                  "id": "T2",
                  "type": "loop",
                  "parent": "ROOT",
                  "parent_branch": null,
                  "branches": ["retry", "success"],
                  "purpose": "retry the audit update until it succeeds"
                }
              ]
            }
            """,
            ["decision", "loop"],
            ["ROOT", "ROOT"],
        ),
        (
            "If the request is approved, it proceeds. Otherwise, it is rejected. If the package is ready, it is archived. Otherwise, it is held.",
            """
            {
              "structures": [
                {
                  "id": "T1",
                  "type": "decision",
                  "parent": "ROOT",
                  "parent_branch": null,
                  "branches": ["approved", "rejected"],
                  "purpose": "determine request outcome"
                },
                {
                  "id": "T2",
                  "type": "decision",
                  "parent": "ROOT",
                  "parent_branch": null,
                  "branches": ["ready", "held"],
                  "purpose": "determine package disposition"
                }
              ]
            }
            """,
            ["decision", "decision"],
            ["ROOT", "ROOT"],
        ),
    ],
)
def test_generate_topology_artifact_accepts_existing_working_topology_patterns(
    process_text: str,
    raw_output: str,
    expected_types: list[str],
    expected_parents: list[str],
) -> None:
    with patch("llm.topology_experiment.call_openai", return_value=raw_output):
        result = generate_topology_artifact(process_text, model="gpt-4o")

    assert [structure["type"] for structure in result["artifact"]["structures"]] == expected_types
    assert [structure["parent"] for structure in result["artifact"]["structures"]] == expected_parents


_CASE_2_1_TIMEOUT_SOURCE = (
    "Resource Provisioning has been on-hold and waiting for a restoration request - "
    "but this must happen within 2 days after the status report was sent out, "
    "otherwise Resource Provisioning terminates the process."
)


def _incomplete_timeout_topology() -> dict:
    return {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["normal", "priority"],
                "purpose": "route the request for ordinary processing",
            }
        ]
    }


def _corrected_timeout_topology() -> dict:
    return {
        "structures": [
            {
                "id": "T4",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["no_problem", "minor_problem", "automatic_resource_restoration"],
                "purpose": "select the resource provisioning countermeasure",
            },
            {
                "id": "T5",
                "type": "decision",
                "parent": "T4",
                "parent_branch": "automatic_resource_restoration",
                "branches": ["restoration_received_within_2_days", "restoration_timeout"],
                "purpose": "determine whether the restoration request arrives before the deadline",
            },
        ]
    }


def test_validate_topology_rejects_explicit_timeout_termination_without_local_decision() -> None:
    with pytest.raises(ValueError, match="MISSING_TIMEOUT_DECISION") as exc_info:
        _validate_topology_artifact_against_process_text(
            process_text="The request must arrive within 2 days, otherwise the process is terminated.",
            topology_artifact=_incomplete_timeout_topology(),
        )

    assert "missing local timeout conditional structure" in str(exc_info.value)
    assert "within 2 days" in str(exc_info.value)


def test_validate_topology_accepts_explicit_timeout_termination_with_local_decision() -> None:
    artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["request_received_within_deadline", "request_timeout"],
                "purpose": "determine whether the request arrives before the deadline",
            }
        ]
    }

    validated = _validate_topology_artifact_against_process_text(
        process_text="The request must arrive within 2 days, otherwise the process is terminated.",
        topology_artifact=artifact,
    )

    assert validated == artifact


@pytest.mark.parametrize(
    "process_text",
    [
        "The process waits for 2 days before continuing.",
        "The request should arrive within 2 days.",
        "If the customer rejects the offer, the process terminates.",
    ],
)
def test_validate_topology_does_not_overtrigger_timeout_completeness(process_text: str) -> None:
    validated = _validate_topology_artifact_against_process_text(
        process_text=process_text,
        topology_artifact={"structures": []},
    )

    assert validated == {"structures": []}


def test_validate_topology_recognizes_unless_timeout_cancellation() -> None:
    process_text = (
        "The process continues only if approval is received within 24 hours; "
        "unless it is received, the case is cancelled."
    )

    with pytest.raises(ValueError, match="MISSING_TIMEOUT_DECISION"):
        _validate_topology_artifact_against_process_text(
            process_text=process_text,
            topology_artifact={"structures": []},
        )


def test_validate_topology_rejects_saved_case_2_1_shape_without_timeout_decision() -> None:
    with pytest.raises(ValueError, match="MISSING_TIMEOUT_DECISION"):
        _validate_topology_artifact_against_process_text(
            process_text=_CASE_2_1_TIMEOUT_SOURCE,
            topology_artifact={
                "structures": [
                    {
                        "id": "T4",
                        "type": "decision",
                        "parent": "ROOT",
                        "parent_branch": None,
                        "branches": ["no_problem", "minor_problem", "automatic_resource_restoration"],
                        "purpose": "select the resource provisioning countermeasure",
                    }
                ]
            },
        )


def test_validate_topology_accepts_corrected_case_2_1_timeout_decision() -> None:
    validated = _validate_topology_artifact_against_process_text(
        process_text=_CASE_2_1_TIMEOUT_SOURCE,
        topology_artifact=_corrected_timeout_topology(),
    )

    assert validated == _corrected_timeout_topology()


def test_missing_timeout_decision_uses_existing_topology_correction_loop() -> None:
    invalid_output = json.dumps(_incomplete_timeout_topology())
    valid_output = json.dumps(_corrected_timeout_topology())

    with patch(
        "llm.topology_experiment.call_openai",
        side_effect=[invalid_output, valid_output],
    ) as mocked_call:
        result = generate_topology_artifact(_CASE_2_1_TIMEOUT_SOURCE, model="gpt-4o")

    assert result["artifact"] == _corrected_timeout_topology()
    assert len(result["planner_attempts"]) == 2
    assert "MISSING_TIMEOUT_DECISION" in result["planner_attempts"][0]["validation_error"]
    retry_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "missing local timeout conditional structure" in retry_prompt
    assert "timely_or_success" in retry_prompt
    assert "timeout_or_failure" in retry_prompt
