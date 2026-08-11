import json
from unittest.mock import patch

import pytest

from llm.refinement_planner import (
    RefinementPlannerError,
    build_refinement_planner_prompt,
    generate_refinement_plan,
    parse_refinement_planner_json,
    refinement_planner_response_format,
)
from llm.topology_to_sketch_compiler import compile_topology_and_semantics_to_activity_sketch
from llm.experimental_compiler import compile_activity_sketch


def _canonical_root_actions(entries):
    canonical = []
    for entry in entries:
        actions = entry.get("actions")
        if isinstance(actions, list):
            canonical.append({"slot_id": entry["slot_id"], "actions": actions})
            continue
        action = entry.get("action")
        canonical.append(
            {
                "slot_id": entry["slot_id"],
                "actions": [{"action": action}] if action else [],
            }
        )
    return canonical


CURRENT_TOPOLOGY = {
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
}

CURRENT_SEMANTICS = {
    "root_actions": _canonical_root_actions([
        {"slot_id": "ROOT_START", "action": "review request"},
        {"slot_id": "AFTER_T1", "action": "finalize request"},
    ]),
    "branch_plans": [
        {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
        {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
    ],
}

SIMPLE_LIFECYCLE_TOPOLOGY = {
    "structures": [
        {
            "id": "T1",
            "type": "decision",
            "parent": "ROOT",
            "parent_branch": None,
            "branches": ["approved", "rejected"],
            "purpose": "determine if the request is complete",
        }
    ]
}

SIMPLE_LIFECYCLE_SEMANTICS = {
    "root_actions": _canonical_root_actions([
        {"slot_id": "ROOT_START", "action": "submit request"},
        {"slot_id": "AFTER_T1", "action": "complete request handling"},
    ]),
    "branch_plans": [
        {
            "structure_id": "T1",
            "branch": "approved",
            "intent": "continue",
            "steps": [{"action": "approve request"}],
        },
        {
            "structure_id": "T1",
            "branch": "rejected",
            "intent": "terminate",
            "steps": [{"action": "return request for rework"}],
        },
    ],
}

COMPLEX_ROOT_TOPOLOGY = {
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
            "id": "T2",
            "type": "loop",
            "parent": "T1",
            "parent_branch": "infrastructure",
            "branches": ["retry", "success"],
            "purpose": "retry provisioning until it succeeds",
        },
        {
            "id": "T3",
            "type": "loop",
            "parent": "T1",
            "parent_branch": "security",
            "branches": ["retry", "success"],
            "purpose": "repeat security validation until all requirements are satisfied",
        },
        {
            "id": "T4",
            "type": "decision",
            "parent": "ROOT",
            "parent_branch": None,
            "branches": ["cancelled", "approved"],
            "purpose": "decide if the deployment request is approved",
        },
        {
            "id": "T5",
            "type": "decision",
            "parent": "T4",
            "parent_branch": "approved",
            "branches": ["needs_compliance", "deploy"],
            "purpose": "determine whether additional compliance approval is required",
        },
        {
            "id": "T6",
            "type": "decision",
            "parent": "T5",
            "parent_branch": "needs_compliance",
            "branches": ["compliance_approved", "rejected"],
            "purpose": "decide whether to approve the deployment request",
        },
    ]
}

