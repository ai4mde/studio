from __future__ import annotations

import json
import pytest
from unittest.mock import patch

from llm.semantic_sketch_experiment import (
    SemanticCoverageEvidenceValidationError,
    SemanticOwnershipEvidenceValidationError,
    SemanticSketchPlanGenerationError,
    build_semantic_sketch_experiment_prompt,
    generate_semantic_sketch_plan,
    parse_semantic_sketch_plan_json,
    preserve_explicit_business_activities,
    semantic_sketch_plan_response_format,
    validate_semantic_coverage_against_evidence,
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

    assert "Every business action mentioned in the process text must appear exactly once somewhere in the semantic plan" in prompt
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

    with pytest.raises(
        SemanticOwnershipEvidenceValidationError,
        match=r"loop=T2, success_branch=success, expected_continuation=AFTER_T1",
    ):
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


def _nested_shared_retry_topology() -> dict:
    return {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["insured", "not_insured"],
                "purpose": "determine whether claim is insured",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "T1",
                "parent_branch": "insured",
                "branches": ["complete", "incomplete"],
                "purpose": "check claim form completeness",
            },
            {
                "id": "T3",
                "type": "loop",
                "parent": "T2",
                "parent_branch": "incomplete",
                "branches": ["correct", "complete"],
                "purpose": "correct and check claim form until complete",
            },
        ]
    }


def _nested_shared_retry_plan(*, shared_registration: bool) -> dict:
    return {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {
                "slot_id": "AFTER_T1",
                "actions": [{"action": "register claim"}] if shared_registration else [],
            },
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "insured", "intent": "continue", "steps": []},
            {
                "structure_id": "T1",
                "branch": "not_insured",
                "intent": "terminate",
                "steps": [{"action": "reject uninsured claim"}],
            },
            {
                "structure_id": "T2",
                "branch": "complete",
                "intent": "continue",
                "steps": [] if shared_registration else [{"action": "register claim"}],
            },
            {
                "structure_id": "T2",
                "branch": "incomplete",
                "intent": "continue",
                "steps": [{"action": "request claim form correction"}],
            },
            {
                "structure_id": "T3",
                "branch": "correct",
                "intent": "loop_back",
                "steps": [{"action": "correct claim form"}],
            },
            {"structure_id": "T3", "branch": "complete", "intent": "continue", "steps": []},
        ],
    }


def test_semantic_loop_validator_allows_safe_shared_retry_success_continuation() -> None:
    process_text = (
        "If the claim is not insured, reject it and end processing. For an insured claim, check the form. "
        "If complete, register the claim. Otherwise correct and check the form again until complete, then "
        "register the claim."
    )
    invalid_plan = _nested_shared_retry_plan(shared_registration=False)

    with pytest.raises(
        SemanticOwnershipEvidenceValidationError,
        match=r"allowed_shared_slot=AFTER_T1.*register claim",
    ) as exc_info:
        validate_semantic_ownership_against_evidence(
            process_text,
            topology_artifact=_nested_shared_retry_topology(),
            semantic_plan=invalid_plan,
        )

    diagnostic = str(exc_info.value)
    assert "validator-approved constrained ownership relocation" in diagnostic
    assert 'exact_action="register claim"' in diagnostic
    assert "invalid_owner=branch_plans[structure_id=T2,branch=complete].steps" in diagnostic
    assert "allowed_destination=root_actions[slot_id=AFTER_T1].actions" in diagnostic
    assert "REMOVE exact_action from invalid_owner" in diagnostic
    assert "ADD exact_action exactly once to allowed_destination" in diagnostic
    assert "preserve=all_other_actions,intents,target_slot_ids,topology_handles,branch_structure" in diagnostic

    valid_plan = _nested_shared_retry_plan(shared_registration=True)
    assert validate_semantic_ownership_against_evidence(
        process_text,
        topology_artifact=_nested_shared_retry_topology(),
        semantic_plan=valid_plan,
    ) == valid_plan
    assert valid_plan["branch_plans"][1]["intent"] == "terminate"


