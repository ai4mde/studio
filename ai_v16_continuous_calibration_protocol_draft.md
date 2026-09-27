# AI Evaluator v1.6 continuous calibration protocol — draft

**Status:** Methodology design for human review. This document does not freeze v1.6 or authorize a candidate run.

## 1. Purpose and reference judgments

Assess how closely the v1.6 evaluator's **continuous** whole-graph scores align with the existing human calibration judgments. Each AI score remains its returned numeric value in `[0,1]`. Each historical human label remains the recorded ordinal anchor (`0.00`, `0.25`, `0.50`, `0.75`, or `1.00`). Compare these numbers directly; do not turn the AI score into an ordinal category or interpolate a new human label.

The numeric distance to an ordinal anchor is a descriptive calibration measure. It does not imply that the original human annotator supplied a continuous judgment.

## 2. Calibration sample and execution boundary for a later run

Use exactly the existing v1.5 calibration roster: **six cases, three candidates each, 18 slots**. The case IDs are `1-1`, `3-2`, `3-4`, `6-4`, `8-2`, and `9-5`. Verify candidate IDs and frozen process-text, ActivityGraph, and rendering hashes against the existing calibration manifest before a future call. Join human labels to those 18 identities only; the source label file contains other records that are outside this calibration roster. Do not choose or replace candidates based on known results.

These cases were already used during evaluator development. The resulting calibration evidence will be **developmental**, not independent final validation.

For a future run, use one independent stateless call per candidate with the approved v1.6 prompt, schema, model, and reasoning setting. Preserve the existing technical retry policy unless separately changed. Record exact prompt and schema hashes, model, reasoning effort, parser and renderer identities, candidate hashes, request identities and hashes, raw responses, parsed scores, status, and retry count. Keep human labels and previous AI or Code results out of candidate requests. Save and validate all 18 AI slots before loading the fixed human labels. Preserve a failed slot as a technical exception; do not silently omit it or rerun a valid score because it is inconvenient. A final 18-candidate metric summary requires all 18 valid results.

## 3. Primary error measures

For each candidate, let `a` be the original continuous AI score and `h` its unchanged human anchor. Calculate `absolute_error = abs(a - h)` **before display rounding**. For example, `a=0.68` and `h=0.75` give an error of `0.07`, without treating `0.68` as an exact `0.75` match.

Report these primary measures over all 18 valid paired rows:

1. **Mean absolute error (MAE):** arithmetic mean of candidate absolute errors; the main numerical calibration-error measure.
2. **Median absolute error:** median of the 18 absolute errors, to show the typical discrepancy with less influence from one unusual candidate.
3. **Maximum absolute error:** the largest candidate discrepancy.
4. **Candidate-level table:** one row per candidate with identity, human anchor, unrounded AI score, signed difference, and absolute error. Sort the review view from largest to smallest absolute error, with a stable identity tie-break.

Retain full returned score precision in the underlying table and calculations. Rounding in prose or display must be labeled as display-only. Do not round AI scores to the nearest quarter point.

## 4. Secondary rank measure

Report **Spearman rank correlation** between the 18 human anchors and continuous AI scores as a secondary, descriptive measure of quality ordering. Rank both vectors in ascending score order; assign every tied value the average of the rank positions it occupies. Compute Pearson correlation of those two average-rank vectors. If either vector has no rank variance, report Spearman as undefined, not zero.

Spearman asks whether higher-rated candidates tend also to receive higher AI scores. It is not exact-score agreement and does not replace MAE. With 18 candidates clustered within six cases and tied ordinal human labels, use it descriptively; do not claim strong population inference or set a correlation cutoff.

## 5. Ambiguity and candidate-level review

After the later run, sort all 18 rows by absolute error descending. Inspect the largest disagreements qualitatively and record whether the AI and human identified the same semantic defect, whether the difference is mainly severity judgment, whether source ambiguity is involved, whether score and explanation cohere, and whether stochastic variation is plausible. Keep the AI ambiguity and review flags visible as context. Ambiguity does not automatically change the AI score, human anchor, or error calculation.

Do not create an automatic large-error threshold or a fixed number of candidates requiring review. Record which rows were reviewed and why. This review is diagnostic; it does not automatically trigger candidate-specific prompt tuning or label changes.

## 6. Interpretation and limitations

Interpret MAE together with the distribution and maximum of candidate errors, the sorted candidate table, ambiguity context, and descriptive rank alignment. No pass/fail threshold is defined. The historical exact-agreement count, within-one-level count, and five-by-five confusion matrix are **not primary v1.6 metrics**. Do not produce a quarter-rounded comparison merely to recreate them; any optional non-primary comparison would require separate approval and an explicit limitations note.

The anchors are ordinal, the calibration set is small and developmental, candidates share cases, and LLM evaluations can vary between independent runs. Do not introduce multi-run averaging automatically. If score stability is questioned later, address it in a separate reproducibility design rather than silently changing this protocol.

## 7. Later developmental holdout reuse

After calibration review and a separate decision to proceed, apply the same formulas and tie handling to the existing **15-candidate developmental holdout**: MAE, median and maximum absolute error, a candidate-level error table, and descriptive Spearman correlation. Keep its historical labels fixed. Those cases were also examined during earlier evaluator development and must not be described as fully unseen. Do not run them under this draft.

## 8. Static review questions

1. **Does the protocol preserve the AI score as genuinely continuous?** Yes. It uses the original numeric score directly in every error and rank calculation.
2. **Does it avoid converting AI scores back to five ordinal buckets?** Yes. No quarter rounding or category mapping is performed.
3. **Does it preserve historical human labels unchanged?** Yes. They remain fixed ordinal reference anchors joined by candidate identity.
4. **Are MAE and rank correlation used for different purposes?** Yes. MAE measures numerical distance to anchors; Spearman measures relative ordering.
5. **Has an arbitrary acceptance threshold been introduced?** No.
6. **Can the same protocol later be reused for the developmental holdout?** Yes, with the same calculations over its 15 frozen candidates after separate authorization.
7. **Has candidate-specific tuning been introduced?** No.

The exact future table columns and formulas are specified in `ai_v16_continuous_calibration_analysis_spec_draft.md`.