COMPLEX_ROOT_SEMANTICS = {
    "root_actions": _canonical_root_actions([
        {"slot_id": "ROOT_START", "action": "submit deployment request"},
        {"slot_id": "AFTER_T1", "action": "review deployment request"},
        {"slot_id": "AFTER_T4", "action": "complete request handling"},
    ]),
    "branch_plans": [
        {"structure_id": "T1", "branch": "infrastructure", "intent": "continue", "steps": [{"action": "provision servers"}]},
        {"structure_id": "T1", "branch": "security", "intent": "continue", "steps": [{"action": "validate security policies"}]},
        {"structure_id": "T2", "branch": "retry", "intent": "loop_back", "steps": [{"action": "retry provisioning"}]},
        {"structure_id": "T2", "branch": "success", "intent": "continue", "steps": []},
        {"structure_id": "T3", "branch": "retry", "intent": "loop_back", "steps": [{"action": "update security policies"}]},
        {"structure_id": "T3", "branch": "success", "intent": "continue", "steps": []},
        {"structure_id": "T4", "branch": "cancelled", "intent": "terminate", "steps": [{"action": "cancel deployment request"}]},
        {"structure_id": "T4", "branch": "approved", "intent": "continue", "steps": []},
        {"structure_id": "T5", "branch": "needs_compliance", "intent": "continue", "steps": []},
        {"structure_id": "T5", "branch": "deploy", "intent": "continue", "steps": [{"action": "deploy application"}, {"action": "send confirmation notification"}]},
        {"structure_id": "T6", "branch": "compliance_approved", "intent": "continue", "steps": [{"action": "deploy application"}, {"action": "send confirmation notification"}]},
        {"structure_id": "T6", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject deployment request"}]},
    ],
}

ROOT_DECISION_CHAIN_TOPOLOGY = {
    "structures": [
        {
            "id": "T1",
            "type": "decision",
            "parent": "ROOT",
            "parent_branch": None,
            "branches": ["approved", "rejected"],
            "purpose": "determine whether the request can proceed",
        },
        {
            "id": "T2",
            "type": "decision",
            "parent": "ROOT",
            "parent_branch": None,
            "branches": ["ready", "blocked"],
            "purpose": "determine whether the request is ready for approval",
        },
        {
            "id": "T3",
            "type": "decision",
            "parent": "ROOT",
            "parent_branch": None,
            "branches": ["archive", "retain"],
            "purpose": "determine how the request is closed",
        },
    ]
}

ROOT_DECISION_CHAIN_SEMANTICS = {
    "root_actions": _canonical_root_actions([
        {"slot_id": "ROOT_START", "action": "submit request"},
        {"slot_id": "AFTER_T1", "action": "review request"},
        {"slot_id": "AFTER_T2", "action": "approve request"},
        {"slot_id": "AFTER_T3", "action": "archive request"},
    ]),
    "branch_plans": [
        {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
        {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
        {"structure_id": "T2", "branch": "ready", "intent": "continue", "steps": []},
        {"structure_id": "T2", "branch": "blocked", "intent": "terminate", "steps": [{"action": "hold request"}]},
        {"structure_id": "T3", "branch": "archive", "intent": "terminate", "steps": [{"action": "archive request"}]},
        {"structure_id": "T3", "branch": "retain", "intent": "continue", "steps": []},
    ],
}


def _planner_payload(updated_topology, updated_semantics):
    return json.dumps(
        {
            "updated_topology_artifact": updated_topology,
            "updated_semantic_sketch_plan": updated_semantics,
            "refinement_trace": {"user_instruction": "placeholder"},
        }
    )


def test_build_refinement_planner_prompt_includes_locality_rules() -> None:
    prompt = build_refinement_planner_prompt(
        "Review request, approve or reject it, then finalize it.",
        current_topology_artifact=CURRENT_TOPOLOGY,
        current_semantic_sketch_plan=CURRENT_SEMANTICS,
        instruction="Add a compliance review before approval.",
    )

    assert "Default to the smallest possible change that satisfies the instruction" in prompt
    assert "The current TopologyArtifact is the default output" in prompt
    assert "Apply only the minimum necessary edits" in prompt
    assert "Treat every existing structure as immutable unless the instruction explicitly requires changing it" in prompt
    assert "Do not redesign or improve the artifact" in prompt
    assert "Do not rewrite structures for clarity or consistency" in prompt
    assert "Only create new ids for genuinely new structures" in prompt


def test_generate_refinement_plan_retries_after_missing_root_slot_failure() -> None:
    planner_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T4", "action": "conduct compliance review"},
        ],
        "branch_plans": COMPLEX_ROOT_SEMANTICS["branch_plans"],
    }
    corrected_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T1", "action": "conduct compliance review"},
            {"slot_id": "AFTER_T4", "action": "complete request handling"},
        ],
        "branch_plans": COMPLEX_ROOT_SEMANTICS["branch_plans"],
    }

    with patch(
        "llm.refinement_planner.call_openai",
        side_effect=[
            _planner_payload(COMPLEX_ROOT_TOPOLOGY, planner_semantics),
            _planner_payload(COMPLEX_ROOT_TOPOLOGY, corrected_semantics),
        ],
    ) as mocked_call:
        result = generate_refinement_plan(
            "A customer submits a cloud deployment request. After both activities have been completed successfully, the deployment manager reviews the deployment request and decides whether to approve it.",
            current_topology_artifact=COMPLEX_ROOT_TOPOLOGY,
            current_semantic_sketch_plan=COMPLEX_ROOT_SEMANTICS,
            instruction="Replace Review Deployment Request with Conduct Compliance Review.",
        )

    root_actions = result["artifact"]["updated_semantic_sketch_plan"]["root_actions"]
    assert [entry["slot_id"] for entry in root_actions] == ["ROOT_START", "AFTER_T1", "AFTER_T4"]
    assert root_actions[1]["actions"] == [{"action": "conduct compliance review"}]
    assert len(result["planner_attempts"]) == 2
    retry_prompt = mocked_call.call_args_list[1].kwargs["prompt"]
    assert "Deterministic validation diagnostics" in retry_prompt


def test_parse_refinement_planner_json_preserves_empty_and_multi_action_root_slots() -> None:
    raw_output = _planner_payload(
        ROOT_DECISION_CHAIN_TOPOLOGY,
        {
            "root_actions": [
                {"slot_id": "ROOT_START", "action": "submit request"},
                {"slot_id": "AFTER_T1", "actions": []},
                {"slot_id": "AFTER_T2", "actions": [{"action": "record result"}, {"action": "notify manager"}]},
                {"slot_id": "AFTER_T3", "actions": []},
            ],
            "branch_plans": ROOT_DECISION_CHAIN_SEMANTICS["branch_plans"],
        },
    )

    parsed = parse_refinement_planner_json(raw_output)
    root_actions = parsed["updated_semantic_sketch_plan"]["root_actions"]

    assert root_actions == [
        {"slot_id": "ROOT_START", "actions": [{"action": "submit request"}]},
        {"slot_id": "AFTER_T1", "actions": []},
        {"slot_id": "AFTER_T2", "actions": [{"action": "record result"}, {"action": "notify manager"}]},
        {"slot_id": "AFTER_T3", "actions": []},
    ]


def test_generate_refinement_plan_retry_exhaustion_keeps_failure_explicit() -> None:
    planner_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T4", "action": "root_scope_3"},
        ],
        "branch_plans": COMPLEX_ROOT_SEMANTICS["branch_plans"],
    }

    with patch(
        "llm.refinement_planner.call_openai",
        side_effect=[
            _planner_payload(COMPLEX_ROOT_TOPOLOGY, planner_semantics),
            _planner_payload(COMPLEX_ROOT_TOPOLOGY, planner_semantics),
            _planner_payload(COMPLEX_ROOT_TOPOLOGY, planner_semantics),
        ],
    ):
        with pytest.raises(RefinementPlannerError, match="missing_root_slots") as exc_info:
            generate_refinement_plan(
                "A customer submits a cloud deployment request. After both activities have been completed successfully, the deployment manager reviews the deployment request and decides whether to approve it.",
                current_topology_artifact=COMPLEX_ROOT_TOPOLOGY,
                current_semantic_sketch_plan=COMPLEX_ROOT_SEMANTICS,
                instruction="Replace Review Deployment Request with Conduct Compliance Review.",
            )

    assert len(exc_info.value.debug_artifacts["planner_attempts"]) == 3
    assert "root_scope_" in exc_info.value.debug_artifacts["planner_raw_output"]
    assert "missing_root_slots" in exc_info.value.debug_artifacts["planner_validation_error"]


