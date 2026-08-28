from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Mapping

from .core import AutomaticItem, Counts, canonical_json


REVIEW_FIELDS = (
    "case_id", "candidate_id", "metric", "item_id", "review_trigger", "automatic_label",
    "generation_status", "attempt_count", "failure_reason", "failure_stage",
    "item_payload", "local_evidence", "automatic_rationale", "reviewer_verdict",
    "explanation_category", "confidence", "redundancy_decision", "reviewer_rationale",
    "second_reviewer_verdict", "second_explanation_category", "final_verdict",
    "final_explanation_category",
)
VERDICTS = {"", "uphold", "overturn", "unresolved"}
CATEGORIES = {"", "generation_error", "plausible_modelling_variation", "evaluation_limitation", "ambiguous"}
CONFIDENCE = {"", "High", "Medium", "Low"}
REDUNDANCY = {"", "confirmed_redundant", "not_redundant", "uncertain"}


def _audit_sample(items: list[AutomaticItem], seed: int) -> set[str]:
    selected: set[str] = set()
    for metric in ("Action", "Flow", "Structure"):
        candidates = [item for item in items if item.metric == metric and item.label == "TP"]
        amount = min(len(candidates), 20, max(5, math.ceil(len(candidates) * 0.10)))
        grouped: dict[tuple[str, str], list[AutomaticItem]] = {}
        for item in candidates:
            grouped.setdefault((item.case_id, item.candidate_id), []).append(item)
        group_order = sorted(
            grouped,
            key=lambda key: hashlib.sha256(f"{seed}:{metric}:{key[0]}:{key[1]}".encode()).hexdigest(),
        )
        for group in grouped.values():
            group.sort(key=lambda item: hashlib.sha256(f"{seed}:{item.item_id}".encode()).hexdigest())
        depth = 0
        while len(selected & {item.item_id for item in candidates}) < amount:
            added = False
            for key in group_order:
                if depth < len(grouped[key]):
                    selected.add(grouped[key][depth].item_id)
                    added = True
                    if len(selected & {item.item_id for item in candidates}) == amount:
                        break
            if not added:
                break
            depth += 1
    return selected


def build_review_rows(items: Iterable[AutomaticItem], seed: int) -> list[dict[str, str]]:
    all_items = list(items)
    audit = _audit_sample(all_items, seed)
    rows: list[dict[str, str]] = []
    for item in all_items:
        trigger = ""
        if item.label in {"FP", "FN"}:
            trigger = "automatic_error"
        elif item.label == "UNSCORABLE":
            trigger = "unsupported_or_unscorable"
        elif item.metric == "Redundant Control Nodes":
            trigger = "redundancy_candidate"
        elif item.metric == "Generation" and item.label == "FAILED":
            trigger = "generation_failure_audit"
        elif item.item_id in audit:
            trigger = "seeded_tp_audit"
        if not trigger:
            continue
        rows.append({
            "case_id": item.case_id, "candidate_id": item.candidate_id,
            "metric": item.metric, "item_id": item.item_id,
            "review_trigger": trigger, "automatic_label": item.label,
            "generation_status": str(item.payload.get("generation_status") or ""),
            "attempt_count": str(item.payload.get("attempt_count") or ""),
            "failure_reason": str(item.payload.get("failure_reason") or ""),
            "failure_stage": str(item.payload.get("failure_stage") or ""),
            "item_payload": canonical_json(item.payload), "local_evidence": canonical_json(item.evidence),
            "automatic_rationale": item.rationale, "reviewer_verdict": "",
            "explanation_category": "", "confidence": "", "redundancy_decision": "",
            "reviewer_rationale": "", "second_reviewer_verdict": "",
            "second_explanation_category": "", "final_verdict": "",
            "final_explanation_category": "",
        })
    return sorted(rows, key=lambda row: (row["case_id"], row["candidate_id"], row["metric"], row["item_id"]))


def write_review_csv(path: str | Path, rows: Iterable[Mapping[str, str]]) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def load_review_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REVIEW_FIELDS:
            raise ValueError("Human Review CSV schema does not match Friedrich V2")
        rows = list(reader)
    for row in rows:
        if row["reviewer_verdict"] not in VERDICTS or row["final_verdict"] not in VERDICTS:
            raise ValueError("Invalid Human Review verdict")
        if row["explanation_category"] not in CATEGORIES or row["final_explanation_category"] not in CATEGORIES:
            raise ValueError("Invalid Human Review explanation category")
        if row["confidence"] not in CONFIDENCE or row["redundancy_decision"] not in REDUNDANCY:
            raise ValueError("Invalid Human Review confidence or redundancy decision")
    return rows


def review_adjusted_counts(
    raw: Counts,
    metric: str,
    rows: Iterable[Mapping[str, str]],
    *,
    case_id: str,
    candidate_id: str,
) -> Counts:
    tp, fp, fn = raw.tp, raw.fp, raw.fn
    for row in rows:
        if row["metric"] != metric or row["case_id"] != case_id or row["candidate_id"] != candidate_id:
            continue
        verdict = row["final_verdict"] or row["reviewer_verdict"]
        if verdict != "overturn":
            continue
        if row["automatic_label"] == "FP":
            fp = max(0, fp - 1)
        elif row["automatic_label"] == "FN":
            fn = max(0, fn - 1)
        elif row["automatic_label"] == "TP":
            tp, fp, fn = max(0, tp - 1), fp + 1, fn + 1
    return Counts(tp, fp, fn)
