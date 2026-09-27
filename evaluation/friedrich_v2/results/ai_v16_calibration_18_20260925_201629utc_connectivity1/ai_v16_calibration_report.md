# AI Evaluator v1.6 continuous developmental calibration

The 18 human labels are fixed ordinal anchors; AI scores remain continuous and unrounded in calculations.
This calibration set was used in evaluator development and is not independent final validation.

- MAE: **0.0939** (numeric distance to human anchors).
- Median absolute error: **0.0750**.
- Maximum absolute error: **0.3700**.
- Tie-aware Spearman rank correlation: **0.9560** (descriptive ordering only).
- No acceptance threshold was applied; no AI scores were quantized to human categories.

## Candidate review order

Sorted by absolute error descending; ties retain frozen roster order. Candidate values are shown at stored precision; aggregate figures above are display-rounded only.

| Case | Candidate | Human | AI | Signed difference | Absolute error |
|---|---|---:|---:|---:|---:|
| 1-1 | candidate_2 | 0.00 | 0.37 | 0.37 | 0.37 |
| 9-5 | candidate_2 | 0.25 | 0.44 | 0.19 | 0.19 |
| 1-1 | candidate_3 | 0.25 | 0.4 | 0.15 | 0.15 |
| 9-5 | candidate_3 | 0.50 | 0.65 | 0.15 | 0.15 |
| 9-5 | candidate_1 | 0.50 | 0.64 | 0.14 | 0.14 |
| 8-2 | candidate_2 | 0.75 | 0.87 | 0.12 | 0.12 |
| 1-1 | candidate_1 | 0.25 | 0.35 | 0.10 | 0.10 |
| 6-4 | candidate_1 | 0.75 | 0.84 | 0.09 | 0.09 |
| 6-4 | candidate_3 | 0.75 | 0.84 | 0.09 | 0.09 |
| 3-4 | candidate_3 | 0.75 | 0.69 | -0.06 | 0.06 |
| 8-2 | candidate_1 | 0.50 | 0.44 | -0.06 | 0.06 |
| 3-4 | candidate_2 | 0.75 | 0.7 | -0.05 | 0.05 |
| 8-2 | candidate_3 | 0.50 | 0.45 | -0.05 | 0.05 |
| 3-4 | candidate_1 | 0.75 | 0.71 | -0.04 | 0.04 |
| 6-4 | candidate_2 | 0.75 | 0.78 | 0.03 | 0.03 |
| 3-2 | candidate_1 | 1.00 | 1 | 0.00 | 0.00 |
| 3-2 | candidate_2 | 1.00 | 1 | 0.00 | 0.00 |
| 3-2 | candidate_3 | 1.00 | 1 | 0.00 | 0.00 |

Inspect leading disagreements for semantic-defect alignment, severity judgment, source ambiguity, explanation/score coherence, and possible run-to-run variation. This review is diagnostic only.

The scatter plot uses human labels on the x-axis and continuous AI scores on the y-axis, with one point per candidate.
