# AI Evaluator v1.6 continuous freeze record

**Status: FROZEN FOR DEVELOPMENTAL HOLDOUT AND FORMAL EVALUATION.** The authoritative freeze timestamp, evaluator binding, and SHA-256 values are in `ai_v16_frozen_evaluator_manifest.json`; the companion `ai_v16_frozen_artifact_hashes.json` inventories the frozen files.

## Decision and scope

The approved prompt `ai_evaluator_v2_prompt_revision_6_continuous_draft.md`, schema `ai_evaluator_v2_output_schema_revision_1_1_continuous_draft.md`, and contract `evaluation/friedrich_v2/ai_v16_continuous_contract_draft.py` are frozen **at their existing bytes**. Their historical filenames and draft wording are retained for provenance; this record establishes their v1.6 frozen status. No semantic rule, scoring rubric, schema logic, candidate input boundary, human label, or calibration artifact was edited as part of the freeze. No post-calibration prompt tuning was performed.

The P1–P4 semantic construct rules and all other pre-scoring developer-prompt text are byte-identical to the approved v1.5-aligned design. The candidate-level user template is also byte-identical. The v1.6 `overall_score` remains one direct holistic continuous value in `[0,1]`; the five-level score-to-severity mapping is not part of this freeze.

The approved `ai_v16_continuous_calibration_protocol_draft.md` and `ai_v16_continuous_calibration_analysis_spec_draft.md` are supporting methodological records, frozen by hash without rewriting their historical draft language. Calibration results remain developmental evidence, not independent final validation. No acceptance threshold was applied.

## Execution binding

Each candidate receives one independent stateless request with only `case_id`, `candidate_id`, the original process text, frozen ActivityGraph JSON, and deterministic textual rendering. The developer prompt and strict output schema are the frozen shared evaluator instructions. Human labels, previous AI results, and Code V3.1 results are outside the request boundary. The model is `gpt-5.4-2026-03-05` with `medium` reasoning effort, `store=false`, and omitted temperature and `top_p`; seed is unsupported and omitted. The deterministic renderer, parser, validator, and one permitted exact-request technical retry are identified and hashed in the manifest.

## Calibration disposition

The completed 18-candidate, six-case calibration and its metrics are recorded in `ai_v16_calibration_freeze_summary.md`. The five largest disagreements were manually reviewed. Each was explainable by severity or partial-credit judgment, with only narrow diagnostic wording issues already covered by the current rules. No general evaluator-methodology concern was identified and no prompt or rubric change was justified.

This freeze authorizes the identified v1.6 configuration for later developmental holdout and formal evaluation under separate tasks. It does not record either later evaluation as having run.
