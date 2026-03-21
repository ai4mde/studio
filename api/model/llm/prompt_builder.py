"""
Load and render activity-modelling prompts from Jinja templates.

All natural-language instructions, rules, and schema descriptions live under
``llm/templates/`` — this module only wires variables and returns the final string.
"""
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


def build_activity_prompt(
    process_text: str,
    current_model: Optional[Dict[str, Any]] = None,
    refinement_instruction: Optional[str] = None,
) -> str:
    """
    Build a unified activity-modelling prompt from ``activity_prompt.jinja``.

    If current_model and refinement_instruction are both empty/None, the template
    renders generation mode. Otherwise it renders refinement mode (same rules as
    the previous Python implementation).
    """
    template = _env.get_template("activity_prompt.jinja")
    return template.render(
        process_text=process_text,
        current_model=current_model,
        instruction=refinement_instruction,
    ).rstrip() + "\n"
