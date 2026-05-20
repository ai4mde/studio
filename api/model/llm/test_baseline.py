# Unit tests: mocked LLM (no network, no DB, no AI4MDE conversion).
#
#   poetry run pytest model/llm/test_baseline.py -q
#
# Optional live OpenAI (still no import):
#   OPENAI_API_KEY=... poetry run pytest model/llm/test_baseline.py -k live_openai -s
#
# Optional full pipeline including DB import (requires Django + project id):
#   RUN_BASELINE_IMPORT_INTEGRATION=1 OPENAI_API_KEY=... EXPERIMENT_DEFAULT_PROJECT_ID=... \\
#     poetry run pytest model/llm/test_baseline.py -k import_integration -s

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

import pytest

MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from llm._test_helpers import create_test_project, import_and_validate_system, setup_django
from llm.prompt_builder import build_activity_prompt
from llm.refinement_generator import debug_model_activity, model_activity

# Minimal valid graph the validator accepts (what a mocked LLM might return).
_MOCK_LLM_JSON = json.dumps(
    {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "Do work"},
            {"id": "n3", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "controlflow"},
            {"source": "n2", "target": "n3", "type": "controlflow"},
        ],
    }
)

BASELINE_PROCESS_TEXT = (
    "Receive order, process order, send confirmation. "
    "User logs in, system verifies credentials, dashboard is shown."
)


def _fake_llm_returns_valid_graph(prompt: str) -> str:
    assert isinstance(prompt, str) and len(prompt) > 0
    return _MOCK_LLM_JSON


def test_model_activity_baseline_mock_llm_graph_schema() -> None:
    """Prompt → LLM → JSON validation only (no converter, no import)."""
    graph = model_activity(
        BASELINE_PROCESS_TEXT,
        llm_caller=_fake_llm_returns_valid_graph,
    )
    assert isinstance(graph, dict)
    assert isinstance(graph.get("nodes"), list) and len(graph["nodes"]) >= 1
    assert isinstance(graph.get("edges"), list)
    for node in graph["nodes"]:
        assert isinstance(node, dict)
        assert "id" in node and "type" in node
        if node.get("type") == "action":
            assert "name" in node
    for edge in graph["edges"]:
        assert "source" in edge and "target" in edge


def test_model_activity_refinement_mock_llm_graph_schema() -> None:
    current = {
        "nodes": [{"id": "a1", "type": "initial"}],
        "edges": [],
    }

    def fake_llm(prompt: str) -> str:
        assert "a1" in prompt or "initial" in prompt.lower() or len(prompt) > 50
        return _MOCK_LLM_JSON

    graph = model_activity(
        "Extend the process",
        current_model=current,
        instruction="Add steps",
        llm_caller=fake_llm,
    )
    assert isinstance(graph["nodes"], list)
    assert isinstance(graph["edges"], list)


def test_debug_model_activity_exposes_prompt_and_raw() -> None:
    bundle = debug_model_activity(
        "Short process",
        llm_caller=_fake_llm_returns_valid_graph,
    )
    assert set(bundle.keys()) >= {"prompt", "raw_response", "parsed", "model"}
    assert bundle["raw_response"] == _MOCK_LLM_JSON
    assert bundle["parsed"] == bundle["model"]
    assert bundle["parsed"]["nodes"][1]["name"] == "Do work"


