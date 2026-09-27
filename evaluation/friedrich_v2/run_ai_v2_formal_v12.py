#!/usr/bin/env python3
"""Frozen AI Evaluator V2 prompt 1.2 formal 120-candidate runner.

Commands are deliberately separated:

* preflight: verifies the frozen cohort and evaluator, then writes manifests;
* run: performs label-blind independent API calls with durable checkpoints;
* aggregate: produces formal descriptive statistics without human labels.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.friedrich_v2 import run_ai_v2_calibration as base


base.PROMPT_PATH = ROOT / "ai_evaluator_v2_prompt_revision_2.md"
base.PROMPT_VERSION = "ai-evaluator-v2-prompt/1.2"

COHORT_ROOT = ROOT / "evaluation/friedrich_v2/cohorts/final_frozen_40x3_20260910"
COHORT_RUN_MANIFEST = COHORT_ROOT / "run_manifest.json"
COHORT_GENERATED_MANIFEST = COHORT_ROOT / "generated_manifest.json"
COHORT_ARTIFACT_INVENTORY = COHORT_ROOT / "manifests/artifact_inventory.json"
SOURCE_FREEZE_RECORD = (
    ROOT
    / "evaluation/friedrich_v2/results/ai_v2_holdout_15_prompt_v12_20260923"
    / "frozen_evaluator_manifest.json"
)

RESULTS_PATH = ROOT / "ai_v2_formal_results.jsonl"
USAGE_PATH = ROOT / "ai_v2_formal_usage.csv"
TABLE_PATH = ROOT / "ai_v2_formal_candidate_results.csv"
REPORT_PATH = ROOT / "ai_v2_formal_report.md"
SUPPORT_ROOT = ROOT / "evaluation/friedrich_v2/results/ai_v2_formal_120_prompt_v12_20260923"
RAW_ROOT = SUPPORT_ROOT / "raw_responses"
REQUEST_ROOT = SUPPORT_ROOT / "request_records"
CHECKPOINT_ROOT = SUPPORT_ROOT / "checkpoints"
MANIFEST_PATH = SUPPORT_ROOT / "run_manifest.json"
FROZEN_EVALUATOR_PATH = SUPPORT_ROOT / "frozen_evaluator_manifest.json"

MODEL = "gpt-5.4-2026-03-05"
REASONING_EFFORT = "medium"
PROMPT_VERSION = "ai-evaluator-v2-prompt/1.2"
SCHEMA_VERSION = "ai-evaluator-v2/1.0"
CANDIDATES = ("candidate_1", "candidate_2", "candidate_3")
SCORE_LEVELS = (1.0, 0.75, 0.5, 0.25, 0.0)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_cohort_run_manifest() -> dict[str, Any]:
    return json.loads(COHORT_RUN_MANIFEST.read_text(encoding="utf-8"))


def locked_case_ids() -> tuple[str, ...]:
    manifest = load_cohort_run_manifest()
    cases = tuple(manifest.get("case_ids", []))
    if len(cases) != 40 or len(set(cases)) != 40:
        raise ValueError("Frozen cohort does not contain exactly 40 unique cases")
    return cases


CASES = locked_case_ids()
EXPECTED_PAIRS = tuple(
    (case_id, candidate_id)
    for case_id in CASES
    for candidate_id in CANDIDATES
)
EXPECTED_COUNT = len(EXPECTED_PAIRS)


def candidate_paths(case_id: str, candidate_id: str) -> dict[str, Path]:
    root = COHORT_ROOT / "cases" / case_id / candidate_id
    return {
        "process": COHORT_ROOT / "cases" / case_id / "process_text.txt",
        "candidate_process": root / "process_text.txt",
        "graph": root / "activity_graph.json",
        "manifest": root / "candidate_manifest.json",
    }


def generated_hash_records() -> dict[tuple[str, str], dict[str, str]]:
    generated = json.loads(COHORT_GENERATED_MANIFEST.read_text(encoding="utf-8"))
    if generated.get("run_integrity_status") != "valid":
        raise ValueError("Generated cohort integrity status is not valid")
    if generated.get("human_selection") is not False:
        raise ValueError("Formal cohort unexpectedly records human selection")
    records: dict[tuple[str, str], dict[str, str]] = {}
    for case in generated.get("cases", []):
        case_id = case["case_id"]
        for candidate in case.get("candidates", []):
            candidate_id = candidate["candidate_id"]
            if candidate.get("generation_status") != "success":
                raise ValueError(f"Unsuccessful frozen candidate: {case_id}/{candidate_id}")
            attempts = candidate.get("attempts", [])
            if not attempts:
                raise ValueError(f"Missing attempt evidence: {case_id}/{candidate_id}")
            evidence = attempts[-1]["evidence"]
            artifact_hashes = evidence["artifact_hashes"]
            records[(case_id, candidate_id)] = {
                "process_text_sha256": artifact_hashes["process_text.txt"],
                "activity_graph_sha256": artifact_hashes["activity_graph.json"],
            }
    if set(records) != set(EXPECTED_PAIRS):
        raise ValueError("Generated manifest identities differ from locked 120 slots")
    return records


def validate_frozen_cohort() -> list[dict[str, Any]]:
    run_manifest = load_cohort_run_manifest()
    if run_manifest.get("status") != "complete":
        raise ValueError("Frozen generation run is not complete")
    expected_summary = {
        "expected_case_count": 40,
        "expected_candidates_per_case": 3,
        "expected_candidate_slots": 120,
        "completed_candidates": 120,
        "failed_candidates": 0,
    }
    for key, expected in expected_summary.items():
        if run_manifest.get(key) != expected:
            raise ValueError(f"Frozen cohort summary mismatch for {key}")

    inventory = json.loads(COHORT_ARTIFACT_INVENTORY.read_text(encoding="utf-8"))
    if inventory.get("status") != "complete":
        raise ValueError("Frozen artifact inventory is not complete")
    if inventory.get("successful_candidate_slots") != 120:
        raise ValueError("Artifact inventory does not confirm 120 successful slots")

    generated_hashes = generated_hash_records()
    records: list[dict[str, Any]] = []
    for case_id, candidate_id in EXPECTED_PAIRS:
        paths = candidate_paths(case_id, candidate_id)
        for label, path in paths.items():
            if not path.is_file():
                raise FileNotFoundError(f"Missing frozen {label}: {path}")
        candidate_manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
        if (
            candidate_manifest.get("case_id") != case_id
            or candidate_manifest.get("candidate_id") != candidate_id
        ):
            raise ValueError(f"Candidate identity mismatch: {case_id}/{candidate_id}")
        process_hash = base.sha256_file(paths["process"])
        graph_hash = base.sha256_file(paths["graph"])
        if base.sha256_file(paths["candidate_process"]) != process_hash:
            raise ValueError(f"Candidate process copy mismatch: {case_id}/{candidate_id}")
        artifact_hashes = candidate_manifest.get("artifact_hashes", {})
        if artifact_hashes.get("process_text.txt") != process_hash:
            raise ValueError(f"Candidate manifest process hash mismatch: {case_id}/{candidate_id}")
        if artifact_hashes.get("activity_graph.json") != graph_hash:
            raise ValueError(f"Candidate manifest graph hash mismatch: {case_id}/{candidate_id}")
        if generated_hashes[(case_id, candidate_id)]["process_text_sha256"] != process_hash:
            raise ValueError(f"Generated manifest process hash mismatch: {case_id}/{candidate_id}")
        if generated_hashes[(case_id, candidate_id)]["activity_graph_sha256"] != graph_hash:
            raise ValueError(f"Generated manifest graph hash mismatch: {case_id}/{candidate_id}")
        graph = json.loads(paths["graph"].read_text(encoding="utf-8"))
        rendering = base.render_activity_graph(graph)
        records.append(
            {
                "case_id": case_id,
                "candidate_id": candidate_id,
                "process_text_path": str(paths["process"].relative_to(ROOT)),
                "process_text_sha256": process_hash,
                "activity_graph_path": str(paths["graph"].relative_to(ROOT)),
                "activity_graph_sha256": graph_hash,
                "rendering_sha256": base.sha256_bytes(rendering.encode("utf-8")),
                "node_count": len(graph["nodes"]),
                "edge_count": len(graph["edges"]),
            }
        )
    if len(records) != 120:
        raise ValueError(f"Expected 120 validated candidates, found {len(records)}")
    return records


def frozen_evaluator_record() -> dict[str, Any]:
    developer_prompt, user_template = base.load_locked_prompt()
    schema_wrapper = base.load_locked_schema_wrapper()
    source = json.loads(SOURCE_FREEZE_RECORD.read_text(encoding="utf-8"))
    actual = {
        "status": "frozen_for_formal_execution",
        "source_freeze_record": str(SOURCE_FREEZE_RECORD.relative_to(ROOT)),
        "source_freeze_record_sha256": base.sha256_file(SOURCE_FREEZE_RECORD),
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "temperature": "omitted",
        "top_p": "omitted",
        "seed": "unsupported/omitted",
        "store": False,
        "batch": False,
        "independent_stateless_calls": True,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "renderer": "activity-graph-deterministic-text-v1",
        "prompt_file": str(base.PROMPT_PATH.relative_to(ROOT)),
        "prompt_file_sha256": base.sha256_file(base.PROMPT_PATH),
        "developer_prompt_sha256": base.sha256_bytes(developer_prompt.encode("utf-8")),
        "user_template_sha256": base.sha256_bytes(user_template.encode("utf-8")),
        "schema_file": str(base.SCHEMA_PATH.relative_to(ROOT)),
        "schema_file_sha256": base.sha256_file(base.SCHEMA_PATH),
        "strict_schema_sha256": base.sha256_bytes(
            base.canonical_json(schema_wrapper).encode("utf-8")
        ),
    }
    comparable = (
        "model",
        "reasoning_effort",
        "temperature",
        "top_p",
        "seed",
        "store",
        "batch",
        "independent_stateless_calls",
        "prompt_version",
        "schema_version",
        "renderer",
        "prompt_file_sha256",
        "developer_prompt_sha256",
        "user_template_sha256",
        "schema_file_sha256",
        "strict_schema_sha256",
    )
    mismatches = [key for key in comparable if source.get(key) != actual.get(key)]
    if mismatches:
        raise ValueError(f"Evaluator differs from frozen holdout record: {mismatches}")
    return actual


def artifact_set_sha256(records: list[dict[str, Any]]) -> str:
    return base.sha256_bytes(base.canonical_json(records).encode("utf-8"))


def cmd_preflight() -> None:
    if MANIFEST_PATH.exists():
        raise FileExistsError("Formal run manifest already exists; refusing to replace it")
    for path in (RESULTS_PATH, USAGE_PATH, TABLE_PATH, REPORT_PATH):
        if path.exists():
            raise FileExistsError(f"Formal output already exists: {path}")
    artifacts = validate_frozen_cohort()
    evaluator = frozen_evaluator_record()
    SUPPORT_ROOT.mkdir(parents=True, exist_ok=False)
    FROZEN_EVALUATOR_PATH.write_text(
        json.dumps(evaluator, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "status": "preflight_passed",
        "created_at_utc": utc_now(),
        "run_kind": "formal_ai_evaluator_v2",
        "human_labels_accessed": False,
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "temperature": "omitted",
        "top_p": "omitted",
        "seed": "unsupported/omitted",
        "store": False,
        "batch": False,
        "independent_stateless_calls": True,
        "automatic_sdk_retries": 0,
        "maximum_technical_retries_per_candidate": 1,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "renderer": "activity-graph-deterministic-text-v1",
        "candidate_count": EXPECTED_COUNT,
        "case_count": len(CASES),
        "candidates_per_case": len(CANDIDATES),
        "case_ids": list(CASES),
        "frozen_generation_run_manifest": str(COHORT_RUN_MANIFEST.relative_to(ROOT)),
        "frozen_generation_run_manifest_sha256": base.sha256_file(COHORT_RUN_MANIFEST),
        "frozen_generated_manifest": str(COHORT_GENERATED_MANIFEST.relative_to(ROOT)),
        "frozen_generated_manifest_sha256": base.sha256_file(COHORT_GENERATED_MANIFEST),
        "frozen_artifact_inventory": str(COHORT_ARTIFACT_INVENTORY.relative_to(ROOT)),
        "frozen_artifact_inventory_sha256": base.sha256_file(COHORT_ARTIFACT_INVENTORY),
        "frozen_evaluator_manifest": str(FROZEN_EVALUATOR_PATH.relative_to(ROOT)),
        "frozen_evaluator_manifest_sha256": base.sha256_file(FROZEN_EVALUATOR_PATH),
        "artifact_set_sha256": artifact_set_sha256(artifacts),
        "candidates": artifacts,
        "completed_candidate_count": 0,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Formal preflight passed for 40 cases and 120 frozen candidates")
    print(f"Prompt version: {PROMPT_VERSION}")
    print(f"Schema version: {SCHEMA_VERSION}")
    print(f"Manifest: {MANIFEST_PATH.relative_to(ROOT)}")


def verify_locked_manifest() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not MANIFEST_PATH.is_file() or not FROZEN_EVALUATOR_PATH.is_file():
        raise RuntimeError("Run formal preflight before execution")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("status") not in {"preflight_passed", "api_evaluations_in_progress"}:
        raise RuntimeError(f"Formal manifest cannot execute from status {manifest.get('status')!r}")
    artifacts = validate_frozen_cohort()
    if manifest.get("artifact_set_sha256") != artifact_set_sha256(artifacts):
        raise RuntimeError("Frozen candidate artifact set changed after preflight")
    evaluator = frozen_evaluator_record()
    if manifest.get("frozen_evaluator_manifest_sha256") != base.sha256_file(FROZEN_EVALUATOR_PATH):
        raise RuntimeError("Frozen evaluator manifest changed after preflight")
    if json.loads(FROZEN_EVALUATOR_PATH.read_text(encoding="utf-8")) != evaluator:
        raise RuntimeError("Evaluator files or configuration changed after preflight")
    return manifest, artifacts


def usage_record(response: dict[str, Any], case_id: str, candidate_id: str, retries: int) -> dict[str, Any]:
    usage = response.get("usage", {})
    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    total_tokens = int(usage.get("total_tokens", input_tokens + output_tokens))
    cached = int(usage.get("input_tokens_details", {}).get("cached_tokens", 0) or 0)
    reasoning = int(usage.get("output_tokens_details", {}).get("reasoning_tokens", 0) or 0)
    cost = (
        (input_tokens - cached) * base.INPUT_PRICE_PER_MILLION
        + cached * base.CACHED_INPUT_PRICE_PER_MILLION
        + output_tokens * base.OUTPUT_PRICE_PER_MILLION
    ) / 1_000_000
    return {
        "case_id": case_id,
        "candidate_id": candidate_id,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning,
        "total_tokens": total_tokens,
        "estimated_api_cost_usd": f"{cost:.8f}",
        "model": response.get("model", MODEL),
        "response_id": response.get("id", ""),
        "retry_count": retries,
    }


def checkpoint_path(case_id: str, candidate_id: str) -> Path:
    return CHECKPOINT_ROOT / f"{case_id}__{candidate_id}.json"


def load_checkpoint(
    case_id: str,
    candidate_id: str,
    schema: dict[str, Any],
    request_record_sha256: str,
) -> dict[str, Any] | None:
    path = checkpoint_path(case_id, candidate_id)
    if not path.exists():
        return None
    checkpoint = json.loads(path.read_text(encoding="utf-8"))
    if checkpoint.get("request_record_sha256") != request_record_sha256:
        raise RuntimeError(f"Checkpoint request hash mismatch: {case_id}/{candidate_id}")
    base.validate_result(checkpoint["result"], case_id, candidate_id, schema)
    return checkpoint


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def candidate_table_row(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": result["case_id"],
        "candidate_id": result["candidate_id"],
        "overall_score": f"{float(result['overall_score']):.2f}",
        "severity": result["severity"],
        "confidence": result["confidence"],
        "main_error_type": result["main_error_type"],
        "ambiguity_flag": str(result["ambiguity_flag"]).lower(),
        "requires_human_review": str(result["requires_human_review"]).lower(),
        "action_status": result["action_assessment"]["status"],
        "flow_status": result["flow_assessment"]["status"],
        "control_flow_status": result["control_flow_assessment"]["status"],
        "action_summary": result["action_assessment"]["summary"],
        "flow_summary": result["flow_assessment"]["summary"],
        "control_flow_summary": result["control_flow_assessment"]["summary"],
        "explanation": result["explanation"],
        "ambiguity_explanation": result["ambiguity_explanation"],
        "review_reason": result["review_reason"],
    }


def cmd_run() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is unavailable")
    manifest, artifacts = verify_locked_manifest()
    developer_prompt, user_template = base.load_locked_prompt()
    schema_wrapper = base.load_locked_schema_wrapper()
    schema = schema_wrapper["schema"]
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    REQUEST_ROOT.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest["status"] = "api_evaluations_in_progress"
    manifest.setdefault("started_at_utc", utc_now())
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    completed_results: list[dict[str, Any]] = []
    completed_usage: list[dict[str, Any]] = []
    for index, artifact in enumerate(artifacts, start=1):
        case_id = artifact["case_id"]
        candidate_id = artifact["candidate_id"]
        paths = candidate_paths(case_id, candidate_id)
        process_text = paths["process"].read_text(encoding="utf-8")
        graph_json_text = paths["graph"].read_text(encoding="utf-8")
        graph = json.loads(graph_json_text)
        rendering = base.render_activity_graph(graph)
        user_prompt = base.instantiate_user_prompt(
            user_template,
            case_id,
            candidate_id,
            process_text,
            graph_json_text,
            rendering,
        )
        request_record = base.build_request_record(
            case_id,
            candidate_id,
            process_text,
            graph_json_text,
            rendering,
            user_prompt,
            developer_prompt,
        )
        record_text = json.dumps(request_record, ensure_ascii=False, indent=2) + "\n"
        record_sha = base.sha256_bytes(record_text.encode("utf-8"))
        record_path = REQUEST_ROOT / f"{case_id}__{candidate_id}.json"
        if record_path.exists():
            if base.sha256_file(record_path) != record_sha:
                raise RuntimeError(f"Existing request record changed: {case_id}/{candidate_id}")
        else:
            record_path.write_text(record_text, encoding="utf-8")

        existing = load_checkpoint(case_id, candidate_id, schema, record_sha)
        if existing is not None:
            completed_results.append(existing["result"])
            completed_usage.append(existing["usage"])
            print(f"[{index:03d}/120] checkpoint {case_id}/{candidate_id}", flush=True)
            continue

        payload = {
            "model": MODEL,
            "reasoning": {"effort": REASONING_EFFORT},
            "store": False,
            "input": [
                {
                    "role": "developer",
                    "content": [{"type": "input_text", "text": developer_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            "text": {"format": schema_wrapper},
        }
        completed_response: dict[str, Any] | None = None
        completed_result: dict[str, Any] | None = None
        last_error: Exception | None = None
        attempts_used = 0
        for attempt in range(1, 3):
            attempts_used = attempt
            try:
                response = base.post_response(payload, api_key)
                raw_path = RAW_ROOT / f"{case_id}__{candidate_id}__attempt_{attempt}.json"
                raw_path.write_text(
                    json.dumps(response, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                if response.get("status") != "completed":
                    raise ValueError(f"Response status was {response.get('status')!r}")
                result = json.loads(base.extract_output_text(response))
                base.validate_result(result, case_id, candidate_id, schema)
                completed_response = response
                completed_result = result
                break
            except Exception as exc:
                last_error = exc
                error_payload: dict[str, Any] = {
                    "case_id": case_id,
                    "candidate_id": candidate_id,
                    "attempt": attempt,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "timestamp_utc": utc_now(),
                }
                if isinstance(exc, urllib.error.HTTPError):
                    try:
                        error_payload["http_body"] = exc.read().decode("utf-8")
                    except Exception:
                        pass
                (RAW_ROOT / f"{case_id}__{candidate_id}__attempt_{attempt}__error.json").write_text(
                    json.dumps(error_payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                if attempt == 1:
                    time.sleep(1)
        if completed_response is None or completed_result is None:
            raise RuntimeError(
                f"Failed {case_id}/{candidate_id} after two attempts: {last_error}"
            )

        usage = usage_record(
            completed_response,
            case_id,
            candidate_id,
            attempts_used - 1,
        )
        checkpoint = {
            "case_id": case_id,
            "candidate_id": candidate_id,
            "completed_at_utc": utc_now(),
            "request_record_sha256": record_sha,
            "result": completed_result,
            "usage": usage,
        }
        checkpoint_path(case_id, candidate_id).write_text(
            json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        completed_results.append(completed_result)
        completed_usage.append(usage)
        manifest["completed_candidate_count"] = len(completed_results)
        manifest["last_completed_identity"] = [case_id, candidate_id]
        manifest["last_updated_at_utc"] = utc_now()
        MANIFEST_PATH.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            f"[{index:03d}/120] completed {case_id}/{candidate_id} "
            f"tokens={usage['total_tokens']} retries={usage['retry_count']}",
            flush=True,
        )

    identities = [(item["case_id"], item["candidate_id"]) for item in completed_results]
    if tuple(identities) != EXPECTED_PAIRS:
        raise RuntimeError("Completed result order differs from locked formal cohort")
    RESULTS_PATH.write_text(
        "".join(
            json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
            for item in completed_results
        ),
        encoding="utf-8",
    )
    write_csv(USAGE_PATH, completed_usage)
    write_csv(TABLE_PATH, [candidate_table_row(item) for item in completed_results])
    manifest["status"] = "api_evaluations_complete"
    manifest["completed_at_utc"] = utc_now()
    manifest["completed_candidate_count"] = EXPECTED_COUNT
    manifest["total_retry_count"] = sum(int(row["retry_count"]) for row in completed_usage)
    manifest["human_labels_accessed"] = False
    manifest["results_sha256"] = base.sha256_file(RESULTS_PATH)
    manifest["usage_sha256"] = base.sha256_file(USAGE_PATH)
    manifest["candidate_table_sha256"] = base.sha256_file(TABLE_PATH)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("All 120 independent formal evaluations completed; no human labels were accessed")


def load_final_results() -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in RESULTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(rows) != EXPECTED_COUNT:
        raise ValueError(f"Expected 120 formal results, found {len(rows)}")
    if tuple((row["case_id"], row["candidate_id"]) for row in rows) != EXPECTED_PAIRS:
        raise ValueError("Formal result identities differ from locked cohort")
    schema = base.load_locked_schema_wrapper()["schema"]
    for row in rows:
        base.validate_result(row, row["case_id"], row["candidate_id"], schema)
    return rows


def markdown_candidate_list(title: str, rows: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not rows:
        return lines + ["None.", ""]
    lines.extend(
        [
            "| Case | Candidate | Score | Confidence | Ambiguity | Human review | Main error type |",
            "|---|---|---:|---|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['case_id']} | {row['candidate_id']} | {float(row['overall_score']):.2f} | "
            f"{row['confidence']} | {str(row['ambiguity_flag']).lower()} | "
            f"{str(row['requires_human_review']).lower()} | {row['main_error_type']} |"
        )
    lines.append("")
    return lines


def distribution_table(title: str, counts: Counter[str], order: list[str] | None = None) -> list[str]:
    keys = order if order is not None else sorted(counts)
    lines = [f"### {title}", "", "| Value | Count | Percent |", "|---|---:|---:|"]
    for key in keys:
        count = counts.get(key, 0)
        lines.append(f"| {key} | {count} | {count / EXPECTED_COUNT:.1%} |")
    lines.append("")
    return lines


def cmd_aggregate() -> None:
    if not all(path.is_file() for path in (RESULTS_PATH, USAGE_PATH, TABLE_PATH, MANIFEST_PATH)):
        raise RuntimeError("Complete all formal evaluations before aggregation")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("status") != "api_evaluations_complete":
        raise RuntimeError("Formal manifest does not confirm completed API evaluations")
    results = load_final_results()
    with USAGE_PATH.open(encoding="utf-8", newline="") as handle:
        usage = list(csv.DictReader(handle))
    if len(usage) != EXPECTED_COUNT:
        raise ValueError("Formal usage table does not contain 120 rows")

    scores = [float(row["overall_score"]) for row in results]
    candidate_macro = sum(scores) / EXPECTED_COUNT
    scores_by_case: dict[str, list[float]] = defaultdict(list)
    for row in results:
        scores_by_case[row["case_id"]].append(float(row["overall_score"]))
    if set(scores_by_case) != set(CASES) or any(len(values) != 3 for values in scores_by_case.values()):
        raise ValueError("Formal case balance differs from 40 cases x 3 candidates")
    case_means = {case_id: sum(values) / len(values) for case_id, values in scores_by_case.items()}
    equal_case_macro = sum(case_means.values()) / len(case_means)

    score_counts = Counter(f"{float(row['overall_score']):.2f}" for row in results)
    confidence_counts = Counter(row["confidence"] for row in results)
    error_counts = Counter(row["main_error_type"] for row in results)
    action_counts = Counter(row["action_assessment"]["status"] for row in results)
    flow_counts = Counter(row["flow_assessment"]["status"] for row in results)
    control_counts = Counter(row["control_flow_assessment"]["status"] for row in results)
    ambiguity_rows = [row for row in results if row["ambiguity_flag"]]
    review_rows = [row for row in results if row["requires_human_review"]]
    lower_confidence_rows = [row for row in results if row["confidence"] in {"low", "medium"}]

    total_input = sum(int(row["input_tokens"]) for row in usage)
    total_cached = sum(int(row["cached_input_tokens"]) for row in usage)
    total_output = sum(int(row["output_tokens"]) for row in usage)
    total_reasoning = sum(int(row["reasoning_tokens"]) for row in usage)
    total_tokens = sum(int(row["total_tokens"]) for row in usage)
    total_cost = sum(float(row["estimated_api_cost_usd"]) for row in usage)
    total_retries = sum(int(row["retry_count"]) for row in usage)

    report: list[str] = [
        "# AI Evaluator V2 formal 120-candidate report",
        "",
        "## Run integrity",
        "",
        "- Execution: **120/120 candidates completed successfully**.",
        "- Cohort: **40 frozen cases x 3 frozen candidates**.",
        f"- Model: `{MODEL}`; reasoning effort: `{REASONING_EFFORT}`.",
        f"- Prompt: `{PROMPT_VERSION}`; schema: `{SCHEMA_VERSION}`.",
        "- Calls were independent, stateless, non-Batch, and used `store=false`.",
        "- Temperature and `top_p` were omitted; seed was unsupported/omitted.",
        "- Human labels, rationales, code-evaluator results, BPMN references, prior diagnoses, calibration results, and holdout results were not evaluator inputs.",
        f"- Technical retries: **{total_retries}**.",
        "",
        "## Aggregate semantic-quality results",
        "",
        f"- Mean whole-graph semantic-quality score: **{candidate_macro:.4f}**.",
        f"- Candidate-level macro average: **{candidate_macro:.4f}**.",
        f"- Equal-case macro average: **{equal_case_macro:.4f}**.",
        "- Candidate and equal-case averages are identical because every case contributes exactly three candidates.",
        "",
        "### Score distribution",
        "",
        "| Score | Count | Percent |",
        "|---:|---:|---:|",
    ]
    for score in ("1.00", "0.75", "0.50", "0.25", "0.00"):
        count = score_counts.get(score, 0)
        report.append(f"| {score} | {count} | {count / EXPECTED_COUNT:.1%} |")
    report.extend(
        [
            "",
            "## Uncertainty and review",
            "",
            f"- `ambiguity_flag=true`: **{len(ambiguity_rows)}/120 ({len(ambiguity_rows)/120:.1%})**.",
            f"- `requires_human_review=true`: **{len(review_rows)}/120 ({len(review_rows)/120:.1%})**.",
            "",
        ]
    )
    report.extend(distribution_table("Confidence distribution", confidence_counts, ["high", "medium", "low"]))
    report.extend(distribution_table("Main error type distribution", error_counts))
    report.extend(distribution_table("Action diagnostic status", action_counts, ["preserved", "defect", "uncertain", "not_applicable"]))
    report.extend(distribution_table("Flow diagnostic status", flow_counts, ["preserved", "defect", "uncertain", "not_applicable"]))
    report.extend(distribution_table("Control-Flow diagnostic status", control_counts, ["preserved", "defect", "uncertain", "not_applicable"]))
    report.extend(
        [
            "## Token usage and estimated API cost",
            "",
            f"- Input tokens: **{total_input:,}** ({total_cached:,} cached).",
            f"- Output tokens: **{total_output:,}**, including **{total_reasoning:,} reasoning tokens**.",
            f"- Total tokens: **{total_tokens:,}**.",
            f"- Estimated API cost: **${total_cost:.4f}**.",
            f"- Average estimated cost per candidate: **${total_cost / EXPECTED_COUNT:.4f}**.",
            "- Cost estimate uses $2.50/M uncached input tokens, $0.25/M cached input tokens, and $15.00/M output tokens.",
            "",
        ]
    )
    report.extend(markdown_candidate_list("Candidates with ambiguity_flag=true", ambiguity_rows))
    report.extend(markdown_candidate_list("Candidates with requires_human_review=true", review_rows))
    report.extend(markdown_candidate_list("Candidates with low or medium confidence", lower_confidence_rows))
    report.extend(
        [
            "## Documented evaluator limitations",
            "",
            "- Scores are discrete rubric judgments, not continuous measurements; adjacent-level boundary uncertainty remains possible.",
            "- The process text is the primary semantic authority. Ambiguous source wording can yield multiple defensible graph interpretations; flags and review metadata should be retained alongside scores.",
            "- Action, Flow, and Control-Flow are diagnostic dimensions, not independently weighted subscores, so the aggregate score cannot be decomposed mathematically into those statuses.",
            "- Calls are independent and seed is unsupported, so exact repeatability of natural-language diagnoses is not guaranteed even with frozen inputs and settings.",
            "- This formal report is descriptive and intentionally contains no comparison with human labels.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest["status"] = "aggregate_complete"
    manifest["aggregate_completed_at_utc"] = utc_now()
    manifest["human_labels_accessed"] = False
    manifest["report_sha256"] = base.sha256_file(REPORT_PATH)
    manifest["aggregate"] = {
        "mean_whole_graph_score": candidate_macro,
        "candidate_macro_average": candidate_macro,
        "equal_case_macro_average": equal_case_macro,
        "ambiguity_count": len(ambiguity_rows),
        "requires_human_review_count": len(review_rows),
        "total_tokens": total_tokens,
        "estimated_api_cost_usd": total_cost,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Formal aggregation complete: mean={candidate_macro:.4f} "
        f"ambiguity={len(ambiguity_rows)} review={len(review_rows)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run", "aggregate"))
    args = parser.parse_args()
    if args.command == "preflight":
        cmd_preflight()
    elif args.command == "run":
        cmd_run()
    else:
        cmd_aggregate()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
