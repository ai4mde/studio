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
    "review_cluster_id", "cluster_member_count", "cluster_members",
    "generation_status", "attempt_count", "failure_reason", "failure_stage",
    "item_payload", "local_evidence", "automatic_rationale", "reviewer_verdict",
    "explanation_category", "source_scope", "confidence", "redundancy_decision", "reviewer_rationale",
    "second_reviewer_verdict", "second_explanation_category", "final_verdict",
    "final_explanation_category",
)
VERDICTS = {"", "uphold", "overturn", "unresolved"}
CATEGORIES = {"", "generation_error", "plausible_modelling_variation", "evaluation_limitation", "ambiguous"}
SOURCE_SCOPE = {
    "", "in_scope_executable_action", "trigger_event", "precondition", "postcondition",
    "out_of_scope_interaction", "reference_only_modelling_addition",
}
SOURCE_SUPPORTED_ACCEPTANCE_RULE = (
    "A deviation may be accepted only when the source text explicitly states or logically entails it, "
    "and it neither removes required behavior, introduces an unsupported alternative, imposes an "
    "unsupported ordering restriction, nor reverses a required branch outcome."
)
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
    selected: list[tuple[AutomaticItem, str, str, str, str]] = []

    def semantic_neighbors(value: object) -> object:
        if not isinstance(value, Mapping):
            return value
        return {
            direction: sorted(
                ({"type": neighbor.get("type"), "label": neighbor.get("label")} for neighbor in neighbors),
                key=canonical_json,
            )
            for direction, neighbors in value.items()
            if isinstance(neighbors, list)
        }

    for item in all_items:
        trigger = ""
        deterministic_triggers = item.payload.get("review_triggers", [])
        if isinstance(deterministic_triggers, (list, tuple)) and deterministic_triggers:
            trigger = ";".join(sorted(str(value) for value in deterministic_triggers))
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
        review_cluster_concept = item.payload.get("review_cluster_concept")
        concept = canonical_json({
            "reference_label": item.evidence.get("reference_label"),
            "generated_label": item.evidence.get("generated_label"),
            "fact": None if review_cluster_concept is not None else item.payload.get("fact"),
            "diagnostic_type": item.payload.get("diagnostic_type"),
            "source_reference_action": item.payload.get("source_reference_action"),
            "target_reference_action": item.payload.get("target_reference_action"),
            "review_cluster_concept": review_cluster_concept,
        })
        context = canonical_json({
            "reference_context": semantic_neighbors(item.evidence.get("reference_context")),
            "generated_context": semantic_neighbors(item.evidence.get("generated_context")),
        })
        unique_scope = item.item_id if trigger in {
            "seeded_tp_audit", "redundancy_candidate", "generation_failure_audit"
        } else ""
        cluster_key = canonical_json({
            "case_id": item.case_id,
            "issue_type": trigger,
            "semantic_concept": concept,
            "local_context": context,
            "unique_scope": unique_scope,
        })
        selected.append((item, trigger, concept, context, cluster_key))

    clusters: dict[str, list[tuple[AutomaticItem, str, str, str, str]]] = {}
    for selected_item in selected:
        clusters.setdefault(selected_item[4], []).append(selected_item)

    rows: list[dict[str, str]] = []
    for item, trigger, concept, context, cluster_key in selected:
        cluster = clusters[cluster_key]
        cluster_id = "hrc-" + hashlib.sha256(cluster_key.encode("utf-8")).hexdigest()[:20]
        members = [
            {
                "case_id": member.case_id,
                "candidate_id": member.candidate_id,
                "metric": member.metric,
                "item_id": member.item_id,
                "automatic_label": member.label,
                "issue_type": member_trigger,
                "semantic_concept": json.loads(member_concept),
                "local_context": json.loads(member_context),
            }
            for member, member_trigger, member_concept, member_context, _ in sorted(
                cluster, key=lambda value: (value[0].candidate_id, value[0].metric, value[0].item_id)
            )
        ]
        rows.append({
            "case_id": item.case_id, "candidate_id": item.candidate_id,
            "metric": item.metric, "item_id": item.item_id,
            "review_trigger": trigger, "automatic_label": item.label,
            "review_cluster_id": cluster_id, "cluster_member_count": str(len(members)),
            "cluster_members": canonical_json(members),
            "generation_status": str(item.payload.get("generation_status") or ""),
            "attempt_count": str(item.payload.get("attempt_count") or ""),
            "failure_reason": str(item.payload.get("failure_reason") or ""),
            "failure_stage": str(item.payload.get("failure_stage") or ""),
            "item_payload": canonical_json(item.payload), "local_evidence": canonical_json(item.evidence),
            "automatic_rationale": item.rationale, "reviewer_verdict": "",
            "explanation_category": "", "source_scope": "", "confidence": "", "redundancy_decision": "",
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
    adjudication_fields = (
        "reviewer_verdict", "explanation_category", "source_scope", "confidence",
        "redundancy_decision", "reviewer_rationale", "second_reviewer_verdict",
        "second_explanation_category", "final_verdict", "final_explanation_category",
    )
    clusters: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        clusters.setdefault(row["review_cluster_id"], []).append(row)
    for cluster_id, cluster_rows in clusters.items():
        if not cluster_id:
            raise ValueError("Human Review cluster id must not be empty")
        declared_members = {row["cluster_members"] for row in cluster_rows}
        if len(declared_members) != 1:
            raise ValueError("Human Review cluster members disagree")
        try:
            members = json.loads(next(iter(declared_members)))
        except json.JSONDecodeError as exc:
            raise ValueError("Human Review cluster members are invalid JSON") from exc
        if not isinstance(members, list) or any(
            row["cluster_member_count"] != str(len(members)) for row in cluster_rows
        ):
            raise ValueError("Human Review cluster member count is invalid")
        actual_keys = {
            (row["case_id"], row["candidate_id"], row["metric"], row["item_id"])
            for row in cluster_rows
        }
        declared_keys = {
            (member.get("case_id"), member.get("candidate_id"), member.get("metric"), member.get("item_id"))
            for member in members if isinstance(member, dict)
        }
        if actual_keys != declared_keys:
            raise ValueError("Human Review cluster does not retain every affected item")
        completed = {
            tuple(row[field] for field in adjudication_fields)
            for row in cluster_rows
            if row["reviewer_verdict"] or row["final_verdict"]
        }
        if len(completed) == 1:
            adjudication = next(iter(completed))
            for row in cluster_rows:
                if not row["reviewer_verdict"] and not row["final_verdict"]:
                    row.update(dict(zip(adjudication_fields, adjudication)))
    for row in rows:
        if row["reviewer_verdict"] not in VERDICTS or row["final_verdict"] not in VERDICTS:
            raise ValueError("Invalid Human Review verdict")
        if row["explanation_category"] not in CATEGORIES or row["final_explanation_category"] not in CATEGORIES:
            raise ValueError("Invalid Human Review explanation category")
        if row["source_scope"] not in SOURCE_SCOPE:
            raise ValueError("Invalid Human Review source scope")
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
