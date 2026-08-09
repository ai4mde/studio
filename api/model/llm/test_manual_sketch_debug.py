from __future__ import annotations

import sys

import pytest

from llm import manual_sketch_debug


def test_main_imports_exact_generated_graph_once(monkeypatch, capsys):
    parsed_graph = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "Review request"},
            {"id": "n3", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "control"},
            {"source": "n2", "target": "n3", "type": "control"},
        ],
    }
    bundle = {
        "parsed": parsed_graph,
        "prompt": "prompt",
        "keyword_hints": None,
        "sketch": None,
        "sketch_alignment": None,
        "semantic_analysis": None,
        "executed_stages": ["Sketch Planner", "Graph Realizer", "Validation"],
        "stage_artifacts": {"initial_graph": parsed_graph, "final_graph": parsed_graph},
    }
    debug_calls = []
    imported_graphs = []

    def fake_generate_activity_model(process_text, **kwargs):
        debug_calls.append((process_text, kwargs))
        return bundle

    def fake_import_graph(graph):
        imported_graphs.append(graph)
        return {
            "project_id": "project-1",
            "session_id": "session-1",
            "system_id": "system-1",
            "diagram_id": "diagram-1",
        }

    monkeypatch.setattr(manual_sketch_debug, "generate_activity_model", fake_generate_activity_model)
    monkeypatch.setattr(manual_sketch_debug, "_import_graph_into_ai4mde", fake_import_graph)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manual_sketch_debug",
            "--text",
            "Review the request and finish the process.",
            "--import",
        ],
    )

    manual_sketch_debug.main()

    assert debug_calls == [
        (
            "Review the request and finish the process.",
            {
                "debug": True,
                "use_sketch": True,
                "pipeline_profile": "both_agents",
                "enable_sketch_review_agent": None,
                "enable_prompted_sketch_repair_agent": None,
                "enable_graph_repair_agent": None,
            },
        )
    ]
    assert imported_graphs == [parsed_graph]

    stdout = capsys.readouterr().out
    assert "project_id: project-1" in stdout
    assert "session_id: session-1" in stdout
    assert "system_id: system-1" in stdout
    assert "ui_path: /diagram/diagram-1" in stdout


def test_import_rejects_multiple_runs(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manual_sketch_debug",
            "--text",
            "Example",
            "--runs",
            "2",
            "--import",
        ],
    )

    with pytest.raises(ValueError, match="--runs 1"):
        manual_sketch_debug.main()


def test_import_allows_single_run_default_configuration(monkeypatch):
    imported_graphs = []

    def fake_generate_activity_model(process_text, **kwargs):
        return {
            "parsed": {"nodes": [], "edges": []},
            "prompt": "prompt",
            "executed_stages": ["Graph Realizer", "Validation"],
            "stage_artifacts": {"initial_graph": {"nodes": [], "edges": []}, "final_graph": {"nodes": [], "edges": []}},
        }

    def fake_import_graph(graph):
        imported_graphs.append(graph)
        return {
            "project_id": "project-1",
            "session_id": "session-1",
            "system_id": "system-1",
            "diagram_id": None,
        }

    monkeypatch.setattr(manual_sketch_debug, "generate_activity_model", fake_generate_activity_model)
    monkeypatch.setattr(manual_sketch_debug, "_import_graph_into_ai4mde", fake_import_graph)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manual_sketch_debug",
            "--text",
            "Example",
            "--import",
        ],
    )

    manual_sketch_debug.main()
    assert imported_graphs == [{"nodes": [], "edges": []}]


