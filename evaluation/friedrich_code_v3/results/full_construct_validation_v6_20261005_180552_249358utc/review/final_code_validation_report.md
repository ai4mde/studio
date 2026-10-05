# Final normal 120-candidate Code validation: combined candidate v8

## Decision

**READY TO FREEZE, pending a separate explicit freeze step.** The normal offline pipeline evaluated all 120 frozen candidates (40 cases × 3) with `.venv-friedrich-v2` and `combined_candidate_v8`. There were no API calls or technical exceptions. No evaluator logic was changed during the run or review.

The 65 targeted fact checks pass in the saved normal-run outputs, including all previous 52 checks. Against the previous reviewed v7 validation, Action, Action alignment, Control anchor evidence, and Flow are identical for all 120 candidates. Control outputs are identical for 118 candidates. The only changes are the reviewed compound Decision correction in 9-5/candidate_2 and candidate_3. No new confirmed regression or new indeterminate status was found. Remaining source ambiguity, including the reviewed 6-4 known-contact item, is not treated as an absence or a freeze blocker.

## Final dataset-level metrics

Coverage is determinate required facts divided by all required facts; indeterminate required facts remain in the denominator. Pooled precision, recall, and F1 use determinate TP/FP/FN. N/A counts are candidates, while indeterminate counts are required facts.

| Dimension | TP | FP | FN | Indeterminate facts | N/A candidates | Coverage | Precision | Recall | Pooled F1 | Numeric / null candidates |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Action | 946 | 0 | 188 | 0 | 0 | 100.00% | 1.0000 | 0.8342 | 0.9096 | 120 / 0 |
| Flow | 723 | 49 | 122 | 331 | 0 | 71.85% | 0.9365 | 0.8556 | 0.8942 | 54 / 66 |
| Control Node | 432 | 0 | 69 | 24 | 0 | 95.43% | 1.0000 | 0.8623 | 0.9260 | 105 / 15 |
| Control Relation | 267 | 39 | 224 | 97 | 21 | 83.50% | 0.8725 | 0.5438 | 0.6700 | 57 / 63 |

**Formal Overall Code F1 = 0.8499803890695803**, the arithmetic mean of the four pooled dimension F1 values. It is a dataset-level summary, not a candidate-level score.

## Change audit against the previous reviewed validation

There are eight Control fact status/owner changes across exactly two candidates. Six are **EXPECTED FIX**: in both 9-5 candidates, the required 30-day Control Node N05 changes FN → TP, and the cancellation branch R10 and termination R12 change FN → TP. Two are **EXPECTED CONSTRUCT CHANGE**: R11 remains FN but is now attributed to the recovered 30-day owner rather than an absent owner. The seven-day Node N04 and progress relation R08 remain TP. Candidate_1 retains its indeterminate time-role assignment. The full fact classification is in `incremental_change_audit.csv`. There are zero changes classified GENUINE AMBIGUITY and zero CONFIRMED REGRESSION.

The unchanged R11 FN is an existing relation-level outcome under the ordinary scorer. Recovering a Control Node owner does not automatically make every owned route correct. Node presence and relation behavior remain separate.

## Known fixes and construct boundaries

The saved normal outputs pass all 65 checks in `targeted_checks_in_normal_run.json`. This includes the two corrected Flow inventory facts, Action guard v4 examples, unmatched-Action Flow indeterminate handling, Decision/Fork/Join/Merge role checks, 5-4/candidate_2 N04 ambiguity, known wrong synchronization, absent 9-6 recurrence, absent 10-9/6-4 source branches, and the 9-5 shared Decision. The prior 15 grouped known-fix checks still hold because their relevant outputs are unchanged or explicitly rechecked. Action completeness remains in Action; Flow still evaluates precedence for reliably matched activities; Control Node evaluates presence; and Control Relation evaluates observed behavior. No new cross-dimension leakage appeared.

All 21 true Control Relation N/A candidates have status N/A and null F1/score. Control Relation is omitted from their candidate Overall dimension list. Applicable indeterminate dimensions remain null. The unchanged indeterminate facts retain their prior diagnostics; this run adds none. Individual human adjudication of every unchanged indeterminate fact was not repeated and is not required by the stop rule.

## Integrity and provenance

The run manifest records the frozen roster hash, both snapshot hashes, the frozen V3.2 and previous reviewed result hashes, component hashes, and output hashes. Post-run checks verified all 120 unique candidate identities, all 65 targeted statuses, all output/component hashes, and 25/25 frozen V3.2 package source/derived hashes. No AI evaluation or formal evaluator rerun occurred; this was the one requested normal offline freeze-validation run.

## Exact proposed freeze scope (not yet frozen)

- **Versioned evaluator components:** `action_operation_guard_v4.py`; `flow_matched_action_v1.py`; `control_node_role_assignment_v4.py` plus `control_node_shared_roles_v5.py`; `control_relation_local_evidence_v3.py` plus `control_relation_shared_owner_v4.py`.
- **Reporting and configuration:** `candidate_reporting_v1.py`; `combined_candidate_v8.py`; validation runner `run_full_construct_validation_v6.py`. Record hashes of their transitive scoring, alignment, reference, inventory, and model-adapter dependencies in the eventual freeze manifest.
- **Approved snapshots:** `fixed_flow_inventory/corpus_v1/v3_2_alignment_flow_facts_1/` with its `manifest.json`; `source_action_eligibility/corpus_v1/v1/` with its `manifest.json`; the unchanged frozen 120-candidate roster and graph hashes from the V3.2 formal identity record.
- **Evidence and manifests:** the existing shared-control targeted manifest and 65-check results; this run's `validation_manifest.json`, `candidate_results.jsonl`, `aggregate_summary.json`, `fact_changes.csv`, and review integrity/change-audit files. The eventual freeze manifest should reference these exact hashes and the frozen V3.2 package manifest, without altering historical artifacts.

The stop rule is satisfied: 120/120 completed, all known checks passed, no new confirmed systemic regression, N/A/null handling correct, and construct boundaries retained. Coverage below 100%, genuine indeterminacy, and remaining human-review items are documented rather than treated as blockers. **Do not freeze until separately instructed.**
