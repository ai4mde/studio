from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import shutil
import tempfile
from typing import Any, Iterable, Mapping

from . import EVALUATOR_SCHEMA, EVALUATOR_VERSION, METHODOLOGY_VERSION
from .action import (
    ACTION_MODEL_NAME, ACTION_MODEL_REVISION, ACTION_SIMILARITY_THRESHOLD,
    COMPATIBILITY_FILENAME, COMPATIBILITY_VERSION, CONTEXT_SIMILARITY_TOLERANCE,
    REFERENCE_RELATIVE_DELTA, SentenceTransformerSimilarity, evaluate_actions,
)
from .adapters import (
    friedrich_reference_review_evidence, friedrich_reference_to_eval_graph,
    load_generated_graph,
)
from .core import AutomaticItem, sha256_file
from .flow import evaluate_flow
from .human_review import build_review_rows, build_sensitivity_results, write_review_csv
from .structure import evaluate_structure


CANDIDATE_FIELDS = (
    "case_id", "candidate_id", "generation_status", "attempt_count",
    "action_tp", "action_fp", "action_fn", "action_precision", "action_recall", "action_f1",
    "action_anchor_coverage", "flow_tp", "flow_fp", "flow_fn", "flow_precision",
    "flow_recall", "flow_f1", "flow_coverage", "flow_action_anchor_coverage",
    "flow_anchor_limited_count", "flow_anchor_limited_rate",
    "structure_tp", "structure_fp", "structure_fn", "structure_precision",
    "structure_recall", "structure_f1", "structure_component_coverage",
    "structure_region_coverage", "structure_anchor_coverage",
    "structure_anchor_limited_count", "structure_anchor_limited_rate", "unscorable_count",
)


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="windows-1252")


def _mean(values: Iterable[float]) -> float:
    values = tuple(values)
    return sum(values) / len(values) if values else 0.0


def _optional_mean(values: Iterable[float | None]) -> float | None:
    defined = tuple(value for value in values if value is not None)
    return sum(defined) / len(defined) if defined else None


def _metric(row: Mapping[str, Any], name: str) -> dict[str, float]:
    return {
        "precision": float(row[f"{name}_precision"]),
        "recall": float(row[f"{name}_recall"]),
        "f1": float(row[f"{name}_f1"]),
    }


def _validate_run_shape(
    config: Mapping[str, Any], generated_cases: Mapping[str, Mapping[str, Any]]
) -> None:
    case_ids = [str(case_id) for case_id in config["case_ids"]]
    expected_cases = int(config["expected_case_count"])
    candidates_per_case = int(config["candidates_per_case"])
    expected_candidates = int(config["expected_candidate_count"])
    if expected_cases <= 0 or candidates_per_case <= 0 or expected_candidates <= 0:
        raise ValueError("Expected run-shape counts must be positive")
    if expected_candidates != expected_cases * candidates_per_case:
        raise ValueError("Expected candidate count must equal cases times candidates per case")
    if len(case_ids) != expected_cases or len(set(case_ids)) != expected_cases:
        raise ValueError(
            f"Expected {expected_cases} unique configured cases, found {len(set(case_ids))}"
        )
    if set(generated_cases) != set(case_ids):
        raise ValueError("Generated manifest cases do not match configured cases")

    expected_ids = {f"candidate_{index}" for index in range(1, candidates_per_case + 1)}
    total = 0
    for case_id in case_ids:
        candidates = generated_cases[case_id].get("candidates")
        if not isinstance(candidates, list):
            raise ValueError(f"Generated case {case_id} has no candidate list")
        candidate_ids = [str(candidate.get("candidate_id") or "") for candidate in candidates]
        if len(candidates) != candidates_per_case:
            raise ValueError(
                f"Expected {candidates_per_case} candidates for case {case_id}, "
                f"found {len(candidates)}"
            )
        if len(set(candidate_ids)) != len(candidate_ids):
            raise ValueError(f"Duplicate candidate IDs for case {case_id}")
        if set(candidate_ids) != expected_ids:
            raise ValueError(
                f"Candidate IDs for case {case_id} must be {sorted(expected_ids)}, "
                f"found {sorted(candidate_ids)}"
            )
        failed = [
            candidate_id for candidate_id, candidate in zip(candidate_ids, candidates)
            if candidate.get("generation_status") != "success"
        ]
        if failed:
            raise ValueError(f"Frozen candidates are not successful for case {case_id}: {failed}")
        total += len(candidates)
    if total != expected_candidates:
        raise ValueError(f"Expected {expected_candidates} candidates, found {total}")


