from __future__ import annotations

import json
from unittest.mock import patch

from llm.semantic_sketch_experiment import (
    build_semantic_sketch_experiment_prompt,
    generate_semantic_sketch_plan,
    parse_semantic_sketch_plan_json,
    semantic_sketch_plan_response_format,
)
from llm.source_action_candidates import (
    calculate_source_action_coverage,
    harvest_source_action_candidates,
)


def _plan(*steps: dict) -> dict:
    return {
        "root_actions": [{"slot_id": "ROOT_START", "actions": list(steps)}],
        "branch_plans": [],
    }


def test_harvester_extracts_stable_ordered_actions_with_exact_offsets() -> None:
    process_text = (
        "The employee registers the application,  checks the documents,\n"
        "records the result, informs the supervisor, and stores the completed file."
    )

    first = harvest_source_action_candidates(process_text)
    second = harvest_source_action_candidates(process_text)

    assert first == second
    assert [candidate["source_action_id"] for candidate in first] == ["SA1", "SA2", "SA3", "SA4", "SA5"]
    assert [candidate["source_span"]["text"] for candidate in first] == [
        "registers the application",
        "checks the documents",
        "records the result",
        "informs the supervisor",
        "stores the completed file",
    ]
    for candidate in first:
        span = candidate["source_span"]
        assert process_text[span["start"] : span["end"]] == span["text"]


def test_harvester_supports_clear_coordinated_actions() -> None:
    candidates = harvest_source_action_candidates(
        "The clerk receives the request and retrieves the customer file."
    )

    assert [candidate["source_span"]["text"] for candidate in candidates] == [
        "receives the request",
        "retrieves the customer file",
    ]


def test_harvester_keeps_states_conditions_descriptions_and_coreference_non_binding() -> None:
    process_text = (
        "The manager is responsible for the northern region. "
        "While the file remains open, the clerk reviews the request. "
        "If necessary, the clerk archives the file. "
        "The clerk receives the request, reviews it, approves it, and archives it."
    )

    candidates = harvest_source_action_candidates(process_text)

    assert [candidate["source_span"]["text"] for candidate in candidates] == ["receives the request"]


def test_harvester_rejects_verb_like_nouns_and_incomplete_coordinated_predicates() -> None:
    process_text = (
        "The registration form and the print from the system are stored in the patient file. "
        "The print contains operational data. "
        "The office prepares and sends a letter to the doctor."
    )

    candidates = harvest_source_action_candidates(process_text)

    assert [candidate["source_span"]["text"] for candidate in candidates] == [
        "sends a letter to the doctor"
    ]


def test_harvester_supports_narrow_executable_passive_actions() -> None:
    process_text = (
        "The request is received. The request is archived. "
        "The file is stored. The application is reviewed."
    )

    candidates = harvest_source_action_candidates(process_text)

    assert [candidate["source_action_id"] for candidate in candidates] == ["SA1", "SA2", "SA3", "SA4"]
    assert [candidate["source_span"]["text"] for candidate in candidates] == [
        "request is received",
        "request is archived",
        "file is stored",
        "application is reviewed",
    ]
    for candidate in candidates:
        span = candidate["source_span"]
        assert process_text[span["start"] : span["end"]] == span["text"]


def test_harvester_does_not_treat_passive_states_as_actions() -> None:
    process_text = (
        "The request is valid. The request is available. The application is complete. "
        "The file is ready. The request is required."
    )

    assert harvest_source_action_candidates(process_text) == []


def test_harvester_extracts_only_clear_main_action_after_temporal_prefix() -> None:
    process_text = (
        "After the review is completed, the employee stores the file. "
        "Once the documents are checked, the clerk records the result."
    )

    candidates = harvest_source_action_candidates(process_text)

    assert [candidate["source_action_id"] for candidate in candidates] == ["SA1", "SA2"]
    assert [candidate["source_span"]["text"] for candidate in candidates] == [
        "stores the file",
        "records the result",
    ]
    assert all("completed" not in candidate["source_span"]["text"] for candidate in candidates)
    assert all("checked" not in candidate["source_span"]["text"] for candidate in candidates)


def test_harvester_rejects_non_executable_main_state_after_temporal_prefix() -> None:
    process_text = (
        "After the review, the file is available. "
        "Once the process is complete, the result is ready."
    )

    assert harvest_source_action_candidates(process_text) == []


def test_harvester_temporal_main_clause_offsets_order_and_deduplication_are_stable() -> None:
    process_text = "After  the review is completed,\n  the employee stores the file."

    first = harvest_source_action_candidates(process_text)
    second = harvest_source_action_candidates(process_text)

    assert first == second
    assert first == [
        {
            "source_action_id": "SA1",
            "source_span": {
                "start": process_text.index("stores"),
                "end": process_text.index("stores") + len("stores the file"),
                "text": "stores the file",
            },
        }
    ]


def test_coverage_supports_one_to_one_and_combined_traceability() -> None:
    candidates = harvest_source_action_candidates(
        "The clerk receives the request and retrieves the customer file."
    )

    one_to_one = calculate_source_action_coverage(
        candidates,
        _plan(
            {"action": "receive request", "source_action_ids": ["SA1"]},
            {"action": "retrieve file", "source_action_ids": ["SA2"]},
        ),
    )
    combined = calculate_source_action_coverage(
        candidates,
        _plan({"action": "receive request and retrieve file", "source_action_ids": ["SA1", "SA2"]}),
    )

    assert one_to_one["coverage_ratio"] == 1.0
    assert combined["coverage_ratio"] == 1.0
    assert one_to_one["uncovered_source_action_ids"] == []
    assert combined["uncovered_source_action_ids"] == []


