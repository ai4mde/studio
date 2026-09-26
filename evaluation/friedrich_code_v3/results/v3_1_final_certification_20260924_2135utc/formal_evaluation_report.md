# Friedrich V3.1 formal 120-candidate evaluation

**FORMAL 120-CANDIDATE V3.1 EVALUATION COMPLETED**

- V3.1 frozen corpus SHA-256: `5f9765bda2ea5d9d9f4a78603207bb0a2ed6532fd0c935149c275595c7d5be8a`
- V3.1 scoring contract SHA-256: `f56d549ce2d725c73d2fc03e0442df599ee538dd1efd6f4f8b773dfb50b9a20a`
- V2 Action matcher SHA-256: `1fc985a2e50da84d12f93134989c970c7e8f36b747c17f6439a9c9775d44b154`
- V2 Action projection SHA-256: `12d3bfaf878d6d056d0ab815d511e4431f5a8a3fa9674922d6f815a36571b80e`
- Cohort: `final_frozen_40x3_20260910`, 40 cases × 3 unchanged candidates
- Generated cohort manifest SHA-256: `e7c703f0fbf3c128a9c3f64567f6d743702cde1a47cd06e377397b1a8541b695`
- Exact roster SHA-256: `f96893bd709cd51a9499e7f7829d454d0c70642896ae9a29128f1fe271506980`
- Processed slots: 120; evaluated: 120; malformed: 0; technical exceptions: 0
- Complete candidates: 62; candidates with indeterminate alignment: 58
- Post-run integrity: passed

## Aggregate component results

Macro and case-balanced all-slot means are null when any required candidate metric is null. The JSON also gives descriptive means and their numeric observation counts. Pooled scalar metrics are null whenever a component has an indeterminate or unavailable slot.

| Component | Candidate macro F1 | Case-balanced F1 | Pooled TP | FP | FN | Pooled F1 | Indeterminate facts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Action | 0.9194523128807306 | 0.9194523128807305 | 966 | 0 | 171 | 0.9186875891583453 | 0 |
| Flow | None | None | 723 | 83 | 214 | None | 239 |
| Control Node | None | None | 179 | 0 | 76 | None | 30 |
| Control Relation | None | None | 231 | 52 | 251 | None | 106 |

## Diagnostics and artifacts

- No-control: 18/18 candidates have zero scored Control FP; Node FP 0, Relation FP 0.
- Human-review diagnostic entries: 156; scores unchanged by shortlist selection.
- Raw candidate results include Action Alignment Tables, Control Anchor Evidence, every scored fact, generated relation coverage, FP abstentions, source questions, and indeterminate reasons.
- Normalization is the frozen evaluator's unlabeled 1-in/1-out gateway contraction; the run uses it without modification. Candidate graph paths and hashes are in the pre-run identity file.
- No Oracle Best-of-Three is reported. No combined overall evaluator F1 is reported.
- No methodology, source inventory, scoring contract, unresolved question, generator, V2 Action evaluator, threshold, anchor rule, matching rule, or candidate changed during this formal run.

### Output paths

- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_1_final_certification_20260924_2135utc/run_identity_before.json`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_1_final_certification_20260924_2135utc/run_integrity.json`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_1_final_certification_20260924_2135utc/candidate_results.jsonl`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_1_final_certification_20260924_2135utc/candidate_results.csv`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_1_final_certification_20260924_2135utc/case_summary.json`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_1_final_certification_20260924_2135utc/case_summary.csv`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_1_final_certification_20260924_2135utc/aggregate_summary.json`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_1_final_certification_20260924_2135utc/human_review_shortlist.json`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_1_final_certification_20260924_2135utc/human_review_shortlist.csv`

FORMAL 120-CANDIDATE V3.1 EVALUATION COMPLETED

## Reporting on Scorable Facts

| Component | Determinate Coverage | Precision on Scorable Facts | Recall on Scorable Facts | F1 on Scorable Facts |
| --- | ---: | ---: | ---: | ---: |
| Action | 100.0% | 1.000 | 0.850 | 0.919 |
| Flow | 79.7% | 0.897 | 0.772 | 0.830 |
| Control Node | 89.5% | 1.000 | 0.702 | 0.825 |
| Control Relation | 82.0% | 0.816 | 0.479 | 0.604 |

The reporting-only metrics are calculated from the certified pooled counts:

- `determinate_coverage = (TP + FN) / D = (D - I) / D`
- `Precision on Scorable Facts = TP / (TP + FP)`
- `Recall on Scorable Facts = TP / (TP + FN)`
- `F1 on Scorable Facts = 2 × Precision × Recall / (Precision + Recall)`

Coverage reports the proportion of required facts for which the code-based evaluator could establish a determinate alignment. Precision, Recall, and F1 on Scorable Facts are calculated only over those determinate facts. Indeterminate facts are excluded rather than forced into TP or FN decisions.

These scorable-fact metrics describe evaluator-assessed quality within the determinate portion of the evaluation and should be interpreted together with coverage.

The frozen formal all-slot pooled P/R/F1 remain null for Flow, Control Node, and Control Relation because each has I > 0. The scorable-fact F1 is not an all-120 complete F1.

### Technical counts and formal pooled metrics

| Component | D | TP | FP | FN | I | Formal all-slot pooled P | Formal all-slot pooled R | Formal all-slot pooled F1 | Recall interval | Candidates with I | Fully determinate candidates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| Action | 1137 | 966 | 0 | 171 | 0 | 1.000 | 0.850 | 0.919 | [0.8496, 0.8496] | 0 | 120 |
| Flow | 1176 | 723 | 83 | 214 | 239 | null | null | null | [0.6148, 0.8180] | 55 | 65 |
| Control Node | 285 | 179 | 0 | 76 | 30 | null | null | null | [0.6281, 0.7333] | 21 | 99 |
| Control Relation | 588 | 231 | 52 | 251 | 106 | null | null | null | [0.3929, 0.5731] | 44 | 76 |


## Final certification

All mandatory integrity and scoring checks passed. See `final_certification_comparison.md` for the historical comparison, scoped audit checks, and complete aggregate table.

FORMAL 120-CANDIDATE V3.1 CERTIFIED — FINAL CONTRACT-COMPLETE RESULT
