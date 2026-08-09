from __future__ import annotations

import json
import sys
from pathlib import Path


MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from llm.experimental_compiler import compile_activity_sketch
from llm.refinement_generator import debug_model_activity_with_experimental_compiler


def _reachable_node_ids(graph: dict) -> set[str]:
    outgoing: dict[str, list[str]] = {}
    for edge in graph["edges"]:
        outgoing.setdefault(str(edge["source"]), []).append(str(edge["target"]))
    pending = [
        str(node["id"])
        for node in graph["nodes"]
        if str(node.get("type") or "") == "initial"
    ]
    reachable = set(pending)
    while pending:
        source = pending.pop()
        for target in outgoing.get(source, []):
            if target not in reachable:
                reachable.add(target)
                pending.append(target)
    return reachable


def _unreachable_convergence_nodes(graph: dict) -> list[dict]:
    reachable = _reachable_node_ids(graph)
    return [
        node
        for node in graph["nodes"]
        if str(node.get("type") or "") in {"merge", "join"}
        and str(node["id"]) not in reachable
    ]


def test_experimental_compiler_realizes_reconnect_to_existing_step_without_duplication() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review request"},
                {"step_id": "S2", "action": "approve request"},
            ],
            "control_blocks": [
                {
                    "block_id": "B1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review request",
                    "branches": [
                        {
                            "label": "complete",
                            "returns_to_main_flow": True,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "rework",
                            "returns_to_main_flow": True,
                            "steps": [{"step_id": "S1A", "action": "recheck request"}],
                            "reconnect_to_step_id": "S1",
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "approve request",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "request complete",
                }
            ],
        }
    )

    review_nodes = [
        node
        for node in graph["nodes"]
        if str(node.get("type") or "") == "action"
        and str(node.get("name") or "") == "review request"
    ]
    decision_nodes = [
        node for node in graph["nodes"] if str(node.get("type") or "") == "decision"
    ]
    review_node_id = review_nodes[0]["id"]
    reconnect_edges = [
        edge
        for edge in graph["edges"]
        if edge["target"] == review_node_id
    ]
    recheck_node = next(
        node for node in graph["nodes"]
        if str(node.get("type") or "") == "action"
        and str(node.get("name") or "") == "recheck request"
    )

    assert len(review_nodes) == 1
    assert len(decision_nodes) == 1
    assert any(edge["source"] == recheck_node["id"] for edge in reconnect_edges)


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


def test_experimental_compiler_collapses_redundant_terminal_merge_chain() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review deployment request"},
                {"step_id": "S2", "action": "complete deployment process"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review deployment request",
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": False,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": ["T2"],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "cancel deployment request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "complete deployment process",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "approve deployment request",
                },
                {
                    "block_id": "T2",
                    "type": "decision",
                    "entry_after": "scope_T1_approved",
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "needs_review",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "review compliance"}],
                            "next_block_id": None,
                            "child_block_ids": ["T3"],
                        },
                        {
                            "label": "no_review",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "deploy application"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "complete deployment process",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "additional compliance required",
                },
                {
                    "block_id": "T3",
                    "type": "decision",
                    "entry_after": "review compliance",
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "send confirmation notification"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "reject deployment request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "complete deployment process",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "compliance approved",
                },
            ],
        }
    )

    nodes_by_name = {
        str(node.get("name") or ""): node["id"]
        for node in graph["nodes"]
        if str(node.get("type") or "") == "action"
    }
    final_nodes = [node for node in graph["nodes"] if str(node.get("type") or "") == "final"]
    assert len(final_nodes) == 1

    completion_id = nodes_by_name["complete deployment process"]
    cancel_id = nodes_by_name["cancel deployment request"]
    reject_id = nodes_by_name["reject deployment request"]

    incoming_to_completion = [
        edge for edge in graph["edges"]
        if edge["target"] == completion_id and edge["type"] == "control"
    ]
    incoming_sources = {edge["source"] for edge in incoming_to_completion}

    assert cancel_id not in incoming_sources
    assert reject_id not in incoming_sources
    outgoing_from_completion = [
        edge for edge in graph["edges"]
        if edge["source"] == completion_id and edge["type"] == "control"
    ]
    assert len(outgoing_from_completion) == 1
    final_merge_id = outgoing_from_completion[0]["target"]

    final_incoming = [
        edge for edge in graph["edges"]
        if edge["target"] == final_nodes[0]["id"] and edge["type"] == "control"
    ]
    final_incoming_sources = {edge["source"] for edge in final_incoming}

    assert completion_id in final_incoming_sources
    assert cancel_id in final_incoming_sources
    assert reject_id in final_incoming_sources


