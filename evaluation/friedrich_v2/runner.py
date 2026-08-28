from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
from typing import Any, Iterable, Mapping, Sequence

from . import EVALUATOR_SCHEMA
from .action import (
    ACTION_MODEL_NAME,
    ACTION_MODEL_REVISION,
    ACTION_SIMILARITY_THRESHOLD,
    SentenceTransformerSimilarity,
    SimilarityProvider,
    evaluate_actions,
)
from .adapters import friedrich_reference_review_evidence, friedrich_reference_to_eval_graph, load_generated_graph
from .core import AutomaticItem, Counts, EvalGraph, canonical_json, evaluation_item_id, sha256_file
from .diagnostics import find_model_validity_diagnostics, find_redundant_control_nodes
from .flow import evaluate_flow
from .generation import load_small_validation_config
from .human_review import build_review_rows, load_review_csv, review_adjusted_counts, write_review_csv
from .manifests import (
    EXPECTED_CANDIDATE_COUNT,
    MAXIMUM_ATTEMPTS_PER_CANDIDATE,
    load_generated_manifest,
    load_source_manifest,
)
from .structure import evaluate_structure


METRICS = ("action", "flow", "structure")
SCORE_NAMES = ("precision", "recall", "f1")
CANDIDATE_SUMMARY_FIELDS = (
    "case_id", "candidate_id", "generation_status", "attempt_count", "failure_reason", "failure_stage",
    "action_tp", "action_fp", "action_fn", "action_precision", "action_recall", "action_f1",
    "flow_tp", "flow_fp", "flow_fn", "flow_precision", "flow_recall", "flow_f1", "flow_coverage",
    "flow_action_anchor_coverage", "flow_occurrence_ambiguous_fact_count", "flow_occurrence_ambiguous_fact_rate",
    "flow_contested_fact_count", "flow_contested_fact_rate", "flow_review_pending_fact_count", "flow_review_pending_fact_rate",
    "structure_tp", "structure_fp", "structure_fn", "structure_precision", "structure_recall", "structure_f1",
    "structure_coverage", "structure_anchor_coverage", "structure_anchor_limited_count", "structure_anchor_limited_rate",
    "validity_status", "validity_diagnostic_count", "redundant_control_node_count", "unscorable_count", "unscorable_status",
)
CASE_SUMMARY_FIELDS = (
    "case_id", "case_status", "candidate_count", "successful_candidate_count", "failed_candidate_count",
    *(f"{metric}_{score}_{stat}" for metric in METRICS for score in SCORE_NAMES for stat in ("mean", "min", "max")),
    *(f"secondary_successful_{metric}_{score}_{stat}" for metric in METRICS for score in SCORE_NAMES for stat in ("mean", "min", "max")),
    *(f"{metric}_{stat}" for metric in ("flow_coverage", "flow_action_anchor_coverage", "structure_coverage", "structure_anchor_coverage") for stat in ("mean", "min", "max")),
    *(f"secondary_successful_{metric}_{stat}" for metric in ("flow_coverage", "flow_action_anchor_coverage", "structure_coverage", "structure_anchor_coverage") for stat in ("mean", "min", "max")),
    *(f"redundant_control_node_count_{stat}" for stat in ("mean", "min", "max")),
    *(f"validity_diagnostic_count_{stat}" for stat in ("mean", "min", "max")),
    *(f"unscorable_count_{stat}" for stat in ("mean", "min", "max")),
)


@dataclass(frozen=True, slots=True)
class CandidateInput:
    candidate_id: str
    generation_status: str
    attempt_count: int
    attempts: tuple[Mapping[str, Any], ...]
    graph: EvalGraph | None = None
    failure_reason: str | None = None
    failure_stage: str | None = None


