# AI Evaluator v1.6 continuous calibration runner — implementation report

**Status:** Implemented for pre-run review. No v1.6 candidate call, calibration, holdout, or formal evaluation was executed. V1.6 is not frozen.

## Versioned implementation

- `evaluation/friedrich_v2/run_ai_v2_calibration_v16_continuous.py` provides separate `preflight`, `run`, and `compare` commands. It requires a new, collision-free `ai_v16_calibration_18_*` directory under `evaluation/friedrich_v2/results` when someone later authorizes execution.
- `evaluation/friedrich_v2/analyze_ai_v16_continuous.py` implements full-precision candidate errors, MAE, median and maximum absolute error, tied maximum identities, average-rank Spearman, descending-error review order, a comparison CSV, and a standalone descriptive scatter SVG (`human_label` x-axis, `ai_score` y-axis).
- `evaluation/friedrich_v2/tests/test_ai_v16_continuous_runner_static.py` contains synthetic/static tests only.

The runner binds to approved draft prompt `ai-evaluator-v2-prompt/1.6`, schema `ai-evaluator-v2/1.1`, model `gpt-5.4-2026-03-05`, medium reasoning, omitted temperature/top_p/seed, `store=false`, the existing deterministic renderer and parser, and the same one-exact-request technical retry policy. It checks approved draft hashes and compares all 18 candidate identity, process-text, ActivityGraph, and rendering records to the prior frozen calibration manifest before a future run. No substitution or additional candidate is permitted.

## Execution and label gate

The future `preflight` command reads only configuration and frozen candidate artifacts. The future `run` command constructs one candidate-level request from the five approved input components, saves request records and hashes, raw responses, parsed results, exact decimal score text, usage, retries, and an 18-slot technical ledger. Completed candidate checkpoints are reused instead of making duplicate valid calls. A failed candidate remains marked as a technical exception and blocks comparison.

The `compare` command accepts only the `all_ai_results_saved` state. Before loading labels it checks all 18 identities, result validation, saved result and usage hashes, slot statuses, request boundary and hashes, raw responses, and checkpoints. Only then does it read the fixed semicolon-separated human calibration file and join the 18 recorded labels by identity. Human labels, Code results, previous AI results, BPMN references, semantic inventories, and cross-candidate context are never sent to the model.

## Scoring and analysis contract

- **Continuous scores remain continuous.** Any finite JSON numeric score in `[0,1]` is permitted, subject to the no-defect endpoint invariant. No quarter-point-only restriction remains.
- **Human labels remain unchanged.** They are fixed ordinal numeric reference anchors; the runner writes no label file.
- **No AI score quantization occurs.** Exact decimal score values are retained in the result JSONL and used by the comparison module. Decimal arithmetic expands its precision to accommodate the longest score. The runner also checks the exact JSON decimal at the `1.00` endpoint so binary-float parsing cannot reclassify a value just below one. CSV errors and metrics are calculated before display rounding.
- **MAE and Spearman have different purposes.** MAE is numeric distance to the human anchors; tie-aware Spearman describes ordering, with average ranks for ties and NA if rank variance is zero.
- **No acceptance threshold was introduced.** The comparison reports evidence and sorts candidates by absolute error without an automatic pass/fail or review cutoff.

The scatter plot is generated only after a future completed comparison. No real calibration plot or data preview was created in this task.

## Static verification

`python3 -m unittest evaluation.friedrich_v2.tests.test_ai_v16_continuous_runner_static -v` passed **12 tests** using synthetic scores and requests. The checks cover `0.83`, `0.61`, `0.37`, both endpoints, invalid values, exact decimal serialization and long-decimal calculations, float rounding just below the endpoint, the frozen 18-candidate roster and mutation detection, the five-component request boundary, human-label access separation, MAE, median, maximum, tie-aware Spearman, undefined rank correlation, and synthetic scatter structure. `py_compile` also passed. No API endpoint was called.

The implementation has not been exercised against live Structured Outputs. Pre-run review should inspect the versioned runner and its output-directory choice before any API execution.