def test_generate_semantic_plan_applies_only_validator_approved_shared_relocation() -> None:
    process_text = (
        "If the claim is not insured, reject it and end processing. For an insured claim, check the form. "
        "If complete, register the claim. Otherwise request correction and check the form again until complete, "
        "then register the claim."
    )
    invalid_plan = _nested_shared_retry_plan(shared_registration=False)
    corrected_plan = _nested_shared_retry_plan(shared_registration=True)

    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        side_effect=[json.dumps(invalid_plan), json.dumps(corrected_plan)],
    ) as mocked_call:
        result = generate_semantic_sketch_plan(
            process_text,
            topology_artifact=_nested_shared_retry_topology(),
        )

    assert len(result["planner_attempts"]) == 2
    correction_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "validator-approved constrained ownership relocation" in correction_prompt
    assert 'exact_action="register claim"' in correction_prompt
    assert "REMOVE exact_action from invalid_owner" in correction_prompt
    assert "ADD exact_action exactly once to allowed_destination" in correction_prompt
    assert "overrides the generic branch-local preference for the exact cited Action only" in correction_prompt
    assert "Use the previous parsed plan as the preservation baseline" in correction_prompt
    assert "Preserve every unrelated Action, intent, target_slot_id, topology handle, and branch structure" in correction_prompt

    artifact = result["artifact"]
    all_actions = [
        step["action"]
        for root in artifact["root_actions"]
        for step in root["actions"]
    ] + [
        step["action"]
        for branch in artifact["branch_plans"]
        for step in branch["steps"]
    ]
    assert all_actions.count("register claim") == 1
    assert artifact["root_actions"][1]["actions"] == [{"action": "register claim"}]
    assert artifact["branch_plans"][2]["steps"] == []
    assert artifact["branch_plans"][3:] == corrected_plan["branch_plans"][3:]
    assert artifact["branch_plans"][1]["intent"] == "terminate"
    assert "root_scope_" not in json.dumps(artifact)


def test_semantic_loop_validator_does_not_constrain_relocation_across_later_structure() -> None:
    topology = _nested_shared_retry_topology()
    topology["structures"].append(
        {
            "id": "T4",
            "type": "decision",
            "parent": "T1",
            "parent_branch": "insured",
            "branches": ["manual", "automatic"],
            "purpose": "select registration handling",
        }
    )
    plan = _nested_shared_retry_plan(shared_registration=False)
    plan["branch_plans"].extend(
        [
            {"structure_id": "T4", "branch": "manual", "intent": "continue", "steps": []},
            {"structure_id": "T4", "branch": "automatic", "intent": "continue", "steps": []},
        ]
    )

    with pytest.raises(SemanticOwnershipEvidenceValidationError) as exc_info:
        validate_semantic_ownership_against_evidence(
            "If complete, register the claim. Otherwise correct and check again until complete. "
            "Afterwards select manual or automatic registration handling.",
            topology_artifact=topology,
            semantic_plan=plan,
        )

    diagnostic = str(exc_info.value)
    assert "allowed_shared_slot=AFTER_T1" in diagnostic
    assert "validator-approved constrained ownership relocation" not in diagnostic


def _unsafe_nested_continuation_plan(*, action_at_root: bool) -> dict:
    return {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {
                "slot_id": "AFTER_T1",
                "actions": [
                    *([{"action": "generate purchase order"}] if action_at_root else []),
                    {"action": "send outcome notification"},
                ],
            },
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "change_required", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "continue", "steps": []},
            {
                "structure_id": "T2",
                "branch": "vendor_valid",
                "intent": "continue",
                "steps": [] if action_at_root else [{"action": "generate purchase order"}],
            },
            {"structure_id": "T2", "branch": "vendor_invalid", "intent": "continue", "steps": []},
            {
                "structure_id": "T3",
                "branch": "correct",
                "intent": "loop_back",
                "steps": [{"action": "correct vendor data"}],
            },
            {"structure_id": "T3", "branch": "vendor_valid", "intent": "continue", "steps": []},
        ],
    }


