"""Read-only formal 40x3 V3.1 run and descriptive reporting.

This module orchestrates the already validated evaluator. It contains no
matching, anchoring, threshold, or scoring decisions.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import traceback
from typing import Any

from evaluation.friedrich_v3.action import (
    ACTION_MODEL_NAME, ACTION_MODEL_REVISION, SentenceTransformerSimilarity,
)
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory
from evaluation.friedrich_semantic_v2.evaluator_adapter import project_reviewed_inventory
from evaluation.friedrich_v3.adapters import load_generated_graph

from .control import normalize_generated_control
from .evaluator import evaluate_candidate_file_v3
from .flow_inventory_store import DEFAULT_FLOW_ROOT, load_fixed_flow_inventory
from .inventory import DEFAULT_FROZEN_ROOT, FrozenCorpus, load_frozen_corpus


STUDIO_ROOT = Path(__file__).resolve().parents[2]
COHORT_ROOT = STUDIO_ROOT / "evaluation/friedrich_v2/cohorts/final_frozen_40x3_20260910"
MODEL_CACHE = STUDIO_ROOT.parent / "studio-friedrich-scoring/.hf-cache"
OUTPUT_ROOT = Path(__file__).resolve().parent / "results/v3_1_formal_120_20260924"
COMPONENTS = ("Action", "Flow", "Control Node", "Control Relation")
METRICS = ("tp", "fp", "fn", "precision", "recall", "f1")
# Declared before formal scoring. Flags are diagnostic only and cannot alter scores.
REVIEW_CRITERIA = (
    "technical_exception_or_malformed",
    "evaluator_indeterminate_alignment",
    "scored_control_false_positive",
    "affirmative_no_control_false_positive",
    "unsupported_flow_cycle_violation",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def source_denominators(corpus: FrozenCorpus, case_id: str) -> dict[str, int]:
    case = corpus.load_case(case_id)
    reviewed = SemanticInventory.from_dict(case.reviewed_action)
    projection = project_reviewed_inventory(reviewed, case.reference_evidence)
    flow = load_fixed_flow_inventory(case_id, corpus)
    return {
        "Action": len(projection.action_units),
        "Flow": len(flow.required_precedence),
        "Control Node": sum(f["status"] == "required" for f in case.control["control_nodes"]),
        "Control Relation": sum(f["status"] == "required" for f in case.control["control_relations"]),
    }


def frozen_files(corpus: FrozenCorpus) -> list[Path]:
    paths = list(DEFAULT_FROZEN_ROOT.rglob("*")) + list(DEFAULT_FLOW_ROOT.rglob("*"))
    paths += [p for p in Path(__file__).resolve().parent.glob("*.py")]
    paths += [p for p in (STUDIO_ROOT / "api/model/llm").rglob("*")
              if p.is_file() and p.suffix in {".py", ".jinja"}]
    paths += [COHORT_ROOT / "generated_manifest.json", COHORT_ROOT / "run_manifest.json"]
    for item in corpus.manifest["components"]["action_scoring_code"].values():
        paths.append(Path(item["path"]))
    for case_id in corpus.case_ids:
        paths += [corpus.source_root / case_id / name for name in
                  ("process_text.txt", "inventory_reviewed.json", "reference_evidence.json")]
    return sorted({p.resolve() for p in paths if p.is_file()})


def snapshot(paths: list[Path]) -> dict[str, str]:
    return {str(path): sha(path) for path in paths}


def verify_cohort(corpus: FrozenCorpus) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest_path = COHORT_ROOT / "generated_manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    if (manifest.get("cohort_id") != "final_frozen_40x3_20260910"
        or manifest.get("run_integrity_status") != "valid"
        or manifest.get("human_selection") is not False
        or len(manifest.get("cases", [])) != 40):
        raise ValueError("frozen cohort manifest identity or case count changed")
    cases = manifest["cases"]
    if {c["case_id"] for c in cases} != set(corpus.case_ids):
        raise ValueError("frozen cohort case roster differs from V3.1")
    roster: list[dict[str, Any]] = []
    for case in cases:
        case_id = case["case_id"]
        candidates = case["candidates"]
        if {c["candidate_id"] for c in candidates} != {"candidate_1", "candidate_2", "candidate_3"}:
            raise ValueError(f"frozen candidate roster mismatch: {case_id}")
        for candidate in sorted(candidates, key=lambda c: c["candidate_id"]):
            candidate_id = candidate["candidate_id"]
            if candidate.get("generation_status") != "success":
                raise ValueError(f"frozen cohort candidate generation status changed: {case_id}/{candidate_id}")
            directory = COHORT_ROOT / "cases" / case_id / candidate_id
            graph = directory / "activity_graph.json"
            technical = directory / "technical_status.json"
            own_manifest = directory / "candidate_manifest.json"
            if sha(graph) != candidate["generated_model_sha256"]:
                raise ValueError(f"candidate graph SHA-256 mismatch: {case_id}/{candidate_id}")
            own = json.loads(own_manifest.read_bytes())
            if own.get("case_id") != case_id or own.get("candidate_id") != candidate_id:
                raise ValueError(f"candidate manifest identity mismatch: {case_id}/{candidate_id}")
            if own["artifact_hashes"]["activity_graph.json"] != sha(graph):
                raise ValueError(f"candidate manifest graph hash mismatch: {case_id}/{candidate_id}")
            if own["artifact_hashes"]["technical_status.json"] != sha(technical):
                raise ValueError(f"candidate technical status hash mismatch: {case_id}/{candidate_id}")
            status = json.loads(technical.read_bytes()).get("status")
            roster.append({
                "case_id": case_id, "candidate_id": candidate_id,
                "activity_graph_path": str(graph), "activity_graph_sha256": sha(graph),
                "candidate_manifest_path": str(own_manifest),
                "candidate_manifest_sha256": sha(own_manifest),
                "technical_status_path": str(technical),
                "technical_status_sha256": sha(technical),
                "technical_status": status,
            })
    if len(roster) != 120 or len({(r["case_id"], r["candidate_id"]) for r in roster}) != 120:
        raise ValueError("formal cohort does not have exactly 120 unique slots")
    return roster, {
        "cohort_id": manifest["cohort_id"],
        "generated_manifest_path": str(manifest_path),
        "generated_manifest_sha256": sha(manifest_path),
        "roster_sha256": canonical_sha(roster),
        "case_count": 40, "candidate_count": 120,
    }


def counts(result: dict[str, Any], component: str) -> dict[str, Any] | None:
    if result.get("candidate_status") != "EVALUATED":
        return None
    value = result[component]
    return value if component == "Action" else value["counts"]


def fact_ids(result: dict[str, Any], component: str, state: str) -> list[str]:
    if result.get("candidate_status") != "EVALUATED":
        return []
    if component == "Flow":
        return [f"{f['source_unit_id']}->{f['target_unit_id']}" for f in result["Flow"]["facts"]
                if f["status"] == state]
    if component in ("Control Node", "Control Relation"):
        return [f["fact_id"] for f in result[component]["facts"] if f["status"] == state]
    return []


def review_items(result: dict[str, Any], no_control: bool) -> list[dict[str, Any]]:
    case_id, candidate_id = result["case_id"], result["candidate_id"]
    out: list[dict[str, Any]] = []

    def add(criterion: str, component: str, ids: list[str], reason: str) -> None:
        out.append({"case_id": case_id, "candidate_id": candidate_id,
                    "triggered_criterion": criterion, "affected_component": component,
                    "exact_fact_ids": ids, "reason_for_review": reason})

    if result.get("candidate_status") != "EVALUATED":
        add("technical_exception_or_malformed", "all", [],
            result.get("malformed_reason") or result.get("technical_exception", "unknown"))
        return out
    for component in ("Flow", "Control Node", "Control Relation"):
        ids = fact_ids(result, component, "indeterminate_alignment")
        if ids:
            add("evaluator_indeterminate_alignment", component, ids,
                "Frozen required facts retain indeterminate evaluator alignment and null scalar metrics.")
    for component in ("Control Node", "Control Relation"):
        value = result[component]
        fp = value["counts"]["fp"]
        if fp:
            affected = [f["fact_id"] for f in value["facts"] if "FP" in f["status"]]
            affected += [x["generated_relation_id"] for x in value["generated_relation_coverage"]
                         if x["status"] == "FP"]
            add("scored_control_false_positive", component, affected,
                f"{fp} scored Control false positive(s); IDs name source facts or generated relations.")
    if no_control and any(result[c]["counts"]["fp"] for c in ("Control Node", "Control Relation")):
        add("affirmative_no_control_false_positive", "Control", [],
            "Generated Control structure violates an affirmative no-control source scope.")
    if result["Flow"].get("unsupported_cycle_violation_count", 0):
        ids = [f"{f['source_unit_id']}->{f['target_unit_id']}" for f in result["Flow"]["facts"]
               if "generated cycle reverses" in f["reason"].lower()]
        add("unsupported_flow_cycle_violation", "Flow", ids,
            "Generated cycle conflicts with frozen required forward precedence.")
    return out


def candidate_row(result: dict[str, Any], technical_status: str,
                  denominators: dict[str, int], flags: list[str]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "case_id": result["case_id"], "candidate_id": result["candidate_id"],
        "technical_status": technical_status, "candidate_status": result["candidate_status"],
        "unresolved_source_question_count": len(result["source_unresolved_questions"]),
        "review_flags": ";".join(flags),
    }
    for component in COMPONENTS:
        prefix = component.lower().replace(" ", "_")
        value = counts(result, component)
        row[f"{prefix}_source_denominator"] = denominators[component]
        for metric in METRICS:
            row[f"{prefix}_{metric}"] = value.get(metric) if value else None
        if component != "Action":
            row[f"{prefix}_indeterminate_alignment_count"] = (
                value["indeterminate_alignment_count"] if value else None)
            row[f"{prefix}_determinate_coverage"] = (
                value["determinate_coverage"] if value else None)
            if component == "Flow":
                row["flow_recall_interval"] = (json.dumps(value["recall_interval"]) if value else None)
    row["complete"] = result["candidate_status"] == "EVALUATED" and all(
        counts(result, component)["f1"] is not None for component in COMPONENTS)
    row["indeterminate"] = result["candidate_status"] == "EVALUATED" and any(
        counts(result, component)["indeterminate_alignment_count"] > 0
        for component in COMPONENTS if component != "Action")
    return row


def metric_summary(values: list[float | int | None], expected: int) -> dict[str, Any]:
    valid = [v for v in values if v is not None]
    return {"all_slot_mean": sum(valid) / expected if len(valid) == expected else None,
            "complete_observation_mean_descriptive": sum(valid) / len(valid) if valid else None,
            "numeric_observation_count": len(valid), "expected_slot_count": expected}


def summarize(rows: list[dict[str, Any]], results: list[dict[str, Any]],
              corpus: FrozenCorpus) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    case_summaries: list[dict[str, Any]] = []
    by_id = {(r["case_id"], r["candidate_id"]): r for r in results}
    metric_keys = [f"{c.lower().replace(' ', '_')}_{m}" for c in COMPONENTS for m in METRICS]
    metric_keys += [f"{c.lower().replace(' ', '_')}_{m}" for c in COMPONENTS[1:]
                    for m in ("indeterminate_alignment_count", "determinate_coverage")]
    for case_id in corpus.case_ids:
        case = corpus.load_case(case_id)
        selected = [r for r in rows if r["case_id"] == case_id]
        assert len(selected) == 3
        case_summaries.append({
            "case_id": case_id,
            "candidates": selected,
            "case_mean_by_metric": {k: metric_summary([r[k] for r in selected], 3)
                                    for k in metric_keys},
            "complete_candidate_count": sum(r["complete"] for r in selected),
            "indeterminate_candidate_count": sum(r["indeterminate"] for r in selected),
            "malformed_candidate_count": sum(r["candidate_status"] == "MALFORMED" for r in selected),
            "technical_exception_count": sum(r["candidate_status"] == "TECHNICAL_ERROR" for r in selected),
            "source_denominators": source_denominators(corpus, case_id),
            "unresolved_source_questions": case.control["unresolved_facts"],
            "no_control": case.control["no_control"],
        })
    macro = {k: metric_summary([r[k] for r in rows], 120) for k in metric_keys}
    balanced = {k: metric_summary([c["case_mean_by_metric"][k]["all_slot_mean"]
                                   for c in case_summaries], 40) for k in metric_keys}
    micro: dict[str, Any] = {}
    for component in COMPONENTS:
        prefix = component.lower().replace(" ", "_")
        available = [r for r in rows if r["candidate_status"] == "EVALUATED"]
        tp, fp, fn = (sum(r[f"{prefix}_{m}"] for r in available) for m in ("tp", "fp", "fn"))
        denominator = sum(r[f"{prefix}_source_denominator"] for r in rows)
        indeterminate = (sum(r[f"{prefix}_indeterminate_alignment_count"] for r in available)
                         if component != "Action" else 0)
        complete = len(available) == 120 and indeterminate == 0
        micro[component] = {
            "tp": tp, "fp": fp, "fn": fn,
            "source_denominator_all_120_slots": denominator,
            "indeterminate_alignment_count": indeterminate,
            "evaluated_slot_count": len(available),
            "precision": (tp / (tp + fp) if tp + fp else 0.0) if complete else None,
            "recall": (tp / (tp + fn) if tp + fn else 0.0) if complete else None,
            "f1": (2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0)
                  if complete else None,
            "determinate_coverage": ((tp + fn) / denominator if denominator else 1.0)
                                     if len(available) == 120 else None,
            "recall_interval": ([tp / denominator if denominator else 1.0,
                                 (tp + indeterminate) / denominator if denominator else 1.0]
                                if len(available) == 120 else None),
        }
    no_control = [r for r in rows if corpus.load_case(r["case_id"]).control["no_control"]]
    aggregate = {
        "candidate_macro_averages": macro,
        "case_balanced_averages": balanced,
        "pooled_micro": micro,
        "coverage_indeterminate": {
            component: {"indeterminate_fact_count": sum(
                r[f"{component.lower().replace(' ', '_')}_indeterminate_alignment_count"] or 0
                for r in rows),
                "candidates_with_indeterminate": sum(
                    (r[f"{component.lower().replace(' ', '_')}_indeterminate_alignment_count"] or 0) > 0
                    for r in rows)} for component in COMPONENTS[1:]},
        "no_control_negative_case_cleanliness": {
            "case_count": len({r["case_id"] for r in no_control}),
            "candidate_count": len(no_control),
            "clean_candidate_count": sum(r["candidate_status"] == "EVALUATED" and
                                         r["control_node_fp"] == 0 and r["control_relation_fp"] == 0
                                         for r in no_control),
            "control_node_fp": sum(r["control_node_fp"] or 0 for r in no_control),
            "control_relation_fp": sum(r["control_relation_fp"] or 0 for r in no_control),
        },
        "malformed_candidate_count": sum(r["candidate_status"] == "MALFORMED" for r in rows),
        "technical_exception_count": sum(r["candidate_status"] == "TECHNICAL_ERROR" for r in rows),
        "complete_candidate_count": sum(r["complete"] for r in rows),
        "indeterminate_candidate_count": sum(r["indeterminate"] for r in rows),
        "evaluated_candidate_count": sum(r["candidate_status"] == "EVALUATED" for r in rows),
        "candidate_slot_count": len(rows),
    }
    return case_summaries, aggregate


def main() -> None:
    if OUTPUT_ROOT.exists():
        raise FileExistsError(f"formal output already exists: {OUTPUT_ROOT}")
    corpus = load_frozen_corpus()
    for case_id in corpus.case_ids:
        load_fixed_flow_inventory(case_id, corpus)
    roster, cohort_identity = verify_cohort(corpus)
    fixed_paths = frozen_files(corpus)
    fixed_paths += [Path(r[key]) for r in roster for key in
                    ("activity_graph_path", "candidate_manifest_path", "technical_status_path")]
    fixed_paths = sorted(set(fixed_paths))
    before = snapshot(fixed_paths)
    denominators = {case_id: source_denominators(corpus, case_id) for case_id in corpus.case_ids}
    OUTPUT_ROOT.mkdir(parents=True)
    identity = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "v3_1_corpus_sha256": corpus.corpus_sha256,
        "scoring_contract_sha256": corpus.manifest["components"]["scoring_contract"]["sha256"],
        "v2_action_code": corpus.manifest["components"]["action_scoring_code"],
        "all_40_control_inventory_hashes": {
            case_id: corpus.manifest["components"]["cases"][case_id]["control_inventory_sha256"]
            for case_id in corpus.case_ids},
        "flow_manifest_sha256": sha(DEFAULT_FLOW_ROOT / "manifest.json"),
        "cohort": cohort_identity,
        "roster": roster,
        "review_criteria_predeclared": REVIEW_CRITERIA,
        "pre_run_file_hashes": before,
    }
    write_json(OUTPUT_ROOT / "run_identity_before.json", identity)
    similarity = SentenceTransformerSimilarity(ACTION_MODEL_NAME, ACTION_MODEL_REVISION,
                                                str(MODEL_CACHE))
    results: list[dict[str, Any]] = []
    raw_path = OUTPUT_ROOT / "candidate_results.jsonl"
    with raw_path.open("w", encoding="utf-8") as stream:
        for index, slot in enumerate(roster, start=1):
            case_id, candidate_id = slot["case_id"], slot["candidate_id"]
            try:
                result = evaluate_candidate_file_v3(
                    case_id, candidate_id, slot["activity_graph_path"], similarity, corpus=corpus)
                result["technical_status"] = slot["technical_status"]
                result["source_denominators"] = denominators[case_id]
                if result["candidate_status"] == "EVALUATED":
                    original = load_generated_graph(slot["activity_graph_path"])
                    normalized = normalize_generated_control(original)
                    original_ids = {node.id for node in original.nodes}
                    normalized_ids = {node.id for node in normalized.nodes}
                    result["normalization_events"] = [
                        {"event": "contract_unlabeled_one_in_one_out_gateway", "generated_node_id": node_id}
                        for node_id in sorted(original_ids - normalized_ids)
                    ]
                    result["action_alignment_table_reference"] = f"candidate_results.jsonl#L{index}/Action Alignment Table"
                    result["control_anchor_evidence_reference"] = f"candidate_results.jsonl#L{index}/Control Anchor Evidence"
                    for component in COMPONENTS:
                        value = counts(result, component)
                        if component == "Action":
                            assert value["tp"] + value["fn"] == denominators[case_id][component]
                        else:
                            assert value["required_denominator"] == denominators[case_id][component]
                            assert value["tp"] + value["fn"] + value["indeterminate_alignment_count"] == denominators[case_id][component]
                    assert result["source_unresolved_questions"] == corpus.load_case(case_id).control["unresolved_facts"]
                else:
                    result["normalization_events"] = None
            except Exception as exc:
                result = {
                    "case_id": case_id, "candidate_id": candidate_id,
                    "candidate_status": "TECHNICAL_ERROR", "technical_status": slot["technical_status"],
                    "technical_exception": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                    "source_denominators": denominators[case_id],
                    "source_unresolved_questions": corpus.load_case(case_id).control["unresolved_facts"],
                    "component_scores": None,
                }
            results.append(result)
            stream.write(json.dumps(result, ensure_ascii=False) + "\n")
            stream.flush()
            print(f"[{index:03d}/120] {case_id}/{candidate_id}: {result['candidate_status']}", flush=True)
    after_corpus = load_frozen_corpus()
    for case_id in after_corpus.case_ids:
        load_fixed_flow_inventory(case_id, after_corpus)
    after_roster, after_identity = verify_cohort(after_corpus)
    after = snapshot(fixed_paths)
    changed = sorted(path for path in before if before[path] != after.get(path))
    if cohort_identity != after_identity or roster != after_roster:
        changed.append("cohort identity or roster")
    if len(results) != 120:
        changed.append("candidate slot count")
    write_json(OUTPUT_ROOT / "run_integrity.json", {
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_slots_processed": len(results),
        "file_count_compared": len(fixed_paths),
        "changed_files_or_identities": changed,
        "pre_run_snapshot_sha256": canonical_sha(before),
        "post_run_snapshot_sha256": canonical_sha(after),
        "integrity_passed": not changed,
    })
    rows: list[dict[str, Any]] = []
    shortlist: list[dict[str, Any]] = []
    for result, slot in zip(results, roster, strict=True):
        case_id = result["case_id"]
        review = review_items(result, corpus.load_case(case_id).control["no_control"])
        shortlist.extend(review)
        rows.append(candidate_row(result, slot["technical_status"], denominators[case_id],
                                  sorted({r["triggered_criterion"] for r in review})))
    row_fields = list(rows[0])
    write_csv(OUTPUT_ROOT / "candidate_results.csv", rows, row_fields)
    cases, aggregate = summarize(rows, results, corpus)
    write_json(OUTPUT_ROOT / "case_summary.json", cases)
    case_csv = [{"case_id": c["case_id"], "complete_candidate_count": c["complete_candidate_count"],
                 "indeterminate_candidate_count": c["indeterminate_candidate_count"],
                 "malformed_candidate_count": c["malformed_candidate_count"],
                 "technical_exception_count": c["technical_exception_count"],
                 "no_control": c["no_control"],
                 "unresolved_source_question_count": len(c["unresolved_source_questions"]),
                 **{f"{k}_mean_all_three": v["all_slot_mean"]
                    for k, v in c["case_mean_by_metric"].items()}}
                for c in cases]
    write_csv(OUTPUT_ROOT / "case_summary.csv", case_csv, list(case_csv[0]))
    write_json(OUTPUT_ROOT / "aggregate_summary.json", aggregate)
    write_json(OUTPUT_ROOT / "human_review_shortlist.json", shortlist)
    review_csv = [{**r, "exact_fact_ids": ";".join(r["exact_fact_ids"])} for r in shortlist]
    write_csv(OUTPUT_ROOT / "human_review_shortlist.csv", review_csv,
              ["case_id", "candidate_id", "triggered_criterion", "affected_component",
               "exact_fact_ids", "reason_for_review"])
    status = ("FORMAL EVALUATION ABORTED — INTEGRITY ISSUE" if changed else
              "FORMAL EVALUATION COMPLETED WITH TECHNICAL EXCEPTIONS" if
              aggregate["technical_exception_count"] or aggregate["malformed_candidate_count"] else
              "FORMAL 120-CANDIDATE V3.1 EVALUATION COMPLETED")
    report = [
        "# Friedrich V3.1 formal 120-candidate evaluation",
        "",
        f"**{status}**",
        "",
        f"- V3.1 frozen corpus SHA-256: `{corpus.corpus_sha256}`",
        f"- V3.1 scoring contract SHA-256: `{identity['scoring_contract_sha256']}`",
        f"- V2 Action matcher SHA-256: `{identity['v2_action_code']['v2_action_matcher']['sha256']}`",
        f"- V2 Action projection SHA-256: `{identity['v2_action_code']['v2_action_projection']['sha256']}`",
        f"- Cohort: `{cohort_identity['cohort_id']}`, 40 cases × 3 unchanged candidates",
        f"- Generated cohort manifest SHA-256: `{cohort_identity['generated_manifest_sha256']}`",
        f"- Exact roster SHA-256: `{cohort_identity['roster_sha256']}`",
        f"- Processed slots: {aggregate['candidate_slot_count']}; evaluated: {aggregate['evaluated_candidate_count']}; malformed: {aggregate['malformed_candidate_count']}; technical exceptions: {aggregate['technical_exception_count']}",
        f"- Complete candidates: {aggregate['complete_candidate_count']}; candidates with indeterminate alignment: {aggregate['indeterminate_candidate_count']}",
        f"- Post-run integrity: {'passed' if not changed else 'FAILED: ' + ', '.join(changed)}",
        "",
        "## Aggregate component results",
        "",
        "Macro and case-balanced all-slot means are null when any required candidate metric is null. The JSON also gives descriptive means and their numeric observation counts. Pooled scalar metrics are null whenever a component has an indeterminate or unavailable slot.",
        "",
        "| Component | Candidate macro F1 | Case-balanced F1 | Pooled TP | FP | FN | Pooled F1 | Indeterminate facts |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for component in COMPONENTS:
        prefix = component.lower().replace(" ", "_")
        p = aggregate["pooled_micro"][component]
        report.append(f"| {component} | {aggregate['candidate_macro_averages'][prefix+'_f1']['all_slot_mean']} | "
                      f"{aggregate['case_balanced_averages'][prefix+'_f1']['all_slot_mean']} | "
                      f"{p['tp']} | {p['fp']} | {p['fn']} | {p['f1']} | {p['indeterminate_alignment_count']} |")
    nc = aggregate["no_control_negative_case_cleanliness"]
    report += ["", "## Diagnostics and artifacts", "",
               f"- No-control: {nc['clean_candidate_count']}/{nc['candidate_count']} candidates have zero scored Control FP; Node FP {nc['control_node_fp']}, Relation FP {nc['control_relation_fp']}.",
               f"- Human-review diagnostic entries: {len(shortlist)}; scores unchanged by shortlist selection.",
               "- Raw candidate results include Action Alignment Tables, Control Anchor Evidence, every scored fact, generated relation coverage, FP abstentions, source questions, and indeterminate reasons.",
               "- Normalization is the frozen evaluator's unlabeled 1-in/1-out gateway contraction; the run uses it without modification. Candidate graph paths and hashes are in the pre-run identity file.",
               "- No Oracle Best-of-Three is reported. No combined overall evaluator F1 is reported.",
               "- No methodology, source inventory, scoring contract, unresolved question, generator, V2 Action evaluator, threshold, anchor rule, matching rule, or candidate changed during this formal run.",
               "", "### Output paths", ""]
    for name in ("run_identity_before.json", "run_integrity.json", "candidate_results.jsonl",
                 "candidate_results.csv", "case_summary.json", "case_summary.csv",
                 "aggregate_summary.json", "human_review_shortlist.json", "human_review_shortlist.csv"):
        report.append(f"- `{OUTPUT_ROOT / name}`")
    report += ["", status, ""]
    (OUTPUT_ROOT / "formal_evaluation_report.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"status": status, "output_root": str(OUTPUT_ROOT),
                      "aggregate": aggregate, "review_entries": len(shortlist)}, indent=2))


if __name__ == "__main__":
    main()
