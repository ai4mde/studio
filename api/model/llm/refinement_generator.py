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
from .experimental_compiler import compile_activity_sketch
from .keyword_hints import extract_keyword_hints
from .normalization import normalize_activity_graph
from .pipeline_profiles import PipelineProfile, resolve_pipeline_config
from .prompt_builder import (
    build_activity_graph_repair_prompt,
    build_activity_prompt,
    build_activity_sketch_repair_prompt,
    build_activity_sketch_prompt_with_hints,
    build_activity_sketch_review_prompt,
)
from .semantic_analysis import analyze_semantic_graph
from .semantic_sketch_experiment import generate_semantic_sketch_plan
from .sketch_alignment import validate_graph_against_sketch
from .sketch_repair import repair_activity_sketch, sketch_requires_retry
from .topology_analysis import analyze_activity_graph
from .topology_experiment import generate_topology_artifact
from .topology_to_sketch_compiler import compile_topology_and_semantics_to_activity_sketch

ActivityDebugResult = Dict[str, Any]
logger = logging.getLogger(__name__)
DEFAULT_ACTIVITY_OPENAI_MODEL = os.environ.get(
    "OPENAI_ACTIVITY_MODEL",
    "gpt-4o-mini-2024-07-18",
)


class SketchGenerationError(Exception):
    def __init__(self, message: str, *, debug_artifacts: Dict[str, Any]) -> None:
        super().__init__(message)
        self.debug_artifacts = debug_artifacts


def _log_pipeline_execution(pipeline_profile: PipelineProfile, executed_stages: List[str]) -> None:
    logger.info("Pipeline Profile: %s", pipeline_profile)
    logger.info("Executed Stages:")
    for stage_name in executed_stages:
        logger.info("- %s", stage_name)


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


_ALLOWED_BRANCH_KEYS = {
    "label",
    "returns_to_main_flow",
    "steps",
    "next_block_id",
    "child_block_ids",
}
_ALLOWED_BRANCH_STEP_KEYS = {
    "step_id",
    "action",
}


def _sanitize_branch_payload(branch: Any) -> Any:
    if not isinstance(branch, dict):
        return branch

    sanitized = {
        key: _sanitize_branch_payload(value)
        for key, value in branch.items()
        if key in _ALLOWED_BRANCH_KEYS
    }

    steps = sanitized.get("steps")
    if isinstance(steps, list):
        sanitized["steps"] = [_sanitize_branch_step_payload(step) for step in steps]

    return sanitized


def _sanitize_branch_step_payload(step: Any) -> Any:
    if not isinstance(step, dict):
        return step
    return {
        key: value
        for key, value in step.items()
        if key in _ALLOWED_BRANCH_STEP_KEYS
    }


def _sanitize_activity_sketch_payload(payload: Any) -> Any:
    if isinstance(payload, list):
        return [_sanitize_activity_sketch_payload(item) for item in payload]
    if not isinstance(payload, dict):
        return payload

    sanitized = {
        key: _sanitize_activity_sketch_payload(value)
        for key, value in payload.items()
    }

    branches = sanitized.get("branches")
    if isinstance(branches, list):
        sanitized["branches"] = [_sanitize_branch_payload(branch) for branch in branches]

    return sanitized


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

    sanitized_payload = _sanitize_activity_sketch_payload(parsed_json)

    try:
        parsed = ActivitySketch.model_validate(sanitized_payload)
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
    sketch_repair: Optional[dict] = None,
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
    if sketch_repair is not None:
        result["sketch_repair"] = sketch_repair
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


_PROBE_TOPOLOGY_RETRY_ISSUES = {
    "disconnected_nodes",
    "dead_end_nodes",
    "possible_missing_merge",
    "possible_missing_join",
}
_PROBE_SEMANTIC_RETRY_ISSUES = {
    "missing_loop_exit",
    "invalid_loop_back_target",
    "dead_end_path",
    "unreachable_nodes",
}
_ALIGNMENT_RETRY_MESSAGES = {
    "exit_to_not_reachable_from_entry": "planned continuation is not reachable from its block entry",
    "loop_back_edge_not_realized": "loop closure is missing its backward path",
    "missing_merge_for_decision": "decision closure is missing a merge",
    "missing_join_for_parallel": "parallel closure is missing a join",
    "child_block_not_realized": "a referenced child block is not realized",
    "missing_decision_node": "a planned decision block is not realized",
}
_TOPOLOGY_RETRY_MESSAGES = {
    "disconnected_nodes": "disconnected topology detected",
    "dead_end_nodes": "a control path ends without a valid continuation",
    "possible_missing_merge": "a decision closure appears to be missing a merge",
    "possible_missing_join": "a parallel closure appears to be missing a join",
}
_SEMANTIC_RETRY_MESSAGES = {
    "missing_loop_exit": "loop exit path missing",
    "invalid_loop_back_target": "loop back target is missing or not reached by a backward edge",
    "dead_end_path": "a non-final path terminates unexpectedly",
    "unreachable_nodes": "some realized nodes are unreachable from the initial node",
}


