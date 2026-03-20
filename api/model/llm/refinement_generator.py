"""
Refinement module for iterative activity model refinement.
Takes the original process description, current model, and a designer's refinement
instruction; produces an updated AI4MDE system JSON for re-rendering.
"""
import json
from typing import Dict, Any, Optional

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
    diagram_id = str(diagrams[0].get("id", "diagram1")) if diagrams else "diagram1"
    return system_id, diagram_id, name, description


def model_activity(
    process_text: str,
    current_model: Optional[dict] = None,
    instruction: Optional[str] = None,
) -> dict:
    """
    Single core for activity-diagram LLM modelling.

    This is the only function that builds the activity prompt, calls the LLM,
    parses JSON, and validates the clean graph. All generation, refinement, and
    multi-candidate flows should go through here (multi-candidate = repeated calls).

    If current_model is None, behaves as initial generation from the process
    description. If current_model is provided, behaves as refinement guided by
    instruction.

    Returns exactly one clean activity graph: {\"nodes\": [...], \"edges\": [...]}.
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
        raise ValueError("LLM refinement output does not follow required schema.")
    if not isinstance(parsed.get("nodes"), list) or not isinstance(parsed.get("edges"), list):
        raise ValueError("LLM refinement output does not follow required schema.")

    for node in parsed["nodes"]:
        if not isinstance(node, dict):
            raise ValueError("LLM activity modelling output does not follow required schema.")
        if "id" not in node or "type" not in node:
            raise ValueError("LLM activity modelling output does not follow required schema.")
        if node.get("type") == "action" and "name" not in node:
            raise ValueError("LLM activity modelling output: action nodes must have a name.")

    for edge in parsed["edges"]:
        if not isinstance(edge, dict):
            raise ValueError("LLM activity modelling output does not follow required schema.")
        if "source" not in edge or "target" not in edge:
            raise ValueError("LLM activity modelling output does not follow required schema.")

    return parsed


def refine_activity_model(
    process_text: str,
    current_model: dict,
    refinement_instruction: str,
) -> dict:
    """
    Refine an activity model based on designer feedback.

    Takes the original process description, current model (clean or AI4MDE format),
    and a refinement instruction. Calls the core modelling operation to produce an
    updated clean activity graph, then converts it to full AI4MDE system JSON
    (project, system, diagram, metadata).

    The returned JSON can be used to re-render the diagram in the system.

    Args:
        process_text: The original process description.
        current_model: Current activity model (clean format or AI4MDE JSON).
        refinement_instruction: Designer's instruction for how to update the model.

    Returns:
        Complete AI4MDE system JSON with interfaces, diagrams (nodes + edges), id, name, description.
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
        system_id, diagram_id, name, description = _get_ai4mde_metadata(current_model)

    return convert_to_ai4mde(
        clean_model=clean_graph,
        system_id=system_id,
        diagram_id=diagram_id,
        name=name,
        description=description,
    )
