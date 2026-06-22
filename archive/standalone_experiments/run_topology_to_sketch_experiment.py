#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


API_ROOT = Path(__file__).resolve().parents[2] / "api"
MODEL_ROOT = API_ROOT / "model"
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from llm.activity_sketch_model import ActivitySketch
from llm.handler import _activity_sketch_response_format, call_openai
from llm.keyword_hints import extract_keyword_hints
from llm.prompt_builder import build_activity_sketch_prompt_with_hints
from llm.topology_experiment import generate_topology_artifact
from llm.topology_to_sketch_compiler import (
    compare_topology_artifact_to_activity_sketch,
    compile_topology_artifact_to_activity_sketch,
)


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
        workflows.append({"name": name, "process_text": process_text})
    return workflows


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
        description="Run a standalone Topology Artifact -> ActivitySketch comparison experiment."
    )
    parser.add_argument("--text", help="Inline process text.")
    parser.add_argument("--text-file", help="Path to a file containing process text.")
    parser.add_argument("--dataset", help="Path to a JSON dataset with workflows.")
    parser.add_argument("--name", help="Optional case name for --text or --text-file.")
    parser.add_argument("--output", required=True, help="Directory for saved experiment artifacts.")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use.")
    parser.add_argument(
        "--include-llm-sketch",
        action="store_true",
        help="Also generate the current topology-guided LLM sketch for side-by-side comparison.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    workflows = _load_workflows(args)
    summary_rows: List[Dict[str, Any]] = []

    for workflow in workflows:
        topology_result = generate_topology_artifact(
            workflow["process_text"],
            model=args.model,
        )
        topology_artifact = topology_result["artifact"]

        deterministic_sketch = compile_topology_artifact_to_activity_sketch(topology_artifact)
        deterministic_report = compare_topology_artifact_to_activity_sketch(
            topology_artifact,
            deterministic_sketch,
        )

        payload: Dict[str, Any] = {
            "workflow": workflow["name"],
            "process_text": workflow["process_text"],
            "topology_artifact": topology_artifact,
            "topology_prompt": topology_result["prompt"],
            "topology_raw_output": topology_result["raw_output"],
            "topology_keyword_hints": topology_result["keyword_hints"],
            "topology_response_mode": topology_result["response_mode"],
            "topology_fallback_reason": topology_result["fallback_reason"],
            "deterministic_activity_sketch": deterministic_sketch,
            "deterministic_preservation_report": deterministic_report,
        }

        if args.include_llm_sketch:
            llm_error: str | None = None
            llm_result: Dict[str, Any] | None = None
            try:
                llm_result = _generate_topology_guided_sketch(
                    workflow["process_text"],
                    topology_artifact=topology_artifact,
                    model=args.model,
                )
            except Exception as exc:
                llm_error = str(exc)

            if llm_result is not None:
                llm_sketch = llm_result["artifact"]
                payload["llm_activity_sketch"] = llm_sketch
                payload["llm_sketch_prompt"] = llm_result["prompt"]
                payload["llm_sketch_raw_output"] = llm_result["raw_output"]
                payload["llm_sketch_keyword_hints"] = llm_result["keyword_hints"]
                payload["llm_preservation_report"] = compare_topology_artifact_to_activity_sketch(
                    topology_artifact,
                    llm_sketch,
                )
            if llm_error is not None:
                payload["llm_sketch_error"] = llm_error

        case_slug = _slugify(workflow["name"])
        output_path = output_dir / f"{case_slug}.json"
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        summary_row: Dict[str, Any] = {
            "workflow": workflow["name"],
            "artifact_path": str(output_path),
            "topology_structure_count": len(topology_artifact.get("structures") or []),
            "deterministic_parent_preservation_ratio": payload["deterministic_preservation_report"]["summary"][
                "parent_preservation_ratio"
            ],
            "deterministic_parent_branch_preservation_ratio": payload["deterministic_preservation_report"]["summary"][
                "parent_branch_preservation_ratio"
            ],
        }
        if payload.get("llm_preservation_report") is not None:
            summary_row["llm_parent_preservation_ratio"] = payload["llm_preservation_report"]["summary"][
                "parent_preservation_ratio"
            ]
            summary_row["llm_parent_branch_preservation_ratio"] = payload["llm_preservation_report"]["summary"][
                "parent_branch_preservation_ratio"
            ]
        if payload.get("llm_sketch_error") is not None:
            summary_row["llm_sketch_error"] = payload["llm_sketch_error"]
        summary_rows.append(summary_row)

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary_rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved experiment artifacts to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