def _unsafe_nested_continuation_topology() -> dict:
    return {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "change_required", "rejected"],
                "purpose": "decide request outcome",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "T1",
                "parent_branch": "approved",
                "branches": ["vendor_valid", "vendor_invalid"],
                "purpose": "validate vendor data",
            },
            {
                "id": "T3",
                "type": "loop",
                "parent": "T2",
                "parent_branch": "vendor_invalid",
                "branches": ["correct", "vendor_valid"],
                "purpose": "correct vendor data until valid",
            },
        ]
    }


@pytest.mark.parametrize("action_at_root", [False, True])
def test_semantic_loop_validator_rejects_unsafe_global_nested_continuation(
    action_at_root: bool,
) -> None:
    process_text = (
        "If approved, validate vendor data. When vendor data is valid, generate a purchase order. "
        "If invalid, correct it until valid. Change requests and rejections continue without a purchase order. "
        "In all cases, send an outcome notification."
    )

    with pytest.raises(
        SemanticOwnershipEvidenceValidationError,
        match=r"unrepresentable under the current root-slot model.*generate purchase order",
    ) as exc_info:
        validate_semantic_ownership_against_evidence(
            process_text,
            topology_artifact=_unsafe_nested_continuation_topology(),
            semantic_plan=_unsafe_nested_continuation_plan(action_at_root=action_at_root),
        )

    assert "do not relocate it to root/shared scope" in str(exc_info.value)
    assert "root_scope_*" in str(exc_info.value)
    assert "validator-approved constrained ownership relocation" not in str(exc_info.value)


def test_semantic_ownership_validator_uses_retry_structure_instead_of_negative_branch_name() -> None:
    process_text = (
        "The submission is checked. If it passes, the submission is archived. "
        "Otherwise, the submitter corrects it. The corrected submission is checked again until it passes."
    )

    with pytest.raises(
        SemanticOwnershipEvidenceValidationError,
        match=r"loop=T2, success_branch=cycle_b, expected_continuation=AFTER_T1",
    ):
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

    with pytest.raises(
        SemanticOwnershipEvidenceValidationError,
        match=r"loop=T3, success_branch=cycle_b, expected_continuation=AFTER_T1",
    ):
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
    assert "loop=T2, success_branch=cycle_b, expected_continuation=AFTER_T1" in result["planner_attempts"][0]["validation_error"]
    assert result["planner_attempts"][1]["validation_error"] is None


def _explicit_review_return_topology() -> dict:
    return {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
                "purpose": "supervisor reviews the report",
            },
            {
                "id": "T2",
                "type": "loop",
                "parent": "T1",
                "parent_branch": "rejected",
                "branches": ["retry", "resubmit"],
                "purpose": "correct and resubmit the rejected report",
            },
        ]
    }


def _explicit_review_return_plan(*, target_slot_id: str | None) -> dict:
    success_plan = {
        "structure_id": "T2",
        "branch": "resubmit",
        "intent": "continue",
        "steps": [],
    }
    if target_slot_id is not None:
        success_plan["target_slot_id"] = target_slot_id
    return {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "submit report"}]},
            {"slot_id": "AFTER_T1", "actions": [{"action": "process approved report"}]},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "continue", "steps": [{"action": "reject report"}]},
            {"structure_id": "T2", "branch": "retry", "intent": "loop_back", "steps": [{"action": "correct and resubmit report"}]},
            success_plan,
        ],
    }


def test_semantic_loop_validator_requires_one_retry_and_one_success_exit() -> None:
    plan = _explicit_review_return_plan(target_slot_id="ROOT_START")
    plan["branch_plans"][-1]["intent"] = "loop_back"
    plan["branch_plans"][-1]["steps"] = [{"action": "return report for another correction"}]

    with pytest.raises(
        SemanticOwnershipEvidenceValidationError,
        match=r"loop=T2 requires exactly one retry branch.*one successful exit branch",
    ):
        validate_semantic_ownership_against_evidence(
            "A rejected report is corrected and returned for review until approved.",
            topology_artifact=_explicit_review_return_topology(),
            semantic_plan=plan,
        )


