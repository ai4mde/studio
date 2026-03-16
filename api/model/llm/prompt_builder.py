import json
from typing import Any, Dict, Optional


EMPTY_JSON_SCHEMA: Dict[str, Any] = {
    "nodes": [],
    "edges": [],
}


BASE_SCHEMA_AND_RULES = """
You must return a single JSON object that represents ONLY this clean activity graph.
Use this overall structure (structure only, no real data):
{empty_schema}

Modeling rules:
- The top-level object has two arrays: "nodes" and "edges".
- Each node has at least: "id" (string) and "type" (string).
- Use simple node ids like "n1", "n2", "n3" (do NOT use UUIDs).
- Allowed node types are: initial, action, decision, merge, fork, join, final, object.
- For every action node (type "action"), include a human-readable "name" field.
- Each edge object has at least: "source" (node id) and "target" (node id).
- You MAY optionally add "type" (e.g. "controlflow" or "objectflow") and "condition" (string) for edges, but they are not required.

Output rules (strict):
- Output ONLY a single valid JSON object.
- Do NOT include any explanations, prose, or reasoning.
- Do NOT include markdown, code fences, or comments.
- Do NOT include any text before or after the JSON.
""".strip()


def build_activity_prompt(
    process_text: str,
    current_model: Optional[Dict[str, Any]] = None,
    refinement_instruction: Optional[str] = None,
) -> str:
    """
    Build a unified activity-modelling prompt.

    If current_model and refinement_instruction are both empty/None, the LLM
    is asked to generate a new model from scratch from the process description.

    If a current_model is provided (clean {nodes, edges}) and a refinement
    instruction is given, the LLM is asked to refine/update the existing model.
    """
    empty_schema_str = json.dumps(EMPTY_JSON_SCHEMA, indent=2)

    # Initial generation mode
    if not current_model and not refinement_instruction:
        header = (
            "You are helping a business analyst describe a process as a UML Activity Diagram.\n\n"
            "Your job is to read the process description and build a simple activity graph:\n"
            "- Identify the main steps and represent them as action nodes.\n"
            "- Add decision points wherever the text describes choices or conditional branches.\n"
            "- Use parallel branches when the description clearly mentions tasks happening at the same time.\n"
            "- Make sure there is a clear starting point and at least one clear end point.\n\n"
            f"Process description:\n{process_text}\n\n"
        )
        body = BASE_SCHEMA_AND_RULES.format(empty_schema=empty_schema_str)
        return header + body + "\n"

    # Refinement / update mode
    # Ensure we always pass a serializable clean model here.
    current_model_json = json.dumps(
        current_model or EMPTY_JSON_SCHEMA, indent=2)
    instruction_text = refinement_instruction or "Update and improve the model as needed."

    header = (
        "You are helping a business analyst refine a UML Activity Diagram.\n\n"
        "You have:\n"
        "1. The original process description.\n"
        "2. The current activity model (as a JSON graph).\n"
        "3. A refinement instruction from the designer.\n\n"
        "Your job is to apply the refinement instruction to the current model and produce an UPDATED "
        "activity graph. Return only the updated graph—add, remove, or modify nodes and edges as requested.\n\n"
        f"Original process description:\n{process_text}\n\n"
        f"Current activity model (JSON):\n{current_model_json}\n\n"
        f"Refinement instruction:\n{instruction_text}\n\n"
    )

    body = BASE_SCHEMA_AND_RULES.format(empty_schema=empty_schema_str)
    return header + body + "\n"
