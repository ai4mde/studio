from __future__ import annotations

import pytest

from llm.topology_to_sketch_compiler import (
    SemanticPlanTopologyValidationError,
    compare_topology_artifact_to_activity_sketch,
    compile_topology_and_semantics_to_activity_sketch,
    compile_topology_artifact_to_activity_sketch,
)


def test_compile_topology_artifact_to_activity_sketch_preserves_branch_local_child() -> None:
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["fraud_detection", "claim_assessment"],
                "purpose": "parallel insurance review",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "T1",
                "parent_branch": "fraud_detection",
                "branches": ["requires_detailed_investigation", "no_suspicion"],
                "purpose": "suspicious activity decision",
            },
            {
                "id": "T3",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
                "purpose": "final claim outcome",
            },
        ]
    }

    sketch = compile_topology_artifact_to_activity_sketch(topology_artifact)
    control_blocks = {block["block_id"]: block for block in sketch["control_blocks"]}

    assert control_blocks["T1"]["branches"][0]["child_block_ids"] == ["T2"]
    assert control_blocks["T1"]["branches"][1]["child_block_ids"] == []
    assert control_blocks["T2"]["entry_after"] == "scope_T1_fraud_detection"


def test_compare_topology_artifact_to_activity_sketch_flags_shared_branch_ownership() -> None:
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["budget_review", "supplier_evaluation"],
            },
            {
                "id": "T2",
                "type": "loop",
                "parent": "T1",
                "parent_branch": "budget_review",
                "branches": ["retry", "success"],
            },
            {
                "id": "T3",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
            },
        ]
    }
    llm_style_sketch = {
        "main_flow": [
            {"step_id": "S1", "action": "root_scope_1"},
            {"step_id": "S2", "action": "root_scope_2"},
            {"step_id": "S3", "action": "root_scope_3"},
        ],
        "control_blocks": [
            {
                "block_id": "B1",
                "type": "parallel",
                "entry_after": "root_scope_1",
                "entry_after_step_id": "S1",
                "branches": [
                    {
                        "label": "budget_review",
                        "returns_to_main_flow": False,
                        "steps": [],
                        "next_block_id": "B2",
                        "child_block_ids": [],
                    },
                    {
                        "label": "supplier_evaluation",
                        "returns_to_main_flow": False,
                        "steps": [],
                        "next_block_id": "B2",
                        "child_block_ids": [],
                    },
                ],
                "requires_merge": True,
                "exit_to": "root_scope_2",
                "exit_to_step_id": "S2",
                "loop_back_to": None,
                "loop_back_to_step_id": None,
            },
            {
                "block_id": "B2",
                "type": "loop",
                "entry_after": "root_scope_1",
                "entry_after_step_id": "S1",
                "branches": [
                    {
                        "label": "retry",
                        "returns_to_main_flow": False,
                        "steps": [],
                        "next_block_id": None,
                        "child_block_ids": [],
                    },
                    {
                        "label": "success",
                        "returns_to_main_flow": True,
                        "steps": [],
                        "next_block_id": None,
                        "child_block_ids": [],
                    },
                ],
                "requires_merge": False,
                "exit_to": "root_scope_2",
                "exit_to_step_id": "S2",
                "loop_back_to": "root_scope_1",
                "loop_back_to_step_id": "S1",
            },
            {
                "block_id": "B3",
                "type": "decision",
                "entry_after": "root_scope_2",
                "entry_after_step_id": "S2",
                "branches": [
                    {
                        "label": "approved",
                        "returns_to_main_flow": True,
                        "steps": [],
                        "next_block_id": None,
                        "child_block_ids": [],
                    },
                    {
                        "label": "rejected",
                        "returns_to_main_flow": True,
                        "steps": [],
                        "next_block_id": None,
                        "child_block_ids": [],
                    },
                ],
                "requires_merge": True,
                "exit_to": "root_scope_3",
                "exit_to_step_id": "S3",
                "loop_back_to": None,
                "loop_back_to_step_id": None,
            },
        ],
    }

    report = compare_topology_artifact_to_activity_sketch(topology_artifact, llm_style_sketch)

    assert report["metrics"]["ownership_conflict_count"] == 1
    assert report["ownership_conflicts"] == ["B2"]


