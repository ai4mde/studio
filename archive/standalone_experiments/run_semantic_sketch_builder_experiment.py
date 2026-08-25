#!/usr/bin/env python3
from __future__ import annotations
# ruff: noqa: E402

import argparse
import csv
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List


API_ROOT = Path(__file__).resolve().parents[2] / "api"
MODEL_ROOT = API_ROOT / "model"
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from llm.activity_sketch_model import ActivitySketch  # noqa: E402
from llm.handler import _activity_sketch_response_format, call_openai  # noqa: E402
from llm.keyword_hints import extract_keyword_hints  # noqa: E402
from llm.prompt_builder import build_activity_sketch_prompt_with_hints  # noqa: E402
from llm.semantic_sketch_experiment import (
    generate_semantic_sketch_plan,
)  # noqa: E402
from llm.topology_experiment import generate_topology_artifact  # noqa: E402
from llm.topology_to_sketch_compiler import (
    compare_topology_artifact_to_activity_sketch,
    compile_topology_and_semantics_to_activity_sketch,
)  # noqa: E402


EXPERIMENT_FLAG_NAME = "use_semantic_sketch_builder"
DEFAULT_INTER_CASE_DELAY_SECONDS = 2.0


def _slugify(value: str) -> str:
    chars = [ch.lower() if ch.isalnum() else "_" for ch in value.strip()]
    slug = "".join(chars)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "workflow"


def _load_workflows(args: argparse.Namespace) -> List[Dict[str, str]]:
    if args.text:
        return [{"name": args.name or "ad_hoc_case", "process_text": args.text.strip()}]

    if args.text_file:
        return [
            {
                "name": args.name or Path(args.text_file).stem,
                "process_text": Path(args.text_file).read_text(encoding="utf-8").strip(),
            }
        ]

    if not args.dataset:
        raise ValueError("Provide one of --text, --text-file, or --dataset.")

    dataset_path = Path(args.dataset).expanduser().resolve()

    if dataset_path.suffix.lower() == ".csv":
        workflows: List[Dict[str, str]] = []
        with dataset_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader, start=1):
                process_text = str(row.get("process_text") or row.get("text") or "").strip()
                if not process_text:
                    source_path = str(row.get("source_process_text_file") or "").strip()
                    if not source_path:
                        raise ValueError(f"Workflow entry at row {index} is missing process text.")
                    process_text = Path(source_path).read_bytes().decode("latin-1").strip()
                case_id = str(row.get("case_id") or row.get("id") or "").strip()
                name = str(row.get("case_name") or case_id or f"workflow_{index}").strip()
                workflow: Dict[str, str] = {
                    "name": name,
                    "process_text": process_text,
                }
                if case_id:
                    workflow["case_id"] = case_id
                workflows.append(workflow)
        return workflows

    payload = json.loads(dataset_path.read_text(encoding="utf-8"))

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
            workflows.append({"name": f"workflow_{index}", "process_text": item.strip()})
            continue
        if not isinstance(item, dict):
            raise ValueError(f"Unsupported workflow entry at index {index}: {type(item)!r}")
        process_text = str(item.get("process_text") or item.get("text") or "").strip()
        if not process_text:
            raise ValueError(f"Workflow entry at index {index} is missing process text.")
        name = str(item.get("name") or item.get("id") or f"workflow_{index}").strip()
        workflow = {"name": name, "process_text": process_text}
        case_id = str(item.get("case_id") or item.get("id") or "").strip()
        if case_id:
            workflow["case_id"] = case_id
        workflows.append(workflow)
    return workflows


def _workflow_label(workflow: Dict[str, str]) -> str:
    return str(workflow.get("case_id") or workflow["name"]).strip()


def _workflow_output_path(output_dir: Path, workflow: Dict[str, str]) -> Path:
    return output_dir / f"{_slugify(_workflow_label(workflow))}.json"


