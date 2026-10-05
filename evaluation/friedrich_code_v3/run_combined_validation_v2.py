"""Offline targeted validation of the opt-in Code construct candidate.

Never invokes the frozen formal runner or modifies frozen results. The pinned
Action embedding model is loaded from its local snapshot only.
"""

from __future__ import annotations

from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from evaluation.friedrich_v3.action import (
    ACTION_MODEL_NAME, ACTION_MODEL_REVISION, SentenceTransformerSimilarity,
)
from evaluation.friedrich_v3.adapters import load_generated_graph

from .action_operation_guard_v3 import semantic_operation_decision
from .combined_candidate_v2 import FLOW_SNAPSHOT, VERSION, evaluate_combined_candidate_v2
from .inventory import load_frozen_corpus
from .run_v3_1_formal import MODEL_CACHE


ROOT = Path(__file__).resolve().parent
FROZEN_RUN = ROOT / "results/v3_2_formal_120_20260930_225036utc"
ACTION_AUDIT = ROOT / "results/action_operation_guard_v2_impact_20261002_151626utc/action_only_impact_audit.json"
PRIOR_COMBINED = ROOT / "results/combined_construct_validation_v1_20261002_171424_254958utc"
CASES_ALL_THREE = ("5-2", "6-4", "6-3", "8-2", "9-1", "10-11", "10-14")
CASES_ONE = ("3-1", "10-5", "3-2", "1-1")
SELECTED = {(case, f"candidate_{i}") for case in CASES_ALL_THREE for i in (1, 2, 3)} | {
    (case, "candidate_1") for case in CASES_ONE
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _identity() -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]], dict[str, Any]]:
    identity = json.loads((FROZEN_RUN / "run_identity_before.json").read_text())
    failures = [path for path, digest in identity["pre_run_file_hashes"].items()
                if not Path(path).is_file() or _sha(Path(path)) != digest]
    output = json.loads((FROZEN_RUN / "output_manifest.json").read_text())["output_hashes"]
    failures += [str(FROZEN_RUN / path) for path, digest in output.items()
                 if _sha(FROZEN_RUN / path) != digest]
    if failures:
        raise ValueError(f"frozen baseline hash mismatch: {failures[:3]}")
    with (FROZEN_RUN / "candidate_results.jsonl").open() as stream:
        baseline = {(row["case_id"], row["candidate_id"]): row for row in
                    map(json.loads, stream)}
    if len(baseline) != 120 or len(identity["roster"]) != 120:
        raise ValueError("frozen baseline is not 120 unique candidates")
    return identity["roster"], baseline, identity


def _facts(value: dict[str, Any], dimension: str) -> list[dict[str, Any]]:
    if dimension == "Control Node":
        return value["Control Node"]["facts"]
    return value[dimension]["facts"]


def _key(fact: dict[str, Any], dimension: str) -> str:
    if dimension == "Flow":
        return f"{fact['source_unit_id']}->{fact['target_unit_id']}"
    return fact["fact_id"]


