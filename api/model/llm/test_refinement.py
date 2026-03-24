# Human-in-the-loop refinement automation (real OpenAI).
#
# Pipeline: generate N clean candidates → save all → pick one (hardcoded) → refine once.
#
# Run from ``api/`` (requires OPENAI_API_KEY):
#   poetry run pytest model/llm/test_refinement.py -s -k refinement
#
# Writes under ``llm/outputs/``:
#   candidate_{1..N}_clean.json    — raw LLM graph (nodes/edges)
#   candidate_{1..N}_ai4mde.json   — same candidates in AI4MDE form (import in product UI)
#   refined.json                 — single AI4MDE output after one refinement

import json
import sys
import uuid
from pathlib import Path

import pytest  # type: ignore[import-untyped]

MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from llm.converter import convert_to_ai4mde
from llm.refinement_generator import generate_initial_candidates, refine_activity_model

PROCESS_TEXT = (
    "Receive order, process order, send confirmation. "
    "User logs in, system verifies credentials, dashboard is shown. "
    "Customer places order, payment is processed, receipt is sent."
)

NUM_CANDIDATES = 3

# Simulated human choice: 1-based index into the candidate list.
SELECTED_CANDIDATE_INDEX = 1

REFINEMENT_INSTRUCTION = "Make the process more detailed"


def test_run_refinement_automation() -> None:
    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) N× generation only — repeated ``model_activity``; no refinement.
    candidates = generate_initial_candidates(PROCESS_TEXT, n=NUM_CANDIDATES)
    assert len(candidates) == NUM_CANDIDATES

    candidate_ai4mde: list[dict] = []
    for i, clean in enumerate(candidates, start=1):
        assert clean is not None

        clean_path = out_dir / f"candidate_{i}_clean.json"
        with clean_path.open("w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2, ensure_ascii=False)

        ai4mde = convert_to_ai4mde(
            clean_model=clean,
            system_id=str(uuid.uuid4()),
            diagram_id=str(uuid.uuid4()),
            name=f"Refinement candidate {i}",
            description=f"Generated candidate {i} for interactive selection (test_refinement).",
        )
        candidate_ai4mde.append(ai4mde)

        ai4mde_path = out_dir / f"candidate_{i}_ai4mde.json"
        with ai4mde_path.open("w", encoding="utf-8") as f:
            json.dump(ai4mde, f, indent=2, ensure_ascii=False)

        preview = json.dumps(ai4mde, indent=2, ensure_ascii=False)
        print(f"\n=== candidate {i} (clean: {clean_path.name}, AI4MDE: {ai4mde_path.name}) ===\n")
        print(preview[:4000] + ("" if len(preview) <= 4000 else "\n... [truncated; full JSON in file] ...\n"))

    # 2) Human-in-the-loop: one selected model (hardcoded index). Refine using AI4MDE
    #    so system/diagram ids stay aligned with the saved candidate file.
    assert 1 <= SELECTED_CANDIDATE_INDEX <= len(candidates)
    selected_ai4mde = candidate_ai4mde[SELECTED_CANDIDATE_INDEX - 1]

    # 3) Refinement only once — refinement_generator.
    refined = refine_activity_model(
        process_text=PROCESS_TEXT,
        current_model=selected_ai4mde,
        refinement_instruction=REFINEMENT_INSTRUCTION,
    )
    assert refined is not None

    refined_path = out_dir / "refined.json"
    with refined_path.open("w", encoding="utf-8") as f:
        json.dump(refined, f, indent=2, ensure_ascii=False)

    text = json.dumps(refined, indent=2, ensure_ascii=False)
    print(f"\n=== refined (selected candidate {SELECTED_CANDIDATE_INDEX}, saved {refined_path.name}) ===\n{text}\n")
