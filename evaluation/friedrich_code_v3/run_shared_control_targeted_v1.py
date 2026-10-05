"""Gate explicit shared Control roles against frozen graphs and saved Action evidence."""

from __future__ import annotations

from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import evaluation

evaluation.__path__.append(str(Path(__file__).resolve().parents[3]
                               / "studio-semantic-v2/evaluation"))

from evaluation.friedrich_v3.adapters import load_generated_graph
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory

from .alignment import ActionAlignmentTable, AlignmentEntry
from .anchor_evidence import ControlAnchorEvidence
from .control import normalize_generated_control
from .control_node_role_assignment_v4 import match_control_nodes_role_assignment_v4
from .control_node_shared_roles_v5 import match_control_nodes_shared_roles_v5
from .control_relation_local_evidence_v3 import score_control_relations_local_evidence_v3
from .control_relation_shared_owner_v4 import score_control_relations_shared_owner_v4
from .inventory import load_frozen_corpus
from .reference import reference_action_nodes, reference_graph
from .run_combined_validation_v2 import ROOT, _identity, _sha
from .v3_2 import combine_control_nodes, score_structural_endpoints


REVIEW = ROOT / "shared_control_targeted_regression_set_v1.csv"
SAVED = (ROOT / "results" / "full_construct_validation_v3_20261002_193850_915791utc")


def _saved_alignment(row: dict) -> ControlAnchorEvidence:
    saved = row["Action Alignment Table"]
    entries = tuple(AlignmentEntry(
        item["mapping_id"], item["kind"], tuple(item["unit_ids"]),
        tuple(item["reference_ids"]), tuple(item["generated_ids"]),
        item["evidence"], tuple(item["review_triggers"]),
    ) for item in saved["entries"])
    by_unit: dict[str, set[str]] = {}
    by_generated: dict[str, set[str]] = {}
    for item in entries:
        for unit in item.unit_ids:
            by_unit.setdefault(unit, set()).update(item.generated_ids)
        for node in item.generated_ids:
            by_generated.setdefault(node, set()).update(item.unit_ids)
    action = ActionAlignmentTable(
        entries, {unit: frozenset(ids) for unit, ids in by_unit.items()},
        {node: frozenset(units) for node, units in by_generated.items()},
        frozenset(saved["ambiguous_unit_ids"]),
        {unit: tuple(ids) for unit, ids in saved["ambiguous_candidate_ids"].items()},
    )
    saved_control = row["Control Anchor Evidence"]
    return ControlAnchorEvidence(
        action,
        {unit: frozenset(ids) for unit, ids in saved_control["control_only_unit_to_generated"].items()},
        {occ: frozenset(ids) for occ, ids in saved_control["occurrence_to_generated"].items()},
        frozenset(saved_control["indeterminate_unit_ids"]),
        frozenset(saved_control["indeterminate_occurrence_ids"]),
        saved_control["occurrence_evidence"],
    )


