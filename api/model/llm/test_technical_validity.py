from __future__ import annotations

import json

import pytest

from llm.activity_sketch_model import ActivitySketch
from llm.handler import _activity_sketch_response_format
from llm.refinement_generator import (
    _parse_and_validate_activity_graph_json,
    _raise_for_unresolved_explicit_loop_targets,
    debug_model_activity_with_semantic_deterministic_profile,
    generate_and_convert_candidates,
)
from llm.technical_validity import (
    TechnicalValidityError,
    merge_technical_validity_reports,
    normalize_and_validate_activity_graph,
)


def _warning_codes(report: dict) -> set[str]:
    return {str(item["code"]) for item in report["quality_warnings"]}


def test_importable_behaviorally_imperfect_graph_is_accepted_with_warnings() -> None:
    graph = {
        "nodes": [
            {"id": "start", "type": "initial"},
            {"id": "work", "type": "action", "name": "Perform work"},
            {"id": "orphan", "type": "action", "name": "Editable orphan"},
            {"id": "end", "type": "final"},
        ],
        "edges": [{"source": "start", "target": "work", "type": "control"}],
    }

    normalized, report = normalize_and_validate_activity_graph(graph)

    assert normalized == graph
    assert report["technical_accepted"] is True
    assert {"non_final_dead_end", "unreachable_executable_node", "missing_final_reachability"} <= _warning_codes(report)


def test_missing_behavioral_loop_is_not_a_technical_failure() -> None:
    graph = {
        "nodes": [
            {"id": "start", "type": "initial"},
            {"id": "retry", "type": "action", "name": "Revise item"},
            {"id": "end", "type": "final"},
        ],
        "edges": [
            {"source": "start", "target": "retry", "type": "control"},
            {"source": "retry", "target": "end", "type": "control"},
        ],
    }

    _, report = normalize_and_validate_activity_graph(graph)

    assert report["technical_accepted"] is True
    assert report["failure_reason"] is None


def test_only_unresolved_explicit_loop_reference_is_a_technical_failure() -> None:
    _raise_for_unresolved_explicit_loop_targets(
        {"critical_defects": ["L1:missing_loop_back"]}
    )

    with pytest.raises(TechnicalValidityError, match="unresolved explicit loop-back"):
        _raise_for_unresolved_explicit_loop_targets(
            {"critical_defects": ["L1:unresolved_loop_back"]}
        )


def test_semantic_deterministic_boundary_rejects_unresolved_explicit_loop_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "llm.refinement_generator.generate_topology_artifact",
        lambda _: {"artifact": {"structures": []}},
    )
    monkeypatch.setattr(
        "llm.refinement_generator.generate_semantic_sketch_plan",
        lambda *_, **__: {"artifact": {}, "keyword_hints": {}},
    )
    monkeypatch.setattr(
        "llm.refinement_generator.compile_topology_and_semantics_to_activity_sketch",
        lambda *_: {"main_flow": [], "control_blocks": []},
    )
    monkeypatch.setattr(
        "llm.refinement_generator.repair_activity_sketch",
        lambda _: (
            {"main_flow": [], "control_blocks": []},
            {"critical_defects": ["L1:unresolved_loop_back"]},
        ),
    )
    monkeypatch.setattr(
        "llm.refinement_generator.compile_activity_sketch",
        lambda _: pytest.fail("compiler must not receive an unresolved explicit reference"),
    )

    with pytest.raises(TechnicalValidityError, match="unresolved explicit loop-back"):
        debug_model_activity_with_semantic_deterministic_profile("Retry work.")


def test_strict_activity_sketch_schema_includes_block_loop_target() -> None:
    schema = _activity_sketch_response_format()["json_schema"]["schema"]
    block_schema = schema["properties"]["control_blocks"]["items"]
    assert block_schema["properties"]["loop_back_to_block_id"] == {
        "type": ["string", "null"]
    }
    assert "loop_back_to_block_id" in block_schema["required"]

    payload = {
        "main_flow": [{"step_id": "S1", "action": "Review item"}],
        "control_blocks": [
            {
                "block_id": "L1",
                "type": "loop",
                "entry_after": "Review item",
                "entry_after_step_id": "S1",
                "branches": [],
                "requires_merge": False,
                "exit_to": None,
                "exit_to_step_id": None,
                "loop_back_to": None,
                "loop_back_to_step_id": None,
                "loop_back_to_block_id": "L1",
                "notes": None,
            }
        ],
    }
    emitted = ActivitySketch.model_validate(payload).model_dump(exclude_none=True)
    assert emitted["control_blocks"][0]["loop_back_to_block_id"] == "L1"


def test_one_sided_dangling_edge_is_dropped_and_recorded() -> None:
    graph = {
        "nodes": [
            {"id": "start", "type": "initial"},
            {"id": "work", "type": "action", "name": "Perform work"},
        ],
        "edges": [
            {"source": "start", "target": "work", "type": "control"},
            {"source": "work", "target": "missing", "type": "control", "label": "broken"},
        ],
    }

    normalized, report = normalize_and_validate_activity_graph(graph)

    assert len(normalized["edges"]) == 1
    assert report["normalization_applied"] is True
    assert report["dropped_edges"][0]["reason"] == "one_sided_dangling_reference"


def test_missing_isolated_identity_and_exact_duplicate_edge_are_normalized() -> None:
    normalized, report = normalize_and_validate_activity_graph(
        {
            "nodes": [
                {"id": "start", "type": "initial"},
                {"type": "action", "name": "Unconnected editable note"},
            ],
            "edges": [
                {"source": "start", "target": "start", "type": "control"},
                {"source": "start", "target": "start", "type": "control"},
            ],
        }
    )

    assert normalized["nodes"][1]["id"] == "technical_node_2"
    assert len(normalized["edges"]) == 1
    assert report["normalization_applied"] is True


