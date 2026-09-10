from __future__ import annotations

import json
import pytest
from unittest.mock import patch

from llm.semantic_sketch_experiment import (
    SemanticOwnershipEvidenceValidationError,
    SemanticSketchPlanGenerationError,
    build_semantic_sketch_experiment_prompt,
    generate_semantic_sketch_plan,
    parse_semantic_sketch_plan_json,
    preserve_explicit_business_activities,
    semantic_sketch_plan_response_format,
    validate_semantic_ownership_against_evidence,
)


def test_parse_semantic_sketch_plan_json_accepts_valid_semantic_plan() -> None:
    raw_output = """
    {
      "root_actions": [
        {"slot_id": "ROOT_START", "action": "submit request"},
        {"slot_id": "AFTER_T1", "action": "review request"}
      ],
      "branch_plans": [
        {
          "structure_id": "T1",
          "branch": "retry",
          "intent": "loop_back",
          "steps": [{"action": "revise request"}]
        },
        {
          "structure_id": "T1",
          "branch": "success",
          "intent": "continue",
          "steps": []
        }
      ]
    }
    """

    artifact = parse_semantic_sketch_plan_json(raw_output)

    assert artifact["root_actions"][0]["slot_id"] == "ROOT_START"
    assert artifact["branch_plans"][0]["intent"] == "loop_back"


def test_parse_semantic_sketch_plan_json_accepts_target_slot_id() -> None:
    raw_output = """
    {
      "root_actions": [
        {"slot_id": "ROOT_START", "action": "submit request"},
        {"slot_id": "AFTER_T1", "action": "review request"}
      ],
      "branch_plans": [
        {
          "structure_id": "T1",
          "branch": "retry",
          "intent": "continue",
          "steps": [{"action": "recheck request"}],
          "target_slot_id": "ROOT_START"
        },
        {
          "structure_id": "T1",
          "branch": "success",
          "intent": "continue",
          "steps": []
        }
      ]
    }
    """

    artifact = parse_semantic_sketch_plan_json(raw_output)

    assert artifact["branch_plans"][0]["target_slot_id"] == "ROOT_START"


def test_parse_semantic_sketch_plan_json_normalizes_legacy_and_canonical_root_slots() -> None:
    raw_output = """
    {
      "root_actions": [
        {"slot_id": "ROOT_START", "action": "review request"},
        {"slot_id": "AFTER_T1", "actions": [{"action": "record result"}, {"action": "notify manager"}]},
        {"slot_id": "AFTER_T2", "actions": []}
      ],
      "branch_plans": [
        {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
        {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]}
      ]
    }
    """

    artifact = parse_semantic_sketch_plan_json(raw_output)

    assert artifact["root_actions"] == [
        {"slot_id": "ROOT_START", "actions": [{"action": "review request"}]},
        {"slot_id": "AFTER_T1", "actions": [{"action": "record result"}, {"action": "notify manager"}]},
        {"slot_id": "AFTER_T2", "actions": []},
    ]


def test_parse_semantic_sketch_plan_json_accepts_fenced_json() -> None:
    raw_output = """
    ```json
    {
      "root_actions": [
        {"slot_id": "ROOT_START", "action": "submit request"},
        {"slot_id": "AFTER_T1", "action": "review request"}
      ],
      "branch_plans": [
        {
          "structure_id": "T1",
          "branch": "retry",
          "intent": "loop_back",
          "steps": [{"action": "revise request"}]
        },
        {
          "structure_id": "T1",
          "branch": "success",
          "intent": "continue",
          "steps": []
        }
      ]
    }
    ```
    """

    artifact = parse_semantic_sketch_plan_json(raw_output)

    assert artifact["root_actions"][1]["slot_id"] == "AFTER_T1"
    assert artifact["branch_plans"][1]["intent"] == "continue"


def test_parse_semantic_sketch_plan_json_rejects_empty_terminate_branch_steps() -> None:
    raw_output = """
    {
      "root_actions": [
        {"slot_id": "ROOT_START", "action": "review request"},
        {"slot_id": "AFTER_T1", "action": "finalize request"}
      ],
      "branch_plans": [
        {
          "structure_id": "T1",
          "branch": "approved",
          "intent": "continue",
          "steps": []
        },
        {
          "structure_id": "T1",
          "branch": "rejected",
          "intent": "terminate",
          "steps": []
        }
      ]
    }
    """

    with pytest.raises(ValueError, match="intent `terminate` or `loop_back`"):
        parse_semantic_sketch_plan_json(raw_output)


