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

from llm import baseline_generator
from llm.prompt_builder import build_activity_prompt


def test_build_activity_prompt_generation_mode() -> None:
    process_text = "Customer places an order."
    prompt = build_activity_prompt(process_text=process_text)

    assert "describe a process as a UML Activity Diagram" in prompt
    assert "Process description:" in prompt
    assert process_text in prompt
    assert "Current activity model (JSON):" not in prompt
    assert "Refinement instruction:" not in prompt
    assert "Output ONLY a single valid JSON object." in prompt


def test_generate_activity_model_calls_model_activity(monkeypatch) -> None:
    expected = {
        "nodes": [{"id": "n1", "type": "initial"}],
        "edges": [],
    }
    captured = {}

    def fake_model_activity(process_text: str, current_model=None, instruction=None):
        captured["process_text"] = process_text
        captured["current_model"] = current_model
        captured["instruction"] = instruction
        return expected

    monkeypatch.setattr(baseline_generator, "model_activity", fake_model_activity)

    result = baseline_generator.generate_activity_model("Order process text")

    assert result == expected
    assert isinstance(result.get("nodes"), list)
    assert isinstance(result.get("edges"), list)
    assert captured == {
        "process_text": "Order process text",
        "current_model": None,
        "instruction": None,
    }
