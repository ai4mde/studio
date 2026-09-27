# AI Evaluator v1.6 continuous developmental holdout

The frozen v1.6 evaluator was applied to 15 candidates in five cases. These cases had been examined in earlier evaluator versions; this is developmental holdout evidence.

- MAE: **0.0613**.
- Median absolute error: **0.0500**.
- Maximum absolute error: **0.1800**.
- Tie-aware Spearman: **0.8792**.
- AI score range: **0.4–1**.
- Technical failures: **0**; retries: **0**.
- Ambiguity flags: **4**; human-review flags: **4**.
- Human labels were loaded only after all 15 AI outputs were saved and validated.
- AI scores remain continuous and unquantized. No numeric acceptance threshold was applied.

## Candidate-level comparison

| Case | Candidate | Human | AI | Signed difference | Absolute error |
|---|---|---:|---:|---:|---:|
| 10-9 | candidate_3 | 1.00 | 0.82 | -0.18 | 0.18 |
| 10-14 | candidate_2 | 0.25 | 0.41 | 0.16 | 0.16 |
| 10-14 | candidate_3 | 0.25 | 0.4 | 0.15 | 0.15 |
| 3-5 | candidate_3 | 0.75 | 0.86 | 0.11 | 0.11 |
| 3-5 | candidate_2 | 0.75 | 0.84 | 0.09 | 0.09 |
| 10-11 | candidate_2 | 0.75 | 0.68 | -0.07 | 0.07 |
| 3-5 | candidate_1 | 0.75 | 0.81 | 0.06 | 0.06 |
| 10-14 | candidate_1 | 0.75 | 0.8 | 0.05 | 0.05 |
| 10-11 | candidate_1 | 0.75 | 0.78 | 0.03 | 0.03 |
| 10-11 | candidate_3 | 0.75 | 0.77 | 0.02 | 0.02 |
| 5-1 | candidate_1 | 1.00 | 1 | 0.00 | 0.00 |
| 5-1 | candidate_2 | 1.00 | 1 | 0.00 | 0.00 |
| 5-1 | candidate_3 | 1.00 | 1 | 0.00 | 0.00 |
| 10-9 | candidate_1 | 1.00 | 1 | 0.00 | 0.00 |
| 10-9 | candidate_2 | 1.00 | 1 | 0.00 | 0.00 |

## Qualitative review

The five largest gaps were reviewed against the frozen process texts, ActivityGraphs, fixed human rationales, and saved AI explanations. This is descriptive review, not an acceptance test.

| Candidate | Human / AI | Same decisive defect? | Main reason for gap | AI missed a major defect? | Explanation overreach? | General methodology concern? |
|---|---:|---|---|---|---|---|
| `10-9/candidate_3` | 1.00 / 0.82 | No: the human found no defect; AI provisionally inferred a missing MPO-initiated route. | Source ambiguity and possible model variation. | No. | Possible: the source does not clearly say MPO-initiated changes bypass review. | No demonstrated systematic rule failure. |
| `10-14/candidate_2` | 0.25 / 0.41 | Yes: four alternative bill cases are made a mandatory sequence. | Severity and partial-credit judgment. | No. | Possible only for the ancillary claim that bill-sending triggers must be explicit actions. | No. |
| `10-14/candidate_3` | 0.25 / 0.40 | Yes: the same alternative cases are serialized. | Severity and partial-credit judgment. | No. | The AI flagged uncertainty about whether bill-sending is an action or trigger; the core defect remains. | No. |
| `3-5/candidate_3` | 0.75 / 0.86 | Yes: the Registry Manager's posting and Cashier's meantime work are serialized. | Severity judgment for a bounded successful-path defect. | No. | No material overreach found. | No. |
| `3-5/candidate_2` | 0.75 / 0.84 | Yes: the same meantime activities are serialized. | Severity judgment for a bounded successful-path defect. | No. | No material overreach found. | No. |

`10-9/candidate_1` and `10-9/candidate_3` have byte-identical ActivityGraphs and the same process text. They received scores 1.00 and 0.82 in independent stateless calls. Both outputs flagged the source initiation sentence as ambiguous and requested human review. This is meaningful candidate-level interpretive variability, and it should remain visible when reading the holdout result. It does not establish that the frozen P1–P4 rules systematically misrepresent the intended construct; the current ambiguity/review rules surfaced the uncertainty. No candidate was rerun to resolve the difference.

**General methodology concern identified: NO.** The other leading differences preserve the same root diagnoses, and no prompt tuning, label change, or numeric acceptance threshold was introduced. The holdout remains developmental evidence; no formal 120 or Code comparison was run.
