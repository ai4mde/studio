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
    }
    debug_calls = []
    imported_graphs = []

    def fake_debug_model_activity(process_text, use_sketch):
        debug_calls.append((process_text, use_sketch))
        return bundle

    def fake_import_graph(graph):
        imported_graphs.append(graph)
        return {
            "project_id": "project-1",
            "session_id": "session-1",
            "system_id": "system-1",
            "diagram_id": "diagram-1",
        }

    monkeypatch.setattr(manual_sketch_debug, "debug_model_activity", fake_debug_model_activity)
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

    assert debug_calls == [("Review the request and finish the process.", True)]
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


def test_import_rejects_both_modes(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manual_sketch_debug",
            "--text",
            "Example",
            "--mode",
            "both",
            "--import",
        ],
    )

    with pytest.raises(ValueError, match="--mode both"):
        manual_sketch_debug.main()


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
    }
    outcomes = [
        ValueError("run 1 failed"),
        ValueError("run 2 failed"),
        bundle,
        bundle,
        RuntimeError("run 5 failed"),
    ]
    debug_calls = []

    def fake_debug_model_activity(process_text, use_sketch):
        debug_calls.append((process_text, use_sketch))
        outcome = outcomes[len(debug_calls) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(manual_sketch_debug, "debug_model_activity", fake_debug_model_activity)
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
