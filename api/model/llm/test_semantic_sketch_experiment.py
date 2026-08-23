from __future__ import annotations

import json
import pytest
from unittest.mock import patch

from llm.semantic_sketch_experiment import (
    SemanticCoverageEvidenceValidationError,
    SemanticOwnershipEvidenceValidationError,
    SemanticSketchPlanGenerationError,
    _build_semantic_correction_prompt,
    _enforce_semantic_correction_preservation,
    _has_explicit_parallel_branch_ownership,
    _has_explicit_parallel_join_ownership,
    _normalize_topology_artifact,
    _parallel_structure_local_fragments,
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
    assert "preserve that transfer as its own Action" in prompt
    assert "Do not merge an explicit transfer/handoff Action into an earlier action" in prompt
    assert "Do not force a separate transfer Action for incidental destination context" in prompt


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


def test_generate_semantic_plan_retries_after_missing_explicit_handoff_action() -> None:
    process_text = (
        "The nurse records the patient information on a registration form. "
        "After the conversation, the registration form is handed in at the secretarial office. "
        "The secretarial office stores the information in the information system."
    )
    incomplete = json.dumps(
        {
            "root_actions": [
                {
                    "slot_id": "ROOT_START",
                    "actions": [
                        {"action": "record patient information on registration form"},
                        {"action": "store registration information in information system"},
                    ],
                }
            ],
            "branch_plans": [],
        }
    )
    corrected = json.dumps(
        {
            "root_actions": [
                {
                    "slot_id": "ROOT_START",
                    "actions": [
                        {"action": "record patient information on registration form"},
                        {"action": "submit registration form to secretarial office"},
                        {"action": "store registration information in information system"},
                    ],
                }
            ],
            "branch_plans": [],
        }
    )

    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        side_effect=[incomplete, corrected],
    ) as mocked_call:
        result = generate_semantic_sketch_plan(
            process_text,
            topology_artifact={"structures": []},
        )

    assert mocked_call.call_count == 2
    assert result["artifact"]["root_actions"][0]["actions"] == [
        {"action": "record patient information on registration form"},
        {"action": "submit registration form to secretarial office"},
        {"action": "store registration information in information system"},
    ]
    correction_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "preserve that transfer as its own Action" in correction_prompt
    assert "Do not force a separate Action for incidental destination context" in correction_prompt


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


def _parallel_workstream_topology() -> dict:
    return {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["customer_report", "meter_data"],
                "purpose": "run customer report and meter data workstreams in parallel",
            }
        ]
    }


def _parallel_workstream_plan(
    *,
    customer_report_steps: list[str],
    meter_data_steps: list[str],
    shared_actions: list[str],
) -> dict:
    return {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": [{"action": action} for action in shared_actions]},
        ],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "customer_report",
                "intent": "continue",
                "steps": [{"action": action} for action in customer_report_steps],
            },
            {
                "structure_id": "T1",
                "branch": "meter_data",
                "intent": "continue",
                "steps": [{"action": action} for action in meter_data_steps],
            },
        ],
    }


def test_semantic_parallel_branch_ownership_rejects_misowned_customer_report_case_2_1() -> None:
    process_text = (
        "In the customer report branch, create and deliver the customer report. "
        "In the meter data branch, transmit and import meter data. "
        "After both the customer report branch and the meter data branch are complete, close the incident."
    )
    semantic_plan = _parallel_workstream_plan(
        customer_report_steps=[],
        meter_data_steps=["transmit and import meter data"],
        shared_actions=["create and deliver customer report", "close incident"],
    )

    with pytest.raises(
        SemanticOwnershipEvidenceValidationError,
        match=r"parallel-branch ownership evidence.*customer_report",
    ):
        validate_semantic_ownership_against_evidence(
            process_text,
            topology_artifact=_parallel_workstream_topology(),
            semantic_plan=semantic_plan,
        )


def test_semantic_parallel_branch_ownership_keeps_meter_data_branch_local_case_2_2() -> None:
    process_text = (
        "In the customer report branch, create and deliver the customer report. "
        "In the meter data branch, transmit and import meter data. "
        "After both the customer report branch and the meter data branch are complete, close the incident."
    )
    semantic_plan = _parallel_workstream_plan(
        customer_report_steps=["create and deliver customer report", "transmit and import meter data"],
        meter_data_steps=[],
        shared_actions=["close incident"],
    )

    with pytest.raises(
        SemanticOwnershipEvidenceValidationError,
        match=r"parallel-branch ownership evidence.*meter_data",
    ) as exc_info:
        validate_semantic_ownership_against_evidence(
            process_text,
            topology_artifact=_parallel_workstream_topology(),
            semantic_plan=semantic_plan,
        )

    assert "select supplier" not in str(exc_info.value)


def test_parallel_branch_detector_rejects_generic_send_overlap_without_domain_match() -> None:
    topology = {
        "structures": [
            {
                "id": "T4",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["send_report", "compute_billing"],
                "purpose": "transmit meter data and compute final billing in parallel",
            }
        ]
    }
    structure = _normalize_topology_artifact(topology).structures[0]

    assert not _has_explicit_parallel_branch_ownership(
        fragment="send confirmation document to customer",
        structure=structure,
        branch="send_report",
    )


def test_parallel_branch_detector_accepts_real_send_report_domain_match() -> None:
    topology = {
        "structures": [
            {
                "id": "T4",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["send_report", "compute_billing"],
                "purpose": "transmit meter data and compute final billing in parallel",
            }
        ]
    }
    structure = _normalize_topology_artifact(topology).structures[0]

    assert _has_explicit_parallel_branch_ownership(
        fragment="transmit meter data report to the supplier",
        structure=structure,
        branch="send_report",
    )


def test_parallel_branch_detector_rejects_generic_report_overlap_without_domain_match() -> None:
    topology = {
        "structures": [
            {
                "id": "T4",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["send_report", "compute_billing"],
                "purpose": "transmit meter data and compute final billing in parallel",
            }
        ]
    }
    structure = _normalize_topology_artifact(topology).structures[0]

    assert not _has_explicit_parallel_branch_ownership(
        fragment="create confirmation report for customer",
        structure=structure,
        branch="send_report",
    )


