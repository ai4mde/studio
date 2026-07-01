#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "api" / "model"
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from llm.refinement_generator import debug_model_activity
from llm.topology_analysis import analyze_activity_graph


ConditionConfig = Dict[str, Any]
RunRecord = Dict[str, Any]

CONDITIONS: Dict[str, ConditionConfig] = {
    "condition_A": {
        "label": "A",
        "name": "stable",
        "pipeline_profile": "stable",
        "enable_sketch_review_agent": None,
        "enable_graph_repair_agent": None,
    },
    "condition_B": {
        "label": "B",
        "name": "stable_plus_sketch_review",
        "pipeline_profile": "stable",
        "enable_sketch_review_agent": True,
        "enable_graph_repair_agent": None,
    },
    "condition_C": {
        "label": "C",
        "name": "stable_plus_graph_repair",
        "pipeline_profile": "stable",
        "enable_sketch_review_agent": None,
        "enable_graph_repair_agent": True,
    },
    "condition_D": {
        "label": "D",
        "name": "both_agents",
        "pipeline_profile": "both_agents",
        "enable_sketch_review_agent": None,
        "enable_graph_repair_agent": None,
    },
    "condition_E": {
        "label": "E",
        "name": "stable_plus_topology_guidance",
        "pipeline_profile": "stable",
        "enable_sketch_review_agent": None,
        "enable_graph_repair_agent": None,
        "use_topology_artifact_guidance": True,
    },
    "condition_F": {
        "label": "F",
        "name": "semantic_deterministic",
        "pipeline_profile": "semantic_deterministic",
        "enable_sketch_review_agent": None,
        "enable_graph_repair_agent": None,
    },
}


def _slugify(value: str) -> str:
    chars = [ch.lower() if ch.isalnum() else "_" for ch in value.strip()]
    slug = "".join(chars)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "workflow"


def _load_dataset(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict):
        items = payload.get("workflows")
        if items is None:
            raise ValueError("Dataset dict must contain a 'workflows' list.")
    elif isinstance(payload, list):
        items = payload
    else:
        raise ValueError("Dataset must be a list or a dict containing 'workflows'.")

    workflows: List[Dict[str, str]] = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, str):
            name = f"workflow_{index}"
            process_text = item
        elif isinstance(item, dict):
            process_text = str(item.get("process_text") or item.get("text") or "").strip()
            name = str(item.get("name") or item.get("id") or f"workflow_{index}").strip()
        else:
            raise ValueError(f"Unsupported workflow entry at index {index}: {type(item)!r}")

        if not process_text:
            raise ValueError(f"Workflow {name!r} is missing process text.")
        workflows.append({"name": name, "process_text": process_text})
    return workflows