def test_refinement_planner_response_format_requires_steps_for_terminate_or_loop_back() -> None:
    schema = refinement_planner_response_format()["json_schema"]["schema"]
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


def test_generate_refinement_plan_accepts_explicit_empty_required_root_slot() -> None:
    updated_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": []},
            {"slot_id": "AFTER_T1", "action": "archive request"},
        ],
        "branch_plans": CURRENT_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(CURRENT_TOPOLOGY, updated_semantics)):
        result = generate_refinement_plan(
            "Review request, approve or reject it, then archive it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Remove the initial review request step.",
        )

    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"] == [
        {"slot_id": "ROOT_START", "actions": []},
        {"slot_id": "AFTER_T1", "actions": [{"action": "archive request"}]},
    ]


def test_parse_refinement_planner_json_rejects_inconsistent_branch_coverage() -> None:
    raw_output = json.dumps(
        {
            "updated_topology_artifact": CURRENT_TOPOLOGY,
            "updated_semantic_sketch_plan": {
                "root_actions": CURRENT_SEMANTICS["root_actions"],
                "branch_plans": [
                    {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
                ],
            },
            "refinement_trace": {"user_instruction": "Rename the approved branch"},
        }
    )

    try:
        parse_refinement_planner_json(raw_output)
    except ValueError as exc:
        assert "branch plan" in str(exc)
    else:
        raise AssertionError("Expected inconsistent branch coverage to fail validation")


def test_generate_refinement_plan_add_structure() -> None:
    updated_topology = {
        "structures": [
            *CURRENT_TOPOLOGY["structures"],
            {
                "id": "T2",
                "type": "loop",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["retry", "success"],
                "purpose": "retry validation",
            },
        ]
    }
    updated_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "review request"},
            {"slot_id": "AFTER_T1", "action": "finalize request"},
            {"slot_id": "AFTER_T2", "action": "archive request"},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
            {"structure_id": "T2", "branch": "retry", "intent": "loop_back", "steps": [{"action": "collect corrections"}]},
            {"structure_id": "T2", "branch": "success", "intent": "continue", "steps": []},
        ],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(updated_topology, updated_semantics)):
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Add a retry loop after approval.",
        )

    assert len(result["artifact"]["updated_topology_artifact"]["structures"]) == 2
    assert result["artifact"]["refinement_trace"]["user_instruction"] == "Add a retry loop after approval."


def test_generate_refinement_plan_rename_activity() -> None:
    updated_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "screen request"},
            {"slot_id": "AFTER_T1", "action": "finalize request"},
        ],
        "branch_plans": CURRENT_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(CURRENT_TOPOLOGY, updated_semantics)):
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Rename review request to screen request.",
        )

    assert result["artifact"]["updated_topology_artifact"] == CURRENT_TOPOLOGY
    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"][0]["actions"] == [{"action": "screen request"}]


def test_generate_refinement_plan_insert_action_reconciles_missing_branch_plan() -> None:
    updated_topology = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected", "compliance_review"],
                "purpose": "approval decision",
            }
        ]
    }
    incomplete_semantics = {
        "root_actions": CURRENT_SEMANTICS["root_actions"],
        "branch_plans": CURRENT_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(updated_topology, incomplete_semantics)):
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Add a compliance review before approval.",
        )

    branch_plans = result["artifact"]["updated_semantic_sketch_plan"]["branch_plans"]
    compliance_review_branch = next(
        branch_plan
        for branch_plan in branch_plans
        if branch_plan["structure_id"] == "T1" and branch_plan["branch"] == "compliance_review"
    )
    assert compliance_review_branch["intent"] == "continue"
    assert compliance_review_branch["steps"] == [{"action": "compliance review"}]


def test_generate_refinement_plan_insert_action_missing_root_slot_fails_explicitly() -> None:
    updated_topology = {
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
    }
    incomplete_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "review request"},
        ],
        "branch_plans": CURRENT_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(updated_topology, incomplete_semantics)):
        with pytest.raises(RefinementPlannerError, match="missing_root_slots") as exc_info:
            generate_refinement_plan(
                "Review request, approve or reject it, then finalize it.",
                current_topology_artifact=CURRENT_TOPOLOGY,
                current_semantic_sketch_plan=CURRENT_SEMANTICS,
                instruction="Add a compliance review before approval.",
            )

    assert "missing_root_slots=['AFTER_T1']" in exc_info.value.debug_artifacts["planner_validation_error"]


def test_generate_refinement_plan_incomplete_insert_retries_instead_of_returning_no_op() -> None:
    incomplete_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T4", "action": "review deployment request"},
        ],
        "branch_plans": COMPLEX_ROOT_SEMANTICS["branch_plans"],
    }
    corrected_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T1", "action": "conduct compliance review"},
            {"slot_id": "AFTER_T4", "action": "review deployment request"},
        ],
        "branch_plans": COMPLEX_ROOT_SEMANTICS["branch_plans"],
    }

    with patch(
        "llm.refinement_planner.call_openai",
        side_effect=[
            _planner_payload(COMPLEX_ROOT_TOPOLOGY, incomplete_semantics),
            _planner_payload(COMPLEX_ROOT_TOPOLOGY, corrected_semantics),
        ],
    ):
        result = generate_refinement_plan(
            "A customer submits a cloud deployment request. After both activities have been completed successfully, the deployment manager reviews the deployment request and decides whether to approve it.",
            current_topology_artifact=COMPLEX_ROOT_TOPOLOGY,
            current_semantic_sketch_plan=COMPLEX_ROOT_SEMANTICS,
            instruction="Insert conduct compliance review before the review deployment request.",
        )

    assert len(result["planner_attempts"]) == 2
    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"] == _canonical_root_actions([
        {"slot_id": "ROOT_START", "action": "submit deployment request"},
        {"slot_id": "AFTER_T1", "action": "conduct compliance review"},
        {"slot_id": "AFTER_T4", "action": "review deployment request"},
    ])