def test_main_continues_batch_after_per_run_failures(monkeypatch, capsys):
    parsed_graph = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "Review request"},
            {"id": "n3", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "control"},
            {"source": "n2", "target": "n3", "type": "control"},
        ],
    }
    bundle = {
        "parsed": parsed_graph,
        "prompt": "prompt",
        "keyword_hints": None,
        "sketch": None,
        "sketch_repair": None,
        "sketch_alignment": None,
        "semantic_analysis": None,
        "executed_stages": ["Sketch Planner", "Graph Realizer", "Validation"],
        "stage_artifacts": {"initial_graph": parsed_graph, "final_graph": parsed_graph},
    }
    outcomes = [
        ValueError("run 1 failed"),
        ValueError("run 2 failed"),
        bundle,
        bundle,
        RuntimeError("run 5 failed"),
    ]
    debug_calls = []

    def fake_generate_activity_model(process_text, **kwargs):
        debug_calls.append((process_text, kwargs))
        outcome = outcomes[len(debug_calls) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(manual_sketch_debug, "generate_activity_model", fake_generate_activity_model)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manual_sketch_debug",
            "--text",
            "Review the request and finish the process.",
            "--runs",
            "5",
        ],
    )

    manual_sketch_debug.main()

    assert len(debug_calls) == 5

    stdout = capsys.readouterr().out
    assert "run_failed: ValueError: run 1 failed" in stdout
    assert "run_failed: ValueError: run 2 failed" in stdout
    assert "=== with_sketch run 3/5 ===" in stdout
    assert "=== with_sketch run 4/5 ===" in stdout
    assert "run_failed: RuntimeError: run 5 failed" in stdout
    assert "=== with_sketch failures ===" in stdout
    assert "failures: 3/5" in stdout
    assert "run 1: ValueError: run 1 failed" in stdout
    assert "run 2: ValueError: run 2 failed" in stdout
    assert "run 5: RuntimeError: run 5 failed" in stdout


def test_pipeline_profile_and_runs_are_forwarded_together(monkeypatch):
    debug_calls = []

    def fake_generate_activity_model(process_text, **kwargs):
        debug_calls.append((process_text, kwargs))
        return {
            "parsed": {"nodes": [], "edges": []},
            "prompt": "prompt",
            "executed_stages": ["Graph Realizer", "Validation"],
            "stage_artifacts": {"initial_graph": {"nodes": [], "edges": []}, "final_graph": {"nodes": [], "edges": []}},
        }

    monkeypatch.setattr(manual_sketch_debug, "generate_activity_model", fake_generate_activity_model)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manual_sketch_debug",
            "--text",
            "Example",
            "--runs",
            "2",
            "--pipeline-profile",
            "graph_repair_only",
            "--show-topology",
        ],
    )

    manual_sketch_debug.main()

    assert len(debug_calls) == 2
    for _, kwargs in debug_calls:
        assert kwargs["pipeline_profile"] == "graph_repair_only"
        assert kwargs["debug"] is True
        assert kwargs["use_sketch"] is True


def test_show_review_alias_prints_review_stage(monkeypatch, capsys):
    reviewed_sketch = {"main_flow": [{"step_id": "S1", "action": "Review request"}], "control_blocks": []}

    def fake_generate_activity_model(process_text, **kwargs):
        return {
            "parsed": {"nodes": [], "edges": []},
            "prompt": "prompt",
            "executed_stages": ["Sketch Planner", "Sketch Review Agent", "Sketch Repair", "Graph Realizer", "Validation"],
            "stage_artifacts": {
                "original_sketch": {"main_flow": [], "control_blocks": []},
                "reviewed_sketch": reviewed_sketch,
                "repaired_sketch": reviewed_sketch,
                "initial_graph": {"nodes": [], "edges": []},
                "final_graph": {"nodes": [], "edges": []},
                "validation": {},
            },
        }

    monkeypatch.setattr(manual_sketch_debug, "generate_activity_model", fake_generate_activity_model)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manual_sketch_debug",
            "--text",
            "Example",
            "--show-review",
        ],
    )

    manual_sketch_debug.main()

    stdout = capsys.readouterr().out
    assert "SKETCH_AFTER_REVIEW_AGENT" in stdout