def test_build_semantic_sketch_experiment_prompt_includes_semantic_preservation_rules() -> None:
    prompt = build_semantic_sketch_experiment_prompt(
        "Review the request. If rejected, cancel it. If approved, finalize it.",
        topology_artifact={
            "structures": [
                {
                    "id": "T1",
                    "type": "decision",
                    "parent": "ROOT",
                    "parent_branch": None,
                    "branches": ["approved", "rejected"],
                    "purpose": "approval decision",
                }
            ]
        },
    )

    assert "Treat each independently asserted business operation at each explicit process occurrence as one business action" in prompt
    assert "Use concise action names closely derived from the source wording" in prompt
    assert "An explicit operation that establishes a later decision" in prompt
    assert "never absorb the operation only into the decision purpose, label, or condition" in prompt
    assert "`branch_plans.intent` is control-flow only; it must never replace a business action" in prompt
    assert "For every branch plan, decide the branch-local business action text first and set `intent` second" in prompt
    assert "A `terminate` or `loop_back` branch must not return `steps=[]`" in prompt
    assert "Each listed root slot must appear exactly once in `root_actions` using its provided `slot_id`" in prompt
    assert "Do not invent neutral coordination actions such as `complete request handling`" in prompt
    assert "verify internally that every listed root slot appears exactly once in `root_actions`" in prompt
    assert "Do not move branch-specific business actions into shared `root_actions`" in prompt
    assert "An empty `steps` list is valid only when that branch genuinely performs no business action of its own in the process text" in prompt


def test_build_semantic_sketch_experiment_prompt_explains_shared_continuation_ownership() -> None:
    prompt = build_semantic_sketch_experiment_prompt(
        (
            "Review the request. If approved, fulfill it. Otherwise, reject it. "
            "In either case, record the outcome."
        ),
        topology_artifact={
            "structures": [
                {
                    "id": "T1",
                    "type": "decision",
                    "parent": "ROOT",
                    "parent_branch": None,
                    "branches": ["approved", "rejected"],
                    "purpose": "review outcome",
                }
            ]
        },
    )

    assert "Classify ownership by execution scope and process order, not by the action verb alone" in prompt
    assert "A branch is `terminate` only when no later shared business behavior applies to that path" in prompt
    assert "keep every affected branch on `intent=\"continue\"`" in prompt
    assert "Retry success must reconnect to the same shared post-structure actions" in prompt
    assert "Do not duplicate the shared action into branch steps" in prompt


def _decision_topology() -> dict:
    return {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
                "purpose": "review the request outcome",
            }
        ]
    }


def _decision_plan(*, shared_actions: list[str], rejected_intent: str = "continue", approved_steps: list[str] | None = None) -> dict:
    return {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "review request"}]},
            {"slot_id": "AFTER_T1", "actions": [{"action": action} for action in shared_actions]},
        ],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "approved",
                "intent": "continue",
                "steps": [{"action": action} for action in (approved_steps or ["fulfill request"])],
            },
            {
                "structure_id": "T1",
                "branch": "rejected",
                "intent": rejected_intent,
                "steps": [{"action": "reject request"}],
            },
        ],
    }


@pytest.mark.parametrize(
    ("semantic_plan", "expected_reason"),
    [
        (
            _decision_plan(shared_actions=[], approved_steps=["fulfill request", "record outcome"]),
            "shared action is missing from post-structure slot AFTER_T1",
        ),
        (
            _decision_plan(shared_actions=["record outcome"], rejected_intent="terminate"),
            "branch T1/rejected uses intent=terminate",
        ),
        (
            _decision_plan(shared_actions=[]),
            "shared action is missing from post-structure slot AFTER_T1",
        ),
    ],
)
def test_semantic_ownership_validator_rejects_explicit_shared_continuation_contradictions(
    semantic_plan: dict,
    expected_reason: str,
) -> None:
    process_text = (
        "An analyst reviews the request. If approved, the analyst fulfills it. "
        "Otherwise, the analyst rejects it. In either case, the analyst records the outcome."
    )

    with pytest.raises(SemanticOwnershipEvidenceValidationError, match=expected_reason):
        validate_semantic_ownership_against_evidence(
            process_text,
            topology_artifact=_decision_topology(),
            semantic_plan=semantic_plan,
        )


def test_semantic_ownership_validator_rejects_retry_success_stranded_before_shared_work() -> None:
    process_text = (
        "The request is checked for completeness. If it is complete, the request is archived. "
        "Otherwise, the requester updates it. The updated request is checked again until complete."
    )
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["complete", "incomplete"],
                "purpose": "check request completeness",
            },
            {
                "id": "T2",
                "type": "loop",
                "parent": "T1",
                "parent_branch": "incomplete",
                "branches": ["retry", "success"],
                "purpose": "check the updated request again until complete",
            },
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "complete", "intent": "continue", "steps": [{"action": "archive request"}]},
            {"structure_id": "T1", "branch": "incomplete", "intent": "continue", "steps": [{"action": "update request"}]},
            {"structure_id": "T2", "branch": "retry", "intent": "loop_back", "steps": [{"action": "check updated request"}]},
            {"structure_id": "T2", "branch": "success", "intent": "continue", "steps": []},
        ],
    }

    with pytest.raises(SemanticOwnershipEvidenceValidationError, match="retry success T2/success cannot reach shared action"):
        validate_semantic_ownership_against_evidence(
            process_text,
            topology_artifact=topology_artifact,
            semantic_plan=semantic_plan,
        )


