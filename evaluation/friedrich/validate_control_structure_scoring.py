from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from .action_scoring import GranularityMismatch, score_action_case
from .adapters import activity_graph_to_eval_graph, friedrich_reference_to_eval_graph
from .control_structure_scoring import (
    KNOWN_UNSUPPORTED_REFERENCE_CASES,
    aggregate_control_structure_scores,
    score_control_structure_case,
)
from .prototype import _extract_activity_graph


REVIEWED_CASE_SOURCES = {
    "3-8": "untouched_validation/untouched_candidate_matrix.csv",
    "9-6": "action_matching_pilot_pairs.csv",
    "4-1": "action_matching_pilot_pairs.csv",
    "1-1": "untouched_validation/untouched_candidate_matrix.csv",
    "6-1": "final_untouched_validation/untouched_candidate_matrix.csv",
    "2-2": "untouched_validation/untouched_candidate_matrix.csv",
}

REVIEWED_GRANULARITY = {
    "3-8": (
        GranularityMismatch(
            reference_ids=("456", "457"),
            generated_ids=("n2",),
            direction="many_reference_to_one_generated",
        ),
    ),
    "4-1": (
        GranularityMismatch(
            reference_ids=("2120552757", "2120552767"),
            generated_ids=("n15",),
            direction="many_reference_to_one_generated",
        ),
    ),
}

CASE_LIMITATIONS = {
    "9-6": (
        "Uses only the frozen manually reviewed pilot correspondences; this is not "
        "a complete candidate matrix."
    ),
    "4-1": (
        "Uses only the frozen manually reviewed pilot correspondences; low structure "
        "coverage is expected and is retained as validation evidence."
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows: list[dict[str, Any]] = list(csv.DictReader(handle))
    if path.name == "action_matching_pilot_pairs.csv":
        for row in rows:
            row["final_prediction"] = row.get("binary_match") == "yes"
        return rows
    for row in rows:
        for field in (
            "unresolved_reference_nodes",
            "unresolved_generated_nodes",
            "unresolved_candidate_pairs",
        ):
            row[field] = json.loads(row[field]) if row.get(field) else []
    return rows


def main() -> None:
    base = Path(__file__).resolve().parent
    catalog_path = Path(
        "/Users/queenie/Desktop/evaluation-data/friedrich_47_case_catalog.csv"
    )
    with catalog_path.open(encoding="utf-8", newline="") as handle:
        catalog = {row["case_id"]: row for row in csv.DictReader(handle)}

    correspondence_cache = {
        relative: _read_rows(base / relative)
        for relative in sorted(set(REVIEWED_CASE_SOURCES.values()))
    }
    case_scores = []
    case_evidence = {}
    for case_id, relative in REVIEWED_CASE_SOURCES.items():
        item = catalog[case_id]
        reference_path = Path(item["reference_model_path"])
        generated_path = Path(item["generated_artifact_output_path"]) / "run_1.json"
        reference_graph = friedrich_reference_to_eval_graph(reference_path)
        artifact = json.loads(generated_path.read_text(encoding="utf-8"))
        generated_graph = activity_graph_to_eval_graph(_extract_activity_graph(artifact))
        action_score = score_action_case(
            case_id,
            reference_graph,
            generated_graph,
            correspondence_cache[relative],
            granularity_mismatches=REVIEWED_GRANULARITY.get(case_id, ()),
        )
        score = score_control_structure_case(
            case_id, reference_graph, generated_graph, action_score
        )
        case_scores.append(score)
        case_evidence[case_id] = {
            "correspondence_source": relative,
            "correspondence_source_sha256": _sha256(base / relative),
            "reference_model_sha256": _sha256(reference_path),
            "generated_artifact_sha256": _sha256(generated_path),
            "frozen_action_TP": action_score.TP,
            "frozen_action_FP": action_score.FP,
            "frozen_action_FN": action_score.FN,
            "limitation_note": CASE_LIMITATIONS.get(case_id),
        }

    aggregate = aggregate_control_structure_scores(case_scores)
    report = {
        "scope": {
            "purpose": "Control-structure scorer validation over frozen Action evidence",
            "representation_name": "Control Structure Summary",
            "reviewed_cases": list(REVIEWED_CASE_SOURCES),
            "formal_full_47_case_evaluation": False,
            "matcher_or_scorer_tuning": False,
        },
        "evidence": case_evidence,
        "cases": [score.to_dict() for score in case_scores],
        "aggregate": aggregate.to_dict(),
        "accounting_invariants": {
            score.case_id: {
                "TP_plus_FN_equals_scorable_reference_structures": (
                    score.TP + score.FN
                    == score.scorable_reference_structure_count
                ),
                "TP_plus_FP_equals_scorable_generated_structures": (
                    score.TP + score.FP
                    == score.scorable_generated_structure_count
                ),
                "reference_total_is_scorable_plus_unscorable": (
                    score.reference_structure_count
                    == score.scorable_reference_structure_count
                    + score.unscorable_reference_structure_count
                ),
                "generated_total_is_scorable_plus_unscorable": (
                    score.generated_structure_count
                    == score.scorable_generated_structure_count
                    + score.unscorable_generated_structure_count
                ),
            }
            for score in case_scores
        },
        "known_scope_limitations": [
            "Only exclusive splits, parallel regions, and controlled loops are primary types.",
            "Exclusive merges are transparent diagnostics rather than primary structures.",
            "Guard labels and event-trigger semantics are outside primary identity.",
            "Subprocess flattening may hide hierarchy; message flows and data associations are excluded.",
            "This six-case report validates scorer behavior and is not a formal system result.",
        ],
        "known_unsupported_reference_cases": dict(
            KNOWN_UNSUPPORTED_REFERENCE_CASES
        ),
    }
    output_path = base / "control_structure_scorer_validation.json"
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