def run() -> Path:
    manifest = json.loads((SAVED / "validation_manifest.json").read_text())
    if _sha(SAVED / "candidate_results.jsonl") != manifest["output_hashes"]["candidate_results.jsonl"]:
        raise ValueError("saved Action/Control evidence changed")
    roster, _frozen, identity = _identity()
    slots = {(row["case_id"], row["candidate_id"]): row for row in roster}
    if len(slots) != 120 or identity["cohort"]["roster_sha256"] != manifest["frozen_roster_sha256"]:
        raise ValueError("frozen roster differs from reviewed validation")
    saved = {(row["case_id"], row["candidate_id"]): row for row in
             map(json.loads, (SAVED / "candidate_results.jsonl").open())}
    checks = list(csv.DictReader(REVIEW.open()))
    if len(checks) < 50 or len(saved) != 120:
        raise ValueError("review gate or saved output count differs")
    corpus = load_frozen_corpus()
    evaluated: dict[tuple[str, str], dict] = {}
    unintended_changes: list[dict] = []
    for key in sorted({(row["case_id"], row["candidate_id"]) for row in checks}):
        slot = slots[key]
        path = Path(slot["activity_graph_path"])
        if _sha(path) != slot["activity_graph_sha256"]:
            raise ValueError(f"graph hash mismatch: {key}")
        graph = load_generated_graph(path)
        normalized = normalize_generated_control(graph)
        case = corpus.load_case(key[0])
        reviewed = SemanticInventory.from_dict(case.reviewed_action)
        alignment = _saved_alignment(saved[key])
        if alignment.action.to_dict() != saved[key]["Action Alignment Table"]:
            raise ValueError(f"Action evidence reconstruction mismatch: {key}")
        if alignment.to_dict() != saved[key]["Control Anchor Evidence"]:
            raise ValueError(f"Control-only anchor reconstruction mismatch: {key}")
        reference = reference_graph(case.reference_evidence)
        baseline_node, baseline_owners = match_control_nodes_role_assignment_v4(
            case.control, normalized, alignment,
            reference=reference,
            reference_unit_nodes=reference_action_nodes(reviewed, reference),
            reference_evidence=case.reference_evidence,
        )
        baseline_relation = score_control_relations_local_evidence_v3(
            case.control, normalized, alignment, baseline_owners, case.reference_evidence,
            reviewed, owner_alternatives=baseline_node.assignment_alternatives,
        )
        node_source, owners = match_control_nodes_shared_roles_v5(
            case.control, normalized, alignment,
            reference=reference,
            reference_unit_nodes=reference_action_nodes(reviewed, reference),
            reference_evidence=case.reference_evidence,
        )
        relation = score_control_relations_shared_owner_v4(
            case.control, normalized, alignment, owners, case.reference_evidence,
            reviewed, owner_alternatives=node_source.assignment_alternatives,
        )
        node = combine_control_nodes(node_source, score_structural_endpoints(key[0], graph))
        # Outside the explicitly reviewed two candidates, no prior node or
        # relation fact may change status or owner in this targeted set.
        if key not in {("9-5", "candidate_2"), ("9-5", "candidate_3")}:
            for dimension, before, after in (
                ("Control Node", baseline_node, node_source),
                ("Control Relation", baseline_relation, relation),
            ):
                previous = {fact.fact_id: fact for fact in before.facts}
                for fact in after.facts:
                    old = previous[fact.fact_id]
                    if (old.status, old.generated_node_id) != (fact.status, fact.generated_node_id):
                        unintended_changes.append({"case_id": key[0], "candidate_id": key[1],
                            "dimension": dimension, "fact_id": fact.fact_id,
                            "before": [old.status, old.generated_node_id],
                            "after": [fact.status, fact.generated_node_id]})
        shared = {}
        for fact_id, node_id in owners.items():
            if node_id and node_id not in {"implicit", "indeterminate"}:
                shared.setdefault(node_id, []).append(fact_id)
        shared = {node_id: fact_ids for node_id, fact_ids in shared.items()
                  if len(fact_ids) > 1}
        if shared and key not in {("9-5", "candidate_2"), ("9-5", "candidate_3")}:
            unintended_changes.append({"case_id": key[0], "candidate_id": key[1],
                                        "unexpected_shared_owners": shared})
        evaluated[key] = {"case_id": key[0], "candidate_id": key[1],
                          "graph_sha256": slot["activity_graph_sha256"],
                          "Control Node": node.to_dict(),
                          "Control Relation": relation.to_dict(),
                          "owners": dict(owners)}
    outcomes = []
    for check in checks:
        key = check["case_id"], check["candidate_id"]
        fact = next(item for item in evaluated[key][check["dimension"]]["facts"]
                    if item["fact_id"] == check["fact_id"])
        status = fact["status"]
        passed = status == check["expected_after_patch"]
        outcomes.append({**check, "actual_status": status,
                         "actual_node_id": fact.get("generated_node_id"),
                         "actual_reason": fact.get("reason"), "passed": passed})
    role_expected = {
        ("2-2", "candidate_1", "CF-2-2-N05"): "n22",
        ("5-4", "candidate_1", "CF-5-4-N01"): "n7",
        ("5-4", "candidate_1", "CF-5-4-N02"): "n8",
        ("5-4", "candidate_1", "CF-5-4-N04"): "n17",
        ("5-4", "candidate_1", "CF-5-4-R02"): "n7",
    }
    for (case_id, candidate_id, fact_id), expected in role_expected.items():
        row = next(item for item in outcomes if item["case_id"] == case_id
                   and item["candidate_id"] == candidate_id and item["fact_id"] == fact_id)
        row["expected_node_id"] = expected
        row["passed"] = row["passed"] and row["actual_node_id"] == expected
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%futc")
    output = ROOT / "results" / f"shared_control_targeted_v1_{now}"
    output.mkdir(exist_ok=False)
    with (output / "targeted_fact_results.jsonl").open("w") as stream:
        for row in outcomes:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {"status": "PASS" if all(row["passed"] for row in outcomes) and not unintended_changes else "FAIL",
               "fact_checks": len(outcomes), "passed": sum(row["passed"] for row in outcomes),
               "failed": sum(not row["passed"] for row in outcomes),
               "by_role": {role: {"total": sum(row["role"] == role for row in outcomes),
                                  "passed": sum(row["role"] == role and row["passed"] for row in outcomes)}
                           for role in sorted({row["role"] for row in outcomes})},
               "failures": [row for row in outcomes if not row["passed"]],
               "unintended_changes": unintended_changes,
               "candidate_count": len(evaluated), "api_calls": 0,
               "review_gate_sha256": _sha(REVIEW),
               "saved_input_sha256": _sha(SAVED / "candidate_results.jsonl"),
               "frozen_roster_sha256": identity["cohort"]["roster_sha256"]}
    (output / "targeted_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (output / "candidate_control_results.jsonl").open("w") as stream:
        for key in sorted(evaluated):
            stream.write(json.dumps(evaluated[key], ensure_ascii=False) + "\n")
    return output


if __name__ == "__main__":
    print(run())
