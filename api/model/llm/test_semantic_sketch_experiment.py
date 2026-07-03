from __future__ import annotations

import pytest
from unittest.mock import patch

from llm.semantic_sketch_experiment import (
    build_semantic_sketch_experiment_prompt,
    generate_semantic_sketch_plan,
    parse_semantic_sketch_plan_json,
    preserve_explicit_business_activities,
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
    assert "Do not move branch-specific business actions into shared `root_actions`" in prompt
    assert "An empty `steps` list is valid only when that branch genuinely performs no business action of its own in the process text" in prompt


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

    assert enriched == semantic_plan