@pytest.mark.parametrize("terminal_branch", ["cost_unacceptable", "rejected", "cancelled", "aborted"])
def test_semantic_loop_validator_does_not_treat_terminal_failure_as_ordinary_success(
    terminal_branch: str,
) -> None:
    topology = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["repair", terminal_branch],
                "purpose": "decide whether repair should continue",
            },
            {
                "id": "T2",
                "type": "loop",
                "parent": "T1",
                "parent_branch": "repair",
                "branches": ["retry", "success"],
                "purpose": "repair and test until successful",
            },
        ]
    }
    plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "calculate repair cost"}]},
            {"slot_id": "AFTER_T1", "actions": [{"action": "finish repair"}]},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "repair", "intent": "continue", "steps": []},
            {
                "structure_id": "T1",
                "branch": terminal_branch,
                "intent": "terminate",
                "steps": [{"action": "return computer unrepaired"}],
            },
            {
                "structure_id": "T2",
                "branch": "retry",
                "intent": "loop_back",
                "steps": [{"action": "repair computer again"}],
            },
            {"structure_id": "T2", "branch": "success", "intent": "continue", "steps": []},
        ],
    }

    assert validate_semantic_ownership_against_evidence(
        "If the cost is unacceptable, the customer takes the computer home unrepaired. "
        "Otherwise it is repaired and tested until successful, after which the repair is finished.",
        topology_artifact=topology,
        semantic_plan=plan,
    ) == plan


def test_semantic_loop_validator_requires_explicit_review_return_target() -> None:
    process_text = (
        "The supervisor reviews and rejects the report. The employee corrects and resubmits it. "
        "A corrected report must again go to the supervisor for review."
    )

    with pytest.raises(
        SemanticOwnershipEvidenceValidationError,
        match=r"loop=T2, retry_branch=retry, success_branch=resubmit, expected_continuation=ROOT_START",
    ):
        validate_semantic_ownership_against_evidence(
            process_text,
            topology_artifact=_explicit_review_return_topology(),
            semantic_plan=_explicit_review_return_plan(target_slot_id=None),
        )


def test_semantic_loop_validator_accepts_explicit_review_return_without_relocating_branch_actions() -> None:
    process_text = (
        "The supervisor reviews and rejects the report. The employee corrects and resubmits it. "
        "A corrected report must again go to the supervisor for review."
    )
    plan = _explicit_review_return_plan(target_slot_id="ROOT_START")

    assert validate_semantic_ownership_against_evidence(
        process_text,
        topology_artifact=_explicit_review_return_topology(),
        semantic_plan=plan,
    ) == plan
    assert plan["branch_plans"][1]["steps"] == [{"action": "reject report"}]
    assert plan["branch_plans"][2]["steps"] == [{"action": "correct and resubmit report"}]


