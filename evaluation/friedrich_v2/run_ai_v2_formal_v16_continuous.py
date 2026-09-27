#!/usr/bin/env python3
"""Frozen v1.6 continuous formal evaluation of the existing 40-by-3 cohort."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
from collections import Counter
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.friedrich_v2 import run_ai_v2_calibration as legacy  # noqa: E402
from evaluation.friedrich_v2 import run_ai_v2_calibration_v16_continuous as frozen  # noqa: E402
from evaluation.friedrich_v2 import run_ai_v2_holdout_v16_continuous as holdout  # noqa: E402

# This historical module supplies only the frozen cohort's independently
# checked 40-by-3 roster and input hashes. Its old scoring code is never used.
_legacy_prompt_binding = (legacy.PROMPT_PATH, legacy.PROMPT_VERSION)
from evaluation.friedrich_v2 import run_ai_v2_formal_v12 as cohort  # noqa: E402
legacy.PROMPT_PATH, legacy.PROMPT_VERSION = _legacy_prompt_binding


RESULTS_ROOT = ROOT / "evaluation/friedrich_v2/results"
COHORT_CONFIG = ROOT / "evaluation/friedrich_v2/config/final_frozen_40x3_20260910.json"
CASES = cohort.CASES
PAIRS = cohort.EXPECTED_PAIRS


def paths(run_dir: Path) -> dict[str, Path]:
    return {
        "manifest": run_dir / "ai_v16_formal_120_manifest.json",
        "slots": run_dir / "ai_v16_formal_120_slots.json",
        "results": run_dir / "ai_v16_formal_120_results.jsonl",
        "usage": run_dir / "ai_v16_formal_120_usage.csv",
        "scores": run_dir / "ai_v16_formal_120_scores.csv",
        "summary": run_dir / "ai_v16_formal_120_summary.json",
        "report": run_dir / "ai_v16_formal_120_report.md",
        "review": run_dir / "ai_v16_formal_120_review_flags.csv",
        "hashes": run_dir / "ai_v16_formal_120_hashes.json",
        "raw": run_dir / "raw_responses",
        "requests": run_dir / "request_records",
        "checkpoints": run_dir / "checkpoints",
    }


def resolve_run_dir(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if path.parent != RESULTS_ROOT.resolve() or not path.name.startswith("ai_v16_formal_120_"):
        raise ValueError("Run directory must be a new ai_v16_formal_120_* directory under results")
    return path


def verify_cohort() -> list[dict[str, Any]]:
    config = json.loads(COHORT_CONFIG.read_text(encoding="utf-8"))
    if tuple(config["case_ids"]) != CASES or len(CASES) != 40 or len(PAIRS) != 120:
        raise RuntimeError("Formal cohort configuration or roster differs")
    artifacts = cohort.validate_frozen_cohort()
    if len(artifacts) != 120 or [(a["case_id"], a["candidate_id"]) for a in artifacts] != list(PAIRS):
        raise RuntimeError("Formal frozen candidate identities differ")
    if any(sum(a["case_id"] == case_id for a in artifacts) != 3 for case_id in CASES):
        raise RuntimeError("Formal cohort is not exactly three candidates per case")
    return artifacts


def verify_binding(run_dir: Path, statuses: set[str]) -> tuple[dict, list[dict], str, str, dict]:
    p = paths(run_dir)
    manifest = json.loads(p["manifest"].read_text(encoding="utf-8"))
    if manifest["status"] not in statuses:
        raise RuntimeError(f"Formal run status disallows this command: {manifest['status']}")
    evaluator, developer, template, wrapper = holdout.verify_frozen()
    artifacts = verify_cohort()
    required = {
        "frozen_evaluator_manifest_sha256": legacy.sha256_file(holdout.FREEZE_PATH),
        "formal_runner_sha256": legacy.sha256_file(Path(__file__)),
        "cohort_config_sha256": legacy.sha256_file(COHORT_CONFIG),
        "cohort_run_manifest_sha256": legacy.sha256_file(cohort.COHORT_RUN_MANIFEST),
        "cohort_generated_manifest_sha256": legacy.sha256_file(cohort.COHORT_GENERATED_MANIFEST),
        "cohort_artifact_inventory_sha256": legacy.sha256_file(cohort.COHORT_ARTIFACT_INVENTORY),
        "prompt_sha256": evaluator["prompt_sha256"],
        "schema_sha256": evaluator["schema_sha256"],
        "continuous_contract_sha256": evaluator["continuous_contract_sha256"],
        "developer_prompt_sha256": evaluator["developer_prompt_sha256"],
        "user_template_sha256": evaluator["user_template_sha256"],
        "strict_schema_sha256": evaluator["strict_schema_sha256"],
        "model": evaluator["model"],
        "reasoning_effort": evaluator["reasoning_effort"],
        "temperature": evaluator["temperature"],
        "top_p": evaluator["top_p"],
        "seed": evaluator["seed"],
        "store": evaluator["store"],
        "independent_stateless_calls": evaluator["independent_stateless_calls"],
        "renderer": evaluator["renderer_identity"],
        "parser_validator": evaluator["parser_validator_identity"],
        "maximum_technical_retries_per_candidate": 1,
        "automatic_sdk_retries": 0,
        "candidate_input_components": frozen.INPUT_COMPONENTS,
        "candidates": artifacts,
    }
    for key, value in required.items():
        if manifest.get(key) != value:
            raise RuntimeError(f"Formal binding changed after preflight: {key}")
    return manifest, artifacts, developer, template, wrapper


def preflight(run_dir: Path) -> None:
    if run_dir.exists():
        raise FileExistsError(run_dir)
    evaluator, _, _, _ = holdout.verify_frozen()
    artifacts = verify_cohort()
    run_dir.mkdir(parents=False, exist_ok=False)
    p = paths(run_dir)
    manifest = {
        "status": "preflight_passed",
        "created_at_utc": holdout.now(),
        "run_kind": "formal_ai_v16_continuous_40x3",
        "frozen_evaluator_manifest_path": holdout.relative(holdout.FREEZE_PATH),
        "frozen_evaluator_manifest_sha256": legacy.sha256_file(holdout.FREEZE_PATH),
        "formal_runner_path": holdout.relative(Path(__file__)),
        "formal_runner_sha256": legacy.sha256_file(Path(__file__)),
        "cohort_config_path": holdout.relative(COHORT_CONFIG),
        "cohort_config_sha256": legacy.sha256_file(COHORT_CONFIG),
        "cohort_run_manifest_sha256": legacy.sha256_file(cohort.COHORT_RUN_MANIFEST),
        "cohort_generated_manifest_sha256": legacy.sha256_file(cohort.COHORT_GENERATED_MANIFEST),
        "cohort_artifact_inventory_sha256": legacy.sha256_file(cohort.COHORT_ARTIFACT_INVENTORY),
        "case_count": 40, "candidates_per_case": 3, "candidate_count": 120,
        "case_ids": list(CASES), "candidates": artifacts,
        "prompt_version": evaluator["evaluator_version"],
        "schema_version": evaluator["schema_version"],
        "prompt_sha256": evaluator["prompt_sha256"],
        "schema_sha256": evaluator["schema_sha256"],
        "continuous_contract_sha256": evaluator["continuous_contract_sha256"],
        "developer_prompt_sha256": evaluator["developer_prompt_sha256"],
        "user_template_sha256": evaluator["user_template_sha256"],
        "strict_schema_sha256": evaluator["strict_schema_sha256"],
        "model": evaluator["model"], "reasoning_effort": evaluator["reasoning_effort"],
        "temperature": evaluator["temperature"], "top_p": evaluator["top_p"],
        "seed": evaluator["seed"], "store": evaluator["store"],
        "independent_stateless_calls": evaluator["independent_stateless_calls"],
        "renderer": evaluator["renderer_identity"],
        "parser_validator": evaluator["parser_validator_identity"],
        "maximum_technical_retries_per_candidate": 1, "automatic_sdk_retries": 0,
        "candidate_input_components": frozen.INPUT_COMPONENTS,
        "human_labels_accessed": False,
        "human_labels_in_requests": False,
        "code_results_accessed": False,
        "code_results_in_requests": False,
        "calibration_or_holdout_scores_in_requests": False,
        "prior_ai_results_in_requests": False,
        "bpmn_reference_in_requests": False,
        "completed_candidate_count": 0,
    }
    holdout.save_json(p["manifest"], manifest, new=True)
    holdout.save_json(p["slots"], [
        {"case_id": case_id, "candidate_id": candidate_id,
         "technical_status": "pending", "retry_count": 0}
        for case_id, candidate_id in PAIRS
    ], new=True)
    print(f"Formal preflight passed: {len(CASES)} cases, {len(artifacts)} frozen candidates; {run_dir}")


def run(run_dir: Path) -> None:
    manifest, artifacts, developer, template, wrapper = verify_binding(
        run_dir, {"preflight_passed", "api_evaluations_in_progress"}
    )
    api_key = holdout.load_api_key()
    p = paths(run_dir)
    if p["results"].exists() or p["usage"].exists():
        raise FileExistsError("Final AI results already exist; refusing to rerun")
    for key in ("raw", "requests", "checkpoints"):
        p[key].mkdir(exist_ok=True)
    slots = json.loads(p["slots"].read_text(encoding="utf-8"))
    if [(s["case_id"], s["candidate_id"]) for s in slots] != list(PAIRS):
        raise RuntimeError("Formal technical slot roster differs")
    manifest["status"] = "api_evaluations_in_progress"
    manifest.setdefault("started_at_utc", holdout.now())
    holdout.save_json(p["manifest"], manifest)
    results, scores, usage_rows = [], [], []
    for index, artifact in enumerate(artifacts):
        case_id, candidate_id = artifact["case_id"], artifact["candidate_id"]
        source = cohort.candidate_paths(case_id, candidate_id)
        process_text = source["process"].read_text(encoding="utf-8")
        graph_text = source["graph"].read_text(encoding="utf-8")
        rendering = legacy.render_activity_graph(json.loads(graph_text))
        user = legacy.instantiate_user_prompt(template, case_id, candidate_id, process_text, graph_text, rendering)
        record = frozen.input_record(case_id, candidate_id, process_text, graph_text, rendering, user, developer)
        if record["input_components"] != frozen.INPUT_COMPONENTS:
            raise RuntimeError("Formal request boundary differs")
        request_path = p["requests"] / f"{case_id}__{candidate_id}.json"
        if request_path.exists():
            if json.loads(request_path.read_text(encoding="utf-8")) != record:
                raise RuntimeError(f"Request record differs: {case_id}/{candidate_id}")
        else:
            holdout.save_json(request_path, record, new=True)
        request_hash = legacy.sha256_file(request_path)
        checkpoint_path = p["checkpoints"] / f"{case_id}__{candidate_id}.json"
        if checkpoint_path.exists():
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            exact = Decimal(checkpoint["overall_score_decimal"])
            frozen.validate_exact_result(checkpoint["result"], exact, case_id, candidate_id, wrapper["schema"])
            if checkpoint["request_record_sha256"] != request_hash:
                raise RuntimeError(f"Checkpoint request differs: {case_id}/{candidate_id}")
            result, used = checkpoint["result"], checkpoint["usage"]
            if used["retry_count"] not in (0, 1):
                raise RuntimeError(f"Retry policy exceeded: {case_id}/{candidate_id}")
            raw_path = p["raw"] / f"{case_id}__{candidate_id}__attempt_{used['retry_count'] + 1}.json"
            if not raw_path.is_file():
                raise RuntimeError(f"Checkpoint raw response missing: {case_id}/{candidate_id}")
        else:
            if list(p["raw"].glob(f"{case_id}__{candidate_id}__attempt_*.json")):
                raise RuntimeError(f"Uncheckpointed prior request requires technical review: {case_id}/{candidate_id}")
            payload = frozen.build_payload(developer, user, wrapper)
            result = None
            last_error: Exception | None = None
            for attempt in (1, 2):
                try:
                    response = legacy.post_response(payload, api_key)
                    raw_path = p["raw"] / f"{case_id}__{candidate_id}__attempt_{attempt}.json"
                    holdout.save_json(raw_path, response, new=True)
                    if response.get("status") != "completed" or response.get("model") != frozen.MODEL:
                        raise ValueError("Response status or model differs")
                    output = frozen.contract.extract_output_text(response)
                    candidate_result = json.loads(output)
                    exact = frozen.parse_score_decimal(output)
                    frozen.validate_exact_result(candidate_result, exact, case_id, candidate_id, wrapper["schema"])
                    result = candidate_result
                    break
                except Exception as exc:
                    last_error = exc
                    error = {"case_id": case_id, "candidate_id": candidate_id,
                             "attempt": attempt, "error_type": type(exc).__name__,
                             "error": str(exc), "timestamp_utc": holdout.now()}
                    if isinstance(exc, urllib.error.HTTPError):
                        try:
                            error["http_body"] = exc.read().decode("utf-8")
                        except Exception:
                            pass
                    holdout.save_json(p["raw"] / f"{case_id}__{candidate_id}__attempt_{attempt}__error.json", error, new=True)
                    if attempt == 1:
                        time.sleep(1)
            if result is None:
                slots[index].update(technical_status="technical_exception", retry_count=1,
                                    request_record_sha256=request_hash, error=str(last_error))
                holdout.save_json(p["slots"], slots)
                manifest.update(status="technical_exception", last_failed_identity=[case_id, candidate_id],
                                completed_candidate_count=len(results), last_updated_at_utc=holdout.now())
                holdout.save_json(p["manifest"], manifest)
                raise RuntimeError(f"Formal run stopped after two attempts at {case_id}/{candidate_id}: {last_error}")
            used = frozen.usage_record(response, case_id, candidate_id, attempt - 1)
            holdout.save_json(checkpoint_path, {
                "case_id": case_id, "candidate_id": candidate_id, "completed_at_utc": holdout.now(),
                "request_record_sha256": request_hash, "result": result,
                "overall_score_decimal": str(exact), "usage": used,
            }, new=True)
        results.append(result)
        scores.append(exact)
        usage_rows.append(used)
        slots[index].update(technical_status="completed", retry_count=used["retry_count"],
                            request_record_sha256=request_hash,
                            raw_response_path=holdout.relative(raw_path),
                            raw_response_sha256=legacy.sha256_file(raw_path))
        holdout.save_json(p["slots"], slots)
        manifest.update(completed_candidate_count=len(results),
                        last_completed_identity=[case_id, candidate_id], last_updated_at_utc=holdout.now())
        holdout.save_json(p["manifest"], manifest)
        print(f"[{index + 1:03d}/120] completed {case_id}/{candidate_id} retries={used['retry_count']}", flush=True)
    with p["results"].open("x", encoding="utf-8") as handle:
        for result, score in zip(results, scores):
            handle.write(frozen.serialize_result(result, score) + "\n")
    with p["usage"].open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(usage_rows[0]))
        writer.writeheader()
        writer.writerows(usage_rows)
    manifest.update(status="all_ai_results_saved", completed_candidate_count=120,
                    completed_at_utc=holdout.now(),
                    total_retry_count=sum(row["retry_count"] for row in usage_rows),
                    results_sha256=legacy.sha256_file(p["results"]),
                    usage_sha256=legacy.sha256_file(p["usage"]),
                    human_labels_accessed=False, code_results_accessed=False)
    holdout.save_json(p["manifest"], manifest)
    print("All 120 formal AI results saved and validated; Code and human results not accessed", flush=True)


def aggregate(run_dir: Path) -> None:
    manifest, artifacts, developer, template, wrapper = verify_binding(run_dir, {"all_ai_results_saved"})
    p = paths(run_dir)
    if any(p[key].exists() for key in ("scores", "summary", "report", "review", "hashes")):
        raise FileExistsError("Formal aggregate output already exists")
    if (manifest["results_sha256"] != legacy.sha256_file(p["results"])
            or manifest["usage_sha256"] != legacy.sha256_file(p["usage"])):
        raise RuntimeError("Saved AI results or usage changed")
    lines = p["results"].read_text(encoding="utf-8").splitlines()
    slots = json.loads(p["slots"].read_text(encoding="utf-8"))
    if len(lines) != 120 or len(slots) != 120 or any(s["technical_status"] != "completed" for s in slots):
        raise RuntimeError("All 120 formal outputs must be saved before aggregation")
    with p["usage"].open(encoding="utf-8", newline="") as handle:
        usage = list(csv.DictReader(handle))
    if len(usage) != 120 or [(x["case_id"], x["candidate_id"]) for x in usage] != list(PAIRS):
        raise RuntimeError("Formal usage roster differs")
    result_rows, table_rows, flagged, scores = [], [], [], []
    for line, artifact, slot in zip(lines, artifacts, slots):
        pair = (artifact["case_id"], artifact["candidate_id"])
        result = json.loads(line)
        score = frozen.parse_score_decimal(line)
        frozen.validate_exact_result(result, score, *pair, wrapper["schema"])
        if (result["case_id"], result["candidate_id"]) != pair or (slot["case_id"], slot["candidate_id"]) != pair:
            raise RuntimeError(f"Formal result identity differs: {pair}")
        source = cohort.candidate_paths(*pair)
        process_text = source["process"].read_text(encoding="utf-8")
        graph_text = source["graph"].read_text(encoding="utf-8")
        rendering = legacy.render_activity_graph(json.loads(graph_text))
        user = legacy.instantiate_user_prompt(template, *pair, process_text, graph_text, rendering)
        record = frozen.input_record(*pair, process_text, graph_text, rendering, user, developer)
        request_path = p["requests"] / f"{pair[0]}__{pair[1]}.json"
        if (json.loads(request_path.read_text(encoding="utf-8")) != record
                or slot["request_record_sha256"] != legacy.sha256_file(request_path)
                or record["input_components"] != frozen.INPUT_COMPONENTS):
            raise RuntimeError(f"Formal request boundary or hash differs: {pair}")
        raw_path = p["raw"] / f"{pair[0]}__{pair[1]}__attempt_{slot['retry_count'] + 1}.json"
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        raw_text = frozen.contract.extract_output_text(raw)
        checkpoint = json.loads((p["checkpoints"] / f"{pair[0]}__{pair[1]}.json").read_text(encoding="utf-8"))
        if (raw.get("status") != "completed" or raw.get("model") != frozen.MODEL
                or json.loads(raw_text) != result or frozen.parse_score_decimal(raw_text) != score
                or checkpoint["result"] != result or Decimal(checkpoint["overall_score_decimal"]) != score
                or checkpoint["request_record_sha256"] != slot["request_record_sha256"]
                or legacy.sha256_file(raw_path) != slot["raw_response_sha256"]):
            raise RuntimeError(f"Formal raw response or checkpoint differs: {pair}")
        result_rows.append(result)
        scores.append(score)
        table = {
            "case_id": pair[0], "candidate_id": pair[1],
            "overall_score": str(score),
            "action_assessment": json.dumps(result["action_assessment"], ensure_ascii=False, separators=(",", ":")),
            "flow_assessment": json.dumps(result["flow_assessment"], ensure_ascii=False, separators=(",", ":")),
            "control_flow_assessment": json.dumps(result["control_flow_assessment"], ensure_ascii=False, separators=(",", ":")),
            "main_error_type": result["main_error_type"], "severity": result["severity"],
            "uncertainty_flag": result["ambiguity_flag"],
            "human_review_flag": result["requires_human_review"],
            "technical_status": slot["technical_status"], "retry_count": slot["retry_count"],
            "process_text_path": artifact["process_text_path"],
            "process_text_sha256": artifact["process_text_sha256"],
            "activity_graph_path": artifact["activity_graph_path"],
            "activity_graph_sha256": artifact["activity_graph_sha256"],
            "rendering_sha256": artifact["rendering_sha256"],
            "prompt_sha256": manifest["prompt_sha256"], "schema_sha256": manifest["schema_sha256"],
            "model": manifest["model"], "reasoning_effort": manifest["reasoning_effort"],
            "request_record_sha256": slot["request_record_sha256"],
            "raw_response_path": slot["raw_response_path"],
            "raw_response_sha256": slot["raw_response_sha256"],
        }
        table_rows.append(table)
        if result["ambiguity_flag"] or result["requires_human_review"]:
            flagged.append({
                "case_id": pair[0], "candidate_id": pair[1], "overall_score": str(score),
                "ambiguity_flag": result["ambiguity_flag"],
                "ambiguity_explanation": result["ambiguity_explanation"],
                "requires_human_review": result["requires_human_review"],
                "review_reason": result["review_reason"],
            })
    with localcontext() as context:
        context.prec = max(80, max(max(0, -x.as_tuple().exponent) for x in scores) + 50)
        mean = sum(scores) / Decimal(120)
        sorted_scores = sorted(scores)
        median = (sorted_scores[59] + sorted_scores[60]) / 2
        population_std = (sum((x - mean) ** 2 for x in scores) / Decimal(120)).sqrt()
        case_summaries = []
        for case_id in CASES:
            values = sorted(score for artifact, score in zip(artifacts, scores) if artifact["case_id"] == case_id)
            if len(values) != 3:
                raise RuntimeError(f"Case does not have exactly three results: {case_id}")
            case_summaries.append({
                "case_id": case_id, "candidate_count": 3,
                "minimum_score": str(values[0]), "maximum_score": str(values[2]),
                "mean_score": str(sum(values) / 3), "median_score": str(values[1]),
            })
    summary = {
        "run_kind": "formal_ai_v16_continuous_40x3",
        "completed_candidates": 120,
        "technical_failures": 0,
        "total_retries": sum(s["retry_count"] for s in slots),
        "minimum_overall_score": str(min(scores)),
        "maximum_overall_score": str(max(scores)),
        "mean_overall_score": str(mean),
        "median_overall_score": str(median),
        "standard_deviation_population": str(population_std),
        "standard_deviation_definition": "population standard deviation across the 120 saved candidate scores",
        "severity_distribution": dict(sorted(Counter(r["severity"] for r in result_rows).items())),
        "main_error_type_distribution": dict(sorted(Counter(r["main_error_type"] for r in result_rows).items())),
        "uncertainty_flag_count": sum(bool(r["ambiguity_flag"]) for r in result_rows),
        "human_review_flag_count": sum(bool(r["requires_human_review"]) for r in result_rows),
        "case_summaries": case_summaries,
        "code_results_in_requests": False,
        "human_judgments_in_requests": False,
        "oracle_or_human_selected_result_created": False,
    }
    with p["scores"].open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table_rows[0]))
        writer.writeheader()
        writer.writerows(table_rows)
    with p["review"].open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["case_id", "candidate_id", "overall_score", "ambiguity_flag", "ambiguity_explanation", "requires_human_review", "review_reason"])
        writer.writeheader()
        writer.writerows(flagged)
    holdout.save_json(p["summary"], summary, new=True)
    report = [
        "# Frozen AI Evaluator v1.6 — formal 120-candidate evaluation", "",
        "The frozen continuous evaluator scored all 40 cases × three candidates independently. These are descriptive AI-only results; no human or Code Evaluator judgments were supplied to the requests or used in this summary.", "",
        f'- Completed candidates: **120**; technical failures: **0**; retries: **{summary["total_retries"]}**.',
        f'- Score range: **{min(scores)}–{max(scores)}**.',
        f'- Mean: **{mean:.4f}**; median: **{median:.4f}**.',
        f'- Population standard deviation: **{population_std:.4f}**.',
        f'- Uncertainty flags: **{summary["uncertainty_flag_count"]}**; human-review flags: **{summary["human_review_flag_count"]}**.',
        "- AI scores are continuous and unquantized. No oracle or human-selected score was created.", "",
        "## Severity distribution", "",
        "| Severity | Candidates |", "|---|---:|",
    ]
    for key, count in summary["severity_distribution"].items():
        report.append(f"| {key} | {count} |")
    report += ["", "## Main error type distribution", "", "| Main error type | Candidates |", "|---|---:|"]
    for key, count in summary["main_error_type_distribution"].items():
        report.append(f"| {key} | {count} |")
    report += ["", "## Case-level descriptive summaries", "", "Each row summarizes the three frozen candidates for that case; it does not select a best candidate.", "", "| Case | n | Min | Max | Mean | Median |", "|---|---:|---:|---:|---:|---:|"]
    for row in case_summaries:
        report.append(f'| {row["case_id"]} | 3 | {row["minimum_score"]} | {row["maximum_score"]} | {Decimal(row["mean_score"]):.4f} | {row["median_score"]} |')
    report += ["", "The candidate-level scores, diagnostics, technical status, and hashes are in `ai_v16_formal_120_scores.csv`; flagged outputs are in `ai_v16_formal_120_review_flags.csv`. No Code-versus-AI comparison or correlation was performed.", ""]
    with p["report"].open("x", encoding="utf-8") as handle:
        handle.write("\n".join(report))
    manifest.update(status="formal_complete", aggregate_completed_at_utc=holdout.now(),
                    scores_sha256=legacy.sha256_file(p["scores"]),
                    summary_sha256=legacy.sha256_file(p["summary"]),
                    report_sha256=legacy.sha256_file(p["report"]),
                    review_flags_sha256=legacy.sha256_file(p["review"]),
                    hashes_path=holdout.relative(p["hashes"]),
                    human_labels_accessed=False, code_results_accessed=False,
                    code_vs_ai_comparison_performed=False)
    holdout.save_json(p["manifest"], manifest)
    files = [path for path in sorted(run_dir.rglob("*")) if path.is_file() and path != p["hashes"]]
    holdout.save_json(p["hashes"], {
        "algorithm": "sha256", "created_at_utc": holdout.now(),
        "file_count": len(files),
        "files_sha256": {holdout.relative(path): legacy.sha256_file(path) for path in files},
        "self_hash_note": "This file omits its own SHA-256 to avoid a circular dependency.",
    }, new=True)
    print("Formal 120 AI-only aggregation complete; no Code or human comparison performed", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "aggregate"))
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    run_dir = resolve_run_dir(args.run_dir)
    if args.command == "preflight":
        preflight(run_dir)
    elif args.command == "run":
        run(run_dir)
    else:
        aggregate(run_dir)


if __name__ == "__main__":
    main()