def _read_checkpoint(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _is_successful_checkpoint_payload(
    payload: Dict[str, Any],
    *,
    semantic_enabled: bool,
) -> bool:
    if payload.get("status") == "completed":
        return True
    if payload.get("topology_artifact") is None:
        return False
    if semantic_enabled:
        return (
            payload.get("semantic_sketch_error") is None
            and payload.get("semantic_sketch_plan") is not None
            and payload.get("semantic_deterministic_activity_sketch") is not None
        )
    return True


def _should_skip_completed_case(
    workflow: Dict[str, str],
    *,
    output_dir: Path,
    semantic_enabled: bool,
    force: bool,
) -> bool:
    if force:
        return False
    payload = _read_checkpoint(_workflow_output_path(output_dir, workflow))
    if payload is None:
        return False
    return _is_successful_checkpoint_payload(payload, semantic_enabled=semantic_enabled)


def _summary_row_for_case(
    workflow: Dict[str, str],
    *,
    artifact_path: Path,
    status: str,
    payload: Dict[str, Any] | None = None,
    skipped: bool = False,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "workflow": workflow["name"],
        "case_id": workflow.get("case_id"),
        "artifact_path": str(artifact_path),
        "status": status,
    }
    if skipped:
        row["skipped"] = True
        return row
    if payload is None:
        return row
    topology_artifact = payload.get("topology_artifact") or {}
    row["topology_structure_count"] = len(topology_artifact.get("structures") or [])
    if payload.get("semantic_deterministic_preservation_report") is not None:
        row["semantic_parent_preservation_ratio"] = payload["semantic_deterministic_preservation_report"]["summary"][
            "parent_preservation_ratio"
        ]
        row["semantic_parent_branch_preservation_ratio"] = payload["semantic_deterministic_preservation_report"]["summary"][
            "parent_branch_preservation_ratio"
        ]
    if payload.get("semantic_sketch_error") is not None:
        row["semantic_sketch_error"] = payload["semantic_sketch_error"]
    if payload.get("current_topology_guided_preservation_report") is not None:
        row["current_parent_preservation_ratio"] = payload["current_topology_guided_preservation_report"]["summary"][
            "parent_preservation_ratio"
        ]
        row["current_parent_branch_preservation_ratio"] = payload["current_topology_guided_preservation_report"]["summary"][
            "parent_branch_preservation_ratio"
        ]
    if payload.get("current_topology_guided_error") is not None:
        row["current_topology_guided_error"] = payload["current_topology_guided_error"]
    if payload.get("error_type") is not None:
        row["error_type"] = payload["error_type"]
    if payload.get("error_message") is not None:
        row["error_message"] = payload["error_message"]
    return row


def _write_summary(output_dir: Path, summary_rows: List[Dict[str, Any]]) -> None:
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary_rows, indent=2, ensure_ascii=False), encoding="utf-8")


def _is_rate_limit_failure(exc: BaseException) -> bool:
    text = f"{type(exc).__name__}: {exc}"
    lowered = text.lower()
    return "rate_limit_exceeded" in lowered or (
        "429" in text
        and any(
            marker in lowered
            for marker in ("too many requests", "error code", "status code", "status_code")
        )
    )


def _build_failure_payload(
    workflow: Dict[str, str],
    *,
    exc: BaseException,
    semantic_enabled: bool,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "workflow": workflow["name"],
        "case_id": workflow.get("case_id"),
        "process_text": workflow["process_text"],
        "feature_flag": EXPERIMENT_FLAG_NAME,
        "feature_enabled": semantic_enabled,
        "status": "failed_rate_limit" if _is_rate_limit_failure(exc) else "failed",
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "traceback": traceback.format_exc(),
    }
    debug_artifacts = getattr(exc, "debug_artifacts", None)
    if isinstance(debug_artifacts, dict):
        payload["debug_artifacts"] = debug_artifacts
    return payload


def _sleep_between_cases(
    *,
    workflow_index: int,
    workflows: List[Dict[str, str]],
    output_dir: Path,
    semantic_enabled: bool,
    force: bool,
    inter_case_delay: float,
    sleep_fn: Any,
) -> None:
    if inter_case_delay <= 0:
        return
    for later_workflow in workflows[workflow_index + 1 :]:
        if not _should_skip_completed_case(
            later_workflow,
            output_dir=output_dir,
            semantic_enabled=semantic_enabled,
            force=force,
        ):
            sleep_fn(inter_case_delay)
            return