def _label_independent_retry_plan(*, shared: bool) -> dict:
    return {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {
                "slot_id": "AFTER_T1",
                "actions": [{"action": "archive submission"}] if shared else [],
            },
        ],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "route_a",
                "intent": "continue",
                "steps": [] if shared else [{"action": "archive submission"}],
            },
            {
                "structure_id": "T1",
                "branch": "route_b",
                "intent": "continue",
                "steps": [{"action": "correct submission"}],
            },
            {
                "structure_id": "T2",
                "branch": "cycle_a",
                "intent": "loop_back",
                "steps": [{"action": "check corrected submission"}],
            },
            {
                "structure_id": "T2",
                "branch": "cycle_b",
                "intent": "continue",
                "steps": [],
            },
        ],
    }


def _label_independent_retry_topology() -> dict:
    return {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["route_a", "route_b"],
                "purpose": "check submission result",
            },
            {
                "id": "T2",
                "type": "loop",
                "parent": "T1",
                "parent_branch": "route_b",
                "branches": ["cycle_a", "cycle_b"],
                "purpose": "check corrected submission again until it passes",
            },
        ]
    }


def test_semantic_ownership_validator_uses_retry_structure_instead_of_negative_branch_name() -> None:
    process_text = (
        "The submission is checked. If it passes, the submission is archived. "
        "Otherwise, the submitter corrects it. The corrected submission is checked again until it passes."
    )

    with pytest.raises(SemanticOwnershipEvidenceValidationError, match="retry success T2/cycle_b cannot reach shared action"):
        validate_semantic_ownership_against_evidence(
            process_text,
            topology_artifact=_label_independent_retry_topology(),
            semantic_plan=_label_independent_retry_plan(shared=False),
        )


def test_semantic_ownership_validator_finds_retry_loop_below_intermediate_child_control() -> None:
    process_text = (
        "The submission is checked. If it passes, the submission is archived. "
        "Otherwise, the correction route is selected and the submitter corrects it. "
        "The corrected submission is checked again until it passes."
    )
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["route_a", "route_b"],
                "purpose": "check submission result",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "T1",
                "parent_branch": "route_b",
                "branches": ["path_a", "path_b"],
                "purpose": "select correction route for the submission",
            },
            {
                "id": "T3",
                "type": "loop",
                "parent": "T2",
                "parent_branch": "path_a",
                "branches": ["cycle_a", "cycle_b"],
                "purpose": "check corrected submission again until it passes",
            },
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "route_a", "intent": "continue", "steps": [{"action": "archive submission"}]},
            {"structure_id": "T1", "branch": "route_b", "intent": "continue", "steps": []},
            {"structure_id": "T2", "branch": "path_a", "intent": "continue", "steps": [{"action": "correct submission"}]},
            {"structure_id": "T2", "branch": "path_b", "intent": "terminate", "steps": [{"action": "cancel correction"}]},
            {"structure_id": "T3", "branch": "cycle_a", "intent": "loop_back", "steps": [{"action": "check corrected submission"}]},
            {"structure_id": "T3", "branch": "cycle_b", "intent": "continue", "steps": []},
        ],
    }

    with pytest.raises(SemanticOwnershipEvidenceValidationError, match="retry success T3/cycle_b cannot reach shared action"):
        validate_semantic_ownership_against_evidence(
            process_text,
            topology_artifact=topology_artifact,
            semantic_plan=semantic_plan,
        )


def test_generate_semantic_sketch_plan_retries_for_label_independent_retry_convergence() -> None:
    process_text = (
        "The submission is checked. If it passes, the submission is archived. "
        "Otherwise, the submitter corrects it. The corrected submission is checked again until it passes."
    )
    invalid_plan = _label_independent_retry_plan(shared=False)
    valid_plan = _label_independent_retry_plan(shared=True)

    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        side_effect=[json.dumps(invalid_plan), json.dumps(valid_plan)],
    ):
        result = generate_semantic_sketch_plan(
            process_text,
            topology_artifact=_label_independent_retry_topology(),
            model="gpt-4o",
        )

    assert len(result["planner_attempts"]) == 2
    assert "retry success T2/cycle_b cannot reach shared action" in result["planner_attempts"][0]["validation_error"]
    assert result["planner_attempts"][1]["validation_error"] is None


