from __future__ import annotations

import json
import sys
from pathlib import Path

MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from llm.activity_sketch_model import ActivitySketch
from llm.keyword_hints import extract_keyword_hints
from llm.prompt_builder import build_activity_sketch_prompt_with_hints
from llm.refinement_generator import _parse_and_validate_activity_sketch_json
from llm.semantic_analysis import analyze_semantic_graph
from llm.sketch_repair import repair_activity_sketch, sketch_requires_retry
from llm.sketch_experiment import compare_sketch_generation
from llm.sketch_alignment import validate_graph_against_sketch
from llm.topology_analysis import analyze_activity_graph


def test_topology_analysis_flags_missing_merge_and_branch_labels() -> None:
    graph = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "decision", "label": "approved?"},
            {"id": "n3", "type": "action", "name": "process order"},
            {"id": "n4", "type": "action", "name": "reject order"},
            {"id": "n5", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n2", "target": "n4", "label": "no"},
            {"source": "n3", "target": "n5"},
            {"source": "n4", "target": "n5"},
        ],
    }

    report = analyze_activity_graph(graph)

    assert "decision_unlabeled_branch" in report["issues"]
    assert "possible_missing_merge" in report["issues"]


def test_compare_sketch_generation_reports_better_topology_with_sketch() -> None:
    unstable = json.dumps(
        {
            "nodes": [
                {"id": "n1", "type": "initial"},
                {"id": "n2", "type": "decision", "label": "approved?"},
                {"id": "n3", "type": "action", "name": "process order"},
                {"id": "n4", "type": "action", "name": "reject order"},
                {"id": "n5", "type": "final"},
            ],
            "edges": [
                {"source": "n1", "target": "n2"},
                {"source": "n2", "target": "n3"},
                {"source": "n2", "target": "n4"},
                {"source": "n3", "target": "n5"},
                {"source": "n4", "target": "n5"},
            ],
        }
    )
    stable = json.dumps(
        {
            "nodes": [
                {"id": "n1", "type": "initial"},
                {"id": "n2", "type": "decision", "label": "approved?"},
                {"id": "n3", "type": "action", "name": "process order"},
                {"id": "n4", "type": "action", "name": "reject order"},
                {"id": "n5", "type": "merge"},
                {"id": "n6", "type": "final"},
            ],
            "edges": [
                {"source": "n1", "target": "n2"},
                {"source": "n2", "target": "n3", "label": "yes"},
                {"source": "n2", "target": "n4", "label": "no"},
                {"source": "n3", "target": "n5"},
                {"source": "n4", "target": "n5"},
                {"source": "n5", "target": "n6"},
            ],
        }
    )
    sketch = json.dumps(
        {
            "main_flow": ["review order", "process order"],
            "control_blocks": [
                {
                    "type": "decision",
                    "entry_after": "review order",
                    "branches": [
                        {"label": "approved", "returns_to_main_flow": True},
                        {"label": "rejected", "returns_to_main_flow": True},
                    ],
                    "requires_merge": True,
                    "exit_to": "process order",
                    "notes": None,
                }
            ],
        }
    )

    def fake_graph_llm(prompt: str) -> str:
        return stable if "Topology plan" in prompt else unstable

    report = compare_sketch_generation(
        "If approved, process the order, otherwise reject it.",
        runs_per_condition=2,
        llm_caller=fake_graph_llm,
        sketch_llm_caller=lambda prompt: sketch,
    )

    assert len(report["entries"]) == 4
    assert report["summary"]["without_sketch"]["topology_issue_runs"] == 2
    assert report["summary"]["with_sketch"]["topology_issue_runs"] == 0


def test_validate_graph_against_sketch_reports_missing_parallel_join() -> None:
    sketch = {
        "main_flow": ["submit request", "archive request"],
        "control_blocks": [
            {
                "type": "parallel",
                "entry_after": "submit request",
                "branches": [
                    {"label": "review", "returns_to_main_flow": True},
                    {"label": "notify", "returns_to_main_flow": True},
                ],
                "requires_merge": True,
                "exit_to": "archive request",
                "notes": None,
            }
        ],
    }
    graph = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "submit request"},
            {"id": "n3", "type": "fork"},
            {"id": "n4", "type": "action", "name": "review request"},
            {"id": "n5", "type": "action", "name": "notify requester"},
            {"id": "n6", "type": "action", "name": "archive request"},
            {"id": "n7", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n4"},
            {"source": "n3", "target": "n5"},
            {"source": "n4", "target": "n6"},
            {"source": "n5", "target": "n6"},
            {"source": "n6", "target": "n7"},
        ],
    }

    report = validate_graph_against_sketch(sketch, graph)

    assert "missing_join_for_parallel" in report["issues"]