def test_generate_refinement_plan_topology_removal_drops_obsolete_semantics() -> None:
    updated_topology = {"structures": []}
    incomplete_semantics = CURRENT_SEMANTICS

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(updated_topology, incomplete_semantics)):
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Remove the approval decision and keep a simple linear flow.",
        )

    assert result["artifact"]["updated_topology_artifact"] == updated_topology
    assert result["artifact"]["updated_semantic_sketch_plan"] == {
        "root_actions": _canonical_root_actions([{"slot_id": "ROOT_START", "action": "review request"}]),
        "branch_plans": [],
    }


def test_generate_refinement_plan_loop_reconciliation_is_topology_driven() -> None:
    updated_topology = {
        "structures": [
            {
                "id": "L1",
                "type": "loop",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["path_a", "path_b"],
                "purpose": "iterative review",
            }
        ]
    }
    incomplete_semantics = {
        "root_actions": [{"slot_id": "ROOT_START", "action": "review request"}],
        "branch_plans": [],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(updated_topology, incomplete_semantics)):
        with pytest.raises(Exception, match="missing_root_slots"):
            generate_refinement_plan(
                "Review request, approve or reject it, then finalize it.",
                current_topology_artifact=CURRENT_TOPOLOGY,
                current_semantic_sketch_plan=CURRENT_SEMANTICS,
                instruction="Replace approval with a two-path iterative review loop.",
            )


def test_generate_refinement_plan_semantic_only_refinement() -> None:
    updated_semantics = {
        "root_actions": CURRENT_SEMANTICS["root_actions"],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": [{"action": "notify requester"}]},
            {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
        ],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(CURRENT_TOPOLOGY, updated_semantics)):
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Add a notification step on the approved branch.",
        )

    approved_branch = next(
        branch for branch in result["artifact"]["updated_semantic_sketch_plan"]["branch_plans"]
        if branch["branch"] == "approved"
    )
    assert approved_branch["steps"][0]["action"] == "notify requester"


def test_generate_refinement_plan_topology_refinement() -> None:
    updated_topology = {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["finance", "compliance"],
                "purpose": "parallel reviews",
            }
        ]
    }
    updated_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "review request"},
            {"slot_id": "AFTER_T1", "action": "finalize request"},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "finance", "intent": "continue", "steps": [{"action": "review budget"}]},
            {"structure_id": "T1", "branch": "compliance", "intent": "continue", "steps": [{"action": "review compliance"}]},
        ],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(updated_topology, updated_semantics)):
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Replace the approval decision with parallel finance and compliance review.",
        )

    assert result["artifact"]["updated_topology_artifact"]["structures"][0]["type"] == "parallel"


def test_generate_refinement_plan_no_op() -> None:
    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(CURRENT_TOPOLOGY, CURRENT_SEMANTICS)):
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Keep the current process unchanged.",
        )

    assert result["artifact"]["updated_topology_artifact"] == CURRENT_TOPOLOGY
    assert result["artifact"]["updated_semantic_sketch_plan"] == CURRENT_SEMANTICS


def test_generate_refinement_plan_ambiguous_instruction_preserves_unrelated_structure() -> None:
    updated_semantics = {
        "root_actions": CURRENT_SEMANTICS["root_actions"],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": [{"action": "perform review"}]},
            {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
        ],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(CURRENT_TOPOLOGY, updated_semantics)):
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Improve the review step.",
        )

    assert result["artifact"]["updated_topology_artifact"] == CURRENT_TOPOLOGY
    assert result["artifact"]["refinement_trace"]["user_instruction"] == "Improve the review step."


def test_generate_refinement_plan_best_effort_refinement() -> None:
    updated_topology = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected", "manual_review"],
                "purpose": "approval decision",
            }
        ]
    }
    updated_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "review request"},
            {"slot_id": "AFTER_T1", "action": "finalize request"},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
            {"structure_id": "T1", "branch": "manual_review", "intent": "continue", "steps": [{"action": "perform manual review"}]},
        ],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(updated_topology, updated_semantics)):
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Add a fallback review route if needed.",
        )

    branches = result["artifact"]["updated_topology_artifact"]["structures"][0]["branches"]
    assert "manual_review" in branches


def test_generate_refinement_plan_infers_target_slot_id_for_existing_decision_reconnect() -> None:
    current_topology = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["complete", "retry"],
                "purpose": "Determine if the request is complete?",
            }
        ]
    }
    current_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "Review Request"},
            {"slot_id": "AFTER_T1", "action": "Approve Request"},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "complete", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "retry", "intent": "continue", "steps": []},
        ],
    }

    with patch(
        "llm.refinement_planner.call_openai",
        return_value=_planner_payload(current_topology, current_semantics),
    ):
        result = generate_refinement_plan(
            "Review Request. Determine if the request is complete? If complete, Approve Request.",
            current_topology_artifact=current_topology,
            current_semantic_sketch_plan=current_semantics,
            instruction=(
                "Remove the connection from the retry path to Perform Corrective Action. "
                "Connect the retry path to Determine if the request is complete?"
            ),
        )

    retry_branch = next(
        branch
        for branch in result["artifact"]["updated_semantic_sketch_plan"]["branch_plans"]
        if branch["structure_id"] == "T1" and branch["branch"] == "retry"
    )
    assert retry_branch["target_slot_id"] == "ROOT_START"

    sketch = compile_topology_and_semantics_to_activity_sketch(
        result["artifact"]["updated_topology_artifact"],
        result["artifact"]["updated_semantic_sketch_plan"],
    )
    retry_sketch_branch = next(
        branch
        for branch in sketch["control_blocks"][0]["branches"]
        if branch["label"] == "retry"
    )
    assert retry_sketch_branch["reconnect_to_step_id"] == "S1"

    graph = compile_activity_sketch(sketch)
    review_nodes = [
        node for node in graph["nodes"]
        if node.get("type") == "action" and node.get("name") == "Review Request"
    ]
    decision_nodes = [
        node for node in graph["nodes"]
        if node.get("type") == "decision"
    ]
    assert len(review_nodes) == 1
    assert len(decision_nodes) == 1
    assert any(
        edge.get("label") == "retry" and edge.get("target") == review_nodes[0]["id"]
        for edge in graph["edges"]
    )


