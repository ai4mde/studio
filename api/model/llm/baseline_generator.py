"""
Baseline (single-shot) activity generation: one call to ``model_activity`` per request.

Used for the baseline experimental condition: one model only, no multi-candidate
and no LLM refinement loop here — multi-candidate lives in ``multi_generator``.
"""
import json

from .refinement_generator import model_activity


def generate_activity_model(process_text: str) -> dict:
    """
    Generate one clean activity graph from natural-language process text.

    Delegates to the unified core ``model_activity`` (prompt → LLM → validate).
    """
    return model_activity(process_text=process_text)


def export_activity_model(model: dict) -> None:
    """
    Pretty-print an activity model (clean or AI4MDE) and save it to a JSON file
    in the current working directory.
    """
    print(json.dumps(model, indent=2))

    with open("activity_model.json", "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2, ensure_ascii=False)