def test_validate_graph_against_sketch_reports_clean_loop_alignment() -> None:
    sketch = {
        "main_flow": ["process payment", "ship order"],
        "control_blocks": [
            {
                "type": "loop",
                "entry_after": "process payment",
                "branches": [
                    {"label": "retry", "returns_to_main_flow": True},
                    {"label": "success", "returns_to_main_flow": True},
                ],
                "requires_merge": False,
                "exit_to": "ship order",
                "notes": None,
            }
        ],
    }
    graph = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "process payment"},
            {"id": "n3", "type": "decision", "label": "payment successful?"},
            {"id": "n4", "type": "action", "name": "retry payment"},
            {"id": "n5", "type": "action", "name": "ship order"},
            {"id": "n6", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n4", "label": "no"},
            {"source": "n3", "target": "n5", "label": "yes"},
            {"source": "n4", "target": "n2", "label": "retry"},
            {"source": "n5", "target": "n6"},
        ],
    }

    report = validate_graph_against_sketch(sketch, graph)

    assert report["issues"] == []


def test_activity_sketch_defaults_retry_loops_to_no_merge() -> None:
    sketch = ActivitySketch.model_validate(
        {
            "main_flow": ["validate form", "store application"],
            "control_blocks": [
                {
                    "type": "loop",
                    "entry_after": "validate form",
                    "branches": [
                        {"label": "errors found", "returns_to_main_flow": False},
                        {"label": "valid", "returns_to_main_flow": True},
                    ],
                    "exit_to": "store application",
                    "loop_back_to": "validate form",
                }
            ],
        }
    )

    assert sketch.control_blocks[0].requires_merge is False


def test_activity_sketch_accepts_stable_step_and_block_identifiers() -> None:
    sketch = ActivitySketch.model_validate(
        {
            "main_flow": [
                {"step_id": "S1", "action": "validate form"},
                {"step_id": "S2", "action": "store application"},
            ],
            "control_blocks": [
                {
                    "block_id": "B1",
                    "type": "loop",
                    "entry_after_step_id": "S1",
                    "entry_after": "validate form",
                    "branches": [
                        {"label": "errors found", "returns_to_main_flow": False},
                        {"label": "valid", "returns_to_main_flow": True},
                    ],
                    "exit_to_step_id": "S2",
                    "exit_to": "store application",
                    "loop_back_to_step_id": "S1",
                    "loop_back_to": "validate form",
                }
            ],
        }
    )

    first_step = sketch.main_flow[0]
    assert not isinstance(first_step, str)
    assert first_step.step_id == "S1"
    assert sketch.control_blocks[0].block_id == "B1"
    assert sketch.control_blocks[0].entry_after_step_id == "S1"
    assert sketch.control_blocks[0].exit_to_step_id == "S2"


def test_activity_sketch_accepts_branch_local_steps_and_next_block_id() -> None:
    sketch = ActivitySketch.model_validate(
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
                                {"step_id": "S1A", "action": "submit missing documents"}
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
                    "notes": None,
                },
            ],
        }
    )

    first_branch = sketch.control_blocks[0].branches[0]
    second_branch = sketch.control_blocks[0].branches[1]
    assert first_branch.steps[0].step_id == "S1A"
    assert first_branch.steps[0].action == "submit missing documents"
    assert second_branch.next_block_id == "B2"


def test_activity_sketch_accepts_branch_reconnect_to_step_id() -> None:
    sketch = ActivitySketch.model_validate(
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
                            "label": "rework",
                            "returns_to_main_flow": True,
                            "steps": [{"action": "recheck request"}],
                            "next_block_id": None,
                            "child_block_ids": [],
                            "reconnect_to_step_id": "S1",
                        },
                        {
                            "label": "approved",
                            "returns_to_main_flow": True,
                            "steps": [],
                            "next_block_id": None,
                            "child_block_ids": [],
                        },
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "approve request",
                    "loop_back_to_step_id": None,
                    "loop_back_to": None,
                    "notes": None,
                }
            ],
        }
    )

    assert sketch.control_blocks[0].branches[0].reconnect_to_step_id == "S1"
    assert sketch.control_blocks[0].branches[1].reconnect_to_step_id is None


