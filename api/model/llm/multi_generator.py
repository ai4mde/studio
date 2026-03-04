from typing import List, Dict, Any

from .baseline_generator import generate_activity_model


def generate_multiple_models(process_text: str, n: int = 3) -> List[Dict[str, Any]]:
    """
    Generate multiple independent activity models from the same process text.
    """
    models: List[Dict[str, Any]] = []
    for _ in range(n):
        models.append(generate_activity_model(process_text))
    return models