@pytest.mark.parametrize("duplicate_shared_action", [False, True])
def test_inferred_retry_ownership_errors_are_warning_only(duplicate_shared_action: bool) -> None:
    process_text = (
        "The submission is checked. If it passes, the submission is archived. "
        "Otherwise, the submitter corrects it. The corrected submission is checked again until it passes."
    )
    semantic_plan = _label_independent_retry_plan(shared=duplicate_shared_action)
    if duplicate_shared_action:
        semantic_plan["branch_plans"][0]["steps"] = [{"action": "archive submission"}]

    with pytest.raises(SemanticOwnershipEvidenceValidationError) as exc_info:
        validate_semantic_ownership_against_evidence(
            process_text,
            topology_artifact=_label_independent_retry_topology(),
            semantic_plan=semantic_plan,
        )

    assert exc_info.value.warning_only is True


def test_retry_ownership_warning_is_recorded_and_accepted_after_correction_exhaustion() -> None:
    process_text = (
        "The submission is checked. If it passes, the submission is archived. "
        "Otherwise, the submitter corrects it. The corrected submission is checked again until it passes."
    )
    warning_plan = _label_independent_retry_plan(shared=False)

    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        side_effect=[json.dumps(warning_plan), json.dumps(warning_plan), json.dumps(warning_plan)],
    ) as mocked_call:
        result = generate_semantic_sketch_plan(
            process_text,
            topology_artifact=_label_independent_retry_topology(),
            model="gpt-4o",
        )

    assert mocked_call.call_count == 3
    assert result["artifact"] == warning_plan
    assert len(result["planner_attempts"]) == 3
    assert all(
        "retry success T2/cycle_b cannot reach shared action" in attempt["validation_error"]
        for attempt in result["planner_attempts"]
    )
    assert "Shared-continuation correction" in mocked_call.call_args_list[1].kwargs["prompt"]


def test_semantic_ownership_validator_does_not_promote_unrelated_direct_branch_action() -> None:
    process_text = (
        "The customer chooses a delivery method. For express delivery, a courier is dispatched. "
        "For standard delivery, payment is validated and retried until accepted. The process then ends."
    )
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["route_a", "route_b"],
                "purpose": "choose delivery method",
            },
            {
                "id": "T2",
                "type": "loop",
                "parent": "T1",
                "parent_branch": "route_b",
                "branches": ["cycle_a", "cycle_b"],
                "purpose": "validate payment until accepted",
            },
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "route_a", "intent": "continue", "steps": [{"action": "dispatch courier"}]},
            {"structure_id": "T1", "branch": "route_b", "intent": "continue", "steps": [{"action": "validate payment"}]},
            {"structure_id": "T2", "branch": "cycle_a", "intent": "loop_back", "steps": [{"action": "retry payment"}]},
            {"structure_id": "T2", "branch": "cycle_b", "intent": "continue", "steps": []},
        ],
    }

    assert validate_semantic_ownership_against_evidence(
        process_text,
        topology_artifact=topology_artifact,
        semantic_plan=semantic_plan,
    ) == semantic_plan


def test_semantic_ownership_validator_preserves_terminating_sibling_of_nested_retry() -> None:
    process_text = (
        "The request is accepted or rejected. If rejected, the request is closed. "
        "If accepted, each item is checked and corrected until complete, then the accepted request is delivered."
    )
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["route_a", "route_b"],
                "purpose": "decide request acceptance",
            },
            {
                "id": "T2",
                "type": "loop",
                "parent": "T1",
                "parent_branch": "route_a",
                "branches": ["cycle_a", "cycle_b"],
                "purpose": "check each request item until complete",
            },
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "route_a", "intent": "continue", "steps": [{"action": "accept request"}]},
            {"structure_id": "T1", "branch": "route_b", "intent": "terminate", "steps": [{"action": "reject and close request"}]},
            {"structure_id": "T2", "branch": "cycle_a", "intent": "loop_back", "steps": [{"action": "correct request item"}]},
            {"structure_id": "T2", "branch": "cycle_b", "intent": "continue", "steps": [{"action": "deliver accepted request"}]},
        ],
    }

    assert validate_semantic_ownership_against_evidence(
        process_text,
        topology_artifact=topology_artifact,
        semantic_plan=semantic_plan,
    ) == semantic_plan