def test_experimental_compiler_excludes_terminating_branch_from_shared_continuation() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review request"},
                {"step_id": "S2", "action": "continue processing"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review request",
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "approve request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "reject request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "continue processing",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "request approved",
                }
            ],
        }
    )

    node_ids = {
        str(node.get("name") or ""): node["id"]
        for node in graph["nodes"]
        if str(node.get("type") or "") == "action"
    }
    continue_id = node_ids["continue processing"]
    reject_id = node_ids["reject request"]
    merge = next(
        node
        for node in graph["nodes"]
        if str(node.get("type") or "") == "merge"
        and str(node.get("origin_block_id") or "") == "T1"
    )
    merge_incoming = [edge for edge in graph["edges"] if edge["target"] == merge["id"]]

    assert not any(edge["source"] == reject_id and edge["target"] == continue_id for edge in graph["edges"])
    assert not any(edge["target"] == continue_id and edge["source"] == reject_id for edge in graph["edges"])
    assert merge["id"] in _reachable_node_ids(graph)
    assert len(merge_incoming) == 1
    assert merge_incoming[0]["source"] != reject_id


def test_experimental_compiler_terminating_branch_does_not_reach_downstream_root_activity() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review request"},
                {"step_id": "S2", "action": "archive request"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review request",
                    "branches": [
                        {
                            "label": "valid",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "validate request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "invalid",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "terminate request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "archive request",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "request valid",
                }
            ],
        }
    )

    node_ids = {
        str(node.get("name") or ""): node["id"]
        for node in graph["nodes"]
        if str(node.get("type") or "") == "action"
    }
    invalid_id = node_ids["terminate request"]
    archive_id = node_ids["archive request"]

    assert not any(edge["source"] == invalid_id and edge["target"] == archive_id for edge in graph["edges"])


def test_experimental_compiler_preserves_merge_for_two_continuing_branches() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review request"},
                {"step_id": "S2", "action": "archive request"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review request",
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "issue order"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "send rejection"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "archive request",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "request approved",
                }
            ],
        }
    )

    merge_nodes = [node for node in graph["nodes"] if str(node.get("type") or "") == "merge"]
    assert merge_nodes
    merge = next(node for node in merge_nodes if str(node.get("origin_block_id") or "") == "T1")
    incoming = [edge for edge in graph["edges"] if edge["target"] == merge["id"]]
    assert len(incoming) == 2
    assert merge["id"] in _reachable_node_ids(graph)


def test_experimental_compiler_all_terminating_branches_do_not_invent_shared_continuation() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [{"step_id": "S1", "action": "review request"}],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review request",
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "close request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "reject request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": None,
                    "exit_to": None,
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "request approved",
                }
            ],
        }
    )

    action_names = {
        str(node.get("name") or "")
        for node in graph["nodes"]
        if str(node.get("type") or "") == "action"
    }
    assert "close request" in action_names
    assert "reject request" in action_names
    assert "root_scope_" not in " ".join(action_names)


