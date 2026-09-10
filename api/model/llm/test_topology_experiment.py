from __future__ import annotations

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
from llm.keyword_hints import extract_keyword_hints


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
    assert "Create a loop only when the text explicitly indicates repetition" in prompt
    assert "Create a parallel block only when the text explicitly indicates concurrent work" in prompt
    assert "Compound concurrency evidence can include separate executable activities linked by `in the meantime`" in prompt


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


def test_bare_meantime_requires_two_activities_and_shared_continuation() -> None:
    process_text = (
        "The ready files are handed to the Associate, and meantime the Judge's Lawlist is "
        "distributed to the relevant people. Afterwards, the directions hearings are conducted."
    )

    hints = extract_keyword_hints(process_text)

    assert hints["flags"]["possible_parallelism"] is True
    assert "bare_meantime_with_independent_activities_and_shared_continuation" in hints["evidence"]["parallel_terms"]


def test_bare_meantime_without_shared_continuation_does_not_require_parallelism() -> None:
    hints = extract_keyword_hints(
        "The ready files are handed to the Associate, and meantime the Judge's Lawlist is distributed."
    )

    assert hints["flags"]["possible_parallelism"] is False