def _count_issue_codes(issues: Iterable[Dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for issue in issues:
        code = str(issue.get("code") or "").strip()
        if code:
            counter[code] += 1
    return counter


def _run_condition(
    workflow: Dict[str, str],
    condition_key: str,
    condition: ConditionConfig,
    run_index: int,
    output_dir: Path,
) -> RunRecord:
    raw_path = output_dir / condition_key / f"{_slugify(workflow['name'])}_run_{run_index:02d}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        bundle = debug_model_activity(
            workflow["process_text"],
            pipeline_profile=condition["pipeline_profile"],
            enable_sketch_review_agent=condition["enable_sketch_review_agent"],
            enable_graph_repair_agent=condition["enable_graph_repair_agent"],
            use_topology_artifact_guidance=condition.get("use_topology_artifact_guidance", False),
        )
    except Exception as exc:
        debug_artifacts = getattr(exc, "debug_artifacts", None)
        failure_payload = {
            "workflow": workflow["name"],
            "process_text": workflow["process_text"],
            "condition": condition_key,
            "condition_name": condition["name"],
            "run_index": run_index,
            "failed": True,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "debug_artifacts": debug_artifacts,
        }
        with raw_path.open("w", encoding="utf-8") as handle:
            json.dump(failure_payload, handle, indent=2, ensure_ascii=False)
        return {
            "workflow": workflow["name"],
            "condition": condition_key,
            "condition_name": condition["name"],
            "run_index": run_index,
            "raw_path": str(raw_path),
            "failed": True,
            "clean_topology": False,
            "topology_issues": [],
            "topology_metrics": {},
            "topology_details": {},
            "semantic_issue_codes": [],
            "semantic_issue_counts": {},
            "alignment_issue_counts": {},
            "sketch_repair_metrics": {},
        }
    topology = analyze_activity_graph(bundle["parsed"])
    semantic = bundle.get("semantic_analysis") or {"issues": [], "metrics": {}}
    alignment = bundle.get("sketch_alignment") or {"issues": [], "metrics": {}, "details": {}}
    repair = bundle.get("sketch_repair") or {"metrics": {}, "critical_defects": []}

    semantic_issue_counts = _count_issue_codes(semantic.get("issues") or [])
    alignment_issue_counts = Counter(alignment.get("issues") or [])

    raw_payload = {
        "workflow": workflow["name"],
        "process_text": workflow["process_text"],
        "condition": condition_key,
        "condition_name": condition["name"],
        "run_index": run_index,
        "pipeline_config": bundle.get("pipeline_config"),
        "prompt": bundle.get("prompt"),
        "raw_response": bundle.get("raw_response"),
        "parsed": bundle.get("parsed"),
        "keyword_hints": bundle.get("keyword_hints"),
        "sketch": bundle.get("sketch"),
        "sketch_repair": repair,
        "sketch_alignment": alignment,
        "semantic_analysis": semantic,
        "topology": topology,
        "stage_artifacts": bundle.get("stage_artifacts"),
    }

    with raw_path.open("w", encoding="utf-8") as handle:
        json.dump(raw_payload, handle, indent=2, ensure_ascii=False)

    return {
        "workflow": workflow["name"],
        "condition": condition_key,
        "condition_name": condition["name"],
        "run_index": run_index,
        "raw_path": str(raw_path),
        "clean_topology": not topology.get("issues"),
        "topology_issues": topology.get("issues") or [],
        "topology_metrics": topology.get("metrics") or {},
        "topology_details": topology.get("details") or {},
        "semantic_issue_codes": sorted(semantic_issue_counts.elements()),
        "semantic_issue_counts": dict(semantic_issue_counts),
        "alignment_issue_counts": dict(alignment_issue_counts),
        "sketch_repair_metrics": repair.get("metrics") or {},
    }


def _build_summary_rows(records: List[RunRecord], runs: int) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str], List[RunRecord]] = defaultdict(list)
    for record in records:
        if record.get("failed"):
            continue
        grouped[(record["workflow"], record["condition"])].append(record)

    rows: List[Dict[str, Any]] = []
    for (workflow, condition), entries in sorted(grouped.items()):
        clean_runs = sum(1 for entry in entries if entry["clean_topology"])
        rows.append(
            {
                "workflow": workflow,
                "condition": condition,
                "runs": runs,
                "clean_topology_rate": f"{clean_runs / len(entries):.4f}",
                "clean_topology_runs": clean_runs,
            }
        )
    return rows


def _build_topology_metric_rows(records: List[RunRecord]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str], Counter[str]] = defaultdict(Counter)
    for record in records:
        if record.get("failed"):
            continue
        key = (record["workflow"], record["condition"])
        grouped[key]["clean_topology_runs"] += int(record["clean_topology"])
        grouped[key]["disconnected_nodes"] += int(record["topology_metrics"].get("disconnected_node_count", 0))
        grouped[key]["dead_end_nodes"] += int(record["topology_metrics"].get("dead_end_count", 0))
        for issue in record["topology_issues"]:
            grouped[key][issue] += 1
        for issue, count in record["semantic_issue_counts"].items():
            grouped[key][issue] += int(count)

    rows: List[Dict[str, Any]] = []
    for (workflow, condition), metrics in sorted(grouped.items()):
        for metric_name, metric_count in sorted(metrics.items()):
            rows.append(
                {
                    "workflow": workflow,
                    "condition": condition,
                    "metric_name": metric_name,
                    "metric_count": metric_count,
                }
            )
    return rows


