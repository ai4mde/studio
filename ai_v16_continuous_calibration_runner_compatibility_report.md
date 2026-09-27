# AI Evaluator v1.6 runner — compatibility and boundaries

## Approved draft identity

| Item | Bound value | Static compatibility result |
|---|---|---|
| Prompt | `ai_evaluator_v2_prompt_revision_6_continuous_draft.md`; `ai-evaluator-v2-prompt/1.6` | Hash checked against the approved draft hash manifest. |
| Schema | `ai_evaluator_v2_output_schema_revision_1_1_continuous_draft.md`; `ai-evaluator-v2/1.1` | Numeric `overall_score` range `[0,1]`; all other diagnostic and review fields retained. |
| Parser/validator | Existing `extract_output_text`; separate `ai_v16_continuous_contract_draft.validate_result` | Non-quarter values accepted; the old five-value and exact severity lookup are not used by the new runner. |
| Model/configuration | `gpt-5.4-2026-03-05`, medium reasoning, omitted temperature/top_p/seed, independent stateless calls, `store=false` | Same configuration declarations as v1.5. |
| Renderer/template | Existing deterministic renderer and exact candidate-level template | Same five input components; no additional context. |
| Technical retry | One exact-request retry after a technical failure, maximum two attempts; no SDK retry | Matches the historical policy, with per-slot status and checkpoint records added for durability. |
| Calibration roster | Cases `1-1`, `3-2`, `3-4`, `6-4`, `8-2`, `9-5`; three candidates each | Read-only check confirms all 18 full candidate records equal the completed v1.5 calibration manifest, including process, graph, and rendering hashes. |

## Historical isolation

No historical prompt, schema, runner, human label, calibration result, holdout result, formal result, or Code V3.1 artifact was modified. The v1.5 calibration core still rejects non-quarter scores by design; the v1.6 runner imports only its unchanged artifact, rendering, template-substitution, and response-transport helpers and binds to the separate continuous validator. Existing v1.5 scripts remain versioned to their original runs.

The v1.6 comparison module replaces the old exact-agreement, within-one-level, and five-by-five confusion outputs with the approved continuous measures. It does not round AI scores to human categories. Human labels are read only after all 18 AI slots have been saved and validated.

## Future run boundary

The implementation requires three deliberate commands in a new v1.6 results directory: `preflight`, `run`, then `compare`. None was invoked here. `preflight` creates a run manifest but does not freeze the evaluator; `run` is the only command that can call the API; `compare` is the only command that can read human labels. A future holdout and formal runner are not implemented by this calibration task. The analysis formulas can be reused later on the developmental holdout after separate authorization, but its roster and label gate will need their own versioned binding.

The live API contract and actual calibration outcomes remain untested. No pass/fail threshold, multi-run averaging, score tuning, candidate-specific wording, or label revision was added.