def test_parallel_branch_detector_declines_ambiguous_generic_overlap_across_multiple_branches() -> None:
    topology = {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["send_report", "review_report"],
                "purpose": "send meter data and review final billing in parallel",
            }
        ]
    }
    structure = _normalize_topology_artifact(topology).structures[0]

    assert not _has_explicit_parallel_branch_ownership(
        fragment="send report to customer",
        structure=structure,
        branch="send_report",
    )


def test_parallel_branch_detector_rejects_supplier_concurrence_without_parallel_domain_support() -> None:
    topology = {
        "structures": [
            {
                "id": "T5",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["billing_old_supplier", "billing_customer_service"],
                "purpose": "transmit meter data and create final billing in parallel",
            }
        ]
    }
    structure = _normalize_topology_artifact(topology).structures[0]

    assert not _has_explicit_parallel_branch_ownership(
        fragment="In the case of supplier concurrence the grid operator would inform all involved suppliers and demand the resolution of the conflict",
        structure=structure,
        branch="billing_old_supplier",
    )


def test_parallel_branch_detector_accepts_true_old_supplier_billing_match() -> None:
    topology = {
        "structures": [
            {
                "id": "T5",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["billing_old_supplier", "billing_customer_service"],
                "purpose": "transmit meter data and create final billing in parallel",
            }
        ]
    }
    structure = _normalize_topology_artifact(topology).structures[0]

    assert _has_explicit_parallel_branch_ownership(
        fragment="calculate final billing for the old supplier",
        structure=structure,
        branch="billing_old_supplier",
    )


def test_parallel_branch_detector_accepts_true_customer_service_branch_match() -> None:
    topology = {
        "structures": [
            {
                "id": "T5",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["billing_old_supplier", "billing_customer_service"],
                "purpose": "transmit meter data and create final billing in parallel",
            }
        ]
    }
    structure = _normalize_topology_artifact(topology).structures[0]

    assert _has_explicit_parallel_branch_ownership(
        fragment="send meter data and final billing information to customer service",
        structure=structure,
        branch="billing_customer_service",
    )


def test_parallel_branch_detector_rejects_structure_level_token_only_overlap() -> None:
    topology = {
        "structures": [
            {
                "id": "T5",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["billing_old_supplier", "billing_customer_service"],
                "purpose": "transmit meter data and create final billing in parallel",
            }
        ]
    }
    structure = _normalize_topology_artifact(topology).structures[0]

    assert not _has_explicit_parallel_branch_ownership(
        fragment="review the billing",
        structure=structure,
        branch="billing_old_supplier",
    )


def test_parallel_branch_detector_rejects_single_weak_domain_token_overlap() -> None:
    topology = {
        "structures": [
            {
                "id": "T5",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["billing_old_supplier", "billing_customer_service"],
                "purpose": "transmit meter data and create final billing in parallel",
            }
        ]
    }
    structure = _normalize_topology_artifact(topology).structures[0]

    assert not _has_explicit_parallel_branch_ownership(
        fragment="notify the supplier",
        structure=structure,
        branch="billing_old_supplier",
    )


def test_parallel_branch_detector_preserves_strong_actor_identity_overlap() -> None:
    topology = {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["kitchen_task", "waiter_task"],
                "purpose": "prepare food and drinks in parallel",
            }
        ]
    }
    structure = _normalize_topology_artifact(topology).structures[0]

    assert _has_explicit_parallel_branch_ownership(
        fragment="assign order to waiter",
        structure=structure,
        branch="waiter_task",
    )


def _source_locality_topology() -> dict:
    return {
        "structures": [
            {
                "id": "T5",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["meter_data_transmission", "billing_processing"],
                "purpose": "handle meter data and billing concurrently after switch",
            }
        ]
    }


def _source_locality_process_text() -> str:
    return (
        "The customer transmits customer data to customer service. Customer service receives the customer data.\n\n"
        "Customer service prepares the switch contract. A confirmation document is sent to the customer. "
        "The grid operator resolves any supplier concurrence conflict.\n\n"
        "On the switch date, the grid operator transmits power meter data to customer service and the old supplier. "
        "At the same time, the grid operator computes final billing from the meter data. "
        "The old supplier sends its final billing to the customer. After receiving the meter data, customer service "
        "imports it into the required systems."
    )


def test_parallel_branch_locality_rejects_distant_customer_data_but_accepts_real_meter_data() -> None:
    artifact = _normalize_topology_artifact(_source_locality_topology())
    structure = artifact.structures[0]
    local_fragments = _parallel_structure_local_fragments(_source_locality_process_text(), artifact)["T5"]

    assert _has_explicit_parallel_branch_ownership(
        fragment="The customer transmits customer data to customer service",
        structure=structure,
        branch="meter_data_transmission",
    )
    assert not _has_explicit_parallel_branch_ownership(
        fragment="The customer transmits customer data to customer service",
        structure=structure,
        branch="meter_data_transmission",
        local_fragments=local_fragments,
    )
    assert _has_explicit_parallel_branch_ownership(
        fragment="On the switch date, the grid operator transmits power meter data to customer service and the old supplier",
        structure=structure,
        branch="meter_data_transmission",
        local_fragments=local_fragments,
    )


def test_parallel_branch_locality_keeps_adjacent_same_phase_action_outside_exact_evidence() -> None:
    process_text = (
        "Open the case.\n\n"
        "The grid operator transmits power meter data. At the same time, the billing service computes final billing. "
        "The old supplier sends final billing to the customer.\n\n"
        "Send a final billing report during a later audit phase."
    )
    artifact = _normalize_topology_artifact(_source_locality_topology())
    structure = artifact.structures[0]
    local_fragments = _parallel_structure_local_fragments(process_text, artifact)["T5"]

    assert _has_explicit_parallel_branch_ownership(
        fragment="The old supplier sends final billing to the customer",
        structure=structure,
        branch="billing_processing",
        local_fragments=local_fragments,
    )
    assert _has_explicit_parallel_branch_ownership(
        fragment="Send a final billing report during a later audit phase",
        structure=structure,
        branch="billing_processing",
    )
    assert not _has_explicit_parallel_branch_ownership(
        fragment="Send a final billing report during a later audit phase",
        structure=structure,
        branch="billing_processing",
        local_fragments=local_fragments,
    )