def run_semantic_experiment_case(
    workflow: Dict[str, str],
    *,
    model: str,
    use_semantic_sketch_builder: bool,
    include_current_topology_guided: bool,
) -> Dict[str, Any]:
    topology_result = generate_topology_artifact(
        workflow["process_text"],
        model=model,
    )
    topology_artifact = topology_result["artifact"]
    payload: Dict[str, Any] = {
        "workflow": workflow["name"],
        "case_id": workflow.get("case_id"),
        "process_text": workflow["process_text"],
        "feature_flag": EXPERIMENT_FLAG_NAME,
        "feature_enabled": use_semantic_sketch_builder,
        "status": "completed",
        "topology_artifact": topology_artifact,
        "topology_prompt": topology_result["prompt"],
        "topology_raw_output": topology_result["raw_output"],
        "topology_keyword_hints": topology_result["keyword_hints"],
        "topology_response_mode": topology_result["response_mode"],
        "topology_fallback_reason": topology_result["fallback_reason"],
    }

    if use_semantic_sketch_builder:
        semantic_result = generate_semantic_sketch_plan(
            workflow["process_text"],
            topology_artifact=topology_artifact,
            model=model,
        )
        semantic_plan = semantic_result["artifact"]
        deterministic_sketch = compile_topology_and_semantics_to_activity_sketch(
            topology_artifact,
            semantic_plan,
        )
        payload["semantic_sketch_plan"] = semantic_plan
        payload["semantic_prompt"] = semantic_result["prompt"]
        payload["semantic_raw_output"] = semantic_result["raw_output"]
        payload["semantic_keyword_hints"] = semantic_result["keyword_hints"]
        payload["semantic_response_mode"] = semantic_result["response_mode"]
        payload["semantic_fallback_reason"] = semantic_result["fallback_reason"]
        payload["semantic_deterministic_activity_sketch"] = deterministic_sketch
        payload["semantic_deterministic_preservation_report"] = compare_topology_artifact_to_activity_sketch(
            topology_artifact,
            deterministic_sketch,
        )

    if include_current_topology_guided:
        llm_result = _generate_topology_guided_sketch(
            workflow["process_text"],
            topology_artifact=topology_artifact,
            model=model,
        )
        llm_sketch = llm_result["artifact"]
        payload["current_topology_guided_sketch"] = llm_sketch
        payload["current_topology_guided_prompt"] = llm_result["prompt"]
        payload["current_topology_guided_raw_output"] = llm_result["raw_output"]
        payload["current_topology_guided_keyword_hints"] = llm_result["keyword_hints"]
        payload["current_topology_guided_preservation_report"] = compare_topology_artifact_to_activity_sketch(
            topology_artifact,
            llm_sketch,
        )
    return payload


