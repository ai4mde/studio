"""Build and source-validate the approved V3.1 Control Fact Inventory amendment.

This script reads only V3.0 frozen facts, reviewed source inventories, process text,
reference evidence, and the unchanged V2 Action implementation. It never reads
generated candidates or evaluation results. It refuses to overwrite a freeze.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
V30 = HERE / "frozen"
V31 = HERE / "v3_1" / "frozen"
SOURCE = Path(__file__).resolve().parents[5] / "studio-semantic-v2/evaluation/friedrich_semantic_v2/inventories/corpus_v1/cases"
ACTION_CODE = Path(__file__).resolve().parents[5] / "studio-semantic-v2/evaluation"
CASES = ("4-1", "9-6", "2-2", "6-3", "10-8", "9-1")
VERSION = "v3.1-control-facts-frozen-20260924"
CONTRACT_VERSION = "v3.1-cfi-anchor-evidence-1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(path: Path) -> str:
    return sha(path.read_bytes())


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def item(items: list[dict], fact_id: str) -> dict:
    return next(x for x in items if x["fact_id"] == fact_id)


def span(source_text: str, excerpt: str) -> dict:
    start = source_text.find(excerpt)
    if start < 0 or source_text.find(excerpt, start + 1) >= 0:
        raise ValueError(f"source excerpt missing or nonunique: {excerpt!r}")
    return {"start_offset": start, "end_offset": start + len(excerpt), "exact_excerpt": excerpt}


def source_text(case_id: str, case: dict) -> str:
    return (SOURCE / case_id / "process_text.txt").read_bytes().decode(case["source_encoding"])


def amend_4_1(case: dict) -> None:
    nodes, relations = case["control_nodes"], case["control_relations"]
    join = item(nodes, "CF-4-1-N04")
    join["anchor_action_ids"] = ["SU-4-1-31"]
    join["control_anchor_evidence"] = [{
        "kind": "gateway_guard",
        "source_predicate": "both first- and second-intaker patient meetings have occurred",
        "required_structural_roles": ["first_meeting_completion_input", "second_meeting_completion_input", "listing_after_join"],
        "source_span": join["source_spans"][0],
        "action_context_ids": ["SU-4-1-31"],
        "action_context_is_completion_proxy": False,
    }]
    join["notes"] = "The source explicitly requires both meetings before listing; examination and dictaphone recording are not meeting-completion proxies."
    for fact_id, boundary in (("CF-4-1-R06", "first_intaker_meeting_completion"),
                              ("CF-4-1-R08", "second_intaker_meeting_completion")):
        relation = item(relations, fact_id)
        relation["incoming_action_ids"] = []
        relation["incoming_boundary"] = boundary
        relation["control_anchor_evidence"] = [{
            "kind": "gateway_guard",
            "source_predicate": boundary.replace("_", " ") + " before patient listing",
            "required_structural_roles": [boundary, "listing_after_join"],
            "source_span": relation["source_spans"][0],
        }]
        relation["notes"] = "Source-grounded meeting-completion boundary; no standalone reviewed Action unit is required."
        if fact_id.endswith("R08"):
            relation["status"] = "required"
            relation.pop("reason_code", None)
    case["unresolved_facts"] = [
        q for q in case["unresolved_facts"]
        if "CF-4-1-R08" not in q.get("affected_fact_ids", [])
    ]
    case["review_notes"].append(
        "V3.1: both meeting-completion inputs are required Control boundaries grounded in the explicit source conjunction; SU-4-1-25 and SU-4-1-28 are not completion proxies."
    )


def amend_9_6(case: dict) -> None:
    occurrence_ids = ["SO-9-6-23", "SO-9-6-24"]
    for fact_id in ("CF-9-6-N04", "CF-9-6-R11", "CF-9-6-R12"):
        fact = item(case["control_nodes"] + case["control_relations"], fact_id)
        fact["target_occurrence_ids"] = occurrence_ids
        fact["control_anchor_evidence"] = [{
            "kind": "occurrence_anchor_set",
            "semantic_unit_ids": ["SU-9-6-13"],
            "occurrence_ids": occurrence_ids,
            "occurrence_roles": {"SO-9-6-23": "initial", "SO-9-6-24": "repeated"},
            "assignment_rule": "match the combine occurrence in the same design cycle as both incoming revised designs",
            "source_span": fact["source_spans"][0],
        }]
    for fact_id in ("CF-9-6-R09", "CF-9-6-R10"):
        fact = item(case["control_relations"], fact_id)
        fact["exclusion_scope"] = "before_interrupted_design_branch_restarts"
        fact["notes"] = (fact.get("notes", "") + " V3.1: SU-9-6-13 is excluded only before the interrupted branch restarts; combining is required after both revisions complete.").strip()


def amend_2_2(case: dict, text: str) -> None:
    fork = item(case["control_nodes"], "CF-2-2-N06")
    fork["purpose"] = "Grid-operator meter-data distribution and grid-operator final-billing work proceed concurrently"
    fork["anchor_action_ids"] = ["SU-2-2-28", "SU-2-2-29", "SU-2-2-30", "SU-2-2-31"]
    fork["control_anchor_evidence"] = [
        {"kind": "anchor_set", "role": "meter_data_distribution_branch",
         "semantic_unit_ids": ["SU-2-2-28", "SU-2-2-29"],
         "mapping_cardinalities": ["one_to_one", "many_to_one", "one_to_many"],
         "source_span": span(text, "the grid operator transmits the power meter data to the customer service and the old\nsupplier")},
        {"kind": "anchor_set", "role": "grid_operator_billing_branch",
         "semantic_unit_ids": ["SU-2-2-30", "SU-2-2-31"],
         "mapping_cardinalities": ["one_to_one", "many_to_one", "one_to_many"],
         "source_span": span(text, "At the same time, the grid\noperator computes the final billing based on the meter data and sends it to the old supplier.")},
    ]
    fork["notes"] = "Old-supplier creation and sending (SU-2-2-32/33) are downstream billing meanings, not evidence of this Fork's two concurrent grid-operator branches."
    r10 = item(case["control_relations"], "CF-2-2-R10")
    r11 = item(case["control_relations"], "CF-2-2-R11")
    r10["target_action_ids"] = ["SU-2-2-28", "SU-2-2-29"]
    r11["target_action_ids"] = ["SU-2-2-30", "SU-2-2-31"]
    r10["control_anchor_evidence"] = [fork["control_anchor_evidence"][0]]
    r11["control_anchor_evidence"] = [fork["control_anchor_evidence"][1]]
    case["unresolved_facts"].append({
        "status": "unresolved",
        "question": "Does old-supplier final-billing creation/sending overlap the grid-operator meter-data and billing branches, or follow receipt of grid-operator billing?",
        "reason_code": "cross_path_scope_unspecified",
        "affected_fact_ids": [],
        "source_spans": [span(text, "Likewise the old supplier creates and sends the final billing to the customer.")],
        "coverage_kind": "source_scope_question",
        "fp_scope": "abstain_on_unstated_old_supplier_timing",
    })


def amend_6_3(case: dict) -> None:
    fact = item(case["control_nodes"], "CF-6-3-N01")
    fact["control_anchor_evidence"] = [{
        "kind": "gateway_guard",
        "source_predicate": "whether any parts are missing and must be procured",
        "required_structural_roles": ["decision_about_missing_parts", "procure_if_missing", "skip_procurement_if_not_missing"],
        "source_span": fact["source_spans"][0],
        "action_anchor_is_optional_for_control": True,
    }]


def amend_10_8(case: dict) -> None:
    fact = item(case["control_nodes"], "CF-10-8-N01")
    fact["control_anchor_evidence"] = [{
        "kind": "gateway_guard",
        "source_predicate": "verification of deregistration routes to rejection or preliminary confirmation",
        "required_structural_roles": ["deregistration_verification_meaning", "rejection_route", "preliminary_confirmation_route"],
        "source_span": fact["source_spans"][0],
        "action_anchor_is_optional_for_control": True,
    }]


def amend_9_1(case: dict, text: str) -> dict:
    node = item(case["control_nodes"], "CF-9-1-N04")
    node["purpose"] = "Trigger supervisor alert when work covered by the 2:30 pm deadline remains incomplete"
    node["anchor_action_ids"] = ["SU-9-1-08"]
    node["source_spans"] = [span(text, "All of this must be completed by 2:30 pm, if it is not, then an\nalert should be sent to the supervisor.")]
    node["control_anchor_evidence"] = [{
        "kind": "gateway_guard",
        "source_predicate": "work covered by the 2:30 pm deadline is incomplete",
        "required_structural_roles": ["deadline_decision", "missed_deadline_alert_branch"],
        "source_span": node["source_spans"][0],
        "action_context_ids": ["SU-9-1-08"],
        "exact_preceding_work_scope": "unresolved_source_scope",
    }]
    node["notes"] = "SU-9-1-07 is researcher-ambiguous and is not eligible as a Control anchor. The explicit missed-deadline predicate and SU-9-1-08 alert outcome support this narrower required fact."
    r04 = item(case["control_relations"], "CF-9-1-R04")
    r04["source_spans"] = [node["source_spans"][0]]
    r04["control_anchor_evidence"] = [{
        "kind": "gateway_guard",
        "source_predicate": "misses the 2:30 pm deadline",
        "required_structural_roles": ["missed_deadline_guard", "alert_to_supervisor_outcome"],
        "source_span": node["source_spans"][0],
        "action_context_ids": ["SU-9-1-08"],
    }]
    retired = deepcopy(item(case["control_relations"], "CF-9-1-R05"))
    case["control_relations"] = [x for x in case["control_relations"] if x["fact_id"] != "CF-9-1-R05"]
    case["unresolved_facts"].append({
        "status": "unresolved",
        "question": "Which preceding activities are covered by 'All of this' in the 2:30 pm deadline?",
        "reason_code": "deadline_scope_ambiguous",
        "affected_fact_ids": ["CF-9-1-N04", "CF-9-1-R04"],
        "source_spans": [span(text, "All of this must be completed by 2:30 pm,")],
        "coverage_kind": "source_scope_question",
        "fp_scope": "abstain_on_exact_deadline_scope",
    })
    case["review_notes"].append(
        "V3.1: CF-9-1-R05 is retired because later CRM checking follows report completion, not an asserted on-time branch; source scope of 'All of this' remains unresolved."
    )
    return retired


def amend_contract(old: dict) -> dict:
    contract = deepcopy(old)
    contract["contract_version"] = CONTRACT_VERSION
    contract["amendment_parent_contract_version"] = old["contract_version"]
    contract["fact_statuses"]["required"]["eligible_for_indeterminate_alignment"] = True
    contract["control_anchor_evidence_contract"] = {
        "evidence_classes": ["action_anchor", "occurrence_anchor_set", "gateway_guard"],
        "accepted_action_mappings_locked_first": True,
        "control_only_text_only_eligibility": "review_state accepted or modified; at least one source-supported text_only occurrence; Control anchor only",
        "researcher_ambiguous_automatic_eligibility": False,
        "action_scoring_counts_and_mappings_mutable": False,
        "matching_policy": "reuse existing V2 semantic compatibility, source grounding, and accepted similarity rules; no new arbitrary threshold; a separate auditable adapter is required because text_only units lack V2 projected reference Action nodes",
        "occurrence_policy": "specific occurrences require matching branch, cycle, recurrence role, and source-supported order; unit-level alignment alone is insufficient",
        "mixed_occurrence_policy": "a text_only occurrence may receive a Control-only occurrence alignment even when another occurrence of the same semantic unit has an accepted V2 Action mapping; that V2 mapping remains locked to its own occurrence",
        "anchor_set_policy": "many-to-one and one-to-many mappings may supply one compound anchor set only when every claimed semantic component is supported; a compound label does not establish an internal Control boundary",
        "gateway_guard_policy": "explicit source predicate plus generated logical control node, guard semantics, and required routing may establish Control evidence without a standalone generated Action; a bare gateway is insufficient and no gateway becomes an Action TP",
        "control_fact_matching": "test only source-registered evidence modes and structural roles; Action context alone never earns Control TP",
        "conflict_policy": "Control-only mappings cannot displace accepted V2 Action mappings; competing non-equivalent mappings require occurrence/structure resolution or indeterminate alignment",
        "genuine_absence_policy": "FN only after all source-permitted observable evidence modes are tested and none is present",
    }
    contract["candidate_scoring_state_contract"] = {
        "required_fact_states": ["TP", "FN", "indeterminate_alignment"],
        "source_side_unresolved_is_candidate_state": False,
        "fixed_denominator_equation": "D = TP + FN + indeterminate_alignment_count",
        "candidate_specific_required_fact_removal_allowed": False,
        "candidate_specific_required_to_unresolved_allowed": False,
        "missing_evidence": "FN",
        "correct_evidence": "TP",
        "source_contradiction": "FN plus applicable generated FP under existing substitution and single-wrong-outcome policy",
        "evaluator_indeterminacy": "separate flag; neither TP nor FN until resolved; D unchanged",
        "component_metrics_when_indeterminate_count_positive": "precision, recall, and F1 null; report TP, FN, FP, D, indeterminate count, determinate coverage, and recall interval; no partial-score ranking",
        "determinate_coverage": "(TP + FN) / D",
        "recall_interval": "[TP / D, (TP + indeterminate_alignment_count) / D]",
        "source_unresolved": "frozen before candidate evaluation; excluded from TP/FP/FN and reported separately",
    }
    contract["coverage_reporting"]["report_separately"].extend([
        "indeterminate_alignment_count", "determinate_coverage", "recall_interval",
    ])
    contract["coverage_reporting"]["scalar_coverage_rate"] = "determinate_coverage_for_required_facts; source_unresolved_coverage_reported_separately"
    contract["case_contract_binding"] = "V3.1 manifest selects this contract for all 40 cases; unchanged case files retain V3.0 origin metadata and byte identity"
    contract["retired_fact_policy"] = "retired facts are recorded verbatim in amendment history and excluded from the live V3.1 inventory, statuses, and denominators"
    return contract


def diff(before: object, after: object, path: str = "") -> list[dict]:
    if before == after:
        return []
    if isinstance(before, list) and isinstance(after, list) and all(
        isinstance(x, dict) and "fact_id" in x for x in before + after
    ):
        previous = {x["fact_id"]: x for x in before}
        current = {x["fact_id"]: x for x in after}
        if len(previous) == len(before) and len(current) == len(after):
            result = []
            for fact_id in sorted(set(previous) | set(current)):
                p = path + "/" + fact_id
                if fact_id not in previous:
                    result.append({"path": p, "before": None, "after": current[fact_id]})
                elif fact_id not in current:
                    result.append({"path": p, "before": previous[fact_id], "after": None})
                else:
                    result.extend(diff(previous[fact_id], current[fact_id], p))
            return result
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(set(before) | set(after)):
            p = path + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in before:
                result.append({"path": p, "before": None, "after": after[key]})
            elif key not in after:
                result.append({"path": p, "before": before[key], "after": None})
            else:
                result.extend(diff(before[key], after[key], p))
        return result
    return [{"path": path or "/", "before": before, "after": after}]


def summary(cases: dict[str, dict]) -> dict:
    nodes = Counter()
    relations = Counter()
    node_types: dict[str, Counter] = {}
    relation_types: dict[str, Counter] = {}
    unresolved_cases = []
    no_control_cases = []
    required_cases = 0
    questions = 0
    for case_id, case in cases.items():
        required_cases += int(any(x["status"] == "required" for x in case["control_nodes"] + case["control_relations"]))
        if case["no_control"]:
            no_control_cases.append(case_id)
        if case["unresolved_facts"]:
            unresolved_cases.append(case_id)
        questions += len(case["unresolved_facts"])
        for x in case["control_nodes"]:
            nodes[x["status"]] += 1
            node_types.setdefault(x["status"], Counter())[x["type"]] += 1
        for x in case["control_relations"]:
            relations[x["status"]] += 1
            relation_types.setdefault(x["status"], Counter())[x["type"]] += 1
    return {
        "supported_cases": len(cases),
        "cases_with_required_controls": required_cases,
        "affirmative_no_control_cases": len(no_control_cases),
        "unresolved_cases": len(unresolved_cases),
        "unresolved_source_questions": questions,
        "required_control_nodes": nodes["required"],
        "required_control_relations": relations["required"],
        "permitted_control_nodes": nodes["permitted"],
        "permitted_control_relations": relations["permitted"],
        "unresolved_control_nodes": nodes["unresolved"],
        "unresolved_control_relations": relations["unresolved"],
        "node_counts_by_status_and_type": {k: dict(sorted(v.items())) for k, v in sorted(node_types.items())},
        "relation_counts_by_status_and_type": {k: dict(sorted(v.items())) for k, v in sorted(relation_types.items())},
        "unresolved_case_ids": sorted(unresolved_cases, key=lambda x: tuple(map(int, x.split("-")))),
        "no_control_case_ids": sorted(no_control_cases, key=lambda x: tuple(map(int, x.split("-")))),
    }


def validate(cases: dict[str, dict], parent_manifest: dict, contract: dict, retired: dict,
             old_tree_hashes: dict[str, str]) -> dict:
    errors: list[str] = []
    checks = Counter()
    unit_ids_by_case: dict[str, set[str]] = {}
    occurrence_to_unit_by_case: dict[str, dict[str, str]] = {}
    case_components: dict[str, dict] = {}
    for case_id, case in cases.items():
        prior = parent_manifest["components"]["cases"][case_id]
        source_dir = SOURCE / case_id
        source_bytes = (source_dir / "process_text.txt").read_bytes()
        action_bytes = (source_dir / "inventory_reviewed.json").read_bytes()
        reference = json.loads((source_dir / "reference_evidence.json").read_bytes())
        if sha(source_bytes) != prior["source_sha256"] or sha(action_bytes) != prior["reviewed_action_inventory_sha256"] or reference["reference_sha256"] != prior["reference_model_sha256"]:
            errors.append(f"{case_id}: source/Action/reference dependency changed")
        reviewed = json.loads(action_bytes)
        units = {x["semantic_unit_id"]: x for x in reviewed["units"]}
        occurrences = {x["occurrence_id"]: x["semantic_unit_id"] for x in reviewed["occurrences"]}
        unit_ids_by_case[case_id] = set(units)
        occurrence_to_unit_by_case[case_id] = occurrences
        text = source_bytes.decode(case["source_encoding"])
        if case["case_id"] != case_id or case["status"] != "FROZEN":
            errors.append(f"{case_id}: case identity/status mismatch")
        node_by_id = {x["fact_id"]: x for x in case["control_nodes"]}
        fact_ids = [x["fact_id"] for x in case["control_nodes"] + case["control_relations"]]
        if len(fact_ids) != len(set(fact_ids)):
            errors.append(f"{case_id}: duplicate fact id")
        for fact in case["control_nodes"] + case["control_relations"]:
            fid = fact["fact_id"]
            checks["facts"] += 1
            if fact["status"] not in {"required", "permitted", "unresolved"}:
                errors.append(f"{fid}: invalid status")
            if fact in case["control_relations"]:
                owner = node_by_id.get(fact["source_control_fact"])
                if owner is None:
                    errors.append(f"{fid}: missing owner")
                elif fact["status"] == "required" and owner["status"] != "required":
                    errors.append(f"{fid}: required relation has non-required owner")
                elif fact["status"] == "unresolved" and not fact.get("reason_code"):
                    errors.append(f"{fid}: unresolved relation lacks reason code")
            for key in ("anchor_action_ids", "target_action_ids", "incoming_action_ids", "excluded_action_ids"):
                for unit_id in fact.get(key, []):
                    checks["semantic_unit_references"] += 1
                    if unit_id not in units:
                        errors.append(f"{fid}: unknown {key} {unit_id}")
                    elif fact["status"] == "required":
                        reviewed_state = units[unit_id]["provenance"]["review_state"]
                        source_occurrences = [
                            occurrence for occurrence in reviewed["occurrences"]
                            if occurrence["semantic_unit_id"] == unit_id
                            and occurrence["source_text_evidence"]
                            and occurrence["evidence_status"] != "reference_only"
                        ]
                        if reviewed_state not in {"accepted", "modified"} or not source_occurrences:
                            errors.append(f"{fid}: required anchor is not reviewed and source-supported: {unit_id}")
            for key in ("anchor_occurrence_ids", "target_occurrence_ids", "incoming_occurrence_ids"):
                for occurrence_id in fact.get(key, []):
                    checks["occurrence_references"] += 1
                    if occurrence_id not in occurrences:
                        errors.append(f"{fid}: unknown occurrence {occurrence_id}")
            for evidence in fact.get("control_anchor_evidence", []):
                checks["control_anchor_evidence"] += 1
                if evidence.get("kind") not in {"anchor_set", "occurrence_anchor_set", "gateway_guard"}:
                    errors.append(f"{fid}: unsupported evidence kind")
                for unit_id in evidence.get("semantic_unit_ids", []) + evidence.get("action_context_ids", []):
                    if unit_id not in units or units[unit_id]["provenance"]["review_state"] not in {"accepted", "modified"}:
                        errors.append(f"{fid}: invalid evidence unit {unit_id}")
                    elif not any(
                        occurrence["semantic_unit_id"] == unit_id
                        and occurrence["source_text_evidence"]
                        and occurrence["evidence_status"] != "reference_only"
                        for occurrence in reviewed["occurrences"]
                    ):
                        errors.append(f"{fid}: evidence unit lacks source support {unit_id}")
                for occurrence_id in evidence.get("occurrence_ids", []):
                    if occurrence_id not in occurrences:
                        errors.append(f"{fid}: invalid evidence occurrence {occurrence_id}")
                    elif occurrences[occurrence_id] not in evidence.get("semantic_unit_ids", []):
                        errors.append(f"{fid}: occurrence/unit mismatch {occurrence_id}")
                if "source_span" in evidence:
                    s = evidence["source_span"]
                    if text[s["start_offset"]:s["end_offset"]] != s["exact_excerpt"]:
                        errors.append(f"{fid}: bad evidence span")
            for s in fact.get("source_spans", []):
                checks["source_spans"] += 1
                if text[s["start_offset"]:s["end_offset"]] != s["exact_excerpt"]:
                    errors.append(f"{fid}: bad source span")
        for question in case["unresolved_facts"]:
            checks["source_questions"] += 1
            if question.get("status") != "unresolved" or not question.get("reason_code"):
                errors.append(f"{case_id}: invalid unresolved source question")
            for fid in question.get("affected_fact_ids", []):
                if fid not in fact_ids:
                    errors.append(f"{case_id}: unresolved question references retired fact {fid}")
            for s in question.get("source_spans", []):
                if text[s["start_offset"]:s["end_offset"]] != s["exact_excerpt"]:
                    errors.append(f"{case_id}: bad source-question span")
        case_components[case_id] = {
            "relative_path": f"cases/{case_id}/control_inventory.json",
            "control_inventory_sha256": digest(V31 / f"cases/{case_id}/control_inventory.json"),
            "source_sha256": prior["source_sha256"],
            "reviewed_action_inventory_sha256": prior["reviewed_action_inventory_sha256"],
            "reference_model_sha256": prior["reference_model_sha256"],
            "origin_inventory_version": case["inventory_version"],
        }
    for rel, old_sha in old_tree_hashes.items():
        if digest(V30 / rel) != old_sha:
            errors.append(f"V3.0 modified during amendment: {rel}")
    if set(old_tree_hashes) != {str(p.relative_to(V30)) for p in V30.rglob("*") if p.is_file()}:
        errors.append("V3.0 file set modified during amendment")
    for case_id in parent_manifest["components"]["cases"]:
        if case_id not in CASES and case_components[case_id]["control_inventory_sha256"] != parent_manifest["components"]["cases"][case_id]["control_inventory_sha256"]:
            errors.append(f"{case_id}: unapproved case modified")
    if item(cases["9-1"]["control_nodes"], "CF-9-1-N04")["status"] != "required" or any(x["fact_id"] == "CF-9-1-R05" for x in cases["9-1"]["control_relations"]):
        errors.append("9-1 disposition mismatch")
    if item(cases["9-1"]["control_nodes"], "CF-9-1-N04")["anchor_action_ids"] != ["SU-9-1-08"]:
        errors.append("9-1 N04 not reanchored to alert")
    if item(cases["9-1"]["control_relations"], "CF-9-1-R04")["status"] != "required":
        errors.append("9-1 R04 lost required status")
    if item(cases["4-1"]["control_relations"], "CF-4-1-R08")["status"] != "required":
        errors.append("4-1 second-meeting synchronization not required")
    if retired["fact_id"] != "CF-9-1-R05":
        errors.append("wrong retired fact")
    if contract["candidate_scoring_state_contract"]["fixed_denominator_equation"] != "D = TP + FN + indeterminate_alignment_count":
        errors.append("fixed denominator contract missing")
    return {
        "status": "passed" if not errors else "failed",
        "validation_kind": "deterministic_source_and_schema_only",
        "candidate_graphs_or_scores_accessed": False,
        "evaluator_run": False,
        "formal_120_candidate_evaluation_run": False,
        "v3_0_corpus_sha256": parent_manifest["corpus_sha256"],
        "v3_0_file_count_verified_unchanged": len(old_tree_hashes),
        "unchanged_case_files": sum(case_id not in CASES for case_id in cases),
        "modified_case_ids": list(CASES),
        "checks": dict(sorted(checks.items())),
        "errors": errors,
        "case_components": case_components,
    }


def main() -> None:
    if V31.exists():
        raise SystemExit(f"refusing to overwrite V3.1 freeze: {V31}")
    parent = json.loads((V30 / "freeze_manifest.json").read_bytes())
    if parent["corpus_sha256"] != "8d8e9dc51bf45cf37721cce8aadb8953bbf8656217382fb8afdbbb39944f0968":
        raise SystemExit("unexpected V3.0 parent hash")
    old_tree_hashes = {str(p.relative_to(V30)): digest(p) for p in V30.rglob("*") if p.is_file()}
    cases = {}
    old_cases = {}
    for case_id in parent["components"]["cases"]:
        path = V30 / f"cases/{case_id}/control_inventory.json"
        cases[case_id] = json.loads(path.read_bytes())
        old_cases[case_id] = deepcopy(cases[case_id])
    V31.mkdir(parents=True)
    for case_id in cases:
        destination = V31 / f"cases/{case_id}/control_inventory.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(V30 / f"cases/{case_id}/control_inventory.json", destination)
    amend_4_1(cases["4-1"])
    amend_9_6(cases["9-6"])
    amend_2_2(cases["2-2"], source_text("2-2", cases["2-2"]))
    amend_6_3(cases["6-3"])
    amend_10_8(cases["10-8"])
    retired = amend_9_1(cases["9-1"], source_text("9-1", cases["9-1"]))
    for case_id in CASES:
        cases[case_id]["inventory_version"] = VERSION
        cases[case_id]["scoring_contract_version"] = CONTRACT_VERSION
        cases[case_id]["adjudication_revision"] = "v3.1-approved-source-only-amendment-20260924"
        write_json(V31 / f"cases/{case_id}/control_inventory.json", cases[case_id])
    old_contract = json.loads((V30 / "scoring_contract.json").read_bytes())
    contract = amend_contract(old_contract)
    write_json(V31 / "scoring_contract.json", contract)
    history = {
        "amendment_version": VERSION,
        "status": "FROZEN",
        "parent_v3_0_corpus_sha256": parent["corpus_sha256"],
        "approved_scope_case_ids": list(CASES),
        "source_only_review": True,
        "candidate_graphs_or_scores_used": False,
        "action_scoring_changed": False,
        "case_changes": {
            case_id: {
                "before_sha256": parent["components"]["cases"][case_id]["control_inventory_sha256"],
                "after_sha256": digest(V31 / f"cases/{case_id}/control_inventory.json"),
                "exact_json_differences": diff(old_cases[case_id], cases[case_id]),
            }
            for case_id in CASES
        },
        "scoring_contract_change": {
            "before_sha256": digest(V30 / "scoring_contract.json"),
            "after_sha256": digest(V31 / "scoring_contract.json"),
            "exact_json_differences": diff(old_contract, contract),
        },
        "retired_facts": [{
            "case_id": "9-1",
            "fact_id": "CF-9-1-R05",
            "before": retired,
            "after": None,
            "reason": "The source conditions later CRM checking on report completion, not on meeting the 2:30 pm deadline.",
        }],
        "source_decisions": {
            "4-1": "Both patient meetings are explicit prerequisites for listing; meeting completion is a Control-only boundary, not dictaphone recording or examination.",
            "9-6": "Initial and repeated combining have distinct reviewed occurrences and must be bound to the correct design cycle.",
            "2-2": "The simultaneous grid-operator work supports the Fork; old-supplier billing timing is not fixed by the word 'Likewise'.",
            "6-3": "The source explicitly states the missing-parts decision; gateway/guard evidence can express it without an Action proxy.",
            "10-8": "Verification precedes rejection or preliminary confirmation; the Decision may be shown through routing semantics.",
            "9-1": "The missed-2:30 deadline alert is explicit; the exact scope of 'All of this' is ambiguous, and an on-time branch to the later CRM check is unsupported.",
        },
    }
    write_json(V31 / "amendment_history.json", history)
    validation = validate(cases, parent, contract, retired, old_tree_hashes)
    if validation["status"] != "passed":
        write_json(V31 / "source_only_validation.json", validation)
        raise SystemExit("V3.1 source-only validation failed: " + "; ".join(validation["errors"]))
    code_paths = {
        "v2_action_matcher": ACTION_CODE / "friedrich_semantic/action.py",
        "v2_action_projection": ACTION_CODE / "friedrich_semantic_v2/evaluator_adapter.py",
    }
    code_hashes = {key: {"path": str(path), "sha256": digest(path)} for key, path in code_paths.items()}
    validation["action_scoring_code_hashes"] = code_hashes
    validation["summary"] = summary(cases)
    write_json(V31 / "source_only_validation.json", validation)
    components = {
        "scoring_contract": {"relative_path": "scoring_contract.json", "sha256": digest(V31 / "scoring_contract.json")},
        "amendment_history": {"relative_path": "amendment_history.json", "sha256": digest(V31 / "amendment_history.json")},
        "action_scoring_code": code_hashes,
        "cases": validation["case_components"],
    }
    corpus_hash = sha(canonical(components))
    manifest = {
        "status": "FROZEN",
        "freeze_version": VERSION,
        "effective_scoring_contract_version": CONTRACT_VERSION,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "parent_v3_0_corpus_sha256": parent["corpus_sha256"],
        "parent_v3_0_manifest_sha256": digest(V30 / "freeze_manifest.json"),
        "candidate_graphs_or_scores_accessed": False,
        "evaluator_run": False,
        "formal_120_candidate_evaluation_run": False,
        "action_scoring_changed": False,
        "summary": validation["summary"],
        "source_only_validation": {"relative_path": "source_only_validation.json", "sha256": digest(V31 / "source_only_validation.json"), "status": "passed"},
        "corpus_sha256": corpus_hash,
        "corpus_hash_algorithm": "SHA-256 of UTF-8 compact sorted-key JSON of components, ensure_ascii=False; components include contract, amendment history, Action code hashes, all 40 Control files, and source/reviewed Action/reference dependency hashes",
        "components": components,
    }
    write_json(V31 / "freeze_manifest.json", manifest)
    print(json.dumps({"status": "FROZEN", "root": str(V31), "corpus_sha256": corpus_hash, "summary": manifest["summary"]}, indent=2))


if __name__ == "__main__":
    main()
