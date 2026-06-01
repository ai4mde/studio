"""
ActivityGraph modelling pipeline.

# Responsibility:
# - orchestrate ProcessText -> ActivityGraph realization
# - optionally obtain a TopologyPlan (implemented today as ``ActivitySketch``)
# - parse and validate ActivityGraph JSON returned by the LLM
# - expose orchestration helpers for candidate generation and refinement
#
# Must NOT:
# - silently redesign topology beyond prompt-directed realization
# - act as the canonical home for AI4MDEExport translation policy
# - become the canonical home for diagnostics policy
#
# ARCHITECTURE NOTE:
# This module is currently overloaded. It mixes orchestration, prompt
# coordination, TopologyPlan handling, JSON recovery, ActivityGraph validation
# entrypoints, diagnostics hookup, and refinement-to-AI4MDEExport wrapping.
#
# Future stabilization may separate:
# - orchestration
# - realization
# - AI4MDEExport translation
# - diagnostics
# without changing runtime behavior in this phase.

This module follows a single-core LLM design:
all ActivityGraph generation and refinement flows are handled
through the same core function, with different inputs.

Core entry point
----------------
`model_activity` is the only function responsible for:
- building the LLM prompt
- calling the LLM
- parsing the returned JSON
- validating the resulting ActivityGraph

Debugging / tests
-----------------
Use :func:`debug_model_activity` or ``model_activity(..., debug=True)`` to inspect
``prompt`` and ``raw_response``. Pass ``llm_caller=`` to inject a fake LLM in unit
tests (no network).

Note:
Generation and refinement share the same pipeline.
The only difference lies in the input provided.

Refinement wrapper
------------------
`refine_activity_model` is a thin wrapper around `model_activity`.
It additionally converts the output into AI4MDEExport form
for downstream/product usage.

Multiple candidates (not a separate pipeline stage)
---------------------------------------------------
``generate_initial_candidates`` returns N ActivityGraph candidates by calling
``model_activity(process_text=...)`` **N times** — same core operation as
single-shot generation; there is no extra “multi-generation” layer beyond
those repeated calls. No refinement and no AI4MDE conversion here.

``generate_candidates_with_conversion`` calls ``generate_initial_candidates``
then converts **every**
candidate to AI4MDEExport **before** user selection, so the UI can render all options.
Each candidate gets fresh ``system_id`` / ``diagram_id`` UUIDs to avoid clashes.

After selection, use `refine_activity_model` for iterative refinement (pass the
chosen AI4MDEExport or ActivityGraph).

Baseline (single model) stays in `baseline_generator` only.
"""
import json
import logging
import os
import re
import uuid
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import ValidationError

from .activity_model import ActivityModel
from .activity_sketch_model import ActivitySketch
from .handler import call_openai, _activity_response_format, _activity_sketch_response_format
from .converter import convert_to_ai4mde, unwrap_ai4mde_systems_export
from .keyword_hints import extract_keyword_hints
from .normalization import normalize_activity_graph
from .prompt_builder import build_activity_prompt, build_activity_sketch_prompt_with_hints
from .semantic_analysis import analyze_semantic_graph
from .sketch_alignment import validate_graph_against_sketch

ActivityDebugResult = Dict[str, Any]
logger = logging.getLogger(__name__)
DEFAULT_ACTIVITY_OPENAI_MODEL = os.environ.get(
    "OPENAI_ACTIVITY_MODEL",
    "gpt-4o-mini-2024-07-18",
)


def _is_clean_format(model: Any) -> bool:
# Check whether the payload already matches the ActivityGraph shape.
    return (
        isinstance(model, dict)
        and isinstance(model.get("nodes"), list)
        and isinstance(model.get("edges"), list)
    )


def _unwrap_ai4mde_model(model: Any) -> dict:
    if _is_clean_format(model):
        return model
    return unwrap_ai4mde_systems_export(model)


