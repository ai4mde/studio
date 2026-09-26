# Certified Code Evaluator V3.1 dependency record

This note indexes dependencies of the final 40-case × 3-candidate certification. It does not change the evaluator, frozen inventories, scores, or certification findings.

The authoritative file identities and SHA-256 values are in `results/v3_1_final_certification_20260924_2135utc/run_identity_before.json`, under `pre_run_file_hashes`. That snapshot recorded 644 files; `run_integrity.json` records matching pre-run and post-run snapshots. The final certification bundle also contains `pre_run_verification.json`, `certification_validation.json`, and `reporting_validation.json`.

## Dependencies outside this commit scope

- The sibling `../studio-semantic-v2/evaluation/` checkout supplied the Action implementation and source evidence. The snapshot records 122 files there: `friedrich_semantic/action.py` (SHA-256 `1fc985a2e50da84d12f93134989c970c7e8f36b747c17f6439a9c9775d44b154`), `friedrich_semantic_v2/evaluator_adapter.py` (SHA-256 `12d3bfaf878d6d056d0ab815d511e4431f5a8a3fa9674922d6f815a36571b80e`), and each of 40 cases' `process_text.txt`, `inventory_reviewed.json`, and `reference_evidence.json` (120 files; individual hashes are in the authoritative snapshot). The evaluator also imports `friedrich_v3` and semantic modules from that sibling checkout; the snapshot does not enumerate every imported library file.
- The certification snapshot records 59 files under `api/model/llm/` in the main `studio` checkout. Their paths and individual hashes are in `pre_run_file_hashes`. These broad environment-snapshot files were not copied into this dedicated Code V3.1 commit.
- `run_v3_1_formal.py` references a local sentence-transformer model cache in the sibling `studio-friedrich-scoring` directory. The cache is outside this commit. The model name and revision are declared in the imported Action implementation.

The 362 frozen 120-candidate input files referenced by the formal runner, the frozen V3.1 Control and Flow inventories, the final blocker evidence, and the 21-file certification bundle are included in this commit scope. This commit preserves the certified evaluator and results but does not by itself make the external sibling checkout or model cache portable. The certification hash snapshot remains the authoritative record; this note adds no new acceptance criteria or methodology changes.