def run_batch(
    workflows: List[Dict[str, str]],
    *,
    output_dir: Path,
    model: str,
    use_semantic_sketch_builder: bool,
    include_current_topology_guided: bool,
    force: bool = False,
    inter_case_delay: float = DEFAULT_INTER_CASE_DELAY_SECONDS,
    sleep_fn: Any = time.sleep,
) -> int:
    summary_rows: List[Dict[str, Any]] = []

    for workflow_index, workflow in enumerate(workflows):
        artifact_path = _workflow_output_path(output_dir, workflow)
        if _should_skip_completed_case(
            workflow,
            output_dir=output_dir,
            semantic_enabled=use_semantic_sketch_builder,
            force=force,
        ):
            print(f"[SKIP] {_workflow_label(workflow)} already completed")
            summary_rows.append(
                _summary_row_for_case(
                    workflow,
                    artifact_path=artifact_path,
                    status="skipped",
                    skipped=True,
                )
            )
            _write_summary(output_dir, summary_rows)
            continue

        try:
            payload = run_semantic_experiment_case(
                workflow,
                model=model,
                use_semantic_sketch_builder=use_semantic_sketch_builder,
                include_current_topology_guided=include_current_topology_guided,
            )
        except Exception as exc:
            failure_payload = _build_failure_payload(
                workflow,
                exc=exc,
                semantic_enabled=use_semantic_sketch_builder,
            )
            artifact_path.write_text(json.dumps(failure_payload, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[STOP] {_workflow_label(workflow)} failed: {type(exc).__name__}: {exc}")
            if _is_rate_limit_failure(exc):
                print(f"[STOP] confirmed rate limit on {_workflow_label(workflow)}; resume later to continue unfinished cases")
            summary_rows.append(
                _summary_row_for_case(
                    workflow,
                    artifact_path=artifact_path,
                    status=failure_payload["status"],
                    payload=failure_payload,
                )
            )
            _write_summary(output_dir, summary_rows)
            return 1

        artifact_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] {_workflow_label(workflow)} completed")
        summary_rows.append(
            _summary_row_for_case(
                workflow,
                artifact_path=artifact_path,
                status="completed",
                payload=payload,
            )
        )
        _write_summary(output_dir, summary_rows)
        _sleep_between_cases(
            workflow_index=workflow_index,
            workflows=workflows,
            output_dir=output_dir,
            semantic_enabled=use_semantic_sketch_builder,
            force=force,
            inter_case_delay=inter_case_delay,
            sleep_fn=sleep_fn,
        )
    print(f"Saved experiment artifacts to {output_dir}")
    return 0


def _generate_topology_guided_sketch(
    process_text: str,
    *,
    topology_artifact: Dict[str, Any],
    model: str,
) -> Dict[str, Any]:
    keyword_hints = extract_keyword_hints(process_text)
    prompt = build_activity_sketch_prompt_with_hints(
        process_text,
        keyword_hints=keyword_hints,
        topology_artifact=topology_artifact,
    )
    raw_output = call_openai(
        model=model,
        prompt=prompt,
        response_format=_activity_sketch_response_format(),
        require_structured_output=True,
    )
    parsed_json = json.loads(raw_output)
    validated = ActivitySketch.model_validate(parsed_json)
    return {
        "keyword_hints": keyword_hints,
        "prompt": prompt,
        "raw_output": raw_output,
        "artifact": validated.model_dump(mode="json"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the semantic-only sketch builder experiment."
    )
    parser.add_argument("--text", help="Inline process text.")
    parser.add_argument("--text-file", help="Path to a file containing process text.")
    parser.add_argument("--dataset", help="Path to a JSON dataset with workflows.")
    parser.add_argument("--name", help="Optional case name for --text or --text-file.")
    parser.add_argument("--output", required=True, help="Directory for saved experiment artifacts.")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use.")
    parser.add_argument(
        "--case-ids",
        nargs="+",
        help="Optional case ids to run from the dataset/catalog. Completed successful cases are skipped by default.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rerun cases even if a completed successful checkpoint already exists.",
    )
    parser.add_argument(
        "--inter-case-delay",
        type=float,
        default=DEFAULT_INTER_CASE_DELAY_SECONDS,
        help=f"Delay in seconds between completed generated cases. Default: {DEFAULT_INTER_CASE_DELAY_SECONDS}.",
    )
    parser.add_argument(
        f"--{EXPERIMENT_FLAG_NAME}",
        f"--{EXPERIMENT_FLAG_NAME.replace('_', '-')}",
        dest=EXPERIMENT_FLAG_NAME,
        action="store_true",
        help="Enable the semantic-only planner plus deterministic sketch builder path.",
    )
    parser.add_argument(
        "--include-current-topology-guided",
        action="store_true",
        help="Also generate the current topology-guided LLM sketch for comparison.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    workflows = _load_workflows(args)
    if args.case_ids:
        selected_case_ids = {case_id.strip() for case_id in args.case_ids if case_id.strip()}
        workflows = [
            workflow
            for workflow in workflows
            if str(workflow.get("case_id") or "").strip() in selected_case_ids
        ]

    return run_batch(
        workflows,
        output_dir=output_dir,
        model=args.model,
        use_semantic_sketch_builder=bool(getattr(args, EXPERIMENT_FLAG_NAME)),
        include_current_topology_guided=bool(args.include_current_topology_guided),
        force=bool(args.force),
        inter_case_delay=float(args.inter_case_delay),
    )


if __name__ == "__main__":
    raise SystemExit(main())