def test_activity_sketch_accepts_child_block_ids_for_one_level_composition() -> None:
    sketch = ActivitySketch.model_validate(
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
                            "label": "security validation",
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
                    "notes": None,
                }
            ],
        }
    )

    assert sketch.control_blocks[0].branches[0].child_block_ids == ["B2"]
    assert sketch.control_blocks[0].branches[1].child_block_ids == ["B3"]


def test_parse_and_validate_activity_sketch_sanitizes_branch_notes_without_mutating_steps() -> None:
    parsed = _parse_and_validate_activity_sketch_json(
        json.dumps(
            {
                "main_flow": [
                    {"step_id": "S1", "action": "review request"},
                    {"step_id": "S2", "action": "finish request"},
                ],
                "control_blocks": [
                    {
                        "block_id": "B1",
                        "type": "decision",
                        "entry_after_step_id": "S1",
                        "entry_after": "review request",
                        "branches": [
                            {
                                "label": "approved",
                                "returns_to_main_flow": True,
                                "steps": [
                                    {
                                        "step_id": "S1A",
                                        "action": "retry provisioning",
                                    }
                                ],
                                "next_block_id": None,
                                "child_block_ids": [],
                            },
                            {
                                "label": "request rejected",
                                "notes": "request rejected",
                                "returns_to_main_flow": True,
                                "steps": [],
                                "next_block_id": None,
                                "child_block_ids": [],
                            },
                        ],
                        "requires_merge": True,
                        "exit_to_step_id": "S2",
                        "exit_to": "finish request",
                        "loop_back_to_step_id": None,
                        "loop_back_to": None,
                        "notes": None,
                    }
                ],
            }
        )
    )

    approved_branch = parsed["control_blocks"][0]["branches"][0]
    rejected_branch = parsed["control_blocks"][0]["branches"][1]
    assert approved_branch["steps"] == [
        {
            "step_id": "S1A",
            "action": "retry provisioning",
        }
    ]
    assert "notes" not in rejected_branch
    assert rejected_branch == {
        "label": "request rejected",
        "returns_to_main_flow": True,
        "steps": [],
        "child_block_ids": [],
    }


def test_extract_keyword_hints_detects_decision_loop_and_retry_guidance() -> None:
    hints = extract_keyword_hints(
        "If errors are found, the user corrects the form and submits it again. Otherwise, the system stores the application."
    )

    assert hints["flags"]["possible_decision"] is True
    assert hints["flags"]["possible_loop"] is True
    assert hints["flags"]["retry_semantics"] is True
    assert hints["flags"]["exit_condition"] is True
    assert any(hint["kind"] == "possible_loop" for hint in hints["hints"])
    assert "again" in hints["evidence"]["loop_terms"]
    assert "corrects" in hints["evidence"]["retry_terms"]


def test_extract_keyword_hints_keeps_resubmission_as_retry_without_loop() -> None:
    hints = extract_keyword_hints(
        "If the documents are incomplete, the student is asked to resubmit the missing documents."
    )

    assert hints["flags"]["possible_decision"] is True
    assert hints["flags"]["possible_loop"] is False
    assert hints["flags"]["retry_semantics"] is True
    assert "resubmit" in hints["evidence"]["retry_terms"]
    assert hints["evidence"]["loop_terms"] == []


def test_extract_keyword_hints_still_detects_explicit_retry_loops() -> None:
    hints = extract_keyword_hints(
        "If payment fails, the customer retries payment until it succeeds."
    )

    assert hints["flags"]["possible_loop"] is True
    assert hints["flags"]["retry_semantics"] is True
    assert "until" in hints["evidence"]["loop_terms"]