def test_compile_topology_and_semantics_to_activity_sketch_uses_semantic_actions() -> None:
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "parallel",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["budget_review", "supplier_review"],
                "purpose": "parallel purchasing checks",
            },
            {
                "id": "T2",
                "type": "loop",
                "parent": "T1",
                "parent_branch": "budget_review",
                "branches": ["retry", "success"],
                "purpose": "repeat budget review until it succeeds",
            },
            {
                "id": "T3",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
                "purpose": "final manager decision",
            },
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "employee submits purchase request"},
            {"slot_id": "AFTER_T1", "action": "department manager reviews request"},
            {"slot_id": "AFTER_T3", "action": "issue purchase order"},
        ],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "budget_review",
                "intent": "continue",
                "steps": [{"action": "collect budget review results"}],
            },
            {
                "structure_id": "T1",
                "branch": "supplier_review",
                "intent": "continue",
                "steps": [{"action": "collect supplier review results"}],
            },
            {
                "structure_id": "T2",
                "branch": "retry",
                "intent": "loop_back",
                "steps": [{"action": "employee revises request and resubmits for budget review"}],
            },
            {
                "structure_id": "T2",
                "branch": "success",
                "intent": "continue",
                "steps": [],
            },
            {
                "structure_id": "T3",
                "branch": "approved",
                "intent": "continue",
                "steps": [],
            },
            {
                "structure_id": "T3",
                "branch": "rejected",
                "intent": "terminate",
                "steps": [{"action": "request is rejected"}],
            },
        ],
    }

    sketch = compile_topology_and_semantics_to_activity_sketch(topology_artifact, semantic_plan)
    control_blocks = {block["block_id"]: block for block in sketch["control_blocks"]}

    assert sketch["main_flow"][0]["action"] == "employee submits purchase request"
    assert sketch["main_flow"][1]["action"] == "department manager reviews request"
    assert control_blocks["T1"]["branches"][0]["child_block_ids"] == ["T2"]
    assert control_blocks["T2"]["branches"][0]["steps"] == [
        {"step_id": None, "action": "employee revises request and resubmits for budget review"}
    ]
    assert control_blocks["T3"]["branches"][1]["returns_to_main_flow"] is False


def test_compile_topology_and_semantics_to_activity_sketch_lowers_target_slot_id_to_reconnect_step_id() -> None:
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rework"],
                "purpose": "request completeness decision",
            }
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "review request"},
            {"slot_id": "AFTER_T1", "action": "approve request"},
        ],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "approved",
                "intent": "continue",
                "steps": [],
            },
            {
                "structure_id": "T1",
                "branch": "rework",
                "intent": "continue",
                "steps": [{"action": "recheck request"}],
                "target_slot_id": "ROOT_START",
            },
        ],
    }

    sketch = compile_topology_and_semantics_to_activity_sketch(topology_artifact, semantic_plan)
    control_blocks = {block["block_id"]: block for block in sketch["control_blocks"]}
    rework_branch = next(
        branch for branch in control_blocks["T1"]["branches"] if branch["label"] == "rework"
    )
    approved_branch = next(
        branch for branch in control_blocks["T1"]["branches"] if branch["label"] == "approved"
    )

    assert rework_branch["reconnect_to_step_id"] == "S1"
    assert "reconnect_to_step_id" not in approved_branch


def test_compile_topology_and_semantics_to_activity_sketch_preserves_output_when_target_slot_id_is_absent() -> None:
    topology_artifact = {
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
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "review request"},
            {"slot_id": "AFTER_T1", "action": "finalize request"},
        ],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": "approved",
                "intent": "continue",
                "steps": [],
            },
            {
                "structure_id": "T1",
                "branch": "rejected",
                "intent": "terminate",
                "steps": [{"action": "reject request"}],
            },
        ],
    }

    sketch = compile_topology_and_semantics_to_activity_sketch(topology_artifact, semantic_plan)

    assert sketch == {
        "main_flow": [
            {"step_id": "S1", "action": "review request"},
            {"step_id": "S2", "action": "finalize request"},
        ],
        "control_blocks": [
            {
                "block_id": "T1",
                "type": "decision",
                "entry_after": "review request",
                "entry_after_step_id": "S1",
                "branches": [
                    {
                        "label": "approved",
                        "returns_to_main_flow": True,
                        "steps": [],
                        "next_block_id": None,
                        "child_block_ids": [],
                    },
                    {
                        "label": "rejected",
                        "returns_to_main_flow": False,
                        "steps": [{"step_id": None, "action": "reject request"}],
                        "next_block_id": None,
                        "child_block_ids": [],
                    },
                ],
                "requires_merge": False,
                "exit_to": "finalize request",
                "exit_to_step_id": "S2",
                "loop_back_to": None,
                "loop_back_to_step_id": None,
                "notes": "approval decision",
            }
        ],
    }