def _probe_activity_sketch(
    sketch: Optional[dict],
    *,
    keyword_hints: Optional[dict] = None,
) -> dict:
    probe_graph = compile_activity_sketch(sketch)
    sketch_alignment = validate_graph_against_sketch(sketch, probe_graph) if sketch is not None else None
    topology_report = analyze_activity_graph(probe_graph)
    semantic_analysis = analyze_semantic_graph(
        probe_graph,
        sketch=sketch,
        keyword_hints=keyword_hints,
    )
    return {
        "graph": probe_graph,
        "sketch_alignment": sketch_alignment,
        "topology_report": topology_report,
        "semantic_analysis": semantic_analysis,
    }


def _should_retry_after_probe(
    repair_report: Optional[dict],
    *,
    probe_report: Optional[dict] = None,
) -> bool:
    if sketch_requires_retry(repair_report):
        return True
    if not probe_report:
        return False

    alignment = probe_report.get("sketch_alignment") or {}
    topology = probe_report.get("topology_report") or {}
    semantic = probe_report.get("semantic_analysis") or {}

    topology_issues = set(topology.get("issues") or [])
    if topology_issues & _PROBE_TOPOLOGY_RETRY_ISSUES:
        return True

    semantic_issue_codes = {
        str(issue.get("code") or "").strip()
        for issue in semantic.get("issues") or []
        if isinstance(issue, dict)
    }
    if semantic_issue_codes & _PROBE_SEMANTIC_RETRY_ISSUES:
        return True

    alignment_metrics = alignment.get("metrics") or {}
    if int(alignment_metrics.get("realized_reconnects", 0)) < int(alignment_metrics.get("expected_reconnects", 0)):
        return True
    if int(alignment_metrics.get("realized_loop_backs", 0)) < int(alignment_metrics.get("expected_loop_backs", 0)):
        return True
    if int(alignment_metrics.get("realized_merges", 0)) < int(alignment_metrics.get("expected_merges", 0)):
        return True

    return False


