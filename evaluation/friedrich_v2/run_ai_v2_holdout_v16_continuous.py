#!/usr/bin/env python3
"""Frozen v1.6 continuous developmental holdout; 15 candidates only."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
import urllib.error
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.friedrich_v2 import analyze_ai_v16_continuous as analysis  # noqa: E402
from evaluation.friedrich_v2 import run_ai_v2_calibration as legacy  # noqa: E402
from evaluation.friedrich_v2 import run_ai_v2_calibration_v16_continuous as frozen  # noqa: E402


RESULTS_ROOT = ROOT / "evaluation/friedrich_v2/results"
FREEZE_PATH = ROOT / "evaluation/friedrich_v2/frozen/ai_v16_continuous/ai_v16_frozen_evaluator_manifest.json"
HISTORICAL_HOLDOUT_PATH = ROOT / "evaluation/friedrich_v2/results/ai_v15_holdout_15_20260925/ai_v15_frozen_evaluator_manifest.json"
EARLIER_HOLDOUT_PATH = ROOT / "evaluation/friedrich_v2/results/ai_v2_holdout_15_prompt_v14_20260923/run_manifest.json"
HUMAN_LABELS_PATH = ROOT / "evaluation/friedrich_v2/review/human_calibration_selected_cases/human_calibration.csv"
SECRET_ENV_PATH = ROOT / "config/secrets.env"
CASES = ("3-5", "5-1", "10-9", "10-11", "10-14")
CANDIDATES = ("candidate_1", "candidate_2", "candidate_3")
PAIRS = tuple((case_id, candidate_id) for case_id in CASES for candidate_id in CANDIDATES)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def save_json(path: Path, value: object, *, new: bool = False) -> None:
    with path.open("x" if new else "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_api_key() -> str:
    """Use the calibration launch's `set -a; source config/secrets.env` mechanism."""
    existing = os.environ.get("OPENAI_API_KEY")
    if existing:
        return existing
    if not SECRET_ENV_PATH.is_file():
        raise RuntimeError(f"Calibration credential file is unavailable: {SECRET_ENV_PATH}")
    script = 'set -a\nsource "$1" >/dev/null\nset +a\n[[ -n ${OPENAI_API_KEY-} ]] || exit 3\nprint -r -n -- "$OPENAI_API_KEY"'
    loaded = subprocess.run(
        ["zsh", "-c", script, "holdout-credential", str(SECRET_ENV_PATH)],
        capture_output=True, text=True, check=False,
    )
    if loaded.returncode != 0 or not loaded.stdout:
        raise RuntimeError("OPENAI_API_KEY could not be loaded from the calibration credential file")
    os.environ["OPENAI_API_KEY"] = loaded.stdout
    return loaded.stdout


