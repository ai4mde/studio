# Frozen AI Evaluator v1.6 — formal 120-candidate evaluation

The frozen continuous evaluator scored all 40 cases × three candidates independently. These are descriptive AI-only results; no human or Code Evaluator judgments were supplied to the requests or used in this summary.

- Completed candidates: **120**; technical failures: **0**; retries: **0**.
- Score range: **0.24–1.0**.
- Mean: **0.7978**; median: **0.8500**.
- Population standard deviation: **0.2266**.
- Uncertainty flags: **29**; human-review flags: **29**.
- AI scores are continuous and unquantized. No oracle or human-selected score was created.

## Severity distribution

| Severity | Candidates |
|---|---:|
| major | 31 |
| minor | 6 |
| moderate | 30 |
| none | 53 |

## Main error type distribution

| Main error type | Candidates |
|---|---:|
| extra_or_duplicated_action | 2 |
| incorrect_action_meaning_or_grouping | 1 |
| missing_action | 3 |
| mixed_or_cascading | 14 |
| none | 53 |
| wrong_branching_or_condition | 10 |
| wrong_continuation_or_termination | 16 |
| wrong_loop_or_recurrence | 14 |
| wrong_parallelism_or_synchronization | 7 |

## Case-level descriptive summaries

Each row summarizes the three frozen candidates for that case; it does not select a best candidate.

| Case | n | Min | Max | Mean | Median |
|---|---:|---:|---:|---:|---:|
| 1-1 | 3 | 0.34 | 0.41 | 0.3633 | 0.34 |
| 1-2 | 3 | 0.62 | 0.7 | 0.6633 | 0.67 |
| 2-1 | 3 | 0.44 | 0.58 | 0.4933 | 0.46 |
| 2-2 | 3 | 0.7 | 0.8 | 0.7433 | 0.73 |
| 3-1 | 3 | 0.92 | 1 | 0.9733 | 1.0 |
| 3-2 | 3 | 0.79 | 1 | 0.8800 | 0.85 |
| 3-3 | 3 | 0.36 | 1 | 0.6067 | 0.46 |
| 3-4 | 3 | 0.68 | 0.69 | 0.6867 | 0.69 |
| 3-5 | 3 | 0.8 | 0.85 | 0.8233 | 0.82 |
| 3-6 | 3 | 0.4 | 0.58 | 0.4700 | 0.43 |
| 3-7 | 3 | 1 | 1 | 1.0000 | 1 |
| 3-8 | 3 | 0.88 | 1 | 0.9300 | 0.91 |
| 4-1 | 3 | 0.68 | 0.73 | 0.7067 | 0.71 |
| 5-1 | 3 | 1 | 1 | 1.0000 | 1 |
| 5-2 | 3 | 1 | 1 | 1.0000 | 1 |
| 5-3 | 3 | 0.76 | 0.84 | 0.7900 | 0.77 |
| 5-4 | 3 | 0.24 | 0.32 | 0.2867 | 0.3 |
| 6-1 | 3 | 0.45 | 0.76 | 0.6333 | 0.69 |
| 6-2 | 3 | 0.93 | 1 | 0.9767 | 1 |
| 6-3 | 3 | 0.57 | 0.72 | 0.6400 | 0.63 |
| 6-4 | 3 | 0.78 | 0.84 | 0.8133 | 0.82 |
| 8-1 | 3 | 0.91 | 1 | 0.9700 | 1 |
| 8-2 | 3 | 0.47 | 0.87 | 0.6067 | 0.48 |
| 9-1 | 3 | 0.84 | 1 | 0.8933 | 0.84 |
| 9-3 | 3 | 1 | 1 | 1.0000 | 1.0 |
| 9-4 | 3 | 1 | 1 | 1.0000 | 1 |
| 9-5 | 3 | 0.43 | 0.64 | 0.5433 | 0.56 |
| 9-6 | 3 | 0.39 | 0.41 | 0.3967 | 0.39 |
| 10-1 | 3 | 1 | 1 | 1.0000 | 1 |
| 10-4 | 3 | 1 | 1 | 1.0000 | 1 |
| 10-5 | 3 | 1.0 | 1 | 1.0000 | 1 |
| 10-6 | 3 | 1 | 1 | 1.0000 | 1 |
| 10-7 | 3 | 1 | 1 | 1.0000 | 1 |
| 10-8 | 3 | 1 | 1 | 1.0000 | 1 |
| 10-9 | 3 | 1 | 1 | 1.0000 | 1 |
| 10-10 | 3 | 0.71 | 1 | 0.8100 | 0.72 |
| 10-11 | 3 | 0.67 | 0.7 | 0.6833 | 0.68 |
| 10-12 | 3 | 1 | 1 | 1.0000 | 1 |
| 10-13 | 3 | 1 | 1 | 1.0000 | 1 |
| 10-14 | 3 | 0.4 | 0.77 | 0.5300 | 0.42 |

The candidate-level scores, diagnostics, technical status, and hashes are in `ai_v16_formal_120_scores.csv`; flagged outputs are in `ai_v16_formal_120_review_flags.csv`. No Code-versus-AI comparison or correlation was performed.
