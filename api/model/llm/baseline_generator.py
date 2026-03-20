import json
from typing import List

from .refinement_generator import model_activity


def generate_activity_model(process_text: str) -> dict:
    """
    Generate one clean activity graph from natural-language process text.

    Delegates to the unified core ``model_activity`` (prompt → LLM → validate).
    """
    return model_activity(process_text=process_text)


def generate_multiple_models(process_text: str, num_models: int = 3) -> List[dict]:
    """
    Produce several independent candidate models for the same process description.

    Each candidate is one clean ``{"nodes": [...], "edges": [...]}`` graph from a
    separate ``model_activity`` call (no batching).
    """
    if num_models <= 0:
        return []

    models: List[dict] = []
    for _ in range(num_models):
        model = model_activity(process_text=process_text)
        models.append(model)
    return models


def export_activity_model(model: dict) -> None:
    """
    Pretty-print an activity model (clean or AI4MDE) and save it to a JSON file
    in the current working directory.
    """
    print(json.dumps(model, indent=2))

    with open("activity_model.json", "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2, ensure_ascii=False)