def test_compile_topology_and_semantics_to_activity_sketch_rejects_missing_required_root_slot() -> None:
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
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "action": "submit deployment request"},
            {"slot_id": "AFTER_T4", "action": "conduct compliance review"},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "infrastructure", "intent": "continue", "steps": [{"action": "provision servers"}]},
            {"structure_id": "T1", "branch": "security", "intent": "continue", "steps": [{"action": "validate security policies"}]},
            {"structure_id": "T4", "branch": "cancelled", "intent": "terminate", "steps": [{"action": "cancel deployment request"}]},
            {"structure_id": "T4", "branch": "approved", "intent": "continue", "steps": []},
        ],
    }

    with pytest.raises(SemanticPlanTopologyValidationError, match="missing_root_slots"):
        compile_topology_and_semantics_to_activity_sketch(topology_artifact, semantic_plan)


def test_compile_topology_and_semantics_to_activity_sketch_allows_empty_slot_between_root_controls() -> None:
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
                "purpose": "first decision",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["ready", "blocked"],
                "purpose": "second decision",
            },
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "review request"}]},
            {"slot_id": "AFTER_T1", "actions": []},
            {"slot_id": "AFTER_T2", "actions": [{"action": "archive request"}]},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
            {"structure_id": "T2", "branch": "ready", "intent": "continue", "steps": []},
            {"structure_id": "T2", "branch": "blocked", "intent": "terminate", "steps": [{"action": "hold request"}]},
        ],
    }

    sketch = compile_topology_and_semantics_to_activity_sketch(topology_artifact, semantic_plan)
    control_blocks = {block["block_id"]: block for block in sketch["control_blocks"]}

    assert sketch["main_flow"] == [
        {"step_id": "S1", "action": "review request"},
        {"step_id": "S2", "action": "archive request"},
    ]
    assert control_blocks["T1"]["exit_to"] == "second decision"
    assert control_blocks["T1"]["exit_to_step_id"] is None
    assert control_blocks["T2"]["entry_after"] == "first decision"
    assert control_blocks["T2"]["entry_after_step_id"] is None


def test_compile_topology_and_semantics_to_activity_sketch_allows_empty_terminal_slot_after_root_control() -> None:
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
                "purpose": "final approval",
            }
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "review request"}]},
            {"slot_id": "AFTER_T1", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
        ],
    }

    sketch = compile_topology_and_semantics_to_activity_sketch(topology_artifact, semantic_plan)

    assert sketch["main_flow"] == [{"step_id": "S1", "action": "review request"}]
    assert sketch["control_blocks"][0]["exit_to"] is None
    assert sketch["control_blocks"][0]["exit_to_step_id"] is None


def test_compile_topology_and_semantics_to_activity_sketch_preserves_single_action_root_slot() -> None:
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
                "purpose": "first decision",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["ready", "blocked"],
                "purpose": "second decision",
            },
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "submit request"}]},
            {"slot_id": "AFTER_T1", "actions": [{"action": "archive request"}]},
            {"slot_id": "AFTER_T2", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
            {"structure_id": "T2", "branch": "ready", "intent": "continue", "steps": []},
            {"structure_id": "T2", "branch": "blocked", "intent": "terminate", "steps": [{"action": "hold request"}]},
        ],
    }

    sketch = compile_topology_and_semantics_to_activity_sketch(topology_artifact, semantic_plan)

    assert sketch["main_flow"] == [
        {"step_id": "S1", "action": "submit request"},
        {"step_id": "S2", "action": "archive request"},
    ]