def test_activity_sketch_prompt_can_include_keyword_guidance() -> None:
    hints = extract_keyword_hints("If approved, process the request. Otherwise, reject it.")
    prompt = build_activity_sketch_prompt_with_hints(
        "If approved, process the request. Otherwise, reject it.",
        keyword_hints=hints,
    )

    assert "These are soft planning signals extracted from the process text." in prompt
    assert '"possible_decision": true' in prompt.lower()
    assert "Keyword guidance:" in prompt
    assert 'Use loop and retry hints to prefer `type="loop"`' in prompt
    assert "next_block_id" in prompt
    assert "child_block_ids" in prompt
    assert "branch `steps`" in prompt
    assert "A decision block must represent exactly one business question" in prompt
    assert "Do not mix retry, correction, or rework outcomes with approval or rejection outcomes in the same decision block" in prompt
    assert "Parallel -> Loop / Loop" in prompt
    assert "## Branch Continuation Semantics" in prompt
    assert "A branch must use exactly one continuation mechanism" in prompt
    assert "`next_block_id` and `child_block_ids` are mutually exclusive" in prompt
    assert "If `child_block_ids` is non-empty, `next_block_id` must be `null`" in prompt
    assert "If the downstream control structure belongs inside the branch's own topology, use `child_block_ids` instead of `next_block_id`" in prompt
    assert '"next_block_id": "B2",' in prompt
    assert '"child_block_ids": []' in prompt
    assert '"child_block_ids": ["B3"]' not in prompt.split("Return a JSON object with this structure:")[1].split("Rules:")[0]


def test_repair_activity_sketch_removes_invalid_references_and_normalizes_loop_merge() -> None:
    sketch, report = repair_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "validate form"},
                {"step_id": "S2", "action": "store application"},
            ],
            "control_blocks": [
                {
                    "block_id": "B1",
                    "type": "loop",
                    "entry_after_step_id": "S9",
                    "entry_after": "unknown",
                    "branches": [
                        {
                            "label": "retry",
                            "returns_to_main_flow": True,
                            "steps": [],
                            "next_block_id": "B9",
                            "child_block_ids": ["B8"],
                        }
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S8",
                    "exit_to": "missing target",
                    "loop_back_to_step_id": "S7",
                    "loop_back_to": "missing step",
                    "notes": None,
                }
            ],
        }
    )

    block = sketch["control_blocks"][0]
    assert "entry_after_step_id" not in block
    assert block["requires_merge"] is False
    assert "loop_back_to_step_id" not in block
    assert "next_block_id" not in block["branches"][0]
    assert block["branches"][0]["child_block_ids"] == []
    assert report["metrics"]["invalid_reference_count"] >= 3
    assert report["metrics"]["merge_normalization_count"] >= 1
    assert report["metrics"]["child_block_repair_count"] >= 1
    assert report["critical_defects"]


def test_sketch_requires_retry_for_mixed_decision_semantics() -> None:
    _, report = repair_activity_sketch(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review claim"},
                {"step_id": "S2", "action": "resolve claim"},
            ],
            "control_blocks": [
                {
                    "block_id": "B1",
                    "type": "decision",
                    "entry_after_step_id": "S1",
                    "entry_after": "review claim",
                    "branches": [
                        {"label": "additional documents required", "returns_to_main_flow": True, "steps": []},
                        {"label": "claim approved", "returns_to_main_flow": True, "steps": []},
                    ],
                    "requires_merge": True,
                    "exit_to_step_id": "S2",
                    "exit_to": "resolve claim",
                    "notes": None,
                }
            ],
        }
    )

    assert sketch_requires_retry(report) is True
    assert "B1:mixed_decision_semantics" in report["critical_defects"]


def test_validate_graph_against_sketch_uses_step_identifiers_when_present() -> None:
    sketch = {
        "main_flow": [
            {"step_id": "S1", "action": "process payment"},
            {"step_id": "S2", "action": "ship order"},
        ],
        "control_blocks": [
            {
                "block_id": "B1",
                "type": "loop",
                "entry_after_step_id": "S1",
                "entry_after": "wrong label ignored by step id",
                "branches": [
                    {"label": "retry", "returns_to_main_flow": True},
                    {"label": "success", "returns_to_main_flow": True},
                ],
                "requires_merge": False,
                "exit_to_step_id": "S2",
                "exit_to": "also ignored",
                "loop_back_to_step_id": "S1",
                "loop_back_to": "ignored too",
                "notes": None,
            }
        ],
    }
    graph = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "process payment", "origin_step_id": "S1"},
            {"id": "n3", "type": "decision", "label": "payment successful?", "origin_block_id": "B1"},
            {"id": "n4", "type": "action", "name": "retry payment"},
            {"id": "n5", "type": "action", "name": "ship order", "origin_step_id": "S2"},
            {"id": "n6", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n4", "label": "no"},
            {"source": "n3", "target": "n5", "label": "yes"},
            {"source": "n4", "target": "n2", "label": "retry"},
            {"source": "n5", "target": "n6"},
        ],
    }

    report = validate_graph_against_sketch(sketch, graph)

    assert report["issues"] == []
    assert report["metrics"]["resolved_main_flow_step_ids"] == 2
    assert report["metrics"]["resolved_by_origin_step_id"] >= 4
    assert report["metrics"]["resolved_by_name_fallback"] == 0
    assert report["metrics"]["traceability_coverage"] == 2 / 3
    assert report["metrics"]["planner_binding_strength"] == "strong"
    assert report["metrics"]["expected_loop_backs"] == 1
    assert report["metrics"]["realized_loop_backs"] == 1
    assert report["metrics"]["unresolved_block_ids"] == []
    assert report["details"]["step_lookup"] == {
        "S1": "process payment",
        "S2": "ship order",
    }
    assert report["details"]["main_flow_resolution_modes"] == {
        "S1": "origin_step_id",
        "S2": "origin_step_id",
    }


