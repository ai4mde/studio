#!/usr/bin/env python3
"""Read-only comparison of certified Code V3.1 and frozen AI v1.6 formal results.

This is a reporting script. It never invokes either evaluator or an API.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "evaluation/friedrich_code_v3/results/v3_1_final_certification_20260924_2135utc"
AI = ROOT / "evaluation/friedrich_v2/results/ai_v16_formal_120_20260927_212146utc"
OUTPUT_PARENT = ROOT / "evaluation/comparisons"
LABEL = "POST-HOC ORACLE ANALYSIS — NOT DEPLOYABLE CANDIDATE-SELECTION PERFORMANCE"
DIMENSIONS = (
    ("action", "Action"),
    ("flow", "Flow"),
    ("control_node", "Control Node"),
    ("control_relation", "Control Relation"),
)
REVIEW_NOTES = {
    ("action", "5-4"): ("action alignment; semantic severity judgment", "AI describes a duplicated or misgrouped treasurer check and gives a low holistic score; Code's Action ledger finds all eleven required action units and no Action FP. The holistic penalty also involves behavior outside Action F1."),
    ("action", "3-3"): ("action alignment; representation tolerance", "AI accepts the OK/Not OK marking and send-back as implicit in the decision and retry path. Code reports three Action FN and ambiguous accepted anchors for those source units; the two observations use different action granularity."),
    ("action", "10-9"): ("action alignment; representation tolerance", "AI accepts abbreviated wording of the measuring-point change process. Code records three unmatched required Action units and an ambiguous anchor; missing anchors also affect Code Flow."),
    ("action", "3-6"): ("precedence interpretation; semantic severity judgment", "Code finds every required Action unit. AI's low holistic judgment concerns duplicated checking and the incorrect return/recheck behavior, which Action F1 alone does not describe."),
    ("flow", "10-14"): ("precedence interpretation", "Code marks all eight frozen required precedence facts TP. AI objects to extra fixed sequencing of alternative examinations before the outcome; that distinction is not expressed by the saved TP/FN counts alone."),
    ("flow", "3-3"): ("Code coverage/indeterminate handling; precedence interpretation", "Code scores three determinate precedence facts TP while two of five required facts are indeterminate because of ambiguous Action anchors. AI diagnoses the Not-OK return and recurrence as defective."),
    ("flow", "8-2"): ("Code coverage/indeterminate handling; precedence interpretation", "Code scores three determinate precedence facts TP and leaves two of five indeterminate through ambiguous Action anchors. AI focuses on correction-to-resubmission recurrence and approval routing."),
    ("flow", "10-9"): ("action alignment; Code coverage/indeterminate handling", "Code records three Flow FN caused by missing required Action anchors and one indeterminate fact. AI accepts the high-level process order and the wording abstraction."),
    ("flow", "5-2"): ("action alignment; precedence interpretation", "Code marks one of two required Flow facts FN because its Action anchor is missing, despite complete Flow coverage. AI accepts the approval and rejection continuations in the graph."),
    ("control_node", "5-2"): ("control-node detection", "AI accepts the approve/reject branch. Code does not match its one required logical Control Node; the three related Control Relation FN are downstream of that absent owner."),
    ("control_node", "10-14"): ("control-node detection; semantic severity judgment", "Code detects the one required decision node. AI's low holistic judgment concerns where the alternatives occur and how they route, beyond node presence."),
    ("control_node", "3-6"): ("control-node detection; precedence interpretation", "Code matches all three required logical nodes. AI diagnoses wrong loop return and missing recheck, which depend on their relations and continuation rather than their mere presence."),
    ("control_relation", "5-1"): ("control-relation semantics", "AI regards the three alternatives and continuation as acceptable. Code marks each frozen relation FN+FP because its guard or branch target differs from the frozen fact."),
    ("control_relation", "5-2"): ("control-node detection; control-relation semantics", "AI accepts the approve/reject routing. Code marks the three relations FN because their owning required Control Node was not matched, so these FN are linked to node detection."),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_snapshot(path: Path) -> dict:
    entries = [(str(p.relative_to(path)), sha256(p)) for p in sorted(path.rglob("*")) if p.is_file()]
    payload = json.dumps(entries, separators=(",", ":"), ensure_ascii=False).encode()
    return {"file_count": len(entries), "tree_sha256": hashlib.sha256(payload).hexdigest()}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def text_value(value: Decimal | None) -> str:
    return "" if value is None else str(value)


def decimal_or_none(value: str) -> Decimal | None:
    return None if value == "" else Decimal(value)


def median(values: list[Decimal]) -> Decimal:
    ordered = sorted(values)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def mean(values: list[Decimal]) -> Decimal:
    return sum(values) / len(values)


def average_ranks(values: list[Decimal]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    result = [0.0] * len(values)
    start = 0
    while start < len(order):
        stop = start + 1
        while stop < len(order) and values[order[stop]] == values[order[start]]:
            stop += 1
        rank = ((start + 1) + stop) / 2
        for index in order[start:stop]:
            result[index] = rank
        start = stop
    return result


def percentile(rank: float, n: int) -> float:
    return (rank - 1) / (n - 1) if n > 1 else 0.5


def spearman(x: list[Decimal], y: list[Decimal]) -> float | None:
    if len(x) < 2:
        return None
    rx, ry = average_ranks(x), average_ranks(y)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    numerator = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    denominator = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return numerator / denominator if denominator else None


def source_data() -> tuple[list[dict], list[dict], list[dict], dict, dict, dict]:
    certification = json.loads((CODE / "certification_validation.json").read_text())
    reporting = json.loads((CODE / "reporting_validation.json").read_text())
    ai_manifest = json.loads((AI / "ai_v16_formal_120_manifest.json").read_text())
    ai_hashes = json.loads((AI / "ai_v16_formal_120_hashes.json").read_text())
    assert certification["status"] == "CERTIFIED" and certification["integrity_passed"]
    assert certification["candidate_slots"] == certification["evaluated_candidates"] == 120
    assert reporting["certified_result_status"] == "CERTIFIED" and reporting["certified_count_sets_verified"]
    assert ai_manifest["status"] == "formal_complete" and ai_manifest["completed_candidate_count"] == 120
    assert ai_manifest["prompt_version"] == "ai-evaluator-v2-prompt/1.6"
    assert ai_manifest["schema_version"] == "ai-evaluator-v2/1.1"
    assert ai_hashes["file_count"] == len(ai_hashes["files_sha256"])
    assert all(sha256(ROOT / name) == digest for name, digest in ai_hashes["files_sha256"].items())
    code_identity = read_csv(CODE / "candidate_identity.csv")
    code = read_csv(CODE / "candidate_results.csv")
    ai = read_csv(AI / "ai_v16_formal_120_scores.csv")
    code_json = read_jsonl(CODE / "candidate_results.jsonl")
    ai_json = read_jsonl(AI / "ai_v16_formal_120_results.jsonl")
    identity = lambda row: (row["case_id"], row["candidate_id"])
    pairs = [identity(row) for row in ai]
    assert len(code_identity) == len(code) == len(ai) == len(code_json) == len(ai_json) == 120
    assert len(set(pairs)) == 120
    assert pairs == [identity(row) for row in code_identity] == [identity(row) for row in code]
    assert pairs == [identity(row) for row in code_json] == [identity(row) for row in ai_json]
    assert len({case for case, _ in pairs}) == 40
    assert all(count == 3 for count in Counter(case for case, _ in pairs).values())
    assert pairs == [(row["case_id"], row["candidate_id"]) for row in ai_manifest["candidates"]]
    for code_id, code_row, ai_row, code_raw, ai_raw, source in zip(
        code_identity, code, ai, code_json, ai_json, ai_manifest["candidates"]
    ):
        assert code_id["activity_graph_sha256"] == ai_row["activity_graph_sha256"] == source["activity_graph_sha256"]
        assert sha256(Path(code_id["activity_graph_path"])) == code_id["activity_graph_sha256"]
        assert sha256(ROOT / ai_row["process_text_path"]) == ai_row["process_text_sha256"] == source["process_text_sha256"]
        assert code_row["technical_status"] == "success" and ai_row["technical_status"] == "completed"
        assert Decimal(ai_row["overall_score"]) == Decimal(str(ai_raw["overall_score"]))
        for prefix, key in DIMENSIONS:
            counts = code_raw[key] if prefix == "action" else code_raw[key]["counts"]
            for metric in ("tp", "fp", "fn"):
                assert int(code_row[f"{prefix}_{metric}"]) == counts[metric]
    source_hashes = {
        str(path.relative_to(ROOT)): sha256(path)
        for path in (
            CODE / "candidate_results.csv", CODE / "candidate_results.jsonl", CODE / "candidate_identity.csv",
            CODE / "certification_validation.json", CODE / "reporting_validation.json", CODE / "run_integrity.json",
            AI / "ai_v16_formal_120_scores.csv", AI / "ai_v16_formal_120_results.jsonl",
            AI / "ai_v16_formal_120_manifest.json", AI / "ai_v16_formal_120_hashes.json",
        )
    }
    return code, ai, code_identity, ai_manifest, certification, source_hashes


def component(code: dict[str, str], prefix: str) -> dict[str, str]:
    if prefix == "action":
        assert code["action_f1"] != ""
        return {
            "action_D": code["action_source_denominator"],
            "action_TP": code["action_tp"], "action_FP": code["action_fp"], "action_FN": code["action_fn"],
            "action_precision": code["action_precision"], "action_recall": code["action_recall"],
            "action_F1": code["action_f1"],
        }
    d, tp, fp, fn, ind = (
        int(code[f"{prefix}_source_denominator"]), int(code[f"{prefix}_tp"]),
        int(code[f"{prefix}_fp"]), int(code[f"{prefix}_fn"]),
        int(code[f"{prefix}_indeterminate_alignment_count"]),
    )
    assert d == tp + fn + ind
    official = code[f"{prefix}_f1"]
    coverage = Decimal(code[f"{prefix}_determinate_coverage"])
    assert abs(coverage - (Decimal(tp + fn) / d if d else Decimal(1))) < Decimal("1e-12")
    if d == 0:
        assert ind == tp == fn == 0
        p = r = f1 = None
        status = "not_applicable_zero_source_denominator"
    elif tp + fn == 0:
        assert ind == d
        p = r = f1 = None
        status = "unscorable_all_required_facts_indeterminate"
    else:
        # The certified reporting layer uses P=TP/(TP+FP), R=TP/(TP+FN),
        # F1=2PR/(P+R). The Code evaluator's established no-prediction
        # convention is P=F1=0 when scorable FN>0.
        p = Decimal(tp) / (tp + fp) if tp + fp else Decimal(0)
        r = Decimal(tp) / (tp + fn)
        f1 = 2 * p * r / (p + r) if p + r else Decimal(0)
        status = "official_numeric" if ind == 0 else "official_null_indeterminate"
    if ind:
        assert official == ""
    else:
        assert official != ""
        if d:
            assert f1 is not None and abs(f1 - Decimal(official)) < Decimal("1e-12")
    return {
        f"{prefix}_D": str(d), f"{prefix}_TP": str(tp), f"{prefix}_FP": str(fp),
        f"{prefix}_FN": str(fn), f"{prefix}_I": str(ind),
        f"{prefix}_coverage": code[f"{prefix}_determinate_coverage"],
        f"{prefix}_scorable_precision": text_value(p),
        f"{prefix}_scorable_recall": text_value(r),
        f"{prefix}_scorable_F1": text_value(f1),
        f"{prefix}_official_precision": code[f"{prefix}_precision"],
        f"{prefix}_official_recall": code[f"{prefix}_recall"],
        f"{prefix}_official_F1": official,
        f"{prefix}_official_scalar_status": status,
    }


def master_rows(code: list[dict], ai: list[dict], identities: list[dict]) -> list[dict]:
    rows = []
    for c, a, identity in zip(code, ai, identities):
        row = {
            "case_id": a["case_id"], "candidate_id": a["candidate_id"],
            "activity_graph_sha256": identity["activity_graph_sha256"],
            "ai_overall_score": a["overall_score"],
            "ai_action_assessment": a["action_assessment"],
            "ai_flow_assessment": a["flow_assessment"],
            "ai_control_flow_assessment": a["control_flow_assessment"],
            "ai_main_error_type": a["main_error_type"], "ai_severity": a["severity"],
            "ai_uncertainty_flag": a["uncertainty_flag"],
            "ai_human_review_flag": a["human_review_flag"],
            "code_candidate_status": c["candidate_status"],
            "code_technical_status": c["technical_status"],
            "code_unresolved_source_question_count": c["unresolved_source_question_count"],
            "code_review_flags": c["review_flags"],
        }
        for prefix, _ in DIMENSIONS:
            row.update(component(c, prefix))
        rows.append(row)
    return rows


def rankings(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    ai_scores = [Decimal(row["ai_overall_score"]) for row in rows]
    global_ranks = average_ranks(ai_scores)
    # Keep the full joined judgments next to their sortable rank positions.
    ranked = [
        {**row, "ai_rank_all_120": str(rank),
         "ai_percentile_all_120": f"{percentile(rank, 120):.12f}"}
        for row, rank in zip(rows, global_ranks)
    ]
    correlations = []
    for prefix, label in DIMENSIONS:
        metric_key = f"{prefix}_F1" if prefix == "action" else f"{prefix}_scorable_F1"
        indices = [i for i, row in enumerate(rows) if row[metric_key] != ""]
        x = [ai_scores[i] for i in indices]
        y = [Decimal(rows[i][metric_key]) for i in indices]
        ar, cr = average_ranks(x), average_ranks(y)
        for j, index in enumerate(indices):
            ap, cp = percentile(ar[j], len(indices)), percentile(cr[j], len(indices))
            ranked[index].update({
                f"ai_rank_{prefix}_pairwise": str(ar[j]),
                f"ai_percentile_{prefix}_pairwise": f"{ap:.12f}",
                f"code_{prefix}_rank": str(cr[j]),
                f"code_{prefix}_percentile": f"{cp:.12f}",
                f"abs_rank_gap_{prefix}": f"{abs(ap - cp):.12f}",
            })
        for index in set(range(120)) - set(indices):
            ranked[index].update({
                f"ai_rank_{prefix}_pairwise": "", f"ai_percentile_{prefix}_pairwise": "",
                f"code_{prefix}_rank": "", f"code_{prefix}_percentile": "",
                f"abs_rank_gap_{prefix}": "",
            })
        applicable = [row for row in rows if prefix == "action" or int(row[f"{prefix}_D"]) > 0]
        usable_coverage = [Decimal(rows[i][f"{prefix}_coverage"]) for i in indices] if prefix != "action" else [Decimal(1)] * len(indices)
        usable_i = [int(rows[i][f"{prefix}_I"]) for i in indices] if prefix != "action" else [0] * len(indices)
        correlations.append({
            "dimension": label, "code_metric": metric_key, "usable_pairs_N": len(indices),
            "spearman_rho": "" if (rho := spearman(x, y)) is None else f"{rho:.12f}",
            "missing_or_NA_excluded": 120 - len(indices),
            "pairwise_complete_only": "True", "applicable_candidates": len(applicable),
            "coverage_mean_usable": text_value(mean(usable_coverage)),
            "coverage_min_usable": text_value(min(usable_coverage)),
            "coverage_max_usable": text_value(max(usable_coverage)),
            "indeterminate_count_usable_total": sum(usable_i),
            "candidates_with_indeterminate_usable": sum(i > 0 for i in usable_i),
            "coverage_mean_all_applicable": text_value(mean([Decimal(row[f"{prefix}_coverage"]) for row in applicable])) if prefix != "action" else "1",
            "indeterminate_count_all_applicable_total": sum(int(row[f"{prefix}_I"]) for row in applicable) if prefix != "action" else 0,
        })
    for row, original in zip(ranked, rows):
        for prefix, _ in DIMENSIONS:
            metric = f"{prefix}_F1" if prefix == "action" else f"{prefix}_scorable_F1"
            row[metric] = original[metric]
            if prefix != "action":
                row[f"{prefix}_coverage"] = original[f"{prefix}_coverage"]
                row[f"{prefix}_I"] = original[f"{prefix}_I"]
        row["ai_severity"] = original["ai_severity"]
        row["ai_main_error_type"] = original["ai_main_error_type"]
        row["ai_uncertainty_flag"] = original["ai_uncertainty_flag"]
        row["ai_human_review_flag"] = original["ai_human_review_flag"]
    return ranked, correlations


def descriptive(rows: list[dict]) -> list[dict]:
    output = []
    def add(variable: str, group: str, selected: list[dict], metric_values: list[Decimal]) -> None:
        scores = [Decimal(row["ai_overall_score"]) for row in selected]
        output.append({
            "variable": variable, "group": group, "candidate_count": len(selected),
            "metric_min": text_value(min(metric_values)) if metric_values else "",
            "metric_max": text_value(max(metric_values)) if metric_values else "",
            "ai_score_min": text_value(min(scores)) if scores else "",
            "ai_score_median": text_value(median(scores)) if scores else "",
            "ai_score_mean": text_value(mean(scores)) if scores else "",
            "ai_score_max": text_value(max(scores)) if scores else "",
        })
    for prefix, label in DIMENSIONS:
        metric = f"{prefix}_F1" if prefix == "action" else f"{prefix}_scorable_F1"
        usable = [row for row in rows if row[metric] != ""]
        central = median([Decimal(row[metric]) for row in usable])
        for name, predicate in (
            ("below_median_scorable_F1", lambda value: value < central),
            ("at_median_scorable_F1", lambda value: value == central),
            ("above_median_scorable_F1", lambda value: value > central),
        ):
            selected = [row for row in usable if predicate(Decimal(row[metric]))]
            add(label + " F1", name, selected, [Decimal(row[metric]) for row in selected])
        if prefix == "action":
            continue
        applicable = [row for row in rows if int(row[f"{prefix}_D"]) > 0]
        for name, predicate in (("I=0", lambda value: value == 0), ("I>0", lambda value: value > 0)):
            selected = [row for row in applicable if predicate(int(row[f"{prefix}_I"]))]
            add(label + " indeterminate count", name, selected, [Decimal(row[f"{prefix}_I"]) for row in selected])
        cover_med = median([Decimal(row[f"{prefix}_coverage"]) for row in applicable])
        for name, predicate in (
            ("below_median_coverage", lambda value: value < cover_med),
            ("at_median_coverage", lambda value: value == cover_med),
            ("above_median_coverage", lambda value: value > cover_med),
        ):
            selected = [row for row in applicable if predicate(Decimal(row[f"{prefix}_coverage"]))]
            add(label + " coverage", name, selected, [Decimal(row[f"{prefix}_coverage"]) for row in selected])
    return output


def oracle(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict], dict]:
    cases = list(dict.fromkeys(row["case_id"] for row in rows))
    case_rows, ai_rows, code_rows = [], [], []
    counts = Counter()
    dimension_overlap = Counter()
    for case_id in cases:
        group = [row for row in rows if row["case_id"] == case_id]
        assert len(group) == 3
        ai_max = max(Decimal(row["ai_overall_score"]) for row in group)
        ai_best = {row["candidate_id"] for row in group if Decimal(row["ai_overall_score"]) == ai_max}
        scores = {row["candidate_id"]: row["ai_overall_score"] for row in group}
        best_sets = {}
        applicable = []
        unresolved = []
        for prefix, label in DIMENSIONS:
            metric = f"{prefix}_F1" if prefix == "action" else f"{prefix}_scorable_F1"
            if prefix != "action" and all(int(row[f"{prefix}_D"]) == 0 for row in group):
                status, best, maximum = "not_applicable_no_source_facts", set(), None
            else:
                assert prefix == "action" or all(int(row[f"{prefix}_D"]) > 0 for row in group)
                applicable.append(prefix)
                usable = [row for row in group if row[metric] != ""]
                if not usable:
                    status, best, maximum = "applicable_but_unscorable", set(), None
                    unresolved.append(prefix)
                else:
                    maximum = max(Decimal(row[metric]) for row in usable)
                    best = {row["candidate_id"] for row in usable if Decimal(row[metric]) == maximum}
                    status = "scorable"
            best_sets[prefix] = best
            overlap = bool(ai_best & best) if status == "scorable" else None
            if status == "scorable":
                dimension_overlap[f"{prefix}_applicable"] += 1
                dimension_overlap[f"{prefix}_overlap"] += bool(overlap)
            code_rows.append({
                "analysis_label": LABEL, "case_id": case_id, "dimension": label,
                "applicability_status": status,
                "best_candidates_json": json.dumps(sorted(best)),
                "best_scorable_F1": text_value(maximum),
                "candidate_F1_json": json.dumps({row["candidate_id"]: row[metric] or None for row in group}),
                "candidate_coverage_json": json.dumps({row["candidate_id"]: (row[f"{prefix}_coverage"] if prefix != "action" else "1") for row in group}),
                "candidate_indeterminate_json": json.dumps({row["candidate_id"]: (row[f"{prefix}_I"] if prefix != "action" else "0") for row in group}),
                "AI_best_overlaps_dimension_best": "" if overlap is None else str(overlap),
            })
        joint = set.intersection(*(best_sets[prefix] for prefix in applicable)) if applicable else set()
        if unresolved:
            assert not joint
            joint_status = "NO UNIQUE CODE OVERALL BEST: applicable dimension unscorable"
            counts["joint_unscorable"] += 1
        elif joint:
            joint_status = "CODE JOINT-BEST SET"
            counts["joint_best"] += 1
            counts["joint_tied"] += len(joint) > 1
        else:
            joint_status = "NO UNIQUE CODE OVERALL BEST: dimension-best sets do not intersect"
            counts["joint_conflict"] += 1
        counts["ai_unique"] += len(ai_best) == 1
        counts["ai_tied"] += len(ai_best) > 1
        joint_overlap = bool(ai_best & joint)
        counts["ai_joint_overlap"] += joint_overlap
        ai_rows.append({
            "analysis_label": LABEL, "case_id": case_id,
            "AI_best_candidates_json": json.dumps(sorted(ai_best)),
            "AI_best_score": str(ai_max),
            "all_three_AI_scores_json": json.dumps(scores),
            "AI_best_unique": str(len(ai_best) == 1),
        })
        case = {
            "analysis_label": LABEL, "case_id": case_id,
            "AI_best_candidates_json": json.dumps(sorted(ai_best)),
            "AI_best_score": str(ai_max),
            "all_three_AI_scores_json": json.dumps(scores),
            "Code_joint_best_candidates_json": json.dumps(sorted(joint)),
            "Code_joint_best_status": joint_status,
            "AI_best_overlaps_Code_joint_best": str(joint_overlap),
            "AI_best_all_within_Code_joint_best": str(bool(joint) and ai_best <= joint),
            "applicable_Code_dimensions_json": json.dumps(applicable),
            "unscorable_applicable_Code_dimensions_json": json.dumps(unresolved),
        }
        for prefix, _ in DIMENSIONS:
            case[f"{prefix}_best_candidates_json"] = json.dumps(sorted(best_sets[prefix]))
            val = next(row for row in code_rows[::-1] if row["case_id"] == case_id and row["dimension"] == dict(DIMENSIONS)[prefix])
            case[f"AI_best_overlaps_{prefix}_best"] = val["AI_best_overlaps_dimension_best"]
        case_rows.append(case)
    counts["cases"] = len(cases)
    counts["no_joint_best"] = counts["joint_unscorable"] + counts["joint_conflict"]
    return case_rows, ai_rows, code_rows, {"counts": dict(counts), "dimension_overlap": dict(dimension_overlap)}


def disagreement_report(rows: list[dict], ranked: list[dict], top_n: int = 5) -> str:
    lines = [
        "# Largest Code versus AI rank disagreements", "",
        "These are descriptive differences between related but non-identical constructs. Percentiles use average ranks for ties, calculated on each dimension's pairwise-complete candidates. A larger gap does not adjudicate either evaluator.", "",
    ]
    for prefix, label in DIMENSIONS:
        gap_key = f"abs_rank_gap_{prefix}"
        ordered = sorted(
            [(row, rank) for row, rank in zip(rows, ranked) if rank[gap_key] != ""],
            key=lambda item: (-float(item[1][gap_key]), item[0]["case_id"], item[0]["candidate_id"]),
        )
        cutoff = Decimal(ordered[min(top_n, len(ordered)) - 1][1][gap_key])
        candidates = [item for item in ordered if Decimal(item[1][gap_key]) >= cutoff]
        lines += [f"## {label}", "", "The five largest available rank gaps, including all ties at the cutoff, are shown. The full sortable table retains every candidate and every dimension.", ""]
        for row, rank in candidates:
            assessment_key = {"action": "ai_action_assessment", "flow": "ai_flow_assessment", "control_node": "ai_control_flow_assessment", "control_relation": "ai_control_flow_assessment"}[prefix]
            assessment = json.loads(row[assessment_key])
            metric_key = f"{prefix}_F1" if prefix == "action" else f"{prefix}_scorable_F1"
            detail = (
                f"Code {label}: TP={row[f'{prefix}_TP']}, FP={row[f'{prefix}_FP']}, FN={row[f'{prefix}_FN']}, "
                f"scorable F1={row[metric_key]}"
            )
            if prefix != "action":
                detail += f", D={row[f'{prefix}_D']}, I={row[f'{prefix}_I']}, coverage={row[f'{prefix}_coverage']}, official scalar status={row[f'{prefix}_official_scalar_status']}"
            category, reading = REVIEW_NOTES[(prefix, row["case_id"])]
            lines += [
                f"### {row['case_id']} / {row['candidate_id']} — rank gap {rank[gap_key]}", "",
                f"- AI: overall {row['ai_overall_score']}, {row['ai_severity']} severity, {row['ai_main_error_type']}. {assessment['summary']}",
                f"- {detail}.",
                f"- Coverage/indeterminate context: {'Not applicable to Action; all Action facts are determinate.' if prefix == 'action' else ('Indeterminate facts may limit the Code observation.' if int(row[f'{prefix}_I']) else 'All required facts in this dimension are determinate.')}",
                f"- Likely source category: {category}.",
                f"- Descriptive reading: {reading} This does not adjudicate which evaluator is correct.", "",
            ]
    return "\n".join(lines)


def summary_report(correlations: list[dict], descriptive_rows: list[dict], ranked: list[dict], oracle_stats: dict) -> str:
    lines = [
        "# Certified Code V3.1 versus frozen AI v1.6: 120 candidates", "",
        "The AI overall score is a holistic semantic judgment. Code V3.1 reports four separate dimensions: Action, Flow, Control Node, and Control Relation. The latter three also report determinate coverage and indeterminate counts. No Code overall score is defined or calculated here.", "",
        "## Candidate-level associations", "",
        "Tie-aware Spearman rho uses average ranks and only candidates with both values. Null and non-applicable Code dimensions are excluded. Scorable F1 is derived from certified TP/FP/FN counts using the certified reporting formula; official null scalars remain null in the master table.", "",
        "| Code dimension | N | Spearman rho | Excluded | Mean coverage, usable | Usable candidates with I |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in correlations:
        lines.append(f"| {row['dimension']} | {row['usable_pairs_N']} | {row['spearman_rho']} | {row['missing_or_NA_excluded']} | {Decimal(row['coverage_mean_usable']):.3f} | {row['candidates_with_indeterminate_usable']} |")
    lines += [
        "", "Pairwise completeness changes N by dimension. Each Control dimension excludes 21 no-control candidate slots with D=0 and three slots for which every required fact is indeterminate. The corresponding official Code scalar remains visible separately in the master table. These associations describe ranking patterns; the AI score and Code F1 are not interchangeable measurements.", "",
        "## AI score variation with Code metrics and coverage", "",
        "The following descriptive groups use each applicable dimension's observed median F1 or coverage, and the natural distinction between zero and positive indeterminate counts. Empty groups remain empty; no significance or quality threshold is applied. Full min, median, mean, and max values are in `code_vs_ai_120_descriptive.csv`.", "",
        "| Variable | Group | N | Median AI score | Mean AI score |",
        "|---|---|---:|---:|---:|",
    ]
    for row in descriptive_rows:
        lines.append(f"| {row['variable']} | {row['group']} | {row['candidate_count']} | {row['ai_score_median']} | {Decimal(row['ai_score_mean']):.4f} |" if row['candidate_count'] else f"| {row['variable']} | {row['group']} | 0 | N/A | N/A |")
    lines += [
        "", "## Disagreement review", "",
        "The sortable table contains AI and Code percentile positions and four separate absolute rank gaps. The largest available gaps per dimension are documented in `code_vs_ai_120_largest_disagreements.md`. No direct AI-minus-Code score difference or combined gap is calculated.", "",
        "## Secondary oracle analysis", "",
        f"**{LABEL}**", "",
        f"All {oracle_stats['counts']['cases']} cases are summarized separately by AI maximum and by each applicable Code dimension. The Code joint-best set is the intersection of dimension-best sets, with unscorable applicable dimensions preventing a joint-best finding. It is a post-hoc reference summary, not automatic selection performance.", "",
        "## Integrity", "",
        "All 120 candidate identities and ActivityGraph hashes matched. Certified Code results and frozen AI results were read only. No evaluator was rerun, no Code composite was constructed, no null or non-applicable value was substituted with zero, and continuous AI scores were copied exactly.", "",
    ]
    return "\n".join(lines)


def write_outputs(out: Path) -> None:
    before = {"code": tree_snapshot(CODE), "ai": tree_snapshot(AI)}
    code, ai, identities, ai_manifest, certification, source_hashes = source_data()
    rows = master_rows(code, ai, identities)
    ranked, correlations = rankings(rows)
    descriptions = descriptive(rows)
    cases, ai_cases, code_cases, oracle_stats = oracle(rows)
    assert len(rows) == len(ranked) == 120 and len(cases) == len(ai_cases) == 40 and len(code_cases) == 160
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir()
    write_csv(out / "code_vs_ai_120_master.csv", rows, list(rows[0]))
    write_csv(out / "code_vs_ai_120_correlations.csv", correlations, list(correlations[0]))
    write_csv(out / "code_vs_ai_120_disagreement_ranks.csv", ranked, list(ranked[0]))
    write_csv(out / "code_vs_ai_120_descriptive.csv", descriptions, list(descriptions[0]))
    (out / "code_vs_ai_120_largest_disagreements.md").write_text(disagreement_report(rows, ranked), encoding="utf-8")
    (out / "code_vs_ai_120_summary.md").write_text(summary_report(correlations, descriptions, ranked, oracle_stats), encoding="utf-8")
    write_csv(out / "oracle_best_of_three_40_cases.csv", cases, list(cases[0]))
    write_csv(out / "oracle_best_of_three_ai_summary.csv", ai_cases, list(ai_cases[0]))
    write_csv(out / "oracle_best_of_three_code_dimension_summary.csv", code_cases, list(code_cases[0]))
    counts, overlap = oracle_stats["counts"], oracle_stats["dimension_overlap"]
    oracle_lines = [
        "# Oracle best of three: 40 cases", "", f"**{LABEL}**", "",
        "AI-best is the maximum frozen AI score. Each Code dimension has its own best set among scorable candidates. The Code joint-best set is the intersection of the best sets for all applicable dimensions. Ties are retained. A dimension with D=0 is non-applicable; an applicable dimension with no scorable candidate blocks a joint-best finding.", "",
        f"- Cases: {counts['cases']}", f"- Unique AI-best cases: {counts['ai_unique']}",
        f"- AI-tied-best cases: {counts['ai_tied']}",
        f"- Cases with a Code joint-best candidate/set: {counts['joint_best']}",
        f"- Cases with no Code joint-best intersection: {counts['no_joint_best']}",
        f"  - Due to an applicable but unscorable dimension: {counts['joint_unscorable']}",
        f"  - Due to dimension-best sets not intersecting: {counts['joint_conflict']}",
        f"- Cases with a tied Code joint-best set: {counts['joint_tied']}",
        f"- Cases where an AI-best candidate belongs to the Code joint-best set: {counts['ai_joint_overlap']}", "",
        "For tied AI-best sets, agreement means at least one AI-best candidate is in the relevant Code-best set. The case table also records whether all AI-best candidates are in the Code joint-best set.", "",
        "## AI-best overlap by Code dimension", "",
        "| Dimension | Scorable cases | Cases with any AI-best overlap |", "|---|---:|---:|",
    ]
    for prefix, label in DIMENSIONS:
        oracle_lines.append(f"| {label} | {overlap.get(prefix + '_applicable', 0)} | {overlap.get(prefix + '_overlap', 0)} |")
    oracle_lines += ["", "These are post-hoc oracle summaries and must not be interpreted as deployable automatic candidate selection performance.", ""]
    (out / "oracle_best_of_three_agreement_summary.md").write_text("\n".join(oracle_lines), encoding="utf-8")
    after = {"code": tree_snapshot(CODE), "ai": tree_snapshot(AI)}
    assert before == after, "Source results changed during comparison"
    main_files = [p for p in out.iterdir() if p.name.startswith("code_vs_ai_120_") and p.is_file()]
    oracle_files = [p for p in out.iterdir() if p.name.startswith("oracle_best_of_three_") and p.is_file()]
    common = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_certification_status": certification["status"],
        "ai_formal_status": ai_manifest["status"],
        "code_source_directory": str(CODE), "ai_source_directory": str(AI),
        "source_file_sha256": source_hashes, "source_tree_snapshots_before_and_after": before,
        "comparison_script_path": str(Path(__file__).relative_to(ROOT)),
        "comparison_script_sha256": sha256(Path(__file__)),
        "candidate_count": 120, "case_count": 40, "candidates_per_case": 3,
        "activity_graph_hashes_match": True, "join_one_to_one": True,
        "evaluators_rerun": False, "frozen_results_changed": False,
        "code_composite_score_created": False,
        "null_or_NA_replaced_with_zero": False,
    }
    write_json(out / "code_vs_ai_120_manifest.json", {
        **common, "analysis_kind": "PRIMARY_120_CANDIDATE_COMPARISON",
        "rank_method": "average tied ranks; percentile=(average_rank-1)/(pairwise_N-1); pairwise-complete per dimension",
        "correlation_method": "Spearman Pearson correlation of average tied ranks; no significance threshold",
        "scorable_f1_method": "certified reporting formula on each candidate's determinate TP/FP/FN; D=0 and all-I are N/A; established no-prediction P/F1=0 when scorable FN>0",
        "output_sha256": {p.name: sha256(p) for p in sorted(main_files)},
    })
    write_json(out / "oracle_best_of_three_manifest.json", {
        **common, "analysis_kind": "SECONDARY_POST_HOC_ORACLE_BEST_OF_THREE",
        "analysis_label": LABEL,
        "ai_best_method": "maximum exact frozen AI score per case, retaining ties",
        "code_best_method": "separate maxima of each applicable Code scorable F1, retaining ties; no composite",
        "joint_best_method": "intersection of best sets across applicable Code dimensions; any all-unscorable applicable dimension prevents a joint-best finding",
        "ai_tie_agreement_method": "any AI-best member intersects the Code-best set; all-member joint containment reported separately",
        "aggregate_counts": counts, "dimension_overlap_counts": overlap,
        "output_sha256": {p.name: sha256(p) for p in sorted(oracle_files)},
    })
    print(json.dumps({"output": str(out), "correlations": correlations, "oracle_counts": counts}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with localcontext() as context:
        context.prec = 48
        write_outputs(args.output.expanduser().resolve())


if __name__ == "__main__":
    main()