@pytest.mark.parametrize(
    ("process_text", "topology_artifact", "semantic_plan"),
    [
        (
            "An analyst reviews the request. If approved, it is fulfilled. Otherwise, it is rejected and the process ends.",
            _decision_topology(),
            _decision_plan(shared_actions=[], rejected_intent="terminate"),
        ),
        (
            "An analyst reviews the request. If approved, it is fulfilled. Otherwise, it is rejected.",
            _decision_topology(),
            _decision_plan(shared_actions=[]),
        ),
        (
            "An analyst reviews the request. If approved, it is fulfilled. Otherwise, it is rejected. In either case, the outcome is recorded.",
            _decision_topology(),
            _decision_plan(shared_actions=["record outcome"]),
        ),
        (
            "The request is checked. If invalid, revise and check again until valid. When valid, the process ends.",
            {
                "structures": [{"id": "T1", "type": "loop", "parent": "ROOT", "parent_branch": None, "branches": ["retry", "success"], "purpose": "check until valid"}]
            },
            {
                "root_actions": [{"slot_id": "ROOT_START", "actions": [{"action": "check request"}]}, {"slot_id": "AFTER_T1", "actions": []}],
                "branch_plans": [
                    {"structure_id": "T1", "branch": "retry", "intent": "loop_back", "steps": [{"action": "revise request"}]},
                    {"structure_id": "T1", "branch": "success", "intent": "continue", "steps": [], "target_slot_id": "AFTER_T1"},
                ],
            },
        ),
        (
            "The supplier receives an order, processes it, and sends an invoice.",
            {"structures": []},
            {"root_actions": [{"slot_id": "ROOT_START", "actions": [{"action": "receive order"}, {"action": "process order"}, {"action": "send invoice"}]}], "branch_plans": []},
        ),
        (
            "If review is required, inspect the request. If accepted, approve it; otherwise reject it. Without review, approve it directly.",
            {
                "structures": [
                    {"id": "T1", "type": "decision", "parent": "ROOT", "parent_branch": None, "branches": ["review", "direct"], "purpose": "decide whether review is required"},
                    {"id": "T2", "type": "decision", "parent": "T1", "parent_branch": "review", "branches": ["accepted", "rejected"], "purpose": "decide review outcome"},
                ]
            },
            {
                "root_actions": [{"slot_id": "ROOT_START", "actions": []}, {"slot_id": "AFTER_T1", "actions": []}],
                "branch_plans": [
                    {"structure_id": "T1", "branch": "review", "intent": "continue", "steps": [{"action": "inspect request"}]},
                    {"structure_id": "T1", "branch": "direct", "intent": "continue", "steps": [{"action": "approve request"}]},
                    {"structure_id": "T2", "branch": "accepted", "intent": "continue", "steps": [{"action": "approve request"}]},
                    {"structure_id": "T2", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
                ],
            },
        ),
        (
            "If approved, then archive the request. Otherwise, reject it.",
            _decision_topology(),
            _decision_plan(shared_actions=[], approved_steps=["archive request"]),
        ),
        (
            "The analyst approves or rejects the request. Afterwards the record may require further handling.",
            _decision_topology(),
            _decision_plan(shared_actions=[]),
        ),
    ],
)
def test_semantic_ownership_validator_preserves_valid_or_ambiguous_plans(
    process_text: str,
    topology_artifact: dict,
    semantic_plan: dict,
) -> None:
    assert validate_semantic_ownership_against_evidence(
        process_text,
        topology_artifact=topology_artifact,
        semantic_plan=semantic_plan,
    ) == semantic_plan


def test_generate_semantic_sketch_plan_retries_after_shared_ownership_validation_failure() -> None:
    process_text = (
        "An analyst reviews the request. If approved, the analyst fulfills it. "
        "Otherwise, the analyst rejects it. In either case, the analyst records the outcome."
    )
    invalid_plan = _decision_plan(shared_actions=["record outcome"], rejected_intent="terminate")
    valid_plan = _decision_plan(shared_actions=["record outcome"])

    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        side_effect=[json.dumps(invalid_plan), json.dumps(valid_plan)],
    ) as mocked_call:
        result = generate_semantic_sketch_plan(
            process_text,
            topology_artifact=_decision_topology(),
            model="gpt-4o",
        )

    assert len(result["planner_attempts"]) == 2
    assert "shared-continuation evidence" in result["planner_attempts"][0]["validation_error"]
    assert result["planner_attempts"][1]["validation_error"] is None
    retry_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "Preserve branch-local actions" in retry_prompt
    assert "do not terminate a branch before that shared behavior" in retry_prompt


def test_semantic_sketch_plan_response_format_requires_steps_for_terminate_or_loop_back() -> None:
    schema = semantic_sketch_plan_response_format()["json_schema"]["schema"]
    branch_plan_schema = schema["$defs"]["SemanticBranchPlan"]

    assert "steps" in branch_plan_schema["required"]
    assert {
        "if": {
            "properties": {
                "intent": {
                    "enum": ["terminate", "loop_back"],
                }
            },
            "required": ["intent"],
        },
        "then": {
            "properties": {
                "steps": {
                    "minItems": 1,
                }
            },
            "required": ["steps"],
        },
    } in branch_plan_schema["allOf"]


