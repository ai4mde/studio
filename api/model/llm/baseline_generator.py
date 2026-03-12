import json

from .handler import call_openai


# Clean activity diagram schema (structure only) for the LLM.
EMPTY_JSON_SCHEMA = {
    "nodes": [],
    "edges": [],
}


PROMPT_TEMPLATE = (
    "You are helping a business analyst describe a process as a UML Activity Diagram.\n"
    "\n"
    "Your job is to read the process description and build a simple activity graph:\n"
    "- Identify the main steps and represent them as action nodes.\n"
    "- Add decision points wherever the text describes choices or conditional branches.\n"
    "- Use parallel branches when the description clearly mentions tasks happening at the same time.\n"
    "- Make sure there is a clear starting point and at least one clear end point.\n"
    "\n"
    "Process description:\n"
    "{process_text}\n"
    "\n"
    "You must return a single JSON object that represents ONLY this clean activity graph.\n"
    "Use this overall structure (structure only, no real data):\n"
    "{empty_schema}\n"
    "\n"
    "Modeling rules:\n"
    "- The top-level object has two arrays: \"nodes\" and \"edges\".\n"
    "- Each node has at least: \"id\" (string) and \"type\" (string).\n"
    "- Use simple node ids like \"n1\", \"n2\", \"n3\" (do NOT use UUIDs).\n"
    "- Allowed node types are: initial, action, decision, merge, fork, join, final, object.\n"
    "- For every action node (type \"action\"), include a human-readable \"name\" field.\n"
    "- Each edge object has at least: \"source\" (node id) and \"target\" (node id).\n"
    "- You MAY optionally add \"type\" (e.g. \"controlflow\" or \"objectflow\") "
    "and \"condition\" (string) for edges, but they are not required.\n"
    "\n"
    "Output rules (strict):\n"
    "- Output ONLY a single valid JSON object.\n"
    "- Do NOT include any explanations, prose, or reasoning.\n"
    "- Do NOT include markdown, code fences, or comments.\n"
    "- Do NOT include any text before or after the JSON.\n"
)


def generate_activity_model(process_text: str) -> dict:
    """
    Call the LLM to generate a clean activity graph JSON structure.
    """
    prompt = PROMPT_TEMPLATE.format(
        process_text=process_text,
        empty_schema=json.dumps(EMPTY_JSON_SCHEMA, indent=2),
    )

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


def export_activity_model(model: dict) -> None:
    """
    Pretty-print an activity model (clean or AI4MDE) and save it to a JSON file
    in the current working directory.
    """
    print(json.dumps(model, indent=2))

    with open("activity_model.json", "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2, ensure_ascii=False)
