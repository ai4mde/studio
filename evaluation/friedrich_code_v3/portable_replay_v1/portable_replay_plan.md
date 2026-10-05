# Portable replay plan for unchanged Code evaluator v8

## Identity and scope

The scoring entry point remains `evaluation.friedrich_code_v3.combined_candidate_v8.evaluate_combined_candidate_v8`. This wrapper does not edit that module, any scoring component, inventory, candidate, or frozen output. It replaces only the historical v6 runner's path assumptions and reporting preflight. The authoritative frozen run is `full_construct_validation_v6_20261005_180552_249358utc`.

The original freeze manifest, dependency inventory, branch scope, and sibling archive remain unchanged. A runtime dependency omitted from the original archive was identified: `evaluation/friedrich_v3/compatibility_v3.json`, read by the archived Action matcher through `compatibility_veto`. The identical sibling file is copied into `runtime_addendum/friedrich_v3/compatibility_v3.json` and pinned by SHA-256 `52d744c7fd01b7a569ccc8e8c2482dfebc9eb56db5983865616922521532692b`. This addendum belongs to the portable replay package, not the original content freeze.

## Mode A: content verification

Run `verify_frozen_v8.py` using the recorded Python environment. It verifies the freeze manifest sidecar, catalog hashes, all 278 MUST_COMMIT checkout paths by relocated relative path, every one of the 132 sibling archive members, the taxonomy addendum, all 30 model snapshot paths and the model tree digest, the 44 package identities, the interpreter/platform, the 120 roster identities and frozen candidate graph hashes, the final result hash, and the final validation manifest hash. It does not import the evaluator or compute scores. Candidate technical-status and per-candidate manifests were historical v6 guard inputs; if present they are checked, but a clean branch needs only the frozen roster and candidate graph files.

## Mode B: full execution replay

`replay_frozen_v8.py` first runs Mode A. It extracts the verified archive into a temporary `evaluation` namespace path and adds the pinned taxonomy. It supplies the verified model snapshot through a temporary Hugging Face cache layout. The unchanged v8 code is imported from the checkout and its `FrozenCorpus` object points at the archived process text, reviewed Action inventory, and reference evidence. The 120 graph files are loaded in the original frozen roster order. Each result is written to a new collision-free results directory. The wrapper computes only descriptive aggregate metrics and compares them with frozen outputs; the evaluator's matching/scoring logic is untouched.

The v6 runner's 669 absolute-path historical preflight checks are not used. Most concern unrelated application code or historical candidate manifests; the replay wrapper instead verifies the exact score-relevant modules and data from the freeze package. The absolute `action_scoring_code` paths embedded in the old Control manifest are independently checked against the archive hashes; they are not dereferenced from the old location.

## Comparison standard

The frozen v6 JSONL uses insertion order from Python dictionaries. Nine candidate rows replayed with a different order of keys inside diagnostics, although the parsed candidate objects and all four aggregate summaries were identical. Thus a raw JSONL SHA-256 difference alone is not a scoring difference. The replay package reports both raw SHA-256 and a canonical sorted-key candidate-object SHA-256, plus candidate object differences and aggregate metrics. It never substitutes or rewrites the frozen result.

## Commands

From the checkout root:

```sh
.venv-friedrich-v2/bin/python evaluation/friedrich_code_v3/portable_replay_v1/verify_frozen_v8.py --model-snapshot /path/to/pinned/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41
.venv-friedrich-v2/bin/python evaluation/friedrich_code_v3/portable_replay_v1/replay_frozen_v8.py --model-snapshot /path/to/pinned/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41
```

Omit `--model-snapshot` only on the original machine where the recorded cache path still exists. Replay outputs appear under `evaluation/friedrich_code_v3/results/portable_v8_replay_*`; no existing result directory is reused.
