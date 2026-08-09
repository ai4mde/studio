"""
Utilities for building ActivityGraph modelling prompts.

# Responsibility:
# - render prompt text from ProcessText, ActivityGraph, and TopologyPlan inputs
# - keep prompt assembly separate from LLM calls and payload parsing
#
# Must NOT:
# - call the LLM
# - validate ActivityGraph payloads
# - perform AI4MDEExport translation

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
    Build a prompt for ActivityGraph modelling.

    Overview
    --------
    This function loads the Jinja template `activity_prompt.jinja`,
    fills in the given inputs, and returns the final prompt string.

    It does NOT call the LLM. It only prepares the prompt.

    Behavior
    --------
    - If both `current_model` and `refinement_instruction` are None:
        → Generation mode (create a new ActivityGraph)

    - Otherwise:
        → Refinement mode (update an existing ActivityGraph)

    The template will receive:
    - process_text
    - current_model
    - instruction

    Parameters
    ----------
    process_text : str
        Description of the process.

    current_model : dict, optional
        Existing ActivityGraph to refine.

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
    Build a lightweight TopologyPlan prompt for initial generation.

    This prompt is only used before baseline ActivityGraph generation and does
    not produce nodes/edges or AI4MDEExport payloads.
    """
    template = _env.get_template("activity_sketch_prompt.jinja")
    return template.render(process_text=process_text).rstrip() + "\n"


def build_activity_sketch_prompt_with_hints(
    process_text: str,
    *,
    keyword_hints: Optional[Dict[str, Any]] = None,
    topology_artifact: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a lightweight TopologyPlan prompt augmented with soft keyword hints.

    Keyword hints are planner guidance only. They should influence the sketch
    layer without becoming a hard rule engine or direct graph constructor.
    """
    template = _env.get_template("activity_sketch_prompt.jinja")
    return template.render(
        process_text=process_text,
        keyword_hints=keyword_hints,
        topology_artifact=topology_artifact,
    ).rstrip() + "\n"


def build_activity_sketch_review_prompt(
    process_text: str,
    *,
    activity_sketch: Dict[str, Any],
) -> str:
    template = _env.get_template("activity_sketch_review_prompt.jinja")
    return template.render(
        process_text=process_text,
        activity_sketch=activity_sketch,
    ).rstrip() + "\n"


def build_activity_sketch_repair_prompt(
    process_text: str,
    *,
    activity_sketch: Dict[str, Any],
    repair_report: Optional[Dict[str, Any]] = None,
    probe_diagnostics: Optional[Dict[str, Any]] = None,
) -> str:
    template = _env.get_template("activity_sketch_repair_prompt.jinja")
    return template.render(
        process_text=process_text,
        activity_sketch=activity_sketch,
        repair_report=repair_report,
        probe_diagnostics=probe_diagnostics,
    ).rstrip() + "\n"


def build_activity_graph_repair_prompt(
    process_text: str,
    *,
    activity_graph: Dict[str, Any],
    topology_report: Dict[str, Any],
    sketch_alignment: Optional[Dict[str, Any]] = None,
    semantic_analysis: Optional[Dict[str, Any]] = None,
    activity_sketch: Optional[Dict[str, Any]] = None,
) -> str:
    template = _env.get_template("activity_graph_repair_prompt.jinja")
    return template.render(
        process_text=process_text,
        activity_graph=activity_graph,
        topology_report=topology_report,
        sketch_alignment=sketch_alignment,
        semantic_analysis=semantic_analysis,
        activity_sketch=activity_sketch,
    ).rstrip() + "\n"
