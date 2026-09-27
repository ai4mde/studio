#!/usr/bin/env python3
"""Locked AI Evaluator V2 calibration runner.

The commands are deliberately separated:

* preflight: validates prompts, schema, and frozen candidate artifacts;
* run: makes independent stateless Responses API calls and never reads human labels;
* compare: becomes available only after 18 valid results exist.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = ROOT / "ai_evaluator_v2_prompt_final_draft.md"
SCHEMA_PATH = ROOT / "ai_evaluator_v2_output_schema.md"
COHORT_ROOT = ROOT / "evaluation/friedrich_v2/cohorts/final_frozen_40x3_20260910"
REVIEW_ROOT = ROOT / "evaluation/friedrich_v2/review/human_calibration_selected_cases"
HUMAN_LABELS_PATH = REVIEW_ROOT / "human_calibration.csv"

RESULTS_PATH = ROOT / "ai_v2_calibration_results.jsonl"
USAGE_PATH = ROOT / "ai_v2_calibration_usage.csv"
COMPARISON_PATH = ROOT / "ai_v2_calibration_comparison.csv"
REPORT_PATH = ROOT / "ai_v2_calibration_report.md"
SUPPORT_ROOT = ROOT / "evaluation/friedrich_v2/results/ai_v2_calibration_18_20260923"
RAW_ROOT = SUPPORT_ROOT / "raw_responses"
REQUEST_ROOT = SUPPORT_ROOT / "request_records"
MANIFEST_PATH = SUPPORT_ROOT / "run_manifest.json"

MODEL = "gpt-5.4-2026-03-05"
REASONING_EFFORT = "medium"
PROMPT_VERSION = "ai-evaluator-v2-prompt/1.0"
SCHEMA_VERSION = "ai-evaluator-v2/1.0"
INPUT_PRICE_PER_MILLION = 2.50
CACHED_INPUT_PRICE_PER_MILLION = 0.25
OUTPUT_PRICE_PER_MILLION = 15.00

CASES = ("1-1", "3-2", "3-4", "6-4", "8-2", "9-5")
CANDIDATES = ("candidate_1", "candidate_2", "candidate_3")
EXPECTED_PAIRS = tuple((case_id, candidate_id) for case_id in CASES for candidate_id in CANDIDATES)
EXPECTED_COUNT = len(EXPECTED_PAIRS)
RUN_KIND = "calibration"
SCORE_LEVELS = (1.0, 0.75, 0.5, 0.25, 0.0)
SEVERITY_BY_SCORE = {
    1.0: "none",
    0.75: "minor",
    0.5: "moderate",
    0.25: "major",
    0.0: "fundamental",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def decode_text_artifact(path: Path) -> str:
    data = path.read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252")


def extract_fenced_block(text: str, heading: str, language: str) -> str:
    marker = f"## {heading}"
    if marker not in text:
        raise ValueError(f"Missing heading: {marker}")
    section = text.split(marker, 1)[1]
    match = re.search(rf"```{re.escape(language)}\n(.*?)\n```", section, re.DOTALL)
    if not match:
        raise ValueError(f"Missing {language!r} fenced block after {marker}")
    return match.group(1)


def load_locked_prompt() -> tuple[str, str]:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    if f"Prompt version: `{PROMPT_VERSION}`" not in text:
        raise ValueError(f"Prompt version {PROMPT_VERSION!r} is not declared")
    if f"Model: `{MODEL}`" not in text:
        raise ValueError(f"Model {MODEL!r} is not declared")
    developer = extract_fenced_block(text, "Exact developer prompt", "text")
    user_template = extract_fenced_block(text, "Exact candidate-level user prompt template", "text")
    required_placeholders = {
        "{{CASE_ID}}",
        "{{CANDIDATE_ID}}",
        "{{ORIGINAL_PROCESS_TEXT}}",
        "{{ACTIVITY_GRAPH_JSON}}",
        "{{DETERMINISTIC_TEXTUAL_RENDERING}}",
    }
    found = set(re.findall(r"\{\{[A-Z_]+\}\}", user_template))
    if found != required_placeholders:
        raise ValueError(f"Unexpected prompt placeholders: {sorted(found)}")
    return developer, user_template


def load_locked_schema_wrapper() -> dict[str, Any]:
    text = SCHEMA_PATH.read_text(encoding="utf-8")
    if f"Schema version: `{SCHEMA_VERSION}`" not in text:
        raise ValueError(f"Schema version {SCHEMA_VERSION!r} is not declared")
    match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
    if not match:
        raise ValueError("Strict schema JSON block not found")
    wrapper = json.loads(match.group(1))
    if wrapper.get("type") != "json_schema" or wrapper.get("strict") is not True:
        raise ValueError("Schema wrapper is not strict json_schema")
    schema = wrapper.get("schema")
    if not isinstance(schema, dict):
        raise ValueError("Schema object missing")
    if schema.get("additionalProperties") is not False:
        raise ValueError("Root schema must forbid additional properties")
    properties = schema.get("properties", {})
    if set(schema.get("required", [])) != set(properties):
        raise ValueError("Every root schema field must be required")
    version_values = properties["schema_version"].get("enum")
    if version_values != [SCHEMA_VERSION]:
        raise ValueError("Schema version enum does not match locked version")
    return wrapper


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def render_activity_graph(graph: dict[str, Any]) -> str:
    """Lossless deterministic line rendering derived only from ActivityGraph JSON."""
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("ActivityGraph must contain nodes and edges arrays")
    sorted_nodes = sorted(nodes, key=lambda item: (str(item.get("id", "")), canonical_json(item)))
    sorted_edges = sorted(
        edges,
        key=lambda item: (
            str(item.get("source", "")),
            str(item.get("target", "")),
            str(item.get("type", "")),
            str(item.get("label", "")),
            canonical_json(item),
        ),
    )
    lines = ["ActivityGraph deterministic textual rendering v1", "NODES"]
    lines.extend(f"node {canonical_json(node)}" for node in sorted_nodes)
    lines.append("EDGES")
    lines.extend(f"edge {canonical_json(edge)}" for edge in sorted_edges)
    return "\n".join(lines)


def candidate_paths(case_id: str, candidate_id: str) -> dict[str, Path]:
    candidate_root = COHORT_ROOT / "cases" / case_id / candidate_id
    number = candidate_id.removeprefix("candidate_")
    return {
        "process": COHORT_ROOT / "cases" / case_id / "process_text.txt",
        "candidate_process": candidate_root / "process_text.txt",
        "graph": candidate_root / "activity_graph.json",
        "manifest": candidate_root / "candidate_manifest.json",
        "review_process": REVIEW_ROOT / case_id / "process_text.txt",
        "review_graph": REVIEW_ROOT / case_id / f"generated_candidate_{number}_activity_graph.json",
    }


def validate_artifacts() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for case_id, candidate_id in EXPECTED_PAIRS:
        paths = candidate_paths(case_id, candidate_id)
        for label, path in paths.items():
            if not path.is_file():
                raise FileNotFoundError(f"Missing {label}: {path}")
        manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
        if manifest.get("case_id") != case_id or manifest.get("candidate_id") != candidate_id:
            raise ValueError(f"Manifest identity mismatch for {case_id}/{candidate_id}")
        process_hash = sha256_file(paths["process"])
        graph_hash = sha256_file(paths["graph"])
        if sha256_file(paths["candidate_process"]) != process_hash:
            raise ValueError(f"Candidate process text mismatch for {case_id}/{candidate_id}")
        review_process_hash = sha256_file(paths["review_process"])
        if review_process_hash != process_hash:
            frozen_text = paths["process"].read_text(encoding="utf-8")
            review_text = decode_text_artifact(paths["review_process"])
            if review_text != frozen_text:
                raise ValueError(f"Review process text mismatch for {case_id}/{candidate_id}")
        if sha256_file(paths["review_graph"]) != graph_hash:
            raise ValueError(f"Review graph mismatch for {case_id}/{candidate_id}")
        artifact_hashes = manifest.get("artifact_hashes", {})
        if artifact_hashes.get("process_text.txt") != process_hash:
            raise ValueError(f"Manifest process hash mismatch for {case_id}/{candidate_id}")
        if artifact_hashes.get("activity_graph.json") != graph_hash:
            raise ValueError(f"Manifest graph hash mismatch for {case_id}/{candidate_id}")
        graph = json.loads(paths["graph"].read_text(encoding="utf-8"))
        rendering = render_activity_graph(graph)
        identity = (case_id, candidate_id)
        if identity in seen:
            raise ValueError(f"Duplicate candidate identity: {identity}")
        seen.add(identity)
        records.append(
            {
                "case_id": case_id,
                "candidate_id": candidate_id,
                "process_text_path": str(paths["process"].relative_to(ROOT)),
                "process_text_sha256": process_hash,
                "review_process_text_sha256": review_process_hash,
                "review_process_byte_identical": review_process_hash == process_hash,
                "review_process_text_equivalent": True,
                "activity_graph_path": str(paths["graph"].relative_to(ROOT)),
                "activity_graph_sha256": graph_hash,
                "rendering_sha256": sha256_bytes(rendering.encode("utf-8")),
                "node_count": len(graph["nodes"]),
                "edge_count": len(graph["edges"]),
            }
        )
    if tuple(seen) == () or len(records) != EXPECTED_COUNT or seen != set(EXPECTED_PAIRS):
        raise ValueError(
            f"{RUN_KIND.title()} candidate set is not exactly the locked "
            f"{EXPECTED_COUNT} candidates"
        )
    return records


def instantiate_user_prompt(
    template: str,
    case_id: str,
    candidate_id: str,
    process_text: str,
    graph_json_text: str,
    rendering: str,
) -> str:
    replacements = {
        "{{CASE_ID}}": case_id,
        "{{CANDIDATE_ID}}": candidate_id,
        "{{ORIGINAL_PROCESS_TEXT}}": process_text,
        "{{ACTIVITY_GRAPH_JSON}}": graph_json_text,
        "{{DETERMINISTIC_TEXTUAL_RENDERING}}": rendering,
    }
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    if re.search(r"\{\{[A-Z_]+\}\}", result):
        raise ValueError("Unresolved candidate prompt placeholder")
    return result


def validate_result(result: dict[str, Any], case_id: str, candidate_id: str, schema: dict[str, Any]) -> None:
    required = set(schema["required"])
    if set(result) != required:
        raise ValueError(f"Result fields differ from schema: {set(result) ^ required}")
    if result["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Wrong schema_version")
    if result["case_id"] != case_id or result["candidate_id"] != candidate_id:
        raise ValueError("Result identity does not match request")
    score = float(result["overall_score"])
    if score not in SEVERITY_BY_SCORE:
        raise ValueError("Invalid score")
    if result["severity"] != SEVERITY_BY_SCORE[score]:
        raise ValueError("Score/severity mismatch")
    if (result["main_error_type"] == "none") != (score == 1.0):
        raise ValueError("Score/main_error_type mismatch")
    if bool(result["ambiguity_explanation"]) != bool(result["ambiguity_flag"]):
        raise ValueError("Ambiguity explanation invariant failed")
    if bool(result["review_reason"]) != bool(result["requires_human_review"]):
        raise ValueError("Review reason invariant failed")
    for field in ("action_assessment", "flow_assessment", "control_flow_assessment"):
        value = result[field]
        if not isinstance(value, dict) or set(value) != {"status", "summary"}:
            raise ValueError(f"Invalid {field}")


def extract_output_text(response: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                chunks.append(content.get("text", ""))
            elif content.get("type") == "refusal":
                raise ValueError(f"Model refusal: {content.get('refusal', '')}")
    if not chunks:
        raise ValueError("Response contained no output_text")
    return "".join(chunks)


def post_response(payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.loads(response.read().decode("utf-8"))


def build_request_record(
    case_id: str,
    candidate_id: str,
    process_text: str,
    graph_json_text: str,
    rendering: str,
    user_prompt: str,
    developer_prompt: str,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "candidate_id": candidate_id,
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "temperature": "omitted",
        "top_p": "omitted",
        "seed": "unsupported/omitted",
        "store": False,
        "stateless": True,
        "batch": False,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "developer_prompt_sha256": sha256_bytes(developer_prompt.encode("utf-8")),
        "user_prompt_sha256": sha256_bytes(user_prompt.encode("utf-8")),
        "process_text_sha256": sha256_bytes(process_text.encode("utf-8")),
        "activity_graph_sha256": sha256_bytes(graph_json_text.encode("utf-8")),
        "rendering_sha256": sha256_bytes(rendering.encode("utf-8")),
        "input_components": [
            "case_id",
            "candidate_id",
            "original_process_text",
            "frozen_activity_graph_json",
            "deterministic_textual_rendering",
        ],
    }


def cmd_preflight() -> None:
    developer_prompt, user_template = load_locked_prompt()
    schema_wrapper = load_locked_schema_wrapper()
    artifacts = validate_artifacts()
    SUPPORT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "status": "preflight_passed",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "temperature": "omitted",
        "top_p": "omitted",
        "seed": "unsupported/omitted",
        "batch": False,
        "independent_stateless_calls": True,
        "api_storage": False,
        "automatic_sdk_retries": 0,
        "maximum_technical_retries_per_candidate": 1,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "prompt_file": str(PROMPT_PATH.relative_to(ROOT)),
        "prompt_file_sha256": sha256_file(PROMPT_PATH),
        "schema_file": str(SCHEMA_PATH.relative_to(ROOT)),
        "schema_file_sha256": sha256_file(SCHEMA_PATH),
        "developer_prompt_sha256": sha256_bytes(developer_prompt.encode("utf-8")),
        "user_template_sha256": sha256_bytes(user_template.encode("utf-8")),
        "strict_schema_sha256": sha256_bytes(canonical_json(schema_wrapper).encode("utf-8")),
        "renderer": "activity-graph-deterministic-text-v1",
        "candidate_count": len(artifacts),
        "candidates": artifacts,
        "human_labels_accessed_by_preflight": False,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Preflight passed for {len(artifacts)} frozen candidates")
    print(f"Prompt version: {PROMPT_VERSION}")
    print(f"Schema version: {SCHEMA_VERSION}")
    print(f"Manifest: {MANIFEST_PATH.relative_to(ROOT)}")


def cmd_run() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is unavailable")
    developer_prompt, user_template = load_locked_prompt()
    schema_wrapper = load_locked_schema_wrapper()
    schema = schema_wrapper["schema"]
    artifacts = validate_artifacts()
    if not MANIFEST_PATH.is_file():
        raise RuntimeError("Run preflight before API execution")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("status") != "preflight_passed":
        raise RuntimeError("Preflight manifest is not locked for execution")
    if manifest.get("prompt_file_sha256") != sha256_file(PROMPT_PATH):
        raise RuntimeError("Prompt changed after preflight")
    if manifest.get("schema_file_sha256") != sha256_file(SCHEMA_PATH):
        raise RuntimeError("Schema changed after preflight")
    if RESULTS_PATH.exists() or USAGE_PATH.exists():
        raise FileExistsError(f"{RUN_KIND.title()} outputs already exist; refusing to overwrite")

    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    REQUEST_ROOT.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    usage_rows: list[dict[str, Any]] = []

    for index, artifact in enumerate(artifacts, start=1):
        case_id = artifact["case_id"]
        candidate_id = artifact["candidate_id"]
        paths = candidate_paths(case_id, candidate_id)
        process_text = paths["process"].read_text(encoding="utf-8")
        graph_json_text = paths["graph"].read_text(encoding="utf-8")
        graph = json.loads(graph_json_text)
        rendering = render_activity_graph(graph)
        user_prompt = instantiate_user_prompt(
            user_template,
            case_id,
            candidate_id,
            process_text,
            graph_json_text,
            rendering,
        )
        request_record = build_request_record(
            case_id,
            candidate_id,
            process_text,
            graph_json_text,
            rendering,
            user_prompt,
            developer_prompt,
        )
        record_path = REQUEST_ROOT / f"{case_id}__{candidate_id}.json"
        record_path.write_text(json.dumps(request_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

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
                response = post_response(payload, api_key)
                raw_path = RAW_ROOT / f"{case_id}__{candidate_id}__attempt_{attempt}.json"
                raw_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                if response.get("status") != "completed":
                    raise ValueError(f"Response status was {response.get('status')!r}")
                result = json.loads(extract_output_text(response))
                validate_result(result, case_id, candidate_id, schema)
                completed_response = response
                completed_result = result
                break
            except Exception as exc:  # one exact-request retry for technical failures
                last_error = exc
                error_path = RAW_ROOT / f"{case_id}__{candidate_id}__attempt_{attempt}__error.json"
                error_payload = {
                    "case_id": case_id,
                    "candidate_id": candidate_id,
                    "attempt": attempt,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                }
                if isinstance(exc, urllib.error.HTTPError):
                    try:
                        error_payload["http_body"] = exc.read().decode("utf-8")
                    except Exception:
                        pass
                error_path.write_text(json.dumps(error_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                if attempt == 1:
                    time.sleep(1)
        if completed_response is None or completed_result is None:
            raise RuntimeError(f"Failed {case_id}/{candidate_id} after two attempts: {last_error}")

        usage = completed_response.get("usage", {})
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        total_tokens = int(usage.get("total_tokens", input_tokens + output_tokens))
        cached_input_tokens = int(usage.get("input_tokens_details", {}).get("cached_tokens", 0) or 0)
        reasoning_tokens = int(usage.get("output_tokens_details", {}).get("reasoning_tokens", 0) or 0)
        uncached_input_tokens = input_tokens - cached_input_tokens
        estimated_cost = (
            uncached_input_tokens * INPUT_PRICE_PER_MILLION
            + cached_input_tokens * CACHED_INPUT_PRICE_PER_MILLION
            + output_tokens * OUTPUT_PRICE_PER_MILLION
        ) / 1_000_000
        results.append(completed_result)
        usage_rows.append(
            {
                "case_id": case_id,
                "candidate_id": candidate_id,
                "input_tokens": input_tokens,
                "cached_input_tokens": cached_input_tokens,
                "output_tokens": output_tokens,
                "reasoning_tokens": reasoning_tokens,
                "total_tokens": total_tokens,
                "estimated_api_cost_usd": f"{estimated_cost:.8f}",
                "model": completed_response.get("model", MODEL),
                "response_id": completed_response.get("id", ""),
                "retry_count": attempts_used - 1,
            }
        )
        print(
            f"[{index:02d}/{EXPECTED_COUNT:02d}] completed {case_id}/{candidate_id} "
            f"tokens={total_tokens} retries={attempts_used - 1}",
            flush=True,
        )

    RESULTS_PATH.write_text(
        "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in results),
        encoding="utf-8",
    )
    usage_fields = list(usage_rows[0])
    with USAGE_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=usage_fields)
        writer.writeheader()
        writer.writerows(usage_rows)
    manifest["status"] = "api_evaluations_complete"
    manifest["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["successful_candidate_count"] = len(results)
    manifest["total_retry_count"] = sum(int(row["retry_count"]) for row in usage_rows)
    manifest["human_labels_accessed_by_run"] = False
    manifest["results_sha256"] = sha256_file(RESULTS_PATH)
    manifest["usage_sha256"] = sha256_file(USAGE_PATH)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"All {EXPECTED_COUNT} independent API evaluations completed; "
        "human labels were not accessed"
    )


def read_results() -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in RESULTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != EXPECTED_COUNT:
        raise ValueError(f"Expected {EXPECTED_COUNT} results, found {len(rows)}")
    identities = [(row["case_id"], row["candidate_id"]) for row in rows]
    if tuple(identities) != EXPECTED_PAIRS:
        raise ValueError("Result identities/order differ from locked candidate list")
    return rows


def load_human_labels_after_completion() -> dict[tuple[str, str], dict[str, str]]:
    labels: dict[tuple[str, str], dict[str, str]] = {}
    with HUMAN_LABELS_PATH.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            identity = (row["Case"], row["Candidate"])
            if identity in set(EXPECTED_PAIRS):
                labels[identity] = row
    if set(labels) != set(EXPECTED_PAIRS):
        missing = sorted(set(EXPECTED_PAIRS) - set(labels))
        raise ValueError(f"Missing human {RUN_KIND} labels: {missing}")
    return labels


def fmt_score(score: float) -> str:
    return f"{score:.2f}"


def cmd_compare() -> None:
    if not RESULTS_PATH.is_file() or not USAGE_PATH.is_file() or not MANIFEST_PATH.is_file():
        raise RuntimeError("All API evaluations must complete before comparison")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if (
        manifest.get("status") != "api_evaluations_complete"
        or manifest.get("successful_candidate_count") != EXPECTED_COUNT
    ):
        raise RuntimeError(
            f"Run manifest does not confirm {EXPECTED_COUNT} completed evaluations"
        )
    results = read_results()
    labels = load_human_labels_after_completion()
    comparison_rows: list[dict[str, Any]] = []
    for result in results:
        identity = (result["case_id"], result["candidate_id"])
        human = labels[identity]
        human_score = float(human["Human Score"])
        ai_score = float(result["overall_score"])
        difference = abs(ai_score - human_score)
        comparison_rows.append(
            {
                "case_id": identity[0],
                "candidate_id": identity[1],
                "human_score": fmt_score(human_score),
                "ai_score": fmt_score(ai_score),
                "absolute_difference": fmt_score(difference),
                "exact_match": str(difference == 0).lower(),
                "within_one_level": str(difference <= 0.25).lower(),
                "human_judgement": human["Human Judgement"],
                "ai_severity": result["severity"],
                "ai_confidence": result["confidence"],
                "ai_requires_human_review": str(result["requires_human_review"]).lower(),
            }
        )
    with COMPARISON_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparison_rows[0]))
        writer.writeheader()
        writer.writerows(comparison_rows)

    ai_counts = Counter(float(row["ai_score"]) for row in comparison_rows)
    human_counts = Counter(float(row["human_score"]) for row in comparison_rows)
    exact = sum(row["exact_match"] == "true" for row in comparison_rows)
    within = sum(row["within_one_level"] == "true" for row in comparison_rows)
    differences = [float(row["absolute_difference"]) for row in comparison_rows]
    severe = sum(value >= 0.5 for value in differences)
    total_input = total_cached = total_output = total_reasoning = total_tokens = 0
    total_cost = 0.0
    retry_count = 0
    with USAGE_PATH.open(encoding="utf-8", newline="") as handle:
        usage_rows = list(csv.DictReader(handle))
    for row in usage_rows:
        total_input += int(row["input_tokens"])
        total_cached += int(row["cached_input_tokens"])
        total_output += int(row["output_tokens"])
        total_reasoning += int(row["reasoning_tokens"])
        total_tokens += int(row["total_tokens"])
        total_cost += float(row["estimated_api_cost_usd"])
        retry_count += int(row["retry_count"])

    result_by_id = {(row["case_id"], row["candidate_id"]): row for row in results}
    disagreements = [row for row in comparison_rows if row["exact_match"] != "true"]
    matrix = {
        human_score: {ai_score: 0 for ai_score in SCORE_LEVELS}
        for human_score in SCORE_LEVELS
    }
    for row in comparison_rows:
        matrix[float(row["human_score"])][float(row["ai_score"])] += 1

    report: list[str] = [
        f"# AI Evaluator V2 {RUN_KIND} report",
        "",
        "## Run status",
        "",
        f"- Execution: **{EXPECTED_COUNT}/{EXPECTED_COUNT} candidates completed successfully**.",
        f"- Model: `{MODEL}`; reasoning effort: `{REASONING_EFFORT}`.",
        "- Calls: independent, stateless, non-Batch Responses API calls with `store=false`.",
        "- Temperature, `top_p`, and seed: omitted.",
        f"- Prompt version: `{PROMPT_VERSION}`.",
        f"- Output schema version: `{SCHEMA_VERSION}`.",
        f"- Technical retries: {retry_count}.",
        f"- Human labels were loaded only after all {EXPECTED_COUNT} valid AI results had been saved.",
        "",
        f"## Aggregate {RUN_KIND} metrics",
        "",
        f"- Exact matches: **{exact}/{EXPECTED_COUNT} ({exact / EXPECTED_COUNT:.1%})**.",
        f"- Within one level (absolute difference <= 0.25): **{within}/{EXPECTED_COUNT} ({within / EXPECTED_COUNT:.1%})**.",
        f"- Mean absolute error (MAE): **{sum(differences) / EXPECTED_COUNT:.3f}**.",
        f"- Severe disagreements (absolute difference >= 0.50): **{severe}**.",
        "",
        "## Score distributions",
        "",
        "| Score | Human | AI |",
        "|---:|---:|---:|",
    ]
    for score in SCORE_LEVELS:
        report.append(f"| {score:.2f} | {human_counts[score]} | {ai_counts[score]} |")
    report.extend(
        [
            "",
            "## Confusion matrix",
            "",
            "Rows are human scores; columns are AI scores.",
            "",
            "| Human \\ AI | 1.00 | 0.75 | 0.50 | 0.25 | 0.00 |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for human_score in SCORE_LEVELS:
        cells = " | ".join(str(matrix[human_score][ai_score]) for ai_score in SCORE_LEVELS)
        report.append(f"| {human_score:.2f} | {cells} |")

    report.extend(["", "## Candidate disagreements", ""])
    if not disagreements:
        report.append("No candidate-level score disagreements occurred.")
    else:
        report.extend(
            [
                "| Case | Candidate | Human | AI | Abs. diff. | AI confidence | AI review | AI diagnosis |",
                "|---|---|---:|---:|---:|---|---|---|",
            ]
        )
        for row in disagreements:
            result = result_by_id[(row["case_id"], row["candidate_id"])]
            explanation = result["explanation"].replace("|", "\\|").replace("\n", " ")
            report.append(
                f"| {row['case_id']} | {row['candidate_id']} | {row['human_score']} | "
                f"{row['ai_score']} | {row['absolute_difference']} | {row['ai_confidence']} | "
                f"{row['ai_requires_human_review']} | {explanation} |"
            )

    report.extend(
        [
            "",
            "## Disagreement-cause review",
            "",
            "This section is intentionally completed after execution. It should classify each disagreement as primarily a severity-boundary difference, source ambiguity, incorrect semantic diagnosis, whole-graph impact overestimation, or whole-graph impact underestimation. Human rationales may be consulted only for this post-run analysis.",
            "",
            "<!-- POST_RUN_CAUSE_ANALYSIS -->",
            "",
            "## Token usage and estimated API cost",
            "",
            f"- Input tokens: **{total_input:,}** ({total_cached:,} cached).",
            f"- Output tokens: **{total_output:,}**, including **{total_reasoning:,} reasoning tokens**.",
            f"- Total tokens: **{total_tokens:,}**.",
            f"- Estimated API cost: **${total_cost:.4f}**.",
            f"- Average estimated cost per candidate: **${total_cost / EXPECTED_COUNT:.4f}**.",
            "- Cost estimate uses $2.50/M uncached input tokens, $0.25/M cached input tokens, and $15.00/M output tokens.",
            "",
            f"## {RUN_KIND.title()} disposition",
            "",
            "<!-- POST_RUN_RECOMMENDATION -->",
            "",
            "The disposition must be selected after reviewing the completed metrics and disagreements:",
            "",
            "- A. Current evaluator is ready to freeze.",
            "- B. Minor prompt/rubric revision is needed.",
            "- C. Configuration/model appears insufficient.",
        ]
    )
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest["status"] = "comparison_complete"
    manifest["comparison_completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["human_labels_accessed_after_all_ai_calls"] = True
    manifest["comparison_sha256"] = sha256_file(COMPARISON_PATH)
    manifest["report_draft_sha256"] = sha256_file(REPORT_PATH)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Comparison complete: exact={exact}/{EXPECTED_COUNT} "
        f"within_one={within}/{EXPECTED_COUNT} "
        f"MAE={sum(differences)/EXPECTED_COUNT:.3f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run", "compare"))
    args = parser.parse_args()
    if args.command == "preflight":
        cmd_preflight()
    elif args.command == "run":
        cmd_run()
    else:
        cmd_compare()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
