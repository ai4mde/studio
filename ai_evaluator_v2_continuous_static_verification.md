# AI Evaluator v1.6 continuous-scoring draft — static verification

Status: **draft only; static checks passed.** No candidate evaluation, calibration, holdout, formal run, Code-vs-AI comparison, correlation, or human review was performed. The draft is not frozen.

## Checks performed

The reproducible check is `python3 -m evaluation.friedrich_v2.verify_ai_v16_continuous_draft` from the repository root. It reads only the prompt, schema, and draft validator files; it does not load candidate inputs or call an API.

| Check | Result |
|---|---|
| P1 Action boundaries, P2 Control roles, P3 recurrence, P4 non-cascading Control judgment, and all other pre-scoring developer-prompt text | **PASS** — byte-identical to v1.5 within the exact developer prompt before `Whole-graph scoring rubric`. |
| Non-scoring output instructions | **PASS** — identical except the scoring-dependent severity sentence. |
| Candidate-level user template and input substitution rules | **PASS** — byte-identical to v1.5. The input boundary is unchanged. |
| Model, reasoning effort, and sampling declarations | **PASS** — same `gpt-5.4-2026-03-05`, medium reasoning, omitted temperature/top_p/seed, independent stateless calls. |
| New prompt scoring instruction | **PASS** — direct holistic score in `[0,1]`; no five-choice instruction, fixed deductions, quarter-point rounding, severity-to-score lookup, or diagnostic averaging. |
| Strict schema structure | **PASS** — all required root fields, diagnostic enums, ambiguity/review fields, and closed-object constraints remain unchanged except the scoring-specific version, score range, and severity description. |
| In-range non-quarter values | **PASS** — `0.83` and `0.61` satisfy the new numeric `minimum: 0.0` / `maximum: 1.0` schema field and the draft result validator. Additional non-quarter values were checked. |
| Old values remain numerically valid | **PASS** — `0.00`, `0.25`, `0.50`, `0.75`, and `1.00` satisfy the new range; they are no longer exhaustive choices. |
| Out-of-range and non-finite values | **PASS** — negative and above-one values, booleans, numeric strings, NaN, and infinity are rejected by the draft validator; the schema range excludes out-of-range finite numbers. |
| No-defect endpoint | **PASS** — `1.00` requires `main_error_type=none` and `severity=none`; below 1.00, both must be non-`none`, without any other numeric severity cutoff. |
| Parser compatibility | **PASS** — the existing `extract_output_text` function is reused unchanged; the separate draft validator accepts continuous values. Historical v1.5 validation remains untouched. |

OpenAI's [Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs) lists `minimum` and `maximum` as supported numeric schema properties for standard models. The checks here are static; the draft schema was not submitted to the API.

## Compatibility boundary

The legacy calibration and formal runners still carry five-level score validation or reporting logic. They must not be repointed at this draft without the changes listed in `ai_evaluator_v2_continuous_downstream_inventory.md`. In particular, a future continuous-score validation protocol must define how continuous AI scores are compared with any ordinal human labels before a validation run; no threshold is chosen here.

The new artifacts and their SHA-256 hashes are recorded in `ai_evaluator_v2_continuous_draft_hashes.json`. Frozen v1.5 prompt, schema, calibration, holdout, and formal artifacts remain unchanged.
