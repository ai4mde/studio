from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .adapters import activity_graph_to_eval_graph, friedrich_reference_to_eval_graph
from .calibrate_action_similarity import MODEL_NAME, MODEL_REVISION
from .linguistic_operations import LinguisticOperationExtractor
from .prototype import _extract_activity_graph
from .revised_action_matching import apply_revised_matching


VALIDATION_CASES = {
    "8-1": "simple sequential HR process",
    "1-1": "nested decision and loop in bicycle manufacturing",
    "2-2": "decision, loop, and explicit parallel structure in supplier switching",
    "3-8": "decision-oriented claims-handling process",
    "10-9": "nested decision process from the Messwesen collection",
}
EXCLUDED_CASES = frozenset(
    {
        "6-2", "5-2", "3-3", "6-3", "9-6", "4-1", "9-5",
        "3-1", "3-4", "8-2", "10-7", "1-2",
        "3-2", "3-6", "5-4", "10-6", "10-8",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rounded(value: Any) -> Any:
    return round(value, 8) if isinstance(value, float) else value


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Run the frozen-ish revised Action matcher on untouched cases"
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("/Users/queenie/Desktop/evaluation-data/friedrich_47_case_catalog.csv"),
    )
    parser.add_argument(
        "--model-cache", type=Path, default=Path("/private/tmp/friedrich-hf-cache")
    )
    parser.add_argument(
        "--wordnet-data", type=Path, default=Path("/private/tmp/friedrich-nltk-data")
    )
    parser.add_argument(
        "--output-dir", type=Path, default=base / "untouched_validation"
    )
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()

    if set(VALIDATION_CASES) & EXCLUDED_CASES:
        raise ValueError("Untouched validation selection overlaps prior evaluation cases")

    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer

    with args.catalog.open(encoding="utf-8", newline="") as handle:
        catalog = {row["case_id"]: row for row in csv.DictReader(handle)}

    reference_graphs = {}
    generated_graphs = {}
    case_records = []
    all_labels: set[str] = set()
    for case_id, rationale in VALIDATION_CASES.items():
        item = catalog[case_id]
        reference_path = Path(item["reference_model_path"])
        generated_path = Path(item["generated_artifact_output_path"]) / "run_1.json"
        reference_graph = friedrich_reference_to_eval_graph(reference_path)
        artifact = json.loads(generated_path.read_text(encoding="utf-8"))
        generated_graph = activity_graph_to_eval_graph(_extract_activity_graph(artifact))
        reference_graphs[case_id] = reference_graph
        generated_graphs[case_id] = generated_graph
        reference_actions = [node for node in reference_graph.nodes if node.type == "action" and node.label]
        generated_actions = [node for node in generated_graph.nodes if node.type == "action" and node.label]
        all_labels.update(node.label for node in (*reference_actions, *generated_actions))
        case_records.append(
            {
                "case_id": case_id,
                "case_name": Path(item["source_process_text_file"]).stem,
                "selection_rationale": rationale,
                "catalog_pattern": item["major_process_pattern"],
                "has_decision": item["has_decision"],
                "has_loop": item["has_loop"],
                "has_parallel": item["has_parallel"],
                "reference_path": str(reference_path),
                "reference_sha256": _sha256(reference_path),
                "generated_path": str(generated_path),
                "generated_sha256": _sha256(generated_path),
                "reference_actions": reference_actions,
                "generated_actions": generated_actions,
            }
        )

    extractor = LinguisticOperationExtractor(args.wordnet_data)
    representations = {label: extractor.extract(label) for label in sorted(all_labels)}
    texts = sorted(
        {
            text
            for representation in representations.values()
            for text in (
                representation.original_normalized_label,
                representation.canonical_label,
                representation.canonical_operation,
            )
        }
    )
    torch.manual_seed(0)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
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

    rows: list[dict[str, Any]] = []
    action_rows: list[dict[str, Any]] = []
    for case in case_records:
        case_id = case["case_id"]
        for side in ("reference", "generated"):
            for node in case[f"{side}_actions"]:
                representation = representations[node.label]
                action_rows.append(
                    {
                        "case_id": case_id,
                        "case_name": case["case_name"],
                        "side": side,
                        "action_id": node.id,
                        "label": node.label,
                        "canonical_operation": representation.canonical_operation,
                        "operation_resolved": representation.operation_resolved,
                        "object_phrase": representation.object_phrase or "",
                        "canonical_label": representation.canonical_label,
                    }
                )
        for reference in case["reference_actions"]:
            for generated in case["generated_actions"]:
                reference_rep = representations[reference.label]
                generated_rep = representations[generated.label]
                original = float(np.dot(embeddings[reference.label], embeddings[generated.label]))
                canonical = float(np.dot(embeddings[reference_rep.canonical_label], embeddings[generated_rep.canonical_label]))
                operation = float(np.dot(embeddings[reference_rep.canonical_operation], embeddings[generated_rep.canonical_operation]))
                rows.append(
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
                        "cosine_similarity": original,
                        "canonical_similarity": canonical,
                        "semantic_similarity": max(original, canonical),
                        "operation_similarity": operation,
                        "reference_representation": reference_rep.to_dict(),
                        "generated_representation": generated_rep.to_dict(),
                    }
                )

    evaluated, topology_decisions = apply_revised_matching(
        rows, reference_graphs, generated_graphs
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "untouched_actions.csv", action_rows)
    candidate_rows = []
    for row in evaluated:
        item = {key: _rounded(value) for key, value in row.items()}
        for field in (
            "reference_representation",
            "generated_representation",
            "topology_evidence",
            "unresolved_reference_nodes",
            "unresolved_generated_nodes",
            "unresolved_candidate_pairs",
        ):
            item[field] = json.dumps(item[field], sort_keys=True) if item[field] else ""
        candidate_rows.append(item)
    _write_csv(args.output_dir / "untouched_candidate_matrix.csv", candidate_rows)

    cases = []
    for case in case_records:
        case_id = case["case_id"]
        selected = [row for row in evaluated if row["case_id"] == case_id and row["final_prediction"]]
        matched_reference = {str(row["reference_id"]) for row in selected}
        matched_generated = {str(row["generated_id"]) for row in selected}
        unresolved_by_id: dict[str, dict[str, Any]] = {}
        for row in evaluated:
            if row["case_id"] != case_id or not row["unresolved_ambiguity"]:
                continue
            component_id = str(row["unresolved_component_id"])
            unresolved_by_id[component_id] = {
                "component_id": component_id,
                "reason": row["unresolved_reason"],
                "reference_nodes": row["unresolved_reference_nodes"],
                "generated_nodes": row["unresolved_generated_nodes"],
                "candidate_pairs": row["unresolved_candidate_pairs"],
            }
        cases.append(
            {
                **{key: value for key, value in case.items() if key not in {"reference_actions", "generated_actions"}},
                "reference_action_count": len(case["reference_actions"]),
                "generated_action_count": len(case["generated_actions"]),
                "selected_matches": [
                    {
                        "reference_id": str(row["reference_id"]),
                        "reference_label": row["reference_label"],
                        "generated_id": str(row["generated_id"]),
                        "generated_label": row["generated_label"],
                        "semantic_similarity": _rounded(row["semantic_similarity"]),
                        "reference_operation": row["reference_representation"]["canonical_operation"],
                        "generated_operation": row["generated_representation"]["canonical_operation"],
                        "operation_similarity": _rounded(row["operation_similarity"]),
                        "operation_compatible": row["operation_compatible"],
                        "compatibility_reason": row["compatibility_reason"],
                        "selection_stage": row["selection_stage"],
                        "topology_used": row["selection_stage"] == "topology_tie_break",
                        "topology_evidence": row["topology_evidence"],
                    }
                    for row in sorted(selected, key=lambda item: str(item["reference_id"]))
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
                "unresolved_components": [
                    unresolved_by_id[key] for key in sorted(unresolved_by_id)
                ],
            }
        )

    report = {
        "scope": {
            "selected_cases": list(VALIDATION_CASES),
            "excluded_prior_cases": sorted(EXCLUDED_CASES),
            "overlap": sorted(set(VALIDATION_CASES) & EXCLUDED_CASES),
        },
        "frozen_matcher": {
            "semantic_threshold": 0.44,
            "operation_threshold": None,
            "action_matching_sha256": _sha256(base / "action_matching.py"),
            "linguistic_operations_sha256": _sha256(base / "linguistic_operations.py"),
            "revised_action_matching_sha256": _sha256(base / "revised_action_matching.py"),
            "model": MODEL_NAME,
            "model_revision": MODEL_REVISION,
        },
        "topology_decisions": topology_decisions,
        "cases": cases,
    }
    (args.output_dir / "untouched_raw_results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