def test_parallel_branch_locality_uses_one_adjacent_sentence_without_paragraph_boundaries() -> None:
    process_text = (
        "Open the case. The grid operator transmits power meter data. "
        "At the same time, the billing service computes final billing. "
        "The old supplier sends final billing to the customer. Archive the record."
    )
    artifact = _normalize_topology_artifact(_source_locality_topology())
    structure = artifact.structures[0]
    local_fragments = _parallel_structure_local_fragments(process_text, artifact)["T5"]

    assert _has_explicit_parallel_branch_ownership(
        fragment="The old supplier sends final billing to the customer",
        structure=structure,
        branch="billing_processing",
        local_fragments=local_fragments,
    )
    assert not _has_explicit_parallel_branch_ownership(
        fragment="Open the case",
        structure=structure,
        branch="billing_processing",
        local_fragments=local_fragments,
    )


def test_parallel_branch_locality_falls_back_when_parallel_source_evidence_is_unavailable() -> None:
    process_text = "Transmit meter data. Compute final billing."
    artifact = _normalize_topology_artifact(_source_locality_topology())
    structure = artifact.structures[0]

    assert _parallel_structure_local_fragments(process_text, artifact) == {}
    assert _has_explicit_parallel_branch_ownership(
        fragment="Transmit meter data",
        structure=structure,
        branch="meter_data_transmission",
        local_fragments=None,
    )


def test_semantic_parallel_locality_prevents_2_2_false_ownership_diagnostics() -> None:
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "receive customer data"}]},
            {"slot_id": "AFTER_T5", "actions": [{"action": "import meter data"}]},
        ],
        "branch_plans": [
            {
                "structure_id": "T5",
                "branch": "meter_data_transmission",
                "intent": "continue",
                "steps": [{"action": "transmit power meter data"}],
            },
            {
                "structure_id": "T5",
                "branch": "billing_processing",
                "intent": "continue",
                "steps": [
                    {"action": "compute final billing"},
                    {"action": "send final billing to customer"},
                ],
            },
        ],
    }

    assert validate_semantic_ownership_against_evidence(
        _source_locality_process_text(),
        topology_artifact=_source_locality_topology(),
        semantic_plan=semantic_plan,
    ) == semantic_plan


def test_semantic_parallel_locality_reports_real_t5_omission_without_claiming_root_start() -> None:
    topology = _source_locality_topology()
    topology["structures"].insert(
        0,
        {
            "id": "T4",
            "type": "decision",
            "parent": "ROOT",
            "parent_branch": None,
            "branches": ["withdraw", "confirm"],
            "purpose": "customer decides whether to withdraw or confirm",
        },
    )
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "receive customer data"}]},
            {"slot_id": "AFTER_T4", "actions": []},
            {"slot_id": "AFTER_T5", "actions": [{"action": "import meter data"}]},
        ],
        "branch_plans": [
            {
                "structure_id": "T4",
                "branch": "withdraw",
                "intent": "terminate",
                "steps": [{"action": "withdraw from contract"}],
            },
            {
                "structure_id": "T4",
                "branch": "confirm",
                "intent": "continue",
                "steps": [],
            },
            {
                "structure_id": "T5",
                "branch": "meter_data_transmission",
                "intent": "continue",
                "steps": [],
            },
            {
                "structure_id": "T5",
                "branch": "billing_processing",
                "intent": "continue",
                "steps": [{"action": "compute final billing"}],
            },
        ],
    }

    with pytest.raises(SemanticOwnershipEvidenceValidationError) as exc_info:
        validate_semantic_ownership_against_evidence(
            _source_locality_process_text(),
            topology_artifact=topology,
            semantic_plan=semantic_plan,
        )

    diagnostic = str(exc_info.value)
    assert "grid operator transmits power meter data" in diagnostic
    assert "customer transmits customer data" not in diagnostic
    assert "root_actions[ROOT_START]" not in diagnostic


def _assembly_parallel_topology() -> dict:
    return {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["storehouse", "engineering"],
                "purpose": "prepare storehouse and engineering work in parallel",
            }
        ]
    }


def _assembly_parallel_structure():
    return _normalize_topology_artifact(_assembly_parallel_topology()).structures[0]


def test_parallel_join_detector_accepts_conjoined_completion_then_business_action() -> None:
    sentence = (
        "If the storehouse has successfully reserved every item of the part list "
        "and the engineering preparation activity has finished, the engineering department assembles the bicycle."
    )

    assert _has_explicit_parallel_join_ownership(
        sentence=sentence,
        structure=_assembly_parallel_structure(),
    )


def test_parallel_join_detector_rejects_plain_sequential_and_sentence() -> None:
    sentence = "The storehouse reserves the items and the engineering department assembles the bicycle."

    assert not _has_explicit_parallel_join_ownership(
        sentence=sentence,
        structure=_assembly_parallel_structure(),
    )


def test_parallel_join_detector_rejects_two_actions_in_same_branch() -> None:
    sentence = "The storehouse has reserved the items and has packed them, then shipping prepares the dispatch."
    topology = {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["storehouse", "shipping"],
                "purpose": "run storehouse and shipping work in parallel",
            }
        ]
    }

    assert not _has_explicit_parallel_join_ownership(
        sentence=sentence,
        structure=_normalize_topology_artifact(topology).structures[0],
    )


def test_parallel_join_detector_rejects_two_branches_without_completion_semantics() -> None:
    sentence = "The storehouse and the engineering department coordinate, and the engineering department assembles the bicycle."

    assert not _has_explicit_parallel_join_ownership(
        sentence=sentence,
        structure=_assembly_parallel_structure(),
    )


def test_parallel_join_detector_rejects_completion_without_business_action() -> None:
    sentence = (
        "If the storehouse has reserved every item and the engineering preparation activity has finished, "
        "the process continues."
    )

    assert not _has_explicit_parallel_join_ownership(
        sentence=sentence,
        structure=_assembly_parallel_structure(),
    )