def resolve_run_dir(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if path.parent != RESULTS_ROOT.resolve() or not path.name.startswith("ai_v16_holdout_15_"):
        raise ValueError("Run directory must be a new ai_v16_holdout_15_* directory under the results root")
    return path


def paths(run_dir: Path) -> dict[str, Path]:
    return {
        "manifest": run_dir / "ai_v16_holdout_manifest.json",
        "slots": run_dir / "ai_v16_holdout_slots.json",
        "results": run_dir / "ai_v16_holdout_results.jsonl",
        "usage": run_dir / "ai_v16_holdout_usage.csv",
        "comparison": run_dir / "ai_v16_holdout_comparison.csv",
        "review": run_dir / "ai_v16_holdout_review_order.csv",
        "metrics": run_dir / "ai_v16_holdout_metrics.json",
        "report": run_dir / "ai_v16_holdout_report.md",
        "scatter": run_dir / "ai_v16_holdout_scatter.svg",
        "raw": run_dir / "raw_responses",
        "requests": run_dir / "request_records",
        "checkpoints": run_dir / "checkpoints",
    }


def verify_frozen() -> tuple[dict, str, str, dict]:
    manifest = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    frozen.verify_approved_draft_hashes()
    developer, template = frozen.load_prompt()
    wrapper = frozen.contract.load_schema_wrapper()
    expected = {
        "prompt_path": relative(frozen.PROMPT_PATH),
        "prompt_sha256": legacy.sha256_file(frozen.PROMPT_PATH),
        "schema_path": relative(frozen.SCHEMA_PATH),
        "schema_sha256": legacy.sha256_file(frozen.SCHEMA_PATH),
        "continuous_contract_path": relative(Path(frozen.contract.__file__)),
        "continuous_contract_sha256": legacy.sha256_file(Path(frozen.contract.__file__)),
        "developer_prompt_sha256": legacy.sha256_bytes(developer.encode("utf-8")),
        "user_template_sha256": legacy.sha256_bytes(template.encode("utf-8")),
        "strict_schema_sha256": legacy.sha256_bytes(legacy.canonical_json(wrapper).encode("utf-8")),
        "evaluator_version": frozen.PROMPT_VERSION,
        "schema_version": frozen.SCHEMA_VERSION,
        "model": frozen.MODEL,
        "reasoning_effort": frozen.REASONING_EFFORT,
        "temperature": "omitted",
        "top_p": "omitted",
        "seed": "unsupported/omitted",
        "store": False,
        "independent_stateless_calls": True,
        "renderer_identity": frozen.RENDERER,
        "parser_validator_identity": "extract_output_text + json.loads + v1.6 continuous validate_result",
        "maximum_technical_retries_per_candidate": 1,
        "automatic_sdk_retries": 0,
        "candidate_input_components": frozen.INPUT_COMPONENTS,
    }
    if manifest.get("status") != "FROZEN FOR DEVELOPMENTAL HOLDOUT AND FORMAL EVALUATION" or manifest.get("frozen") is not True:
        raise RuntimeError("v1.6 evaluator is not frozen")
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise RuntimeError(f"Frozen evaluator mismatch: {key}")
    for key, path in (
        ("calibration_runner_sha256", ROOT / manifest["calibration_runner_path"]),
        ("renderer_implementation_sha256", ROOT / manifest["renderer_implementation_path"]),
        ("analysis_implementation_sha256", ROOT / manifest["analysis_implementation_path"]),
    ):
        if manifest[key] != legacy.sha256_file(path):
            raise RuntimeError(f"Frozen implementation mismatch: {key}")
    for path, digest in manifest["parser_validator_paths_sha256"].items():
        if legacy.sha256_file(ROOT / path) != digest:
            raise RuntimeError(f"Frozen parser/validator mismatch: {path}")
    if wrapper["schema"]["properties"]["overall_score"] != {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": wrapper["schema"]["properties"]["overall_score"]["description"]}:
        raise RuntimeError("Continuous score schema differs")
    return manifest, developer, template, wrapper


def verify_holdout_artifacts(freeze: dict) -> list[dict]:
    historical = json.loads(HISTORICAL_HOLDOUT_PATH.read_text(encoding="utf-8"))["candidate_artifacts"]
    earlier = json.loads(EARLIER_HOLDOUT_PATH.read_text(encoding="utf-8"))["candidates"]
    if historical != earlier or [(a["case_id"], a["candidate_id"]) for a in historical] != list(PAIRS):
        raise RuntimeError("Historical holdout roster differs")
    if len(historical) != 15 or set(CASES) & set(freeze["calibration_evidence"]["case_ids"]):
        raise RuntimeError("Holdout size or calibration overlap differs")
    for artifact in historical:
        case_id, candidate_id = artifact["case_id"], artifact["candidate_id"]
        source = legacy.candidate_paths(case_id, candidate_id)
        for path in source.values():
            if not path.is_file():
                raise FileNotFoundError(path)
        process_hash = legacy.sha256_file(source["process"])
        graph_hash = legacy.sha256_file(source["graph"])
        rendering = legacy.render_activity_graph(json.loads(source["graph"].read_text(encoding="utf-8")))
        if (process_hash != artifact["process_text_sha256"]
                or graph_hash != artifact["activity_graph_sha256"]
                or legacy.sha256_bytes(rendering.encode("utf-8")) != artifact["rendering_sha256"]
                or legacy.sha256_file(source["candidate_process"]) != process_hash
                or legacy.sha256_file(source["review_graph"]) != graph_hash):
            raise RuntimeError(f"Frozen holdout input hash differs: {case_id}/{candidate_id}")
        candidate_manifest = json.loads(source["manifest"].read_text(encoding="utf-8"))
        if (candidate_manifest["case_id"] != case_id or candidate_manifest["candidate_id"] != candidate_id
                or candidate_manifest["artifact_hashes"]["process_text.txt"] != process_hash
                or candidate_manifest["artifact_hashes"]["activity_graph.json"] != graph_hash):
            raise RuntimeError(f"Candidate manifest differs: {case_id}/{candidate_id}")
        review_hash = legacy.sha256_file(source["review_process"])
        if review_hash != artifact["review_process_text_sha256"]:
            raise RuntimeError(f"Review process hash differs: {case_id}/{candidate_id}")
        if review_hash != process_hash and legacy.decode_text_artifact(source["review_process"]) != source["process"].read_text(encoding="utf-8"):
            raise RuntimeError(f"Review process text differs: {case_id}/{candidate_id}")
    return historical


def verify_run(run_dir: Path, statuses: set[str]) -> tuple[dict, list[dict], str, str, dict]:
    p = paths(run_dir)
    manifest = json.loads(p["manifest"].read_text(encoding="utf-8"))
    if manifest["status"] not in statuses:
        raise RuntimeError(f"Holdout status disallows operation: {manifest['status']}")
    freeze, developer, template, wrapper = verify_frozen()
    artifacts = verify_holdout_artifacts(freeze)
    if (manifest["frozen_evaluator_manifest_sha256"] != legacy.sha256_file(FREEZE_PATH)
            or manifest["holdout_runner_sha256"] != legacy.sha256_file(Path(__file__))
            or manifest["candidates"] != artifacts):
        raise RuntimeError("Holdout evaluator or roster changed after preflight")
    return manifest, artifacts, developer, template, wrapper


def preflight(run_dir: Path) -> None:
    if run_dir.exists():
        raise FileExistsError(run_dir)
    freeze, _, _, _ = verify_frozen()
    artifacts = verify_holdout_artifacts(freeze)
    label_metadata = HUMAN_LABELS_PATH.stat()  # Metadata only; labels are not read.
    if label_metadata.st_mtime >= datetime.now(timezone.utc).timestamp():
        raise RuntimeError("Human holdout labels do not predate this run")
    run_dir.mkdir(parents=False, exist_ok=False)
    p = paths(run_dir)
    manifest = {
        "status": "preflight_passed",
        "created_at_utc": now(),
        "run_kind": "developmental_continuous_holdout",
        "validation_role": "developmental_holdout_previously_examined_in_earlier_versions",
        "frozen_evaluator_manifest_path": relative(FREEZE_PATH),
        "frozen_evaluator_manifest_sha256": legacy.sha256_file(FREEZE_PATH),
        "holdout_runner_path": relative(Path(__file__)),
        "holdout_runner_sha256": legacy.sha256_file(Path(__file__)),
        "historical_holdout_manifest_sha256": legacy.sha256_file(HISTORICAL_HOLDOUT_PATH),
        "earlier_holdout_manifest_sha256": legacy.sha256_file(EARLIER_HOLDOUT_PATH),
        "candidate_count": 15, "case_count": 5, "case_ids": list(CASES),
        "calibration_case_ids": freeze["calibration_evidence"]["case_ids"],
        "holdout_calibration_overlap": [],
        "candidates": artifacts,
        "prompt_version": freeze["evaluator_version"],
        "prompt_sha256": freeze["prompt_sha256"],
        "schema_version": freeze["schema_version"],
        "schema_sha256": freeze["schema_sha256"],
        "continuous_contract_sha256": freeze["continuous_contract_sha256"],
        "developer_prompt_sha256": freeze["developer_prompt_sha256"],
        "user_template_sha256": freeze["user_template_sha256"],
        "model": freeze["model"], "reasoning_effort": freeze["reasoning_effort"],
        "temperature": freeze["temperature"], "top_p": freeze["top_p"],
        "seed": freeze["seed"], "store": freeze["store"],
        "independent_stateless_calls": freeze["independent_stateless_calls"],
        "renderer": freeze["renderer_identity"],
        "parser_validator": freeze["parser_validator_identity"],
        "maximum_technical_retries_per_candidate": 1, "automatic_sdk_retries": 0,
        "human_labels_preexisting_path": relative(HUMAN_LABELS_PATH),
        "human_labels_preexisting_mtime_utc": datetime.fromtimestamp(label_metadata.st_mtime, timezone.utc).isoformat(),
        "human_labels_accessed": False,
        "completed_candidate_count": 0,
    }
    save_json(p["manifest"], manifest, new=True)
    save_json(p["slots"], [
        {"case_id": c, "candidate_id": k, "technical_status": "pending", "retry_count": 0}
        for c, k in PAIRS
    ], new=True)
    print(f"Preflight passed: {len(artifacts)} candidates across {len(CASES)} cases; labels not loaded; {run_dir}")


def run(run_dir: Path) -> None:
    manifest, artifacts, developer, template, wrapper = verify_run(run_dir, {"preflight_passed", "api_evaluations_in_progress"})
    api_key = load_api_key()
    p = paths(run_dir)
    if p["results"].exists() or p["usage"].exists():
        raise FileExistsError("Final AI outputs already exist")
    for key in ("raw", "requests", "checkpoints"):
        p[key].mkdir(exist_ok=True)
    slots = json.loads(p["slots"].read_text(encoding="utf-8"))
    if [(s["case_id"], s["candidate_id"]) for s in slots] != list(PAIRS):
        raise RuntimeError("Holdout slot roster differs")
    manifest["status"] = "api_evaluations_in_progress"
    manifest.setdefault("started_at_utc", now())
    save_json(p["manifest"], manifest)
    results, usage_rows, exact_scores = [], [], []
    for index, artifact in enumerate(artifacts):
        case_id, candidate_id = artifact["case_id"], artifact["candidate_id"]
        source = legacy.candidate_paths(case_id, candidate_id)
        process_text = source["process"].read_text(encoding="utf-8")
        graph_text = source["graph"].read_text(encoding="utf-8")
        rendering = legacy.render_activity_graph(json.loads(graph_text))
        user = legacy.instantiate_user_prompt(template, case_id, candidate_id, process_text, graph_text, rendering)
        record = frozen.input_record(case_id, candidate_id, process_text, graph_text, rendering, user, developer)
        request_path = p["requests"] / f"{case_id}__{candidate_id}.json"
        if request_path.exists():
            if json.loads(request_path.read_text(encoding="utf-8")) != record:
                raise RuntimeError(f"Request record differs: {case_id}/{candidate_id}")
        else:
            save_json(request_path, record, new=True)
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
                    save_json(raw_path, response, new=True)
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
                    error = {"case_id": case_id, "candidate_id": candidate_id, "attempt": attempt,
                             "error_type": type(exc).__name__, "error": str(exc), "timestamp_utc": now()}
                    if isinstance(exc, urllib.error.HTTPError):
                        try:
                            error["http_body"] = exc.read().decode("utf-8")
                        except Exception:
                            pass
                    save_json(p["raw"] / f"{case_id}__{candidate_id}__attempt_{attempt}__error.json", error, new=True)
                    if attempt == 1:
                        time.sleep(1)
            if result is None:
                slots[index].update(technical_status="technical_exception", retry_count=1,
                                    request_record_sha256=request_hash, error=str(last_error))
                save_json(p["slots"], slots)
                manifest.update(status="technical_exception", last_failed_identity=[case_id, candidate_id],
                                last_updated_at_utc=now(), completed_candidate_count=len(results))
                save_json(p["manifest"], manifest)
                raise RuntimeError(f"Holdout stopped after two attempts at {case_id}/{candidate_id}: {last_error}")
            used = frozen.usage_record(response, case_id, candidate_id, attempt - 1)
            save_json(checkpoint_path, {"case_id": case_id, "candidate_id": candidate_id,
                                        "completed_at_utc": now(), "request_record_sha256": request_hash,
                                        "result": result, "overall_score_decimal": str(exact), "usage": used}, new=True)
        results.append(result)
        usage_rows.append(used)
        exact_scores.append(exact)
        slots[index].update(technical_status="completed", retry_count=used["retry_count"],
                            request_record_sha256=request_hash, raw_response_path=relative(raw_path),
                            raw_response_sha256=legacy.sha256_file(raw_path))
        save_json(p["slots"], slots)
        manifest.update(completed_candidate_count=len(results), last_completed_identity=[case_id, candidate_id],
                        last_updated_at_utc=now())
        save_json(p["manifest"], manifest)
        print(f"[{index + 1:02d}/15] completed {case_id}/{candidate_id} retries={used['retry_count']}", flush=True)
    with p["results"].open("x", encoding="utf-8") as handle:
        for result, exact in zip(results, exact_scores):
            handle.write(frozen.serialize_result(result, exact) + "\n")
    with p["usage"].open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(usage_rows[0]))
        writer.writeheader()
        writer.writerows(usage_rows)
    manifest.update(status="all_ai_results_saved", completed_candidate_count=15, completed_at_utc=now(),
                    total_retry_count=sum(row["retry_count"] for row in usage_rows),
                    results_sha256=legacy.sha256_file(p["results"]), usage_sha256=legacy.sha256_file(p["usage"]),
                    human_labels_accessed=False, human_labels_accessed_during_ai_generation=False)
    save_json(p["manifest"], manifest)
    print("All 15 independent AI results saved and validated; human labels not accessed", flush=True)


def compare(run_dir: Path) -> None:
    manifest, artifacts, developer, template, wrapper = verify_run(run_dir, {"all_ai_results_saved"})
    p = paths(run_dir)
    if any(p[key].exists() for key in ("comparison", "review", "metrics", "report", "scatter")):
        raise FileExistsError("Comparison artifact already exists")
    if (manifest["results_sha256"] != legacy.sha256_file(p["results"])
            or manifest["usage_sha256"] != legacy.sha256_file(p["usage"])):
        raise RuntimeError("Saved AI outputs changed")
    lines = p["results"].read_text(encoding="utf-8").splitlines()
    slots = json.loads(p["slots"].read_text(encoding="utf-8"))
    if len(lines) != 15 or len(slots) != 15 or any(s["technical_status"] != "completed" for s in slots):
        raise RuntimeError("All 15 AI results must be complete before reading labels")
    scores: dict[tuple[str, str], Decimal] = {}
    for line, artifact, slot in zip(lines, artifacts, slots):
        result = json.loads(line)
        pair = (artifact["case_id"], artifact["candidate_id"])
        exact = frozen.parse_score_decimal(line)
        frozen.validate_exact_result(result, exact, *pair, wrapper["schema"])
        if (result["case_id"], result["candidate_id"]) != pair or (slot["case_id"], slot["candidate_id"]) != pair:
            raise RuntimeError(f"Saved AI identity differs: {pair}")
        source = legacy.candidate_paths(*pair)
        process_text = source["process"].read_text(encoding="utf-8")
        graph_text = source["graph"].read_text(encoding="utf-8")
        rendering = legacy.render_activity_graph(json.loads(graph_text))
        user = legacy.instantiate_user_prompt(template, *pair, process_text, graph_text, rendering)
        record = frozen.input_record(*pair, process_text, graph_text, rendering, user, developer)
        request_path = p["requests"] / f"{pair[0]}__{pair[1]}.json"
        if json.loads(request_path.read_text(encoding="utf-8")) != record or slot["request_record_sha256"] != legacy.sha256_file(request_path):
            raise RuntimeError(f"Request boundary changed: {pair}")
        raw_path = p["raw"] / f"{pair[0]}__{pair[1]}__attempt_{slot['retry_count'] + 1}.json"
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        raw_text = frozen.contract.extract_output_text(raw)
        checkpoint = json.loads((p["checkpoints"] / f"{pair[0]}__{pair[1]}.json").read_text(encoding="utf-8"))
        if (raw.get("status") != "completed" or raw.get("model") != frozen.MODEL
                or json.loads(raw_text) != result or frozen.parse_score_decimal(raw_text) != exact
                or checkpoint["result"] != result or Decimal(checkpoint["overall_score_decimal"]) != exact
                or checkpoint["request_record_sha256"] != slot["request_record_sha256"]):
            raise RuntimeError(f"Raw response or checkpoint differs: {pair}")
        scores[pair] = exact
    with p["usage"].open(encoding="utf-8", newline="") as handle:
        usage = list(csv.DictReader(handle))
    if len(usage) != 15 or [(r["case_id"], r["candidate_id"]) for r in usage] != list(PAIRS):
        raise RuntimeError("Usage roster differs")
    # First human-label content read: all 15 AI outputs are saved and verified above.
    labels = analysis.load_human_labels(HUMAN_LABELS_PATH, PAIRS)
    rows, metrics = analysis.calculate(PAIRS, scores, labels)
    analysis.write_csv(p["comparison"], rows)
    analysis.write_csv(p["review"], analysis.review_order(rows))
    save_json(p["metrics"], {
        **analysis.metrics_json_ready(metrics),
        "minimum_ai_score": str(min(scores.values())),
        "maximum_ai_score": str(max(scores.values())),
        "technical_failure_count": 0,
        "total_retry_count": manifest["total_retry_count"],
        "ambiguity_flag_count": sum(bool(json.loads(line)["ambiguity_flag"]) for line in lines),
        "requires_human_review_count": sum(bool(json.loads(line)["requires_human_review"]) for line in lines),
    }, new=True)
    analysis.write_scatter_svg(p["scatter"], rows)
    p["scatter"].write_text(p["scatter"].read_text(encoding="utf-8").replace("Continuous calibration scatter", "Continuous developmental holdout scatter"), encoding="utf-8")
    rho = "undefined/NA" if metrics["spearman_tie_aware"] is None else f'{metrics["spearman_tie_aware"]:.4f}'
    report = [
        "# AI Evaluator v1.6 continuous developmental holdout", "",
        "The frozen v1.6 evaluator was applied to 15 candidates in five cases. These cases had been examined in earlier evaluator versions; this is developmental holdout evidence.", "",
        f'- MAE: **{metrics["mean_absolute_error"]:.4f}**.',
        f'- Median absolute error: **{metrics["median_absolute_error"]:.4f}**.',
        f'- Maximum absolute error: **{metrics["maximum_absolute_error"]:.4f}**.',
        f'- Tie-aware Spearman: **{rho}**.',
        f'- AI score range: **{min(scores.values())}–{max(scores.values())}**.',
        f'- Technical failures: **0**; retries: **{manifest["total_retry_count"]}**.',
        "- Human labels were loaded only after all 15 AI outputs were saved and validated.",
        "- AI scores remain continuous and unquantized. No numeric acceptance threshold was applied.", "",
        "## Candidate-level comparison", "",
        "| Case | Candidate | Human | AI | Signed difference | Absolute error |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in analysis.review_order(rows):
        report.append(f'| {row["case_id"]} | {row["candidate_id"]} | {row["human_label"]} | {row["ai_score"]} | {row["signed_difference"]} | {row["absolute_error"]} |')
    report.extend(["", "## Qualitative review", "", "The leading disagreements are reviewed separately after this comparison is saved. No evaluator tuning or candidate rerun follows from the review.", ""])
    with p["report"].open("x", encoding="utf-8") as handle:
        handle.write("\n".join(report))
    manifest.update(status="comparison_complete", human_labels_accessed=True,
                    human_labels_accessed_during_ai_generation=False,
                    human_labels_accessed_after_all_results_saved=True,
                    comparison_completed_at_utc=now(),
                    comparison_sha256=legacy.sha256_file(p["comparison"]),
                    review_sha256=legacy.sha256_file(p["review"]),
                    metrics_sha256=legacy.sha256_file(p["metrics"]),
                    scatter_sha256=legacy.sha256_file(p["scatter"]),
                    report_sha256=legacy.sha256_file(p["report"]))
    save_json(p["manifest"], manifest)
    print("Continuous developmental holdout comparison complete", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "compare"))
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    run_dir = resolve_run_dir(args.run_dir)
    if args.command == "preflight":
        preflight(run_dir)
    elif args.command == "run":
        run(run_dir)
    else:
        compare(run_dir)


if __name__ == "__main__":
    main()
