"""Offline, opt-in final normal validation of combined Code candidate v8.

This does not invoke the formal runner or modify frozen inputs or outputs.
"""

from __future__ import annotations

from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from evaluation.friedrich_v3.action import ACTION_MODEL_NAME, ACTION_MODEL_REVISION, SentenceTransformerSimilarity
from evaluation.friedrich_v3.adapters import load_generated_graph

from .combined_candidate_v8 import FLOW_SNAPSHOT, VERSION, evaluate_combined_candidate_v8
from .combined_candidate_v3 import SNAPSHOT, SourceEligibilityCorpus
from .inventory import load_frozen_corpus
from .run_combined_validation_v2 import FROZEN_RUN, MODEL_CACHE, ROOT, _identity, _sha


DIMENSIONS = ("Action", "Flow", "Control Node", "Control Relation")
PREVIOUS = ROOT / "results/full_construct_validation_v5_20261004_125517_863820utc"
TARGETED = ROOT / "results/shared_control_targeted_v1_20261005_115517_125999utc"


def _facts(row: dict, dimension: str) -> dict[str, dict]:
    if dimension == "Action":
        return {}
    facts = row[dimension]["facts"]
    if dimension == "Flow":
        return {f"{fact['source_unit_id']}->{fact['target_unit_id']}": fact for fact in facts}
    return {fact["fact_id"]: fact for fact in facts}


def _alignment(row: dict) -> dict[str, set[str]]:
    output: dict[str, set[str]] = {}
    for entry in row["Action Alignment Table"]["entries"]:
        for unit in entry["unit_ids"]:
            output.setdefault(unit, set()).update(entry["generated_ids"])
    return output


def _counts(row: dict, dimension: str) -> dict:
    return row[dimension] if dimension == "Action" else row[dimension]["counts"]