def test_parallel_join_detector_rejects_ambiguous_branch_identity() -> None:
    sentence = "If packing has finished and preparation has finished, the engineering department assembles the bicycle."

    assert not _has_explicit_parallel_join_ownership(
        sentence=sentence,
        structure=_assembly_parallel_structure(),
    )


def test_semantic_parallel_join_ownership_rejects_branch_owned_assembly_case_1_1() -> None:
    process_text = (
        "In the storehouse branch, process the part list and check quantities. "
        "In the engineering branch, prepare for bicycle assembling. "
        "If the storehouse has successfully reserved or back-ordered every item of the part list "
        "and the preparation activity has finished, the engineering department assembles the bicycle. "
        "Afterwards, shipping sends the bicycle to the customer."
    )
    invalid_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": [{"action": "send bicycle to customer"}]},
        ],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "storehouse",
                "intent": "continue",
                "steps": [{"action": "process part list and check quantities"}],
            },
            {
                "structure_id": "T1",
                "branch": "engineering",
                "intent": "continue",
                "steps": [
                    {"action": "prepare for bicycle assembling"},
                    {"action": "assemble bicycle"},
                ],
            },
        ],
    }

    with pytest.raises(
        SemanticOwnershipEvidenceValidationError,
        match=r"parallel-join ownership evidence.*AFTER_T1",
    ):
        validate_semantic_ownership_against_evidence(
            process_text,
            topology_artifact=_assembly_parallel_topology(),
            semantic_plan=invalid_plan,
        )

    valid_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": [{"action": "assemble bicycle"}, {"action": "send bicycle to customer"}]},
        ],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "storehouse",
                "intent": "continue",
                "steps": [{"action": "process part list and check quantities"}],
            },
            {
                "structure_id": "T1",
                "branch": "engineering",
                "intent": "continue",
                "steps": [{"action": "prepare for bicycle assembling"}],
            },
        ],
    }

    assert validate_semantic_ownership_against_evidence(
        process_text,
        topology_artifact=_assembly_parallel_topology(),
        semantic_plan=valid_plan,
    ) == valid_plan


def test_semantic_parallel_join_ownership_requires_safe_shared_slot() -> None:
    process_text = (
        "In the storehouse branch, process part list and check quantities. "
        "In the engineering branch, prepare for bicycle assembling. "
        "If the storehouse has successfully reserved every item and the engineering preparation activity has finished, "
        "the engineering department assembles the bicycle."
    )
    unsafe_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "storehouse",
                "intent": "continue",
                "steps": [{"action": "process part list and check quantities"}],
            },
            {
                "structure_id": "T1",
                "branch": "engineering",
                "intent": "terminate",
                "steps": [
                    {"action": "prepare for bicycle assembling"},
                    {"action": "assemble bicycle"},
                ],
            },
        ],
    }

    assert validate_semantic_ownership_against_evidence(
        process_text,
        topology_artifact=_assembly_parallel_topology(),
        semantic_plan=unsafe_plan,
    ) == unsafe_plan


def test_semantic_parallel_join_ownership_requires_explicit_sync_for_patient_listing_case_4_1() -> None:
    topology = {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["first_intaker_meeting", "second_intaker_meeting"],
                "purpose": "conduct the two intaker meetings in parallel",
            }
        ]
    }
    process_text = (
        "In the first intaker meeting branch, check the medical file condition. "
        "In the second intaker meeting branch, conduct the second intaker meeting. "
        "After both the first intaker meeting branch and the second intaker meeting branch are complete, "
        "list the patient for treatment."
    )
    invalid_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "first_intaker_meeting",
                "intent": "continue",
                "steps": [{"action": "check medical file condition"}, {"action": "list patient for treatment"}],
            },
            {
                "structure_id": "T1",
                "branch": "second_intaker_meeting",
                "intent": "continue",
                "steps": [{"action": "conduct second intaker meeting"}],
            },
        ],
    }

    with pytest.raises(
        SemanticOwnershipEvidenceValidationError,
        match=r"parallel-join ownership evidence.*list the patient for treatment",
    ):
        validate_semantic_ownership_against_evidence(
            process_text,
            topology_artifact=topology,
            semantic_plan=invalid_plan,
        )

    no_sync_text = (
        "In the first intaker meeting branch, check the medical file condition. "
        "In the second intaker meeting branch, conduct the second intaker meeting. "
        "Later, list the patient for treatment."
    )
    ambiguous_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": invalid_plan["branch_plans"],
    }
    assert validate_semantic_ownership_against_evidence(
        no_sync_text,
        topology_artifact=topology,
        semantic_plan=ambiguous_plan,
    ) == ambiguous_plan


def test_semantic_parallel_join_ownership_does_not_fabricate_shared_action_case_3_5() -> None:
    process_text = (
        "In the intake branch, create the intake package. "
        "In the verification branch, verify the intake package. "
        "After both the intake branch and the verification branch are complete, the process ends."
    )
    plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "intake",
                "intent": "continue",
                "steps": [{"action": "create intake package"}],
            },
            {
                "structure_id": "T1",
                "branch": "verification",
                "intent": "continue",
                "steps": [{"action": "verify intake package"}],
            },
        ],
    }

    assert validate_semantic_ownership_against_evidence(
        process_text,
        topology_artifact={
            "structures": [
                {
                    "id": "T1",
                    "type": "parallel",
                    "parent": "ROOT",
                    "parent_branch": None,
                    "branches": ["intake", "verification"],
                    "purpose": "run intake and verification in parallel",
                }
            ]
        },
        semantic_plan=plan,
    ) == plan
    assert "root_scope_" not in json.dumps(plan)