def run() -> Path:
    roster, frozen, identity = _identity()
    corpus = load_frozen_corpus()
    correction_manifest = json.loads((FLOW_SNAPSHOT / "manifest.json").read_text())
    if (correction_manifest["snapshot_version"] != "v3_2_alignment_flow_facts_1"
        or len(correction_manifest["reviewed_fact_amendments"]) != 2):
        raise ValueError("unexpected corrected Flow snapshot")
    action_audit = json.loads(ACTION_AUDIT.read_text())
    if (action_audit["roster_sha256"] != identity["cohort"]["roster_sha256"]
        or action_audit["frozen_action_result_sha256"] != _sha(FROZEN_RUN / "candidate_results.jsonl")):
        raise ValueError("Action guard v2 audit does not match frozen baseline")
    with (PRIOR_COMBINED / "combined_candidate_results.jsonl").open() as stream:
        prior_combined = {(row["case_id"], row["candidate_id"]): row
                          for row in map(json.loads, stream)}
    if len(SELECTED) != 25:
        raise ValueError("targeted validation roster differs")
    selected_slots = [slot for slot in roster
                      if (slot["case_id"], slot["candidate_id"]) in SELECTED]
    if len(selected_slots) != len(SELECTED):
        raise ValueError("targeted candidate identity missing from frozen roster")
    model = SentenceTransformerSimilarity(ACTION_MODEL_NAME, ACTION_MODEL_REVISION,
                                          str(MODEL_CACHE))
    result_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    fact_rows: list[dict[str, Any]] = []
    alignment_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for slot in selected_slots:
        case_id, candidate_id = slot["case_id"], slot["candidate_id"]
        key = case_id, candidate_id
        graph_path = Path(slot["activity_graph_path"])
        if _sha(graph_path) != slot["activity_graph_sha256"]:
            raise ValueError(f"candidate graph hash mismatch: {key}")
        generated = load_generated_graph(graph_path)
        result = evaluate_combined_candidate_v2(
            case_id, candidate_id, generated, model, corpus=corpus)
        combined = result.to_dict()
        previous = frozen[key]
        combined["graph_sha256"] = slot["activity_graph_sha256"]
        result_rows.append(combined)
        prior = prior_combined[key]
        old_alignment = previous["Action Alignment Table"]
        new_alignment = combined["Action Alignment Table"]
        old_by_unit: dict[str, set[str]] = {}
        new_by_unit: dict[str, set[str]] = {}
        for table, target in ((old_alignment, old_by_unit), (new_alignment, new_by_unit)):
            for entry in table["entries"]:
                for unit in entry["unit_ids"]:
                    target.setdefault(unit, set()).update(entry["generated_ids"])
        old_ambiguous = set(old_alignment["ambiguous_unit_ids"])
        new_ambiguous = set(new_alignment["ambiguous_unit_ids"])
        for unit in sorted(old_by_unit.keys() | new_by_unit.keys()
                           | old_ambiguous | new_ambiguous):
            old_match, new_match = old_by_unit.get(unit, set()), new_by_unit.get(unit, set())
            if old_match == new_match and (unit in old_ambiguous) == (unit in new_ambiguous):
                continue
            alignment_rows.append({
                "case_id": case_id, "candidate_id": candidate_id, "source_unit_id": unit,
                "old_accepted_ids": ";".join(sorted(old_match)),
                "new_accepted_ids": ";".join(sorted(new_match)),
                "old_ambiguous": unit in old_ambiguous,
                "new_ambiguous": unit in new_ambiguous,
                "old_plausible_ids": ";".join(old_alignment["ambiguous_candidate_ids"].get(unit, [])),
                "new_plausible_ids": ";".join(new_alignment["ambiguous_candidate_ids"].get(unit, [])),
            })
            if (unit in set(prior["Action Alignment Table"]["ambiguous_unit_ids"])
                and unit not in new_ambiguous and not new_match):
                issues.append({"case_id": case_id, "candidate_id": candidate_id,
                               "code": "NEW_ACTION_AMBIGUITY_SUPPRESSION_VS_V1",
                               "detail": unit})
        reviewed = {unit["semantic_unit_id"]: unit for unit in
                    corpus.load_case(case_id).reviewed_action["units"]}
        for entry in result.alignment.entries:
            for unit_id in entry.unit_ids:
                for node_id in entry.generated_ids:
                    source = reviewed[unit_id]["canonical_meaning"]
                    target = generated.by_id[node_id].label or ""
                    if semantic_operation_decision(source, target) in {"incompatible", "ambiguous"}:
                        issues.append({"case_id": case_id, "candidate_id": candidate_id,
                                       "code": "INCOMPATIBLE_ACTION_ACCEPTED",
                                       "detail": f"{unit_id}->{node_id}"})
        expected_valid = {
            ("1-1", "candidate_1"): ("SU-1-1-10", "n13"),
            **{("8-2", f"candidate_{i}"): ("SU-8-2-03", "n2") for i in (1, 2, 3)},
        }
        if key in expected_valid:
            unit_id, node_id = expected_valid[key]
            if node_id not in result.alignment.generated(unit_id):
                issues.append({"case_id": case_id, "candidate_id": candidate_id,
                               "code": "ADJUDICATED_VALID_ACTION_NOT_RESTORED",
                               "detail": f"{unit_id}->{node_id}"})
        if key == ("8-2", "candidate_2") and (
            "SU-8-2-07" not in new_ambiguous or result.alignment.generated("SU-8-2-07")
        ):
            issues.append({"case_id": case_id, "candidate_id": candidate_id,
                           "code": "CORRECTION_REQUEST_AMBIGUITY_NOT_PRESERVED",
                           "detail": "SU-8-2-07"})
        if case_id == "6-4":
            unit = next(u for u in result.action.semantic_activity_units
                        if u.unit_id == "SU-6-4-16")
            if unit.source_passage or result.alignment.generated(unit.unit_id):
                issues.append({"case_id": case_id, "candidate_id": candidate_id,
                               "code": "REFERENCE_ONLY_EXCEL_FACT_AUTO_RESOLVED",
                               "detail": unit.unit_id})
        if case_id == "5-2" and result.alignment.generated("SU-5-2-04"):
            issues.append({"case_id": case_id, "candidate_id": candidate_id,
                           "code": "FALSE_APPROVAL_MATCH_REINTRODUCED",
                           "detail": "SU-5-2-04"})
        if key == ("1-1", "candidate_1"):
            join = next(f for f in result.control_node_source.facts
                        if f.fact_id == "CF-1-1-N05")
            sync = {f.fact_id: f.status for f in result.control_relation.facts
                    if f.fact_id in {"CF-1-1-R10", "CF-1-1-R11"}}
            if (join.status, join.generated_node_id) != ("TP", "n18") or sync != {
                "CF-1-1-R10": "FN", "CF-1-1-R11": "FN"}:
                issues.append({"case_id": case_id, "candidate_id": candidate_id,
                               "code": "JOIN_PRESENCE_RELATION_BOUNDARY_FAILED",
                               "detail": {"node": join.status, "relations": sync}})
        old_inventory = {tuple(pair) for pair in previous["Flow"]["fixed_required_precedence"]}
        new_inventory = set(result.flow.inventory.required_precedence)
        expected_add = {("SU-10-11-06", "SU-10-11-07")} if case_id == "10-11" else set()
        expected_remove = {("SU-6-4-06", "SU-6-4-07")} if case_id == "6-4" else set()
        if new_inventory - old_inventory != expected_add or old_inventory - new_inventory != expected_remove:
            issues.append({"case_id": case_id, "candidate_id": candidate_id,
                           "code": "FLOW_FACT_SNAPSHOT_MISMATCH",
                           "detail": "required precedence differs beyond approved two fact changes"})
        for dimension in ("Flow", "Control Node", "Control Relation"):
            old_facts = {_key(fact, dimension): fact for fact in _facts(previous, dimension)}
            new_facts = {_key(fact, dimension): fact for fact in _facts(combined, dimension)}
            for fact_key in sorted(old_facts.keys() | new_facts.keys()):
                old, new = old_facts.get(fact_key), new_facts.get(fact_key)
                if old and new and old["status"] == new["status"]:
                    continue
                fact_rows.append({
                    "case_id": case_id, "candidate_id": candidate_id,
                    "dimension": dimension, "fact_id": fact_key,
                    "old_status": old["status"] if old else "ABSENT",
                    "new_status": new["status"] if new else "ABSENT",
                    "new_reason": new.get("reason", "") if new else "",
                    "new_reason_code": new.get("diagnostics", {}).get("reason_code", "") if new else "",
                })
            old_count = (previous[dimension]["counts"] if dimension != "Control Node"
                         else previous["Control Node"]["counts"])
            new_count = combined[dimension]["counts"]
            candidate_rows.append({
                "case_id": case_id, "candidate_id": candidate_id,
                "dimension": dimension,
                "old_tp": old_count["tp"], "new_tp": new_count["tp"],
                "old_fp": old_count["fp"], "new_fp": new_count["fp"],
                "old_fn": old_count["fn"], "new_fn": new_count["fn"],
                "old_i": old_count["indeterminate_alignment_count"],
                "new_i": new_count["indeterminate_alignment_count"],
                "old_coverage": old_count["determinate_coverage"],
                "new_coverage": new_count["determinate_coverage"],
                "old_scorable": old_count["f1"] is not None,
                "new_scorable": new_count["f1"] is not None,
            })
        # Action has no source-fact I state in the existing contract.
        candidate_rows.append({
            "case_id": case_id, "candidate_id": candidate_id, "dimension": "Action",
            "old_tp": previous["Action"]["tp"], "new_tp": combined["Action"]["tp"],
            "old_fp": previous["Action"]["fp"], "new_fp": combined["Action"]["fp"],
            "old_fn": previous["Action"]["fn"], "new_fn": combined["Action"]["fn"],
            "old_i": 0, "new_i": 0,
            "old_coverage": 1.0, "new_coverage": 1.0,
            "old_scorable": True, "new_scorable": True,
        })
        for fact in result.flow.facts:
            if fact.status == "indeterminate_alignment" and fact.diagnostics.get(
                "reason_code") == "FLOW_ACTION_ANCHOR_UNMATCHED":
                if all(result.alignment.generated(unit) for unit in
                       (fact.source_unit_id, fact.target_unit_id)):
                    issues.append({"case_id": case_id, "candidate_id": candidate_id,
                                   "code": "FLOW_MATCHED_PAIR_ABSTAINED",
                                   "detail": f"{fact.source_unit_id}->{fact.target_unit_id}"})
        for fact in result.control_relation.facts:
            owner_id = next((item["source_control_fact"] for item in
                             corpus.load_case(case_id).control["control_relations"]
                             if item["fact_id"] == fact.fact_id), None)
            if (fact.status == "TP"
                and fact.diagnostics.get("reason_code") == "CONTROL_RELATION_LOCAL_EVIDENCE_V1"
                and result.owners.get(owner_id) in {None, "indeterminate"}):
                issues.append({"case_id": case_id, "candidate_id": candidate_id,
                               "code": "RELATION_TP_WITHOUT_RELIABLE_OWNER",
                               "detail": fact.fact_id})
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%futc")
    output = ROOT / "results" / f"combined_construct_validation_v2_{now}"
    output.mkdir(parents=False, exist_ok=False)
    with (output / "combined_candidate_results.jsonl").open("w") as stream:
        for row in result_rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    _write_csv(output / "candidate_component_changes.csv", candidate_rows,
               list(candidate_rows[0]))
    _write_csv(output / "fact_status_changes.csv", fact_rows,
               ["case_id", "candidate_id", "dimension", "fact_id", "old_status",
                "new_status", "new_reason", "new_reason_code"])
    _write_csv(output / "action_alignment_changes.csv", alignment_rows,
               ["case_id", "candidate_id", "source_unit_id", "old_accepted_ids",
                "new_accepted_ids", "old_ambiguous", "new_ambiguous",
                "old_plausible_ids", "new_plausible_ids"])
    _write_json(output / "interaction_issues.json", issues)
    counts = Counter((row["dimension"], row["old_status"], row["new_status"])
                     for row in fact_rows)
    summary = {
        "status": "PASSED" if not issues else "REVIEW_REQUIRED",
        "selected_candidates": len(result_rows),
        "selected_cases": len(set(row["case_id"] for row in result_rows)),
        "selected_case_ids": sorted(set(row["case_id"] for row in result_rows)),
        "fact_transition_counts": [
            {"dimension": d, "old_status": old, "new_status": new, "count": count}
            for (d, old, new), count in sorted(counts.items())],
        "candidate_component_changes": {
            dimension: sum(row["dimension"] == dimension and
                           any(row[f"old_{field}"] != row[f"new_{field}"]
                               for field in ("tp", "fp", "fn", "i", "coverage", "scorable"))
                           for row in candidate_rows)
            for dimension in ("Action", "Flow", "Control Node", "Control Relation")},
        "issues": issues,
        "action_alignment_changed_rows": len(alignment_rows),
        "remaining_suppressed_ambiguities_vs_frozen": sum(
            row["old_ambiguous"] and not row["new_ambiguous"] and not row["new_accepted_ids"]
            for row in alignment_rows),
        "new_suppressed_ambiguities_vs_v1": sum(
            issue["code"] == "NEW_ACTION_AMBIGUITY_SUPPRESSION_VS_V1" for issue in issues),
        "unresolved_reference_only_source_facts": [
            {"case_id": "6-4", "source_unit_id": "SU-6-4-16",
             "status": "HUMAN_ADJUDICATION_REQUIRED",
             "reason": "reviewed reference-only occurrence has no process-text evidence",
             "candidate_ids": ["candidate_1", "candidate_2", "candidate_3"]},
        ],
    }
    _write_json(output / "aggregate_summary.json", summary)
    after_roster, after_baseline, _ = _identity()
    if after_roster != roster or after_baseline != frozen:
        raise ValueError("frozen baseline changed during combined validation")
    manifest = {
        "status": "TARGETED_OFFLINE_COMBINED_VALIDATION",
        "configuration_version": VERSION,
        "frozen_formal_run": FROZEN_RUN.name,
        "frozen_roster_sha256": identity["cohort"]["roster_sha256"],
        "frozen_result_sha256": _sha(FROZEN_RUN / "candidate_results.jsonl"),
        "corrected_flow_snapshot": str(FLOW_SNAPSHOT),
        "corrected_flow_manifest_sha256": _sha(FLOW_SNAPSHOT / "manifest.json"),
        "action_model": ACTION_MODEL_NAME,
        "action_model_revision": ACTION_MODEL_REVISION,
        "api_calls": 0,
        "formal_120_run": False,
        "component_hashes": {name: _sha(ROOT / name) for name in (
            "action_operation_guard_v3.py", "flow_matched_action_v1.py",
            "control_node_presence_fallback_v2.py",
            "control_relation_local_evidence_v1.py", "combined_candidate_v2.py",
        )},
        "output_hashes": {name: _sha(output / name) for name in (
            "combined_candidate_results.jsonl", "candidate_component_changes.csv",
            "fact_status_changes.csv", "action_alignment_changes.csv",
            "interaction_issues.json", "aggregate_summary.json",
        )},
    }
    manifest["prior_combined_result_sha256"] = _sha(PRIOR_COMBINED / "combined_candidate_results.jsonl")
    _write_json(output / "validation_manifest.json", manifest)
    return output


if __name__ == "__main__":
    print(run())