def test_generate_refinement_plan_prefers_existing_decision_reconnect_over_generated_return_step() -> None:
    current_topology = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["complete", "retry"],
                "purpose": "Determine if the request is complete?",
            }
        ]
    }
    current_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "Review Request"},
            {"slot_id": "AFTER_T1", "action": "Approve Request"},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "complete", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "retry", "intent": "continue", "steps": []},
        ],
    }
    planner_semantics = {
        "root_actions": current_semantics["root_actions"],
        "branch_plans": [
            {"structure_id": "T1", "branch": "complete", "intent": "continue", "steps": []},
            {
                "structure_id": "T1",
                "branch": "retry",
                "intent": "continue",
                "steps": [{"action": "Return to check if request is complete"}],
            },
        ],
    }

    with patch(
        "llm.refinement_planner.call_openai",
        return_value=_planner_payload(current_topology, planner_semantics),
    ):
        result = generate_refinement_plan(
            "Review Request. Determine if the request is complete? If complete, Approve Request.",
            current_topology_artifact=current_topology,
            current_semantic_sketch_plan=current_semantics,
            instruction=(
                "Connect the retry path to the existing Determine if the request is complete? decision."
            ),
        )

    retry_branch = next(
        branch
        for branch in result["artifact"]["updated_semantic_sketch_plan"]["branch_plans"]
        if branch["structure_id"] == "T1" and branch["branch"] == "retry"
    )
    assert retry_branch["target_slot_id"] == "ROOT_START"
    assert retry_branch["steps"] == []


def test_generate_refinement_plan_rejects_ambiguous_reconnect_across_repeated_branch_labels() -> None:
    current_topology = {
        "structures": [
            {
                "id": "T1",
                "type": "loop",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["retry", "success"],
                "purpose": "retry validation until complete",
            },
            {
                "id": "T2",
                "type": "loop",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["retry", "success"],
                "purpose": "retry approval until complete",
            },
        ]
    }
    current_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "Review Request"},
            {"slot_id": "AFTER_T1", "action": "Validate Request"},
            {"slot_id": "AFTER_T2", "action": "Approve Request"},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "retry", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "success", "intent": "continue", "steps": []},
            {"structure_id": "T2", "branch": "retry", "intent": "continue", "steps": []},
            {"structure_id": "T2", "branch": "success", "intent": "continue", "steps": []},
        ],
    }

    with patch(
        "llm.refinement_planner.call_openai",
        side_effect=[
            _planner_payload(current_topology, current_semantics),
            _planner_payload(current_topology, current_semantics),
            _planner_payload(current_topology, current_semantics),
        ],
    ):
        with pytest.raises(RefinementPlannerError, match="ambiguous across multiple branches") as exc_info:
            generate_refinement_plan(
                "Review Request. Validate Request. Approve Request.",
                current_topology_artifact=current_topology,
                current_semantic_sketch_plan=current_semantics,
                instruction="Connect the retry path to the existing Review Request action.",
            )

    assert len(exc_info.value.debug_artifacts["planner_attempts"]) == 3
    assert "candidate_branches" in exc_info.value.debug_artifacts["planner_validation_error"]


def test_generate_refinement_plan_recovers_json_from_fallback_output() -> None:
    noisy_fallback_output = (
        "Here is the updated planner payload:\n"
        "```json\n"
        f"{_planner_payload(CURRENT_TOPOLOGY, CURRENT_SEMANTICS)}\n"
        "```\n"
        "This preserves the existing refinement contract."
    )

    with patch(
        "llm.refinement_planner.call_openai",
        side_effect=[
            Exception("Structured output request failed before a valid JSON response was returned."),
            noisy_fallback_output,
        ],
    ):
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Keep the current process unchanged.",
        )

    assert result["response_mode"] == "fallback_json_mode"
    assert result["artifact"]["updated_topology_artifact"] == CURRENT_TOPOLOGY
    assert result["artifact"]["updated_semantic_sketch_plan"] == CURRENT_SEMANTICS


def test_generate_refinement_plan_deduplicates_root_actions_before_validation() -> None:
    duplicated_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "screen request"},
            {"slot_id": "ROOT_START", "action": "review request"},
            {"slot_id": "AFTER_T1", "action": "finalize request"},
            {"slot_id": "AFTER_T1", "action": "finalize request"},
        ],
        "branch_plans": CURRENT_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(CURRENT_TOPOLOGY, duplicated_semantics)):
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Rename review request to screen request.",
        )

    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"] == _canonical_root_actions([
        {"slot_id": "ROOT_START", "action": "screen request"},
        {"slot_id": "AFTER_T1", "action": "finalize request"},
    ])


