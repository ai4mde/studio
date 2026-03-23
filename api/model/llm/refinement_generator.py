"""
Activity modelling pipeline.

This module follows a single-core LLM design:
all activity models (generation and refinement) are handled
through the same core function, with different inputs.

Core entry point
----------------
`model_activity` is the only function responsible for:
- building the LLM prompt
- calling the LLM
- parsing the returned JSON
- validating the resulting activity graph

Note:
Generation and refinement share the same pipeline.
The only difference lies in the input provided.

Refinement wrapper
------------------
`refine_activity_model` is a thin wrapper around `model_activity`.
It additionally converts the output into AI4MDE format
for downstream/product usage.

Initial candidates (refinement pipeline)
----------------------------------------
`generate_initial_candidates` is the first step of the AI-assisted refinement
workflow: it produces several independent clean graphs by calling
`model_activity(process_text=...)` repeatedly. It does not convert to AI4MDE;
that happens after a candidate is chosen, via `refine_activity_model`.

Baseline (single model) stays in `baseline_generator` only.
"""
import json
from typing import Any, Dict, List, Optional

from .handler import call_openai
from .converter import convert_to_ai4mde
from .prompt_builder import build_activity_prompt


def _is_clean_format(model: dict) -> bool:
    """Check if the model is in clean format (nodes + edges at top level)."""
    return isinstance(model.get("nodes"), list) and isinstance(model.get("edges"), list)


def _extract_clean_from_ai4mde(ai4mde: dict) -> dict:
    """
    Extract a clean activity graph from AI4MDE format for use in prompts.
    Maps classifier IDs to simple ids (n1, n2, ...).
    """
    diagrams = ai4mde.get("diagrams") or []
    if not diagrams:
        return {"nodes": [], "edges": []}
    d = diagrams[0]
    nodes_raw = d.get("nodes") or []
    edges_raw = d.get("edges") or []

    cls_id_to_clean: Dict[str, str] = {}
    clean_nodes: list = []
    for i, node in enumerate(nodes_raw):
        cls_data = node.get("cls_data") or {}
        cls_id = cls_data.get("id") or str(node.get("cls", ""))
        data = cls_data.get("data") or {}
        node_type = data.get("type", "action")
        node_name = data.get("name", "")

        clean_id = f"n{i + 1}"
        cls_id_to_clean[cls_id] = clean_id

        clean_node: Dict[str, Any] = {"id": clean_id, "type": node_type}
        if node_type == "action" and node_name:
            clean_node["name"] = node_name
        clean_nodes.append(clean_node)

    clean_edges: list = []
    for edge in edges_raw:
        rel_data = edge.get("rel_data") or {}
        source_cls = rel_data.get("source")
        target_cls = rel_data.get("target")
        if source_cls and target_cls and source_cls in cls_id_to_clean and target_cls in cls_id_to_clean:
            edge_data: Dict[str, Any] = {
                "source": cls_id_to_clean[source_cls],
                "target": cls_id_to_clean[target_cls],
            }
            cond = (rel_data.get("data") or {}).get("condition")
            if cond:
                edge_data["condition"] = cond
            edge_type = (rel_data.get("data") or {}).get("type")
            if edge_type:
                edge_data["type"] = edge_type
            clean_edges.append(edge_data)

    return {"nodes": clean_nodes, "edges": clean_edges}


def _get_clean_model(model: dict) -> dict:
    """Return the model in clean format, converting from AI4MDE if needed."""
    if _is_clean_format(model):
        return model
    return _extract_clean_from_ai4mde(model)


def _get_ai4mde_metadata(ai4mde: dict) -> tuple:
    """Extract system_id, diagram_id, name, description from AI4MDE format."""
    system_id = str(ai4mde.get("id", "System"))
    name = str(ai4mde.get("name", "GeneratedActivity"))
    description = str(ai4mde.get("description", ""))
    diagrams = ai4mde.get("diagrams") or []
    diagram_id = str(diagrams[0].get("id", "diagram1")
                     ) if diagrams else "diagram1"
    return system_id, diagram_id, name, description


