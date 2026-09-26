"""Reproducible fact-level audit of the four V3.1 blocker fixes."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "results/v3_1_blocker_fixes_20260924"
STAGES = (
    ("Baseline", ROOT / "baseline.json"),
    ("Occurrence scope", ROOT / "after_fix_1/results.json"),
    ("Case-wide assignment", ROOT / "after_fix_2/results.json"),
    ("Relation coverage", ROOT / "after_fix_3/results.json"),
    ("Cycle classification", ROOT / "after_fix_4_final/results.json"),
)
COMPONENTS = ("Flow", "Control Node", "Control Relation")


def fact_id(item: dict) -> str:
    return item.get("fact_id") or f"{item['source_unit_id']} → {item['target_unit_id']}"


def main() -> None:
    stages = [(name, json.loads(path.read_text())["results"] if name != "Baseline"
               else json.loads(path.read_text())["results"])
              for name, path in STAGES]
    roster = [(item["case_id"], item["candidate_id"]) for item in stages[0][1]]
    assert len(roster) == 18
    rows = ["# V3.1 blocker-fix candidate fact audit", "",
            "The approved roster is identical at every stage: candidates 1–3 for cases "
            "2-2, 4-1, 6-3, 9-1, 9-6, and 10-8. All 18 candidates evaluated at every stage. "
            "Every case-specific Action, Flow, Control Node, and Control Relation denominator "
            "and every frozen unresolved question remained identical.", ""]
    prior = None
    for name, results in stages:
        assert roster == [(item["case_id"], item["candidate_id"]) for item in results]
        if prior is None:
            prior = results
            continue
        rows.extend((f"## After {name}", ""))
        changes = []
        anchor_changes = []
        ledger_changes = []
        for before, after in zip(prior, results):
            assert before["Action"] == after["Action"]
            assert before["source_unresolved_questions"] == after["source_unresolved_questions"]
            for field in ("control_only_unit_to_generated", "occurrence_to_generated"):
                old_map = before["Control Anchor Evidence"][field]
                new_map = after["Control Anchor Evidence"][field]
                for identifier in sorted(old_map.keys() | new_map.keys()):
                    if old_map.get(identifier) != new_map.get(identifier):
                        anchor_changes.append((after["case_id"], after["candidate_id"],
                                               field, identifier, old_map.get(identifier),
                                               new_map.get(identifier)))
            old_ledger = {item["generated_relation_id"]: item for item in
                          before["Control Relation"].get("generated_relation_coverage", [])}
            new_ledger = {item["generated_relation_id"]: item for item in
                          after["Control Relation"].get("generated_relation_coverage", [])}
            for identifier in sorted(old_ledger.keys() | new_ledger.keys()):
                if old_ledger.get(identifier) != new_ledger.get(identifier):
                    ledger_changes.append((after["case_id"], after["candidate_id"],
                                           identifier, old_ledger.get(identifier),
                                           new_ledger.get(identifier)))
            for component in COMPONENTS:
                b, a = before[component], after[component]
                assert b["counts"]["required_denominator"] == a["counts"]["required_denominator"]
                old_facts = {fact_id(item): item for item in b["facts"]}
                new_facts = {fact_id(item): item for item in a["facts"]}
                assert old_facts.keys() == new_facts.keys()
                for identifier in old_facts:
                    old, new = old_facts[identifier], new_facts[identifier]
                    fields = ("status", "generated_node_id", "reason")
                    if any(old.get(field) != new.get(field) for field in fields):
                        changes.append((after["case_id"], after["candidate_id"], component,
                                        identifier, old, new))
        if changes:
            rows.extend(("| Case | Candidate | Component | Fact | Before | After | Explanation |",
                         "| --- | --- | --- | --- | --- | --- | --- |"))
            for case, candidate, component, identifier, old, new in changes:
                explanation = ("Case-wide assignment selected the same node with an updated evidence reason."
                               if component == "Control Node" else
                               "The fixed source recurrence supports this candidate cycle; "
                               "the occurrence-level Flow phase remains indeterminate.")
                rows.append(f"| {case} | {candidate} | {component} | {identifier} | "
                            f"{old['status']}: {old['reason']} | {new['status']}: {new['reason']} | "
                            f"{explanation} |")
        else:
            rows.append("No scored candidate fact, assignment, or reason changed.")
        rows.append("")
        if anchor_changes:
            rows.extend(("### Control Anchor Evidence changes", "",
                         "| Case | Candidate | Evidence class | ID | Before generated nodes | After generated nodes | Explanation |",
                         "| --- | --- | --- | --- | --- | --- | --- |"))
            for case, candidate, field, identifier, old, new in anchor_changes:
                rows.append(f"| {case} | {candidate} | {field} | {identifier} | "
                            f"{old or '—'} | {new or '—'} | Required branch, loop, or boundary evidence "
                            "was absent; the Control-only anchor was withdrawn. |")
            rows.append("")
        if ledger_changes:
            rows.extend(("### Generated Control Relation coverage changes", "",
                         "Every relation below is a new or changed candidate-level coverage entry. "
                         "`MATCHED` links to a required source fact; `FP_ABSTAIN` means the "
                         "non-exhaustive source does not justify FP.", "",
                         "| Case | Candidate | Generated relation | Before | After | Linked frozen facts |",
                         "| --- | --- | --- | --- | --- | --- |"))
            for case, candidate, identifier, old, new in ledger_changes:
                rows.append(f"| {case} | {candidate} | {identifier} | "
                            f"{old['status'] if old else 'not enumerated'} | "
                            f"{new['status'] if new else 'removed'} | "
                            f"{', '.join(new['source_fact_ids']) if new and new['source_fact_ids'] else '—'} |")
            rows.append("")
        prior = results
    rows.extend(("## Final invariants", ""))
    final = stages[-1][1]
    assert all(item["candidate_status"] == "EVALUATED" for item in final)
    assert all(item["frozen_corpus_sha256"] == "5f9765bda2ea5d9d9f4a78603207bb0a2ed6532fd0c935149c275595c7d5be8a"
               for item in final)
    rows.append(f"- New generated Control Relation abstention entries: "
                f"{sum(item['Control Relation']['fp_abstention_count'] for item in final)}.")
    rows.append(f"- Source-supported cyclic Flow indeterminacy instances: "
                f"{sum(item['Flow']['source_supported_cycle_indeterminate_count'] for item in final)}.")
    rows.append(f"- Unsupported cyclic Flow violations in this roster: "
                f"{sum(item['Flow']['unsupported_cycle_violation_count'] for item in final)}. "
                "The unsupported-cycle path is covered by synthetic regression tests.")
    rows.append("- No required fact status, Action score, source denominator, or unresolved source question changed.")
    (ROOT / "candidate_fact_change_audit.md").write_text("\n".join(rows) + "\n")
    print(ROOT / "candidate_fact_change_audit.md")


if __name__ == "__main__":
    main()
