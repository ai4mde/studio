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