def test_model_activity_uses_sketch_for_baseline_when_enabled() -> None:
    sketch_json = json.dumps(
        {
            "main_flow": ["submit order", "process order"],
            "control_blocks": [
                {
                    "type": "decision",
                    "entry_after": "submit order",
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
        assert "Topology plan" in prompt
        assert "topology plan as authoritative" in prompt
        assert "requires_merge" in prompt
        assert '"main_flow"' in prompt
        return _MOCK_LLM_JSON

    bundle = debug_model_activity(
        "Submit and process order",
        llm_caller=fake_graph_llm,
        sketch_llm_caller=lambda prompt: sketch_json,
        use_sketch=True,
    )

    assert bundle["sketch"]["main_flow"] == ["submit order", "process order"]
    assert bundle["parsed"]["nodes"][1]["name"] == "Do work"
    assert bundle["sketch_alignment"]["metrics"]["control_block_count"] == 1


def test_model_activity_skips_sketch_for_refinement_even_if_enabled() -> None:
    def fake_graph_llm(prompt: str) -> str:
        assert "Topology sketch" not in prompt
        return _MOCK_LLM_JSON

    current = {
        "nodes": [{"id": "a1", "type": "initial"}],
        "edges": [],
    }

    bundle = debug_model_activity(
        "Extend the process",
        current_model=current,
        instruction="Add steps",
        llm_caller=fake_graph_llm,
        sketch_llm_caller=lambda prompt: pytest.fail("Sketch caller should not run during refinement"),
        use_sketch=True,
    )

    assert "sketch" not in bundle


def test_baseline_prompt_is_positioned_as_graph_realizer() -> None:
    prompt = build_activity_prompt(
        process_text="Submit order then process it",
        activity_sketch={
            "main_flow": ["submit order", "process order"],
            "control_blocks": [],
        },
    )

    assert "Use the topology plan as authoritative" in prompt
    assert "Do not redesign the control flow" in prompt
    assert "Your task is to realize the topology into valid graph JSON" in prompt
    assert "Do not add a merge node merely because one branch loops back to an earlier action" in prompt
    assert "Modeling Procedure" not in prompt
    assert "Decision Structure" not in prompt
    assert "Parallel Structure" not in prompt
    assert "Loop Structure" not in prompt


def test_extract_clean_model_from_wrapped_ai4mde_export() -> None:
    from llm.converter import convert_to_ai4mde
    from llm.refinement_generator import _get_clean_model

    clean = json.loads(_MOCK_LLM_JSON)
    export = convert_to_ai4mde(
        clean_model=clean,
        system_id=str(uuid.uuid4()),
        diagram_id=str(uuid.uuid4()),
        name="Wrapped",
        description="",
        project_id=str(uuid.uuid4()),
    )

    extracted = _get_clean_model(export)

    assert len(extracted["nodes"]) == 3
    assert extracted["nodes"][1]["name"] == "Do work"
    assert extracted["edges"][0]["source"] == "n1"
    assert extracted["edges"][0]["target"] == "n2"


def test_model_activity_debug_true_matches_debug_model_activity() -> None:
    a = model_activity(
        "x",
        llm_caller=_fake_llm_returns_valid_graph,
        debug=True,
    )
    b = debug_model_activity("x", llm_caller=_fake_llm_returns_valid_graph)
    assert a["prompt"] == b["prompt"]
    assert a["raw_response"] == b["raw_response"]
    assert a["parsed"] == b["parsed"]


def test_parse_rejects_invalid_json() -> None:
    from llm.refinement_generator import _parse_and_validate_activity_graph_json

    with pytest.raises(ValueError, match="not valid JSON"):
        _parse_and_validate_activity_graph_json("not json")


def test_parse_normalizes_action_label_and_legacy_edge_type() -> None:
    from llm.refinement_generator import _parse_and_validate_activity_graph_json

    parsed = _parse_and_validate_activity_graph_json(
        json.dumps(
            {
                "nodes": [
                    {"id": "n1", "type": "INITIAL"},
                    {"id": "n2", "type": "Action", "label": "Do work"},
                    {"id": "n3", "type": "FINAL"},
                ],
                "edges": [
                    {"source": "n1", "target": "n2", "type": "control_flow"},
                    {"source": "n2", "target": "n3", "type": "controlflow"},
                ],
            }
        )
    )

    assert parsed["nodes"][0]["type"] == "initial"
    assert parsed["nodes"][1]["type"] == "action"
    assert parsed["nodes"][1]["name"] == "Do work"
    assert parsed["edges"][0]["type"] == "control"
    assert parsed["edges"][1]["type"] == "control"


def test_parse_normalizes_text_aliases_without_repairing_semantics() -> None:
    from llm.refinement_generator import _parse_and_validate_activity_graph_json

    parsed = _parse_and_validate_activity_graph_json(
        json.dumps(
            {
                "nodes": [
                    {"id": "n1", "type": "start"},
                    {"id": "n2", "type": "task", "title": "Review order"},
                    {"id": "n3", "type": "end"},
                ],
                "edges": [
                    {"source": "n1", "target": "n2", "branch": "yes"},
                    {"source": "n2", "target": "n3", "condition": "approved"},
                ],
            }
        )
    )

    assert parsed["nodes"][1]["type"] == "action"
    assert parsed["nodes"][1]["name"] == "Review order"
    assert parsed["edges"][0]["label"] == "yes"
    assert parsed["edges"][1]["condition"] == "approved"
    assert "label" not in parsed["edges"][1]


def test_parse_accepts_nullable_required_fields_and_drops_none_on_dump() -> None:
    from llm.refinement_generator import _parse_and_validate_activity_graph_json

    parsed = _parse_and_validate_activity_graph_json(
        json.dumps(
            {
                "nodes": [
                    {
                        "id": "n1",
                        "type": "initial",
                        "name": None,
                        "label": None,
                        "partition": None,
                    },
                    {
                        "id": "n2",
                        "type": "action",
                        "name": "Validate order",
                        "label": None,
                        "partition": None,
                    },
                    {
                        "id": "n3",
                        "type": "final",
                        "name": None,
                        "label": None,
                        "partition": None,
                    },
                ],
                "edges": [
                    {
                        "source": "n1",
                        "target": "n2",
                        "type": "control",
                        "label": None,
                        "condition": None,
                    },
                    {
                        "source": "n2",
                        "target": "n3",
                        "type": "control",
                        "label": None,
                        "condition": None,
                    },
                ],
            }
        )
    )

    assert parsed["nodes"][0] == {"id": "n1", "type": "initial"}
    assert parsed["nodes"][1]["name"] == "Validate order"
    assert parsed["edges"][0] == {"source": "n1", "target": "n2", "type": "control"}


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="Set OPENAI_API_KEY to run live LLM test (no import).",
)
def test_baseline_live_openai_clean_graph_only() -> None:
    graph = model_activity("User pays invoice; system sends receipt.")
    assert isinstance(graph.get("nodes"), list) and len(graph["nodes"]) >= 1
    assert isinstance(graph.get("edges"), list)


@pytest.mark.skipif(
    not os.environ.get("RUN_BASELINE_IMPORT_INTEGRATION"),
    reason="Set RUN_BASELINE_IMPORT_INTEGRATION=1 to run DB import integration.",
)
def test_baseline_import_integration() -> None:
    from llm.baseline_generator import generate_activity_model
    from llm.converter import convert_to_ai4mde

    setup_django()

    project = create_test_project()
    project_id = str(project.id)

    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    clean = generate_activity_model(BASELINE_PROCESS_TEXT)
    assert clean is not None

    systems_export = convert_to_ai4mde(
        clean_model=clean,
        system_id=str(uuid.uuid4()),
        diagram_id=str(uuid.uuid4()),
        name="BaselineAutomation",
        description="import_integration test",
        project_id=project_id,
    )
    assert isinstance(systems_export, list) and len(systems_export) == 1
    _, imported = import_and_validate_system(project, systems_export)

    out_path = out_dir / "baseline_output.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(systems_export, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {out_path.name}; import OK for system {imported.id}")
