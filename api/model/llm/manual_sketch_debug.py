from __future__ import annotations

import argparse
import json
import os
import uuid
from collections import Counter
from statistics import mean
from typing import Any, Dict, Iterable, List

from .baseline_generator import generate_activity_model
from .pipeline_profiles import PipelineProfile
from .refinement_generator import debug_model_activity_with_experimental_compiler
from .topology_analysis import analyze_activity_graph


def _condition_label(use_sketch: bool) -> str:
    return "with_sketch" if use_sketch else "without_sketch"


def _read_process_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text.strip()
    if args.text_file:
        with open(args.text_file, "r", encoding="utf-8") as handle:
            return handle.read().strip()
    raise ValueError("Provide either --text or --text-file.")


def _format_ratio(realized: Any, expected: Any) -> str:
    return f"{realized}/{expected}"


def _summarize_run(bundle: Dict[str, Any], *, use_sketch: bool) -> Dict[str, Any]:
    graph = bundle["parsed"]
    sketch = bundle.get("sketch")
    sketch_repair = bundle.get("sketch_repair") or {"metrics": {}, "critical_defects": []}
    keyword_hints = bundle.get("keyword_hints") or {"flags": {}, "hints": []}
    alignment = bundle.get("sketch_alignment") or {"metrics": {}, "details": {}, "issues": []}
    semantic_analysis = bundle.get("semantic_analysis") or {"issues": [], "metrics": {}}
    topology = analyze_activity_graph(graph)

    alignment_metrics = alignment.get("metrics") or {}
    topology_metrics = topology.get("metrics") or {}
    nodes = graph.get("nodes") or []

    origin_step_ids = sorted(
        {
            str(node.get("origin_step_id", "")).strip()
            for node in nodes
            if isinstance(node, dict) and str(node.get("origin_step_id", "")).strip()
        }
    )
    origin_block_ids = sorted(
        {
            str(node.get("origin_block_id", "")).strip()
            for node in nodes
            if isinstance(node, dict) and str(node.get("origin_block_id", "")).strip()
        }
    )

    return {
        "use_sketch": use_sketch,
        "sketch": sketch,
        "keyword_hints": keyword_hints,
        "graph": graph,
        "sketch_repair": sketch_repair,
        "alignment": alignment,
        "semantic_analysis": semantic_analysis,
        "topology": topology,
        "planner_binding_strength": alignment_metrics.get("planner_binding_strength", "weak"),
        "traceability_coverage": float(alignment_metrics.get("traceability_coverage", 0.0)),
        "resolved_by_origin_step_id": int(alignment_metrics.get("resolved_by_origin_step_id", 0)),
        "resolved_by_name_fallback": int(alignment_metrics.get("resolved_by_name_fallback", 0)),
        "unresolved_step_ids": alignment_metrics.get("unresolved_step_ids", []),
        "unresolved_block_ids": alignment_metrics.get("unresolved_block_ids", []),
        "expected_reconnects": int(alignment_metrics.get("expected_reconnects", 0)),
        "realized_reconnects": int(alignment_metrics.get("realized_reconnects", 0)),
        "expected_loop_backs": int(alignment_metrics.get("expected_loop_backs", 0)),
        "realized_loop_backs": int(alignment_metrics.get("realized_loop_backs", 0)),
        "expected_merges": int(alignment_metrics.get("expected_merges", 0)),
        "realized_merges": int(alignment_metrics.get("realized_merges", 0)),
        "topology_issues": topology.get("issues", []),
        "topology_summary": topology.get("summary", ""),
        "node_count": int(topology_metrics.get("node_count", len(nodes))),
        "edge_count": int(topology_metrics.get("edge_count", len(graph.get("edges") or []))),
        "decision_count": int(topology_metrics.get("decision_count", 0)),
        "merge_count": int(topology_metrics.get("merge_count", 0)),
        "fork_count": int(topology_metrics.get("fork_count", 0)),
        "join_count": int(topology_metrics.get("join_count", 0)),
        "origin_step_ids": origin_step_ids,
        "origin_block_ids": origin_block_ids,
        "main_flow_resolution_modes": (alignment.get("details") or {}).get("main_flow_resolution_modes", {}),
        "keyword_flags": keyword_hints.get("flags", {}),
        "semantic_issue_codes": [issue.get("code") for issue in semantic_analysis.get("issues", [])],
        "semantic_warning_count": int((semantic_analysis.get("metrics") or {}).get("warning_count", 0)),
        "semantic_error_count": int((semantic_analysis.get("metrics") or {}).get("error_count", 0)),
        "sketch_repair_metrics": sketch_repair.get("metrics", {}),
        "sketch_repair_critical_defects": sketch_repair.get("critical_defects", []),
    }