def _build_diagnostics_rows(records: List[RunRecord]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for record in records:
        rows.append(
            {
                "workflow": record["workflow"],
                "condition": record["condition"],
                "run_index": record["run_index"],
                "failed": record.get("failed", False),
                "clean_topology": record["clean_topology"],
                "topology_issues": "|".join(record["topology_issues"]),
                "semantic_issue_codes": "|".join(record["semantic_issue_codes"]),
                "disconnected_nodes": "|".join(record["topology_details"].get("disconnected_nodes", [])),
                "dead_end_nodes": "|".join(record["topology_details"].get("dead_end_nodes", [])),
                "dangling_entry_nodes": "|".join(record["topology_details"].get("dangling_entry_nodes", [])),
                "raw_path": record["raw_path"],
            }
        )
    return rows


def _overall_condition_rates(summary_rows: List[Dict[str, Any]]) -> Dict[str, float]:
    grouped: Dict[str, List[float]] = defaultdict(list)
    for row in summary_rows:
        grouped[row["condition"]].append(float(row["clean_topology_rate"]))
    return {
        condition: sum(values) / len(values) if values else 0.0
        for condition, values in grouped.items()
    }


def _build_report(summary_rows: List[Dict[str, Any]], output_dir: Path, runs: int, dataset_path: Path) -> str:
    rates = _overall_condition_rates(summary_rows)
    ordered = sorted(rates.items(), key=lambda item: item[1], reverse=True)
    best_condition = ordered[0][0] if ordered else "n/a"
    stable_rate = rates.get("condition_A", 0.0)
    sketch_review_rate = rates.get("condition_B", 0.0)
    graph_repair_rate = rates.get("condition_C", 0.0)
    both_rate = rates.get("condition_D", 0.0)

    lines = [
        "# Agent Experiment Report",
        "",
        f"- Dataset: `{dataset_path}`",
        f"- Runs per condition: `{runs}`",
        f"- Output directory: `{output_dir}`",
        "",
        "## Aggregate Clean Topology Rates",
        "",
    ]

    for condition, rate in ordered:
        lines.append(f"- {condition}: {rate:.4f}")

    lines.extend(
        [
            "",
            "## Findings",
            "",
            f"- Highest clean topology rate: `{best_condition}` at `{rates.get(best_condition, 0.0):.4f}`.",
            (
                f"- Sketch Review Agent effect: baseline `condition_A={stable_rate:.4f}` vs "
                f"`condition_B={sketch_review_rate:.4f}`."
            ),
            (
                f"- Graph Repair Agent effect: baseline `condition_A={stable_rate:.4f}` vs "
                f"`condition_C={graph_repair_rate:.4f}`."
            ),
            (
                f"- Both agents together: `condition_D={both_rate:.4f}` "
                f"({'best overall' if best_condition == 'condition_D' else 'not best overall'})."
            ),
            "",
            "## Artifacts",
            "",
            "- `summary.csv`",
            "- `topology_metrics.csv`",
            "- `diagnostics.csv`",
            "- `raw/condition_A` through `raw/condition_D`",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run agent-condition UML activity experiments.")
    parser.add_argument("--dataset", required=True, help="Path to a workflow dataset JSON file.")
    parser.add_argument("--runs", type=int, default=10, help="Runs per condition for each workflow.")
    parser.add_argument("--output", required=True, help="Directory for raw outputs and reports.")
    parser.add_argument(
        "--conditions",
        help="Optional comma-separated condition keys to run, e.g. 'condition_A,condition_E'. Defaults to all conditions.",
    )
    args = parser.parse_args()

    if args.runs <= 0:
        raise ValueError("--runs must be positive")

    dataset_path = Path(args.dataset).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    raw_dir = output_dir / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    selected_conditions = CONDITIONS
    if args.conditions:
        requested_keys = [item.strip() for item in args.conditions.split(",") if item.strip()]
        unknown = [key for key in requested_keys if key not in CONDITIONS]
        if unknown:
            raise ValueError(f"Unknown condition keys: {', '.join(unknown)}")
        selected_conditions = {key: CONDITIONS[key] for key in requested_keys}

    workflows = _load_dataset(dataset_path)
    records: List[RunRecord] = []

    for workflow in workflows:
        for condition_key, condition in selected_conditions.items():
            for run_index in range(1, args.runs + 1):
                records.append(
                    _run_condition(
                        workflow,
                        condition_key,
                        condition,
                        run_index,
                        raw_dir,
                    )
                )

    summary_rows = _build_summary_rows(records, args.runs)
    topology_metric_rows = _build_topology_metric_rows(records)
    diagnostics_rows = _build_diagnostics_rows(records)
    report = _build_report(summary_rows, output_dir, args.runs, dataset_path)

    _write_csv(
        output_dir / "summary.csv",
        summary_rows,
        ["workflow", "condition", "runs", "clean_topology_rate", "clean_topology_runs"],
    )
    _write_csv(
        output_dir / "topology_metrics.csv",
        topology_metric_rows,
        ["workflow", "condition", "metric_name", "metric_count"],
    )
    _write_csv(
        output_dir / "diagnostics.csv",
        diagnostics_rows,
        [
            "workflow",
            "condition",
            "run_index",
            "failed",
            "clean_topology",
            "topology_issues",
            "semantic_issue_codes",
            "disconnected_nodes",
            "dead_end_nodes",
            "dangling_entry_nodes",
            "raw_path",
        ],
    )
    (output_dir / "experiment_report.md").write_text(report, encoding="utf-8")

    print(f"Saved experiment artifacts to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
