from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
from typing import Any, Iterable

from .eval_graph import normalize_label


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
FROZEN_PILOT_SHA256 = "5d0b01e8ed28032f7904c72d6a4e5517e82fc276f73f0d617f5d680b348494a1"
ELIGIBLE_CATEGORIES = frozenset({"equivalent", "different"})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_calibration_rows(path: Path) -> list[dict[str, str]]:
    actual_hash = _sha256(path)
    if actual_hash != FROZEN_PILOT_SHA256:
        raise ValueError(
            "Frozen pilot checksum mismatch: "
            f"expected {FROZEN_PILOT_SHA256}, got {actual_hash}"
        )

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    eligible = [
        row
        for row in rows
        if row["annotation_category"] in ELIGIBLE_CATEGORIES
        and row["used_topology"] == "no"
    ]
    positives = sum(row["annotation_category"] == "equivalent" for row in eligible)
    negatives = sum(row["annotation_category"] == "different" for row in eligible)
    if (len(rows), len(eligible), positives, negatives) != (35, 29, 19, 10):
        raise ValueError(
            "Unexpected frozen pilot composition: "
            f"rows={len(rows)}, eligible={len(eligible)}, "
            f"positives={positives}, negatives={negatives}"
        )

    for row in eligible:
        reference = normalize_label(row["reference_label"])
        generated = normalize_label(row["generated_label"])
        if reference != row["reference_normalized"]:
            raise ValueError(f"Reference normalization mismatch for {row['pair_id']}")
        if generated != row["generated_normalized"]:
            raise ValueError(f"Generated normalization mismatch for {row['pair_id']}")
    return eligible


def classification_metrics(
    rows: Iterable[dict[str, Any]], threshold: float
) -> dict[str, float | int]:
    tp = fp = fn = tn = 0
    for row in rows:
        predicted_positive = float(row["cosine_similarity"]) >= threshold
        actual_positive = row["annotation_category"] == "equivalent"
        if predicted_positive and actual_positive:
            tp += 1
        elif predicted_positive:
            fp += 1
        elif actual_positive:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / (tp + fp + fn + tn)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
    }


