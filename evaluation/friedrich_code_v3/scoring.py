"""Fixed-denominator V3.1 component reporting."""

from __future__ import annotations

from typing import Any

from evaluation.friedrich_v3.core import Counts


def component_summary(counts: Counts, required: int, indeterminate: int) -> dict[str, Any]:
    if counts.tp + counts.fn + indeterminate != required:
        raise ValueError("V3.1 required denominator changed during candidate scoring")
    result: dict[str, Any] = counts.to_dict()
    result["required_denominator"] = required
    result["indeterminate_alignment_count"] = indeterminate
    result["determinate_coverage"] = ((counts.tp + counts.fn) / required) if required else 1.0
    result["recall_interval"] = [
        counts.tp / required if required else 1.0,
        (counts.tp + indeterminate) / required if required else 1.0,
    ]
    if indeterminate:
        result.update(precision=None, recall=None, f1=None)
    return result
