import sys
import types
from pathlib import Path

MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))


def _install_llm_dependency_stubs() -> None:
    """Allow importing llm modules in test envs without SDK deps installed."""
    if "openai" not in sys.modules:
        openai_stub = types.ModuleType("openai")

        class OpenAI:  # pragma: no cover - import shim only
            def __init__(self, *args, **kwargs):
                self.chat = types.SimpleNamespace(completions=None)

        openai_stub.OpenAI = OpenAI
        sys.modules["openai"] = openai_stub

    if "groq" not in sys.modules:
        groq_stub = types.ModuleType("groq")

        class Groq:  # pragma: no cover - import shim only
            def __init__(self, *args, **kwargs):
                self.chat = types.SimpleNamespace(completions=None)

        groq_stub.Groq = Groq
        sys.modules["groq"] = groq_stub


_install_llm_dependency_stubs()

from llm.prompt_builder import build_activity_prompt
from llm.refinement_generator import refine_activity_model
import llm.refinement_generator as refinement_generator


def test_build_activity_prompt_refinement_mode() -> None:
    process_text = "Customer places an order."
    current_model = {
        "nodes": [{"id": "n1", "type": "initial"}],
        "edges": [],
    }
    refinement_instruction = "Add payment validation before confirmation."

    prompt = build_activity_prompt(
        process_text=process_text,
        current_model=current_model,
        refinement_instruction=refinement_instruction,
    )

    assert "refine a UML Activity Diagram" in prompt
    assert "Original process description:" in prompt
    assert process_text in prompt
    assert "Current activity model (JSON):" in prompt
    assert "\"id\": \"n1\"" in prompt
    assert "Refinement instruction:" in prompt
    assert refinement_instruction in prompt
    assert "Output ONLY a single valid JSON object." in prompt


def test_refine_activity_model_returns_ai4mde_from_clean_input(monkeypatch) -> None:
    captured = {}
    clean_output = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "Validate payment"},
            {"id": "n3", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
        ],
    }

    def fake_model_activity(process_text: str, current_model=None, instruction=None):
        captured["process_text"] = process_text
        captured["current_model"] = current_model
        captured["instruction"] = instruction
        return clean_output

    monkeypatch.setattr(refinement_generator, "model_activity", fake_model_activity)

    current_model = {
        "nodes": [{"id": "n1", "type": "initial"}],
        "edges": [],
    }
    result = refine_activity_model(
        process_text="Order processing",
        current_model=current_model,
        refinement_instruction="Add payment validation",
    )

    assert captured["process_text"] == "Order processing"
    assert captured["current_model"] == current_model
    assert captured["instruction"] == "Add payment validation"

    # AI4MDE top-level structure
    assert isinstance(result, dict)
    assert "interfaces" in result
    assert "diagrams" in result
    assert isinstance(result["diagrams"], list)
    assert len(result["diagrams"]) == 1
    assert result["diagrams"][0]["type"] == "activity"

    # When current_model is already clean, defaults are used.
    assert result["id"] == "System"
    assert result["diagrams"][0]["id"] == "diagram1"