def test_parse_semantic_sketch_plan_json_logs_invalid_branch_plan_details(caplog: pytest.LogCaptureFixture) -> None:
    raw_output = """
    {
      "root_actions": [
        {"slot_id": "ROOT_START", "action": "review request"},
        {"slot_id": "AFTER_T1", "action": "finalize request"}
      ],
      "branch_plans": [
        {
          "structure_id": "T1",
          "branch": "approved",
          "intent": "continue",
          "steps": []
        },
        {
          "structure_id": "T2",
          "branch": "exit",
          "intent": "terminate",
          "steps": []
        }
      ]
    }
    """

    with caplog.at_level("ERROR"):
        with pytest.raises(ValueError, match="intent `terminate` or `loop_back`"):
            parse_semantic_sketch_plan_json(raw_output)

    assert "structure_id=T2" in caplog.text
    assert "branch=exit" in caplog.text
    assert "intent=terminate" in caplog.text
    assert "raw_planner_output=" in caplog.text
    assert "parsed_branch_plan={'structure_id': 'T2', 'branch': 'exit', 'intent': 'terminate', 'steps': []}" in caplog.text


def test_generate_semantic_sketch_plan_rejects_missing_required_root_slot() -> None:
    process_text = "A customer submits a cloud deployment request. After both activities have been completed successfully, the deployment manager reviews the deployment request and decides whether to approve it."
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["infrastructure", "security"],
                "purpose": "run deployment tracks concurrently",
            },
            {
                "id": "T4",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["cancelled", "approved"],
                "purpose": "decide if the deployment request is approved",
            },
        ]
    }
    raw_semantic_plan = """
    {
      "root_actions": [
        {"slot_id": "ROOT_START", "action": "submit deployment request"},
        {"slot_id": "AFTER_T4", "action": "conduct compliance review"}
      ],
      "branch_plans": [
        {"structure_id": "T1", "branch": "infrastructure", "intent": "continue", "steps": [{"action": "provision servers"}]},
        {"structure_id": "T1", "branch": "security", "intent": "continue", "steps": [{"action": "validate security policies"}]},
        {"structure_id": "T4", "branch": "cancelled", "intent": "terminate", "steps": [{"action": "cancel deployment request"}]},
        {"structure_id": "T4", "branch": "approved", "intent": "continue", "steps": []}
      ]
    }
    """

    with patch("llm.semantic_sketch_experiment.call_openai", return_value=raw_semantic_plan):
        with pytest.raises(SemanticSketchPlanGenerationError, match="missing_root_slots"):
            generate_semantic_sketch_plan(
                process_text,
                topology_artifact=topology_artifact,
                model="gpt-4o",
            )


def test_generate_semantic_sketch_plan_retries_after_missing_root_slot_failure() -> None:
    process_text = "A customer submits a cloud deployment request. After both activities have been completed successfully, the deployment manager reviews the deployment request and decides whether to approve it."
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["infrastructure", "security"],
                "purpose": "run deployment tracks concurrently",
            },
            {
                "id": "T4",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["cancelled", "approved"],
                "purpose": "decide if the deployment request is approved",
            },
        ]
    }
    invalid_semantic_plan = """
    {
      "root_actions": [
        {"slot_id": "ROOT_START", "action": "submit deployment request"},
        {"slot_id": "AFTER_T4", "action": "conduct compliance review"}
      ],
      "branch_plans": [
        {"structure_id": "T1", "branch": "infrastructure", "intent": "continue", "steps": [{"action": "provision servers"}]},
        {"structure_id": "T1", "branch": "security", "intent": "continue", "steps": [{"action": "validate security policies"}]},
        {"structure_id": "T4", "branch": "cancelled", "intent": "terminate", "steps": [{"action": "cancel deployment request"}]},
        {"structure_id": "T4", "branch": "approved", "intent": "continue", "steps": []}
      ]
    }
    """
    valid_semantic_plan = """
    {
      "root_actions": [
        {"slot_id": "ROOT_START", "action": "submit deployment request"},
        {"slot_id": "AFTER_T1", "action": "conduct compliance review"},
        {"slot_id": "AFTER_T4", "action": "complete deployment rollout"}
      ],
      "branch_plans": [
        {"structure_id": "T1", "branch": "infrastructure", "intent": "continue", "steps": [{"action": "provision servers"}]},
        {"structure_id": "T1", "branch": "security", "intent": "continue", "steps": [{"action": "validate security policies"}]},
        {"structure_id": "T4", "branch": "cancelled", "intent": "terminate", "steps": [{"action": "cancel deployment request"}]},
        {"structure_id": "T4", "branch": "approved", "intent": "continue", "steps": []}
      ]
    }
    """

    with patch("llm.semantic_sketch_experiment.call_openai", side_effect=[invalid_semantic_plan, valid_semantic_plan]) as mocked_call:
        result = generate_semantic_sketch_plan(
            process_text,
            topology_artifact=topology_artifact,
            model="gpt-4o",
        )

    assert [entry["slot_id"] for entry in result["artifact"]["root_actions"]] == ["ROOT_START", "AFTER_T1", "AFTER_T4"]
    assert len(result["planner_attempts"]) == 2
    retry_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "Required root-slot sequence" in retry_prompt
    assert "missing_root_slots=['AFTER_T1']" in retry_prompt
    assert "misplaced_root_actions" in retry_prompt