def model_activity(
    process_text: str,
    current_model: Optional[dict] = None,
    instruction: Optional[str] = None,
) -> dict:
    """
Core function for activity-diagram LLM modelling.

Overview
--------
`model_activity` is the single entry point for all activity modelling flows.
It is responsible for:
- building the LLM prompt
- calling the LLM
- parsing the returned JSON
- validating the resulting activity graph

All generation, refinement, and multi-candidate flows should go through this function.

Behavior
--------
- If `current_model` is None:
  Performs initial generation from the process description.

- If `current_model` is provided:
  Performs refinement of the existing model, optionally guided by `instruction`.

Multi-candidate generation is implemented as repeated calls to this function.

Parameters
----------
process_text : str
    Natural language description of the process.

current_model : dict, optional
    Existing activity graph to refine.

instruction : str, optional
    Additional guidance for refinement.

Returns
-------
dict
    A single validated activity graph with the structure:
    {
        "nodes": [...],
        "edges": [...]
    }
"""
    clean_current: Optional[dict] = None
    if current_model is not None:
        clean_current = _get_clean_model(current_model)

    prompt = build_activity_prompt(
        process_text=process_text,
        current_model=clean_current,
        refinement_instruction=instruction,
    )

    raw_output = call_openai("gpt-4o-mini", prompt)

    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        raise ValueError("LLM activity modelling output is not valid JSON.")

    if not isinstance(parsed, dict) or "nodes" not in parsed or "edges" not in parsed:
        raise ValueError(
            "LLM activity modelling output does not follow required schema.")
    if not isinstance(parsed.get("nodes"), list) or not isinstance(parsed.get("edges"), list):
        raise ValueError(
            "LLM activity modelling output does not follow required schema.")

    for node in parsed["nodes"]:
        if not isinstance(node, dict):
            raise ValueError(
                "LLM activity modelling output does not follow required schema.")
        if "id" not in node or "type" not in node:
            raise ValueError(
                "LLM activity modelling output does not follow required schema.")
        if node.get("type") == "action" and "name" not in node:
            raise ValueError(
                "LLM activity modelling output: action nodes must have a name.")

    for edge in parsed["edges"]:
        if not isinstance(edge, dict):
            raise ValueError(
                "LLM activity modelling output does not follow required schema.")
        if "source" not in edge or "target" not in edge:
            raise ValueError(
                "LLM activity modelling output does not follow required schema.")

    return parsed


def generate_initial_candidates(process_text: str, n: int = 3) -> List[dict]:
    """
    Produce multiple independent clean activity graphs for the same process text.

    This is the initial step of the AI-assisted refinement pipeline: several
    candidates are generated so a user (or UI) can pick one before iterative
    refinement. It replaces the previous standalone ``multi_generator`` module.

    Each candidate is produced by a separate call to ``model_activity`` with only
    ``process_text`` (generation mode). No AI4MDE conversion is performed here.

    Parameters
    ----------
    process_text : str
        Natural language description of the process.
    n : int, default 3
        Number of candidate models to generate. If ``n <= 0``, returns an empty list.

    Returns
    -------
    list of dict
        Each element is a clean graph ``{"nodes": [...], "edges": [...]}``.
    """
    if n <= 0:
        return []

    models: List[dict] = []
    for _ in range(n):
        models.append(model_activity(process_text=process_text))
    return models


def refine_activity_model(
    process_text: str,
    current_model: dict,
    refinement_instruction: str,
) -> dict:
    """
Refine an existing activity model based on designer feedback.

Overview
--------
`refine_activity_model` is a wrapper around `model_activity`.
It performs refinement of an existing activity graph and converts
the result into AI4MDE system format for downstream usage.

Behavior
--------
- Takes the original process description and a current activity model
  (either clean format or AI4MDE JSON).
- Applies the refinement instruction via the core modelling pipeline.
- Produces an updated clean activity graph.
- Converts the result into full AI4MDE system JSON
  (including project, system, diagram, and metadata).

The returned JSON can be used directly to re-render the diagram in the system.

Parameters
----------
process_text : str
    Original process description.

current_model : dict
    Existing activity model (clean graph or AI4MDE JSON).

refinement_instruction : str
    Instruction specifying how the model should be updated.

Returns
-------
dict
    Complete AI4MDE system JSON, including:
    - interfaces
    - diagrams (nodes and edges)
    - id, name, description
"""
    clean_graph = model_activity(
        process_text=process_text,
        current_model=current_model,
        instruction=refinement_instruction,
    )

    # Preserve metadata from current model if it's AI4MDE; otherwise use defaults
    if _is_clean_format(current_model):
        system_id = "System"
        diagram_id = "diagram1"
        name = "GeneratedActivity"
        description = ""
    else:
        system_id, diagram_id, name, description = _get_ai4mde_metadata(
            current_model)

    return convert_to_ai4mde(
        clean_model=clean_graph,
        system_id=system_id,
        diagram_id=diagram_id,
        name=name,
        description=description,
    )