def test_use_experimental_compiler_routes_to_compiler_debug_path(monkeypatch, capsys):
    bundle = {
        "parsed": {
            "nodes": [
                {"id": "n1", "type": "initial"},
                {"id": "n2", "type": "action", "name": "Verify claim", "origin_step_id": "S1"},
                {"id": "n3", "type": "final"},
            ],
            "edges": [
                {"source": "n1", "target": "n2", "type": "control"},
                {"source": "n2", "target": "n3", "type": "control"},
            ],
        },
        "prompt": "sketch prompt",
        "keyword_hints": {"flags": {"retry_semantics": True}, "hints": []},
        "sketch": {"main_flow": [{"step_id": "S1", "action": "Verify claim"}], "control_blocks": []},
        "sketch_repair": {"metrics": {}, "critical_defects": []},
        "sketch_alignment": {"metrics": {}, "details": {}, "issues": []},
        "semantic_analysis": {"issues": [], "metrics": {}},
        "executed_stages": ["Sketch Planner", "Deterministic Compiler", "Validation"],
        "stage_artifacts": {
            "original_sketch": {"main_flow": [{"step_id": "S1", "action": "Verify claim"}], "control_blocks": []},
            "reviewed_sketch": None,
            "repaired_sketch": {"main_flow": [{"step_id": "S1", "action": "Verify claim"}], "control_blocks": []},
            "initial_graph": {
                "nodes": [
                    {"id": "n1", "type": "initial"},
                    {"id": "n2", "type": "action", "name": "Verify claim", "origin_step_id": "S1"},
                    {"id": "n3", "type": "final"},
                ],
                "edges": [
                    {"source": "n1", "target": "n2", "type": "control"},
                    {"source": "n2", "target": "n3", "type": "control"},
                ],
            },
            "repaired_graph": None,
            "final_graph": {
                "nodes": [
                    {"id": "n1", "type": "initial"},
                    {"id": "n2", "type": "action", "name": "Verify claim", "origin_step_id": "S1"},
                    {"id": "n3", "type": "final"},
                ],
                "edges": [
                    {"source": "n1", "target": "n2", "type": "control"},
                    {"source": "n2", "target": "n3", "type": "control"},
                ],
            },
            "validation": {
                "sketch_alignment": {"issues": []},
                "semantic_analysis": {"issues": []},
                "topology_report": {"issues": []},
            },
        },
    }
    compiler_calls = []
    baseline_calls = []

    def fake_compiler_debug(process_text, **kwargs):
        compiler_calls.append((process_text, kwargs))
        return bundle

    def fake_generate_activity_model(process_text, **kwargs):
        baseline_calls.append((process_text, kwargs))
        return bundle

    monkeypatch.setattr(
        manual_sketch_debug,
        "debug_model_activity_with_experimental_compiler",
        fake_compiler_debug,
    )
    monkeypatch.setattr(manual_sketch_debug, "generate_activity_model", fake_generate_activity_model)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manual_sketch_debug",
            "--text",
            "Verify claim and finish.",
            "--use-experimental-compiler",
            "--show-all-stages",
        ],
    )

    manual_sketch_debug.main()

    assert baseline_calls == []
    assert compiler_calls == [
        (
            "Verify claim and finish.",
            {
                "use_sketch_review_agent": False,
                "use_prompted_sketch_repair_agent": False,
            },
        )
    ]

    stdout = capsys.readouterr().out
    assert "SKETCH_PLANNER_OUTPUT" in stdout
    assert "SKETCH_AFTER_REPAIR" in stdout
    assert "INITIAL_GRAPH" in stdout
    assert "FINAL_GRAPH" in stdout
    assert "VALIDATION_DIAGNOSTICS" in stdout


def test_use_experimental_compiler_forwards_sketch_review_toggle(monkeypatch):
    compiler_calls = []

    def fake_compiler_debug(process_text, **kwargs):
        compiler_calls.append((process_text, kwargs))
        return {
            "parsed": {"nodes": [], "edges": []},
            "prompt": "prompt",
            "executed_stages": ["Sketch Planner", "Sketch Review Agent", "Sketch Repair", "Deterministic Compiler", "Validation"],
            "stage_artifacts": {
                "original_sketch": {"main_flow": [], "control_blocks": []},
                "reviewed_sketch": {"main_flow": [], "control_blocks": []},
                "repaired_sketch": {"main_flow": [], "control_blocks": []},
                "initial_graph": {"nodes": [], "edges": []},
                "final_graph": {"nodes": [], "edges": []},
                "validation": {},
            },
        }

    monkeypatch.setattr(
        manual_sketch_debug,
        "debug_model_activity_with_experimental_compiler",
        fake_compiler_debug,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manual_sketch_debug",
            "--text",
            "Example",
            "--use-experimental-compiler",
            "--enable-sketch-review-agent",
        ],
    )

    manual_sketch_debug.main()

    assert compiler_calls == [
        (
            "Example",
            {
                "use_sketch_review_agent": True,
                "use_prompted_sketch_repair_agent": False,
            },
        )
    ]