def test_generate_semantic_sketch_plan_retries_after_misplaced_root_action_failure() -> None:
    process_text = "A customer submits a cloud deployment request. After both activities have been completed successfully, the deployment manager reviews the deployment request and decides whether to approve it."
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["infrastructure", "security"],
                "purpose": "run deployment tracks concurrently",
            },
            {
                "id": "T4",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["cancelled", "approved"],
                "purpose": "decide if the deployment request is approved",
            },
        ]
    }
    invalid_semantic_plan = """
    {
      "root_actions": [
        {"slot_id": "ROOT_START", "action": "submit deployment request"},
        {"slot_id": "AFTER_T4", "action": "conduct compliance review"},
        {"slot_id": "AFTER_T4", "action": "complete deployment rollout"}
      ],
      "branch_plans": [
        {"structure_id": "T1", "branch": "infrastructure", "intent": "continue", "steps": [{"action": "provision servers"}]},
        {"structure_id": "T1", "branch": "security", "intent": "continue", "steps": [{"action": "validate security policies"}]},
        {"structure_id": "T4", "branch": "cancelled", "intent": "terminate", "steps": [{"action": "cancel deployment request"}]},
        {"structure_id": "T4", "branch": "approved", "intent": "continue", "steps": []}
      ]
    }
    """
    valid_semantic_plan = """
    {
      "root_actions": [
        {"slot_id": "ROOT_START", "action": "submit deployment request"},
        {"slot_id": "AFTER_T1", "action": "conduct compliance review"},
        {"slot_id": "AFTER_T4", "action": "complete deployment rollout"}
      ],
      "branch_plans": [
        {"structure_id": "T1", "branch": "infrastructure", "intent": "continue", "steps": [{"action": "provision servers"}]},
        {"structure_id": "T1", "branch": "security", "intent": "continue", "steps": [{"action": "validate security policies"}]},
        {"structure_id": "T4", "branch": "cancelled", "intent": "terminate", "steps": [{"action": "cancel deployment request"}]},
        {"structure_id": "T4", "branch": "approved", "intent": "continue", "steps": []}
      ]
    }
    """

    with patch("llm.semantic_sketch_experiment.call_openai", side_effect=[invalid_semantic_plan, valid_semantic_plan]):
        result = generate_semantic_sketch_plan(
            process_text,
            topology_artifact=topology_artifact,
            model="gpt-4o",
        )

    assert [entry["slot_id"] for entry in result["artifact"]["root_actions"]] == ["ROOT_START", "AFTER_T1", "AFTER_T4"]


def test_generate_semantic_sketch_plan_retry_exhaustion_keeps_failure_explicit() -> None:
    process_text = "A customer submits a cloud deployment request. After both activities have been completed successfully, the deployment manager reviews the deployment request and decides whether to approve it."
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["infrastructure", "security"],
                "purpose": "run deployment tracks concurrently",
            },
            {
                "id": "T4",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["cancelled", "approved"],
                "purpose": "decide if the deployment request is approved",
            },
        ]
    }
    invalid_semantic_plan = """
    {
      "root_actions": [
        {"slot_id": "ROOT_START", "action": "submit deployment request"},
        {"slot_id": "AFTER_T4", "action": "root_scope_3"}
      ],
      "branch_plans": [
        {"structure_id": "T1", "branch": "infrastructure", "intent": "continue", "steps": [{"action": "provision servers"}]},
        {"structure_id": "T1", "branch": "security", "intent": "continue", "steps": [{"action": "validate security policies"}]},
        {"structure_id": "T4", "branch": "cancelled", "intent": "terminate", "steps": [{"action": "cancel deployment request"}]},
        {"structure_id": "T4", "branch": "approved", "intent": "continue", "steps": []}
      ]
    }
    """

    with patch("llm.semantic_sketch_experiment.call_openai", side_effect=[invalid_semantic_plan, invalid_semantic_plan, invalid_semantic_plan]):
        with pytest.raises(SemanticSketchPlanGenerationError, match="missing_root_slots") as exc_info:
            generate_semantic_sketch_plan(
                process_text,
                topology_artifact=topology_artifact,
                model="gpt-4o",
            )

    assert len(exc_info.value.debug_artifacts["semantic_attempts"]) == 3
    assert "root_scope_" in exc_info.value.debug_artifacts["semantic_raw_output"]
    assert "placeholder_root_actions" in exc_info.value.debug_artifacts["semantic_validation_error"]


