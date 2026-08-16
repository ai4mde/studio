from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
from typing import Any

from .action_matching import PROVISIONAL_THRESHOLD, apply_one_to_one_matching
from .adapters import activity_graph_to_eval_graph, friedrich_reference_to_eval_graph
from .calibrate_action_similarity import MODEL_NAME, MODEL_REVISION
from .prototype import _extract_activity_graph


HELD_OUT_CASES = {
    "3-1": "clean simple sequence with repeated store/retrieve activities",
    "3-4": "loop with questionnaire and repeated reminders",
    "8-2": "decision loop with correction and resubmission",
    "10-7": "decision with three repeated assignment-information activities",
    "1-2": "parallel repair activities, decisions, and repetition",
}
PILOT_CASES = frozenset({"6-2", "5-2", "3-3", "6-3", "9-6", "4-1", "9-5"})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rounded(value: Any) -> Any:
    return round(value, 8) if isinstance(value, float) else value


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            {field: _rounded(row.get(field, "")) for field in fieldnames}
            for row in rows
        )


def main() -> None:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Run the frozen action matcher on held-out Friedrich cases"
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("/Users/queenie/Desktop/evaluation-data/friedrich_47_case_catalog.csv"),
    )
    parser.add_argument(
        "--output-dir", type=Path, default=base / "heldout_validation"
    )
    parser.add_argument("--threshold", type=float, default=PROVISIONAL_THRESHOLD)
    parser.add_argument(
        "--model-cache",
        type=Path,
        default=Path("/private/tmp/friedrich-hf-cache"),
    )
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()

    if args.threshold != PROVISIONAL_THRESHOLD:
        raise ValueError(
            f"Held-out validation must use frozen provisional threshold {PROVISIONAL_THRESHOLD}"
        )
    if set(HELD_OUT_CASES) & PILOT_CASES:
        raise ValueError("Held-out selection overlaps the calibration pilot")

    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("DO_NOT_TRACK", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer

    with args.catalog.open(encoding="utf-8", newline="") as handle:
        catalog = {row["case_id"]: row for row in csv.DictReader(handle)}

    cases: list[dict[str, Any]] = []
    all_texts: set[str] = set()
    for case_id, rationale in HELD_OUT_CASES.items():
        catalog_row = catalog[case_id]
        reference_path = Path(catalog_row["reference_model_path"])
        generated_path = Path(catalog_row["generated_artifact_output_path"]) / "run_1.json"
        reference_graph = friedrich_reference_to_eval_graph(reference_path)
        artifact = json.loads(generated_path.read_text(encoding="utf-8"))
        generated_graph = activity_graph_to_eval_graph(_extract_activity_graph(artifact))
        reference_actions = sorted(
            (node for node in reference_graph.nodes if node.type == "action"),
            key=lambda node: node.id,
        )
        generated_actions = sorted(
            (node for node in generated_graph.nodes if node.type == "action"),
            key=lambda node: node.id,
        )
        for node in (*reference_actions, *generated_actions):
            if node.label:
                all_texts.add(node.label)
        cases.append(
            {
                "case_id": case_id,
                "case_name": Path(catalog_row["source_process_text_file"]).stem,
                "rationale": rationale,
                "catalog": catalog_row,
                "reference_path": reference_path,
                "generated_path": generated_path,
                "reference_graph": reference_graph,
                "generated_graph": generated_graph,
                "reference_actions": reference_actions,
                "generated_actions": generated_actions,
            }
        )

    torch.manual_seed(0)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    texts = sorted(all_texts)
    model = SentenceTransformer(
        MODEL_NAME,
        revision=MODEL_REVISION,
        device="cpu",
        cache_folder=str(args.model_cache),
        local_files_only=args.local_files_only,
    )
    vectors = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    embeddings = dict(zip(texts, vectors))

    all_candidates: list[dict[str, Any]] = []
    action_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for case in cases:
        case_id = case["case_id"]
        for side, actions in (
            ("reference", case["reference_actions"]),
            ("generated", case["generated_actions"]),
        ):
            action_rows.extend(
                {
                    "case_id": case_id,
                    "case_name": case["case_name"],
                    "side": side,
                    "action_id": node.id,
                    "label": node.label,
                }
                for node in actions
            )

        matrix_rows = []
        for reference in case["reference_actions"]:
            for generated in case["generated_actions"]:
                if reference.label is None or generated.label is None:
                    continue
                matrix_rows.append(
                    {
                        "pair_id": f"{case_id}:{reference.id}:{generated.id}",
                        "case_id": case_id,
                        "case_name": case["case_name"],
                        "reference_id": reference.id,
                        "reference_label": reference.label,
                        "reference_normalized": reference.label,
                        "generated_id": generated.id,
                        "generated_label": generated.label,
                        "generated_normalized": generated.label,
                        "cosine_similarity": float(
                            np.dot(
                                embeddings[reference.label], embeddings[generated.label]
                            )
                        ),
                    }
                )
        evaluated = apply_one_to_one_matching(matrix_rows, args.threshold)
        all_candidates.extend(evaluated)
        matches = [row for row in evaluated if row["final_prediction"]]
        matched_reference = {row["reference_id"] for row in matches}
        matched_generated = {row["generated_id"] for row in matches}
        summaries.append(
            {
                "case_id": case_id,
                "case_name": case["case_name"],
                "selection_rationale": case["rationale"],
                "source_pattern": case["catalog"]["major_process_pattern"],
                "has_decision": case["catalog"]["has_decision"],
                "has_loop": case["catalog"]["has_loop"],
                "has_parallel": case["catalog"]["has_parallel"],
                "reference_path": str(case["reference_path"]),
                "reference_sha256": _sha256(case["reference_path"]),
                "generated_path": str(case["generated_path"]),
                "generated_sha256": _sha256(case["generated_path"]),
                "reference_action_count": len(case["reference_actions"]),
                "generated_action_count": len(case["generated_actions"]),
                "candidate_pair_count": len(evaluated),
                "selected_matches": [
                    {
                        "reference_id": row["reference_id"],
                        "reference_label": row["reference_label"],
                        "generated_id": row["generated_id"],
                        "generated_label": row["generated_label"],
                        "cosine_similarity": _rounded(row["cosine_similarity"]),
                        "compatibility_reason": row["compatibility_reason"],
                        "topology_used": False,
                        "topology_evidence": None,
                    }
                    for row in sorted(matches, key=lambda item: item["reference_id"])
                ],
                "unmatched_reference_actions": [
                    {"id": node.id, "label": node.label}
                    for node in case["reference_actions"]
                    if node.id not in matched_reference
                ],
                "unmatched_generated_actions": [
                    {"id": node.id, "label": node.label}
                    for node in case["generated_actions"]
                    if node.id not in matched_generated
                ],
                "compatibility_rejections_above_threshold": [
                    {
                        "reference_id": row["reference_id"],
                        "reference_label": row["reference_label"],
                        "generated_id": row["generated_id"],
                        "generated_label": row["generated_label"],
                        "cosine_similarity": _rounded(row["cosine_similarity"]),
                        "reason": row["compatibility_reason"],
                    }
                    for row in evaluated
                    if row["threshold_prediction"] and not row["operation_compatible"]
                ],
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    action_fields = ["case_id", "case_name", "side", "action_id", "label"]
    candidate_fields = [
        "pair_id",
        "case_id",
        "case_name",
        "reference_id",
        "reference_label",
        "generated_id",
        "generated_label",
        "cosine_similarity",
        "threshold_prediction",
        "reference_operation",
        "reference_operation_family",
        "generated_operation",
        "generated_operation_family",
        "operation_compatible",
        "compatibility_reason",
        "candidate_after_compatibility",
        "selected_by_assignment",
        "final_prediction",
        "decision_change_source",
    ]
    _write_csv(args.output_dir / "heldout_actions.csv", action_fields, action_rows)
    _write_csv(
        args.output_dir / "heldout_candidate_matrix.csv",
        candidate_fields,
        all_candidates,
    )
    output = {
        "method": {
            "normalization": "evaluation.friedrich.eval_graph.normalize_label",
            "model": MODEL_NAME,
            "model_revision": MODEL_REVISION,
            "dimensions": int(vectors.shape[1]),
            "threshold": args.threshold,
            "operation_compatibility": "evaluation.friedrich.action_matching",
            "assignment": "per-case maximum-weight bipartite assignment",
            "topology_policy": "tie-breaker only; not applied automatically in this run",
            "sentence_transformers_version": importlib.metadata.version(
                "sentence-transformers"
            ),
            "scipy_version": importlib.metadata.version("scipy"),
            "torch_version": torch.__version__,
            "numpy_version": np.__version__,
            "python_version": platform.python_version(),
        },
        "pilot_case_ids": sorted(PILOT_CASES),
        "held_out_case_ids": list(HELD_OUT_CASES),
        "cases": summaries,
    }
    (args.output_dir / "heldout_matching_results.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
