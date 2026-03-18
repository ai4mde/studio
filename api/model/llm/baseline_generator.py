import json
from typing import List

from .handler import call_openai
from .prompt_builder import build_activity_prompt


def generate_activity_model(process_text: str) -> dict:
    """
    Call the LLM to generate a clean activity graph JSON structure.
    """
    # Use unified activity prompt in "initial generation" mode
    prompt = build_activity_prompt(process_text=process_text)

    raw_output = call_openai("gpt-4o-mini", prompt)

    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        raise Exception("LLM output is not valid JSON.")

    # Basic structural validation of the clean graph.
    if not isinstance(parsed, dict) or "nodes" not in parsed or "edges" not in parsed:
        raise Exception("LLM output does not follow required schema.")
    if not isinstance(parsed.get("nodes"), list) or not isinstance(parsed.get("edges"), list):
        raise Exception("LLM output does not follow required schema.")

    for node in parsed["nodes"]:
        if not isinstance(node, dict):
            raise Exception("LLM output does not follow required schema.")
        if "id" not in node or "type" not in node:
            raise Exception("LLM output does not follow required schema.")
        if node.get("type") == "action" and "name" not in node:
            raise Exception("LLM output does not follow required schema.")

    for edge in parsed["edges"]:
        if not isinstance(edge, dict):
            raise Exception("LLM output does not follow required schema.")
        if "source" not in edge or "target" not in edge:
            raise Exception("LLM output does not follow required schema.")

    return parsed


def generate_multiple_models(process_text: str, n: int = 3) -> List[dict]:
    """
    Generate up to ``n`` independent candidate activity models for the same process description.

    Each candidate is a clean activity graph in ``{"nodes": [...], "edges": [...]}`` form,
    produced by a separate call to ``generate_activity_model``.
    """
    if n <= 0:
        return []

    candidates: List[dict] = []
    for _ in range(n):
        candidates.append(generate_activity_model(process_text))
    return candidates


def export_activity_model(model: dict) -> None:
    """
    Pretty-print an activity model (clean or AI4MDE) and save it to a JSON file
    in the current working directory.
    """
    print(json.dumps(model, indent=2))

    with open("activity_model.json", "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2, ensure_ascii=False)