def _git_state() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, text=True
        ).stdout)
        return {"commit": commit, "dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "dirty": None}


def _candidate_summary_row(
    case_id: str,
    candidate_id: str,
    action: Any,
    flow: Any,
    structure: Any,
    redundant: int,
    validity: Any,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "case_id": case_id, "candidate_id": candidate_id, "generation_status": "success",
        "attempt_count": None, "failure_reason": None, "failure_stage": None,
    }
    for name, result in (("action", action), ("flow", flow), ("structure", structure)):
        row.update({f"{name}_{key}": value for key, value in result.counts.to_dict().items()})
    row["flow_coverage"] = flow.coverage
    row["flow_action_anchor_coverage"] = flow.action_anchor_coverage
    row["flow_occurrence_ambiguous_fact_count"] = flow.occurrence_ambiguous_fact_count
    row["flow_occurrence_ambiguous_fact_rate"] = flow.occurrence_ambiguous_fact_rate
    row["flow_contested_fact_count"] = flow.contested_fact_count
    row["flow_contested_fact_rate"] = flow.contested_fact_rate
    row["flow_review_pending_fact_count"] = flow.review_pending_fact_count
    row["flow_review_pending_fact_rate"] = flow.review_pending_fact_rate
    row["structure_coverage"] = structure.coverage
    row["structure_anchor_coverage"] = structure.anchor_coverage
    row["structure_anchor_limited_count"] = structure.anchor_limited_count
    row["structure_anchor_limited_rate"] = structure.anchor_limited_rate
    row["validity_status"] = validity.status
    row["validity_diagnostic_count"] = validity.diagnostic_count
    row["redundant_control_node_count"] = redundant
    row["unscorable_count"] = len(flow.unscorable) + len(structure.unscorable)
    row["unscorable_status"] = "unscorable" if row["unscorable_count"] else "scorable"
    return row


def _failed_candidate_summary_row(case_id: str, candidate: CandidateInput) -> dict[str, Any]:
    row: dict[str, Any] = {
        "case_id": case_id,
        "candidate_id": candidate.candidate_id,
        "generation_status": "failed",
        "attempt_count": candidate.attempt_count,
        "failure_reason": candidate.failure_reason,
        "failure_stage": candidate.failure_stage,
    }
    for metric in METRICS:
        for field in ("tp", "fp", "fn", "precision", "recall", "f1"):
            row[f"{metric}_{field}"] = None
    row.update({
        "flow_coverage": None,
        "flow_action_anchor_coverage": None,
        "flow_occurrence_ambiguous_fact_count": None, "flow_occurrence_ambiguous_fact_rate": None,
        "flow_contested_fact_count": None, "flow_contested_fact_rate": None,
        "flow_review_pending_fact_count": None, "flow_review_pending_fact_rate": None,
        "structure_coverage": None,
        "structure_anchor_coverage": None, "structure_anchor_limited_count": None,
        "structure_anchor_limited_rate": None, "validity_status": "not_applicable_generation_failure",
        "validity_diagnostic_count": None,
        "redundant_control_node_count": None,
        "unscorable_count": None,
        "unscorable_status": "not_applicable_generation_failure",
    })
    return row


def evaluate_case_candidates(
    case_id: str,
    reference_graph: EvalGraph,
    generated_candidates: Sequence[CandidateInput],
    similarity: SimilarityProvider,
    threshold: float,
    *,
    source_text: str | None = None,
    reference_review_evidence: Sequence[Mapping[str, Any]] = (),
) -> tuple[list[dict[str, Any]], list[AutomaticItem], int]:
    if len(generated_candidates) != EXPECTED_CANDIDATE_COUNT:
        raise ValueError(f"Case {case_id} requires exactly 3 generated candidates")
    candidate_ids = [candidate.candidate_id for candidate in generated_candidates]
    if len(set(candidate_ids)) != EXPECTED_CANDIDATE_COUNT:
        raise ValueError(f"Case {case_id} candidate IDs must be unique")
    rows: list[dict[str, Any]] = []
    items: list[AutomaticItem] = []
    control_node_count = 0
    for candidate in sorted(generated_candidates, key=lambda item: item.candidate_id):
        candidate_id = candidate.candidate_id
        if candidate.generation_status == "failed":
            rows.append(_failed_candidate_summary_row(case_id, candidate))
            items.append(AutomaticItem(
                case_id, candidate_id, "Generation",
                evaluation_item_id(case_id, candidate_id, "generation", "failed"), "FAILED",
                {
                    "generation_status": "failed", "attempt_count": candidate.attempt_count,
                    "failure_reason": candidate.failure_reason, "failure_stage": candidate.failure_stage,
                },
                {"attempts": list(candidate.attempts)},
                "No valid ActivityGraph was produced after the frozen maximum attempts.",
            ))
            continue
        if candidate.generation_status != "success" or candidate.graph is None:
            raise ValueError(f"Case {case_id} candidate {candidate_id} has inconsistent success data")
        generated_graph = candidate.graph
        control_node_count += sum(
            node.type in {"decision", "merge", "fork", "join"} for node in generated_graph.nodes
        )
        action = evaluate_actions(
            case_id, candidate_id, reference_graph, generated_graph, similarity, threshold,
            source_text=source_text, reference_review_evidence=reference_review_evidence,
        )
        flow = evaluate_flow(case_id, candidate_id, reference_graph, generated_graph, action)
        structure = evaluate_structure(case_id, candidate_id, reference_graph, generated_graph, action)
        candidates, diagnostic_items = find_redundant_control_nodes(
            case_id, candidate_id, generated_graph, action
        )
        validity = find_model_validity_diagnostics(
            case_id, candidate_id, generated_graph, reference_graph, action
        )
        high_confidence = sum(candidate.confidence == "High" for candidate in candidates)
        row = _candidate_summary_row(case_id, candidate_id, action, flow, structure, high_confidence, validity)
        row["attempt_count"] = candidate.attempt_count
        rows.append(row)
        items.extend((*action.items, *flow.items, *structure.items, *diagnostic_items, *validity.items))
    return rows, items, control_node_count


def _stats(values: Sequence[float | int]) -> dict[str, float]:
    if not values:
        raise ValueError("Cannot aggregate an empty value sequence")
    numeric = [float(value) for value in values]
    return {"mean": sum(numeric) / len(numeric), "min": min(numeric), "max": max(numeric)}


def build_case_summary(candidate_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in candidate_rows:
        grouped.setdefault(str(row["case_id"]), []).append(row)
    result: list[dict[str, Any]] = []
    for case_id, rows in sorted(grouped.items()):
        if len(rows) != EXPECTED_CANDIDATE_COUNT or len({row["candidate_id"] for row in rows}) != EXPECTED_CANDIDATE_COUNT:
            raise ValueError(f"Case {case_id} must have exactly 3 unique candidate rows")
        successful = [row for row in rows if row["generation_status"] == "success"]
        success_count = len(successful)
        case_status = "complete" if success_count == 3 else "failed" if success_count == 0 else "incomplete"
        summary: dict[str, Any] = {
            "case_id": case_id,
            "case_status": case_status,
            "candidate_count": len(rows),
            "successful_candidate_count": success_count,
            "failed_candidate_count": len(rows) - success_count,
        }
        for metric in METRICS:
            for score in SCORE_NAMES:
                primary = _stats([row[f"{metric}_{score}"] for row in successful]) if case_status == "complete" else {}
                secondary = _stats([row[f"{metric}_{score}"] for row in successful]) if successful else {}
                for stat in ("mean", "min", "max"):
                    summary[f"{metric}_{score}_{stat}"] = primary.get(stat)
                    summary[f"secondary_successful_{metric}_{score}_{stat}"] = secondary.get(stat)
        coverage_fallback = {
            "flow_action_anchor_coverage": "flow_coverage",
            "structure_anchor_coverage": "structure_coverage",
        }
        for metric in ("flow_coverage", "flow_action_anchor_coverage", "structure_coverage", "structure_anchor_coverage"):
            values = [row.get(metric, row[coverage_fallback.get(metric, metric)]) for row in successful]
            primary = _stats(values) if case_status == "complete" else {}
            secondary = _stats(values) if successful else {}
            for stat in ("mean", "min", "max"):
                summary[f"{metric}_{stat}"] = primary.get(stat)
                summary[f"secondary_successful_{metric}_{stat}"] = secondary.get(stat)
        for field in ("redundant_control_node_count", "validity_diagnostic_count", "unscorable_count"):
            values = [row.get(field, 0) for row in successful]
            stats = _stats(values) if case_status == "complete" else {}
            for stat in ("mean", "min", "max"):
                summary[f"{field}_{stat}"] = stats.get(stat)
        result.append(summary)
    return result


def _counts_from_row(row: Mapping[str, Any], metric: str) -> Counts:
    if row["generation_status"] != "success":
        raise ValueError("Generation failures do not have metric counts")
    return Counts(int(row[f"{metric}_tp"]), int(row[f"{metric}_fp"]), int(row[f"{metric}_fn"]))


def _sum_candidate_counts(rows: Iterable[Mapping[str, Any]], metric: str) -> Counts:
    counts = [_counts_from_row(row, metric) for row in rows]
    return Counts(sum(item.tp for item in counts), sum(item.fp for item in counts), sum(item.fn for item in counts))


def _reporting_block(
    candidate_rows: Sequence[Mapping[str, Any]], case_rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    successful_rows = [row for row in candidate_rows if row["generation_status"] == "success"]
    complete_cases = [row for row in case_rows if row["case_status"] == "complete"]
    primary: dict[str, Any] = {}
    variability: dict[str, Any] = {}
    micro: dict[str, Any] = {}
    for metric in METRICS:
        primary[metric] = {
            score: (
                sum(float(row[f"{metric}_{score}_mean"]) for row in complete_cases) / len(complete_cases)
                if complete_cases else None
            )
            for score in SCORE_NAMES
        }
        ranges = [
            float(row[f"{metric}_f1_max"]) - float(row[f"{metric}_f1_min"])
            for row in complete_cases
        ]
        variability[metric] = {
            "mean_within_case_f1_range": sum(ranges) / len(ranges) if ranges else None,
            "min_within_case_f1_range": min(ranges) if ranges else None,
            "max_within_case_f1_range": max(ranges) if ranges else None,
        }
        micro[metric] = _sum_candidate_counts(successful_rows, metric).to_dict() if successful_rows else None
    return {
        "primary_complete_case_macro": primary,
        "primary_macro_denominator": len(complete_cases),
        "complete_case_candidate_variability": variability,
        "secondary_successful_candidate_output_micro_aggregate": micro,
        "secondary_successful_candidate_denominator": len(successful_rows),
    }


def _review_adjusted_candidate_rows(
    candidate_rows: Sequence[Mapping[str, Any]], review_rows: Sequence[Mapping[str, str]]
) -> list[dict[str, Any]]:
    adjusted_rows: list[dict[str, Any]] = []
    for raw_row in candidate_rows:
        row = dict(raw_row)
        if raw_row["generation_status"] != "success":
            adjusted_rows.append(row)
            continue
        for metric in METRICS:
            counts = review_adjusted_counts(
                _counts_from_row(raw_row, metric), metric.title(), review_rows,
                case_id=str(raw_row["case_id"]), candidate_id=str(raw_row["candidate_id"]),
            )
            row.update({f"{metric}_{key}": value for key, value in counts.to_dict().items()})
        adjusted_rows.append(row)
    return adjusted_rows


def build_aggregate_summary(
    candidate_rows: Sequence[Mapping[str, Any]],
    case_rows: Sequence[Mapping[str, Any]],
    generated_control_node_count: int,
    prepared_review_rows: Sequence[Mapping[str, str]],
    supplied_review_rows: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    if not candidate_rows or not case_rows:
        raise ValueError("Cannot aggregate an empty cohort")
    successful_rows = [row for row in candidate_rows if row["generation_status"] == "success"]
    failed_rows = [row for row in candidate_rows if row["generation_status"] == "failed"]
    complete_cases = [row for row in case_rows if row["case_status"] == "complete"]
    incomplete_cases = [row for row in case_rows if row["case_status"] == "incomplete"]
    failed_cases = [row for row in case_rows if row["case_status"] == "failed"]
    attempt_breakdown = {
        f"succeeded_on_attempt_{index}": sum(
            row["generation_status"] == "success" and int(row["attempt_count"]) == index
            for row in candidate_rows
        )
        for index in range(1, MAXIMUM_ATTEMPTS_PER_CANDIDATE + 1)
    }
    attempt_breakdown["failed_after_attempt_3"] = len(failed_rows)
    aggregate: dict[str, Any] = {
        "schema_version": EVALUATOR_SCHEMA,
        "case_count": len(case_rows),
        "candidate_count": len(candidate_rows),
        "candidates_per_case": EXPECTED_CANDIDATE_COUNT,
        "reporting_unit": "Friedrich case",
        "candidate_observations_are_nested": True,
        "generation_reliability": {
            "expected_candidates": len(candidate_rows),
            "successful_candidates": len(successful_rows),
            "failed_candidates": len(failed_rows),
            "generation_success_rate": len(successful_rows) / len(candidate_rows),
            "total_cases": len(case_rows),
            "complete_cases": len(complete_cases),
            "incomplete_cases": len(incomplete_cases),
            "failed_cases": len(failed_cases),
            "complete_case_rate": len(complete_cases) / len(case_rows),
            "attempt_breakdown": attempt_breakdown,
        },
        "model_quality": _reporting_block(candidate_rows, case_rows),
    }
    aggregate["model_quality"]["coverage"] = {
        f"{metric}_complete_case_macro_mean": (
            sum(float(row[f"{metric}_coverage_mean"]) for row in complete_cases) / len(complete_cases)
            if complete_cases else None
        )
        for metric in ("flow", "structure")
    }
    aggregate["model_quality"]["coverage"].update({
        f"{metric}_secondary_successful_candidate_mean": (
            sum(float(row[f"{metric}_coverage"]) for row in successful_rows) / len(successful_rows)
            if successful_rows else None
        )
        for metric in ("flow", "structure")
    })
    for metric in ("flow_action_anchor", "structure_anchor"):
        aggregate["model_quality"]["coverage"][f"{metric}_complete_case_macro_mean"] = (
            sum(float(row[f"{metric}_coverage_mean"]) for row in complete_cases) / len(complete_cases)
            if complete_cases else None
        )
        aggregate["model_quality"]["coverage"][f"{metric}_secondary_successful_candidate_mean"] = (
            sum(float(row.get(f"{metric}_coverage", row[f"{metric.split('_')[0]}_coverage"])) for row in successful_rows) / len(successful_rows)
            if successful_rows else None
        )
    aggregate["model_validity"] = {
        "status": "issues_detected" if any(int(row.get("validity_diagnostic_count", 0)) for row in successful_rows) else "pass",
        "diagnostic_count": sum(int(row.get("validity_diagnostic_count", 0)) for row in successful_rows),
    }
    redundant = sum(int(row["redundant_control_node_count"]) for row in successful_rows)
    aggregate["redundant_control_nodes"] = {
        "count": redundant,
        "per_generated_control_node_rate": redundant / generated_control_node_count if generated_control_node_count else 0.0,
    }
    aggregate["human_review"] = {
        "prepared_item_count": len(prepared_review_rows),
        "category_counts": dict(Counter(
            row["final_explanation_category"] or row["explanation_category"]
            for row in supplied_review_rows
            if row["final_explanation_category"] or row["explanation_category"]
        )),
    }
    if supplied_review_rows:
        adjusted_candidates = _review_adjusted_candidate_rows(candidate_rows, supplied_review_rows)
        adjusted_cases = build_case_summary(adjusted_candidates)
        aggregate["review_adjusted_sensitivity"] = _reporting_block(adjusted_candidates, adjusted_cases)
    return aggregate


def _write_csv(path: Path, fields: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run(args: argparse.Namespace) -> None:
    output = Path(args.output_dir).resolve()
    if output.exists():
        raise FileExistsError(f"Immutable result run already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    source_path = Path(args.source_manifest).resolve()
    generated_path = Path(args.generated_manifest).resolve()
    source = load_source_manifest(source_path)
    selected_case_ids: list[str] | None = None
    validation_config: dict[str, Any] | None = None
    if args.small_validation_config:
        validation_config = load_small_validation_config(args.small_validation_config)
        frozen_evaluation = validation_config["evaluation"]
        supplied_action = (args.action_model, args.action_model_revision, args.action_threshold)
        frozen_action = (
            frozen_evaluation["action_model"],
            frozen_evaluation["action_model_revision"],
            frozen_evaluation["action_threshold"],
        )
        if supplied_action != frozen_action:
            raise ValueError("Action matcher arguments differ from the frozen small-validation configuration")
        if args.review_seed != frozen_evaluation["human_review_seed"]:
            raise ValueError("Human Review seed differs from the frozen small-validation configuration")
        selected_case_ids = validation_config["small_validation"]["case_ids"]
        selected = set(selected_case_ids)
        source["cases"] = [case for case in source["cases"] if case["case_id"] in selected]
        if len(source["cases"]) != len(selected):
            raise ValueError("Frozen small-validation cases do not all exist in the source manifest")
    case_ids = {case["case_id"] for case in source["cases"]}
    generated = load_generated_manifest(generated_path, case_ids)
    generated_by_id = {case["case_id"]: case for case in generated["cases"]}
    similarity = SentenceTransformerSimilarity(args.action_model, args.action_model_revision, args.model_cache)
    temp = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    candidate_rows: list[dict[str, Any]] = []
    all_items: list[AutomaticItem] = []
    generated_control_node_count = 0
    try:
        for source_case in sorted(source["cases"], key=lambda case: case["case_id"]):
            case_id = source_case["case_id"]
            reference_graph = friedrich_reference_to_eval_graph(source_case["reference_model_path"])
            process_path = Path(source_case["process_text_path"])
            try:
                source_text = process_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                source_text = process_path.read_text(encoding="cp1252")
            reference_evidence = friedrich_reference_review_evidence(source_case["reference_model_path"])
            generated_candidates = [
                CandidateInput(
                    candidate_id=candidate["candidate_id"],
                    generation_status=candidate["generation_status"],
                    attempt_count=candidate["attempt_count"],
                    attempts=tuple(candidate["attempts"]),
                    graph=(
                        load_generated_graph(candidate["generated_model_path"])
                        if candidate["generation_status"] == "success"
                        else None
                    ),
                    failure_reason=candidate["failure_reason"],
                    failure_stage=candidate["failure_stage"],
                )
                for candidate in generated_by_id[case_id]["candidates"]
            ]
            rows, items, control_count = evaluate_case_candidates(
                case_id, reference_graph, generated_candidates, similarity, args.action_threshold,
                source_text=source_text, reference_review_evidence=reference_evidence,
            )
            candidate_rows.extend(rows)
            all_items.extend(items)
            generated_control_node_count += control_count
        expected_outputs = len(source["cases"]) * EXPECTED_CANDIDATE_COUNT
        if len(candidate_rows) != expected_outputs:
            raise RuntimeError(f"Expected {expected_outputs} candidate evaluations, got {len(candidate_rows)}")
        case_rows = build_case_summary(candidate_rows)
        _write_csv(temp / "candidate_summary.csv", CANDIDATE_SUMMARY_FIELDS, candidate_rows)
        _write_csv(temp / "case_summary.csv", CASE_SUMMARY_FIELDS, case_rows)
        with (temp / "automatic_items.jsonl").open("w", encoding="utf-8") as handle:
            for item in all_items:
                handle.write(canonical_json(item.to_dict()) + "\n")
        prepared_review_rows = build_review_rows(all_items, args.review_seed)
        write_review_csv(temp / "human_review.csv", prepared_review_rows)
        supplied_review_rows = load_review_csv(args.review_file) if args.review_file else []
        aggregate = build_aggregate_summary(
            candidate_rows, case_rows, generated_control_node_count,
            prepared_review_rows, supplied_review_rows,
        )
        (temp / "aggregate_summary.json").write_text(
            json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        provenance = {
            "schema_version": EVALUATOR_SCHEMA,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "evaluator_snapshot": {
                "path": str((Path(__file__).resolve().parent / "evaluator_snapshot.json")),
                "sha256": sha256_file(Path(__file__).resolve().parent / "evaluator_snapshot.json"),
                "snapshot_id": json.loads(
                    (Path(__file__).resolve().parent / "evaluator_snapshot.json").read_text(encoding="utf-8")
                )["snapshot_id"],
                "status": "pre-commit evaluation snapshot; not yet final-frozen",
            },
            "source_manifest": {"path": str(source_path), "sha256": sha256_file(source_path)},
            "small_validation_config": (
                {
                    "path": str(Path(args.small_validation_config).resolve()),
                    "sha256": sha256_file(args.small_validation_config),
                    "selected_case_ids": selected_case_ids,
                }
                if validation_config is not None else None
            ),
            "generated_manifest": {
                "path": str(generated_path), "sha256": sha256_file(generated_path),
                "cohort_id": generated["cohort_id"], "cohort_stage": generated["cohort_stage"],
                "condition": generated["condition"], "human_selection": generated["human_selection"],
                "maximum_attempts_per_candidate": generated["maximum_attempts_per_candidate"],
                "run_integrity_status": generated["run_integrity_status"],
            },
            "evaluation_units": {
                "generation_unit": "case_id + candidate_id",
                "candidate_count": len(candidate_rows), "reporting_unit": "case_id",
                "case_count": len(case_rows),
            },
            "evaluator_git": _git_state(),
            "python": platform.python_version(),
            "action_matching": {
                "model": args.action_model, "model_revision": args.action_model_revision,
                "threshold": args.action_threshold, "cache_folder": str(Path(args.model_cache).resolve()),
            },
            "review_seed": args.review_seed,
        }
        (temp / "provenance.json").write_text(
            json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temp, output)
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Run an immutable three-candidate Friedrich V2 evaluation")
    result.add_argument("--source-manifest", required=True)
    result.add_argument("--generated-manifest", required=True)
    result.add_argument("--output-dir", required=True)
    result.add_argument("--small-validation-config")
    result.add_argument("--action-model", default=ACTION_MODEL_NAME)
    result.add_argument("--action-model-revision", default=ACTION_MODEL_REVISION)
    result.add_argument("--action-threshold", default=ACTION_SIMILARITY_THRESHOLD, type=float)
    result.add_argument("--model-cache", required=True)
    result.add_argument("--review-seed", type=int, default=20260827)
    result.add_argument("--review-file")
    return result


if __name__ == "__main__":
    run(parser().parse_args())
