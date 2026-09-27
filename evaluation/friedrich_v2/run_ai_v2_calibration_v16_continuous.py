#!/usr/bin/env python3
"""Versioned v1.6 continuous calibration runner; no command runs by import."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.friedrich_v2 import ai_v16_continuous_contract_draft as contract  # noqa: E402
from evaluation.friedrich_v2 import analyze_ai_v16_continuous as analysis  # noqa: E402
from evaluation.friedrich_v2 import run_ai_v2_calibration as legacy  # noqa: E402


PROMPT_PATH = ROOT / "ai_evaluator_v2_prompt_revision_6_continuous_draft.md"
SCHEMA_PATH = contract.SCHEMA_PATH
HASH_MANIFEST_PATH = ROOT / "ai_evaluator_v2_continuous_draft_hashes.json"
BASELINE_MANIFEST_PATH = ROOT / "evaluation/friedrich_v2/results/ai_v15_calibration_18_20260925_resume1/ai_v15_calibration_run_manifest.json"
HUMAN_LABELS_PATH = ROOT / "evaluation/friedrich_v2/review/human_calibration_selected_cases/human_calibration.csv"
RESULTS_ROOT = ROOT / "evaluation/friedrich_v2/results"
CASES = ("1-1", "3-2", "3-4", "6-4", "8-2", "9-5")
CANDIDATES = ("candidate_1", "candidate_2", "candidate_3")
EXPECTED_PAIRS = tuple((case_id, candidate_id) for case_id in CASES for candidate_id in CANDIDATES)
MODEL = "gpt-5.4-2026-03-05"
REASONING_EFFORT = "medium"
PROMPT_VERSION = "ai-evaluator-v2-prompt/1.6"
SCHEMA_VERSION = "ai-evaluator-v2/1.1"
RENDERER = "activity-graph-deterministic-text-v1"
INPUT_COMPONENTS = [
    "case_id", "candidate_id", "original_process_text", "frozen_activity_graph_json",
    "deterministic_textual_rendering",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_run_dir(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if path.parent != RESULTS_ROOT.resolve() or not path.name.startswith("ai_v16_calibration_18_"):
        raise ValueError("Run directory must be a new ai_v16_calibration_18_* directory under the results root")
    return path


def paths(run_dir: Path) -> dict[str, Path]:
    return {
        "manifest": run_dir / "ai_v16_calibration_run_manifest.json",
        "slots": run_dir / "ai_v16_calibration_slots.json",
        "results": run_dir / "ai_v16_calibration_results.jsonl",
        "usage": run_dir / "ai_v16_calibration_usage.csv",
        "comparison": run_dir / "ai_v16_calibration_comparison.csv",
        "review": run_dir / "ai_v16_calibration_review_order.csv",
        "metrics": run_dir / "ai_v16_calibration_metrics.json",
        "report": run_dir / "ai_v16_calibration_report.md",
        "scatter": run_dir / "ai_v16_calibration_scatter.svg",
        "raw": run_dir / "raw_responses",
        "requests": run_dir / "request_records",
        "checkpoints": run_dir / "checkpoints",
    }


def verify_approved_draft_hashes() -> None:
    record = json.loads(HASH_MANIFEST_PATH.read_text(encoding="utf-8"))
    for source in (PROMPT_PATH, SCHEMA_PATH, contract.ROOT / "evaluation/friedrich_v2/ai_v16_continuous_contract_draft.py"):
        relative = str(source.relative_to(ROOT))
        if legacy.sha256_file(source) != record["new_artifact_sha256"][relative]:
            raise ValueError(f"Approved draft artifact hash differs: {relative}")
    if record["prompt_version"] != PROMPT_VERSION or record["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Approved draft version differs")


def load_prompt() -> tuple[str, str]:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    if f"Prompt version: `{PROMPT_VERSION}`" not in text or f"Model: `{MODEL}`" not in text:
        raise ValueError("Prompt version or model declaration differs")
    if f"Reasoning effort: `{REASONING_EFFORT}`" not in text:
        raise ValueError("Reasoning effort declaration differs")
    developer = legacy.extract_fenced_block(text, "Exact developer prompt", "text")
    template = legacy.extract_fenced_block(text, "Exact candidate-level user prompt template", "text")
    placeholders = set(re.findall(r"\{\{[A-Z_]+\}\}", template))
    if placeholders != {
        "{{CASE_ID}}", "{{CANDIDATE_ID}}", "{{ORIGINAL_PROCESS_TEXT}}",
        "{{ACTIVITY_GRAPH_JSON}}", "{{DETERMINISTIC_TEXTUAL_RENDERING}}",
    }:
        raise ValueError("Candidate template placeholders differ")
    return developer, template


def assert_same_roster(actual: list[dict[str, Any]], baseline: list[dict[str, Any]]) -> None:
    pairs = [(item["case_id"], item["candidate_id"]) for item in actual]
    if tuple(pairs) != EXPECTED_PAIRS or len(actual) != 18 or actual != baseline:
        raise ValueError("Frozen candidate identities or process/graph/rendering hashes differ from v1.5 calibration")


def verified_artifacts() -> list[dict[str, Any]]:
    actual = legacy.validate_artifacts()  # frozen files and deterministic renderer; no labels
    baseline = json.loads(BASELINE_MANIFEST_PATH.read_text(encoding="utf-8"))["candidates"]
    assert_same_roster(actual, baseline)
    return actual


def input_record(
    case_id: str, candidate_id: str, process_text: str, graph_text: str,
    rendering: str, user_prompt: str, developer_prompt: str,
) -> dict[str, Any]:
    return {
        "case_id": case_id, "candidate_id": candidate_id,
        "model": MODEL, "reasoning_effort": REASONING_EFFORT,
        "temperature": "omitted", "top_p": "omitted", "seed": "unsupported/omitted",
        "store": False, "stateless": True, "batch": False,
        "prompt_version": PROMPT_VERSION, "schema_version": SCHEMA_VERSION,
        "developer_prompt_sha256": legacy.sha256_bytes(developer_prompt.encode("utf-8")),
        "user_prompt_sha256": legacy.sha256_bytes(user_prompt.encode("utf-8")),
        "process_text_sha256": legacy.sha256_bytes(process_text.encode("utf-8")),
        "activity_graph_sha256": legacy.sha256_bytes(graph_text.encode("utf-8")),
        "rendering_sha256": legacy.sha256_bytes(rendering.encode("utf-8")),
        "input_components": INPUT_COMPONENTS,
    }


def build_payload(developer_prompt: str, user_prompt: str, schema_wrapper: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": MODEL,
        "reasoning": {"effort": REASONING_EFFORT},
        "store": False,
        "input": [
            {"role": "developer", "content": [{"type": "input_text", "text": developer_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
        ],
        "text": {"format": schema_wrapper},
    }


def parse_score_decimal(output_text: str) -> Decimal:
    value = json.loads(output_text, parse_float=Decimal, parse_int=Decimal)["overall_score"]
    if not isinstance(value, Decimal) or not value.is_finite() or not Decimal(0) <= value <= Decimal(1):
        raise ValueError("Continuous score must be a finite JSON number from 0 through 1")
    return value


def validate_exact_result(result: dict[str, Any], exact_score: Decimal,
                          case_id: str, candidate_id: str, schema: dict[str, Any]) -> None:
    """Apply the frozen validator without binary-float endpoint misclassification."""
    if not exact_score.is_finite() or not Decimal(0) <= exact_score <= Decimal(1):
        raise ValueError("Continuous score must be a finite JSON number from 0 through 1")
    validation_copy = dict(result)
    # The approved validator accepts Python floats. A long JSON number just below
    # one can float-round to 1.0, so use a representative interior float while
    # checking the exact score range and endpoint here.
    validation_copy["overall_score"] = 1.0 if exact_score == 1 else 0.5
    contract.validate_result(validation_copy, case_id, candidate_id, schema)


def serialize_result(result: dict[str, Any], exact_score: Decimal) -> str:
    """Keep the exact decimal score numeric in compact JSONL, without quantization."""
    fields = []
    for key, value in result.items():
        encoded = str(exact_score) if key == "overall_score" else json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        fields.append(f"{json.dumps(key)}:{encoded}")
    return "{" + ",".join(fields) + "}"


def save_json(path: Path, value: Any, *, new: bool = False) -> None:
    with path.open("x" if new else "w", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def slot_records() -> list[dict[str, Any]]:
    return [
        {"case_id": case_id, "candidate_id": candidate_id, "technical_status": "pending", "retry_count": 0}
        for case_id, candidate_id in EXPECTED_PAIRS
    ]


def verify_manifest_and_inputs(run_dir: Path, allowed_statuses: set[str]) -> tuple[dict[str, Any], list[dict[str, Any]], str, str, dict[str, Any]]:
    p = paths(run_dir)
    manifest = json.loads(p["manifest"].read_text(encoding="utf-8"))
    if manifest.get("status") not in allowed_statuses:
        raise RuntimeError(f"Run manifest status disallows this command: {manifest.get('status')}")
    verify_approved_draft_hashes()
    artifacts = verified_artifacts()
    if manifest["candidates"] != artifacts or manifest["baseline_manifest_sha256"] != legacy.sha256_file(BASELINE_MANIFEST_PATH):
        raise RuntimeError("Frozen calibration roster changed after preflight")
    developer, template = load_prompt()
    wrapper = contract.load_schema_wrapper()
    if (manifest["prompt_file_sha256"] != legacy.sha256_file(PROMPT_PATH)
            or manifest["schema_file_sha256"] != legacy.sha256_file(SCHEMA_PATH)
            or manifest["strict_schema_sha256"] != legacy.sha256_bytes(legacy.canonical_json(wrapper).encode("utf-8"))
            or manifest["developer_prompt_sha256"] != legacy.sha256_bytes(developer.encode("utf-8"))
            or manifest["user_template_sha256"] != legacy.sha256_bytes(template.encode("utf-8"))
            or manifest["prompt_version"] != PROMPT_VERSION or manifest["schema_version"] != SCHEMA_VERSION
            or manifest["model"] != MODEL or manifest["reasoning_effort"] != REASONING_EFFORT
            or manifest["temperature"] != "omitted" or manifest["top_p"] != "omitted"
            or manifest["seed"] != "unsupported/omitted" or manifest["store"] is not False
            or manifest["independent_stateless_calls"] is not True or manifest["renderer"] != RENDERER
            or manifest["maximum_technical_retries_per_candidate"] != 1
            or manifest["automatic_sdk_retries"] != 0):
        raise RuntimeError("v1.6 evaluator binding changed after preflight")
    return manifest, artifacts, developer, template, wrapper


def cmd_preflight(run_dir: Path) -> None:
    if run_dir.exists():
        raise FileExistsError(f"Run directory already exists: {run_dir}")
    verify_approved_draft_hashes()
    artifacts = verified_artifacts()
    developer, template = load_prompt()
    wrapper = contract.load_schema_wrapper()
    run_dir.mkdir(parents=False, exist_ok=False)
    p = paths(run_dir)
    manifest = {
        "status": "preflight_passed", "created_at_utc": utc_now(),
        "run_kind": "developmental_continuous_calibration", "candidate_count": 18,
        "case_count": 6, "case_ids": list(CASES), "candidates": artifacts,
        "baseline_manifest_sha256": legacy.sha256_file(BASELINE_MANIFEST_PATH),
        "prompt_version": PROMPT_VERSION, "prompt_file_sha256": legacy.sha256_file(PROMPT_PATH),
        "schema_version": SCHEMA_VERSION, "schema_file_sha256": legacy.sha256_file(SCHEMA_PATH),
        "strict_schema_sha256": legacy.sha256_bytes(legacy.canonical_json(wrapper).encode("utf-8")),
        "developer_prompt_sha256": legacy.sha256_bytes(developer.encode("utf-8")),
        "user_template_sha256": legacy.sha256_bytes(template.encode("utf-8")),
        "model": MODEL, "reasoning_effort": REASONING_EFFORT,
        "temperature": "omitted", "top_p": "omitted", "seed": "unsupported/omitted",
        "store": False, "independent_stateless_calls": True,
        "renderer": RENDERER, "parser": "extract_output_text + json.loads + v1.6 continuous validate_result",
        "maximum_technical_retries_per_candidate": 1, "automatic_sdk_retries": 0,
        "human_labels_accessed": False, "completed_candidate_count": 0,
        "frozen": False,
    }
    save_json(p["manifest"], manifest, new=True)
    save_json(p["slots"], slot_records(), new=True)
    print(f"Preflight passed for 18 frozen candidates: {run_dir}")


def usage_record(response: dict[str, Any], case_id: str, candidate_id: str, retries: int) -> dict[str, Any]:
    usage = response.get("usage", {})
    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    cached = int(usage.get("input_tokens_details", {}).get("cached_tokens", 0) or 0)
    cost = ((input_tokens - cached) * legacy.INPUT_PRICE_PER_MILLION
            + cached * legacy.CACHED_INPUT_PRICE_PER_MILLION
            + output_tokens * legacy.OUTPUT_PRICE_PER_MILLION) / 1_000_000
    return {
        "case_id": case_id, "candidate_id": candidate_id,
        "input_tokens": input_tokens, "cached_input_tokens": cached,
        "output_tokens": output_tokens, "reasoning_tokens": int(usage.get("output_tokens_details", {}).get("reasoning_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", input_tokens + output_tokens)),
        "estimated_api_cost_usd": f"{cost:.8f}", "model": response.get("model", MODEL),
        "response_id": response.get("id", ""), "retry_count": retries,
    }


def cmd_run(run_dir: Path) -> None:
    manifest, artifacts, developer, template, wrapper = verify_manifest_and_inputs(
        run_dir, {"preflight_passed", "api_evaluations_in_progress"}
    )
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is unavailable")
    p = paths(run_dir)
    if p["results"].exists() or p["usage"].exists():
        raise FileExistsError("Final AI outputs already exist; refusing to rerun")
    for key in ("raw", "requests", "checkpoints"):
        p[key].mkdir(exist_ok=True)
    slots = json.loads(p["slots"].read_text(encoding="utf-8"))
    if [(row["case_id"], row["candidate_id"]) for row in slots] != list(EXPECTED_PAIRS):
        raise RuntimeError("Technical slot ledger differs from frozen roster")
    manifest["status"] = "api_evaluations_in_progress"
    manifest.setdefault("started_at_utc", utc_now())
    save_json(p["manifest"], manifest)
    results, usage_rows, exact_scores = [], [], []
    for index, artifact in enumerate(artifacts):
        case_id, candidate_id = artifact["case_id"], artifact["candidate_id"]
        source = legacy.candidate_paths(case_id, candidate_id)
        process_text = source["process"].read_text(encoding="utf-8")
        graph_text = source["graph"].read_text(encoding="utf-8")
        rendering = legacy.render_activity_graph(json.loads(graph_text))
        user_prompt = legacy.instantiate_user_prompt(template, case_id, candidate_id, process_text, graph_text, rendering)
        record = input_record(case_id, candidate_id, process_text, graph_text, rendering, user_prompt, developer)
        request_path = p["requests"] / f"{case_id}__{candidate_id}.json"
        record_text = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
        request_hash = legacy.sha256_bytes(record_text.encode("utf-8"))
        if request_path.exists():
            if legacy.sha256_file(request_path) != request_hash:
                raise RuntimeError(f"Existing request record hash mismatch: {case_id}/{candidate_id}")
        else:
            with request_path.open("x", encoding="utf-8") as handle:
                handle.write(record_text)
        checkpoint_path = p["checkpoints"] / f"{case_id}__{candidate_id}.json"
        if checkpoint_path.exists():
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if checkpoint["request_record_sha256"] != request_hash:
                raise RuntimeError(f"Checkpoint request hash mismatch: {case_id}/{candidate_id}")
            validate_exact_result(checkpoint["result"], Decimal(checkpoint["overall_score_decimal"]),
                                  case_id, candidate_id, wrapper["schema"])
            results.append(checkpoint["result"])
            usage_rows.append(checkpoint["usage"])
            exact_scores.append(Decimal(checkpoint["overall_score_decimal"]))
            retries = int(checkpoint["usage"]["retry_count"])
            if retries not in (0, 1):
                raise RuntimeError(f"Checkpoint retry policy exceeded: {case_id}/{candidate_id}")
            raw_path = p["raw"] / f"{case_id}__{candidate_id}__attempt_{retries + 1}.json"
            if not raw_path.is_file():
                raise RuntimeError(f"Checkpoint raw response is missing: {case_id}/{candidate_id}")
            slots[index].update(technical_status="completed", retry_count=retries,
                                request_record_sha256=request_hash, raw_response_path=str(raw_path.relative_to(ROOT)))
            save_json(p["slots"], slots)
            manifest["completed_candidate_count"] = len(results)
            manifest["last_completed_identity"] = [case_id, candidate_id]
            manifest["last_updated_at_utc"] = utc_now()
            save_json(p["manifest"], manifest)
            continue
        if list(p["raw"].glob(f"{case_id}__{candidate_id}__attempt_*.json")):
            raise RuntimeError(f"Uncheckpointed prior attempt requires technical review: {case_id}/{candidate_id}")
        payload = build_payload(developer, user_prompt, wrapper)
        response = None
        result = None
        exact_score = None
        last_error: Exception | None = None
        attempt_used = 0
        for attempt in (1, 2):
            attempt_used = attempt
            try:
                candidate_response = legacy.post_response(payload, api_key)
                raw_path = p["raw"] / f"{case_id}__{candidate_id}__attempt_{attempt}.json"
                save_json(raw_path, candidate_response, new=True)
                if candidate_response.get("status") != "completed":
                    raise ValueError(f"Response status was {candidate_response.get('status')!r}")
                output_text = contract.extract_output_text(candidate_response)
                candidate_result = json.loads(output_text)
                candidate_exact_score = parse_score_decimal(output_text)
                validate_exact_result(candidate_result, candidate_exact_score,
                                      case_id, candidate_id, wrapper["schema"])
                response, result = candidate_response, candidate_result
                exact_score = candidate_exact_score
                break
            except Exception as exc:
                last_error = exc
                error = {
                    "case_id": case_id, "candidate_id": candidate_id, "attempt": attempt,
                    "error_type": type(exc).__name__, "error": str(exc), "timestamp_utc": utc_now(),
                }
                if isinstance(exc, urllib.error.HTTPError):
                    try:
                        error["http_body"] = exc.read().decode("utf-8")
                    except Exception:
                        pass
                save_json(p["raw"] / f"{case_id}__{candidate_id}__attempt_{attempt}__error.json", error, new=True)
                if attempt == 1:
                    time.sleep(1)
        if response is None or result is None or exact_score is None:
            slots[index].update(technical_status="technical_exception", retry_count=attempt_used - 1,
                                request_record_sha256=request_hash, error=str(last_error))
            save_json(p["slots"], slots)
            manifest["status"] = "technical_exception"
            manifest["last_failed_identity"] = [case_id, candidate_id]
            manifest["last_updated_at_utc"] = utc_now()
            save_json(p["manifest"], manifest)
            raise RuntimeError(f"Failed {case_id}/{candidate_id} after two attempts: {last_error}")
        used = usage_record(response, case_id, candidate_id, attempt_used - 1)
        checkpoint = {
            "case_id": case_id, "candidate_id": candidate_id,
            "completed_at_utc": utc_now(), "request_record_sha256": request_hash,
            "result": result, "overall_score_decimal": str(exact_score), "usage": used,
        }
        save_json(checkpoint_path, checkpoint, new=True)
        results.append(result)
        usage_rows.append(used)
        exact_scores.append(exact_score)
        slots[index].update(technical_status="completed", retry_count=attempt_used - 1,
                            request_record_sha256=request_hash, raw_response_path=str(raw_path.relative_to(ROOT)))
        save_json(p["slots"], slots)
        manifest["completed_candidate_count"] = len(results)
        manifest["last_completed_identity"] = [case_id, candidate_id]
        manifest["last_updated_at_utc"] = utc_now()
        save_json(p["manifest"], manifest)
        print(f"[{index + 1:02d}/18] completed {case_id}/{candidate_id} retries={attempt_used - 1}", flush=True)
    if tuple((row["case_id"], row["candidate_id"]) for row in results) != EXPECTED_PAIRS:
        raise RuntimeError("Completed AI results differ from frozen order")
    with p["results"].open("x", encoding="utf-8") as handle:
        for result, exact_score in zip(results, exact_scores):
            handle.write(serialize_result(result, exact_score) + "\n")
    with p["usage"].open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(usage_rows[0]))
        writer.writeheader()
        writer.writerows(usage_rows)
    manifest.update(status="all_ai_results_saved", completed_candidate_count=18,
                    completed_at_utc=utc_now(), total_retry_count=sum(row["retry_count"] for row in usage_rows),
                    results_sha256=legacy.sha256_file(p["results"]), usage_sha256=legacy.sha256_file(p["usage"]),
                    human_labels_accessed=False)
    save_json(p["manifest"], manifest)
    print("All 18 AI results saved and validated; human labels have not been accessed")


def cmd_compare(run_dir: Path) -> None:
    manifest, artifacts, developer, template, wrapper = verify_manifest_and_inputs(run_dir, {"all_ai_results_saved"})
    p = paths(run_dir)
    if any(p[key].exists() for key in ("comparison", "review", "metrics", "report", "scatter")):
        raise FileExistsError("Comparison artifacts already exist; refusing to overwrite")
    if manifest["results_sha256"] != legacy.sha256_file(p["results"]) or manifest["usage_sha256"] != legacy.sha256_file(p["usage"]):
        raise RuntimeError("Saved AI result or usage hash differs")
    lines = [line for line in p["results"].read_text(encoding="utf-8").splitlines() if line]
    if len(lines) != 18:
        raise RuntimeError("All 18 saved AI results are required before labels")
    results = [json.loads(line) for line in lines]
    pairs = tuple((row["case_id"], row["candidate_id"]) for row in results)
    if pairs != EXPECTED_PAIRS or pairs != tuple((row["case_id"], row["candidate_id"]) for row in artifacts):
        raise RuntimeError("Saved AI result identities differ from frozen roster")
    slots = json.loads(p["slots"].read_text(encoding="utf-8"))
    if (len(slots) != 18 or tuple((row["case_id"], row["candidate_id"]) for row in slots) != EXPECTED_PAIRS
            or any(row["technical_status"] != "completed" for row in slots)):
        raise RuntimeError("All 18 technical slots must be complete before labels")
    scores: dict[tuple[str, str], Decimal] = {}
    for line, row, artifact, slot in zip(lines, results, artifacts, slots):
        pair = (row["case_id"], row["candidate_id"])
        scores[pair] = parse_score_decimal(line)
        validate_exact_result(row, scores[pair], *pair, wrapper["schema"])
        checkpoint = json.loads((p["checkpoints"] / f"{pair[0]}__{pair[1]}.json").read_text(encoding="utf-8"))
        request_path = p["requests"] / f"{pair[0]}__{pair[1]}.json"
        source = legacy.candidate_paths(*pair)
        process_text = source["process"].read_text(encoding="utf-8")
        graph_text = source["graph"].read_text(encoding="utf-8")
        rendering = legacy.render_activity_graph(json.loads(graph_text))
        user_prompt = legacy.instantiate_user_prompt(template, *pair, process_text, graph_text, rendering)
        expected_record = input_record(*pair, process_text, graph_text, rendering, user_prompt, developer)
        request_record = json.loads(request_path.read_text(encoding="utf-8"))
        if request_record != expected_record or request_record["input_components"] != INPUT_COMPONENTS:
            raise RuntimeError(f"Request boundary or hashes differ: {pair}")
        raw_path = p["raw"] / f"{pair[0]}__{pair[1]}__attempt_{int(slot['retry_count']) + 1}.json"
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        if raw.get("status") != "completed" or raw.get("model") != MODEL:
            raise RuntimeError(f"Raw response status or model differs: {pair}")
        raw_text = contract.extract_output_text(raw)
        if json.loads(raw_text) != row or parse_score_decimal(raw_text) != scores[pair]:
            raise RuntimeError(f"Raw response result differs: {pair}")
        if (checkpoint["result"] != row or checkpoint["request_record_sha256"] != legacy.sha256_file(request_path)
                or Decimal(checkpoint["overall_score_decimal"]) != scores[pair]
                or slot["request_record_sha256"] != legacy.sha256_file(request_path)):
            raise RuntimeError(f"Checkpoint or request hash differs: {pair}")
    with p["usage"].open(encoding="utf-8", newline="") as handle:
        usage_rows = list(csv.DictReader(handle))
    if (len(usage_rows) != 18
            or tuple((row["case_id"], row["candidate_id"]) for row in usage_rows) != EXPECTED_PAIRS):
        raise RuntimeError("All 18 technical slots and usage rows must be complete before labels")
    # The first human-label read in this runner is below, after all saved AI checks.
    labels = analysis.load_human_labels(HUMAN_LABELS_PATH, EXPECTED_PAIRS)
    rows, metrics = analysis.calculate(EXPECTED_PAIRS, scores, labels)
    analysis.write_csv(p["comparison"], rows)
    analysis.write_csv(p["review"], analysis.review_order(rows))
    with p["metrics"].open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(analysis.metrics_json_ready(metrics), ensure_ascii=False, indent=2) + "\n")
    analysis.write_scatter_svg(p["scatter"], rows)
    analysis.write_report(p["report"], rows, metrics)
    manifest.update(status="comparison_complete", human_labels_accessed=True,
                    human_labels_accessed_after_all_results_saved=True, comparison_completed_at_utc=utc_now(),
                    comparison_sha256=legacy.sha256_file(p["comparison"]),
                    metrics_sha256=legacy.sha256_file(p["metrics"]),
                    scatter_sha256=legacy.sha256_file(p["scatter"]),
                    report_sha256=legacy.sha256_file(p["report"]))
    save_json(p["manifest"], manifest)
    print("Continuous calibration comparison complete; no acceptance threshold applied")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "compare"))
    parser.add_argument("--run-dir", required=True, help="New collision-free ai_v16_calibration_18_* results directory")
    args = parser.parse_args()
    run_dir = resolve_run_dir(args.run_dir)
    if args.command == "preflight":
        cmd_preflight(run_dir)
    elif args.command == "run":
        cmd_run(run_dir)
    else:
        cmd_compare(run_dir)


if __name__ == "__main__":
    main()