def test_validate_graph_against_sketch_reports_invalid_child_block_references() -> None:
    sketch = {
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
                        "label": "security validation",
                        "returns_to_main_flow": False,
                        "steps": [],
                        "next_block_id": None,
                        "child_block_ids": ["B9"],
                    },
                ],
                "requires_merge": True,
                "exit_to_step_id": "S2",
                "exit_to": "synchronize results",
                "loop_back_to_step_id": None,
                "loop_back_to": None,
                "notes": None,
            },
            {
                "block_id": "B2",
                "type": "loop",
                "entry_after_step_id": "S1",
                "entry_after": "start deployment",
                "branches": [
                    {"label": "retry", "returns_to_main_flow": False, "steps": [], "next_block_id": None, "child_block_ids": []},
                    {"label": "success", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
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
    graph = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "start deployment", "origin_step_id": "S1"},
            {"id": "n3", "type": "fork", "origin_block_id": "B1"},
            {"id": "n4", "type": "action", "name": "retry provisioning"},
            {"id": "n5", "type": "join", "origin_block_id": "B1"},
            {"id": "n6", "type": "action", "name": "synchronize results", "origin_step_id": "S2"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n4"},
            {"source": "n4", "target": "n5"},
            {"source": "n5", "target": "n6"},
        ],
    }

    report = validate_graph_against_sketch(sketch, graph)

    assert "child_block_not_realized" in report["issues"] or "child_block_id_not_found" in report["issues"]
    assert "B9" in report["metrics"]["unresolved_child_block_ids"]


def test_validate_graph_against_sketch_does_not_emit_missing_decision_node_for_late_decision_block() -> None:
    sketch = {
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
                    {"label": "provisioning", "returns_to_main_flow": False, "steps": [], "next_block_id": None, "child_block_ids": ["B2"]},
                    {"label": "compliance", "returns_to_main_flow": False, "steps": [], "next_block_id": None, "child_block_ids": ["B3"]},
                ],
                "requires_merge": True,
                "exit_to_step_id": "S2",
                "exit_to": "synchronize results",
                "loop_back_to_step_id": None,
                "loop_back_to": None,
                "notes": None,
            },
            {
                "block_id": "B2",
                "type": "loop",
                "entry_after_step_id": "S1",
                "entry_after": "start deployment",
                "branches": [
                    {"label": "retry", "returns_to_main_flow": False, "steps": [], "next_block_id": None, "child_block_ids": []},
                    {"label": "success", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                ],
                "requires_merge": False,
                "exit_to_step_id": "S2",
                "exit_to": "synchronize results",
                "loop_back_to_step_id": "S1",
                "loop_back_to": "start deployment",
                "notes": None,
            },
            {
                "block_id": "B3",
                "type": "decision",
                "entry_after_step_id": "S1",
                "entry_after": "start deployment",
                "branches": [
                    {"label": "passed", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                    {"label": "rework", "returns_to_main_flow": True, "steps": [], "next_block_id": None, "child_block_ids": []},
                ],
                "requires_merge": True,
                "exit_to_step_id": "S2",
                "exit_to": "synchronize results",
                "loop_back_to_step_id": None,
                "loop_back_to": None,
                "notes": None,
            },
        ],
    }
    graph = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "start deployment", "origin_step_id": "S1"},
            {"id": "n3", "type": "fork", "origin_block_id": "B1"},
            {"id": "n4", "type": "decision", "label": "retry?", "origin_block_id": "B2"},
            {"id": "n5", "type": "action", "name": "repair provisioning"},
            {"id": "n6", "type": "decision", "label": "compliance passed?", "origin_block_id": "B3"},
            {"id": "n7", "type": "merge", "origin_block_id": "B3"},
            {"id": "n8", "type": "join", "origin_block_id": "B1"},
            {"id": "n9", "type": "action", "name": "synchronize results", "origin_step_id": "S2"},
            {"id": "n10", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n4", "label": "provisioning"},
            {"source": "n4", "target": "n5", "label": "retry"},
            {"source": "n5", "target": "n2"},
            {"source": "n4", "target": "n8", "label": "success"},
            {"source": "n3", "target": "n6", "label": "compliance"},
            {"source": "n6", "target": "n7", "label": "passed"},
            {"source": "n6", "target": "n7", "label": "rework"},
            {"source": "n7", "target": "n8"},
            {"source": "n8", "target": "n9"},
            {"source": "n9", "target": "n10"},
        ],
    }

    report = validate_graph_against_sketch(sketch, graph)

    decision_block = next(
        block for block in report["details"]["block_reports"] if block["block_id"] == "B3"
    )
    assert "missing_decision_node" not in report["issues"]
    assert decision_block["matched_decision_node_ids"] == ["n6"]
    assert decision_block["decision_resolution_mode"] == "origin_block_id"


