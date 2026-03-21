"""
AI-assisted multi-candidate generation: repeated ``model_activity`` calls.

Not part of the baseline condition — this is an optional usage pattern for the
AI-assisted condition (e.g. present N candidates for human selection).
"""
from typing import List

from .refinement_generator import model_activity


def generate_multiple_models(process_text: str, num_models: int = 3) -> List[dict]:
    """
    Produce several independent candidate models for the same process description.

    Each candidate is one clean ``{"nodes": [...], "edges": [...]}`` graph from a
    separate ``model_activity`` call (no batching; ``model_activity`` always
    returns exactly one dict).
    """
    if num_models <= 0:
        return []

    models: List[dict] = []
    for _ in range(num_models):
        model = model_activity(process_text=process_text)
        models.append(model)
    return models