def test_semantic_loop_validator_accepts_only_derived_earlier_review_target() -> None:
    topology = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["prepared", "manual"],
                "purpose": "prepare report route",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
                "purpose": "supervisor reviews report",
            },
            {
                "id": "T3",
                "type": "loop",
                "parent": "T2",
                "parent_branch": "rejected",
                "branches": ["correct", "approved"],
                "purpose": "correct rejected report and return for supervisor review",
            },
        ]
    }

    def plan(target_slot_id: str) -> dict:
        return {
            "root_actions": [
                {"slot_id": "ROOT_START", "actions": [{"action": "prepare report"}]},
                {"slot_id": "AFTER_T1", "actions": [{"action": "submit report for supervisor review"}]},
                {"slot_id": "AFTER_T2", "actions": [{"action": "archive approved report"}]},
            ],
            "branch_plans": [
                {"structure_id": "T1", "branch": "prepared", "intent": "continue", "steps": []},
                {"structure_id": "T1", "branch": "manual", "intent": "continue", "steps": []},
                {"structure_id": "T2", "branch": "approved", "intent": "continue", "steps": []},
                {"structure_id": "T2", "branch": "rejected", "intent": "continue", "steps": []},
                {
                    "structure_id": "T3",
                    "branch": "correct",
                    "intent": "loop_back",
                    "steps": [{"action": "correct report"}],
                },
                {
                    "structure_id": "T3",
                    "branch": "approved",
                    "intent": "continue",
                    "steps": [],
                    "target_slot_id": target_slot_id,
                },
            ],
        }

    process_text = (
        "Prepare and submit the report for supervisor review. If rejected, correct it; it is sent back to the "
        "supervisor for review again until approved. Then archive the approved report."
    )
    with pytest.raises(
        SemanticOwnershipEvidenceValidationError,
        match=r"allowed_target_slot_id=AFTER_T1, current_target=AFTER_T2",
    ):
        validate_semantic_ownership_against_evidence(
            process_text,
            topology_artifact=topology,
            semantic_plan=plan("AFTER_T2"),
        )

    accepted = plan("AFTER_T1")
    assert validate_semantic_ownership_against_evidence(
        process_text,
        topology_artifact=topology,
        semantic_plan=accepted,
    ) == accepted


def test_semantic_loop_validator_preserves_multi_root_slot_ordering() -> None:
    topology = {
        "structures": [
            {"id": "T1", "type": "decision", "parent": "ROOT", "parent_branch": None, "branches": ["yes", "no"], "purpose": "check request"},
            {"id": "T2", "type": "loop", "parent": "ROOT", "parent_branch": None, "branches": ["retry", "complete"], "purpose": "revise until complete"},
            {"id": "T3", "type": "decision", "parent": "ROOT", "parent_branch": None, "branches": ["send", "hold"], "purpose": "route result"},
        ]
    }
    plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "receive request"}]},
            {"slot_id": "AFTER_T1", "actions": [{"action": "prepare request"}]},
            {"slot_id": "AFTER_T2", "actions": [{"action": "record completion"}]},
            {"slot_id": "AFTER_T3", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "yes", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "no", "intent": "continue", "steps": []},
            {"structure_id": "T2", "branch": "retry", "intent": "loop_back", "steps": [{"action": "revise request"}]},
            {"structure_id": "T2", "branch": "complete", "intent": "continue", "steps": []},
            {"structure_id": "T3", "branch": "send", "intent": "continue", "steps": [{"action": "send result"}]},
            {"structure_id": "T3", "branch": "hold", "intent": "continue", "steps": [{"action": "hold result"}]},
        ],
    }

    assert validate_semantic_ownership_against_evidence(
        "Receive and prepare the request. Revise it until complete, record completion, and route the result.",
        topology_artifact=topology,
        semantic_plan=plan,
    ) == plan
    assert [entry["slot_id"] for entry in plan["root_actions"]] == [
        "ROOT_START",
        "AFTER_T1",
        "AFTER_T2",
        "AFTER_T3",
    ]


def test_semantic_loop_validator_does_not_enforce_ambiguous_continuation() -> None:
    plan = _explicit_review_return_plan(target_slot_id=None)

    assert validate_semantic_ownership_against_evidence(
        "The employee corrects the rejected report. Later processing may continue.",
        topology_artifact=_explicit_review_return_topology(),
        semantic_plan=plan,
    ) == plan