def test_validate_graph_against_sketch_falls_back_to_action_names_without_traceability() -> None:
    sketch = {
        "main_flow": [
            {"step_id": "S1", "action": "process payment"},
            {"step_id": "S2", "action": "ship order"},
        ],
        "control_blocks": [],
    }
    graph = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "process payment"},
            {"id": "n3", "type": "action", "name": "ship order"},
            {"id": "n4", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n4"},
        ],
    }

    report = validate_graph_against_sketch(sketch, graph)

    assert report["issues"] == []
    assert report["metrics"]["resolved_by_origin_step_id"] == 0
    assert report["metrics"]["resolved_by_name_fallback"] == 2
    assert report["metrics"]["planner_binding_strength"] == "partial"
    assert report["metrics"]["traceability_coverage"] == 0.0
    assert report["metrics"]["unresolved_step_ids"] == []


def test_validate_graph_against_sketch_reports_permuted_loop_back_reference() -> None:
    sketch = {
        "main_flow": [
            {"step_id": "S1", "action": "process payment"},
            {"step_id": "S2", "action": "ship order"},
        ],
        "control_blocks": [
            {
                "block_id": "B1",
                "type": "loop",
                "entry_after_step_id": "S1",
                "entry_after": "process payment",
                "branches": [
                    {"label": "retry", "returns_to_main_flow": True},
                    {"label": "success", "returns_to_main_flow": True},
                ],
                "requires_merge": False,
                "exit_to_step_id": "S2",
                "exit_to": "ship order",
                "loop_back_to_step_id": "S2",
                "loop_back_to": "ship order",
                "notes": None,
            }
        ],
    }
    graph = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "process payment", "origin_step_id": "S1"},
            {"id": "n3", "type": "decision", "label": "payment successful?", "origin_block_id": "B1"},
            {"id": "n4", "type": "action", "name": "retry payment"},
            {"id": "n5", "type": "action", "name": "ship order", "origin_step_id": "S2"},
            {"id": "n6", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n4", "label": "no"},
            {"source": "n3", "target": "n5", "label": "yes"},
            {"source": "n4", "target": "n2", "label": "retry"},
            {"source": "n5", "target": "n6"},
        ],
    }

    report = validate_graph_against_sketch(sketch, graph)

    assert "loop_back_edge_not_realized" in report["issues"]
    assert report["metrics"]["expected_loop_backs"] == 1
    assert report["metrics"]["realized_loop_backs"] == 0