def test_experimental_compiler_nested_all_terminal_child_does_not_create_orphan_merge() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review expense"},
                {"step_id": "S2", "action": "archive expense"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review expense",
                    "branches": [
                        {
                            "label": "needs_receipt_review",
                            "returns_to_main_flow": False,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": ["T2"],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "reject expense"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "archive expense",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "expense approved",
                },
                {
                    "block_id": "T2",
                    "type": "decision",
                    "entry_after_step_id": None,
                    "entry_after": None,
                    "branches": [
                        {
                            "label": "valid",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "close receipt review"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "invalid",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "reject receipt"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": None,
                    "exit_to": None,
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "receipts valid",
                },
            ],
        }
    )

    assert _unreachable_convergence_nodes(graph) == []
    assert not any(
        str(node.get("type") or "") == "merge"
        and str(node.get("origin_block_id") or "") == "T1"
        for node in graph["nodes"]
    )


def test_experimental_compiler_parallel_children_without_continuations_do_not_create_orphan_join() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "start design"},
                {"step_id": "S2", "action": "send design"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "parallel",
                    "entry_after_step_id": "S1",
                    "entry_after": "start design",
                    "branches": [
                        {
                            "label": "electrical",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "test electrical design"}],
                            "next_block_id": None,
                            "child_block_ids": ["T2"],
                        },
                        {
                            "label": "physical",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "test physical design"}],
                            "next_block_id": None,
                            "child_block_ids": ["T3"],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "send design",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "design tracks",
                },
                *[
                    {
                        "block_id": block_id,
                        "type": "decision",
                        "entry_after_step_id": None,
                        "entry_after": None,
                        "branches": [
                            {
                                "label": "restart",
                                "returns_to_main_flow": False,
                                "steps": [{"action": f"restart {track} design"}],
                                "next_block_id": None,
                                "child_block_ids": [],
                            },
                            {
                                "label": "stop",
                                "returns_to_main_flow": False,
                                "steps": [],
                                "next_block_id": None,
                                "child_block_ids": [],
                            },
                        ],
                        "requires_merge": True,
                        "exit_to_step_id": None,
                        "exit_to": None,
                        "loop_back_to_step_id": None,
                        "loop_back_to": None,
                        "notes": f"{track} design accepted",
                    }
                    for block_id, track in (("T2", "electrical"), ("T3", "physical"))
                ],
            ],
        }
    )

    assert _unreachable_convergence_nodes(graph) == []
    assert not any(str(node.get("type") or "") == "join" for node in graph["nodes"])


def test_experimental_compiler_nested_terminating_branch_does_not_rejoin_inner_or_outer_continuation() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review request"},
                {"step_id": "S2", "action": "archive request"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review request",
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": False,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": ["T2"],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "reject request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "archive request",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "request approved",
                },
                {
                    "block_id": "T2",
                    "type": "decision",
                    "entry_after": "scope_T1_approved",
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "needs_review",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "review compliance"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "blocked",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "block request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "archive request",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "compliance approved",
                },
            ],
        }
    )

    node_ids = {
        str(node.get("name") or ""): node["id"]
        for node in graph["nodes"]
        if str(node.get("type") or "") == "action"
    }
    blocked_id = node_ids["block request"]
    archive_id = node_ids["archive request"]
    assert not any(edge["source"] == blocked_id and edge["target"] == archive_id for edge in graph["edges"])


def test_experimental_compiler_final_node_normalization_keeps_terminating_paths_out_of_shared_business_flow() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review request"},
                {"step_id": "S2", "action": "complete processing"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review request",
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "approve request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "reject request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "complete processing",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "request approved",
                }
            ],
        }
    )

    node_ids = {
        str(node.get("name") or ""): node["id"]
        for node in graph["nodes"]
        if str(node.get("type") or "") == "action"
    }
    reject_id = node_ids["reject request"]
    complete_id = node_ids["complete processing"]
    assert not any(edge["source"] == reject_id and edge["target"] == complete_id for edge in graph["edges"])


def test_experimental_compiler_mixed_terminal_and_continuing_final_paths_do_not_collapse_into_shared_pre_final_merge() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review request"},
                {"step_id": "S2", "action": "complete processing"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review request",
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "approve request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "reject request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "complete processing",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "request approved",
                }
            ],
        }
    )

    node_ids = {
        str(node.get("name") or ""): node["id"]
        for node in graph["nodes"]
        if str(node.get("type") or "") == "action"
    }
    final_id = next(node["id"] for node in graph["nodes"] if str(node.get("type") or "") == "final")

    reject_id = node_ids["reject request"]
    complete_id = node_ids["complete processing"]
    incoming_to_final = [edge for edge in graph["edges"] if edge["target"] == final_id]
    incoming_sources = {edge["source"] for edge in incoming_to_final}

    assert reject_id in incoming_sources
    assert complete_id in incoming_sources
    assert not any(
        edge["source"] == reject_id and str(edge.get("target") or "") != final_id
        for edge in graph["edges"]
    )


