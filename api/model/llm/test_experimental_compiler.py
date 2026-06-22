from __future__ import annotations

import json
import sys
from pathlib import Path


MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from llm.experimental_compiler import compile_activity_sketch
from llm.refinement_generator import debug_model_activity_with_experimental_compiler


def test_experimental_compiler_realizes_loop_then_decision_chain() -> None:
    sketch_json = json.dumps(
        {
            "main_flow": [
                {"step_id": "S1", "action": "verify claim"},
                {"step_id": "S2", "action": "resolve claim"},
            ],
            "control_blocks": [
                {
                    "block_id": "B1",
                    "type": "loop",
                    "entry_after_step_id": "S1",
                    "entry_after": "verify claim",
                    "branches": [
                        {
                            "label": "documents required",
                            "returns_to_main_flow": False,
                            "steps": [
                                {"step_id": "S1A", "action": "submit missing documents"},
                            ],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "documents complete",
                            "returns_to_main_flow": False,
                            "steps": [],
                            "next_block_id": "B2",
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": False,
                    "exit_to_step_id": "S2",
                    "exit_to": "resolve claim",
                    "loop_back_to_step_id": "S1",
                    "loop_back_to": "verify claim",
                    "notes": None,
                },
                {
                    "block_id": "B2",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "verify claim",
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": True,
                            "steps": [{"step_id": "S2A", "action": "issue payment"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": True,
                            "steps": [{"step_id": "S2B", "action": "send rejection notice"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "resolve claim",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "claim approved",
                },
            ],
        }
    )

    bundle = debug_model_activity_with_experimental_compiler(
        "Verify claim, request documents if needed, then decide whether to approve it.",
        sketch_llm_caller=lambda prompt: sketch_json,
    )

    alignment = bundle["sketch_alignment"]
    topology = bundle["stage_artifacts"]["validation"]["topology_report"]
    realized_block_ids = {
        str(node.get("origin_block_id"))
        for node in bundle["parsed"]["nodes"]
        if str(node.get("origin_block_id") or "").strip()
    }

    assert bundle["executed_stages"] == [
        "Sketch Planner",
        "Sketch Repair",
        "Deterministic Compiler",
        "Validation",
    ]
    assert alignment["metrics"]["expected_loop_backs"] == 1
    assert alignment["metrics"]["realized_loop_backs"] == 1
    assert alignment["metrics"]["expected_merges"] == 1
    assert alignment["metrics"]["realized_merges"] == 1
    assert "missing_decision_node" not in alignment["issues"]
    assert "loop_back_edge_not_realized" not in alignment["issues"]
    assert "missing_merge_for_decision" not in alignment["issues"]
    assert realized_block_ids >= {"B1", "B2"}
    assert "disconnected_nodes" not in topology["issues"]
    assert "dead_end_nodes" not in topology["issues"]


def test_experimental_compiler_preserves_child_blocks_and_parallel_reconnects() -> None:
    sketch_json = json.dumps(
        {
            "main_flow": [
                {"step_id": "S1", "action": "start deployment"},
                {"step_id": "S2", "action": "synchronize results"},
            ],
            "control_blocks": [
                {
                    "block_id": "B1",
                    "type": "parallel",
                    "entry_after_step_id": "S1",
                    "entry_after": "start deployment",
                    "branches": [
                        {
                            "label": "provisioning",
                            "returns_to_main_flow": False,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": ["B2"],
                        },
                        {
                            "label": "compliance",
                            "returns_to_main_flow": False,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": ["B3"],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "synchronize results",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "deployment tracks",
                },
                {
                    "block_id": "B3",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "start deployment",
                    "branches": [
                        {
                            "label": "passed",
                            "returns_to_main_flow": True,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "rework",
                            "returns_to_main_flow": True,
                            "steps": [{"step_id": "S1B", "action": "apply compliance fixes"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "synchronize results",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "compliance passed",
                },
                {
                    "block_id": "B2",
                    "type": "loop",
                    "entry_after_step_id": "S1",
                    "entry_after": "start deployment",
                    "branches": [
                        {
                            "label": "retry",
                            "returns_to_main_flow": False,
                            "steps": [{"step_id": "S1A", "action": "repair provisioning"}],
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
                    "exit_to_step_id": "S2",
                    "exit_to": "synchronize results",
                    "loop_back_to_step_id": "S1",
                    "loop_back_to": "start deployment",
                    "notes": None,
                },
            ],
        }
    )

    bundle = debug_model_activity_with_experimental_compiler(
        "Run deployment provisioning and compliance work in parallel. Provisioning may retry. Compliance may require fixes before the streams synchronize.",
        sketch_llm_caller=lambda prompt: sketch_json,
    )

    alignment = bundle["sketch_alignment"]
    topology = bundle["stage_artifacts"]["validation"]["topology_report"]
    realized_block_ids = {
        str(node.get("origin_block_id"))
        for node in bundle["parsed"]["nodes"]
        if str(node.get("origin_block_id") or "").strip()
    }

    assert alignment["metrics"]["expected_loop_backs"] == 1
    assert alignment["metrics"]["realized_loop_backs"] == 1
    assert alignment["metrics"]["expected_merges"] == 2
    assert alignment["metrics"]["realized_merges"] == 2
    assert "child_block_not_realized" not in alignment["issues"]
    assert "missing_join_for_parallel" not in alignment["issues"]
    assert realized_block_ids >= {"B1", "B2", "B3"}
    assert topology["metrics"]["join_count"] >= 1
    assert topology["metrics"]["merge_count"] >= 1
    assert "disconnected_nodes" not in topology["issues"]
    assert "dead_end_nodes" not in topology["issues"]


def test_experimental_compiler_suppresses_parallel_edge_labels_but_keeps_decision_and_loop_labels() -> None:
    sketch_json = json.dumps(
        {
            "main_flow": [
                {"step_id": "S1", "action": "start deployment"},
                {"step_id": "S2", "action": "manager reviews request"},
                {"step_id": "S3", "action": "complete workflow"},
            ],
            "control_blocks": [
                {
                    "block_id": "B1",
                    "type": "parallel",
                    "entry_after_step_id": "S1",
                    "entry_after": "start deployment",
                    "branches": [
                        {
                            "label": "infrastructure",
                            "returns_to_main_flow": False,
                            "steps": [{"step_id": "S1A", "action": "provision infrastructure"}],
                            "next_block_id": None,
                            "child_block_ids": ["B2"],
                        },
                        {
                            "label": "security",
                            "returns_to_main_flow": False,
                            "steps": [{"step_id": "S1B", "action": "validate security"}],
                            "next_block_id": None,
                            "child_block_ids": ["B3"],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "manager reviews request",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "deployment tracks",
                },
                {
                    "block_id": "B2",
                    "type": "loop",
                    "entry_after_step_id": "S1",
                    "entry_after": "start deployment",
                    "branches": [
                        {
                            "label": "retry",
                            "returns_to_main_flow": False,
                            "steps": [{"step_id": "S1C", "action": "repair provisioning"}],
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
                    "exit_to_step_id": "S2",
                    "exit_to": "manager reviews request",
                    "loop_back_to_step_id": "S1A",
                    "loop_back_to": "provision infrastructure",
                    "notes": None,
                },
                {
                    "block_id": "B3",
                    "type": "decision",
                    "entry_after_step_id": "S2",
                    "entry_after": "manager reviews request",
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": True,
                            "steps": [{"step_id": "S2A", "action": "deploy application"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": True,
                            "steps": [{"step_id": "S2B", "action": "reject deployment"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S3",
                    "exit_to": "complete workflow",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "approval required",
                },
            ],
        }
    )

    bundle = debug_model_activity_with_experimental_compiler(
        "Run infrastructure and security work in parallel. Retry provisioning if needed. If approved, deploy; otherwise reject.",
        sketch_llm_caller=lambda prompt: sketch_json,
    )

    graph = bundle["parsed"]
    labels = {
        edge["label"]
        for edge in graph["edges"]
        if isinstance(edge, dict) and str(edge.get("label") or "").strip()
    }

    assert "infrastructure" not in labels
    assert "security" not in labels
    assert "approved" in labels
    assert "rejected" in labels
    assert "retry" in labels
    assert "success" in labels


def test_experimental_compiler_normalizes_only_obvious_loop_labels() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "start workflow"},
            ],
            "control_blocks": [
                {
                    "block_id": "L1",
                    "type": "loop",
                    "entry_after_step_id": "S1",
                    "entry_after": "start workflow",
                    "branches": [
                        {"label": "retry", "returns_to_main_flow": False, "steps": [], "next_block_id": None, "child_block_ids": []},
                        {"label": "success", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                    ],
                    "requires_merge": False,
                    "exit_to_step_id": None,
                    "exit_to": None,
                    "loop_back_to_step_id": "S1",
                    "loop_back_to": "start workflow",
                    "notes": "retry provisioning until it succeeds",
                },
                {
                    "block_id": "L2",
                    "type": "loop",
                    "entry_after_step_id": "S1",
                    "entry_after": "start workflow",
                    "branches": [
                        {"label": "retry", "returns_to_main_flow": False, "steps": [], "next_block_id": None, "child_block_ids": []},
                        {"label": "success", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                    ],
                    "requires_merge": False,
                    "exit_to_step_id": None,
                    "exit_to": None,
                    "loop_back_to_step_id": "S1",
                    "loop_back_to": "start workflow",
                    "notes": "repeat security fixes until validation passes",
                },
                {
                    "block_id": "L3",
                    "type": "loop",
                    "entry_after_step_id": "S1",
                    "entry_after": "start workflow",
                    "branches": [
                        {"label": "retry", "returns_to_main_flow": False, "steps": [], "next_block_id": None, "child_block_ids": []},
                        {"label": "success", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                    ],
                    "requires_merge": False,
                    "exit_to_step_id": None,
                    "exit_to": None,
                    "loop_back_to_step_id": "S1",
                    "loop_back_to": "start workflow",
                    "notes": "repeat until all requirements are satisfied",
                },
                {
                    "block_id": "L4",
                    "type": "loop",
                    "entry_after_step_id": "S1",
                    "entry_after": "start workflow",
                    "branches": [
                        {"label": "retry", "returns_to_main_flow": False, "steps": [], "next_block_id": None, "child_block_ids": []},
                        {"label": "success", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                    ],
                    "requires_merge": False,
                    "exit_to_step_id": None,
                    "exit_to": None,
                    "loop_back_to_step_id": "S1",
                    "loop_back_to": "start workflow",
                    "notes": "repeat processing as needed",
                },
                {
                    "block_id": "D1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "start workflow",
                    "branches": [
                        {"label": "approved", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                        {"label": "rejected", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": None,
                    "exit_to": None,
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "approval required",
                },
            ],
        }
    )

    labels_by_block = {
        str(node.get("origin_block_id")): str(node.get("label") or "")
        for node in graph["nodes"]
        if str(node.get("type") or "") == "decision" and str(node.get("origin_block_id") or "").strip()
    }

    assert labels_by_block["L1"] == "Provisioning successful?"
    assert labels_by_block["L2"] == "Validation passed?"
    assert labels_by_block["L3"] == "All requirements satisfied?"
    assert labels_by_block["L4"] == "repeat processing as needed?"
    assert labels_by_block["D1"] == "approval required?"


def test_experimental_compiler_sweeps_uncompiled_blocks_and_preserves_all_block_ids() -> None:
    sketch_json = json.dumps(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review claim"},
                {"step_id": "S2", "action": "finalize claim"},
            ],
            "control_blocks": [
                {
                    "block_id": "B1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review claim",
                    "branches": [
                        {
                            "label": "needs documents",
                            "returns_to_main_flow": False,
                            "steps": [{"step_id": "S1A", "action": "request documents"}],
                            "next_block_id": "B2",
                            "child_block_ids": [],
                        },
                        {
                            "label": "ready",
                            "returns_to_main_flow": True,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "finalize claim",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "documents complete",
                },
                {
                    "block_id": "B3",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review claim",
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
                            "steps": [{"step_id": "S1B", "action": "send rejection"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "finalize claim",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "claim approved",
                },
                {
                    "block_id": "B2",
                    "type": "loop",
                    "entry_after_step_id": "S1",
                    "entry_after": "review claim",
                    "branches": [
                        {
                            "label": "retry",
                            "returns_to_main_flow": False,
                            "steps": [{"step_id": "S1C", "action": "review documents"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "complete",
                            "returns_to_main_flow": True,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": False,
                    "exit_to_step_id": "S2",
                    "exit_to": "finalize claim",
                    "loop_back_to_step_id": "S1",
                    "loop_back_to": "review claim",
                    "notes": None,
                },
            ],
        }
    )

    bundle = debug_model_activity_with_experimental_compiler(
        "Review a claim, request documents if needed, possibly review again, then approve or reject before finalizing.",
        sketch_llm_caller=lambda prompt: sketch_json,
    )

    realized_block_ids = [
        str(node.get("origin_block_id"))
        for node in bundle["parsed"]["nodes"]
        if str(node.get("origin_block_id") or "").strip()
    ]
    topology = bundle["stage_artifacts"]["validation"]["topology_report"]
    alignment = bundle["sketch_alignment"]

    assert set(realized_block_ids) >= {"B1", "B2", "B3"}
    assert realized_block_ids.count("B2") == 1
    assert "unresolved_block_ids" in alignment["metrics"]
    assert alignment["metrics"]["unresolved_block_ids"] == []
    assert "loop_back_edge_not_realized" not in alignment["issues"]
    assert "missing_merge_for_decision" not in alignment["issues"]
    assert "disconnected_nodes" not in topology["issues"]
