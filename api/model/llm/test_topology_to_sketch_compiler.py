from __future__ import annotations

from llm.topology_to_sketch_compiler import (
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