def test_experimental_compiler_friedrich_10_7_fixture_preserves_terminal_and_continuing_endings() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "MSPN registers measurement at GO"},
                {"step_id": "S2", "action": "GO examines MSPN application"},
                {"step_id": "S3", "action": "GO assigns the MSPN"},
                {"step_id": "S4", "action": "GO informs MSPO about the assignment of MSPN"},
                {"step_id": "S5", "action": "GO informs MPO about the assignment of MSPN"},
                {"step_id": "S6", "action": "GO informs SP about the assignment of MSPN"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after_step_id": "S2",
                    "entry_after": "GO examines MSPN application",
                    "branches": [
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "GO rejects MSPN application"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "confirmed",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "GO confirms MSPN application"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S3",
                    "exit_to": "GO assigns the MSPN",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "determine whether to reject or confirm the MSPN application",
                }
            ],
        }
    )

    node_ids = {
        str(node.get("name") or ""): node["id"]
        for node in graph["nodes"]
        if str(node.get("type") or "") == "action"
    }
    final_id = next(node["id"] for node in graph["nodes"] if str(node.get("type") or "") == "final")
    reject_id = node_ids["GO rejects MSPN application"]
    confirm_id = node_ids["GO confirms MSPN application"]
    assign_id = node_ids["GO assigns the MSPN"]
    last_inform_id = node_ids["GO informs SP about the assignment of MSPN"]

    merge_id = next(node["id"] for node in graph["nodes"] if str(node.get("type") or "") == "merge")

    assert any(edge["source"] == confirm_id and edge["target"] == merge_id for edge in graph["edges"])
    assert any(edge["source"] == merge_id and edge["target"] == assign_id for edge in graph["edges"])
    assert not any(edge["source"] == reject_id and edge["target"] == assign_id for edge in graph["edges"])

    incoming_to_final = [edge for edge in graph["edges"] if edge["target"] == final_id]
    incoming_sources = {edge["source"] for edge in incoming_to_final}
    assert reject_id in incoming_sources
    assert last_inform_id in incoming_sources


def test_experimental_compiler_enters_root_decision_when_main_flow_is_empty() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "approve request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "reject request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to": None,
                    "exit_to_step_id": None,
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "request approved",
                }
            ],
        }
    )

    initial_id = next(node["id"] for node in graph["nodes"] if str(node.get("type") or "") == "initial")
    final_id = next(node["id"] for node in graph["nodes"] if str(node.get("type") or "") == "final")
    decision_id = next(node["id"] for node in graph["nodes"] if str(node.get("type") or "") == "decision")

    assert any(edge["source"] == initial_id and edge["target"] == decision_id for edge in graph["edges"])
    assert not (
        len(graph["nodes"]) == 2
        and any(edge["source"] == initial_id and edge["target"] == final_id for edge in graph["edges"])
    )


def test_experimental_compiler_enters_root_loop_when_main_flow_is_empty() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [],
            "control_blocks": [
                {
                    "block_id": "L1",
                    "type": "loop",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "retry",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "correct form"}],
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
                    "exit_to": None,
                    "exit_to_step_id": None,
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "repeat form correction until it succeeds",
                }
            ],
        }
    )

    initial_id = next(node["id"] for node in graph["nodes"] if str(node.get("type") or "") == "initial")
    decision_id = next(node["id"] for node in graph["nodes"] if str(node.get("type") or "") == "decision")
    correct_id = next(
        node["id"]
        for node in graph["nodes"]
        if str(node.get("type") or "") == "action" and str(node.get("name") or "") == "correct form"
    )

    assert any(edge["source"] == initial_id and edge["target"] == decision_id for edge in graph["edges"])
    assert any(edge["source"] == decision_id and edge["target"] == correct_id for edge in graph["edges"])


def test_experimental_compiler_enters_root_parallel_when_main_flow_is_empty() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [],
            "control_blocks": [
                {
                    "block_id": "P1",
                    "type": "parallel",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "infrastructure",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "provision servers"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "security",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "validate policies"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to": None,
                    "exit_to_step_id": None,
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "deployment tracks",
                }
            ],
        }
    )

    initial_id = next(node["id"] for node in graph["nodes"] if str(node.get("type") or "") == "initial")
    fork_id = next(node["id"] for node in graph["nodes"] if str(node.get("type") or "") == "fork")
    join_nodes = [node for node in graph["nodes"] if str(node.get("type") or "") == "join"]

    assert any(edge["source"] == initial_id and edge["target"] == fork_id for edge in graph["edges"])
    assert len(join_nodes) == 1


def test_experimental_compiler_preserves_consecutive_root_control_structures_without_root_actions() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": False,
                            "steps": [],
                            "next_block_id": "T2",
                            "child_block_ids": [],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "reject request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": False,
                    "exit_to": None,
                    "exit_to_step_id": None,
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "first decision",
                },
                {
                    "block_id": "T2",
                    "type": "decision",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "ready",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "archive request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "blocked",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "hold request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to": None,
                    "exit_to_step_id": None,
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "second decision",
                },
            ],
        }
    )

    decision_labels = {
        str(node.get("label") or "")
        for node in graph["nodes"]
        if str(node.get("type") or "") == "decision"
    }

    assert "first decision?" in decision_labels
    assert "second decision?" in decision_labels
    assert all("root_scope_" not in str(node.get("name") or "") for node in graph["nodes"])