def _extract_clean_from_ai4mde(ai4mde: dict) -> dict:
    # Extract an ActivityGraph from AI4MDEExport form for prompt reuse.
    # Maps classifier IDs to simple ids (n1, n2, ...).
    ai4mde = _unwrap_ai4mde_model(ai4mde)
    diagrams = ai4mde.get("diagrams") or []
    if not diagrams:
        return {"nodes": [], "edges": []}
    d = diagrams[0]
    nodes_raw = d.get("nodes") or []
    edges_raw = d.get("edges") or []
    classifiers = {
        str(classifier.get("id")): classifier.get("data") or {}
        for classifier in ai4mde.get("classifiers") or []
        if isinstance(classifier, dict) and classifier.get("id")
    }
    relations = {
        str(relation.get("id")): relation
        for relation in ai4mde.get("relations") or []
        if isinstance(relation, dict) and relation.get("id")
    }

    cls_id_to_clean: Dict[str, str] = {}
    clean_nodes: list = []
    for i, node in enumerate(nodes_raw):
        cls_id = str(node.get("cls", ""))
        data = classifiers.get(cls_id, {})
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
        rel_data = relations.get(str(edge.get("rel", "")), {})
        source_cls = str(rel_data.get("source", ""))
        target_cls = str(rel_data.get("target", ""))
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

    return normalize_activity_graph({"nodes": clean_nodes, "edges": clean_edges})


def _get_clean_model(model: dict) -> dict:
    # Return the payload as an ActivityGraph, converting from AI4MDEExport if needed.
    if _is_clean_format(model):
        return model
    return _extract_clean_from_ai4mde(model)


def _get_ai4mde_metadata(ai4mde: dict) -> tuple:
    # Extract metadata needed to preserve AI4MDEExport identity across refinement.
    ai4mde = _unwrap_ai4mde_model(ai4mde)
    system_id = str(ai4mde.get("id", "System"))
    name = str(ai4mde.get("name", "GeneratedActivity"))
    description = str(ai4mde.get("description", ""))
    project_id = ai4mde.get("project")
    project_id_str = str(project_id) if project_id is not None else ""
    diagrams = ai4mde.get("diagrams") or []
    diagram_id = str(diagrams[0].get("id", "diagram1")
                     ) if diagrams else "diagram1"
    return system_id, diagram_id, name, description, project_id_str


