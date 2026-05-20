from __future__ import annotations

import json
import sys
from pathlib import Path

MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from llm.activity_sketch_model import ActivitySketch
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