def test_experimental_compiler_preserves_truly_empty_process_behavior() -> None:
    graph = compile_activity_sketch({"main_flow": [], "control_blocks": []})

    assert graph == {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "control"},
        ],
    }


def test_experimental_compiler_uses_root_structure_instead_of_nested_child_as_entry_when_main_flow_is_empty() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": False,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": ["T2"],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "reject request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to": None,
                    "exit_to_step_id": None,
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "root decision",
                },
                {
                    "block_id": "T2",
                    "type": "decision",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "ready",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "finalize request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "blocked",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "hold request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to": None,
                    "exit_to_step_id": None,
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "nested decision",
                },
            ],
        }
    )

    initial_id = next(node["id"] for node in graph["nodes"] if str(node.get("type") or "") == "initial")
    root_decision_id = next(
        node["id"]
        for node in graph["nodes"]
        if str(node.get("type") or "") == "decision" and str(node.get("label") or "") == "root decision?"
    )
    nested_decision_id = next(
        node["id"]
        for node in graph["nodes"]
        if str(node.get("type") or "") == "decision" and str(node.get("label") or "") == "nested decision?"
    )

    assert any(edge["source"] == initial_id and edge["target"] == root_decision_id for edge in graph["edges"])
    assert not any(edge["source"] == initial_id and edge["target"] == nested_decision_id for edge in graph["edges"])


def test_experimental_compiler_friedrich_3_6_fixture_does_not_collapse_when_main_flow_is_empty() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "insured",
                            "returns_to_main_flow": False,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": ["T2"],
                        },
                        {
                            "label": "not_insured",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "inform claimant of rejection"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to": None,
                    "exit_to_step_id": None,
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "check claimant's insurance status",
                },
                {
                    "block_id": "T2",
                    "type": "decision",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "simple_claim",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "send simple forms to claimant"}],
                            "next_block_id": "T3",
                            "child_block_ids": [],
                        },
                        {
                            "label": "complex_claim",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "send complex forms to claimant"}],
                            "next_block_id": "T3",
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": False,
                    "exit_to": None,
                    "exit_to_step_id": None,
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "evaluate claim severity",
                },
                {
                    "block_id": "T3",
                    "type": "decision",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "complete",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "register claim in Claims Management system"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "incomplete",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "inform claimant to update forms"}],
                            "next_block_id": None,
                            "child_block_ids": ["T4"],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to": None,
                    "exit_to_step_id": None,
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "check forms for completeness after return",
                },
                {
                    "block_id": "T4",
                    "type": "loop",
                    "entry_after": "inform claimant to update forms",
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "retry",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "check updated forms for completeness"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "success",
                            "returns_to_main_flow": False,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": False,
                    "exit_to": None,
                    "exit_to_step_id": None,
                    "loop_back_to": "inform claimant to update forms",
                    "loop_back_to_step_id": None,
                    "notes": "recheck forms until complete",
                },
            ],
        }
    )

    decision_labels = {
        str(node.get("label") or "")
        for node in graph["nodes"]
        if str(node.get("type") or "") == "decision"
    }
    action_names = {
        str(node.get("name") or "")
        for node in graph["nodes"]
        if str(node.get("type") or "") == "action"
    }

    assert "check claimant's insurance status?" in decision_labels
    assert "evaluate claim severity?" in decision_labels
    assert "check forms for completeness after return?" in decision_labels
    assert "inform claimant to update forms" in action_names
    assert "check updated forms for completeness" in action_names
    assert _unreachable_convergence_nodes(graph) == []


def test_experimental_compiler_type_b_empty_slot_fixture_keeps_following_control_without_placeholder() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "loop",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "retry",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "request additional information"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "complete",
                            "returns_to_main_flow": False,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": False,
                    "exit_to": None,
                    "exit_to_step_id": None,
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "repeat review until all requirements are satisfied",
                }
            ],
        }
    )

    assert any(str(node.get("type") or "") == "decision" for node in graph["nodes"])
    assert all("root_scope_" not in str(node.get("name") or "") for node in graph["nodes"])