def test_generate_refinement_plan_preserves_current_type_when_fallback_type_is_invalid() -> None:
    invalid_type_topology = {
        "structures": [
            {
                "id": "T1",
                "type": "approval decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
                "purpose": "approval decision",
            }
        ]
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(invalid_type_topology, CURRENT_SEMANTICS)):
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Keep the current process unchanged.",
        )

    assert result["artifact"]["updated_topology_artifact"] == CURRENT_TOPOLOGY


def test_generate_refinement_plan_simple_insert_action_keeps_branch_local_behavior() -> None:
    inserted_semantics = {
        "root_actions": SIMPLE_LIFECYCLE_SEMANTICS["root_actions"],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "approved",
                "intent": "continue",
                "steps": [{"action": "conduct compliance review"}, {"action": "approve request"}],
            },
            SIMPLE_LIFECYCLE_SEMANTICS["branch_plans"][1],
        ],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(SIMPLE_LIFECYCLE_TOPOLOGY, inserted_semantics)):
        result = generate_refinement_plan(
            "A request is submitted. A reviewer checks whether the request is complete. If the request is complete, it is approved. Otherwise, the request is returned for rework.",
            current_topology_artifact=SIMPLE_LIFECYCLE_TOPOLOGY,
            current_semantic_sketch_plan=SIMPLE_LIFECYCLE_SEMANTICS,
            instruction="Insert a new activity named Conduct Compliance Review between the decision node and the Approve Request activity.",
        )

    approved_branch = next(
        branch_plan
        for branch_plan in result["artifact"]["updated_semantic_sketch_plan"]["branch_plans"]
        if branch_plan["structure_id"] == "T1" and branch_plan["branch"] == "approved"
    )
    assert approved_branch["steps"] == [{"action": "conduct compliance review"}, {"action": "approve request"}]
    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"] == SIMPLE_LIFECYCLE_SEMANTICS["root_actions"]


def test_generate_refinement_plan_simple_replace_action_keeps_branch_local_behavior() -> None:
    replaced_semantics = {
        "root_actions": SIMPLE_LIFECYCLE_SEMANTICS["root_actions"],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "approved",
                "intent": "continue",
                "steps": [{"action": "confirm request"}],
            },
            SIMPLE_LIFECYCLE_SEMANTICS["branch_plans"][1],
        ],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(SIMPLE_LIFECYCLE_TOPOLOGY, replaced_semantics)):
        result = generate_refinement_plan(
            "A request is submitted. A reviewer checks whether the request is complete. If the request is complete, it is approved. Otherwise, the request is returned for rework.",
            current_topology_artifact=SIMPLE_LIFECYCLE_TOPOLOGY,
            current_semantic_sketch_plan=SIMPLE_LIFECYCLE_SEMANTICS,
            instruction="Replace Approve Request with Confirm Request.",
        )

    approved_branch = next(
        branch_plan
        for branch_plan in result["artifact"]["updated_semantic_sketch_plan"]["branch_plans"]
        if branch_plan["structure_id"] == "T1" and branch_plan["branch"] == "approved"
    )
    assert approved_branch["steps"] == [{"action": "confirm request"}]
    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"] == SIMPLE_LIFECYCLE_SEMANTICS["root_actions"]


def test_generate_refinement_plan_simple_remove_action_keeps_branch_local_behavior() -> None:
    current_semantics = {
        "root_actions": SIMPLE_LIFECYCLE_SEMANTICS["root_actions"],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "approved",
                "intent": "continue",
                "steps": [{"action": "conduct compliance review"}, {"action": "approve request"}],
            },
            SIMPLE_LIFECYCLE_SEMANTICS["branch_plans"][1],
        ],
    }
    removed_semantics = {
        "root_actions": SIMPLE_LIFECYCLE_SEMANTICS["root_actions"],
        "branch_plans": SIMPLE_LIFECYCLE_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(SIMPLE_LIFECYCLE_TOPOLOGY, removed_semantics)):
        result = generate_refinement_plan(
            "A request is submitted. A reviewer checks whether the request is complete. If the request is complete, it is approved. Otherwise, the request is returned for rework.",
            current_topology_artifact=SIMPLE_LIFECYCLE_TOPOLOGY,
            current_semantic_sketch_plan=current_semantics,
            instruction="Remove the conduct compliance review step.",
        )

    approved_branch = next(
        branch_plan
        for branch_plan in result["artifact"]["updated_semantic_sketch_plan"]["branch_plans"]
        if branch_plan["structure_id"] == "T1" and branch_plan["branch"] == "approved"
    )
    assert approved_branch["steps"] == [{"action": "approve request"}]
    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"] == SIMPLE_LIFECYCLE_SEMANTICS["root_actions"]


def test_generate_refinement_plan_complex_insert_action_recomputes_root_actions_in_order() -> None:
    inserted_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T4", "action": "conduct compliance review"},
            {"slot_id": "AFTER_T4", "action": "review deployment request"},
        ],
        "branch_plans": COMPLEX_ROOT_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(COMPLEX_ROOT_TOPOLOGY, inserted_semantics)):
        result = generate_refinement_plan(
            "A customer submits a cloud deployment request. After both activities have been completed successfully, the deployment manager reviews the deployment request and decides whether to approve it.",
            current_topology_artifact=COMPLEX_ROOT_TOPOLOGY,
            current_semantic_sketch_plan=COMPLEX_ROOT_SEMANTICS,
            instruction="Insert conduct compliance Review before the review deployment request",
        )

    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"] == _canonical_root_actions([
        {"slot_id": "ROOT_START", "action": "submit deployment request"},
        {"slot_id": "AFTER_T1", "action": "conduct compliance review"},
        {"slot_id": "AFTER_T4", "action": "review deployment request"},
    ])
    assert result["artifact"]["updated_semantic_sketch_plan"]["branch_plans"] == COMPLEX_ROOT_SEMANTICS["branch_plans"]


