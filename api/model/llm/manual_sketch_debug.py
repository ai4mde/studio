from __future__ import annotations

import argparse
import json
from collections import Counter
from statistics import mean
from typing import Any, Dict, Iterable, List

from .refinement_generator import debug_model_activity
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


def _print_json_section(title: str, payload: Any) -> None:
    print(f"\n{title}:")
    if isinstance(payload, str):
        print(payload)
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lightweight manual sketch-generation debugger for planner influence inspection.",
    )
    parser.add_argument("--text", help="Process text to model.")
    parser.add_argument("--text-file", help="Path to a file containing the process text.")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs per condition.")
    parser.add_argument(
        "--mode",
        choices=("sketch", "no-sketch", "both"),
        default="sketch",
        help="Whether to run with sketch, without sketch, or both.",
    )
    parser.add_argument("--show-sketch", action="store_true", help="Print the planner output JSON.")
    parser.add_argument("--show-keywords", action="store_true", help="Print extracted keyword hints JSON.")
    parser.add_argument("--show-graph", action="store_true", help="Print the realized graph JSON.")
    parser.add_argument("--show-alignment", action="store_true", help="Print the alignment report JSON.")
    parser.add_argument("--show-semantic", action="store_true", help="Print the semantic analysis JSON.")
    parser.add_argument("--show-prompt", action="store_true", help="Print the rendered prompt.")
    args = parser.parse_args()

    process_text = _read_process_text(args)
    use_sketch_values = (
        [True] if args.mode == "sketch"
        else [False] if args.mode == "no-sketch"
        else [False, True]
    )

    for use_sketch in use_sketch_values:
        condition_results: List[Dict[str, Any]] = []
        for run_index in range(1, args.runs + 1):
            bundle = debug_model_activity(process_text, use_sketch=use_sketch)
            result = _summarize_run(bundle, use_sketch=use_sketch)
            condition_results.append(result)

            _print_run_summary(result, run_index=run_index, total_runs=args.runs)
            if args.show_prompt:
                _print_json_section("PROMPT", bundle["prompt"])
            if args.show_keywords and bundle.get("keyword_hints") is not None:
                _print_json_section("KEYWORD_HINTS", bundle["keyword_hints"])
            if args.show_sketch and bundle.get("sketch") is not None:
                _print_json_section("SKETCH", bundle["sketch"])
            if args.show_graph:
                _print_json_section("GRAPH", bundle["parsed"])
            if args.show_alignment and bundle.get("sketch_alignment") is not None:
                _print_json_section("ALIGNMENT", bundle["sketch_alignment"])
            if args.show_semantic and bundle.get("semantic_analysis") is not None:
                _print_json_section("SEMANTIC_ANALYSIS", bundle["semantic_analysis"])

        _print_aggregate_summary(condition_results, use_sketch=use_sketch)


if __name__ == "__main__":
    main()
