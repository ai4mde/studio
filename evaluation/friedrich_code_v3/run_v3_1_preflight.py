"""Approved 18-candidate V3.1 amendment preflight; never runs the formal cohort."""

from __future__ import annotations

import json
import argparse
from pathlib import Path

from evaluation.friedrich_v3.action import (
    ACTION_MODEL_NAME, ACTION_MODEL_REVISION, SentenceTransformerSimilarity,
)
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory
from evaluation.friedrich_semantic_v2.evaluator_adapter import project_reviewed_inventory

from .evaluator import evaluate_candidate_file_v3
from .flow_inventory_store import load_fixed_flow_inventory
from .inventory import load_frozen_corpus


STUDIO_ROOT = Path(__file__).resolve().parents[2]
COHORT_ROOT = STUDIO_ROOT / "evaluation/friedrich_v2/cohorts/final_frozen_40x3_20260910/cases"
MODEL_CACHE = STUDIO_ROOT.parent / "studio-friedrich-scoring/.hf-cache"
OUTPUT_ROOT = Path(__file__).resolve().parent / "results/v3_1_preflight_18_amended_20260924"
PREFLIGHT_CASES = ("2-2", "4-1", "6-3", "9-1", "9-6", "10-8")
PREFLIGHT_ROSTER = tuple(
    (case_id, f"candidate_{index}")
    for case_id in PREFLIGHT_CASES for index in (1, 2, 3)
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    corpus = load_frozen_corpus()
    similarity = SentenceTransformerSimilarity(
        ACTION_MODEL_NAME, ACTION_MODEL_REVISION, str(MODEL_CACHE),
    )
    results = []
    assert len(PREFLIGHT_ROSTER) == 18
    for case_id, candidate_id in PREFLIGHT_ROSTER:
        path = COHORT_ROOT / case_id / candidate_id / "activity_graph.json"
        result = evaluate_candidate_file_v3(
            case_id, candidate_id, path, similarity, corpus=corpus,
        )
        case = corpus.load_case(case_id)
        questions = case.control["unresolved_facts"]
        if result["candidate_status"] == "EVALUATED":
            assert result["source_unresolved_questions"] == questions
            reviewed = SemanticInventory.from_dict(case.reviewed_action)
            projection = project_reviewed_inventory(reviewed, case.reference_evidence)
            assert result["Action"]["tp"] + result["Action"]["fn"] == len(projection.action_units)
            ambiguous_source = {unit.semantic_unit_id for unit in reviewed.units
                                if unit.provenance.review_state == "ambiguous"}
            assert not ambiguous_source & set(result["Control Anchor Evidence"]["control_only_unit_to_generated"])
            expected_nodes = sum(f["status"] == "required" for f in case.control["control_nodes"])
            expected_relations = sum(f["status"] == "required" for f in case.control["control_relations"])
            expected_flow = len(load_fixed_flow_inventory(case_id, corpus).required_precedence)
            for component, expected in (
                ("Control Node", expected_nodes),
                ("Control Relation", expected_relations),
                ("Flow", expected_flow),
            ):
                assert result[component]["counts"]["required_denominator"] == expected
                assert result[component]["counts"]["tp"] + result[component]["counts"]["fn"] + result[component]["counts"]["indeterminate_alignment_count"] == expected
        else:
            assert result["source_unresolved_questions"] == questions
        results.append(result)
    args.output_root.mkdir(parents=True, exist_ok=True)
    output = {
        "preflight_version": "v3.1-approved-amended-cases-three-candidates-each",
        "frozen_corpus_sha256": corpus.corpus_sha256,
        "roster": [{"case_id": case_id, "candidate_id": candidate_id}
                   for case_id, candidate_id in PREFLIGHT_ROSTER],
        "formal_120_candidate_evaluation_run": False,
        "results": results,
    }
    (args.output_root / "results.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "output": str(args.output_root / "results.json"),
        "candidate_statuses": [r["candidate_status"] for r in results],
        "component_counts": [{
            "case_id": r["case_id"],
            **({component: r[component]["counts"] for component in
                ("Flow", "Control Node", "Control Relation")}
               if r["candidate_status"] == "EVALUATED" else {}),
        } for r in results],
    }, indent=2))


if __name__ == "__main__":
    main()
