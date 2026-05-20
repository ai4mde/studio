"""
Utilities for building activity modelling prompts.

Overview
--------
This module loads Jinja templates and fills them with data to create
LLM prompts.

All prompt content (instructions, rules, schemas) is stored in
`llm/templates/`. This file only handles template rendering.

Behavior
--------
- Templates are loaded from the templates folder
- Variables are injected into the template
- A final prompt string is returned

This module does NOT:
- call the LLM
- process model outputs
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
    activity_sketch: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a prompt for activity modelling.

    Overview
    --------
    This function loads the Jinja template `activity_prompt.jinja`,
    fills in the given inputs, and returns the final prompt string.

    It does NOT call the LLM. It only prepares the prompt.

    Behavior
    --------
    - If both `current_model` and `refinement_instruction` are None:
        → Generation mode (create a new model)

    - Otherwise:
        → Refinement mode (update an existing model)

    The template will receive:
    - process_text
    - current_model
    - instruction

    Parameters
    ----------
    process_text : str
        Description of the process.

    current_model : dict, optional
        Existing model to refine.

    refinement_instruction : str, optional
        Extra instructions for refinement.

    Returns
    -------
    str
        The final prompt string.
    """

    if current_model is None and refinement_instruction is None:
        template = _env.get_template("activity_baseline_prompt.jinja")
    else:
        template = _env.get_template("activity_refinement_prompt.jinja")

    return template.render(
        process_text=process_text,
        current_model=current_model,
        instruction=refinement_instruction,
        activity_sketch=activity_sketch,
    ).rstrip() + "\n"


def build_activity_sketch_prompt(process_text: str) -> str:
    """
    Build a lightweight topology-sketch prompt for initial generation.

    This prompt is only used before baseline graph generation and does not
    produce nodes/edges or AI4MDE JSON.
    """
    template = _env.get_template("activity_sketch_prompt.jinja")
    return template.render(process_text=process_text).rstrip() + "\n"
