#!/usr/bin/env python3
"""Continuous calibration analysis; imported only after all AI slots are saved."""

from __future__ import annotations

import csv
import json
from decimal import Decimal, localcontext
from html import escape
from pathlib import Path
from typing import Any


COLUMNS = ("case_id", "candidate_id", "human_label", "ai_score", "signed_difference", "absolute_error")
HUMAN_LEVELS = frozenset(Decimal(x) for x in ("0", "0.25", "0.50", "0.75", "1"))


def load_human_labels(path: Path, expected_pairs: tuple[tuple[str, str], ...]) -> dict[tuple[str, str], Decimal]:
    """Called by compare only, after its completion gate succeeds."""
    expected = set(expected_pairs)
    labels: dict[tuple[str, str], Decimal] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for source in csv.DictReader(handle, delimiter=";"):
            pair = (source["Case"], source["Candidate"])
            if pair not in expected:
                continue
            if pair in labels:
                raise ValueError(f"Duplicate human calibration label: {pair}")
            value = Decimal(source["Human Score"])
            if value not in HUMAN_LEVELS:
                raise ValueError(f"Human label is not a recorded ordinal anchor: {pair}")
            labels[pair] = value
    if set(labels) != expected:
        raise ValueError(f"Human label roster mismatch: {sorted(expected - set(labels))}")
    return labels


def average_ranks(values: list[Decimal]) -> list[Decimal]:
    """Ascending one-based ranks; all tied values receive their average rank."""
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [Decimal(0)] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = Decimal(start + 1 + end) / 2
        for position in range(start, end):
            ranks[order[position]] = rank
        start = end
    return ranks


def spearman_tie_aware(human: list[Decimal], ai: list[Decimal]) -> Decimal | None:
    if len(human) != len(ai) or not human:
        raise ValueError("Rank vectors must have the same nonzero length")
    left, right = average_ranks(human), average_ranks(ai)
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    centered_left = [value - mean_left for value in left]
    centered_right = [value - mean_right for value in right]
    variance_left = sum(value * value for value in centered_left)
    variance_right = sum(value * value for value in centered_right)
    if variance_left == 0 or variance_right == 0:
        return None
    covariance = sum(a * b for a, b in zip(centered_left, centered_right))
    return covariance / (variance_left * variance_right).sqrt()


