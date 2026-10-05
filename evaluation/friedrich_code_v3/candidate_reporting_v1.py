"""Versioned nullable candidate reporting; fact scoring is unchanged."""

from __future__ import annotations

from typing import Any


VERSION = "friedrich-code-candidate-reporting/1"
DIMENSIONS = ("Action", "Flow", "Control Node", "Control Relation")


def project_candidate_output(row: dict[str, Any]) -> dict[str, Any]:
    """Project true Control Relation N/A as null and apply the Overall mask."""
    relation = row["Control Relation"]
    counts = relation["counts"]
    true_na = (counts["required_denominator"] == 0
               and counts["indeterminate_alignment_count"] == 0
               and all(counts[name] == 0 for name in ("tp", "fp", "fn")))
    if true_na:
        counts.update(status="N/A", precision=None, recall=None, f1=None)
    elif counts["indeterminate_alignment_count"]:
        counts.update(status="indeterminate", precision=None, recall=None, f1=None)
    else:
        counts["status"] = "scored"
    relation["status"] = counts["status"]
    relation["score"] = counts["f1"]
    applicable = tuple(dim for dim in DIMENSIONS
                       if dim != "Control Relation" or not true_na)
    values = [row[dim]["f1"] if dim == "Action" else row[dim]["counts"]["f1"]
              for dim in applicable]
    row["Candidate Overall"] = {
        "status": "indeterminate" if any(value is None for value in values) else "scored",
        "score": None if any(value is None for value in values)
                 else sum(values) / len(values),
        "applicable_dimensions": list(applicable),
        "na_dimensions": [dim for dim in DIMENSIONS if dim not in applicable],
    }
    row["reporting_version"] = VERSION
    return row