def test_semantic_analysis_flags_merge_and_loop_quality_issues() -> None:
    sketch = {
        "main_flow": [
            {"step_id": "S1", "action": "validate form"},
            {"step_id": "S2", "action": "store application"},
        ],
        "control_blocks": [
            {
                "block_id": "B1",
                "type": "loop",
                "entry_after_step_id": "S1",
                "entry_after": "validate form",
                "branches": [
                    {"label": "errors", "returns_to_main_flow": False},
                    {"label": "valid", "returns_to_main_flow": True},
                ],
                "requires_merge": False,
                "exit_to_step_id": "S2",
                "exit_to": "store application",
                "loop_back_to_step_id": "S1",
                "loop_back_to": "validate form",
                "notes": None,
            }
        ],
    }
    graph = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "validate form", "origin_step_id": "S1"},
            {"id": "n3", "type": "decision", "label": "errors found?", "origin_block_id": "B1"},
            {"id": "n4", "type": "action", "name": "correct form"},
            {"id": "n5", "type": "merge"},
            {"id": "n6", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n4"},
            {"source": "n3", "target": "n5", "label": "valid"},
            {"source": "n5", "target": "n6"},
        ],
    }

    report = analyze_semantic_graph(
        graph,
        sketch=sketch,
        keyword_hints=extract_keyword_hints(
            "If errors are found, the user corrects the form and submits it again. Otherwise, the system stores the application."
        ),
    )
    issue_codes = {issue["code"] for issue in report["issues"]}

    assert "decision_unlabeled_branch" in issue_codes
    assert "merge_underconnected" in issue_codes
    assert "invalid_loop_back_target" in issue_codes
    assert "retry_loop_with_merge" in issue_codes
    assert report["metrics"]["warning_count"] >= 2
    assert report["metrics"]["error_count"] >= 1


def test_semantic_analysis_flags_non_question_decision_text() -> None:
    graph = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "decision", "label": "Check for errors"},
            {"id": "n3", "type": "action", "name": "Correct form"},
            {"id": "n4", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3", "label": "Yes"},
            {"source": "n2", "target": "n4", "label": "No"},
        ],
    }

    report = analyze_semantic_graph(graph)
    issue_codes = {issue["code"] for issue in report["issues"]}

    assert "decision_not_question_like" in issue_codes


def test_debug_model_activity_exposes_keyword_and_semantic_layers() -> None:
    from llm.refinement_generator import debug_model_activity

    sketch_json = json.dumps(
        {
            "main_flow": [
                {"step_id": "S1", "action": "review request"},
                {"step_id": "S2", "action": "store request"},
            ],
            "control_blocks": [],
        }
    )
    graph_json = json.dumps(
        {
            "nodes": [
                {"id": "n1", "type": "initial"},
                {"id": "n2", "type": "action", "name": "review request", "origin_step_id": "S1"},
                {"id": "n3", "type": "action", "name": "store request", "origin_step_id": "S2"},
                {"id": "n4", "type": "final"},
            ],
            "edges": [
                {"source": "n1", "target": "n2"},
                {"source": "n2", "target": "n3"},
                {"source": "n3", "target": "n4"},
            ],
        }
    )

    bundle = debug_model_activity(
        "If approved, store the request. Otherwise, reject it.",
        use_sketch=True,
        llm_caller=lambda prompt: graph_json,
        sketch_llm_caller=lambda prompt: sketch_json,
    )

    assert bundle["keyword_hints"]["flags"]["possible_decision"] is True
    assert "sketch_repair" in bundle
    assert bundle["sketch_repair"]["metrics"]["planner_retry_triggered"] is False
    assert "semantic_analysis" in bundle
    assert "issues" in bundle["semantic_analysis"]


def test_validate_graph_against_sketch_flags_loop_merge_semantics() -> None:
    sketch = {
        "main_flow": ["validate form", "store application"],
        "control_blocks": [
            {
                "type": "loop",
                "entry_after": "validate form",
                "branches": [
                    {"label": "errors found", "returns_to_main_flow": False},
                    {"label": "valid", "returns_to_main_flow": True},
                ],
                "requires_merge": True,
                "exit_to": "store application",
                "loop_back_to": "validate form",
                "notes": None,
            }
        ],
    }
    graph = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "validate form"},
            {"id": "n3", "type": "decision", "label": "errors found?"},
            {"id": "n4", "type": "action", "name": "correct form"},
            {"id": "n5", "type": "action", "name": "store application"},
            {"id": "n6", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n4", "label": "yes"},
            {"source": "n3", "target": "n5", "label": "no"},
            {"source": "n4", "target": "n2", "label": "retry"},
            {"source": "n5", "target": "n6"},
        ],
    }

    report = validate_graph_against_sketch(sketch, graph)

    assert "loop_requires_merge_semantics" in report["issues"]