def test_generate_semantic_plan_loop_correction_is_targeted_and_has_no_placeholder() -> None:
    process_text = (
        "The supervisor reviews and rejects the report. The employee corrects and resubmits it. "
        "A corrected report must again go to the supervisor for review."
    )
    invalid = _explicit_review_return_plan(target_slot_id=None)
    corrected = _explicit_review_return_plan(target_slot_id="ROOT_START")

    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        side_effect=[json.dumps(invalid), json.dumps(corrected)],
    ) as mocked_call:
        result = generate_semantic_sketch_plan(
            process_text,
            topology_artifact=_explicit_review_return_topology(),
        )

    assert len(result["planner_attempts"]) == 2
    diagnostic = result["planner_attempts"][0]["validation_error"]
    assert "loop=T2" in diagnostic
    assert "success_branch=resubmit" in diagnostic
    assert "expected_continuation=ROOT_START" in diagnostic
    assert "retry_target=ROOT_START" in diagnostic
    assert "retry_success_continuation remains separate" in diagnostic
    retry_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "Loop-success-continuation correction" in retry_prompt
    assert "Preserve the authoritative topology, unrelated root actions, and branch-local actions" in retry_prompt
    assert "Treat retry_target and retry_success_continuation as distinct concepts" in retry_prompt
    assert "root_scope_" not in json.dumps(result["artifact"])


def test_generate_semantic_plan_persistent_loop_continuation_failure_uses_three_attempts() -> None:
    process_text = (
        "The supervisor reviews and rejects the report. The employee corrects and resubmits it. "
        "A corrected report must again go to the supervisor for review."
    )
    invalid = json.dumps(_explicit_review_return_plan(target_slot_id=None))

    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        side_effect=[invalid, invalid, invalid],
    ) as mocked_call:
        with pytest.raises(SemanticSketchPlanGenerationError) as exc_info:
            generate_semantic_sketch_plan(
                process_text,
                topology_artifact=_explicit_review_return_topology(),
            )

    assert mocked_call.call_count == 3
    attempts = exc_info.value.debug_artifacts["semantic_attempts"]
    assert len(attempts) == 3
    assert all("loop-success-continuation evidence" in attempt["validation_error"] for attempt in attempts)


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


def _linear_plan(*actions: str) -> dict:
    return {
        "root_actions": [
            {
                "slot_id": "ROOT_START",
                "actions": [{"action": action} for action in actions],
            }
        ],
        "branch_plans": [],
    }