@pytest.mark.parametrize(
    ("process_text", "topology_artifact", "semantic_plan"),
    [
        (
            "Receive the request. Prepare the record. Send the result.",
            {"structures": []},
            {"root_actions": [{"slot_id": "ROOT_START", "actions": [{"action": "receive request"}, {"action": "prepare record"}, {"action": "send result"}]}], "branch_plans": []},
        ),
        (
            "The request is checked. If invalid, revise and check again until valid. When valid, archive it.",
            {
                "structures": [
                    {"id": "T1", "type": "loop", "parent": "ROOT", "parent_branch": None, "branches": ["retry", "success"], "purpose": "check request until valid"}
                ]
            },
            {
                "root_actions": [
                    {"slot_id": "ROOT_START", "actions": [{"action": "check request"}]},
                    {"slot_id": "AFTER_T1", "actions": [{"action": "archive request"}]},
                ],
                "branch_plans": [
                    {"structure_id": "T1", "branch": "retry", "intent": "loop_back", "steps": [{"action": "revise request"}]},
                    {"structure_id": "T1", "branch": "success", "intent": "continue", "steps": []},
                ],
            },
        ),
        (
            "Determine parts and quantities. Enter the data into PPS. Procure missing parts when needed.",
            {"structures": []},
            {"root_actions": [{"slot_id": "ROOT_START", "actions": [{"action": "determine parts and quantities"}, {"action": "enter data into PPS"}, {"action": "procure missing parts"}]}], "branch_plans": []},
        ),
        (
            "If review is required, inspect the request. Without review, approve it directly.",
            {
                "structures": [
                    {"id": "T1", "type": "decision", "parent": "ROOT", "parent_branch": None, "branches": ["review", "direct"], "purpose": "decide whether review is required"}
                ]
            },
            {
                "root_actions": [
                    {"slot_id": "ROOT_START", "actions": []},
                    {"slot_id": "AFTER_T1", "actions": []},
                ],
                "branch_plans": [
                    {"structure_id": "T1", "branch": "review", "intent": "continue", "steps": [{"action": "inspect request"}]},
                    {"structure_id": "T1", "branch": "direct", "intent": "continue", "steps": [{"action": "approve request"}]},
                ],
            },
        ),
    ],
)
def test_semantic_parallel_ownership_regressions_preserve_non_target_cases(
    process_text: str,
    topology_artifact: dict,
    semantic_plan: dict,
) -> None:
    assert validate_semantic_ownership_against_evidence(
        process_text,
        topology_artifact=topology_artifact,
        semantic_plan=semantic_plan,
    ) == semantic_plan
    assert "root_scope_" not in json.dumps(semantic_plan)


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
        {"slot_id": "AFTER_T1", "action": "review deployment request"},
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
        {"slot_id": "AFTER_T1", "action": "review deployment request"},
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


def test_semantic_coverage_accepts_create_request_nominalization_with_same_object() -> None:
    plan = _linear_plan("request automatic resource restoration")

    assert validate_semantic_coverage_against_evidence(
        "Service Management creates a request for automatic resource restoration.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_accepts_determine_whether_decision_semantics() -> None:
    topology = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["insured", "rejected"],
                "purpose": "determine whether claim is insured",
            }
        ]
    }
    plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "insured", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "continue", "steps": []},
        ],
    }

    assert validate_semantic_coverage_against_evidence(
        "It is checked whether the claim is insured.",
        topology_artifact=topology,
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_accepts_morphological_request_variation() -> None:
    plan = _linear_plan("request updated customer records")

    assert validate_semantic_coverage_against_evidence(
        "The clerk creates a request for updated customer records.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_extracts_embedded_reprioritize_from_process_wrapper() -> None:
    plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "re_prioritize", "intent": "loop_back", "steps": [{"action": "re-prioritize counter measures"}]},
            {"structure_id": "T1", "branch": "continue", "intent": "continue", "steps": []},
        ],
    }
    topology = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["re_prioritize", "continue"],
                "purpose": "determine whether counter measures must be adjusted",
            }
        ]
    }

    assert validate_semantic_coverage_against_evidence(
        "The process goes back to re-prioritize these measures.",
        topology_artifact=topology,
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_extracts_embedded_review_from_process_wrapper() -> None:
    plan = _linear_plan("review claim")

    assert validate_semantic_coverage_against_evidence(
        "The process goes back to review the claim.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_handles_full_reprioritize_wrapper_with_control_tail() -> None:
    plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "premium", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "re_prioritize", "intent": "loop_back", "steps": [{"action": "re-prioritize counter measures"}]},
            {"structure_id": "T1", "branch": "continue", "intent": "continue", "steps": []},
        ],
    }
    topology = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["premium", "re_prioritize", "continue"],
                "purpose": "determine customer significance and adjust actions",
            }
        ]
    }

    assert validate_semantic_coverage_against_evidence(
        "The process goes back to re-prioritize these measures - otherwise the process continues.",
        topology_artifact=topology,
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
    ("process_text", "semantic_action"),
    [
        ("The clerk creates a request for correction.", "approve request for correction"),
        ("The clerk submits the form.", "review form"),
        ("The clerk checks the claim.", "reject claim"),
    ],
)
def test_semantic_coverage_rejects_same_object_with_different_operation(
    process_text: str,
    semantic_action: str,
) -> None:
    with pytest.raises(SemanticCoverageEvidenceValidationError):
        validate_semantic_coverage_against_evidence(
            process_text,
            topology_artifact={"structures": []},
            semantic_plan=_linear_plan(semantic_action),
        )


def test_semantic_coverage_still_rejects_true_missing_action() -> None:
    with pytest.raises(SemanticCoverageEvidenceValidationError):
        validate_semantic_coverage_against_evidence(
            "At the end of the conversation, the form is handed in at the secretarial office.",
            topology_artifact={"structures": []},
            semantic_plan=_linear_plan("request medical file from family doctor"),
        )


@pytest.mark.parametrize(
    "process_text",
    [
        "The process continues.",
        "The process ends.",
        "The process goes back.",
        "Otherwise the process continues.",
        "The process goes back to it.",
    ],
)
def test_semantic_coverage_keeps_control_flow_only_wrappers_non_executable(process_text: str) -> None:
    assert validate_semantic_coverage_against_evidence(
        process_text,
        topology_artifact={"structures": []},
        semantic_plan=_linear_plan(),
    ) == _linear_plan()


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


def test_semantic_coverage_rejects_partial_case_6_3_compound_operation() -> None:
    with pytest.raises(SemanticCoverageEvidenceValidationError) as exc_info:
        validate_semantic_coverage_against_evidence(
            "Optimize production processes and create uniform work packages.",
            topology_artifact={"structures": []},
            semantic_plan=_linear_plan("optimize production processes"),
        )

    assert exc_info.value.issues[0]["operations"] == ["create"]
    assert set(exc_info.value.issues[0]["objects"]) == {"packag", "uniform", "work"}
    assert exc_info.value.issues[0]["uncovered_requirements"] == [
        {
            "operation": "create",
            "objects": ["packag", "uniform", "work"],
            "terms": ["create"],
            "checked_semantic_content": [],
        }
    ]