def _print_run_summary(result: Dict[str, Any], *, run_index: int, total_runs: int) -> None:
    print(f"\n=== {_condition_label(result['use_sketch'])} run {run_index}/{total_runs} ===")
    print(
        "planner:"
        f" binding={result['planner_binding_strength']}"
        f" traceability={result['traceability_coverage']:.2f}"
        f" origin_resolved={result['resolved_by_origin_step_id']}"
        f" name_fallback={result['resolved_by_name_fallback']}"
    )
    print(f"keyword_flags: {result['keyword_flags']}")
    print(
        "repair:"
        f" invalid_refs={result['sketch_repair_metrics'].get('invalid_reference_count', 0)}"
        f" reconnects={result['sketch_repair_metrics'].get('reconnect_repair_count', 0)}"
        f" merges={result['sketch_repair_metrics'].get('merge_normalization_count', 0)}"
        f" dead_ends={result['sketch_repair_metrics'].get('dead_end_repair_count', 0)}"
        f" retry={result['sketch_repair_metrics'].get('planner_retry_triggered', False)}"
    )
    print(
        "topology:"
        f" nodes={result['node_count']}"
        f" edges={result['edge_count']}"
        f" decisions={result['decision_count']}"
        f" merges={result['merge_count']}"
        f" forks={result['fork_count']}"
        f" joins={result['join_count']}"
    )
    print(
        "plan_obedience:"
        f" reconnects={_format_ratio(result['realized_reconnects'], result['expected_reconnects'])}"
        f" loop_backs={_format_ratio(result['realized_loop_backs'], result['expected_loop_backs'])}"
        f" closures={_format_ratio(result['realized_merges'], result['expected_merges'])}"
    )
    print(
        "semantic:"
        f" warnings={result['semantic_warning_count']}"
        f" errors={result['semantic_error_count']}"
        f" issues={result['semantic_issue_codes']}"
    )
    print(
        "traceability:"
        f" origin_step_ids={result['origin_step_ids']}"
        f" origin_block_ids={result['origin_block_ids']}"
    )
    if result["unresolved_step_ids"] or result["unresolved_block_ids"]:
        print(
            "unresolved:"
            f" step_ids={result['unresolved_step_ids']}"
            f" block_ids={result['unresolved_block_ids']}"
        )
    if result["topology_issues"]:
        print(f"issues: {', '.join(result['topology_issues'])}")
    else:
        print("issues: none")
    if result["sketch_repair_critical_defects"]:
        print(f"repair_critical_defects: {result['sketch_repair_critical_defects']}")


def _print_json_section(title: str, payload: Any) -> None:
    print(f"\n{title}:")
    if isinstance(payload, str):
        print(payload)
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))


def _print_stage_execution(bundle: Dict[str, Any]) -> None:
    for stage_name in bundle.get("executed_stages") or []:
        print(f"[{stage_name}]")