def test_preserve_explicit_business_activities_restores_missing_review_before_nested_decision() -> None:
    process_text = (
        "If additional compliance approval is required, the compliance officer reviews the request. "
        "If the compliance officer approves it, the application is deployed. Otherwise, the deployment request is rejected."
    )
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["needs_review", "no_review"],
                "purpose": "determine if additional compliance approval is required",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "T1",
                "parent_branch": "needs_review",
                "branches": ["approved", "rejected"],
                "purpose": "compliance officer approval decision",
            },
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "review deployment request"},
            {"slot_id": "AFTER_T1", "action": "complete deployment process"},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "needs_review", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "no_review", "intent": "continue", "steps": [{"action": "deploy application"}]},
            {"structure_id": "T2", "branch": "approved", "intent": "continue", "steps": [{"action": "deploy application"}]},
            {"structure_id": "T2", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject deployment request"}]},
        ],
    }

    enriched = preserve_explicit_business_activities(
        process_text,
        topology_artifact=topology_artifact,
        semantic_plan=semantic_plan,
    )
    branch_steps = {
        (entry["structure_id"], entry["branch"]): [step["action"] for step in entry["steps"]]
        for entry in enriched["branch_plans"]
    }

    assert branch_steps[("T1", "needs_review")] == ["compliance officer reviews request"]


def test_generate_semantic_sketch_plan_does_not_apply_experimental_recovery_in_pipeline() -> None:
    process_text = (
        "If additional compliance approval is required, the compliance officer reviews the request. "
        "If the compliance officer approves it, the application is deployed. Otherwise, the deployment request is rejected."
    )
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["needs_review", "no_review"],
                "purpose": "determine if additional compliance approval is required",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "T1",
                "parent_branch": "needs_review",
                "branches": ["approved", "rejected"],
                "purpose": "compliance officer approval decision",
            },
        ]
    }
    raw_semantic_plan = """
    {
      "root_actions": [
        {"slot_id": "ROOT_START", "action": "review deployment request"},
        {"slot_id": "AFTER_T1", "action": "complete deployment process"}
      ],
      "branch_plans": [
        {"structure_id": "T1", "branch": "needs_review", "intent": "continue", "steps": []},
        {"structure_id": "T1", "branch": "no_review", "intent": "continue", "steps": [{"action": "deploy application"}]},
        {"structure_id": "T2", "branch": "approved", "intent": "continue", "steps": [{"action": "deploy application"}]},
        {"structure_id": "T2", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject deployment request"}]}
      ]
    }
    """

    with patch("llm.semantic_sketch_experiment.call_openai", return_value=raw_semantic_plan):
        result = generate_semantic_sketch_plan(
            process_text,
            topology_artifact=topology_artifact,
            model="gpt-4o",
        )

    branch_steps = {
        (entry["structure_id"], entry["branch"]): [step["action"] for step in entry["steps"]]
        for entry in result["artifact"]["branch_plans"]
    }
    assert branch_steps[("T1", "needs_review")] == []


def test_preserve_explicit_business_activities_does_not_modify_loop_retry_semantics() -> None:
    process_text = (
        "The security team validates security policies. "
        "If security validation fails, the security team updates the policies and repeats "
        "the validation process until all requirements are satisfied."
    )
    topology_artifact = {
        "structures": [
            {
                "id": "T3",
                "type": "loop",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["retry", "success"],
                "purpose": "validation passed",
            }
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "validate security policies"},
            {"slot_id": "AFTER_T3", "action": "continue deployment process"},
        ],
        "branch_plans": [
            {
                "structure_id": "T3",
                "branch": "retry",
                "intent": "loop_back",
                "steps": [{"action": "update security policies"}],
            },
            {
                "structure_id": "T3",
                "branch": "success",
                "intent": "continue",
                "steps": [],
            },
        ],
    }

    enriched = preserve_explicit_business_activities(
        process_text,
        topology_artifact=topology_artifact,
        semantic_plan=semantic_plan,
    )

    assert enriched == {
        **semantic_plan,
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "validate security policies"}]},
            {"slot_id": "AFTER_T3", "actions": [{"action": "continue deployment process"}]},
        ],
    }


def test_generate_semantic_sketch_plan_fails_closed_after_post_assignment_validation_errors() -> None:
    process_text = (
        "An analyst reviews the request. If approved, the analyst fulfills it. "
        "Otherwise, the analyst rejects it. In either case, the analyst records the outcome."
    )
    invalid_plan = _decision_plan(shared_actions=[], approved_steps=["fulfill request", "record outcome"])

    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        side_effect=[json.dumps(invalid_plan), json.dumps(invalid_plan), json.dumps(invalid_plan)],
    ):
        with pytest.raises(SemanticSketchPlanGenerationError, match="validation failed") as exc_info:
            generate_semantic_sketch_plan(
                process_text,
                topology_artifact=_decision_topology(),
                model="gpt-4o",
            )

    assert len(exc_info.value.debug_artifacts["semantic_attempts"]) == 3
    assert all(attempt["validation_error"] for attempt in exc_info.value.debug_artifacts["semantic_attempts"])