def test_later_validation_does_not_erase_normalization_provenance() -> None:
    raw = {
        "nodes": [
            {"node_id": "start", "type": "initial"},
            {"id": "work", "type": "action", "name": "Work"},
        ],
        "edges": [
            {"source": "start", "target": "work", "type": "control"},
            {"source": "start", "target": "work", "type": "control"},
            {"source": "work", "target": "missing", "type": "control"},
        ],
    }
    normalized, first = normalize_and_validate_activity_graph(raw)
    _, later = normalize_and_validate_activity_graph(normalized)

    merged = merge_technical_validity_reports(first, later)

    kinds = {item["kind"] for item in merged["normalizations"]}
    assert "node_id_alias" in kinds
    assert "removed_exact_duplicate_edge" in kinds
    assert "dropped_one_sided_dangling_edge" in kinds
    assert merged["dropped_edges"][0]["edge"]["target"] == "missing"
    assert merged["normalization_applied"] is True
    assert merged["technical_accepted"] is True


def test_candidate_provenance_retains_initial_normalization_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = {
        "nodes": [{"node_id": "work", "type": "action", "name": "Work"}],
        "edges": [{"source": "work", "target": "missing", "type": "control"}],
    }
    clean, initial_report = normalize_and_validate_activity_graph(raw)
    debug_bundle = {
        "parsed": clean,
        "stage_artifacts": {"validation": {"technical_validity": initial_report}},
    }
    monkeypatch.setattr(
        "llm.refinement_generator.model_activity", lambda **_: debug_bundle
    )

    candidate = generate_and_convert_candidates(
        "Perform work.", n=1, project_id="project-id", pipeline_profile="stable"
    )[0]

    assert candidate["technical_validity"]["normalization_applied"] is True
    assert candidate["technical_validity"]["dropped_edges"][0]["edge"]["target"] == "missing"
    assert candidate["technical_validity"]["conversion_result"] == "accepted"
    assert (
        candidate["debug_bundle"]["stage_artifacts"]["validation"]["technical_validity"]
        == candidate["technical_validity"]
    )


def test_ambiguous_invalid_reference_and_unsupported_node_are_hard_failures() -> None:
    with pytest.raises(TechnicalValidityError, match="two unknown endpoint identities"):
        normalize_and_validate_activity_graph(
            {
                "nodes": [{"id": "known", "type": "action", "name": "Work"}],
                "edges": [{"source": "missing-a", "target": "missing-b"}],
            }
        )

    with pytest.raises(TechnicalValidityError, match="not technically representable"):
        normalize_and_validate_activity_graph(
            {"nodes": [{"id": "n1", "type": "unsupported"}], "edges": []}
        )


def test_failed_parse_retains_normalization_and_failure_provenance() -> None:
    raw = {
        "nodes": [{"node_id": "known", "type": "action", "name": "Work"}],
        "edges": [{"source": "missing-a", "target": "missing-b", "type": "control"}],
    }

    with pytest.raises(TechnicalValidityError) as exc_info:
        _parse_and_validate_activity_graph_json(json.dumps(raw))

    assert exc_info.value.report["failure_reason"] == (
        "edge 1 has two unknown endpoint identities"
    )
    assert any(
        item["kind"] == "node_id_alias"
        for item in exc_info.value.report["normalizations"]
    )


def test_missing_initial_and_final_are_warnings_not_import_requirements() -> None:
    normalized, report = normalize_and_validate_activity_graph(
        {"nodes": [{"id": "work", "type": "action", "name": "Work"}], "edges": []}
    )

    assert normalized["nodes"][0]["id"] == "work"
    assert report["technical_accepted"] is True
    assert {"missing_initial_node", "missing_final_node"} <= _warning_codes(report)


def test_quality_warning_does_not_trigger_an_inner_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def fake_model_activity(**_: object) -> dict:
        nonlocal calls
        calls += 1
        return {
            "nodes": [
                {"id": "start", "type": "initial"},
                {"id": "dead-end", "type": "action", "name": "Editable dead end"},
            ],
            "edges": [{"source": "start", "target": "dead-end", "type": "control"}],
        }

    monkeypatch.setattr("llm.refinement_generator.model_activity", fake_model_activity)
    candidates = generate_and_convert_candidates(
        "Perform work.", n=1, project_id="project-id", pipeline_profile="stable"
    )

    assert calls == 1
    assert candidates[0]["technical_validity"]["technical_accepted"] is True
    assert candidates[0]["technical_validity"]["conversion_result"] == "accepted"
    assert "non_final_dead_end" in _warning_codes(candidates[0]["technical_validity"])


def test_conversion_failure_is_a_technical_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "llm.refinement_generator.model_activity",
        lambda **_: {"nodes": [{"id": "work", "type": "action", "name": "Work"}], "edges": []},
    )
    monkeypatch.setattr(
        "llm.refinement_generator.convert_to_ai4mde",
        lambda **_: (_ for _ in ()).throw(ValueError("unsupported conversion")),
    )

    with pytest.raises(TechnicalValidityError, match="failed AI4MDE conversion") as exc_info:
        generate_and_convert_candidates(
            "Perform work.", n=1, project_id="project-id", pipeline_profile="stable"
        )

    assert exc_info.value.report["conversion_result"] == "failed"
    assert exc_info.value.report["technical_accepted"] is False
