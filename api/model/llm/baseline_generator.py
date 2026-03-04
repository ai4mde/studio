import json

from .handler import call_openai


# Empty AI4MDE import schema (structure only). Derived from AI4MDE export format.
# No instance data—used so the LLM outputs import-compatible JSON.
EMPTY_JSON_SCHEMA = {
    "interfaces": [],
    "diagrams": [
        {
            "nodes": [
                {
                    "cls_data": {
                        "id": "",
                        "project": "",
                        "system": "",
                        "data": {
                            "role": "",
                            "type": "",
                            "activity_scope": "",
                            "name": "",
                            "body": "",
                            "localPrecondition": "",
                            "localPostcondition": ""
                        }
                    },
                    "id": "",
                    "diagram": "",
                    "cls": "",
                    "data": {"position": {"x": 0, "y": 0}}
                }
            ],
            "edges": [
                {
                    "rel_data": {
                        "id": "",
                        "data": {
                            "type": "controlflow",
                            "guard": "",
                            "weight": "",
                            "condition": None,
                            "is_directed": True,
                            "position_handlers": []
                        },
                        "system": "",
                        "source": "",
                        "target": ""
                    },
                    "id": "",
                    "diagram": "",
                    "rel": "",
                    "data": {}
                }
            ],
            "id": "",
            "type": "activity",
            "name": "",
            "description": "",
            "system": ""
        }
    ],
    "id": "",
    "name": "",
    "description": ""
}


PROMPT_TEMPLATE = (
    "You are helping a business analyst capture a process as a UML Activity Diagram in a format "
    "that can be imported into an AI4MDE system.\n"
    "\n"
    "Read the process description below and model it as an activity diagram:\n"
    "- Identify the main actions and model them as action nodes (role \"action\", type \"action\").\n"
    "- Use one initial node (role \"control\", type \"initial\") and one or more final nodes "
    "(role \"control\", type \"final\") to show start and end.\n"
    "- Add decision/merge (type \"decision\", \"merge\") where the text describes choices or branching.\n"
    "- Use fork/join (type \"fork\", \"join\") when tasks happen in parallel.\n"
    "- Use object nodes (role \"object\", type \"object\") when the focus is on data or artifacts.\n"
    "\n"
    "Process description:\n"
    "{process_text}\n"
    "\n"
    "You must return a single JSON object that conforms to this structure (structure only, no real data):\n"
    "{empty_schema}\n"
    "\n"
    "Structure rules:\n"
    "- Top level: \"interfaces\" (empty array), \"diagrams\" (array with one diagram object), "
    "\"id\", \"name\", \"description\".\n"
    "- Each diagram has \"nodes\", \"edges\", \"id\", \"type\" (\"activity\"), \"name\", \"description\", \"system\".\n"
    "- Each node has \"cls_data\" (with \"id\", \"project\", \"system\", \"data\"), \"id\", \"diagram\", \"cls\" "
    "(same as cls_data.id), \"data\" with \"position\" (\"x\", \"y\"). In cls_data.data: \"role\" "
    "(\"control\" or \"action\" or \"object\"), \"type\" (initial, action, final, decision, merge, fork, join, object). "
    "For action nodes include \"name\", \"body\", \"localPrecondition\", \"localPostcondition\"; "
    "for control nodes include \"activity_scope\" (e.g. \"activity\") where relevant.\n"
    "- Each edge has \"rel_data\" (with \"id\", \"data\" containing \"type\" (\"controlflow\" or \"objectflow\"), "
    "\"guard\", \"weight\", \"condition\", \"is_directed\" true, \"position_handlers\" []), \"system\", "
    "\"source\" and \"target\" (must be the cls_data.id of the source and target nodes). Also \"id\", \"diagram\", \"rel\", \"data\" ({}).\n"
    "- Use unique string IDs (e.g. UUIDs) for every \"id\", \"cls\", \"rel\", \"source\", \"target\", \"diagram\", \"system\", \"project\".\n"
    "\n"
    "Output rules (strict):\n"
    "- Output ONLY a single valid JSON object.\n"
    "- Do NOT include any explanations, prose, or reasoning.\n"
    "- Do NOT include markdown, code fences, or comments.\n"
    "- Do NOT include any text before or after the JSON.\n"
)


def generate_activity_model(process_text: str) -> dict:
    """
    Call the LLM to generate a clean activity model JSON structure.
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

    if not isinstance(parsed, dict) or "diagrams" not in parsed:
        raise Exception("LLM output does not follow required schema.")
    diagrams = parsed.get("diagrams") or []
    if not diagrams or "nodes" not in diagrams[0] or "edges" not in diagrams[0]:
        raise Exception("LLM output does not follow required schema.")

    return parsed


def export_activity_model(model: dict) -> None:
    """
    Pretty-print an activity model and save it to a JSON file
    in the current working directory.
    """
    print(json.dumps(model, indent=2))

    with open("activity_model.json", "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2, ensure_ascii=False)

