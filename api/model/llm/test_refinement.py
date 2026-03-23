# Manual / integration-style tests call the real LLM (see tests marked below).
# Fast check: prompt rendering only (no API key required).
#
# Run real LLM refinement tests (from api/model, with OPENAI_API_KEY):
#   pytest llm/test_refinement.py -v -s -k "manual_"
#
# Outputs: llm/integration_debug_output/refinement_*.json, candidate_*_clean/ai4mde.json

import json
import os
import sys
import types
import uuid
from pathlib import Path

import pytest

MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))


def _install_llm_dependency_stubs() -> None:
    """So importing ``llm.refinement_generator`` works without SDK packages (unit tests)."""
    if "openai" not in sys.modules:
        openai_stub = types.ModuleType("openai")

        class OpenAI:  # pragma: no cover
            def __init__(self, *args, **kwargs):
                self.chat = types.SimpleNamespace(completions=None)

        openai_stub.OpenAI = OpenAI
        sys.modules["openai"] = openai_stub
    if "groq" not in sys.modules:
        groq_stub = types.ModuleType("groq")

        class Groq:  # pragma: no cover
            def __init__(self, *args, **kwargs):
                self.chat = types.SimpleNamespace(completions=None)

        groq_stub.Groq = Groq
        sys.modules["groq"] = groq_stub


_install_llm_dependency_stubs()

from llm.prompt_builder import build_activity_prompt


def test_generate_candidates_with_conversion_structure(monkeypatch) -> None:
    """No LLM: ensure wrapper pairs each clean graph with AI4MDE and distinct system ids."""
    import llm.refinement_generator as refinement_generator

    def fake_initial(process_text: str, n: int = 3):
        assert process_text == "stub process"
        return [
            {"nodes": [{"id": f"n{i}", "type": "initial"}], "edges": []}
            for i in range(n)
        ]

    monkeypatch.setattr(
        refinement_generator,
        "generate_initial_candidates",
        fake_initial,
    )

    pairs = refinement_generator.generate_candidates_with_conversion(
        "stub process", n=3
    )
    assert len(pairs) == 3
    ids = set()
    for p in pairs:
        assert set(p.keys()) == {"clean", "ai4mde"}
        assert "nodes" in p["clean"] and "edges" in p["clean"]
        a = p["ai4mde"]
        assert a["diagrams"][0]["type"] == "activity"
        ids.add(str(a["id"]))
    assert len(ids) == 3


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


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set; skip real LLM refinement tests",
)
def test_manual_candidates_with_conversion() -> None:
    """Real LLM: ``generate_candidates_with_conversion`` — all clean + AI4MDE before selection."""
    pytest.importorskip("openai")
    pytest.importorskip("groq")

    from llm.refinement_generator import generate_candidates_with_conversion

    process_text = "Receive order, process order, send confirmation"
    pairs = generate_candidates_with_conversion(
        process_text,
        n=3,
        name_prefix="Integration candidate",
    )

    assert len(pairs) == 3
    system_ids = set()
    for p in pairs:
        assert "clean" in p and "ai4mde" in p
        clean = p["clean"]
        ai4mde = p["ai4mde"]
        assert "nodes" in clean and isinstance(clean["nodes"], list)
        assert "edges" in clean and isinstance(clean["edges"], list)
        assert "diagrams" in ai4mde
        assert len(ai4mde["diagrams"]) == 1
        assert ai4mde["diagrams"][0].get("type") == "activity"
        sid = ai4mde.get("id")
        assert sid
        system_ids.add(str(sid))
    assert len(system_ids) == 3, "each candidate should have a distinct system id"

    out_dir = Path(__file__).resolve().parent / "integration_debug_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, p in enumerate(pairs, start=1):
        clean_path = out_dir / f"candidate_{i}_clean.json"
        ai_path = out_dir / f"candidate_{i}_ai4mde.json"
        print(f"\n=== candidate_{i}_clean.json ===")
        print(json.dumps(p["clean"], indent=2))
        print(f"\n=== candidate_{i}_ai4mde.json (summary) ===")
        print("system id:", p["ai4mde"].get("id"))
        with clean_path.open("w", encoding="utf-8") as f:
            json.dump(p["clean"], f, indent=2, ensure_ascii=False)
        with ai_path.open("w", encoding="utf-8") as f:
            json.dump(p["ai4mde"], f, indent=2, ensure_ascii=False)


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set; skip real LLM refinement tests",
)
def test_manual_refinement_end_to_end() -> None:
    """Real LLM: generate → AI4MDE → refine_activity_model → save for import debugging."""
    pytest.importorskip("openai")
    pytest.importorskip("groq")

    from llm.baseline_generator import generate_activity_model
    from llm.converter import convert_to_ai4mde
    from llm.refinement_generator import refine_activity_model

    process_text = (
        "A customer places an order. The system validates payment and ships the order."
    )
    clean = generate_activity_model(process_text)
    initial_ai4mde = convert_to_ai4mde(
        clean,
        system_id=str(uuid.uuid4()),
        diagram_id=str(uuid.uuid4()),
        name="RefinementIntegrationInitial",
        description="Before refinement",
    )
    instruction = "Add an explicit step to send an order confirmation email after payment validation."

    refined = refine_activity_model(
        process_text=process_text,
        current_model=initial_ai4mde,
        refinement_instruction=instruction,
    )

    assert isinstance(refined, dict)
    assert "diagrams" in refined
    assert len(refined.get("diagrams", [])) == 1
    assert refined["diagrams"][0].get("type") == "activity"

    out_dir = Path(__file__).resolve().parent / "integration_debug_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "refinement_initial_ai4mde.json").open("w", encoding="utf-8") as f:
        json.dump(initial_ai4mde, f, indent=2, ensure_ascii=False)
    with (out_dir / "refinement_refined_ai4mde.json").open("w", encoding="utf-8") as f:
        json.dump(refined, f, indent=2, ensure_ascii=False)

    print("\n=== refinement_initial_ai4mde.json / refinement_refined_ai4mde.json written ===")
    print(json.dumps(refined, indent=2)[:2000] + ("..." if len(json.dumps(refined)) > 2000 else ""))
