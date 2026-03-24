# Baseline automation: real OpenAI via ``generate_activity_model`` (no mocks).
#
# Run from ``api/`` (requires OPENAI_API_KEY):
#   poetry run pytest model/llm/test_baseline.py -s -k baseline
#
# Writes AI4MDE JSON under ``llm/outputs/baseline.json`` (importable by the product).

import json
import sys
import uuid
from pathlib import Path

import pytest  # type: ignore[import-untyped]

MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from llm.baseline_generator import generate_activity_model
from llm.converter import convert_to_ai4mde

# One combined process description (previously three redundant cases).
BASELINE_PROCESS_TEXT = (
    "Receive order, process order, send confirmation. "
    "User logs in, system verifies credentials, dashboard is shown. "
    "Customer places order, payment is processed, receipt is sent."
)


def test_run_baseline_automation() -> None:
    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    clean = generate_activity_model(BASELINE_PROCESS_TEXT)
    assert clean is not None

    ai4mde = convert_to_ai4mde(
        clean_model=clean,
        system_id=str(uuid.uuid4()),
        diagram_id=str(uuid.uuid4()),
        name="BaselineAutomation",
        description="From test_run_baseline_automation",
    )

    print("\n=== clean graph (LLM) ===\n")
    print(json.dumps(clean, indent=2, ensure_ascii=False))
    text = json.dumps(ai4mde, indent=2, ensure_ascii=False)
    print(f"\n=== AI4MDE (saved to outputs/baseline.json) ===\n{text[:4000]}")
    if len(text) > 4000:
        print("\n... [truncated in log; full JSON in file] ...\n")

    out_path = out_dir / "baseline.json"
    with out_path.open("w", encoding="utf-8") as f:
        f.write(text)