def test_experimental_compiler_preserves_merges_separated_by_intervening_actions() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review request"},
                {"step_id": "S2", "action": "archive request"},
            ],
            "control_blocks": [
                {
                    "block_id": "B1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review request",
                    "branches": [
                        {"label": "approved", "returns_to_main_flow": True, "steps": [{"action": "issue order"}], "next_block_id": None, "child_block_ids": []},
                        {"label": "rejected", "returns_to_main_flow": False, "steps": [{"action": "send rejection"}], "next_block_id": None, "child_block_ids": []},
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "archive request",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "request approved",
                },
                {
                    "block_id": "B2",
                    "type": "decision",
                    "entry_after_step_id": "S2",
                    "entry_after": "archive request",
                    "branches": [
                        {"label": "notify", "returns_to_main_flow": True, "steps": [{"action": "notify customer"}], "next_block_id": None, "child_block_ids": []},
                        {"label": "skip", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": None,
                    "exit_to": None,
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "notification required",
                },
            ],
        }
    )

    merge_nodes = [node for node in graph["nodes"] if str(node.get("type") or "") == "merge"]
    assert len(merge_nodes) == 2


def test_experimental_compiler_preserves_retry_loop_back_edges_after_merge_canonicalization() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "submit request"},
                {"step_id": "S2", "action": "review deployment request"},
                {"step_id": "S3", "action": "complete deployment process"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "parallel",
                    "entry_after_step_id": "S1",
                    "entry_after": "submit request",
                    "branches": [
                        {
                            "label": "infrastructure",
                            "returns_to_main_flow": False,
                            "steps": [{"step_id": "S1A", "action": "provision servers"}],
                            "next_block_id": None,
                            "child_block_ids": ["T2"],
                        },
                        {
                            "label": "security",
                            "returns_to_main_flow": False,
                            "steps": [{"step_id": "S1B", "action": "validate security policies"}],
                            "next_block_id": None,
                            "child_block_ids": ["T3"],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "review deployment request",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "deployment tracks",
                },
                {
                    "block_id": "T2",
                    "type": "loop",
                    "entry_after_step_id": "S1",
                    "entry_after": "submit request",
                    "branches": [
                        {
                            "label": "retry",
                            "returns_to_main_flow": False,
                            "steps": [{"step_id": "S1C", "action": "retry server provisioning"}],
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
                    "exit_to": "review deployment request",
                    "loop_back_to_step_id": "S1A",
                    "loop_back_to": "provision servers",
                    "notes": None,
                },
                {
                    "block_id": "T3",
                    "type": "loop",
                    "entry_after_step_id": "S1",
                    "entry_after": "submit request",
                    "branches": [
                        {
                            "label": "retry",
                            "returns_to_main_flow": False,
                            "steps": [{"step_id": "S1D", "action": "update security policies"}],
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
                    "exit_to": "review deployment request",
                    "loop_back_to_step_id": "S1B",
                    "loop_back_to": "validate security policies",
                    "notes": "repeat validation until requirements are satisfied",
                },
                {
                    "block_id": "T4",
                    "type": "decision",
                    "entry_after_step_id": "S2",
                    "entry_after": "review deployment request",
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": False,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": ["T5"],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"step_id": "S2A", "action": "cancel deployment request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S3",
                    "exit_to": "complete deployment process",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "approve or reject deployment request",
                },
                {
                    "block_id": "T5",
                    "type": "decision",
                    "entry_after_step_id": "S2",
                    "entry_after": "review deployment request",
                    "branches": [
                        {
                            "label": "needs_review",
                            "returns_to_main_flow": False,
                            "steps": [{"step_id": "S2B", "action": "compliance officer reviews request"}],
                            "next_block_id": None,
                            "child_block_ids": ["T6"],
                        },
                        {
                            "label": "no_review",
                            "returns_to_main_flow": True,
                            "steps": [{"step_id": "S2C", "action": "deploy application"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S3",
                    "exit_to": "complete deployment process",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "determine if additional compliance approval is required",
                },
                {
                    "block_id": "T6",
                    "type": "decision",
                    "entry_after_step_id": "S2",
                    "entry_after": "review deployment request",
                    "branches": [
                        {
                            "label": "approved",
                            "returns_to_main_flow": True,
                            "steps": [{"step_id": "S2D", "action": "deploy application"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"step_id": "S2E", "action": "reject deployment request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S3",
                    "exit_to": "complete deployment process",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "compliance officer approval decision",
                },
            ],
        }
    )

    node_names = {node["id"]: node.get("name") for node in graph["nodes"]}
    loop_edges = [
        edge
        for edge in graph["edges"]
        if node_names.get(edge["source"]) == "update security policies"
        and node_names.get(edge["target"]) == "validate security policies"
    ]

    assert loop_edges


def test_experimental_compiler_does_not_hide_unreachable_business_activities() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review request"},
                {"step_id": "S2", "action": "unreachable follow-up"},
                {"step_id": "S3", "action": "unreachable archive"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review request",
                    "branches": [
                        {
                            "label": "closed",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "close request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "cancelled",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "cancel request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": None,
                    "exit_to": None,
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": "request closed",
                }
            ],
        }
    )

    reachable = _reachable_node_ids(graph)
    unreachable_business_names = {
        str(node.get("name") or "")
        for node in graph["nodes"]
        if str(node.get("type") or "") == "action"
        and str(node["id"]) not in reachable
    }

    assert unreachable_business_names == {"unreachable follow-up", "unreachable archive"}


def _initial_targets(graph: dict) -> list[dict]:
    initial_id = next(
        str(node["id"])
        for node in graph["nodes"]
        if str(node.get("type") or "") == "initial"
    )
    node_by_id = {str(node["id"]): node for node in graph["nodes"]}
    return [
        node_by_id[str(edge["target"])]
        for edge in graph["edges"]
        if str(edge["source"]) == initial_id
    ]


def _node_id(graph: dict, *, node_type: str, text: str) -> str:
    return next(
        str(node["id"])
        for node in graph["nodes"]
        if str(node.get("type") or "") == node_type
        and str(node.get("name") or node.get("label") or "") == text
    )


def test_experimental_compiler_root_decision_precedes_post_control_action() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [{"step_id": "S1", "action": "register claim"}],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "insured",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "review claim"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "not_insured",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "reject claim"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to": "register claim",
                    "exit_to_step_id": "S1",
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "claimant insured",
                }
            ],
        }
    )

    assert [target["type"] for target in _initial_targets(graph)] == ["decision"]
    register_id = _node_id(graph, node_type="action", text="register claim")
    decision_id = _node_id(graph, node_type="decision", text="claimant insured?")
    assert not any(
        edge["source"] in {
            node["id"] for node in graph["nodes"] if node["type"] == "initial"
        }
        and edge["target"] == register_id
        for edge in graph["edges"]
    )
    assert decision_id in _reachable_node_ids(graph)
    assert register_id in _reachable_node_ids(graph)


def test_experimental_compiler_root_loop_precedes_post_loop_continuation() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [{"step_id": "S1", "action": "archive request"}],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "loop",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "retry",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "correct request"}],
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
                    "exit_to": "archive request",
                    "exit_to_step_id": "S1",
                    "loop_back_to": "correct request",
                    "loop_back_to_step_id": None,
                    "notes": "request complete",
                }
            ],
        }
    )

    assert [target["type"] for target in _initial_targets(graph)] == ["decision"]
    assert str(_initial_targets(graph)[0].get("label") or "") == "request complete?"