def _strip_markdown_fences(text: str) -> str:
    stripped = text.strip()
    fence_match = re.match(
        r"^\s*```(?:json)?\s*(.*?)\s*```\s*$",
        stripped,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if fence_match:
        return fence_match.group(1).strip()
    return stripped


def _extract_first_json_region(text: str) -> Optional[str]:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char not in "[{":
            continue
        candidate = text[index:].lstrip()
        leading_trim = len(text[index:]) - len(candidate)
        try:
            _, end = decoder.raw_decode(candidate)
        except json.JSONDecodeError:
            continue
        start = index + leading_trim
        return text[start:start + end]
    return None


def _prepare_json_payload(raw_output: str) -> str:
    cleaned = raw_output.strip()
    candidates = [cleaned]

    fence_stripped = _strip_markdown_fences(cleaned)
    if fence_stripped != cleaned:
        candidates.append(fence_stripped)

    for candidate in list(candidates):
        extracted = _extract_first_json_region(candidate)
        if extracted and extracted not in candidates:
            candidates.append(extracted)

    for candidate in candidates:
        try:
            json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if candidate != raw_output:
            logger.debug("Recovered JSON payload from fallback generation output.")
        return candidate

    return raw_output


def _parse_and_validate_activity_graph_json(raw_output: str) -> dict:
    # Parse LLM output and validate the ActivityGraph schema (nodes / edges).
    json_payload = _prepare_json_payload(raw_output)
    try:
        parsed_json = json.loads(json_payload)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM activity modelling output is not valid JSON.") from exc

    normalized_payload = normalize_activity_graph(parsed_json)

    try:
        parsed = ActivityModel.model_validate(normalized_payload)
    except ValidationError as exc:
        raise ValueError(
            f"LLM activity modelling output failed Pydantic validation: {exc}"
        ) from exc
    except ValueError as exc:
        raise ValueError(
            f"LLM activity modelling output failed semantic validation: {exc}"
        ) from exc

    return parsed.model_dump(exclude_none=True)


def _parse_and_validate_activity_sketch_json(raw_output: str) -> dict:
    # Parse LLM output and validate the TopologyPlan shape
    # (implemented today as ``ActivitySketch``).
    json_payload = _prepare_json_payload(raw_output)
    try:
        parsed_json = json.loads(json_payload)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM activity sketch output is not valid JSON.") from exc

    try:
        parsed = ActivitySketch.model_validate(parsed_json)
    except ValidationError as exc:
        raise ValueError(
            f"LLM activity sketch output failed Pydantic validation: {exc}"
        ) from exc

    return parsed.model_dump(exclude_none=True)


def _default_activity_llm_caller(prompt: str) -> str:
    return call_openai(
        DEFAULT_ACTIVITY_OPENAI_MODEL,
        prompt,
        response_format=_activity_response_format(),
    )


def _default_activity_sketch_llm_caller(prompt: str) -> str:
    return call_openai(
        DEFAULT_ACTIVITY_OPENAI_MODEL,
        prompt,
        response_format=_activity_sketch_response_format(),
    )


def _build_debug_result(
    prompt: str,
    raw_output: str,
    parsed: dict,
    *,
    keyword_hints: Optional[dict] = None,
    sketch: Optional[dict] = None,
    sketch_alignment: Optional[dict] = None,
    semantic_analysis: Optional[dict] = None,
) -> ActivityDebugResult:
    result: ActivityDebugResult = {
        "prompt": prompt,
        "raw_response": raw_output,
        "parsed": parsed,
        "model": parsed,
    }
    if keyword_hints is not None:
        result["keyword_hints"] = keyword_hints
    if sketch is not None:
        result["sketch"] = sketch
    if sketch_alignment is not None:
        result["sketch_alignment"] = sketch_alignment
    if semantic_analysis is not None:
        result["semantic_analysis"] = semantic_analysis
    return result


def _log_sketch_realization_debug(
    keyword_hints: dict,
    sketch: dict,
    parsed: dict,
    sketch_alignment: Optional[dict],
    semantic_analysis: Optional[dict],
) -> None:
    if not logger.isEnabledFor(logging.DEBUG):
        return

    planned_step_ids = [
        str(step_id).strip()
        for entry in sketch.get("main_flow") or []
        if isinstance(entry, dict)
        and (step_id := entry.get("step_id")) is not None
        and str(step_id).strip()
    ]
    planned_block_ids = [
        str(block_id).strip()
        for block in sketch.get("control_blocks") or []
        if isinstance(block, dict)
        and (block_id := block.get("block_id")) is not None
        and str(block_id).strip()
    ]
    action_nodes = [
        node
        for node in parsed.get("nodes") or []
        if isinstance(node, dict) and str(node.get("type", "")) == "action"
    ]
    realized_node_names = [
        str(node.get("name", "")).strip()
        for node in action_nodes
        if str(node.get("name", "")).strip()
    ]
    realized_origin_step_ids = [
        str(node.get("origin_step_id", "")).strip()
        for node in action_nodes
        if str(node.get("origin_step_id", "")).strip()
    ]
    metrics = (sketch_alignment or {}).get("metrics") or {}
    details = (sketch_alignment or {}).get("details") or {}
    semantic_metrics = (semantic_analysis or {}).get("metrics") or {}

    logger.debug(
        "Sketch realization summary: %s",
        {
            "keyword_flags": (keyword_hints or {}).get("flags", {}),
            "planned_step_ids": planned_step_ids,
            "planned_block_ids": planned_block_ids,
            "realized_node_names": realized_node_names,
            "realized_origin_step_ids": realized_origin_step_ids,
            "main_flow_resolution_modes": details.get("main_flow_resolution_modes", {}),
            "unresolved_step_ids": metrics.get("unresolved_step_ids", []),
            "unresolved_block_ids": metrics.get("unresolved_block_ids", []),
            "planner_binding_strength": metrics.get("planner_binding_strength"),
            "semantic_issue_count": semantic_metrics.get("issue_count", 0),
            "semantic_warning_count": semantic_metrics.get("warning_count", 0),
            "semantic_error_count": semantic_metrics.get("error_count", 0),
        },
    )


def _should_use_sketch(
    *,
    current_model: Optional[dict],
    instruction: Optional[str],
    llm_caller: Optional[Callable[[str], str]],
    use_sketch: Optional[bool],
) -> bool:
    if current_model is not None or instruction is not None:
        return False
    if use_sketch is not None:
        return use_sketch
    return llm_caller is None


def _generate_activity_sketch(
    process_text: str,
    *,
    sketch_llm_caller: Optional[Callable[[str], str]] = None,
) -> tuple[dict, str, str, dict]:
    keyword_hints = extract_keyword_hints(process_text)
    prompt = build_activity_sketch_prompt_with_hints(
        process_text,
        keyword_hints=keyword_hints,
    )
    caller = (
        sketch_llm_caller
        if sketch_llm_caller is not None
        else _default_activity_sketch_llm_caller
    )
    raw_output = caller(prompt)
    parsed = _parse_and_validate_activity_sketch_json(raw_output)
    return keyword_hints, prompt, raw_output, parsed


def _activity_llm_roundtrip(
    process_text: str,
    current_model: Optional[dict] = None,
    instruction: Optional[str] = None,
    *,
    llm_caller: Optional[Callable[[str], str]] = None,
    sketch_llm_caller: Optional[Callable[[str], str]] = None,
    use_sketch: Optional[bool] = None,
) -> tuple[Optional[dict], Optional[dict], Optional[dict], dict, str, str, dict]:
    
    # Build prompt, call the LLM, and validate the returned ActivityGraph.
    # Returns (TopologyPlan-as-ActivitySketch, alignment report, prompt, raw_response, ActivityGraph).
    
    clean_current: Optional[dict] = None
    if current_model is not None:
        clean_current = _get_clean_model(current_model)

    keyword_hints: Optional[dict] = None
    sketch: Optional[dict] = None
    if _should_use_sketch(
        current_model=current_model,
        instruction=instruction,
        llm_caller=llm_caller,
        use_sketch=use_sketch,
    ):
        keyword_hints, _, _, sketch = _generate_activity_sketch(
            process_text,
            sketch_llm_caller=sketch_llm_caller,
        )

    prompt = build_activity_prompt(
        process_text=process_text,
        current_model=clean_current,
        refinement_instruction=instruction,
        activity_sketch=sketch,
    )

    caller = llm_caller if llm_caller is not None else _default_activity_llm_caller
    raw_output = caller(prompt)
    parsed = _parse_and_validate_activity_graph_json(raw_output)
    sketch_alignment = (
        validate_graph_against_sketch(sketch, parsed)
        if sketch is not None
        else None
    )
    semantic_analysis = analyze_semantic_graph(
        parsed,
        sketch=sketch,
        keyword_hints=keyword_hints,
    )
    if sketch is not None:
        _log_sketch_realization_debug(
            keyword_hints or {},
            sketch,
            parsed,
            sketch_alignment,
            semantic_analysis,
        )
    return keyword_hints, sketch, sketch_alignment, semantic_analysis, prompt, raw_output, parsed


def debug_model_activity(
    process_text: str,
    current_model: Optional[dict] = None,
    instruction: Optional[str] = None,
    *,
    llm_caller: Optional[Callable[[str], str]] = None,
    sketch_llm_caller: Optional[Callable[[str], str]] = None,
    use_sketch: Optional[bool] = None,
) -> ActivityDebugResult:
    """
    Same pipeline as ``model_activity``, but returns intermediates for debugging
    and unit tests.

    Returns
    -------
    dict
        ``prompt`` — text sent to the LLM
        ``raw_response`` — string returned by the LLM (before JSON parse)
        ``parsed`` / ``model`` — validated ActivityGraph ``{"nodes": [...], "edges": [...]}``
        ``sketch_alignment`` — diagnostic TopologyPlan-versus-ActivityGraph alignment report when planning is enabled
    """
    keyword_hints, sketch, sketch_alignment, semantic_analysis, prompt, raw_output, parsed = _activity_llm_roundtrip(
        process_text,
        current_model=current_model,
        instruction=instruction,
        llm_caller=llm_caller,
        sketch_llm_caller=sketch_llm_caller,
        use_sketch=use_sketch,
    )
    return _build_debug_result(
        prompt,
        raw_output,
        parsed,
        keyword_hints=keyword_hints,
        sketch=sketch,
        sketch_alignment=sketch_alignment,
        semantic_analysis=semantic_analysis,
    )


def model_activity(
    process_text: str,
    current_model: Optional[dict] = None,
    instruction: Optional[str] = None,
    *,
    debug: bool = False,
    llm_caller: Optional[Callable[[str], str]] = None,
    sketch_llm_caller: Optional[Callable[[str], str]] = None,
    use_sketch: Optional[bool] = None,
) -> Union[dict, ActivityDebugResult]:
    """
Core function for ActivityGraph LLM modelling.

Overview
--------
`model_activity` is the single entry point for all activity modelling flows.
It is responsible for:
- building the LLM prompt
- calling the LLM
- parsing the returned JSON
- validating the resulting ActivityGraph

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
    Existing ActivityGraph or AI4MDEExport payload to refine.

instruction : str, optional
    Additional guidance for refinement.

Returns
-------
dict
    A single validated ActivityGraph with the structure:
    {
        "nodes": [...],
        "edges": [...]
    }

debug : bool, optional
    If True, return the same structure as :func:`debug_model_activity` instead
    of only the model.

llm_caller : callable, optional
    ``(prompt: str) -> str`` replacing the default OpenAI call. For tests and
    offline debugging only.
"""
    keyword_hints, sketch, sketch_alignment, semantic_analysis, prompt, raw_output, parsed = _activity_llm_roundtrip(
        process_text,
        current_model=current_model,
        instruction=instruction,
        llm_caller=llm_caller,
        sketch_llm_caller=sketch_llm_caller,
        use_sketch=use_sketch,
    )
    if debug:
        return _build_debug_result(
            prompt,
            raw_output,
            parsed,
            keyword_hints=keyword_hints,
            sketch=sketch,
            sketch_alignment=sketch_alignment,
            semantic_analysis=semantic_analysis,
        )
    return parsed


def generate_initial_candidates(
    process_text: str,
    n: int = 3,
    *,
    use_sketch: Optional[bool] = None,
) -> List[dict]:
    """
    Return N independent ActivityGraph candidates for the same ``process_text``.

    Implementation is **only** repeated calls to ``model_activity(process_text=...)``
    (generation mode). Multi-candidate output is not a separate pipeline: it is
    the same core function executed N times so a human (or UI) can choose one
    candidate before refinement.

    Does **not** refine ActivityGraph payloads, convert to AI4MDEExport, or call ``refine_activity_model``.

    Parameters
    ----------
    process_text : str
        Natural language description of the process.
    n : int, default 3
        How many times to run generation. If ``n <= 0``, returns an empty list.

    Returns
    -------
    list of dict
        Each element is an ActivityGraph ``{"nodes": [...], "edges": [...]}``.
    """
    if n <= 0:
        return []

    models: List[dict] = []
    for _ in range(n):
        models.append(model_activity(process_text=process_text, use_sketch=use_sketch))
    return models


def generate_and_convert_candidates(
    process_text: str,
    n: int = 3,
    *,
    project_id: str,
    use_sketch: Optional[bool] = None,
    name_prefix: str = "Activity candidate",
    description_template: str = "Generated candidate {index} for interactive selection",
) -> List[Dict[str, Any]]:
    """
    Generate N ActivityGraph candidates and convert each to AI4MDEExport before selection.

    Intended for AI-assisted flows where the frontend displays diagrams in
    AI4MDEExport form: all candidates are converted up front so the user can compare
    visualizations, then pick one for refinement.

    Parameters
    ----------
    process_text : str
        Natural language process description.
    n : int, default 3
        Number of candidates. If ``n <= 0``, returns an empty list.
    project_id : str
        Existing AI4MDE project UUID reused by all generated candidates in the same session.
    name_prefix : str, optional
        Base name for each system's ``name`` field (index appended).
    description_template : str, optional
        ``description`` for each AI4MDEExport payload; ``{index}`` is replaced with 1-based index.

    Returns
    -------
    list of dict
        Each element is ``{"clean": <ActivityGraph>, "ai4mde": <AI4MDEExport list>}``.
        Each candidate uses a new ``system_id`` and ``diagram_id`` but the same project id.
    """
    cleans = generate_initial_candidates(process_text, n=n, use_sketch=use_sketch)
    results: List[Dict[str, Any]] = []
    for i, clean in enumerate(cleans, start=1):
        system_id = str(uuid.uuid4())
        diagram_id = str(uuid.uuid4())
        ai4mde = convert_to_ai4mde(
            clean_model=clean,
            system_id=system_id,
            diagram_id=diagram_id,
            name=f"{name_prefix} {i}",
            description=description_template.format(index=i),
            project_id=project_id,
        )
        results.append({"clean": clean, "ai4mde": ai4mde})
    return results


def generate_candidates_with_conversion(
    process_text: str,
    n: int = 3,
    *,
    project_id: str,
    use_sketch: Optional[bool] = None,
    name_prefix: str = "Activity candidate",
    description_template: str = "Generated candidate {index} for interactive selection",
) -> List[Dict[str, Any]]:
    return generate_and_convert_candidates(
        process_text,
        n=n,
        project_id=project_id,
        use_sketch=use_sketch,
        name_prefix=name_prefix,
        description_template=description_template,
    )


def refine_activity_model(
    process_text: str,
    current_model: dict,
    refinement_instruction: str,
    *,
    project_id: Optional[str] = None,
) -> dict:
    """
Refine **one** ActivityGraph per call (after human selection of a single candidate).

Overview
--------
`refine_activity_model` is a wrapper around `model_activity`.
It performs refinement of an existing ActivityGraph and converts
the result into AI4MDEExport form for downstream usage.

Behavior
--------
- Takes the original process description and a current ActivityGraph
  (or AI4MDEExport payload).
- Applies the refinement instruction via the core modelling pipeline.
- Produces an updated ActivityGraph.
- Converts the result into full AI4MDEExport form
  (including project, system, diagram, and metadata).

The returned JSON can be used directly to re-render the diagram in the system.

Parameters
----------
process_text : str
    Original process description.

current_model : dict
    Existing ActivityGraph or AI4MDEExport payload.

refinement_instruction : str
    Instruction specifying how the model should be updated.

Returns
-------
dict
    Complete AI4MDEExport payload, including:
    - interfaces
    - diagrams (nodes and edges)
    - id, name, description
"""
    clean_graph = model_activity(
        process_text=process_text,
        current_model=current_model,
        instruction=refinement_instruction,
    )

    # Preserve metadata from the existing AI4MDEExport when available.
    resolved_project_id = project_id
    if _is_clean_format(current_model):
        system_id = "System"
        diagram_id = "diagram1"
        name = "GeneratedActivity"
        description = ""
        if not resolved_project_id:
            raise ValueError(
                "project_id is required when refining from a clean model so the refined "
                "system stays in the same experiment session"
            )
    else:
        system_id, diagram_id, name, description, proj = _get_ai4mde_metadata(
            current_model)
        resolved_project_id = proj or resolved_project_id

    if not resolved_project_id:
        raise ValueError("refine_activity_model could not determine a valid project_id")

    return convert_to_ai4mde(
        clean_model=clean_graph,
        system_id=system_id,
        diagram_id=diagram_id,
        name=name,
        description=description,
        project_id=resolved_project_id,
    )
