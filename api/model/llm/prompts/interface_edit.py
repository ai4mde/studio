"""Prompt for converting a natural-language UI edit request into an interface patch."""

import json

from llm.interface_generator.interface_schemas import _DATA_SCHEMA, _LAYOUT_SCHEMA


def build_interface_edit_prompt(
    actor_name: str,
    classifiers: list[dict],
    current_data: dict,
    user_request: str,
) -> str:
    """Build interface edit prompt."""
    current_json = json.dumps(current_data, ensure_ascii=False)[:50_000]
    classifiers_json = json.dumps(classifiers, ensure_ascii=False)

    return (
        "Convert the user's UI edit request into one JSON patch for the interface editor.\n"
        "Output JSON only. Do not include markdown.\n"
        "Patch schema: {\"pages\": [...], \"sections\": [...], \"styling\": {...}, \"tokens\": {...}}.\n"
        "Only include fields that must change. Preserve existing human edits unless explicitly asked.\n"
        "Every changed page/section must include its existing id. New page/section ids must be stable snake_case strings.\n"
        "Data-bound section attributes must use only real classifier attributes listed below.\n"
        "Do not invent model fields. For static/chrome/media sections use primary_model='', class='', attributes=[].\n\n"
        f"Actor: {actor_name}\n"
        f"Classifiers: {classifiers_json}\n"
        f"Current interface: {current_json}\n"
        f"User request: {user_request}\n\n"
        f"Editable layout fields:\n{_LAYOUT_SCHEMA}\n\n"
        f"Editable data fields:\n{_DATA_SCHEMA}\n"
    )
