from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
from scipy.optimize import linear_sum_assignment


PROVISIONAL_THRESHOLD = 0.44

# Intentionally small: only verbs with a stable process-operation meaning are
# classified. Context-sensitive verbs such as register, submit, transfer, and
# enter remain unclassified and are decided by semantic similarity.
OPERATION_FAMILIES = {
    "accept": "approval",
    "approve": "approval",
    "check": "inspection",
    "create": "creation",
    "decline": "rejection",
    "dispatch": "transmission",
    "edit": "modification",
    "examine": "inspection",
    "forward": "transmission",
    "generate": "creation",
    "inspect": "inspection",
    "modify": "modification",
    "produce": "creation",
    "receive": "reception",
    "recheck": "inspection",
    "reject": "rejection",
    "review": "inspection",
    "revise": "modification",
    "send": "transmission",
    "test": "inspection",
    "update": "modification",
    "write": "creation",
}

INCOMPATIBLE_FAMILY_PAIRS = frozenset(
    {
        frozenset({"transmission", "reception"}),
        frozenset({"approval", "rejection"}),
        frozenset({"creation", "transmission"}),
        frozenset({"creation", "reception"}),
        frozenset({"inspection", "modification"}),
    }
)


@dataclass(frozen=True)
class Operation:
    token: str
    family: str


@dataclass(frozen=True)
class Compatibility:
    compatible: bool
    reference_operation: Operation | None
    generated_operation: Operation | None
    reason: str


def extract_operation(normalized_label: str) -> Operation | None:
    """Return the first high-confidence operation token in label order."""
    for token in normalized_label.split():
        family = OPERATION_FAMILIES.get(token)
        if family:
            return Operation(token=token, family=family)
    return None


def operation_compatibility(
    reference_normalized: str, generated_normalized: str
) -> Compatibility:
    reference = extract_operation(reference_normalized)
    generated = extract_operation(generated_normalized)
    if reference is None or generated is None:
        return Compatibility(
            compatible=True,
            reference_operation=reference,
            generated_operation=generated,
            reason="no_declared_conflict_unclassified_operation",
        )

    family_pair = frozenset({reference.family, generated.family})
    if family_pair in INCOMPATIBLE_FAMILY_PAIRS:
        return Compatibility(
            compatible=False,
            reference_operation=reference,
            generated_operation=generated,
            reason=(
                f"operation_conflict:{reference.family}({reference.token})"
                f"_vs_{generated.family}({generated.token})"
            ),
        )
    return Compatibility(
        compatible=True,
        reference_operation=reference,
        generated_operation=generated,
        reason="no_declared_operation_conflict",
    )


def apply_one_to_one_matching(
    rows: Iterable[dict[str, Any]], threshold: float = PROVISIONAL_THRESHOLD
) -> list[dict[str, Any]]:
    """Filter candidates and select a maximum-weight assignment within each case."""
    evaluated: list[dict[str, Any]] = []
    for source in rows:
        row = dict(source)
        score = float(row["cosine_similarity"])
        compatibility = operation_compatibility(
            row["reference_normalized"], row["generated_normalized"]
        )
        row.update(
            {
                "threshold_prediction": score >= threshold,
                "reference_operation": (
                    compatibility.reference_operation.token
                    if compatibility.reference_operation
                    else ""
                ),
                "reference_operation_family": (
                    compatibility.reference_operation.family
                    if compatibility.reference_operation
                    else ""
                ),
                "generated_operation": (
                    compatibility.generated_operation.token
                    if compatibility.generated_operation
                    else ""
                ),
                "generated_operation_family": (
                    compatibility.generated_operation.family
                    if compatibility.generated_operation
                    else ""
                ),
                "operation_compatible": compatibility.compatible,
                "compatibility_reason": compatibility.reason,
                "candidate_after_compatibility": (
                    score >= threshold and compatibility.compatible
                ),
                "selected_by_assignment": False,
            }
        )
        evaluated.append(row)

    for case_id in sorted({str(row["case_id"]) for row in evaluated}):
        candidates = [
            row
            for row in evaluated
            if str(row["case_id"]) == case_id
            and row["candidate_after_compatibility"]
        ]
        if not candidates:
            continue

        reference_ids = sorted({str(row["reference_id"]) for row in candidates})
        generated_ids = sorted({str(row["generated_id"]) for row in candidates})
        reference_index = {node_id: index for index, node_id in enumerate(reference_ids)}
        generated_index = {node_id: index for index, node_id in enumerate(generated_ids)}
        weights = np.zeros((len(reference_ids), len(generated_ids)), dtype=np.float64)
        pair_by_position: dict[tuple[int, int], dict[str, Any]] = {}

        for row in sorted(candidates, key=lambda item: str(item["pair_id"])):
            position = (
                reference_index[str(row["reference_id"])],
                generated_index[str(row["generated_id"])],
            )
            score = float(row["cosine_similarity"])
            if score > weights[position]:
                weights[position] = score
                pair_by_position[position] = row

        assigned_references, assigned_generated = linear_sum_assignment(
            weights, maximize=True
        )
        for reference_position, generated_position in zip(
            assigned_references, assigned_generated
        ):
            row = pair_by_position.get((reference_position, generated_position))
            if row is not None and weights[reference_position, generated_position] > 0:
                row["selected_by_assignment"] = True

    for row in evaluated:
        row["final_prediction"] = bool(row["selected_by_assignment"])
        if row["threshold_prediction"] and not row["operation_compatible"]:
            row["decision_change_source"] = "operation_compatibility"
        elif row["candidate_after_compatibility"] and not row["selected_by_assignment"]:
            row["decision_change_source"] = "one_to_one_assignment"
        else:
            row["decision_change_source"] = ""
    return evaluated


def prediction_metrics(
    rows: Iterable[dict[str, Any]], prediction_field: str
) -> dict[str, float | int]:
    tp = fp = fn = tn = 0
    for row in rows:
        predicted = bool(row[prediction_field])
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