def test_generate_refinement_plan_complex_replace_action_recomputes_root_actions_in_order() -> None:
    replaced_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T4", "action": "conduct compliance review"},
            {"slot_id": "AFTER_T4", "action": "complete request handling"},
        ],
        "branch_plans": COMPLEX_ROOT_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(COMPLEX_ROOT_TOPOLOGY, replaced_semantics)):
        result = generate_refinement_plan(
            "A customer submits a cloud deployment request. After both activities have been completed successfully, the deployment manager reviews the deployment request and decides whether to approve it.",
            current_topology_artifact=COMPLEX_ROOT_TOPOLOGY,
            current_semantic_sketch_plan=COMPLEX_ROOT_SEMANTICS,
            instruction="Replace Review Deployment Request with Conduct Compliance Review.",
        )

    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"] == _canonical_root_actions([
        {"slot_id": "ROOT_START", "action": "submit deployment request"},
        {"slot_id": "AFTER_T1", "action": "conduct compliance review"},
        {"slot_id": "AFTER_T4", "action": "complete request handling"},
    ])
    assert result["artifact"]["updated_semantic_sketch_plan"]["branch_plans"] == COMPLEX_ROOT_SEMANTICS["branch_plans"]


def test_generate_refinement_plan_complex_remove_action_recomputes_root_actions_in_order() -> None:
    current_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T1", "action": "conduct compliance review"},
            {"slot_id": "AFTER_T4", "action": "review deployment request"},
        ],
        "branch_plans": COMPLEX_ROOT_SEMANTICS["branch_plans"],
    }
    removed_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T4", "action": "review deployment request"},
            {"slot_id": "AFTER_T4", "action": "complete request handling"},
        ],
        "branch_plans": COMPLEX_ROOT_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(COMPLEX_ROOT_TOPOLOGY, removed_semantics)):
        result = generate_refinement_plan(
            "A customer submits a cloud deployment request. After both activities have been completed successfully, the deployment manager reviews the deployment request and decides whether to approve it.",
            current_topology_artifact=COMPLEX_ROOT_TOPOLOGY,
            current_semantic_sketch_plan=current_semantics,
            instruction="Remove the conduct compliance review step.",
        )

    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"] == _canonical_root_actions([
        {"slot_id": "ROOT_START", "action": "submit deployment request"},
        {"slot_id": "AFTER_T1", "action": "review deployment request"},
        {"slot_id": "AFTER_T4", "action": "complete request handling"},
    ])
    assert result["artifact"]["updated_semantic_sketch_plan"]["branch_plans"] == COMPLEX_ROOT_SEMANTICS["branch_plans"]


def test_generate_refinement_plan_remove_continuation_after_root_decision_merge() -> None:
    current_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit request"},
            {"slot_id": "AFTER_T1", "action": "conduct compliance review"},
            {"slot_id": "AFTER_T2", "action": "approve request"},
            {"slot_id": "AFTER_T3", "action": "archive request"},
        ],
        "branch_plans": ROOT_DECISION_CHAIN_SEMANTICS["branch_plans"],
    }
    planner_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit request"},
            {"slot_id": "AFTER_T3", "action": "review request"},
            {"slot_id": "AFTER_T3", "action": "approve request"},
            {"slot_id": "AFTER_T3", "action": "archive request"},
        ],
        "branch_plans": ROOT_DECISION_CHAIN_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(ROOT_DECISION_CHAIN_TOPOLOGY, planner_semantics)):
        result = generate_refinement_plan(
            "A request is submitted, reviewed, approved, and then archived.",
            current_topology_artifact=ROOT_DECISION_CHAIN_TOPOLOGY,
            current_semantic_sketch_plan=current_semantics,
            instruction="Remove the conduct compliance review step.",
        )

    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"] == ROOT_DECISION_CHAIN_SEMANTICS["root_actions"]


def test_generate_refinement_plan_remove_continuation_after_root_parallel_join() -> None:
    current_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T1", "action": "conduct compliance review"},
            {"slot_id": "AFTER_T4", "action": "complete request handling"},
        ],
        "branch_plans": COMPLEX_ROOT_SEMANTICS["branch_plans"],
    }
    planner_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T4", "action": "review deployment request"},
            {"slot_id": "AFTER_T4", "action": "complete request handling"},
        ],
        "branch_plans": COMPLEX_ROOT_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(COMPLEX_ROOT_TOPOLOGY, planner_semantics)):
        result = generate_refinement_plan(
            "A customer submits a cloud deployment request. After both activities have been completed successfully, the deployment manager reviews the deployment request and decides whether to approve it.",
            current_topology_artifact=COMPLEX_ROOT_TOPOLOGY,
            current_semantic_sketch_plan=current_semantics,
            instruction="Remove the conduct compliance review step.",
        )

    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"] == COMPLEX_ROOT_SEMANTICS["root_actions"]


def test_generate_refinement_plan_remove_final_root_continuation_fails_for_missing_required_root_slot() -> None:
    current_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit request"},
            {"slot_id": "AFTER_T1", "action": "review request"},
            {"slot_id": "AFTER_T2", "action": "approve request"},
            {"slot_id": "AFTER_T3", "action": "conduct compliance review"},
        ],
        "branch_plans": ROOT_DECISION_CHAIN_SEMANTICS["branch_plans"],
    }
    planner_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit request"},
            {"slot_id": "AFTER_T1", "action": "review request"},
            {"slot_id": "AFTER_T2", "action": "approve request"},
        ],
        "branch_plans": ROOT_DECISION_CHAIN_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(ROOT_DECISION_CHAIN_TOPOLOGY, planner_semantics)):
        with pytest.raises(Exception, match="missing_root_slots"):
            generate_refinement_plan(
                "A request is submitted, reviewed, approved, and then archived.",
                current_topology_artifact=ROOT_DECISION_CHAIN_TOPOLOGY,
                current_semantic_sketch_plan=current_semantics,
                instruction="Remove the conduct compliance review step after approval.",
            )