def test_compile_topology_and_semantics_to_activity_sketch_preserves_multiple_ordered_actions_in_root_slot() -> None:
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
                "purpose": "first decision",
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["ready", "blocked"],
                "purpose": "second decision",
            },
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "submit request"}]},
            {
                "slot_id": "AFTER_T1",
                "actions": [{"action": "record result"}, {"action": "notify manager"}],
            },
            {"slot_id": "AFTER_T2", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
            {"structure_id": "T2", "branch": "ready", "intent": "continue", "steps": []},
            {"structure_id": "T2", "branch": "blocked", "intent": "terminate", "steps": [{"action": "hold request"}]},
        ],
    }

    sketch = compile_topology_and_semantics_to_activity_sketch(topology_artifact, semantic_plan)
    control_blocks = {block["block_id"]: block for block in sketch["control_blocks"]}

    assert sketch["main_flow"] == [
        {"step_id": "S1", "action": "submit request"},
        {"step_id": "S2", "action": "record result"},
        {"step_id": "S3", "action": "notify manager"},
    ]
    assert control_blocks["T1"]["exit_to"] == "record result"
    assert control_blocks["T1"]["exit_to_step_id"] == "S2"
    assert control_blocks["T2"]["entry_after"] == "notify manager"
    assert control_blocks["T2"]["entry_after_step_id"] == "S3"


def test_validate_semantic_plan_against_topology_still_rejects_missing_empty_slot() -> None:
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
            },
            {
                "id": "T2",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["ready", "blocked"],
            },
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "submit request"}]},
            {"slot_id": "AFTER_T2", "actions": []},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
            {"structure_id": "T2", "branch": "ready", "intent": "continue", "steps": []},
            {"structure_id": "T2", "branch": "blocked", "intent": "terminate", "steps": [{"action": "hold request"}]},
        ],
    }

    with pytest.raises(SemanticPlanTopologyValidationError, match="missing_root_slots"):
        compile_topology_and_semantics_to_activity_sketch(topology_artifact, semantic_plan)


def test_validate_semantic_plan_against_topology_rejects_placeholder_root_actions_in_any_slot_action() -> None:
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["approved", "rejected"],
            }
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "submit request"}]},
            {"slot_id": "AFTER_T1", "actions": [{"action": "root_scope_2"}]},
        ],
        "branch_plans": [
            {"structure_id": "T1", "branch": "approved", "intent": "continue", "steps": []},
            {"structure_id": "T1", "branch": "rejected", "intent": "terminate", "steps": [{"action": "reject request"}]},
        ],
    }

    with pytest.raises(SemanticPlanTopologyValidationError, match="placeholder_root_actions"):
        compile_topology_and_semantics_to_activity_sketch(topology_artifact, semantic_plan)


@pytest.mark.parametrize(
    ("intents", "after_actions", "expected_requires_merge"),
    [
        (("terminate", "terminate"), [], False),
        (("continue", "terminate"), ["shared action"], False),
        (("continue", "continue"), ["shared action"], True),
        (("continue", "continue"), [], False),
    ],
)
def test_decision_requires_merge_only_for_multiple_routes_to_nonterminal_continuation(
    intents,
    after_actions,
    expected_requires_merge,
) -> None:
    topology_artifact = {
        "structures": [
            {
                "id": "T1",
                "type": "decision",
                "parent": "ROOT",
                "parent_branch": None,
                "branches": ["a", "b"],
                "purpose": "choose route",
            }
        ]
    }
    semantic_plan = {
        "root_actions": [
            {"slot_id": "ROOT_START", "actions": [{"action": "review item"}]},
            {
                "slot_id": "AFTER_T1",
                "actions": [{"action": action} for action in after_actions],
            },
        ],
        "branch_plans": [
            {
                "structure_id": "T1",
                "branch": branch,
                "intent": intent,
                "steps": [{"action": f"action {branch}"}],
            }
            for branch, intent in zip(("a", "b"), intents)
        ],
    }

    sketch = compile_topology_and_semantics_to_activity_sketch(
        topology_artifact,
        semantic_plan,
    )

    assert sketch["control_blocks"][0]["requires_merge"] is expected_requires_merge