def _macro(rows: list[dict[str, Any]], metric: str) -> dict[str, float]:
    by_case: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_case.setdefault(str(row["case_id"]), []).append(row)
    return {
        field: _mean(
            _mean(float(row[f"{metric}_{field}"]) for row in candidates
                  if row[f"{metric}_{field}"] is not None)
            for candidates in by_case.values()
            if any(row[f"{metric}_{field}"] is not None for row in candidates)
        )
        for field in ("precision", "recall", "f1")
    }


def _write_csv(path: Path, fields: Iterable[str], rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(fields))
        writer.writeheader()
        writer.writerows(rows)


def run(config_path: Path, output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise ValueError(f"Output directory already exists: {output_dir}")
    config = _json(config_path)
    if config.get("methodology_version") != METHODOLOGY_VERSION:
        raise ValueError("Validation config methodology version does not match the evaluator")
    if config.get("evaluator_version") != EVALUATOR_VERSION:
        raise ValueError("Validation config evaluator version does not match the evaluator")
    source_path = Path(config["source_manifest"])
    generated_path = Path(config["generated_manifest"])
    source = _json(source_path)
    generated = _json(generated_path)
    selected = set(config["case_ids"])
    source_cases = {
        str(case["case_id"]): case for case in source["cases"]
        if str(case["case_id"]) in selected
    }
    generated_cases = {
        str(case["case_id"]): case for case in generated["cases"]
        if str(case["case_id"]) in selected
    }
    if set(source_cases) != selected or set(generated_cases) != selected:
        raise ValueError("Frozen preflight manifests do not contain exactly the selected cases")
    _validate_run_shape(config, generated_cases)

    similarity = SentenceTransformerSimilarity(
        ACTION_MODEL_NAME, ACTION_MODEL_REVISION, str(config["model_cache"])
    )
    rows: list[dict[str, Any]] = []
    items: list[AutomaticItem] = []
    for case_id in config["case_ids"]:
        source_case = source_cases[case_id]
        reference = friedrich_reference_to_eval_graph(source_case["reference_model_path"])
        source_text = _text(Path(source_case["process_text_path"]))
        reference_evidence = friedrich_reference_review_evidence(source_case["reference_model_path"])
        candidates = generated_cases[case_id]["candidates"]
        for candidate in candidates:
            if candidate.get("generation_status") != "success":
                continue
            generated_graph = load_generated_graph(candidate["generated_model_path"])
            candidate_id = str(candidate["candidate_id"])
            action = evaluate_actions(
                case_id, candidate_id, reference, generated_graph, similarity,
                ACTION_SIMILARITY_THRESHOLD, source_text=source_text,
                reference_review_evidence=reference_evidence,
            )
            flow = evaluate_flow(case_id, candidate_id, reference, generated_graph, action)
            structure = evaluate_structure(case_id, candidate_id, reference, generated_graph, action)
            action_metrics = action.counts if action.metric_defined else None
            flow_metrics = flow.counts if flow.metric_defined else None
            structure_metrics = structure.counts if structure.metric_defined else None
            action_anchor = (
                len(action.matches) /
                len([node for node in reference.nodes if node.type == "action"])
                if any(node.type == "action" for node in reference.nodes) else 1.0
            )
            rows.append({
                "case_id": case_id, "candidate_id": candidate_id,
                "generation_status": "success", "attempt_count": candidate.get("attempt_count", 1),
                "action_tp": action.counts.tp, "action_fp": action.counts.fp, "action_fn": action.counts.fn,
                "action_precision": action_metrics.precision if action_metrics else None,
                "action_recall": action_metrics.recall if action_metrics else None,
                "action_f1": action_metrics.f1 if action_metrics else None, "action_anchor_coverage": action_anchor,
                "flow_tp": flow.counts.tp, "flow_fp": flow.counts.fp, "flow_fn": flow.counts.fn,
                "flow_precision": flow_metrics.precision if flow_metrics else None,
                "flow_recall": flow_metrics.recall if flow_metrics else None,
                "flow_f1": flow_metrics.f1 if flow_metrics else None, "flow_coverage": flow.coverage,
                "flow_action_anchor_coverage": flow.action_anchor_coverage,
                "flow_anchor_limited_count": flow.review_pending_fact_count,
                "flow_anchor_limited_rate": flow.review_pending_fact_rate,
                "structure_tp": structure.counts.tp, "structure_fp": structure.counts.fp,
                "structure_fn": structure.counts.fn,
                "structure_precision": structure_metrics.precision if structure_metrics else None,
                "structure_recall": structure_metrics.recall if structure_metrics else None,
                "structure_f1": structure_metrics.f1 if structure_metrics else None,
                "structure_component_coverage": structure.component_coverage,
                "structure_region_coverage": structure.region_coverage,
                "structure_anchor_coverage": structure.action_anchor_coverage,
                "structure_anchor_limited_count": structure.anchor_limited_count,
                "structure_anchor_limited_rate": structure.anchor_limited_rate,
                "unscorable_count": len(flow.unscorable) + len(structure.unscorable),
            })
            items.extend(action.items)
            items.extend(flow.items)
            items.extend(structure.items)

    expected_candidates = int(config["expected_candidate_count"])
    if len(rows) != expected_candidates:
        raise ValueError(
            f"Expected {expected_candidates} evaluated candidates, found {len(rows)}"
        )
    review_rows = build_review_rows(items, int(config["review_seed"]))
    trigger_counts: dict[str, int] = {}
    for row in review_rows:
        for trigger in row["review_trigger"].split(";"):
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
    aggregate = {
        "schema_version": EVALUATOR_SCHEMA,
        "evaluator_version": EVALUATOR_VERSION,
        "methodology_version": METHODOLOGY_VERSION,
        "case_count": len(selected),
        "candidate_count": len(rows),
        "raw_automatic": {metric: _macro(rows, metric) for metric in ("action", "flow", "structure")},
        "coverage": {
            "action_anchor_coverage": _mean(row["action_anchor_coverage"] for row in rows),
            "flow_coverage": _mean(row["flow_coverage"] for row in rows),
            "flow_action_anchor_coverage": _mean(row["flow_action_anchor_coverage"] for row in rows),
            "structure_component_coverage": _optional_mean(
                row["structure_component_coverage"] for row in rows
            ),
            "structure_region_coverage": _optional_mean(
                row["structure_region_coverage"] for row in rows
            ),
            "structure_anchor_coverage": _mean(row["structure_anchor_coverage"] for row in rows),
        },
        "human_review": {
            "prepared_row_count": len(review_rows),
            "trigger_counts": dict(sorted(trigger_counts.items())),
        },
    }
    case_rows: list[dict[str, Any]] = []
    for case_id in config["case_ids"]:
        candidates = [row for row in rows if row["case_id"] == case_id]
        case_rows.append({
            "case_id": case_id,
            **{
                f"{metric}_{field}": _optional_mean(row[f"{metric}_{field}"] for row in candidates)
                for metric in ("action", "flow", "structure")
                for field in ("precision", "recall", "f1")
            },
        })

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent))
    try:
        _write_csv(temporary / "candidate_summary.csv", CANDIDATE_FIELDS, rows)
        _write_csv(temporary / "case_summary.csv", case_rows[0].keys(), case_rows)
        with (temporary / "automatic_items.jsonl").open("w", encoding="utf-8") as handle:
            for item in items:
                handle.write(json.dumps(item.to_dict(), ensure_ascii=True, sort_keys=True) + "\n")
        write_review_csv(temporary / "human_review.csv", review_rows)
        (temporary / "review_adjusted_sensitivity.json").write_text(
            json.dumps(build_sensitivity_results(rows, review_rows), indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        (temporary / "aggregate_summary.json").write_text(
            json.dumps(aggregate, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
        )
        provenance = {
            "schema_version": EVALUATOR_SCHEMA,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(),
            "evaluator_version": EVALUATOR_VERSION,
            "methodology": {
                "version": METHODOLOGY_VERSION,
                "path": str(Path(__file__).with_name("FINAL_EVALUATION_METHODOLOGY.md")),
                "sha256": sha256_file(Path(__file__).with_name("FINAL_EVALUATION_METHODOLOGY.md")),
            },
            "action": {
                "model": ACTION_MODEL_NAME, "model_revision": ACTION_MODEL_REVISION,
                "threshold": ACTION_SIMILARITY_THRESHOLD,
                "compatibility_version": COMPATIBILITY_VERSION,
                "compatibility_sha256": sha256_file(Path(__file__).with_name(COMPATIBILITY_FILENAME)),
                "reference_relative_delta": REFERENCE_RELATIVE_DELTA,
                "context_similarity_tolerance": CONTEXT_SIMILARITY_TOLERANCE,
                "version": "action-reference-relative-one-to-one/v2",
            },
            "flow_methodology_version": "semantic-strict-precedence/v1",
            "structure_region_schema_version": "hierarchical-region-partial-credit/v1",
            "human_review_schema_version": "targeted-review/v2",
            "source_manifest": {"path": str(source_path), "sha256": sha256_file(source_path)},
            "generated_manifest": {"path": str(generated_path), "sha256": sha256_file(generated_path)},
            "validation_config": {"path": str(config_path), "sha256": sha256_file(config_path)},
            "selected_case_ids": list(config["case_ids"]),
            "review_seed": config["review_seed"],
        }
        (temporary / "provenance.json").write_text(
            json.dumps(provenance, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
        )
        temporary.rename(output_dir)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return aggregate


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the frozen Friedrich V3 evaluator")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.config, args.output_dir), indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