def test_semantic_coverage_reports_independent_uncovered_requirements_for_compound_clause() -> None:
    with pytest.raises(SemanticCoverageEvidenceValidationError) as exc_info:
        validate_semantic_coverage_against_evidence(
            "Optimize production processes and create uniform work packages.",
            topology_artifact={"structures": []},
            semantic_plan=_linear_plan(),
        )

    assert exc_info.value.issues[0]["operations"] == ["create", "process"]
    assert exc_info.value.issues[0]["uncovered_requirements"] == [
        {
            "operation": "create",
            "objects": ["packag", "uniform", "work"],
            "terms": ["create"],
            "checked_semantic_content": [],
        },
        {
            "operation": "process",
            "objects": ["optimize", "production"],
            "terms": ["process"],
            "checked_semantic_content": [],
        },
    ]


def test_semantic_coverage_accepts_full_case_6_3_compound_operation() -> None:
    plan = _linear_plan(
        "optimize production processes",
        "create uniform work packages",
    )

    assert validate_semantic_coverage_against_evidence(
        "Optimize production processes and create uniform work packages.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_requires_create_and_send_independently() -> None:
    with pytest.raises(SemanticCoverageEvidenceValidationError) as exc_info:
        validate_semantic_coverage_against_evidence(
            "Create the report and send it.",
            topology_artifact={"structures": []},
            semantic_plan=_linear_plan("create report"),
        )

    assert exc_info.value.issues[0]["operations"] == ["send"]
    assert exc_info.value.issues[0]["objects"] == ["report"]


def test_semantic_coverage_requires_check_and_update_independently() -> None:
    with pytest.raises(SemanticCoverageEvidenceValidationError) as exc_info:
        validate_semantic_coverage_against_evidence(
            "Check the order and update the record.",
            topology_artifact={"structures": []},
            semantic_plan=_linear_plan("check order"),
        )

    assert "correct" in exc_info.value.issues[0]["operations"]


def test_semantic_coverage_keeps_single_operation_matching_unchanged() -> None:
    plan = _linear_plan("review request")

    assert validate_semantic_coverage_against_evidence(
        "Review the request.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_does_not_require_purpose_result_as_separate_operation() -> None:
    plan = _linear_plan("create uniform work packages")

    assert validate_semantic_coverage_against_evidence(
        "Create uniform work packages so that setup times are minimized.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_does_not_split_object_list_into_operations() -> None:
    plan = _linear_plan("create reports and invoices")

    assert validate_semantic_coverage_against_evidence(
        "Create reports and invoices.",
        topology_artifact={"structures": []},
        semantic_plan=plan,
    ) == plan


def test_semantic_coverage_does_not_split_one_verb_with_multiple_objects() -> None:
    plan = _linear_plan("review request and supporting documents")

    assert validate_semantic_coverage_against_evidence(
        "Review the request and supporting documents.",
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


def test_semantic_coverage_rejects_partially_represented_compound_action() -> None:
    with pytest.raises(SemanticCoverageEvidenceValidationError) as exc_info:
        validate_semantic_coverage_against_evidence(
            "The clerk prepares and sends the report.",
            topology_artifact={"structures": []},
            semantic_plan=_linear_plan("send report"),
        )

    assert exc_info.value.issues[0]["operations"] == ["create"]


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


def test_semantic_coverage_does_not_use_object_overlap_as_compound_operation_credit() -> None:
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
            "operations": ["create", "identify"],
            "objects": ["charg", "instance", "invoice", "new", "supplier"],
            "qualification": "explicit executable operation with concrete business content",
            "checked_semantic_content": ["enter invoice into ACME Financial Accounting"],
            "uncovered_requirements": [
                {
                    "operation": "create",
                    "objects": ["instance", "invoice", "new"],
                    "terms": ["create"],
                    "checked_semantic_content": ["enter invoice into ACME Financial Accounting"],
                },
                {
                    "operation": "identify",
                    "objects": ["charg", "supplier"],
                    "terms": ["identify"],
                    "checked_semantic_content": [],
                },
            ],
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


def test_coverage_correction_prompt_renders_exact_scope_and_independent_requirements() -> None:
    previous_plan = _linear_plan("create list of parts to be procured")

    with pytest.raises(SemanticCoverageEvidenceValidationError) as exc_info:
        validate_semantic_coverage_against_evidence(
            (
                "Optimize production processes and create uniform work packages. "
                "Create list of parts to be procured."
            ),
            topology_artifact={"structures": []},
            semantic_plan=previous_plan,
        )

    correction_prompt = _build_semantic_correction_prompt(
        base_prompt="BASE",
        process_text=(
            "Optimize production processes and create uniform work packages. "
            "Create list of parts to be procured."
        ),
        topology_artifact={"structures": []},
        invalid_semantic_output=json.dumps(previous_plan),
        parsed_semantic_output=previous_plan,
        validation_error=str(exc_info.value),
        correction_attempt=1,
    )

    assert "Use the previous parsed SemanticSketchPlan as the preservation baseline" in correction_prompt
    assert "At ROOT_START, preserve the previous plan and independently add the following missing requirements." in correction_prompt
    assert 'Source fragment: "Optimize production processes and create uniform work packages"' in correction_prompt
    assert "1. independently add a source-supported Action covering operation `create`" in correction_prompt
    assert "2. independently add a source-supported Action covering operation `process`" in correction_prompt
    assert "business objects/context: `packag`, `uniform`, `work`" in correction_prompt
    assert "business objects/context: `optimize`, `production`" in correction_prompt
    assert 'checked semantic content near this requirement: ["create list of parts to be procured"]' in correction_prompt
    assert "Do not treat an existing same-verb Action with different business objects as satisfying a missing requirement" in correction_prompt


def test_generate_semantic_plan_correction_preserves_unrelated_existing_actions_when_adding_missing_one() -> None:
    previous_plan = _linear_plan("record request", "review request", "notify customer")
    lossy_correction = _linear_plan("record request", "notify customer", "send invoice")
    preserved_correction = _linear_plan("record request", "review request", "notify customer", "send invoice")

    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        side_effect=[
            json.dumps(previous_plan),
            json.dumps(lossy_correction),
            json.dumps(preserved_correction),
        ],
        ) as mocked_call:
            result = generate_semantic_sketch_plan(
                "Record the request. Review the request. Notify the customer. Send the invoice.",
                topology_artifact={"structures": []},
            )

    assert mocked_call.call_count == 3
    assert len(result["planner_attempts"]) == 3
    assert "omits high-confidence source activities" in result["planner_attempts"][0]["validation_error"]
    assert "dropped unaffected previously valid Actions" in result["planner_attempts"][1]["validation_error"]
    assert result["artifact"] == preserved_correction
    assert result["artifact"]["root_actions"][0]["actions"] == [
        {"action": "record request"},
        {"action": "review request"},
        {"action": "notify customer"},
        {"action": "send invoice"},
    ]


def test_semantic_correction_preservation_allows_targeted_ownership_move() -> None:
    previous_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "review request"}, {"action": "archive request"}]},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "continue", "steps": []},
        ],
    }
    moved_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "review request"}]},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": [{"action": "archive request"}]},
            {"structure_id": "T1", "branch": "rejected", "intent": "continue", "steps": []},
        ],
    }

    assert _enforce_semantic_correction_preservation(
        previous_plan=previous_plan,
        current_plan=moved_plan,
        previous_validation_error=(
            "SemanticSketchPlan contradicts parallel-branch ownership evidence: action from fragment "
            "'archive request' is owned outside branch T1/approved: root_actions[ROOT_START]."
        ),
    ) == moved_plan


