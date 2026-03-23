# Manual / integration-style tests call the real LLM (see tests marked below).
# Fast checks: prompt rendering only (no API key required).
#
# Run real LLM baseline test (from api/model, with OPENAI_API_KEY):
#   pytest llm/test_baseline.py -v -s -k manual_baseline
#
# Outputs: llm/integration_debug_output/baseline_*.json

import json
import os
import sys
import uuid
from pathlib import Path

import pytest

MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

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


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set; skip real LLM baseline test",
)
def test_manual_baseline_generate_and_export() -> None:
    """Real LLM: single baseline model + optional AI4MDE export for import debugging."""
    pytest.importorskip("openai")
    pytest.importorskip("groq")

    from llm.baseline_generator import generate_activity_model
    from llm.converter import convert_to_ai4mde

    process_text = "Receive order, process order, send confirmation"
    clean = generate_activity_model(process_text)

    assert "nodes" in clean and isinstance(clean["nodes"], list)
    assert "edges" in clean and isinstance(clean["edges"], list)

    out_dir = Path(__file__).resolve().parent / "integration_debug_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    clean_path = out_dir / "baseline_clean_model.json"
    print("\n=== baseline_clean_model.json ===")
    print(json.dumps(clean, indent=2))
    with clean_path.open("w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2, ensure_ascii=False)

    ai4mde = convert_to_ai4mde(
        clean,
        system_id=str(uuid.uuid4()),
        diagram_id=str(uuid.uuid4()),
        name="BaselineIntegrationTest",
        description="From test_manual_baseline_generate_and_export",
    )
    ai_path = out_dir / "baseline_ai4mde_model.json"
    with ai_path.open("w", encoding="utf-8") as f:
        json.dump(ai4mde, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {ai_path}")
