# AI Evaluator v1.6 developmental calibration freeze summary

**Frozen roster:** six cases (`1-1`, `3-2`, `3-4`, `6-4`, `8-2`, `9-5`) × three candidates = **18 completed candidates**. The source is `evaluation/friedrich_v2/results/ai_v16_calibration_18_20260925_201629utc_connectivity1/`; its run manifest, saved responses, request records, results, comparison, metrics, and plot are preserved unchanged and inventoried by SHA-256 in the freeze hash record.

| Descriptive measure | Value |
|---|---:|
| Mean absolute error | 0.0939 |
| Median absolute error | 0.0750 |
| Maximum absolute error | 0.3700 |
| Tie-aware Spearman | 0.9560 |

Displayed values are rounded from the saved metrics; the underlying continuous AI scores and calculations were not quantized. The fixed human labels were ordinal reference anchors and were not rewritten. No acceptance or pass/fail threshold was used.

The five largest disagreements were manually reviewed: `1-1/candidate_2`, `9-5/candidate_2`, `1-1/candidate_3`, `9-5/candidate_3`, and `9-5/candidate_1`. In all five, the AI identified the decisive underlying semantic defects also cited by the human rationale. The numerical gaps principally reflected severity and partial-credit judgment. The review noted a narrow Flow-attribution issue for `1-1/candidate_2` and an ancillary unsupported timeout claim for `9-5/candidate_3`; current v1.6 rules already address both. All five disagreements were judged explainable, with **no general methodology concern** and **no post-calibration prompt tuning**.

This was a developmental calibration sample with within-case dependence and fixed ordinal human anchors. The metrics are descriptive and do not establish an independent validation result. No holdout, formal 120-candidate run, Code comparison, Code correlation, or new adjudication was performed in this freeze task.