def test_semantic_correction_preservation_allows_targeted_branch_to_shared_move() -> None:
    previous_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "review request"}]},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": [{"action": "archive request"}]},
            {"structure_id": "T1", "branch": "rejected", "intent": "continue", "steps": []},
        ],
    }
    moved_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "review request"}]},
            {"slot_id": "AFTER_T1", "actions": [{"action": "archive request"}]},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "continue", "steps": []},
        ],
    }

    assert _enforce_semantic_correction_preservation(
        previous_plan=previous_plan,
        current_plan=moved_plan,
        previous_validation_error=(
            "SemanticSketchPlan contradicts parallel-join ownership evidence: post-join action from sentence "
            "'Archive request after both reviews complete.' is not in shared slot AFTER_T1; found at "
            "branch_plans[T1/approved]."
        ),
    ) == moved_plan


def test_semantic_correction_preservation_allows_targeted_replacement_or_removal() -> None:
    previous_plan = _linear_plan("review request", "notify customer")
    corrected_plan = _linear_plan("review request")

    assert _enforce_semantic_correction_preservation(
        previous_plan=previous_plan,
        current_plan=corrected_plan,
        previous_validation_error="SemanticSketchPlan correction must remove notify customer because notify customer is semantically wrong here",
    ) == corrected_plan


def test_semantic_correction_preservation_rejects_unrelated_action_loss() -> None:
    previous_plan = _linear_plan("record request", "review request", "notify customer")
    corrected_plan = _linear_plan("record request", "notify customer", "send invoice")

    with pytest.raises(ValueError, match="review request"):
        _enforce_semantic_correction_preservation(
            previous_plan=previous_plan,
            current_plan=corrected_plan,
            previous_validation_error=(
                'SemanticSketchPlan omits high-confidence source activities: '
                '[{"scope_hint": "ROOT_START", "source_fragment": "Send the invoice.", "operations": ["send"]}]'
            ),
        )


def test_semantic_correction_preservation_rejects_wrong_target_scope_for_diagnosed_move() -> None:
    previous_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "review request"}, {"action": "archive request"}]},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "continue", "steps": []},
        ],
    }
    wrong_target_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "review request"}]},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "continue", "steps": [{"action": "archive request"}]},
        ],
    }

    with pytest.raises(ValueError, match="archive request"):
        _enforce_semantic_correction_preservation(
            previous_plan=previous_plan,
            current_plan=wrong_target_plan,
            previous_validation_error=(
                "SemanticSketchPlan contradicts parallel-branch ownership evidence: action from fragment "
                "'archive request' is owned outside branch T1/approved: root_actions[ROOT_START]."
            ),
        )


def test_semantic_correction_preservation_rejects_arbitrary_same_label_relocation_without_diagnostic() -> None:
    previous_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "review request"}, {"action": "archive request"}]},
        ],
        "branch_plans": [],
    }
    moved_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "review request"}]},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": [{"action": "archive request"}]},
        ],
    }

    with pytest.raises(ValueError, match="archive request"):
        _enforce_semantic_correction_preservation(
            previous_plan=previous_plan,
            current_plan=moved_plan,
            previous_validation_error=(
                'SemanticSketchPlan omits high-confidence source activities: '
                '[{"scope_hint": "ROOT_START", "source_fragment": "Send the invoice.", "operations": ["send"]}]'
            ),
        )


def test_semantic_correction_preservation_rejects_unrelated_ownership_move() -> None:
    previous_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "record request"}, {"action": "review request"}]},
            {"slot_id": "AFTER_T1", "actions": [{"action": "notify customer"}]},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "continue", "steps": []},
        ],
    }
    corrected_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "record request"}]},
            {"slot_id": "AFTER_T1", "actions": [{"action": "notify customer"}]},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": [{"action": "review request"}]},
            {"structure_id": "T1", "branch": "rejected", "intent": "continue", "steps": []},
        ],
    }

    with pytest.raises(ValueError, match="review request"):
        _enforce_semantic_correction_preservation(
            previous_plan=previous_plan,
            current_plan=corrected_plan,
            previous_validation_error=(
                'SemanticSketchPlan omits high-confidence source activities: '
                '[{"scope_hint": "AFTER_T1", "source_fragment": "Notify the customer after approval.", "operations": ["notify"]}]'
            ),
        )