def _print_requested_artifacts(args: argparse.Namespace, bundle: Dict[str, Any]) -> None:
    stage_artifacts = bundle.get("stage_artifacts") or {}
    topology = analyze_activity_graph(bundle["parsed"])
    if args.show_prompt:
        _print_json_section("PROMPT", bundle["prompt"])
    if args.show_keywords and bundle.get("keyword_hints") is not None:
        _print_json_section("KEYWORD_HINTS", bundle["keyword_hints"])
    if args.show_sketch and stage_artifacts.get("original_sketch") is not None:
        _print_json_section("SKETCH_PLANNER_OUTPUT", stage_artifacts["original_sketch"])
    if args.show_sketch_review and stage_artifacts.get("reviewed_sketch") is not None:
        _print_json_section("SKETCH_AFTER_REVIEW_AGENT", stage_artifacts["reviewed_sketch"])
    if args.show_deterministic_sketch_repair and stage_artifacts.get("deterministically_repaired_sketch") is not None:
        _print_json_section("SKETCH_AFTER_DETERMINISTIC_REPAIR", stage_artifacts["deterministically_repaired_sketch"])
    if args.show_prompted_sketch_repair and stage_artifacts.get("prompted_repaired_sketch") is not None:
        _print_json_section("SKETCH_AFTER_PROMPTED_REPAIR", stage_artifacts["prompted_repaired_sketch"])
    if args.show_sketch_repair and stage_artifacts.get("repaired_sketch") is not None:
        _print_json_section("SKETCH_AFTER_REPAIR", stage_artifacts["repaired_sketch"])
    if args.show_graph and stage_artifacts.get("initial_graph") is not None:
        _print_json_section("INITIAL_GRAPH", stage_artifacts["initial_graph"])
    if args.show_graph_repair and stage_artifacts.get("repaired_graph") is not None:
        _print_json_section("GRAPH_AFTER_REPAIR_AGENT", stage_artifacts["repaired_graph"])
    if args.show_final_graph:
        _print_json_section("FINAL_GRAPH", stage_artifacts.get("final_graph", bundle["parsed"]))
    if args.show_alignment and bundle.get("sketch_alignment") is not None:
        _print_json_section("ALIGNMENT", bundle["sketch_alignment"])
    if args.show_semantic and bundle.get("semantic_analysis") is not None:
        _print_json_section("SEMANTIC_ANALYSIS", bundle["semantic_analysis"])
    if args.show_topology:
        _print_json_section("TOPOLOGY", topology)
    if args.show_diagnostics and stage_artifacts.get("validation") is not None:
        _print_json_section("VALIDATION_DIAGNOSTICS", stage_artifacts["validation"])


def _setup_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
    import django
    from django.apps import apps

    if not apps.ready:
        django.setup()


def _import_graph_into_ai4mde(graph: Dict[str, Any]) -> Dict[str, str | None]:
    _setup_django()

    from metadata.models import System
    from model.experiment_pipeline import (
        generate_session_id,
        import_to_ai4mde,
        resolve_experiment_project,
    )
    from .converter import convert_to_ai4mde

    session_id = generate_session_id()
    project = resolve_experiment_project(mode="baseline", session_id=session_id)
    system_id = str(uuid.uuid4())
    diagram_id = str(uuid.uuid4())

    systems_export = convert_to_ai4mde(
        clean_model=graph,
        system_id=system_id,
        diagram_id=diagram_id,
        name=f"{session_id}_Model_1",
        description=f"Manual sketch debug import for {session_id}",
        project_id=str(project.id),
    )
    import_to_ai4mde(project, systems_export)

    imported = System.objects.prefetch_related("diagrams").get(pk=system_id)
    imported_diagram = imported.diagrams.first()

    return {
        "project_id": str(project.id),
        "session_id": session_id,
        "system_id": str(imported.id),
        "diagram_id": str(imported_diagram.id) if imported_diagram is not None else None,
    }


def _print_import_summary(import_result: Dict[str, str | None]) -> None:
    print("\nIMPORT_RESULT:")
    print(f"project_id: {import_result['project_id']}")
    print(f"session_id: {import_result['session_id']}")
    print(f"system_id: {import_result['system_id']}")
    if import_result.get("diagram_id"):
        print(f"diagram_id: {import_result['diagram_id']}")
        print(f"ui_path: /diagram/{import_result['diagram_id']}")


