from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable

from .action_matching import PROVISIONAL_THRESHOLD, operation_compatibility
from .calibrate_action_similarity import (
    FROZEN_PILOT_SHA256,
    MODEL_NAME,
    MODEL_REVISION,
    load_calibration_rows,
)
from .linguistic_operations import LinguisticOperationExtractor


DEVELOPMENT_SHA256 = "4e5ea31e8d18690edb9891a35d1ecb4d4de748460e0d5128d23b245e1d989c6e"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_development_rows(path: Path) -> list[dict[str, str]]:
    if _sha256(path) != DEVELOPMENT_SHA256:
        raise ValueError("Frozen development annotation checksum mismatch")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    eligible = [row for row in rows if row["operation_calibration_eligible"] == "yes"]
    if (
        len(eligible),
        sum(row["annotation_category"] == "equivalent" for row in eligible),
        sum(row["annotation_category"] == "different" for row in eligible),
    ) != (26, 15, 11):
        raise ValueError("Unexpected frozen development calibration composition")
    return eligible


def _metrics(rows: Iterable[dict[str, Any]], threshold: float) -> dict[str, Any]:
    tp = fp = fn = tn = 0
    for row in rows:
        operation_pass = (
            not row["both_operations_resolved"]
            or float(row["operation_similarity"]) >= threshold
        )
        predicted = bool(
            row["semantic_candidate"]
            and row["existing_compatibility"]
            and operation_pass
        )
        actual = row["annotation_category"] == "equivalent"
        if predicted and actual:
            tp += 1
        elif predicted:
            fp += 1
        elif actual:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": (tp + tn) / (tp + fp + fn + tn),
    }


def _threshold_plateaus(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scores = sorted(
        {
            float(row["operation_similarity"])
            for row in rows
            if row["both_operations_resolved"]
        }
    )
    candidates: list[tuple[float, float | None, float | None]] = [
        (scores[0], None, scores[0])
    ]
    candidates.extend(
        ((lower + upper) / 2, lower, upper)
        for lower, upper in zip(scores, scores[1:])
    )
    candidates.append((math.nextafter(scores[-1], math.inf), scores[-1], None))
    return [
        {
            "operation_threshold": threshold,
            "plateau_lower_exclusive": lower,
            "plateau_upper_inclusive": upper,
            **_metrics(rows, threshold),
        }
        for threshold, lower, upper in candidates
    ]


def _rounded(value: Any) -> Any:
    return round(value, 8) if isinstance(value, float) else value


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
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
        description="Calibrate one operation-only threshold on frozen development data"
    )
    parser.add_argument(
        "--pilot", type=Path, default=base / "action_matching_pilot_pairs.csv"
    )
    parser.add_argument(
        "--development",
        type=Path,
        default=base / "development" / "action_matching_development_pairs.csv",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=base / "development" / "operation_calibration"
    )
    parser.add_argument(
        "--model-cache", type=Path, default=Path("/private/tmp/friedrich-hf-cache")
    )
    parser.add_argument(
        "--wordnet-data",
        type=Path,
        default=Path("/private/tmp/friedrich-nltk-data"),
    )
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--recommended-threshold", type=float)
    args = parser.parse_args()

    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("DO_NOT_TRACK", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer

    pilot = [
        {**row, "dataset": "pilot"} for row in load_calibration_rows(args.pilot)
    ]
    development = [
        {**row, "dataset": "development"}
        for row in _read_development_rows(args.development)
    ]
    rows = pilot + development
    if _sha256(args.pilot) != FROZEN_PILOT_SHA256:
        raise ValueError("Frozen pilot checksum mismatch")

    extractor = LinguisticOperationExtractor(args.wordnet_data)
    labels = sorted(
        {
            label
            for row in rows
            for label in (row["reference_normalized"], row["generated_normalized"])
        }
    )
    representations = {label: extractor.extract(label) for label in labels}
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

    scored: list[dict[str, Any]] = []
    for row in rows:
        reference = representations[row["reference_normalized"]]
        generated = representations[row["generated_normalized"]]
        original_similarity = float(
            np.dot(
                embeddings[reference.original_normalized_label],
                embeddings[generated.original_normalized_label],
            )
        )
        canonical_similarity = float(
            np.dot(
                embeddings[reference.canonical_label],
                embeddings[generated.canonical_label],
            )
        )
        operation_similarity = float(
            np.dot(
                embeddings[reference.canonical_operation],
                embeddings[generated.canonical_operation],
            )
        )
        compatibility = operation_compatibility(
            row["reference_normalized"], row["generated_normalized"]
        )
        scored.append(
            {
                "dataset": row["dataset"],
                "pair_id": row["pair_id"],
                "case_id": row["case_id"],
                "reference_label": row["reference_label"],
                "generated_label": row["generated_label"],
                "annotation_category": row["annotation_category"],
                "reference_operation": reference.canonical_operation,
                "reference_operation_resolved": reference.operation_resolved,
                "generated_operation": generated.canonical_operation,
                "generated_operation_resolved": generated.operation_resolved,
                "both_operations_resolved": (
                    reference.operation_resolved and generated.operation_resolved
                ),
                "reference_object": reference.object_phrase or "",
                "generated_object": generated.object_phrase or "",
                "reference_canonical_label": reference.canonical_label,
                "generated_canonical_label": generated.canonical_label,
                "original_similarity": original_similarity,
                "canonical_similarity": canonical_similarity,
                "semantic_similarity": max(original_similarity, canonical_similarity),
                "semantic_candidate": (
                    max(original_similarity, canonical_similarity) >= PROVISIONAL_THRESHOLD
                ),
                "operation_similarity": operation_similarity,
                "existing_compatibility": compatibility.compatible,
            }
        )

    plateaus = _threshold_plateaus(scored)
    best_f1 = max(row["f1"] for row in plateaus)
    best = [row for row in plateaus if math.isclose(row["f1"], best_f1)]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    score_fields = list(scored[0])
    _write_csv(args.output_dir / "operation_pair_scores.csv", score_fields, scored)
    threshold_fields = list(plateaus[0])
    _write_csv(
        args.output_dir / "operation_threshold_results.csv", threshold_fields, plateaus
    )
    summary = {
        "protected_inputs": {
            "pilot_sha256": _sha256(args.pilot),
            "development_sha256": _sha256(args.development),
            "held_out_cases_used": [],
        },
        "composition": {
            "pairs": len(scored),
            "positive": sum(
                row["annotation_category"] == "equivalent" for row in scored
            ),
            "negative": sum(
                row["annotation_category"] == "different" for row in scored
            ),
        },
        "candidate_rule": (
            "max(original full-label cosine, canonical operation+object cosine) "
            f">= {PROVISIONAL_THRESHOLD}; existing conflict filter; operation guard "
            "only when both operations are resolved"
        ),
        "best_f1": _rounded(best_f1),
        "best_plateaus": [
            {key: _rounded(value) for key, value in row.items()} for row in best
        ],
        "recommended_threshold": args.recommended_threshold,
        "threshold_decision": (
            "No additional operation threshold. The best-F1 plateau does not "
            "remove the remaining lifecycle negatives, while a higher cutoff "
            "rejects defensible cross-operation paraphrases. Operation similarity "
            "is retained as inspectable evidence; the frozen conflict map remains "
            "the compatibility guard."
            if args.recommended_threshold is None
            else "A scalar operation threshold was selected."
        ),
        "recommended_metrics": (
            {
                key: _rounded(value)
                for key, value in _metrics(scored, args.recommended_threshold).items()
            }
            if args.recommended_threshold is not None
            else None
        ),
    }
    (args.output_dir / "operation_calibration_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
