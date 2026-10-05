# Friedrich V3.2 formal 120-candidate evaluation

**FORMAL 120-CANDIDATE V3.2 EVALUATION COMPLETED**

- Run ID: `v3_2_formal_120_20260930_225036utc`
- V3.1 frozen corpus SHA-256: `5f9765bda2ea5d9d9f4a78603207bb0a2ed6532fd0c935149c275595c7d5be8a`
- V3.2 structural contract SHA-256: `29472c7c2e61c34a19a573d89bf8b66d4bb1815b9dd73d9123240069306f7ddc`
- Certified V3.1 result SHA-256: `c8726950afadd78165f9e8bd3d8f05cf95f6cab202a1fe45798062484b262b00`
- Frozen 120-candidate roster SHA-256: `f96893bd709cd51a9499e7f7829d454d0c70642896ae9a29128f1fe271506980`
- Evaluated candidates: 120; malformed: 0; technical exceptions: 0

## Four dimensions

Precision, Recall, and F1 below are **pooled scorable-fact** metrics. Coverage is the determinate share of required facts. Formal all-slot metrics are null when a dimension has indeterminate facts.

| Dimension | TP | FP | FN | I | D | Scorable Precision | Scorable Recall | Scorable F1 | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Action | 966 | 0 | 171 | 0 | 1137 | 1.000000 | 0.849604 | 0.918688 | 100.00% |
| Flow | 723 | 83 | 214 | 239 | 1176 | 0.897022 | 0.771612 | 0.829604 | 79.68% |
| Control Node | 419 | 0 | 76 | 30 | 525 | 1.000000 | 0.846465 | 0.916849 | 94.29% |
| Control Relation | 231 | 52 | 251 | 106 | 588 | 0.816254 | 0.479253 | 0.603922 | 81.97% |

**Overall Code F1 (arithmetic mean of the four scorable-fact F1 scores): 0.817266**

This overall value is a descriptive scorable-fact mean, not an all-slot F1. Action, Flow, Control Node, and Control Relation each receive equal weight.

## Control Node breakdown

- Start: TP 120, FN 0
- End: TP 120, FN 0

| Scope | TP | FP | FN | I | D |
| --- | ---: | ---: | ---: | ---: | ---: |
| Source-derived Decision/Merge/Fork/Join | 179 | 0 | 76 | 30 | 285 |
| Structural Start/End | 240 | 0 | 0 | 0 | 240 |
| Combined Control Node | 419 | 0 | 76 | 30 | 525 |

## Regression and integrity

- Exact Action outputs versus certified V3.1: 120/120
- Exact Flow outputs versus certified V3.1: 120/120
- Exact Control Relation outputs versus certified V3.1: 120/120
- Exact source-derived Control Node outputs versus certified V3.1: 120/120
- Unresolved source questions unchanged: 120/120
- Frozen input and certified result files changed during run: 0

## Output files

- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_2_formal_120_20260930_225036utc/run_identity_before.json`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_2_formal_120_20260930_225036utc/run_integrity.json`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_2_formal_120_20260930_225036utc/candidate_results.jsonl`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_2_formal_120_20260930_225036utc/candidate_results.csv`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_2_formal_120_20260930_225036utc/case_summary.json`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_2_formal_120_20260930_225036utc/aggregate_summary.json`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_2_formal_120_20260930_225036utc/formal_evaluation_report.md`
- `/Users/queenie/Desktop/studio/evaluation/friedrich_code_v3/results/v3_2_formal_120_20260930_225036utc/output_manifest.json`

FORMAL 120-CANDIDATE V3.2 EVALUATION COMPLETED
