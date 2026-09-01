from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

from .core import AutomaticItem


REVIEW_FIELDS = (
    "case_id", "candidate_id", "metric", "item_id", "review_trigger",
    "automatic_label", "item_payload", "local_evidence", "automatic_rationale",
    "reviewer_verdict", "reviewer_rationale", "final_verdict",
    "sensitivity_tp_delta", "sensitivity_fp_delta", "sensitivity_fn_delta",
)
TARGETED_TRIGGERS = {
    "possible_merge_action", "possible_split_action",
    "unresolved_duplicate_occurrence", "source_scope_ambiguity",
    "anchor_limited_flow_relation", "anchor_limited_structure_region",
    "guard_ambiguity", "ambiguous_structure_region",
    "unsupported_structure_region",
}


def _seeded_tp_ids(items: list[AutomaticItem], seed: int) -> set[str]:
    selected: set[str] = set()
    for metric in ("Action", "Flow", "Structure"):
        candidates = [
            item for item in items
            if item.metric == metric and item.label in {"TP", "SOFT"}
            and not item.payload.get("review_triggers")
        ]
        amount = min(len(candidates), 20, max(1, math.ceil(len(candidates) * 0.10)))
        ranked = sorted(
            candidates,
            key=lambda item: hashlib.sha256(f"{seed}:{item.item_id}".encode()).hexdigest(),
        )
        selected.update(item.item_id for item in ranked[:amount])
    return selected


def build_review_rows(items: Iterable[AutomaticItem], seed: int) -> list[dict[str, str]]:
    automatic = list(items)
    audit = _seeded_tp_ids(automatic, seed)
    rows: list[dict[str, str]] = []
    for item in automatic:
        triggers = set(item.payload.get("review_triggers", ())) & TARGETED_TRIGGERS
        if item.item_id in audit:
            triggers.add("seeded_tp_audit")
        if not triggers:
            continue
        rows.append({
            "case_id": item.case_id,
            "candidate_id": item.candidate_id,
            "metric": item.metric,
            "item_id": item.item_id,
            "review_trigger": ";".join(sorted(triggers)),
            "automatic_label": item.label,
            "item_payload": json.dumps(item.payload, ensure_ascii=True, sort_keys=True),
            "local_evidence": json.dumps(item.evidence, ensure_ascii=True, sort_keys=True),
            "automatic_rationale": item.rationale,
            "reviewer_verdict": "",
            "reviewer_rationale": "",
            "final_verdict": "",
            "sensitivity_tp_delta": "",
            "sensitivity_fp_delta": "",
            "sensitivity_fn_delta": "",
        })
    return sorted(rows, key=lambda row: (row["case_id"], row["candidate_id"], row["metric"], row["item_id"]))


def write_review_csv(path: Path, rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def build_sensitivity_results(
    candidate_rows: Iterable[dict[str, object]], review_rows: Iterable[dict[str, str]]
) -> dict[str, object]:
    """Apply explicit adjudicator count deltas without creating or rematching anchors."""
    adjusted = {
        (str(row["case_id"]), str(row["candidate_id"])): dict(row)
        for row in candidate_rows
    }
    adjudicated = 0
    for review in review_rows:
        if review.get("final_verdict") not in {"uphold", "overturn"}:
            continue
        deltas = {
            name: float(review.get(f"sensitivity_{name}_delta") or 0.0)
            for name in ("tp", "fp", "fn")
        }
        if not any(deltas.values()):
            continue
        metric = review["metric"].casefold()
        if metric not in {"action", "flow", "structure"}:
            raise ValueError(f"Unsupported sensitivity metric: {review['metric']}")
        row = adjusted[(review["case_id"], review["candidate_id"])]
        for name, delta in deltas.items():
            key = f"{metric}_{name}"
            row[key] = float(row[key]) + delta
            if float(row[key]) < 0.0:
                raise ValueError(f"Sensitivity delta makes {key} negative")
        adjudicated += 1
    return {
        "schema_version": "friedrich-v3-review-sensitivity/v1",
        "status": "computed" if adjudicated else "not_adjudicated",
        "adjudicated_item_count": adjudicated,
        "raw_automatic_results_modified": False,
        "many_to_many_anchors_synthesized": False,
        "flow_or_structure_anchors_recomputed": False,
        "candidate_counts": [
            {
                "case_id": row["case_id"], "candidate_id": row["candidate_id"],
                **{
                    f"{metric}_{name}": row[f"{metric}_{name}"]
                    for metric in ("action", "flow", "structure")
                    for name in ("tp", "fp", "fn")
                },
            }
            for row in adjusted.values()
        ] if adjudicated else [],
    }