def test_generate_refinement_plan_consecutive_root_removals_fail_for_missing_required_root_slots() -> None:
    current_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit request"},
            {"slot_id": "AFTER_T1", "action": "conduct compliance review"},
            {"slot_id": "AFTER_T2", "action": "obtain second approval"},
            {"slot_id": "AFTER_T3", "action": "archive request"},
        ],
        "branch_plans": ROOT_DECISION_CHAIN_SEMANTICS["branch_plans"],
    }
    planner_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit request"},
            {"slot_id": "AFTER_T3", "action": "archive request"},
        ],
        "branch_plans": ROOT_DECISION_CHAIN_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(ROOT_DECISION_CHAIN_TOPOLOGY, planner_semantics)):
        with pytest.raises(Exception, match="missing_root_slots"):
            generate_refinement_plan(
                "A request is submitted, reviewed, approved, and then archived.",
                current_topology_artifact=ROOT_DECISION_CHAIN_TOPOLOGY,
                current_semantic_sketch_plan=current_semantics,
                instruction="Remove the conduct compliance review and obtain second approval steps.",
            )


def test_generate_refinement_plan_incomplete_root_sequence_fails_for_missing_required_root_slot() -> None:
    partial_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T4", "action": "conduct compliance review"},
        ],
        "branch_plans": COMPLEX_ROOT_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(COMPLEX_ROOT_TOPOLOGY, partial_semantics)):
        with pytest.raises(Exception, match="missing_root_slots"):
            generate_refinement_plan(
                "A customer submits a cloud deployment request. After both activities have been completed successfully, the deployment manager reviews the deployment request and decides whether to approve it.",
                current_topology_artifact=COMPLEX_ROOT_TOPOLOGY,
                current_semantic_sketch_plan=COMPLEX_ROOT_SEMANTICS,
                instruction="Replace Review Deployment Request with Conduct Compliance Review.",
            )


def test_generate_refinement_plan_multiple_consecutive_root_edits_reconcile_as_one_sequence() -> None:
    extended_topology = {
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
            {
                "id": "T7",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["completed", "archived"],
                "purpose": "determine how the request is closed",
            },
        ]
    }
    current_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T1", "action": "review deployment request"},
            {"slot_id": "AFTER_T4", "action": "complete request handling"},
            {"slot_id": "AFTER_T7", "action": "archive deployment request"},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "infrastructure", "intent": "continue", "steps": [{"action": "provision servers"}]},
            {"structure_id": "T1", "branch": "security", "intent": "continue", "steps": [{"action": "validate security policies"}]},
            {"structure_id": "T4", "branch": "cancelled", "intent": "terminate", "steps": [{"action": "cancel deployment request"}]},
            {"structure_id": "T4", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T7", "branch": "completed", "intent": "continue", "steps": []},
            {"structure_id": "T7", "branch": "archived", "intent": "terminate", "steps": [{"action": "archive deployment request"}]},
        ],
    }
    updated_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T7", "action": "conduct compliance review"},
            {"slot_id": "AFTER_T7", "action": "obtain deployment approval"},
            {"slot_id": "AFTER_T7", "action": "close deployment request"},
        ],
        "branch_plans": current_semantics["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(extended_topology, updated_semantics)):
        result = generate_refinement_plan(
            "A customer submits a cloud deployment request. After both activities have been completed successfully, the deployment manager reviews the request, completes handling, and archives it.",
            current_topology_artifact=extended_topology,
            current_semantic_sketch_plan=current_semantics,
            instruction="Replace the remaining root actions after submission with Conduct Compliance Review, Obtain Deployment Approval, and Close Deployment Request.",
        )

    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"] == _canonical_root_actions([
        {"slot_id": "ROOT_START", "action": "submit deployment request"},
        {"slot_id": "AFTER_T1", "action": "conduct compliance review"},
        {"slot_id": "AFTER_T4", "action": "obtain deployment approval"},
        {"slot_id": "AFTER_T7", "action": "close deployment request"},
    ])


def test_generate_refinement_plan_multiple_root_lifecycle_edits_do_not_preserve_stale_actions() -> None:
    current_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit request"},
            {"slot_id": "AFTER_T1", "action": "review request"},
            {"slot_id": "AFTER_T2", "action": "approve request"},
            {"slot_id": "AFTER_T3", "action": "archive request"},
        ],
        "branch_plans": ROOT_DECISION_CHAIN_SEMANTICS["branch_plans"],
    }
    planner_semantics = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit request"},
            {"slot_id": "AFTER_T3", "action": "conduct compliance review"},
            {"slot_id": "AFTER_T3", "action": "finalize approval"},
            {"slot_id": "AFTER_T3", "action": "close request"},
        ],
        "branch_plans": ROOT_DECISION_CHAIN_SEMANTICS["branch_plans"],
    }

    with patch("llm.refinement_planner.call_openai", return_value=_planner_payload(ROOT_DECISION_CHAIN_TOPOLOGY, planner_semantics)):
        result = generate_refinement_plan(
            "A request is submitted, reviewed, approved, and then archived.",
            current_topology_artifact=ROOT_DECISION_CHAIN_TOPOLOGY,
            current_semantic_sketch_plan=current_semantics,
            instruction="Replace the remaining root actions after submission with Conduct Compliance Review, Finalize Approval, and Close Request.",
        )

    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"] == _canonical_root_actions([
        {"slot_id": "ROOT_START", "action": "submit request"},
        {"slot_id": "AFTER_T1", "action": "conduct compliance review"},
        {"slot_id": "AFTER_T2", "action": "finalize approval"},
        {"slot_id": "AFTER_T3", "action": "close request"},
    ])
