import json
from unittest.mock import patch

from llm.refinement_planner import (
    build_refinement_planner_prompt,
    generate_refinement_plan,
    parse_refinement_planner_json,
)


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
    "root_actions": [
        {"slot_id": "ROOT_START", "action": "review request"},
        {"slot_id": "AFTER_T1", "action": "finalize request"},
    ],
    "branch_plans": [
        {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
        {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
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
    assert "Never delete an unrelated decision, loop, or parallel structure" in prompt
    assert "Never rename unrelated branches" in prompt
    assert "Never modify unrelated branch intents" in prompt
    assert "For local insertions such as `Add a compliance review before approval`, keep unrelated structures, branches, and branch intents identical" in prompt


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
    assert result["artifact"]["updated_semantic_sketch_plan"]["root_actions"][0]["action"] == "screen request"


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


def test_generate_refinement_plan_insert_action_restores_missing_root_slot() -> None:
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
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Add a compliance review before approval.",
        )

    root_actions = {
        root_action["slot_id"]: root_action["action"]
        for root_action in result["artifact"]["updated_semantic_sketch_plan"]["root_actions"]
    }
    assert root_actions["AFTER_T1"] == "finalize request"


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
        "root_actions": [{"slot_id": "ROOT_START", "action": "review request"}],
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
        result = generate_refinement_plan(
            "Review request, approve or reject it, then finalize it.",
            current_topology_artifact=CURRENT_TOPOLOGY,
            current_semantic_sketch_plan=CURRENT_SEMANTICS,
            instruction="Replace approval with a two-path iterative review loop.",
        )

    branch_plans = result["artifact"]["updated_semantic_sketch_plan"]["branch_plans"]
    intents = {(branch_plan["structure_id"], branch_plan["branch"]): branch_plan["intent"] for branch_plan in branch_plans}
    assert intents[("L1", "path_a")] == "loop_back"
    assert intents[("L1", "path_b")] == "continue"


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
