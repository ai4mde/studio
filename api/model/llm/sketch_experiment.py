from __future__ import annotations

import uuid
from collections import Counter
from statistics import mean
from typing import Any, Callable, Dict, List, Optional

from .converter import convert_to_ai4mde, validate_ai4mde_json
from .refinement_generator import debug_model_activity
from .topology_analysis import analyze_activity_graph


ExperimentEntry = Dict[str, Any]
ExperimentReport = Dict[str, Any]


def _classify_failure(error_text: str) -> str:
    lowered = error_text.lower()
    if "not valid json" in lowered:
        return "json_parse_failure"
    if "pydantic validation" in lowered:
        return "structural_validation_failure"
    if "semantic validation" in lowered:
        return "graph_validation_failure"
    if "failed to call llm" in lowered:
        return "llm_call_failure"
    return "generation_failure"


def _aggregate_condition(entries: List[ExperimentEntry]) -> Dict[str, Any]:
    successes = [entry for entry in entries if entry.get("success")]
    failures = [entry for entry in entries if not entry.get("success")]
    issue_counter: Counter[str] = Counter()
    for entry in successes:
        issue_counter.update(entry.get("issues") or [])
    for entry in failures:
        if entry.get("failure_type"):
            issue_counter.update([entry["failure_type"]])

    avg_nodes = mean([entry["metrics"]["node_count"] for entry in successes]) if successes else 0.0
    avg_edges = mean([entry["metrics"]["edge_count"] for entry in successes]) if successes else 0.0
    topology_clean_runs = sum(1 for entry in successes if not entry.get("issues"))

    return {
        "total_runs": len(entries),
        "success_count": len(successes),
        "failure_count": len(failures),
        "topology_clean_runs": topology_clean_runs,
        "topology_issue_runs": len(successes) - topology_clean_runs,
        "average_node_count": avg_nodes,
        "average_edge_count": avg_edges,
        "issue_counts": dict(issue_counter),
    }


def compare_sketch_generation(
    process_text: str,
    runs_per_condition: int = 10,
    *,
    llm_caller: Optional[Callable[[str], str]] = None,
    sketch_llm_caller: Optional[Callable[[str], str]] = None,
    include_debug_payloads: bool = False,
    project_id: Optional[str] = None,
) -> ExperimentReport:
    """
    Run the same generation request repeatedly with and without the sketch layer.

    The report focuses on topology-level observations rather than only
    parse/validation success.
    """
    if runs_per_condition <= 0:
        raise ValueError("runs_per_condition must be positive")

    entries: List[ExperimentEntry] = []

    for use_sketch in (False, True):
        for run_index in range(1, runs_per_condition + 1):
            entry: ExperimentEntry = {
                "run_id": f"{'with' if use_sketch else 'without'}_sketch_{run_index}",
                "use_sketch": use_sketch,
            }
            try:
                bundle = debug_model_activity(
                    process_text,
                    llm_caller=llm_caller,
                    sketch_llm_caller=sketch_llm_caller,
                    use_sketch=use_sketch,
                )
                graph = bundle["parsed"]
                topology = analyze_activity_graph(graph)

                entry.update(
                    {
                        "success": True,
                        "issues": topology["issues"],
                        "summary": topology["summary"],
                        "metrics": topology["metrics"],
                        "details": topology["details"],
                    }
                )

                if "sketch" in bundle:
                    entry["sketch"] = bundle["sketch"]

                if include_debug_payloads:
                    entry["prompt"] = bundle["prompt"]
                    entry["raw_response"] = bundle["raw_response"]

                if project_id:
                    try:
                        export = convert_to_ai4mde(
                            clean_model=graph,
                            system_id=str(uuid.uuid4()),
                            diagram_id=str(uuid.uuid4()),
                            name=f"Experiment {'With' if use_sketch else 'Without'} Sketch {run_index}",
                            description="Sketch comparison experiment",
                            project_id=project_id,
                        )
                        validate_ai4mde_json(export)
                        entry["converter_success"] = True
                        entry["converter_error"] = None
                    except Exception as exc:  # noqa: BLE001
                        entry["converter_success"] = False
                        entry["converter_error"] = str(exc)
            except Exception as exc:  # noqa: BLE001
                failure_text = str(exc)
                entry.update(
                    {
                        "success": False,
                        "issues": [],
                        "summary": failure_text,
                        "failure_type": _classify_failure(failure_text),
                        "error": failure_text,
                    }
                )
            entries.append(entry)

    without_entries = [entry for entry in entries if not entry["use_sketch"]]
    with_entries = [entry for entry in entries if entry["use_sketch"]]

    return {
        "process_text": process_text,
        "runs_per_condition": runs_per_condition,
        "entries": entries,
        "summary": {
            "without_sketch": _aggregate_condition(without_entries),
            "with_sketch": _aggregate_condition(with_entries),
        },
    }


__all__ = ["compare_sketch_generation", "ExperimentEntry", "ExperimentReport"]