def _build_sketch_retry_feedback(
    repair_report: Optional[dict],
    *,
    probe_report: Optional[dict] = None,
) -> List[str]:
    feedback: List[str] = []

    for defect in (repair_report or {}).get("critical_defects") or []:
        normalized = str(defect).replace("_", " ")
        feedback.append(normalized)

    alignment = (probe_report or {}).get("sketch_alignment") or {}
    topology = (probe_report or {}).get("topology_report") or {}
    semantic = (probe_report or {}).get("semantic_analysis") or {}

    alignment_issues = alignment.get("issues") or []
    for issue in alignment_issues:
        message = _ALIGNMENT_RETRY_MESSAGES.get(str(issue), str(issue).replace("_", " "))
        feedback.append(message)

    for issue in topology.get("issues") or []:
        if issue in _PROBE_TOPOLOGY_RETRY_ISSUES:
            feedback.append(_TOPOLOGY_RETRY_MESSAGES.get(str(issue), str(issue).replace("_", " ")))

    for issue in semantic.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        code = str(issue.get("code") or "").strip()
        if code in _PROBE_SEMANTIC_RETRY_ISSUES:
            feedback.append(_SEMANTIC_RETRY_MESSAGES.get(code, code.replace("_", " ")))

    alignment_metrics = alignment.get("metrics") or {}
    unresolved_block_ids = alignment_metrics.get("unresolved_block_ids") or []
    if unresolved_block_ids:
        feedback.append(
            "unrealized or disconnected blocks: " + ", ".join(str(block_id) for block_id in unresolved_block_ids)
        )
    if int(alignment_metrics.get("realized_reconnects", 0)) < int(alignment_metrics.get("expected_reconnects", 0)):
        feedback.append("missing continuation between planned control blocks")
    if int(alignment_metrics.get("realized_loop_backs", 0)) < int(alignment_metrics.get("expected_loop_backs", 0)):
        feedback.append("loop backward continuation is incomplete")
    if int(alignment_metrics.get("realized_merges", 0)) < int(alignment_metrics.get("expected_merges", 0)):
        feedback.append("planned block closure is incomplete")

    deduped_feedback: List[str] = []
    seen = set()
    for item in feedback:
        normalized = " ".join(str(item).strip().split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped_feedback.append(normalized)
    return deduped_feedback


def _generate_activity_sketch(
    process_text: str,
    *,
    sketch_llm_caller: Optional[Callable[[str], str]] = None,
    use_sketch_review_agent: bool = False,
    use_prompted_sketch_repair_agent: bool = False,
    use_topology_artifact_guidance: bool = False,
) -> tuple[dict, str, str, dict, dict, dict]:
    keyword_hints = extract_keyword_hints(process_text)
    topology_artifact: Optional[dict] = None
    topology_artifact_prompt: Optional[str] = None
    topology_artifact_raw_output: Optional[str] = None
    topology_artifact_response_mode: Optional[str] = None
    topology_artifact_fallback_reason: Optional[str] = None
    if use_topology_artifact_guidance:
        topology_result = generate_topology_artifact(process_text)
        topology_artifact = topology_result.get("artifact")
        topology_artifact_prompt = topology_result.get("prompt")
        topology_artifact_raw_output = topology_result.get("raw_output")
        topology_artifact_response_mode = topology_result.get("response_mode")
        topology_artifact_fallback_reason = topology_result.get("fallback_reason")
    prompt = build_activity_sketch_prompt_with_hints(
        process_text,
        keyword_hints=keyword_hints,
        topology_artifact=topology_artifact,
    )

    def _raise_sketch_generation_error(
        stage: str,
        prompt_text: str,
        output_text: str,
        exc: Exception,
    ) -> None:
        raise SketchGenerationError(
            f"ActivitySketch validation failed during {stage}: {exc}",
            debug_artifacts={
                "process_text": process_text,
                "keyword_hints": keyword_hints,
                "topology_artifact": topology_artifact,
                "topology_artifact_prompt": topology_artifact_prompt,
                "topology_artifact_raw_output": topology_artifact_raw_output,
                "topology_artifact_response_mode": topology_artifact_response_mode,
                "topology_artifact_fallback_reason": topology_artifact_fallback_reason,
                "sketch_prompt": prompt_text,
                "sketch_raw_output": output_text,
                "sketch_error_stage": stage,
                "sketch_validation_error": str(exc),
            },
        ) from exc

    caller = (
        sketch_llm_caller
        if sketch_llm_caller is not None
        else _default_activity_sketch_llm_caller
    )
    raw_output = caller(prompt)
    try:
        parsed = _parse_and_validate_activity_sketch_json(raw_output)
    except Exception as exc:
        _raise_sketch_generation_error("sketch_planner_output", prompt, raw_output, exc)
    original_sketch = parsed
    reviewed_sketch: Optional[dict] = None
    if use_sketch_review_agent:
        review_prompt = build_activity_sketch_review_prompt(
            process_text,
            activity_sketch=parsed,
        )
        reviewed_raw_output = caller(review_prompt)
        try:
            parsed = _parse_and_validate_activity_sketch_json(reviewed_raw_output)
        except Exception as exc:
            _raise_sketch_generation_error("sketch_review_output", review_prompt, reviewed_raw_output, exc)
        reviewed_sketch = parsed
    repaired_sketch, repair_report = repair_activity_sketch(parsed)
    deterministically_repaired_sketch = repaired_sketch
    prompted_repaired_sketch: Optional[dict] = None
    probe_report = _probe_activity_sketch(
        repaired_sketch,
        keyword_hints=keyword_hints,
    )
    if use_prompted_sketch_repair_agent and repaired_sketch is not None:
        sketch_repair_prompt = build_activity_sketch_repair_prompt(
            process_text,
            activity_sketch=repaired_sketch,
            repair_report=repair_report,
            probe_diagnostics={
                "sketch_alignment": probe_report.get("sketch_alignment"),
                "topology_report": probe_report.get("topology_report"),
                "semantic_analysis": probe_report.get("semantic_analysis"),
            },
        )
        prompted_raw_output = caller(sketch_repair_prompt)
        try:
            parsed = _parse_and_validate_activity_sketch_json(prompted_raw_output)
        except Exception as exc:
            _raise_sketch_generation_error("prompted_sketch_repair_output", sketch_repair_prompt, prompted_raw_output, exc)
        repaired_sketch, repair_report = repair_activity_sketch(parsed)
        raw_output = prompted_raw_output
        prompted_repaired_sketch = repaired_sketch
        probe_report = _probe_activity_sketch(
            repaired_sketch,
            keyword_hints=keyword_hints,
        )
    repair_report["probe_diagnostics"] = {
        "sketch_alignment": probe_report.get("sketch_alignment"),
        "topology_report": probe_report.get("topology_report"),
        "semantic_analysis": probe_report.get("semantic_analysis"),
    }
    retry_feedback = _build_sketch_retry_feedback(
        repair_report,
        probe_report=probe_report,
    )
    repair_report["retry_feedback"] = retry_feedback

    if _should_retry_after_probe(repair_report, probe_report=probe_report):
        retry_prompt = (
            prompt.rstrip()
            + "\n\nRepair the sketch and regenerate it once.\n"
            + "Fix the following topology problems while preserving business semantics:\n"
            + "\n".join(f"- {issue}" for issue in retry_feedback)
            + "\n- Remove invalid references instead of inventing uncertain targets.\n"
            + "- Restore block sequencing and continuation before adding new control structure.\n"
            + "- Keep decision decomposition simple and valid.\n"
        )
        raw_output = caller(retry_prompt)
        try:
            parsed = _parse_and_validate_activity_sketch_json(raw_output)
        except Exception as exc:
            _raise_sketch_generation_error("sketch_retry_output", retry_prompt, raw_output, exc)
        repaired_sketch, repair_report = repair_activity_sketch(parsed)
        probe_report = _probe_activity_sketch(
            repaired_sketch,
            keyword_hints=keyword_hints,
        )
        repair_report["used_retry"] = True
        repair_report["metrics"]["planner_retry_triggered"] = True
        repair_report["probe_diagnostics"] = {
            "sketch_alignment": probe_report.get("sketch_alignment"),
            "topology_report": probe_report.get("topology_report"),
            "semantic_analysis": probe_report.get("semantic_analysis"),
        }
        repair_report["retry_feedback"] = _build_sketch_retry_feedback(
            repair_report,
            probe_report=probe_report,
        )

    return keyword_hints, prompt, raw_output, repaired_sketch, repair_report, {
        "topology_artifact": topology_artifact,
        "topology_artifact_prompt": topology_artifact_prompt,
        "topology_artifact_raw_output": topology_artifact_raw_output,
        "topology_artifact_response_mode": topology_artifact_response_mode,
        "topology_artifact_fallback_reason": topology_artifact_fallback_reason,
        "sketch_prompt": prompt,
        "sketch_raw_output": raw_output,
        "original_sketch": original_sketch,
        "reviewed_sketch": reviewed_sketch,
        "deterministically_repaired_sketch": deterministically_repaired_sketch,
        "prompted_repaired_sketch": prompted_repaired_sketch,
        "repaired_sketch": repaired_sketch,
        "probe_graph": probe_report.get("graph"),
        "probe_validation": {
            "sketch_alignment": probe_report.get("sketch_alignment"),
            "topology_report": probe_report.get("topology_report"),
            "semantic_analysis": probe_report.get("semantic_analysis"),
        },
    }


def _activity_llm_roundtrip(
    process_text: str,
    current_model: Optional[dict] = None,
    instruction: Optional[str] = None,
    *,
    llm_caller: Optional[Callable[[str], str]] = None,
    sketch_llm_caller: Optional[Callable[[str], str]] = None,
    use_sketch: Optional[bool] = None,
    use_sketch_review_agent: bool = False,
    use_prompted_sketch_repair_agent: bool = False,
    use_graph_repair_agent: bool = False,
    use_topology_artifact_guidance: bool = False,
) -> tuple[Optional[dict], Optional[dict], Optional[dict], Optional[dict], dict, str, str, dict, dict]:
    
    # Build prompt, call the LLM, and validate the returned ActivityGraph.
    # Returns (keyword_hints, sketch, sketch_repair, alignment report, prompt, raw_response, ActivityGraph).
    
    clean_current: Optional[dict] = None
    if current_model is not None:
        clean_current = _get_clean_model(current_model)

    keyword_hints: Optional[dict] = None
    sketch: Optional[dict] = None
    sketch_repair: Optional[dict] = None
    stage_artifacts: dict = {
        "topology_artifact": None,
        "topology_artifact_prompt": None,
        "topology_artifact_raw_output": None,
        "topology_artifact_response_mode": None,
        "topology_artifact_fallback_reason": None,
        "sketch_prompt": None,
        "sketch_raw_output": None,
        "original_sketch": None,
        "reviewed_sketch": None,
        "deterministically_repaired_sketch": None,
        "prompted_repaired_sketch": None,
        "repaired_sketch": None,
        "probe_graph": None,
        "probe_validation": None,
        "initial_graph": None,
        "repaired_graph": None,
        "final_graph": None,
        "validation": None,
    }
    executed_stages: list[str] = []
    if _should_use_sketch(
        current_model=current_model,
        instruction=instruction,
        llm_caller=llm_caller,
        use_sketch=use_sketch,
    ):
        executed_stages.append("Sketch Planner")
        keyword_hints, _, _, sketch, sketch_repair, sketch_artifacts = _generate_activity_sketch(
            process_text,
            sketch_llm_caller=sketch_llm_caller,
            use_sketch_review_agent=use_sketch_review_agent,
            use_prompted_sketch_repair_agent=use_prompted_sketch_repair_agent,
            use_topology_artifact_guidance=use_topology_artifact_guidance,
        )
        stage_artifacts.update(sketch_artifacts)
        if use_sketch_review_agent:
            executed_stages.append("Sketch Review Agent")
        executed_stages.append("Sketch Repair")
        if use_prompted_sketch_repair_agent:
            executed_stages.append("Prompted Sketch Repair")

    prompt = build_activity_prompt(
        process_text=process_text,
        current_model=clean_current,
        refinement_instruction=instruction,
        activity_sketch=sketch,
    )

    caller = llm_caller if llm_caller is not None else _default_activity_llm_caller
    executed_stages.append("Graph Realizer")
    raw_output = caller(prompt)
    parsed = _parse_and_validate_activity_graph_json(raw_output)
    stage_artifacts["initial_graph"] = parsed
    sketch_alignment = validate_graph_against_sketch(sketch, parsed) if sketch is not None else None
    semantic_analysis = analyze_semantic_graph(parsed, sketch=sketch, keyword_hints=keyword_hints)

    if use_graph_repair_agent:
        topology_report = analyze_activity_graph(parsed)
        should_repair = bool(
            topology_report.get("issues")
            or (sketch_alignment or {}).get("issues")
            or (semantic_analysis or {}).get("issues")
        )
        if should_repair:
            repair_prompt = build_activity_graph_repair_prompt(
                process_text,
                activity_graph=parsed,
                topology_report=topology_report,
                sketch_alignment=sketch_alignment,
                semantic_analysis=semantic_analysis,
                activity_sketch=sketch,
            )
            repaired_raw_output = caller(repair_prompt)
            parsed = _parse_and_validate_activity_graph_json(repaired_raw_output)
            raw_output = repaired_raw_output
            prompt = repair_prompt
            executed_stages.append("Graph Repair Agent")
            stage_artifacts["repaired_graph"] = parsed
            sketch_alignment = validate_graph_against_sketch(sketch, parsed) if sketch is not None else None
            semantic_analysis = analyze_semantic_graph(parsed, sketch=sketch, keyword_hints=keyword_hints)

    executed_stages.append("Validation")
    stage_artifacts["final_graph"] = parsed
    stage_artifacts["validation"] = {
        "sketch_alignment": sketch_alignment,
        "semantic_analysis": semantic_analysis,
        "topology_report": analyze_activity_graph(parsed),
    }

    if sketch is not None:
        _log_sketch_realization_debug(
            keyword_hints or {},
            sketch,
            parsed,
            sketch_alignment,
            semantic_analysis,
        )
    stage_artifacts["executed_stages"] = executed_stages
    return keyword_hints, sketch, sketch_repair, sketch_alignment, semantic_analysis, prompt, raw_output, parsed, stage_artifacts


def debug_model_activity(
    process_text: str,
    current_model: Optional[dict] = None,
    instruction: Optional[str] = None,
    *,
    llm_caller: Optional[Callable[[str], str]] = None,
    sketch_llm_caller: Optional[Callable[[str], str]] = None,
    use_sketch: Optional[bool] = None,
    pipeline_profile: PipelineProfile = "stable",
    enable_sketch_review_agent: Optional[bool] = None,
    enable_prompted_sketch_repair_agent: Optional[bool] = None,
    enable_graph_repair_agent: Optional[bool] = None,
    use_topology_artifact_guidance: bool = False,
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
    if pipeline_profile == "semantic_deterministic":
        if current_model is not None or instruction is not None:
            raise ValueError("pipeline_profile='semantic_deterministic' does not yet support refinement inputs")
        result = debug_model_activity_with_semantic_deterministic_profile(process_text)
        result["pipeline_config"]["pipeline_profile"] = pipeline_profile
        return result

    pipeline_config = resolve_pipeline_config(
        pipeline_profile=pipeline_profile,
        enable_sketch_review_agent=enable_sketch_review_agent,
        enable_prompted_sketch_repair_agent=enable_prompted_sketch_repair_agent,
        enable_graph_repair_agent=enable_graph_repair_agent,
    )
    keyword_hints, sketch, sketch_repair, sketch_alignment, semantic_analysis, prompt, raw_output, parsed, stage_artifacts = _activity_llm_roundtrip(
        process_text,
        current_model=current_model,
        instruction=instruction,
        llm_caller=llm_caller,
        sketch_llm_caller=sketch_llm_caller,
        use_sketch=use_sketch,
        use_sketch_review_agent=pipeline_config["enable_sketch_review_agent"],
        use_prompted_sketch_repair_agent=pipeline_config["enable_prompted_sketch_repair_agent"],
        use_graph_repair_agent=pipeline_config["enable_graph_repair_agent"],
        use_topology_artifact_guidance=use_topology_artifact_guidance,
    )
    result = _build_debug_result(
        prompt,
        raw_output,
        parsed,
        keyword_hints=keyword_hints,
        sketch=sketch,
        sketch_repair=sketch_repair,
        sketch_alignment=sketch_alignment,
        semantic_analysis=semantic_analysis,
    )
    result["stage_artifacts"] = stage_artifacts
    result["executed_stages"] = stage_artifacts.get("executed_stages", [])
    result["pipeline_config"] = pipeline_config
    result["pipeline_config"]["use_topology_artifact_guidance"] = use_topology_artifact_guidance
    return result


def debug_model_activity_with_experimental_compiler(
    process_text: str,
    *,
    sketch_llm_caller: Optional[Callable[[str], str]] = None,
    use_sketch_review_agent: bool = False,
    use_prompted_sketch_repair_agent: bool = False,
    use_topology_artifact_guidance: bool = False,
) -> ActivityDebugResult:
    """
    Experimental path:
    ProcessText -> Sketch Planner -> optional Sketch Review -> Sketch Repair
    -> Deterministic Compiler -> ActivityGraph.

    This path intentionally bypasses the Graph Realizer and Graph Repair Agent
    so experiments can isolate whether topology failures originate from
    sketch insufficiency or from LLM-based realization drift.
    """
    keyword_hints, sketch_prompt, sketch_raw_output, sketch, sketch_repair, sketch_artifacts = _generate_activity_sketch(
        process_text,
        sketch_llm_caller=sketch_llm_caller,
        use_sketch_review_agent=use_sketch_review_agent,
        use_prompted_sketch_repair_agent=use_prompted_sketch_repair_agent,
        use_topology_artifact_guidance=use_topology_artifact_guidance,
    )
    parsed = compile_activity_sketch(sketch)
    sketch_alignment = validate_graph_against_sketch(sketch, parsed)
    semantic_analysis = analyze_semantic_graph(parsed, sketch=sketch, keyword_hints=keyword_hints)
    stage_artifacts = {
        "topology_artifact": sketch_artifacts.get("topology_artifact"),
        "topology_artifact_prompt": sketch_artifacts.get("topology_artifact_prompt"),
        "topology_artifact_raw_output": sketch_artifacts.get("topology_artifact_raw_output"),
        "topology_artifact_response_mode": sketch_artifacts.get("topology_artifact_response_mode"),
        "topology_artifact_fallback_reason": sketch_artifacts.get("topology_artifact_fallback_reason"),
        "sketch_prompt": sketch_artifacts.get("sketch_prompt"),
        "sketch_raw_output": sketch_artifacts.get("sketch_raw_output"),
        "original_sketch": sketch_artifacts.get("original_sketch"),
        "reviewed_sketch": sketch_artifacts.get("reviewed_sketch"),
        "deterministically_repaired_sketch": sketch_artifacts.get("deterministically_repaired_sketch"),
        "prompted_repaired_sketch": sketch_artifacts.get("prompted_repaired_sketch"),
        "repaired_sketch": sketch_artifacts.get("repaired_sketch"),
        "probe_graph": sketch_artifacts.get("probe_graph"),
        "probe_validation": sketch_artifacts.get("probe_validation"),
        "initial_graph": parsed,
        "repaired_graph": None,
        "final_graph": parsed,
        "validation": {
            "sketch_alignment": sketch_alignment,
            "semantic_analysis": semantic_analysis,
            "topology_report": analyze_activity_graph(parsed),
        },
        "executed_stages": [
            "Sketch Planner",
            *(
                ["Sketch Review Agent"]
                if use_sketch_review_agent
                else []
            ),
            "Sketch Repair",
            *(
                ["Prompted Sketch Repair"]
                if use_prompted_sketch_repair_agent
                else []
            ),
            "Deterministic Compiler",
            "Validation",
        ],
    }
    result = _build_debug_result(
        sketch_prompt,
        json.dumps(parsed, ensure_ascii=False),
        parsed,
        keyword_hints=keyword_hints,
        sketch=sketch,
        sketch_repair=sketch_repair,
        sketch_alignment=sketch_alignment,
        semantic_analysis=semantic_analysis,
    )
    result["sketch_raw_response"] = sketch_raw_output
    result["stage_artifacts"] = stage_artifacts
    result["executed_stages"] = stage_artifacts["executed_stages"]
    result["pipeline_config"] = {
        "pipeline_profile": "experimental_compiler",
        "enable_sketch_review_agent": use_sketch_review_agent,
        "enable_prompted_sketch_repair_agent": use_prompted_sketch_repair_agent,
        "enable_graph_repair_agent": False,
        "use_topology_artifact_guidance": use_topology_artifact_guidance,
    }
    return result


def debug_model_activity_with_semantic_deterministic_profile(
    process_text: str,
) -> ActivityDebugResult:
    """
    Experimental production-style profile:
    ProcessText -> Topology Artifact -> Semantic Sketch Plan
    -> Deterministic Sketch Builder -> Sketch Repair
    -> Deterministic Compiler -> Validation.
    """
    topology_result = generate_topology_artifact(process_text)
    topology_artifact = topology_result["artifact"]
    semantic_result = generate_semantic_sketch_plan(
        process_text,
        topology_artifact=topology_artifact,
    )
    semantic_plan = semantic_result["artifact"]
    deterministic_sketch = compile_topology_and_semantics_to_activity_sketch(
        topology_artifact,
        semantic_plan,
    )
    repaired_sketch, sketch_repair = repair_activity_sketch(deterministic_sketch)
    parsed = compile_activity_sketch(repaired_sketch)
    keyword_hints = semantic_result["keyword_hints"]
    sketch_alignment = validate_graph_against_sketch(repaired_sketch, parsed)
    semantic_analysis = analyze_semantic_graph(parsed, sketch=repaired_sketch, keyword_hints=keyword_hints)
    stage_artifacts = {
        "topology_artifact": topology_artifact,
        "topology_artifact_prompt": topology_result.get("prompt"),
        "topology_artifact_raw_output": topology_result.get("raw_output"),
        "topology_artifact_response_mode": topology_result.get("response_mode"),
        "topology_artifact_fallback_reason": topology_result.get("fallback_reason"),
        "semantic_plan": semantic_plan,
        "semantic_prompt": semantic_result.get("prompt"),
        "semantic_raw_output": semantic_result.get("raw_output"),
        "semantic_response_mode": semantic_result.get("response_mode"),
        "semantic_fallback_reason": semantic_result.get("fallback_reason"),
        "sketch_prompt": semantic_result.get("prompt"),
        "sketch_raw_output": json.dumps(deterministic_sketch, ensure_ascii=False),
        "original_sketch": deterministic_sketch,
        "reviewed_sketch": None,
        "deterministically_repaired_sketch": repaired_sketch,
        "prompted_repaired_sketch": None,
        "repaired_sketch": repaired_sketch,
        "probe_graph": None,
        "probe_validation": None,
        "deterministic_sketch": deterministic_sketch,
        "compiled_activity_graph": parsed,
        "initial_graph": parsed,
        "repaired_graph": None,
        "final_graph": parsed,
        "validation": {
            "sketch_alignment": sketch_alignment,
            "semantic_analysis": semantic_analysis,
            "topology_report": analyze_activity_graph(parsed),
        },
        "executed_stages": [
            "Topology Artifact",
            "Semantic Planner",
            "Deterministic Sketch Builder",
            "Sketch Repair",
            "Deterministic Compiler",
            "Validation",
        ],
    }
    result = _build_debug_result(
        semantic_result["prompt"],
        json.dumps(parsed, ensure_ascii=False),
        parsed,
        keyword_hints=keyword_hints,
        sketch=repaired_sketch,
        sketch_repair=sketch_repair,
        sketch_alignment=sketch_alignment,
        semantic_analysis=semantic_analysis,
    )
    result["semantic_raw_response"] = semantic_result["raw_output"]
    result["stage_artifacts"] = stage_artifacts
    result["executed_stages"] = stage_artifacts["executed_stages"]
    result["pipeline_config"] = {
        "pipeline_profile": "semantic_deterministic",
        "enable_sketch_review_agent": False,
        "enable_prompted_sketch_repair_agent": False,
        "enable_graph_repair_agent": False,
        "use_topology_artifact_guidance": False,
        "use_semantic_sketch_builder": True,
    }
    return result


def model_activity_with_experimental_compiler(
    process_text: str,
    *,
    debug: bool = False,
    sketch_llm_caller: Optional[Callable[[str], str]] = None,
    use_sketch_review_agent: bool = False,
    use_prompted_sketch_repair_agent: bool = False,
    use_topology_artifact_guidance: bool = False,
) -> Union[dict, ActivityDebugResult]:
    result = debug_model_activity_with_experimental_compiler(
        process_text,
        sketch_llm_caller=sketch_llm_caller,
        use_sketch_review_agent=use_sketch_review_agent,
        use_prompted_sketch_repair_agent=use_prompted_sketch_repair_agent,
        use_topology_artifact_guidance=use_topology_artifact_guidance,
    )
    if debug:
        return result
    return result["parsed"]


def model_activity(
    process_text: str,
    current_model: Optional[dict] = None,
    instruction: Optional[str] = None,
    *,
    debug: bool = False,
    llm_caller: Optional[Callable[[str], str]] = None,
    sketch_llm_caller: Optional[Callable[[str], str]] = None,
    use_sketch: Optional[bool] = None,
    pipeline_profile: PipelineProfile = "stable",
    enable_sketch_review_agent: Optional[bool] = None,
    enable_prompted_sketch_repair_agent: Optional[bool] = None,
    enable_graph_repair_agent: Optional[bool] = None,
    use_topology_artifact_guidance: bool = False,
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
    if pipeline_profile == "semantic_deterministic":
        if current_model is not None or instruction is not None:
            raise ValueError("pipeline_profile='semantic_deterministic' does not yet support refinement inputs")
        result = debug_model_activity_with_semantic_deterministic_profile(process_text)
        _log_pipeline_execution(pipeline_profile, result.get("executed_stages") or [])
        if debug:
            return result
        return result["parsed"]

    pipeline_config = resolve_pipeline_config(
        pipeline_profile=pipeline_profile,
        enable_sketch_review_agent=enable_sketch_review_agent,
        enable_prompted_sketch_repair_agent=enable_prompted_sketch_repair_agent,
        enable_graph_repair_agent=enable_graph_repair_agent,
    )
    keyword_hints, sketch, sketch_repair, sketch_alignment, semantic_analysis, prompt, raw_output, parsed, stage_artifacts = _activity_llm_roundtrip(
        process_text,
        current_model=current_model,
        instruction=instruction,
        llm_caller=llm_caller,
        sketch_llm_caller=sketch_llm_caller,
        use_sketch=use_sketch,
        use_sketch_review_agent=pipeline_config["enable_sketch_review_agent"],
        use_prompted_sketch_repair_agent=pipeline_config["enable_prompted_sketch_repair_agent"],
        use_graph_repair_agent=pipeline_config["enable_graph_repair_agent"],
        use_topology_artifact_guidance=use_topology_artifact_guidance,
    )
    if debug:
        result = _build_debug_result(
            prompt,
            raw_output,
            parsed,
            keyword_hints=keyword_hints,
            sketch=sketch,
            sketch_repair=sketch_repair,
            sketch_alignment=sketch_alignment,
            semantic_analysis=semantic_analysis,
        )
        result["stage_artifacts"] = stage_artifacts
        result["executed_stages"] = stage_artifacts.get("executed_stages", [])
        result["pipeline_config"] = pipeline_config
        result["pipeline_config"]["use_topology_artifact_guidance"] = use_topology_artifact_guidance
        _log_pipeline_execution(pipeline_config["pipeline_profile"], result.get("executed_stages") or [])
        return result
    _log_pipeline_execution(pipeline_config["pipeline_profile"], stage_artifacts.get("executed_stages", []))
    return parsed


def generate_initial_candidates(
    process_text: str,
    n: int = 3,
    *,
    use_sketch: Optional[bool] = None,
    pipeline_profile: PipelineProfile = "stable",
    enable_sketch_review_agent: Optional[bool] = None,
    enable_prompted_sketch_repair_agent: Optional[bool] = None,
    enable_graph_repair_agent: Optional[bool] = None,
    use_topology_artifact_guidance: bool = False,
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
        models.append(
            model_activity(
                process_text=process_text,
                use_sketch=use_sketch,
                pipeline_profile=pipeline_profile,
                enable_sketch_review_agent=enable_sketch_review_agent,
                enable_prompted_sketch_repair_agent=enable_prompted_sketch_repair_agent,
                enable_graph_repair_agent=enable_graph_repair_agent,
                use_topology_artifact_guidance=use_topology_artifact_guidance,
            )
        )
    return models


def generate_and_convert_candidates(
    process_text: str,
    n: int = 3,
    *,
    project_id: str,
    use_sketch: Optional[bool] = None,
    pipeline_profile: PipelineProfile = "stable",
    enable_sketch_review_agent: Optional[bool] = None,
    enable_prompted_sketch_repair_agent: Optional[bool] = None,
    enable_graph_repair_agent: Optional[bool] = None,
    use_topology_artifact_guidance: bool = False,
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
    results: List[Dict[str, Any]] = []
    for i in range(1, n + 1):
        debug_bundle: Optional[ActivityDebugResult] = None
        if pipeline_profile == "semantic_deterministic":
            debug_bundle = model_activity(
                process_text=process_text,
                debug=True,
                use_sketch=use_sketch,
                pipeline_profile=pipeline_profile,
                enable_sketch_review_agent=enable_sketch_review_agent,
                enable_prompted_sketch_repair_agent=enable_prompted_sketch_repair_agent,
                enable_graph_repair_agent=enable_graph_repair_agent,
                use_topology_artifact_guidance=use_topology_artifact_guidance,
            )
            clean = debug_bundle["parsed"]
        else:
            clean = model_activity(
                process_text=process_text,
                use_sketch=use_sketch,
                pipeline_profile=pipeline_profile,
                enable_sketch_review_agent=enable_sketch_review_agent,
                enable_prompted_sketch_repair_agent=enable_prompted_sketch_repair_agent,
                enable_graph_repair_agent=enable_graph_repair_agent,
                use_topology_artifact_guidance=use_topology_artifact_guidance,
            )
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
        results.append({"clean": clean, "ai4mde": ai4mde, "debug_bundle": debug_bundle})
    return results


def generate_candidates_with_conversion(
    process_text: str,
    n: int = 3,
    *,
    project_id: str,
    use_sketch: Optional[bool] = None,
    pipeline_profile: PipelineProfile = "stable",
    enable_sketch_review_agent: Optional[bool] = None,
    enable_prompted_sketch_repair_agent: Optional[bool] = None,
    enable_graph_repair_agent: Optional[bool] = None,
    use_topology_artifact_guidance: bool = False,
    name_prefix: str = "Activity candidate",
    description_template: str = "Generated candidate {index} for interactive selection",
) -> List[Dict[str, Any]]:
    return generate_and_convert_candidates(
        process_text,
        n=n,
        project_id=project_id,
        use_sketch=use_sketch,
        pipeline_profile=pipeline_profile,
        enable_sketch_review_agent=enable_sketch_review_agent,
        enable_prompted_sketch_repair_agent=enable_prompted_sketch_repair_agent,
        enable_graph_repair_agent=enable_graph_repair_agent,
        use_topology_artifact_guidance=use_topology_artifact_guidance,
        name_prefix=name_prefix,
        description_template=description_template,
    )


def refine_activity_model(
    process_text: str,
    current_model: dict,
    refinement_instruction: str,
    *,
    project_id: Optional[str] = None,
    pipeline_profile: PipelineProfile = "stable",
    enable_sketch_review_agent: Optional[bool] = None,
    enable_prompted_sketch_repair_agent: Optional[bool] = None,
    enable_graph_repair_agent: Optional[bool] = None,
    use_topology_artifact_guidance: bool = False,
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
        pipeline_profile=pipeline_profile,
        enable_sketch_review_agent=enable_sketch_review_agent,
        enable_prompted_sketch_repair_agent=enable_prompted_sketch_repair_agent,
        enable_graph_repair_agent=enable_graph_repair_agent,
        use_topology_artifact_guidance=use_topology_artifact_guidance,
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