def test_semantic_correction_preservation_allows_targeted_scope_local_replacement_for_case_1_1_shape() -> None:
    previous_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "receive order"}]},
            {"slot_id": "AFTER_T1", "actions": [{"action": "assemble bicycle"}, {"action": "ship bicycle"}]},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "accepted", "intent": "continue", "steps": [{"action": "inform storehouse and engineering department"}]},
            {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject order"}]},
            {"structure_id": "T2", "branch": "storehouse", "intent": "continue", "steps": [{"action": "process part list"}]},
            {"structure_id": "T2", "branch": "engineering", "intent": "continue", "steps": [{"action": "prepare for assembly"}]},
            {"structure_id": "T3", "branch": "repeat", "intent": "loop_back", "steps": [{"action": "check item availability"}, {"action": "reserve or back-order item"}]},
            {"structure_id": "T3", "branch": "complete", "intent": "continue", "steps": []},
        ],
    }
    corrected_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "create new process instance for order"}]},
            {"slot_id": "AFTER_T1", "actions": [{"action": "assemble bicycle"}, {"action": "ship bicycle"}]},
        ],
        "branch_plans": previous_plan["branch_plans"],
    }
    validation_error = (
        'SemanticSketchPlan omits high-confidence source activities: '
        '[{"checked_semantic_content": ["reject order", "prepare for assembly"], '
        '"objects": ["instance", "new", "order", "receiv", "sal", "whenever"], '
        '"operations": ["create"], '
        '"scope_hint": "ROOT_START", '
        '"source_fragment": "Whenever the sales department receives an order, a new process instance is created"}]'
    )

    assert _enforce_semantic_correction_preservation(
        previous_plan=previous_plan,
        current_plan=corrected_plan,
        previous_validation_error=validation_error,
    ) == corrected_plan


def test_semantic_correction_preservation_allows_real_1_3_root_to_branch_relocation() -> None:
    previous_plan = {
        "root_actions": [
            {
                "slot_id": "ROOT_START",
                "actions": [
                    {"action": "take order"},
                    {"action": "submit order ticket to kitchen"},
                    {"action": "give order to sommelier"},
                    {"action": "assign order to waiter"},
                ],
            },
            {"slot_id": "AFTER_T1", "actions": [{"action": "deliver order to guest's room"}]},
            {"slot_id": "AFTER_T2", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "kitchen_task", "intent": "continue", "steps": [{"action": "prepare food in kitchen"}]},
            {"structure_id": "T1", "branch": "waiter_task", "intent": "continue", "steps": [{"action": "ready cart"}, {"action": "prepare nonalcoholic drinks"}]},
            {"structure_id": "T2", "branch": "bill_now", "intent": "continue", "steps": [{"action": "debit guest's account"}]},
            {"structure_id": "T2", "branch": "bill_later", "intent": "continue", "steps": []},
        ],
    }
    corrected_plan = {
        "root_actions": [
            {
                "slot_id": "ROOT_START",
                "actions": [
                    {"action": "take order"},
                    {"action": "submit order ticket to kitchen"},
                    {"action": "give order to sommelier"},
                ],
            },
            {"slot_id": "AFTER_T1", "actions": [{"action": "deliver order to guest's room"}]},
            {"slot_id": "AFTER_T2", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "kitchen_task", "intent": "continue", "steps": [{"action": "prepare food in kitchen"}]},
            {
                "structure_id": "T1",
                "branch": "waiter_task",
                "intent": "continue",
                "steps": [
                    {"action": "assign order to waiter"},
                    {"action": "ready cart"},
                    {"action": "prepare nonalcoholic drinks"},
                ],
            },
            {"structure_id": "T2", "branch": "bill_now", "intent": "continue", "steps": [{"action": "debit guest's account"}]},
            {"structure_id": "T2", "branch": "bill_later", "intent": "continue", "steps": []},
        ],
    }
    validation_error = (
        "SemanticSketchPlan contradicts parallel-branch ownership evidence: action from fragment "
        "'she assigns the order to the waiter' is owned outside branch T1/waiter_task: "
        "root_actions[ROOT_START]. Keep the cited branch-local action inside its source-supported "
        "parallel/workstream branch and do not move it into shared/root continuation without explicit "
        "synchronization evidence."
    )

    assert _enforce_semantic_correction_preservation(
        previous_plan=previous_plan,
        current_plan=corrected_plan,
        previous_validation_error=validation_error,
    ) == corrected_plan


def test_semantic_correction_preservation_preserves_case_2_1_style_unrelated_actions_when_fixing_timeout() -> None:
    previous_plan = {
        "root_actions": [
            {
                "slot_id": "ROOT_START",
                "actions": [
                    {"action": "enter problem report into system T"},
                ],
            }
        ],
        "branch_plans": [
            {"structure_id": "T2", "branch": "significant_customer", "intent": "loop_back", "steps": [{"action": "re-prioritize counter measures"}]},
            {"structure_id": "T4", "branch": "automatic_restoration", "intent": "continue", "steps": [{"action": "create request for automatic resource restoration"}]},
            {"structure_id": "T5", "branch": "within_2_days", "intent": "continue", "steps": [{"action": "track errors"}]},
            {"structure_id": "T5", "branch": "terminate", "intent": "terminate", "steps": []},
        ],
    }
    corrected_plan = {
        "root_actions": previous_plan["root_actions"],
        "branch_plans": [
            {"structure_id": "T2", "branch": "significant_customer", "intent": "loop_back", "steps": [{"action": "re-prioritize counter measures"}]},
            {"structure_id": "T4", "branch": "automatic_restoration", "intent": "continue", "steps": [{"action": "create request for automatic resource restoration"}]},
            {"structure_id": "T5", "branch": "within_2_days", "intent": "continue", "steps": [{"action": "track errors"}]},
            {"structure_id": "T5", "branch": "terminate", "intent": "terminate", "steps": [{"action": "terminate process due to delay"}]},
        ],
    }

    assert _enforce_semantic_correction_preservation(
        previous_plan=previous_plan,
        current_plan=corrected_plan,
        previous_validation_error=(
            "branch_plans with intent `terminate` or `loop_back` must include at least one branch-local "
            "business action in `steps`; missing_steps=['T5:terminate']"
        ),
    ) == corrected_plan


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