@pytest.mark.parametrize(
    "process_text",
    [
        "The supervisor reviews the request.",
        "The request is reviewed by the supervisor.",
    ],
)
def test_semantic_coverage_accepts_active_and_passive_equivalence(process_text: str) -> None:
    plan = _linear_plan("review request")

    assert validate_semantic_coverage_against_evidence(
        process_text,
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_accepts_narrow_operation_synonym_with_same_object() -> None:
    plan = _linear_plan("review invoice")

    assert validate_semantic_coverage_against_evidence(
        "The accountant examines the invoice.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_distinguishes_same_operation_with_different_object() -> None:
    with pytest.raises(SemanticCoverageEvidenceValidationError) as exc_info:
        validate_semantic_coverage_against_evidence(
            "The supervisor reviews the invoice.",
            topology_artifact={"structures": []},
            semantic_plan=_linear_plan("review request"),
        )

    assert exc_info.value.issues[0]["objects"] == ["invoice"]
    assert exc_info.value.issues[0]["scope_hint"] == "ROOT_START"


@pytest.mark.parametrize(
    "process_text",
    [
        "If the request is approved.",
        "The request is approved.",
        "After five days the request remains ready.",
        "When the request is received.",
        "The supervisor belongs to the finance department.",
        "The process of winning a new customer ends here.",
    ],
)
def test_semantic_coverage_ignores_context_without_executable_activity(process_text: str) -> None:
    plan = _linear_plan()

    assert validate_semantic_coverage_against_evidence(
        process_text,
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_does_not_treat_conditional_state_as_body_operation() -> None:
    plan = _linear_plan("finalize request")

    assert validate_semantic_coverage_against_evidence(
        "If approved, finalize it.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_counts_decision_semantics_without_duplicate_action() -> None:
    topology = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
                "purpose": "check request approval",
            }
        ]
    }
    plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {
                "structure_id": "T1",
                "branch": "rejected",
                "intent": "terminate",
                "steps": [{"action": "reject request"}],
            },
        ],
    }

    assert validate_semantic_coverage_against_evidence(
        "The supervisor reviews the request and decides whether it is approved.",
        topology_artifact=topology,
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_ignores_compound_decision_outcome_wording() -> None:
    topology = _decision_topology()
    plan = _decision_plan(shared_actions=[])

    assert validate_semantic_coverage_against_evidence(
        "The department does not approve the request, rejects it, and requests correction.",
        topology_artifact=topology,
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_recognizes_shared_continuation_with_of_the_cases() -> None:
    topology = _decision_topology()
    plan = _decision_plan(shared_actions=[])

    with pytest.raises(SemanticCoverageEvidenceValidationError) as exc_info:
        validate_semantic_coverage_against_evidence(
            "In any of the cases, send the notification.",
            topology_artifact=topology,
            semantic_plan=plan,
        )

    assert exc_info.value.issues[0]["scope_hint"] == "AFTER_T1"


def test_semantic_coverage_does_not_infer_scope_from_one_generic_object_token() -> None:
    topology = _decision_topology()
    plan = _decision_plan(shared_actions=[])
    plan["root_actions"][0]["actions"] = [{"action": "create process instance"}]

    assert validate_semantic_coverage_against_evidence(
        "Ship the bicycle to the customer and finish the process instance.",
        topology_artifact=topology,
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_does_not_infer_branch_scope_from_operation_word() -> None:
    topology = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["document_correct", "document_incorrect"],
                "purpose": "check document correctness",
            }
        ]
    }
    plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "document_correct", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "document_incorrect", "intent": "continue", "steps": []},
        ],
    }

    assert validate_semantic_coverage_against_evidence(
        "In case of errors these should be corrected using an error list.",
        topology_artifact=topology,
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_does_not_place_anaphoric_branch_activity_at_root() -> None:
    topology = _decision_topology()
    plan = _decision_plan(shared_actions=[])

    assert validate_semantic_coverage_against_evidence(
        "The clerk rejects or accepts the order. In the latter case, the storehouse is informed.",
        topology_artifact=topology,
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_preserves_valid_compound_action() -> None:
    plan = _linear_plan("prepare and send report")

    assert validate_semantic_coverage_against_evidence(
        "The clerk prepares and sends the report.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_distinguishes_clearly_separate_operations() -> None:
    with pytest.raises(SemanticCoverageEvidenceValidationError) as exc_info:
        validate_semantic_coverage_against_evidence(
            "The clerk prepares the report. The clerk sends the report.",
            topology_artifact={"structures": []},
            semantic_plan=_linear_plan("send report"),
        )

    assert exc_info.value.issues[0]["operations"] == ["create"]


def test_semantic_coverage_reports_only_strongest_of_multiple_omissions() -> None:
    with pytest.raises(SemanticCoverageEvidenceValidationError) as exc_info:
        validate_semantic_coverage_against_evidence(
            "The clerk sends the invoice. The clerk calculates the annual customer account total.",
            topology_artifact={"structures": []},
            semantic_plan=_linear_plan(),
        )

    assert len(exc_info.value.issues) == 1
    assert exc_info.value.issues[0]["operations"] == ["send"]
    assert exc_info.value.issues[0]["objects"] == ["invoice"]


def test_semantic_coverage_suppresses_waiting_constraint() -> None:
    plan = _linear_plan()

    assert validate_semantic_coverage_against_evidence(
        "The process waits for payment confirmation for seven days.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_does_not_split_partially_represented_compound_action() -> None:
    plan = _linear_plan("send report")

    assert validate_semantic_coverage_against_evidence(
        "The clerk prepares and sends the report.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_keeps_same_object_coordinated_verbs_compound() -> None:
    plan = _linear_plan("confirm and send order")

    assert validate_semantic_coverage_against_evidence(
        "The clerk confirms and sends the order.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_accepts_partially_represented_coordinated_result() -> None:
    plan = _linear_plan("resolve supplier conflict")

    assert validate_semantic_coverage_against_evidence(
        "The operator informs the suppliers and demands resolution of the supplier conflict.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_reports_only_unrepresented_part_of_compound_clause() -> None:
    process_text = (
        'In "ACME Financial Accounting", a software specially developed for ACME AG, '
        "she identifies the charging suppliers and creates a new instance (invoice)."
    )

    with pytest.raises(SemanticCoverageEvidenceValidationError) as exc_info:
        validate_semantic_coverage_against_evidence(
            process_text,
            topology_artifact={"structures": []},
            semantic_plan=_linear_plan("enter invoice into ACME Financial Accounting"),
        )

    assert exc_info.value.issues == [
        {
            "source_fragment": "she identifies the charging suppliers and creates a new instance (invoice)",
            "operations": ["identify"],
            "objects": ["charg", "supplier"],
            "qualification": "explicit executable operation with concrete business content",
            "checked_semantic_content": [],
            "scope_hint": "ROOT_START",
            "reason": "no equivalent Action or decision semantics found",
        }
    ]


def test_semantic_coverage_does_not_enforce_ambiguous_ownership() -> None:
    topology = _decision_topology()
    plan = _decision_plan(shared_actions=[])

    assert validate_semantic_coverage_against_evidence(
        "If approved, continue processing. The clerk prepares the invoice.",
        topology_artifact=topology,
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_rejection_does_not_mutate_plan() -> None:
    plan = _linear_plan()
    original = json.loads(json.dumps(plan))

    with pytest.raises(SemanticCoverageEvidenceValidationError):
        validate_semantic_coverage_against_evidence(
            "The clerk sends the invoice.",
            topology_artifact={"structures": []},
            semantic_plan=plan,
        )

    assert plan == original
    assert plan["root_actions"][0]["actions"] == []


def test_generate_semantic_plan_retries_after_coverage_failure() -> None:
    incomplete = _linear_plan()
    corrected = _linear_plan("send invoice")

    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        side_effect=[json.dumps(incomplete), json.dumps(corrected)],
    ) as mocked_call:
        result = generate_semantic_sketch_plan(
            "The clerk sends the invoice.",
            topology_artifact={"structures": []},
        )

    assert mocked_call.call_count == 2
    assert len(result["planner_attempts"]) == 2
    assert "omits high-confidence source activities" in result["planner_attempts"][0]["validation_error"]
    assert result["planner_attempts"][1]["validation_error"] is None
    assert result["artifact"] == corrected
    assert "Source-coverage correction" in mocked_call.call_args_list[1].kwargs["prompt"]
    assert "root_scope_" not in json.dumps(result["artifact"])


def test_generate_semantic_plan_persistent_coverage_failure_is_explicit() -> None:
    incomplete = json.dumps(_linear_plan())

    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        side_effect=[incomplete, incomplete, incomplete],
    ) as mocked_call:
        with pytest.raises(SemanticSketchPlanGenerationError) as exc_info:
            generate_semantic_sketch_plan(
                "The clerk sends the invoice.",
                topology_artifact={"structures": []},
            )

    assert mocked_call.call_count == 3
    attempts = exc_info.value.debug_artifacts["semantic_attempts"]
    assert len(attempts) == 3
    assert all("omits high-confidence source activities" in attempt["validation_error"] for attempt in attempts)
    assert exc_info.value.debug_artifacts["semantic_validation_error"] == attempts[-1]["validation_error"]


def test_generate_semantic_plan_never_returns_stale_post_topology_candidate() -> None:
    incomplete = json.dumps(_linear_plan("review request"))

    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        side_effect=[incomplete, incomplete, incomplete],
    ):
        with pytest.raises(SemanticSketchPlanGenerationError):
            generate_semantic_sketch_plan(
                "The clerk reviews the request. The clerk sends the invoice.",
                topology_artifact={"structures": []},
            )