def _write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run() -> Path:
    roster, frozen, identity = _identity()
    if len(roster) != 120 or len({(s['case_id'], s['candidate_id']) for s in roster}) != 120:
        raise ValueError("frozen roster is not 120 unique candidates")
    previous_manifest = json.loads((PREVIOUS / "validation_manifest.json").read_text())
    for name, digest in previous_manifest["output_hashes"].items():
        if _sha(PREVIOUS / name) != digest:
            raise ValueError(f"previous reviewed validation changed: {name}")
    prior = {(row["case_id"], row["candidate_id"]): row for row in
             map(json.loads, (PREVIOUS / "candidate_results.jsonl").open())}
    if len(prior) != 120 or previous_manifest["frozen_roster_sha256"] != identity["cohort"]["roster_sha256"]:
        raise ValueError("previous reviewed validation roster differs")
    targeted = json.loads((TARGETED / "shared_control_validation_manifest.json").read_text())
    if targeted["passed_checks"] != 65 or targeted["integrated_unexpected_changes"] != 0:
        raise ValueError("shared-control targeted gate is not passed")
    for name, digest in targeted["component_sha256"].items():
        if _sha(ROOT / name) != digest:
            raise ValueError(f"targeted component changed: {name}")
    for name in ("action_operation_guard_v4.py", "flow_matched_action_v1.py",
                 "control_node_role_assignment_v4.py", "control_relation_local_evidence_v3.py",
                 "candidate_reporting_v1.py"):
        if _sha(ROOT / name) != previous_manifest["component_hashes"][name]:
            raise ValueError(f"previous component changed: {name}")
    if (_sha(FLOW_SNAPSHOT / "manifest.json") != previous_manifest["flow_snapshot_manifest_sha256"]
        or _sha(SNAPSHOT / "manifest.json") != previous_manifest["source_action_eligibility_sha256"]):
        raise ValueError("inventory or eligibility snapshot changed")
    for slot in roster:
        if _sha(Path(slot["activity_graph_path"])) != slot["activity_graph_sha256"]:
            raise ValueError(f"frozen graph changed: {slot['case_id']}/{slot['candidate_id']}")
    corpus = SourceEligibilityCorpus(load_frozen_corpus())
    model = SentenceTransformerSimilarity(ACTION_MODEL_NAME, ACTION_MODEL_REVISION, str(MODEL_CACHE))
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%futc")
    output = ROOT / "results" / f"full_construct_validation_v6_{now}"
    output.mkdir(parents=False, exist_ok=False)
    action_rows: list[dict] = []
    fact_rows: list[dict] = []
    candidate_rows: list[dict] = []
    summaries = {dim: Counter() for dim in DIMENSIONS}
    new_results: dict[tuple[str, str], dict] = {}
    with (output / "candidate_results.jsonl").open("w", encoding="utf-8") as stream:
        for slot in roster:
            case_id, candidate_id = slot["case_id"], slot["candidate_id"]
            key = case_id, candidate_id
            graph_path = Path(slot["activity_graph_path"])
            if _sha(graph_path) != slot["activity_graph_sha256"]:
                raise ValueError(f"graph hash mismatch: {key}")
            generated = load_generated_graph(graph_path)
            result = evaluate_combined_candidate_v8(case_id, candidate_id, generated, model, corpus=corpus)
            row = result.to_dict()
            row["configuration_version"] = VERSION
            row["graph_sha256"] = slot["activity_graph_sha256"]
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            new_results[key] = row
            old = prior[key]
            old_map, new_map = _alignment(old), _alignment(row)
            old_a = set(old["Action Alignment Table"]["ambiguous_unit_ids"])
            new_a = set(row["Action Alignment Table"]["ambiguous_unit_ids"])
            for unit in sorted(old_map.keys() | new_map.keys() | old_a | new_a):
                om, nm = old_map.get(unit, set()), new_map.get(unit, set())
                if om == nm and (unit in old_a) == (unit in new_a):
                    continue
                action_rows.append({
                    "case_id": case_id, "candidate_id": candidate_id, "source_unit_id": unit,
                    "old_accepted_ids": ";".join(sorted(om)), "new_accepted_ids": ";".join(sorted(nm)),
                    "old_ambiguous": unit in old_a, "new_ambiguous": unit in new_a,
                    "old_plausible_ids": ";".join(old["Action Alignment Table"]["ambiguous_candidate_ids"].get(unit, [])),
                    "new_plausible_ids": ";".join(row["Action Alignment Table"]["ambiguous_candidate_ids"].get(unit, [])),
                    "classification": "AMBIGUOUS / NEEDS REVIEW", "review_note": "Semantic mapping needs inspection",
                })
            for dim in DIMENSIONS:
                oc, nc = _counts(old, dim), _counts(row, dim)
                for field in ("tp", "fp", "fn"):
                    summaries[dim][field] += nc[field]
                if dim != "Action":
                    summaries[dim]["indeterminate"] += nc["indeterminate_alignment_count"]
                    summaries[dim]["required"] += nc["required_denominator"]
                    summaries[dim]["na_candidates"] += int(nc.get("status") == "N/A")
                    summaries[dim]["indeterminate_candidates"] += int(nc.get("status") == "indeterminate" or
                                                                   (dim != "Control Relation" and nc["f1"] is None))
                summaries[dim]["numeric_candidates"] += int(nc["f1"] is not None)
                summaries[dim]["null_candidates"] += int(nc["f1"] is None)
                changed = any(oc.get(field) != nc.get(field) for field in
                              ("tp", "fp", "fn", "indeterminate_alignment_count", "required_denominator", "f1"))
                candidate_rows.append({
                    "case_id": case_id, "candidate_id": candidate_id, "dimension": dim,
                    "old_tp": oc["tp"], "new_tp": nc["tp"],
                    "old_fp": oc["fp"], "new_fp": nc["fp"],
                    "old_fn": oc["fn"], "new_fn": nc["fn"],
                    "old_indeterminate": oc.get("indeterminate_alignment_count", 0),
                    "new_indeterminate": nc.get("indeterminate_alignment_count", 0),
                    "old_f1": oc["f1"], "new_f1": nc["f1"], "changed": changed,
                })
                if dim == "Action":
                    continue
                old_f, new_f = _facts(old, dim), _facts(row, dim)
                for fact_id in sorted(old_f.keys() | new_f.keys()):
                    before, after = old_f.get(fact_id), new_f.get(fact_id)
                    if before and after and before["status"] == after["status"] and before.get("generated_node_id") == after.get("generated_node_id"):
                        continue
                    fact_rows.append({
                        "case_id": case_id, "candidate_id": candidate_id, "dimension": dim,
                        "fact_id": fact_id, "old_status": before["status"] if before else "ABSENT",
                        "new_status": after["status"] if after else "ABSENT",
                        "old_generated_node_id": before.get("generated_node_id", "") if before else "",
                        "new_generated_node_id": after.get("generated_node_id", "") if after else "",
                        "new_reason": after.get("reason", "") if after else "",
                        "new_reason_code": after.get("diagnostics", {}).get("reason_code", "") if after else "",
                        "classification": "AMBIGUOUS / NEEDS REVIEW", "review_note": "Fact semantics need inspection",
                    })
    # Derived statistics use the existing fact denominator, including indeterminate required facts.
    aggregate = {}
    for dim, c in summaries.items():
        tp, fp, fn = c["tp"], c["fp"], c["fn"]
        p = tp / (tp + fp) if tp + fp else None
        r = tp / (tp + fn) if tp + fn else None
        f1 = 2 * p * r / (p + r) if p is not None and r is not None and p + r else (0.0 if p is not None and r is not None else None)
        aggregate[dim] = dict(c)
        aggregate[dim].update({"coverage": ((c["required"] - c["indeterminate"]) / c["required"] if c["required"] else None) if dim != "Action" else 1.0,
                               "pooled_precision": p, "pooled_recall": r, "pooled_f1": f1})
    _write_csv(output / "action_alignment_changes.csv", action_rows,
               ["case_id", "candidate_id", "source_unit_id", "old_accepted_ids", "new_accepted_ids", "old_ambiguous", "new_ambiguous", "old_plausible_ids", "new_plausible_ids", "classification", "review_note"])
    _write_csv(output / "fact_changes.csv", fact_rows,
               ["case_id", "candidate_id", "dimension", "fact_id", "old_status", "new_status", "old_generated_node_id", "new_generated_node_id", "new_reason", "new_reason_code", "classification", "review_note"])
    _write_csv(output / "candidate_dimension_changes.csv", candidate_rows, list(candidate_rows[0]))
    (output / "aggregate_summary.json").write_text(json.dumps({"dimensions": aggregate, "changed_action_mappings": len(action_rows), "changed_facts": len(fact_rows),
        "changed_candidate_dimensions": sum(r["changed"] for r in candidate_rows), "changed_candidates": len({(r["case_id"], r["candidate_id"]) for r in action_rows + fact_rows + [r for r in candidate_rows if r["changed"]]}),
        "source_fact_adjudication_pending": "6-4/SU-6-4-16"}, indent=2) + "\n")
    after_roster, after_frozen, _ = _identity()
    if after_roster != roster or after_frozen != frozen:
        raise ValueError("frozen baseline changed during validation")
    manifest = {"status": "OFFLINE_FULL_SCOPE_VALIDATION", "configuration_version": VERSION,
        "candidate_count": len(new_results), "case_count": len({k[0] for k in new_results}),
        "api_calls": 0, "formal_run": False, "frozen_roster_sha256": identity["cohort"]["roster_sha256"],
        "frozen_baseline_sha256": _sha(FROZEN_RUN / "candidate_results.jsonl"),
        "previous_reviewed_validation_sha256": _sha(PREVIOUS / "candidate_results.jsonl"),
        "targeted_manifest_sha256": _sha(TARGETED / "shared_control_validation_manifest.json"),
        "flow_snapshot": str(FLOW_SNAPSHOT), "flow_snapshot_manifest_sha256": _sha(FLOW_SNAPSHOT / "manifest.json"),
        "source_action_eligibility_snapshot": str(SNAPSHOT), "source_action_eligibility_sha256": _sha(SNAPSHOT / "manifest.json"),
        "component_hashes": {name: _sha(ROOT / name) for name in (
            "action_operation_guard_v4.py", "flow_matched_action_v1.py", "control_node_role_assignment_v4.py",
            "control_node_shared_roles_v5.py", "control_relation_local_evidence_v3.py",
            "control_relation_shared_owner_v4.py", "candidate_reporting_v1.py",
            "combined_candidate_v8.py", "run_full_construct_validation_v6.py")},
        "output_hashes": {path.name: _sha(path) for path in output.iterdir() if path.is_file()}}
    (output / "validation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return output


if __name__ == "__main__":
    print(run())
