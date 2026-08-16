from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from .action_matching import (
    INCOMPATIBLE_FAMILY_PAIRS,
    OPERATION_FAMILIES,
    PROVISIONAL_THRESHOLD,
    apply_one_to_one_matching,
    prediction_metrics,
)
from .calibrate_action_similarity import FROZEN_PILOT_SHA256, load_calibration_rows


def _rounded(value: Any) -> Any:
    return round(value, 8) if isinstance(value, float) else value


def _read_similarity_scores(path: Path) -> dict[str, float]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row["pair_id"]: float(row["cosine_similarity"]) for row in rows}


def main() -> None:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Validate operation compatibility and one-to-one action matching"
    )
    parser.add_argument(
        "--pilot", type=Path, default=base / "action_matching_pilot_pairs.csv"
    )
    parser.add_argument(
        "--similarities",
        type=Path,
        default=base / "calibration" / "action_similarity_results.csv",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=base / "matching_validation"
    )
    parser.add_argument("--threshold", type=float, default=PROVISIONAL_THRESHOLD)
    args = parser.parse_args()

    pilot_rows = load_calibration_rows(args.pilot)
    scores = _read_similarity_scores(args.similarities)
    expected_ids = {row["pair_id"] for row in pilot_rows}
    if set(scores) != expected_ids:
        raise ValueError("Similarity artifact does not match the frozen eligible subset")

    scored_rows = [
        {**row, "cosine_similarity": scores[row["pair_id"]]}
        for row in pilot_rows
    ]
    evaluated = apply_one_to_one_matching(scored_rows, args.threshold)
    before = prediction_metrics(evaluated, "threshold_prediction")
    after_compatibility = prediction_metrics(evaluated, "candidate_after_compatibility")
    after_assignment = prediction_metrics(evaluated, "final_prediction")

    output_fields = [
        "pair_id",
        "case_id",
        "reference_id",
        "reference_label",
        "generated_id",
        "generated_label",
        "annotation_category",
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
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "action_matching_validation.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(
            {key: _rounded(row[key]) for key in output_fields} for row in evaluated
        )

    changed = [
        {
            "pair_id": row["pair_id"],
            "reference_label": row["reference_label"],
            "generated_label": row["generated_label"],
            "cosine_similarity": _rounded(row["cosine_similarity"]),
            "human_annotation": row["annotation_category"],
            "old_prediction": "equivalent" if row["threshold_prediction"] else "different",
            "new_prediction": "equivalent" if row["final_prediction"] else "different",
            "change_source": row["decision_change_source"],
            "reason": row["compatibility_reason"],
        }
        for row in evaluated
        if row["threshold_prediction"] != row["final_prediction"]
    ]
    summary = {
        "frozen_pilot_sha256": FROZEN_PILOT_SHA256,
        "threshold": args.threshold,
        "candidate_rule": "cosine_similarity >= threshold",
        "operation_rule": {
            "families": OPERATION_FAMILIES,
            "incompatible_family_pairs": sorted(
                sorted(pair) for pair in INCOMPATIBLE_FAMILY_PAIRS
            ),
            "unclassified_policy": "compatible; defer to semantic similarity",
        },
        "assignment": (
            "per-case maximum-weight bipartite assignment over compatible "
            "threshold candidates; sorted node IDs; each node used at most once"
        ),
        "metrics": {
            "threshold_only": {key: _rounded(value) for key, value in before.items()},
            "after_operation_compatibility": {
                key: _rounded(value) for key, value in after_compatibility.items()
            },
            "after_one_to_one_assignment": {
                key: _rounded(value) for key, value in after_assignment.items()
            },
        },
        "changed_decisions": changed,
        "operation_compatibility_changes": sum(
            row["decision_change_source"] == "operation_compatibility"
            for row in evaluated
        ),
        "one_to_one_assignment_changes": sum(
            row["decision_change_source"] == "one_to_one_assignment"
            for row in evaluated
        ),
    }
    (args.output_dir / "action_matching_validation_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
