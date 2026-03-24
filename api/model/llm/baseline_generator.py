"""
Baseline activity generation (single-shot).

Overview
--------
This module provides a minimal generation pipeline that produces a single activity model per request using `model_activity`.

It is used for baseline experimental settings:
- one model only
- no multi-candidate generation
- no refinement loop

For multiple options before selection, call
``refinement_generator.generate_initial_candidates`` (N repeated
``model_activity`` calls — not a separate generator module).
"""
import json

from .refinement_generator import model_activity


def generate_activity_model(process_text: str) -> dict:
    """
    Generate one clean activity diagram from natural-language process text.

    Parameters
    ----------
    process_text : str
        Natural language description of the process.

    Returns
    -------
    dict
        A validated activity diagram with nodes and edges.
        ``model_activity`` (prompt → LLM → validate).
    """
    return model_activity(process_text=process_text)


def export_activity_model(model: dict) -> None:
    """
    Export an activity model to a JSON file.

    Pretty-prints the model (clean or AI4MDE format) and saves it as `activity_model.json` in the current working directory.
    """
    print(json.dumps(model, indent=2))

    with open("activity_model.json", "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2, ensure_ascii=False)