def threshold_plateaus(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scores = sorted({float(row["cosine_similarity"]) for row in rows})
    candidates: list[tuple[float, float | None, float | None]] = [
        (scores[0], None, scores[0])
    ]
    candidates.extend(
        ((lower + upper) / 2.0, lower, upper)
        for lower, upper in zip(scores, scores[1:])
    )
    candidates.append((math.nextafter(scores[-1], math.inf), scores[-1], None))

    results = []
    for threshold, lower, upper in candidates:
        results.append(
            {
                "threshold": threshold,
                "plateau_lower_exclusive": lower,
                "plateau_upper_inclusive": upper,
                **classification_metrics(rows, threshold),
            }
        )
    return results


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _rounded(value: Any) -> Any:
    return round(value, 8) if isinstance(value, float) else value


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calibrate text-only action similarity on the frozen pilot"
    )
    base = Path(__file__).resolve().parent
    parser.add_argument(
        "--pilot", type=Path, default=base / "action_matching_pilot_pairs.csv"
    )
    parser.add_argument("--output-dir", type=Path, default=base / "calibration")
    parser.add_argument("--recommended-threshold", type=float)
    parser.add_argument(
        "--model-cache",
        type=Path,
        default=Path("/private/tmp/friedrich-hf-cache"),
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Load the pinned model only from the local cache (no Hub requests)",
    )
    args = parser.parse_args()

    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("DO_NOT_TRACK", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer

    torch.manual_seed(0)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)

    rows = load_calibration_rows(args.pilot)
    texts = sorted(
        {
            text
            for row in rows
            for text in (row["reference_normalized"], row["generated_normalized"])
        }
    )
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

    scored_rows: list[dict[str, Any]] = []
    for row in rows:
        score = float(
            np.dot(
                embeddings[row["reference_normalized"]],
                embeddings[row["generated_normalized"]],
            )
        )
        scored_rows.append(
            {
                "pair_id": row["pair_id"],
                "case_id": row["case_id"],
                "reference_label": row["reference_label"],
                "generated_label": row["generated_label"],
                "reference_normalized": row["reference_normalized"],
                "generated_normalized": row["generated_normalized"],
                "annotation_category": row["annotation_category"],
                "cosine_similarity": score,
            }
        )

    plateaus = threshold_plateaus(scored_rows)
    best_f1 = max(float(row["f1"]) for row in plateaus)
    best_plateaus = [row for row in plateaus if math.isclose(row["f1"], best_f1)]

    recommended_metrics = None
    false_positives: list[str] = []
    false_negatives: list[str] = []
    if args.recommended_threshold is not None:
        recommended_metrics = classification_metrics(
            scored_rows, args.recommended_threshold
        )
        for row in scored_rows:
            predicted = float(row["cosine_similarity"]) >= args.recommended_threshold
            actual = row["annotation_category"] == "equivalent"
            row["predicted_category"] = "equivalent" if predicted else "different"
            row["classification_outcome"] = (
                "tp" if predicted and actual else
                "fp" if predicted else
                "fn" if actual else
                "tn"
            )
            if row["classification_outcome"] == "fp":
                false_positives.append(row["pair_id"])
            elif row["classification_outcome"] == "fn":
                false_negatives.append(row["pair_id"])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    similarity_fields = [
        "pair_id",
        "case_id",
        "reference_label",
        "generated_label",
        "reference_normalized",
        "generated_normalized",
        "annotation_category",
        "cosine_similarity",
    ]
    if args.recommended_threshold is not None:
        similarity_fields.extend(["predicted_category", "classification_outcome"])
    _write_csv(
        args.output_dir / "action_similarity_results.csv",
        similarity_fields,
        ({key: _rounded(row[key]) for key in similarity_fields} for row in scored_rows),
    )
    threshold_fields = [
        "threshold",
        "plateau_lower_exclusive",
        "plateau_upper_inclusive",
        "tp",
        "fp",
        "fn",
        "tn",
        "precision",
        "recall",
        "f1",
        "accuracy",
    ]
    _write_csv(
        args.output_dir / "action_threshold_results.csv",
        threshold_fields,
        ({key: _rounded(row[key]) for key in threshold_fields} for row in plateaus),
    )

    summary = {
        "frozen_pilot": {
            "path": str(args.pilot),
            "sha256": _sha256(args.pilot),
            "eligible_rule": (
                "annotation_category in {equivalent,different} and used_topology == no"
            ),
            "eligible_pairs": len(scored_rows),
            "positive_pairs": sum(
                row["annotation_category"] == "equivalent" for row in scored_rows
            ),
            "negative_pairs": sum(
                row["annotation_category"] == "different" for row in scored_rows
            ),
        },
        "normalization": (
            "Unicode NFKC; casefold; underscores/hyphens to spaces; non-word "
            "punctuation to spaces; collapse whitespace; trim; empty to null"
        ),
        "embedding": {
            "model": MODEL_NAME,
            "revision": MODEL_REVISION,
            "dimensions": int(vectors.shape[1]),
            "device": "cpu",
            "normalized_embeddings": True,
            "similarity": "cosine (dot product of L2-normalized embeddings)",
            "sentence_transformers_version": importlib.metadata.version(
                "sentence-transformers"
            ),
            "transformers_version": importlib.metadata.version("transformers"),
            "torch_version": torch.__version__,
            "numpy_version": np.__version__,
            "python_version": platform.python_version(),
        },
        "best_f1": best_f1,
        "best_plateaus": [
            {key: _rounded(value) for key, value in row.items()}
            for row in best_plateaus
        ],
        "recommended_threshold": args.recommended_threshold,
        "recommended_threshold_metrics": (
            {key: _rounded(value) for key, value in recommended_metrics.items()}
            if recommended_metrics
            else None
        ),
        "false_positive_pair_ids": false_positives,
        "false_negative_pair_ids": false_negatives,
    }
    (args.output_dir / "action_calibration_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