def test_experimental_compiler_root_parallel_precedes_post_join_continuation() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [{"step_id": "S1", "action": "release deployment"}],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "parallel",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "infrastructure",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "provision servers"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "security",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "validate policies"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to": "release deployment",
                    "exit_to_step_id": "S1",
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "deployment tracks",
                }
            ],
        }
    )

    assert [target["type"] for target in _initial_targets(graph)] == ["fork"]
    release_id = _node_id(graph, node_type="action", text="release deployment")
    join_id = next(
        str(node["id"])
        for node in graph["nodes"]
        if str(node.get("type") or "") == "join"
    )
    assert any(
        edge["source"] == join_id and edge["target"] == release_id
        for edge in graph["edges"]
    )


def test_experimental_compiler_chains_root_controls_across_empty_slot() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "submit request"},
                {"step_id": "S2", "action": "archive request"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after": "submit request",
                    "entry_after_step_id": "S1",
                    "branches": [
                        {
                            "label": "accepted",
                            "returns_to_main_flow": True,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "rejected",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "reject request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to": "archive request",
                    "exit_to_step_id": "S2",
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "request accepted",
                },
                {
                    "block_id": "T2",
                    "type": "decision",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "complete",
                            "returns_to_main_flow": True,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "incomplete",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "request update"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to": "archive request",
                    "exit_to_step_id": "S2",
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "request complete",
                },
            ],
        }
    )

    assert [
        (target["type"], target.get("name"))
        for target in _initial_targets(graph)
    ] == [("action", "submit request")]
    first_merge_id = next(
        str(node["id"])
        for node in graph["nodes"]
        if str(node.get("type") or "") == "merge"
        and str(node.get("origin_block_id") or "") == "T1"
    )
    second_decision_id = _node_id(
        graph,
        node_type="decision",
        text="request complete?",
    )
    assert any(
        edge["source"] == first_merge_id and edge["target"] == second_decision_id
        for edge in graph["edges"]
    )


