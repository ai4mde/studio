# Refinement-mode automation (real OpenAI).
#
# Pipeline: generate N clean candidates → convert to AI4MDE → import each candidate.
#
# Run from ``api/`` (requires OPENAI_API_KEY):
#   poetry run pytest model/llm/test_refinement.py -s -k refinement
#
# Writes under ``llm/outputs/``:
#   candidate_{1..N}_clean.json       — raw LLM graph (nodes/edges)
#   candidate_{1..N}_ai4mde.json      — candidates in AI4MDE form

import json
import os
import sys
import uuid
from pathlib import Path

import pytest

MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from llm._test_helpers import create_test_project, import_and_validate_system
from llm.converter import convert_to_ai4mde
from llm.refinement_generator import generate_initial_candidates

PROCESS_TEXT = (
    "Receive order, process order, send confirmation. "
    "User logs in, system verifies credentials, dashboard is shown. "
    "Customer places order, payment is processed, receipt is sent."
)

NUM_CANDIDATES = 3


def test_run_refinement_automation() -> None:
    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    project = create_test_project()
    project_id = str(project.id)

    # Refinement mode in the experiment API generates three initial candidates.
    candidates = generate_initial_candidates(PROCESS_TEXT, n=NUM_CANDIDATES)
    assert len(candidates) == NUM_CANDIDATES

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
            project_id=project_id,
        )
        _, imported = import_and_validate_system(project, ai4mde)

        ai4mde_path = out_dir / f"candidate_{i}_ai4mde.json"
        with ai4mde_path.open("w", encoding="utf-8") as f:
            json.dump(ai4mde, f, indent=2, ensure_ascii=False)

        preview = json.dumps(ai4mde, indent=2, ensure_ascii=False)
        print(f"\n=== candidate {i} (clean: {clean_path.name}, AI4MDE: {ai4mde_path.name}) ===\n")
        print(preview[:4000] + ("" if len(preview) <= 4000 else "\n... [truncated; full JSON in file] ...\n"))
        print("\n=== import result ===\n")
        print(f"candidate_index: {i}")
        print(f"project_id: {project_id}")
        print(f"system_id: {imported.id}")
        print(f"system_name: {imported.name}")
        print(f"diagrams: {imported.diagrams.count()}")
        print(f"classifiers: {imported.classifiers.count()}")
        print(f"relations: {imported.relations.count()}")
        print("import_status: success")