def calculate(
    expected_pairs: tuple[tuple[str, str], ...],
    ai_scores: dict[tuple[str, str], Decimal],
    human_labels: dict[tuple[str, str], Decimal],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # Decimal's default 28 digits must not truncate a longer JSON score during
    # subtraction or aggregation. Allow room for the anchor, 18-row sum, and rho.
    scale = max((max(0, -value.as_tuple().exponent) for value in ai_scores.values()), default=0)
    with localcontext() as context:
        context.prec = max(50, scale + 40)
        return _calculate_at_full_precision(expected_pairs, ai_scores, human_labels)


def _calculate_at_full_precision(
    expected_pairs: tuple[tuple[str, str], ...],
    ai_scores: dict[tuple[str, str], Decimal],
    human_labels: dict[tuple[str, str], Decimal],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if len(set(expected_pairs)) != len(expected_pairs) or set(ai_scores) != set(expected_pairs) or set(human_labels) != set(expected_pairs):
        raise ValueError("AI, human, or expected candidate roster differs")
    rows: list[dict[str, Any]] = []
    for case_id, candidate_id in expected_pairs:
        pair = (case_id, candidate_id)
        ai, human = ai_scores[pair], human_labels[pair]
        if not ai.is_finite() or ai < 0 or ai > 1 or human not in HUMAN_LEVELS:
            raise ValueError(f"Invalid continuous AI score or human anchor: {pair}")
        difference = ai - human
        rows.append({
            "case_id": case_id,
            "candidate_id": candidate_id,
            "human_label": human,
            "ai_score": ai,
            "signed_difference": difference,
            "absolute_error": abs(difference),
        })
    errors = sorted(row["absolute_error"] for row in rows)
    n = len(rows)
    median = errors[n // 2] if n % 2 else (errors[n // 2 - 1] + errors[n // 2]) / 2
    maximum = errors[-1]
    rank = spearman_tie_aware([row["human_label"] for row in rows], [row["ai_score"] for row in rows])
    metrics = {
        "candidate_count": n,
        "mean_absolute_error": sum(errors) / n,
        "median_absolute_error": median,
        "maximum_absolute_error": maximum,
        "maximum_error_candidates": [
            {"case_id": row["case_id"], "candidate_id": row["candidate_id"]}
            for row in rows if row["absolute_error"] == maximum
        ],
        "spearman_tie_aware": rank,
        "spearman_undefined": rank is None,
        "acceptance_threshold": None,
    }
    return rows, metrics


def review_order(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frozen_position = {(row["case_id"], row["candidate_id"]): index for index, row in enumerate(rows)}
    return sorted(rows, key=lambda row: (-row["absolute_error"], frozen_position[(row["case_id"], row["candidate_id"])]))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: str(row[field]) for field in COLUMNS})


def write_scatter_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    """Generate a standalone descriptive plot only from future completed pairs."""
    width, height = 640, 640
    left, top, span = 80, 45, 500
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Human label versus continuous AI score">',
        '<rect width="640" height="640" fill="white"/>',
        '<text x="320" y="25" text-anchor="middle" font-family="sans-serif" font-size="18">Continuous calibration scatter</text>',
        f'<line x1="{left}" y1="{top + span}" x2="{left + span}" y2="{top + span}" stroke="#333"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + span}" stroke="#333"/>',
    ]
    for tick in (Decimal("0"), Decimal("0.25"), Decimal("0.5"), Decimal("0.75"), Decimal("1")):
        x = left + float(tick) * span
        y = top + (1 - float(tick)) * span
        parts += [
            f'<line x1="{x:.1f}" y1="{top + span}" x2="{x:.1f}" y2="{top + span + 6}" stroke="#333"/>',
            f'<text x="{x:.1f}" y="{top + span + 24}" text-anchor="middle" font-family="sans-serif" font-size="12">{tick}</text>',
            f'<line x1="{left - 6}" y1="{y:.1f}" x2="{left}" y2="{y:.1f}" stroke="#333"/>',
            f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="12">{tick}</text>',
        ]
    parts += [
        '<text x="330" y="625" text-anchor="middle" font-family="sans-serif" font-size="14">Human label</text>',
        '<text x="19" y="295" text-anchor="middle" transform="rotate(-90 19 295)" font-family="sans-serif" font-size="14">AI score</text>',
    ]
    for row in rows:
        x = left + float(row["human_label"]) * span
        y = top + (1 - float(row["ai_score"])) * span
        title = escape(f"{row['case_id']}/{row['candidate_id']}: human {row['human_label']}, AI {row['ai_score']}")
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5" fill="#2563eb" fill-opacity="0.55" stroke="#1e40af"><title>{title}</title></circle>')
    parts.append("</svg>")
    with path.open("x", encoding="utf-8") as handle:
        handle.write("\n".join(parts) + "\n")


def write_report(path: Path, rows: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    rho = "undefined/NA" if metrics["spearman_tie_aware"] is None else f'{metrics["spearman_tie_aware"]:.4f}'
    lines = [
        "# AI Evaluator v1.6 continuous developmental calibration", "",
        "The 18 human labels are fixed ordinal anchors; AI scores remain continuous and unrounded in calculations.",
        "This calibration set was used in evaluator development and is not independent final validation.", "",
        f'- MAE: **{metrics["mean_absolute_error"]:.4f}** (numeric distance to human anchors).',
        f'- Median absolute error: **{metrics["median_absolute_error"]:.4f}**.',
        f'- Maximum absolute error: **{metrics["maximum_absolute_error"]:.4f}**.',
        f'- Tie-aware Spearman rank correlation: **{rho}** (descriptive ordering only).',
        "- No acceptance threshold was applied; no AI scores were quantized to human categories.", "",
        "## Candidate review order", "",
        "Sorted by absolute error descending; ties retain frozen roster order. Candidate values are shown at stored precision; aggregate figures above are display-rounded only.", "",
        "| Case | Candidate | Human | AI | Signed difference | Absolute error |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in review_order(rows):
        lines.append(
            f'| {row["case_id"]} | {row["candidate_id"]} | {row["human_label"]} | '
            f'{row["ai_score"]} | {row["signed_difference"]} | {row["absolute_error"]} |'
        )
    lines += [
        "", "Inspect leading disagreements for semantic-defect alignment, severity judgment, source ambiguity, explanation/score coherence, and possible run-to-run variation. This review is diagnostic only.",
        "", "The scatter plot uses human labels on the x-axis and continuous AI scores on the y-axis, with one point per candidate.", "",
    ]
    with path.open("x", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def metrics_json_ready(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: (str(value) if isinstance(value, Decimal) else value) for key, value in metrics.items()}