def test_experimental_compiler_chains_root_controls_through_interstitial_action() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "submit request"},
                {"step_id": "S2", "action": "prepare review"},
                {"step_id": "S3", "action": "archive request"},
            ],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after": "submit request",
                    "entry_after_step_id": "S1",
                    "branches": [
                        {"label": "yes", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                        {"label": "no", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                    ],
                    "requires_merge": True,
                    "exit_to": "prepare review",
                    "exit_to_step_id": "S2",
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "request valid",
                },
                {
                    "block_id": "T2",
                    "type": "decision",
                    "entry_after": "prepare review",
                    "entry_after_step_id": "S2",
                    "branches": [
                        {"label": "yes", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                        {"label": "no", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                    ],
                    "requires_merge": True,
                    "exit_to": "archive request",
                    "exit_to_step_id": "S3",
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "review approved",
                },
            ],
        }
    )

    assert len(_initial_targets(graph)) == 1
    prepare_id = _node_id(graph, node_type="action", text="prepare review")
    second_decision_id = _node_id(graph, node_type="decision", text="review approved?")
    assert any(
        edge["source"] == prepare_id and edge["target"] == second_decision_id
        for edge in graph["edges"]
    )


def test_experimental_compiler_friedrich_3_6_root_entry_has_no_registration_bypass() -> None:
    graph = compile_activity_sketch(
        {
            "main_flow": [{"step_id": "S1", "action": "register claim"}],
            "control_blocks": [
                {
                    "block_id": "T1",
                    "type": "decision",
                    "entry_after": None,
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "insured",
                            "returns_to_main_flow": False,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": ["T2"],
                        },
                        {
                            "label": "not_insured",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "inform claimant of rejection"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to": "register claim",
                    "exit_to_step_id": "S1",
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "claimant insured",
                },
                {
                    "block_id": "T2",
                    "type": "decision",
                    "entry_after": "scope_T1_insured",
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "simple",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "send simple forms"}],
                            "next_block_id": "T3",
                            "child_block_ids": [],
                        },
                        {
                            "label": "complex",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "send complex forms"}],
                            "next_block_id": "T3",
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": False,
                    "exit_to": None,
                    "exit_to_step_id": None,
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "claim severity",
                },
                {
                    "block_id": "T3",
                    "type": "decision",
                    "entry_after": "scope_T1_insured",
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "complete",
                            "returns_to_main_flow": True,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                        {
                            "label": "incomplete",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "request form update"}],
                            "next_block_id": None,
                            "child_block_ids": ["T4"],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to": "register claim",
                    "exit_to_step_id": "S1",
                    "loop_back_to": None,
                    "loop_back_to_step_id": None,
                    "notes": "forms complete",
                },
                {
                    "block_id": "T4",
                    "type": "loop",
                    "entry_after": "request form update",
                    "entry_after_step_id": None,
                    "branches": [
                        {
                            "label": "retry",
                            "returns_to_main_flow": False,
                            "steps": [{"action": "check forms again"}],
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
                    "exit_to": "register claim",
                    "exit_to_step_id": "S1",
                    "loop_back_to": "request form update",
                    "loop_back_to_step_id": None,
                    "notes": "updated forms complete",
                },
            ],
        }
    )

    initial_targets = _initial_targets(graph)
    assert [target["type"] for target in initial_targets] == ["decision"]
    assert str(initial_targets[0].get("label") or "") == "claimant insured?"

    register_id = _node_id(graph, node_type="action", text="register claim")
    initial_id = next(
        str(node["id"])
        for node in graph["nodes"]
        if str(node.get("type") or "") == "initial"
    )
    assert not any(
        edge["source"] == initial_id and edge["target"] == register_id
        for edge in graph["edges"]
    )
    assert register_id in _reachable_node_ids(graph)
