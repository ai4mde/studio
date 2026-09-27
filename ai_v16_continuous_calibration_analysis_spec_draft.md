# v1.6 continuous calibration — draft analysis specification

This is a specification for a **future** label-comparison script, not a runner or an analysis of candidate results.

## Inputs and gate

1. Read the frozen 18-slot calibration identity list from the existing v1.5 calibration manifest. Require exactly six cases and three candidates per case, with no duplicate `(case_id, candidate_id)` pair.
2. Before reading labels, require 18 valid v1.6 parsed AI results with exactly those identities and a completed technical manifest. Preserve each original numeric `overall_score` in `[0,1]`; do not quantize or map it to a category. If a slot failed, keep it in the technical ledger and withhold the final 18-slot metrics until resolved under the approved technical policy.
3. Only then read `evaluation/friedrich_v2/review/human_calibration_selected_cases/human_calibration.csv` using semicolon (`;`) separation. Join its `Case` and `Candidate` columns to the frozen roster, and read the existing `Human Score` value. Reject missing or duplicate labels within the 18-slot join; ignore records outside that roster. Do not edit or interpolate labels.
4. Calculate from the saved parsed AI scores and joined anchors. Parse decimal JSON numbers without pre-rounding where practical; retain the original response and numeric precision for audit.

## Candidate-level table: exact required columns

| Column | Type and source | Formula or rule |
|---|---|---|
| `case_id` | String; frozen roster and AI result | Must match both sources exactly. |
| `candidate_id` | String; frozen roster and AI result | Must match both sources exactly. |
| `human_label` | Decimal; existing `Human Score` | Must be one of the five recorded ordinal anchors; never synthesize a value. |
| `ai_score` | Decimal; v1.6 `overall_score` | Original continuous value; do not round to a human anchor. |
| `signed_difference` | Decimal | `ai_score - human_label`; positive means AI judged quality higher. |
| `absolute_error` | Nonnegative Decimal | `abs(signed_difference)`. |

Write all 18 rows with full calculation precision. A sorted review view uses `absolute_error` descending, then frozen roster order for ties. The table may format copies for display, but the stored score and all metrics must use the unrounded value. For the illustrative pair `human_label=0.75`, `ai_score=0.68`, the signed difference is `-0.07` and absolute error is `0.07`.

## Aggregate formulas

Let `n=18` and `e_i=abs(ai_score_i - human_label_i)` for each frozen candidate.

- **MAE, primary:** `sum(e_i) / n`.
- **Median absolute error, primary:** sort `e_i` ascending; for 18 rows, average the 9th and 10th values (one-based positions).
- **Maximum absolute error, primary:** `max(e_i)`. Keep the associated candidate identities in the report; list all ties.
- **Spearman rank correlation, secondary:** assign ascending average ranks separately to the human-label vector and AI-score vector. Tied values share the mean of the positions they occupy. Compute Pearson correlation of these two rank vectors:

  `rho = sum((R_h_i - mean(R_h)) * (R_a_i - mean(R_a))) / sqrt(sum((R_h_i - mean(R_h))^2) * sum((R_a_i - mean(R_a))^2))`.

  Report `rho` as undefined/NA when either rank vector has zero variance. Human-label ties must not be broken arbitrarily. Spearman describes ordering only; it is not a substitute for numerical error.

Report the metric values descriptively, with the sample size and no pass/fail threshold. Do not compute historical exact agreement, within-one-level agreement, or a five-by-five confusion table as primary metrics. Do not quarter-round AI scores to recreate them.

## Diagnostic review fields kept separate from score calculations

The future report may show the saved AI `severity`, `main_error_type`, diagnostic summaries, `confidence`, `ambiguity_flag`, `ambiguity_explanation`, `requires_human_review`, and `review_reason` alongside the sorted error table. They do not enter the formulas or change the human anchor. For the largest disagreements, record whether the semantic defect aligns with the human rationale, whether the gap is mainly severity, whether source ambiguity or explanation/score inconsistency is involved, and whether stochastic variation is plausible. No automatic error threshold, review count, label revision, or prompt edit follows from this table.

## Reuse and limitations

For the later 15-slot developmental holdout, substitute `n=15` and its frozen identities and labels; the median is the 8th sorted absolute error. Use the same six columns, MAE, maximum, tie-aware Spearman, and review ordering. No holdout is run now. Both sets have developmental exposure, and the ordinal anchors plus within-case dependence limit inferential claims.