def test_coverage_supports_split_steps_without_inflating_completeness() -> None:
    candidates = harvest_source_action_candidates("The clerk reviews the application.")

    report = calculate_source_action_coverage(
        candidates,
        _plan(
            {"action": "review identity", "source_action_ids": ["SA1"]},
            {"action": "review evidence", "source_action_ids": ["SA1"]},
        ),
    )

    assert report["covered_source_action_ids"] == ["SA1"]
    assert report["coverage_ratio"] == 1.0
    assert report["duplicate_coverage"] == [{"source_action_id": "SA1", "reference_count": 2}]


def test_coverage_reports_uncovered_and_unknown_ids_without_rejecting_plan() -> None:
    candidates = harvest_source_action_candidates(
        "The clerk receives the request and retrieves the customer file."
    )

    report = calculate_source_action_coverage(
        candidates,
        _plan({"action": "receive request", "source_action_ids": ["SA1", "SA99"]}),
    )

    assert report["covered_source_action_ids"] == ["SA1"]
    assert report["uncovered_source_action_ids"] == ["SA2"]
    assert report["unknown_source_action_ids"] == ["SA99"]
    assert len(report["warnings"]) == 2


def test_semantic_step_schema_requires_minimal_traceability_field() -> None:
    schema = semantic_sketch_plan_response_format()["json_schema"]["schema"]
    step_schema = schema["$defs"]["SemanticBranchStep"]

    assert "source_action_ids" in step_schema["required"]
    assert step_schema["properties"]["source_action_ids"]["type"] == "array"
    assert "default" not in step_schema["properties"]["source_action_ids"]


def test_old_semantic_payload_remains_backward_compatible() -> None:
    old_payload = {
        "root_actions": [{"slot_id": "ROOT_START", "actions": [{"action": "receive request"}]}],
        "branch_plans": [],
    }

    assert parse_semantic_sketch_plan_json(json.dumps(old_payload)) == old_payload


def test_semantic_payload_preserves_source_action_ids() -> None:
    payload = {
        "root_actions": [
            {
                "slot_id": "ROOT_START",
                "actions": [{"action": "receive request", "source_action_ids": ["SA1"]}],
            }
        ],
        "branch_plans": [],
    }

    assert parse_semantic_sketch_plan_json(json.dumps(payload)) == payload


def test_prompt_supplies_only_candidate_ids_and_exact_text() -> None:
    process_text = "The clerk receives the request."
    candidates = harvest_source_action_candidates(process_text)

    prompt = build_semantic_sketch_experiment_prompt(
        process_text,
        topology_artifact={"structures": []},
        source_action_candidates=candidates,
    )

    assert '"source_action_id": "SA1"' in prompt
    assert '"source_text": "receives the request"' in prompt
    assert '"start"' not in prompt
    assert '"end"' not in prompt
    assert "One semantic action may reference multiple IDs" in prompt


def test_prompt_does_not_demonstrate_an_unknown_id_when_inventory_is_empty() -> None:
    prompt = build_semantic_sketch_experiment_prompt(
        "The file remains open.",
        topology_artifact={"structures": []},
        source_action_candidates=[],
    )

    assert '"source_action_ids": []' in prompt
    assert '"source_action_ids": ["SA1"]' not in prompt


def test_uncovered_candidate_is_observational_and_does_not_retry() -> None:
    raw_plan = json.dumps(
        {
            "root_actions": [{"slot_id": "ROOT_START", "actions": [{"action": "receive request"}]}],
            "branch_plans": [],
        }
    )

    with patch("llm.semantic_sketch_experiment.call_openai", return_value=raw_plan) as mocked_call:
        result = generate_semantic_sketch_plan(
            "The clerk receives the request.",
            topology_artifact={"structures": []},
        )

    assert mocked_call.call_count == 1
    assert len(result["planner_attempts"]) == 1
    assert result["planner_attempts"][0]["validation_error"] is None
    assert result["source_action_coverage"]["uncovered_source_action_ids"] == ["SA1"]
    assert result["source_action_coverage"]["warnings"]


def test_fallback_json_mode_preserves_traceability_and_coverage() -> None:
    traced_plan = json.dumps(
        {
            "root_actions": [
                {
                    "slot_id": "ROOT_START",
                    "actions": [{"action": "receive request", "source_action_ids": ["SA1"]}],
                }
            ],
            "branch_plans": [],
        }
    )

    with patch(
        "llm.semantic_sketch_experiment.call_openai",
        side_effect=[RuntimeError("structured output unavailable"), traced_plan],
    ) as mocked_call:
        result = generate_semantic_sketch_plan(
            "The clerk receives the request.",
            topology_artifact={"structures": []},
        )

    assert mocked_call.call_count == 2
    assert result["response_mode"] == "fallback_json_mode"
    assert result["source_action_coverage"]["covered_source_action_ids"] == ["SA1"]
    assert result["source_action_coverage"]["warnings"] == []