def _aggregate_results(results: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    results = list(results)
    if not results:
        return {}

    binding_counts = Counter(result["planner_binding_strength"] for result in results)
    issue_counter = Counter(
        issue
        for result in results
        for issue in result["topology_issues"]
    )

    return {
        "runs": len(results),
        "average_traceability_coverage": mean(result["traceability_coverage"] for result in results),
        "average_node_count": mean(result["node_count"] for result in results),
        "average_edge_count": mean(result["edge_count"] for result in results),
        "binding_counts": dict(binding_counts),
        "issue_counts": dict(issue_counter),
        "clean_topology_runs": sum(1 for result in results if not result["topology_issues"]),
        "runs_with_origin_step_ids": sum(1 for result in results if result["origin_step_ids"]),
    }


def _print_aggregate_summary(results: List[Dict[str, Any]], *, use_sketch: bool) -> None:
    summary = _aggregate_results(results)
    print(f"\n=== {_condition_label(use_sketch)} summary ===")
    print(
        "summary:"
        f" runs={summary['runs']}"
        f" avg_traceability={summary['average_traceability_coverage']:.2f}"
        f" avg_nodes={summary['average_node_count']:.1f}"
        f" avg_edges={summary['average_edge_count']:.1f}"
        f" clean_topology_runs={summary['clean_topology_runs']}"
        f" runs_with_origin_step_ids={summary['runs_with_origin_step_ids']}"
    )
    print(f"binding_counts: {summary['binding_counts']}")
    print(f"issue_counts: {summary['issue_counts']}")


def _print_failure_summary(
    failures: List[Dict[str, Any]],
    *,
    use_sketch: bool,
    total_runs: int,
) -> None:
    if not failures:
        print(f"\n=== {_condition_label(use_sketch)} failures ===")
        print(f"failures: 0/{total_runs}")
        return

    print(f"\n=== {_condition_label(use_sketch)} failures ===")
    print(f"failures: {len(failures)}/{total_runs}")
    for failure in failures:
        print(
            f"run {failure['run_index']}: "
            f"{failure['error_type']}: {failure['message']}"
        )


def main() -> None:
    pipeline_profile_choices: tuple[PipelineProfile, ...] = (
        "stable",
        "sketch_review_only",
        "graph_repair_only",
        "both_agents",
    )
    parser = argparse.ArgumentParser(
        description="Manual debugger for the production baseline activity pipeline.",
    )
    parser.add_argument("--text", help="Process text to model.")
    parser.add_argument("--text-file", help="Path to a file containing the process text.")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs per condition.")
    parser.add_argument("--pipeline-profile", choices=pipeline_profile_choices, default="both_agents")
    parser.add_argument("--show-sketch", action="store_true", help="Print the original Sketch Planner output JSON.")
    parser.add_argument("--show-sketch-review", action="store_true", help="Print the sketch after Sketch Review Agent.")
    parser.add_argument("--show-review", dest="show_sketch_review", action="store_true", help="Alias for --show-sketch-review.")
    parser.add_argument("--show-deterministic-sketch-repair", action="store_true", help="Print the sketch after deterministic Sketch Repair.")
    parser.add_argument("--show-prompted-sketch-repair", action="store_true", help="Print the sketch after Prompted Sketch Repair.")
    parser.add_argument("--show-sketch-repair", action="store_true", help="Print the sketch after Sketch Repair.")
    parser.add_argument("--show-keywords", action="store_true", help="Print extracted keyword hints JSON.")
    parser.add_argument("--show-graph", action="store_true", help="Print the initial graph from Graph Realizer.")
    parser.add_argument("--show-graph-repair", action="store_true", help="Print the graph after Graph Repair Agent.")
    parser.add_argument("--show-final-graph", action="store_true", help="Print the final graph JSON.")
    parser.add_argument("--show-alignment", action="store_true", help="Print the alignment report JSON.")
    parser.add_argument("--show-semantic", action="store_true", help="Print the semantic analysis JSON.")
    parser.add_argument("--show-topology", action="store_true", help="Print the topology analysis JSON.")
    parser.add_argument("--show-diagnostics", action="store_true", help="Print final validation and diagnostics JSON.")
    parser.add_argument("--show-prompt", action="store_true", help="Print the rendered prompt.")
    parser.add_argument("--show-all-stages", action="store_true", help="Print all intermediate stage artifacts.")
    parser.add_argument(
        "--use-experimental-compiler",
        action="store_true",
        help="Bypass the Graph Realizer and compile the repaired ActivitySketch deterministically.",
    )
    parser.add_argument("--enable-sketch-review-agent", dest="enable_sketch_review_agent", action="store_true")
    parser.add_argument("--disable-sketch-review-agent", dest="enable_sketch_review_agent", action="store_false")
    parser.add_argument("--enable-prompted-sketch-repair-agent", dest="enable_prompted_sketch_repair_agent", action="store_true")
    parser.add_argument("--disable-prompted-sketch-repair-agent", dest="enable_prompted_sketch_repair_agent", action="store_false")
    parser.add_argument("--enable-graph-repair-agent", dest="enable_graph_repair_agent", action="store_true")
    parser.add_argument("--disable-graph-repair-agent", dest="enable_graph_repair_agent", action="store_false")
    parser.add_argument(
        "--import",
        dest="do_import",
        action="store_true",
        help="Import the exact generated graph from this run into AI4MDE.",
    )
    parser.set_defaults(
        enable_sketch_review_agent=None,
        enable_prompted_sketch_repair_agent=None,
        enable_graph_repair_agent=None,
    )
    args = parser.parse_args()

    process_text = _read_process_text(args)
    if args.do_import and args.runs != 1:
        raise ValueError("--import requires --runs 1 so the graph is generated exactly once.")
    if args.show_all_stages:
        args.show_sketch = True
        args.show_sketch_review = True
        args.show_deterministic_sketch_repair = True
        args.show_prompted_sketch_repair = True
        args.show_sketch_repair = True
        args.show_graph = True
        args.show_graph_repair = True
        args.show_final_graph = True
        args.show_alignment = True
        args.show_semantic = True
        args.show_topology = True
        args.show_diagnostics = True

    use_sketch_values = [True]

    for use_sketch in use_sketch_values:
        condition_results: List[Dict[str, Any]] = []
        failures: List[Dict[str, Any]] = []
        for run_index in range(1, args.runs + 1):
            try:
                if args.use_experimental_compiler:
                    bundle = debug_model_activity_with_experimental_compiler(
                        process_text,
                        use_sketch_review_agent=bool(args.enable_sketch_review_agent),
                        use_prompted_sketch_repair_agent=bool(args.enable_prompted_sketch_repair_agent),
                    )
                else:
                    bundle = generate_activity_model(
                        process_text,
                        debug=True,
                        use_sketch=use_sketch,
                        pipeline_profile=args.pipeline_profile,
                        enable_sketch_review_agent=args.enable_sketch_review_agent,
                        enable_prompted_sketch_repair_agent=args.enable_prompted_sketch_repair_agent,
                        enable_graph_repair_agent=args.enable_graph_repair_agent,
                    )
            except Exception as exc:
                failures.append(
                    {
                        "run_index": run_index,
                        "error_type": type(exc).__name__,
                        "message": str(exc),
                    }
                )
                print(
                    f"\n=== {_condition_label(use_sketch)} run {run_index}/{args.runs} ==="
                )
                print(f"run_failed: {type(exc).__name__}: {exc}")
                continue

            result = _summarize_run(bundle, use_sketch=use_sketch)
            condition_results.append(result)

            _print_run_summary(result, run_index=run_index, total_runs=args.runs)
            _print_stage_execution(bundle)
            _print_requested_artifacts(args, bundle)
            if args.do_import:
                _print_import_summary(_import_graph_into_ai4mde(bundle["parsed"]))

        if condition_results:
            _print_aggregate_summary(condition_results, use_sketch=use_sketch)
        else:
            print(f"\n=== {_condition_label(use_sketch)} summary ===")
            print(f"summary: runs=0/{args.runs} avg_traceability=0.00 avg_nodes=0.0 avg_edges=0.0 clean_topology_runs=0 runs_with_origin_step_ids=0")
            print("binding_counts: {}")
            print("issue_counts: {}")
        _print_failure_summary(failures, use_sketch=use_sketch, total_runs=args.runs)


if __name__ == "__main__":
    main()
