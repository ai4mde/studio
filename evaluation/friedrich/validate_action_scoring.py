from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .action_scoring import (
    GranularityMismatch,
    aggregate_action_scores,
    score_action_case,
)
from .adapters import activity_graph_to_eval_graph, friedrich_reference_to_eval_graph
from .prototype import _extract_activity_graph


REVIEWED_CASE_SOURCES = {
    "10-6": "development/revised_validation/revised_candidate_matrix.csv",
    "8-1": "untouched_validation/untouched_candidate_matrix.csv",
    "1-1": "untouched_validation/untouched_candidate_matrix.csv",
    "2-1": "final_untouched_validation/untouched_candidate_matrix.csv",
    "3-8": "untouched_validation/untouched_candidate_matrix.csv",
}

REVIEWED_GRANULARITY = {
    "3-8": (
        GranularityMismatch(
            reference_ids=("456", "457"),
            generated_ids=("n2",),
            direction="many_reference_to_one_generated",
        ),
    )
}


def _read_candidate_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
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

    candidate_cache = {
        relative: _read_candidate_rows(base / relative)
        for relative in sorted(set(REVIEWED_CASE_SOURCES.values()))
    }
    case_scores = []
    for case_id, relative in REVIEWED_CASE_SOURCES.items():
        item = catalog[case_id]
        reference_graph = friedrich_reference_to_eval_graph(item["reference_model_path"])
        artifact_path = Path(item["generated_artifact_output_path"]) / "run_1.json"
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        generated_graph = activity_graph_to_eval_graph(_extract_activity_graph(artifact))
        score = score_action_case(
            case_id,
            reference_graph,
            generated_graph,
            candidate_cache[relative],
            granularity_mismatches=REVIEWED_GRANULARITY.get(case_id, ()),
        )
        case_scores.append(score)

    report = {
        "scope": {
            "purpose": "scorer accounting validation over frozen matcher decisions",
            "reviewed_cases": list(REVIEWED_CASE_SOURCES),
            "formal_full_47_case_evaluation": False,
        },
        "cases": [score.to_dict() for score in case_scores],
        "aggregate": aggregate_action_scores(case_scores).to_dict(),
        "accounting_invariants": {
            score.case_id: {
                "TP_plus_FN_equals_reference_actions": (
                    score.TP + score.FN == score.reference_action_count
                ),
                "TP_plus_FP_equals_generated_actions": (
                    score.TP + score.FP == score.generated_action_count
                ),
            }
            for score in case_scores
        },
    }
    output_path = base / "action_scorer_validation.json"
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
