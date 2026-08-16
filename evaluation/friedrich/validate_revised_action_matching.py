from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .action_matching import PROVISIONAL_THRESHOLD, apply_one_to_one_matching
from .adapters import activity_graph_to_eval_graph, friedrich_reference_to_eval_graph
from .calibrate_action_similarity import MODEL_NAME, MODEL_REVISION
from .linguistic_operations import LinguisticOperationExtractor
from .prototype import _extract_activity_graph
from .revised_action_matching import apply_revised_matching


DEVELOPMENT_CASES = ("3-2", "3-6", "5-4", "10-6", "10-8")
PROTECTED_HELD_OUT_CASES = frozenset({"3-1", "3-4", "8-2", "10-7", "1-2"})
DEVELOPMENT_SHA256 = "4e5ea31e8d18690edb9891a35d1ecb4d4de748460e0d5128d23b245e1d989c6e"
PROTECTED_HASHES = {
    "action_matching_pilot_pairs.csv": "5d0b01e8ed28032f7904c72d6a4e5517e82fc276f73f0d617f5d680b348494a1",
    "calibration/action_similarity_results.csv": "bf6fea332902e99dbdcd32db63963da63484fa78a2ee8e9fa07e36c8d98e0e6b",
    "heldout_validation/heldout_reviewed_matches.csv": "c9b79287baee181dce679858c4a37c3275d45e754eb829faf710ad92b7a21900",
    "heldout_validation/heldout_missed_matches.csv": "2bfdeb8a3b3f9caf6dcb2a2263a9ba105ae21f188603f251a2007a1855907637",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rounded(value: Any) -> Any:
    return round(value, 8) if isinstance(value, float) else value


def _summary(
    selected: set[tuple[str, str, str]], annotations: list[dict[str, str]]
) -> dict[str, Any]:
    categories = {
        (row["case_id"], row["reference_id"], row["generated_id"]): row["annotation_category"]
        for row in annotations
    }
    expected = {pair for pair, category in categories.items() if category in {"equivalent", "structurally_resolvable"}}
    granularity = {pair for pair, category in categories.items() if category == "granularity_mismatch"}
    unresolved = {pair for pair, category in categories.items() if category == "unresolved_ambiguous"}
    return {
        "selected_matches": len(selected),
        "correct_matches": len(selected & expected),
        "false_matches": len(selected - expected - granularity - unresolved),
        "missed_matches": len(expected - selected),
        "granularity_mismatches_selected": len(selected & granularity),
        "granularity_annotations": len(granularity),
        "unresolved_pairs_selected": len(selected & unresolved),
        "unresolved_annotations": len(unresolved),
    }


def main() -> None:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("/Users/queenie/Desktop/evaluation-data/friedrich_47_case_catalog.csv"))
    parser.add_argument("--model-cache", type=Path, default=Path("/private/tmp/friedrich-hf-cache"))
    parser.add_argument("--wordnet-data", type=Path, default=Path("/private/tmp/friedrich-nltk-data"))
    parser.add_argument("--output-dir", type=Path, default=base / "development" / "revised_validation")
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()

    for relative, expected_hash in PROTECTED_HASHES.items():
        if _sha256(base / relative) != expected_hash:
            raise ValueError(f"Protected evidence changed: {relative}")
    annotation_path = base / "development" / "action_matching_development_pairs.csv"
    if _sha256(annotation_path) != DEVELOPMENT_SHA256:
        raise ValueError("Frozen development annotations changed")
    with annotation_path.open(encoding="utf-8", newline="") as handle:
        annotations = list(csv.DictReader(handle))
    if {row["case_id"] for row in annotations} & PROTECTED_HELD_OUT_CASES:
        raise ValueError("Development annotations overlap protected held-out cases")

    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer

    with args.catalog.open(encoding="utf-8", newline="") as handle:
        catalog = {row["case_id"]: row for row in csv.DictReader(handle)}
    reference_graphs = {}
    generated_graphs = {}
    labels: set[str] = set()
    case_names = {}
    for case_id in DEVELOPMENT_CASES:
        item = catalog[case_id]
        reference_graphs[case_id] = friedrich_reference_to_eval_graph(item["reference_model_path"])
        artifact_path = Path(item["generated_artifact_output_path"]) / "run_1.json"
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        generated_graphs[case_id] = activity_graph_to_eval_graph(_extract_activity_graph(artifact))
        case_names[case_id] = Path(item["source_process_text_file"]).stem
        for graph in (reference_graphs[case_id], generated_graphs[case_id]):
            labels.update(node.label for node in graph.nodes if node.type == "action" and node.label)

    extractor = LinguisticOperationExtractor(args.wordnet_data)
    representations = {label: extractor.extract(label) for label in sorted(labels)}
    texts = sorted({text for rep in representations.values() for text in (rep.original_normalized_label, rep.canonical_label, rep.canonical_operation)})
    torch.manual_seed(0)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    model = SentenceTransformer(MODEL_NAME, revision=MODEL_REVISION, device="cpu", cache_folder=str(args.model_cache), local_files_only=args.local_files_only)
    vectors = model.encode(texts, batch_size=32, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
    embeddings = dict(zip(texts, vectors))

    rows: list[dict[str, Any]] = []
    for case_id in DEVELOPMENT_CASES:
        references = [node for node in reference_graphs[case_id].nodes if node.type == "action" and node.label]
        generated = [node for node in generated_graphs[case_id].nodes if node.type == "action" and node.label]
        for reference in references:
            for candidate in generated:
                reference_rep = representations[reference.label]
                generated_rep = representations[candidate.label]
                original = float(np.dot(embeddings[reference.label], embeddings[candidate.label]))
                canonical = float(np.dot(embeddings[reference_rep.canonical_label], embeddings[generated_rep.canonical_label]))
                operation = float(np.dot(embeddings[reference_rep.canonical_operation], embeddings[generated_rep.canonical_operation]))
                rows.append({
                    "pair_id": f"{case_id}:{reference.id}:{candidate.id}", "case_id": case_id,
                    "case_name": case_names[case_id], "reference_id": reference.id,
                    "reference_label": reference.label, "reference_normalized": reference.label,
                    "generated_id": candidate.id, "generated_label": candidate.label,
                    "generated_normalized": candidate.label, "cosine_similarity": original,
                    "canonical_similarity": canonical, "semantic_similarity": max(original, canonical),
                    "operation_similarity": operation,
                    "reference_representation": reference_rep.to_dict(),
                    "generated_representation": generated_rep.to_dict(),
                })

    previous_rows = apply_one_to_one_matching(rows, PROVISIONAL_THRESHOLD)
    revised_rows, topology_decisions = apply_revised_matching(rows, reference_graphs, generated_graphs)
    previous_selected = {(str(row["case_id"]), str(row["reference_id"]), str(row["generated_id"])) for row in previous_rows if row["final_prediction"]}
    revised_selected = {(str(row["case_id"]), str(row["reference_id"]), str(row["generated_id"])) for row in revised_rows if row["final_prediction"]}
    row_by_pair = {(str(row["case_id"]), str(row["reference_id"]), str(row["generated_id"])): row for row in revised_rows}
    changed = []
    for pair in sorted(previous_selected ^ revised_selected):
        row = row_by_pair[pair]
        changed.append({
            "case_id": pair[0], "reference_id": pair[1], "reference_label": row["reference_label"],
            "generated_id": pair[2], "generated_label": row["generated_label"],
            "previous_selected": pair in previous_selected, "revised_selected": pair in revised_selected,
            "original_similarity": _rounded(row["cosine_similarity"]),
            "canonical_similarity": _rounded(row["canonical_similarity"]),
            "operation_similarity": _rounded(row["operation_similarity"]),
            "revised_selection_stage": row["selection_stage"],
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    serializable_rows = []
    for row in revised_rows:
        item = {key: _rounded(value) for key, value in row.items()}
        item["reference_representation"] = json.dumps(item["reference_representation"], sort_keys=True)
        item["generated_representation"] = json.dumps(item["generated_representation"], sort_keys=True)
        item["topology_evidence"] = json.dumps(item["topology_evidence"], sort_keys=True) if item["topology_evidence"] else ""
        serializable_rows.append(item)
    with (args.output_dir / "revised_candidate_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(serializable_rows[0]))
        writer.writeheader(); writer.writerows(serializable_rows)
    report = {
        "scope": {"development_cases": list(DEVELOPMENT_CASES), "protected_held_out_cases_used": [], "development_annotation_sha256": DEVELOPMENT_SHA256},
        "method": {"semantic_threshold": PROVISIONAL_THRESHOLD, "semantic_score": "max(original_label_cosine, canonical_operation_object_cosine)", "operation_threshold": None, "operation_guard": "frozen small conflict map", "assignment": "deterministic global maximum-weight one-to-one", "topology": "nearest locked predecessor/successor anchors; unique reciprocal winner only"},
        "annotation_counts": dict(Counter(row["annotation_category"] for row in annotations)),
        "previous": _summary(previous_selected, annotations),
        "revised": {**_summary(revised_selected, annotations), "topology_resolved_cases": sorted({row["case_id"] for row in topology_decisions}), "topology_resolved_matches": len(topology_decisions)},
        "changed_decisions": changed,
        "topology_decisions": topology_decisions,
        "selected_matches": [
            {"case_id": pair[0], "reference_id": pair[1], "reference_label": row_by_pair[pair]["reference_label"], "generated_id": pair[2], "generated_label": row_by_pair[pair]["generated_label"], "stage": row_by_pair[pair]["selection_stage"]}
            for pair in sorted(revised_selected)
        ],
    }
    (args.output_dir / "development_comparison.json").write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
