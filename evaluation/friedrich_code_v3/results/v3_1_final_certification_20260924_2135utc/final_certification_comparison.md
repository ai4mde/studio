# V3.1 final certification comparison

**FORMAL 120-CANDIDATE V3.1 CERTIFIED — FINAL CONTRACT-COMPLETE RESULT**

## Integrity and scope

- Final output: `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_1_final_certification_20260924_2135utc`.
- Frozen V3.1 corpus SHA-256: `5f9765bda2ea5d9d9f4a78603207bb0a2ed6532fd0c935149c275595c7d5be8a`; scoring contract SHA-256: `f56d549ce2d725c73d2fc03e0442df599ee538dd1efd6f4f8b773dfb50b9a20a`.
- Cohort manifest SHA-256: `e7c703f0fbf3c128a9c3f64567f6d743702cde1a47cd06e377397b1a8541b695`; exact 120-slot roster SHA-256: `f96893bd709cd51a9499e7f7829d454d0c70642896ae9a29128f1fe271506980`.
- The 40 cases, three candidates per case, 120 unique slots, and all 11 frozen unresolved source questions matched the approved identities before scoring.
- Pre-run reproduction was exact for the 9 targeted candidates, 42 guard-cohort candidates, and approved 18-candidate preflight. The 62 unit/regression tests passed immediately before scoring.
- The formal run evaluated 120/120 slots with zero malformed candidates and zero technical exceptions. 644 input and implementation files had identical before/after snapshot hashes.
- The frozen source facts, denominators, candidate graphs, generator, scoring contract, Action matcher, Flow inventory, and evaluator implementation were unchanged during the run.

## Mandatory scoring checks

- Action counts and exact accepted Action mapping tuples equal the locked provisional, broken-completed, and previous uncertified runs in all 120 slots. The locked Action fact projection was verified against each current mapping and copied byte-for-byte.
- Flow results equal the finalized completed-implementation and previous uncertified runs in all 120 slots.
- The 77 audited guard relations remain 33 morphological-equivalence TP, 38 semantic-equivalence TP, and 6 genuine-contradiction FN+FP: 71 TP and 6 FN+FP.
- All 10 implementation-corrected final blocker facts retain their approved statuses. The eleventh, `9-5/candidate_2/CF-9-5-N05`, remains the reviewed FN.
- The six incomplete compound guards in case 5-1 remain FN+FP. No new Control Relation TP→FN+FP occurred outside the approved 12-change set. No new unjustified TP arose from an incomplete compound guard.
- In 9-5 candidates 1 and 2, the approval relation owner alternatives are n6/n7, excluding temporal gateway n11. In candidate 2, the seven-day Node N04 matches n11; the separate required thirty-day Node N05 is FN under one-to-one matching.
- For every candidate and component, `D = TP + FN + I`; any component with I has null scalar P/R/F1 and a reason code on every I fact. Source-unresolved facts are outside scored denominators.
- Generated relation ledger: {'FP_ABSTAIN': 471, 'MATCHED': 238, 'CONTRADICTION_ACCOUNTED': 33}. The raw results also preserve 17 unattributed contradiction records for explicit audit.

## Historical comparison

Every changed fact and diagnostic against each historical baseline is recorded in `final_certification_diff.csv`. Status and assignment changes are previously reviewed implementation corrections; same-status, same-assignment metadata changes are diagnostic-only. No unexpected regression occurred against the previous uncertified certification run.

| Baseline | Scored fact status changes | Assignment-only changes | Diagnostic-only changes |
| --- | ---: | ---: | ---: |
| provisional | 176 | 56 | 426 |
| broken_completed | 95 | 5 | 14 |
| previous_uncertified_certification | 12 | 1 | 10 |

Against the previous uncertified run, the only scored fact changes are the **12** reviewed changes in `v3_1_final_11_blocker_comparison.csv`: ten corrected blocker statuses and two dependent seven-day deadline facts. `CF-9-5-N05` stays FN. The historical provisional and broken-completed differences consist of earlier reviewed implementation corrections plus these final corrections.

## Final aggregate results

Pooled scalar P/R/F1 are null for components with I. Numeric candidate and case means below are descriptive only. A null all-slot mean was not replaced with a descriptive mean.

| Component | D | TP | FP | FN | I | Coverage | Candidates with I | Fully determinate | Pooled P / R / F1 | Candidate descriptive F1 | Case-balanced descriptive F1 | Recall interval |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Action | 1137 | 966 | 0 | 171 | 0 | 1.0000 | 0 | 120 | 1.0000 / 0.8496 / 0.9187 | 0.9195 (n=120) | 0.9195 (n=40) | [0.8496, 0.8496] |
| Flow | 1176 | 723 | 83 | 214 | 239 | 0.7968 | 55 | 65 | null / null / null | 0.9049 (n=65) | 0.9226 (n=18) | [0.6148, 0.8180] |
| Control Node | 285 | 179 | 0 | 76 | 30 | 0.8947 | 21 | 99 | null / null / null | 0.6812 (n=99) | 0.6780 (n=30) | [0.6281, 0.7333] |
| Control Relation | 588 | 231 | 52 | 251 | 106 | 0.8197 | 44 | 76 | null / null / null | 0.5287 (n=76) | 0.5433 (n=23) | [0.3929, 0.5731] |

The raw candidate results preserve Action Alignment Tables, Control Anchor Evidence, every Flow and Control fact with evidence and reason codes, generated relation coverage, FP abstentions, unattributed contradiction records, frozen source questions, normalization events, and technical status. `run_identity_before.json` and `candidate_identity.csv` map each candidate slot to its graph hash.

FORMAL 120-CANDIDATE V3.1 CERTIFIED — FINAL CONTRACT-COMPLETE RESULT
