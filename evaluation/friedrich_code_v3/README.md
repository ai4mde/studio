# Thesis-final Code-based evaluator

The validated scoring entry point is `evaluation.friedrich_code_v3.combined_candidate_v8.evaluate_combined_candidate_v8`. It is the unchanged `friedrich-code-combined-construct-candidate/8` implementation used in the final 40-case, 120-candidate validation. Earlier `evaluate_inventory_candidate_v3`, `combined_candidate_v2/v3`, V3.1/V3.2 runners, and intermediate guards are historical entry points. Some older-named modules remain live import dependencies of v8; do not remove them simply because of their names.

## Four constructs

- **Action:** presence and semantic correctness of required business activities, including missing, unsupported, duplicated, or incorrect activities.
- **Flow:** source-required activity precedence between reliably matched semantic activities. Indirect paths are valid. A required pair with an absent or unreliable Action match is indeterminate, not automatically a Flow false negative.
- **Control Node:** presence and semantic role of Decision, Merge, Fork, Join, Start, and End nodes. Node presence is separate from routing quality; a semantically explicit shared node may cover compatible source roles.
- **Control Relation:** branch routing and conditions, convergence, synchronization, loops, continuation, and termination behavior.

Each dimension uses fact-based true positives (TP), false positives (FP), false negatives (FN), precision, recall, and F1. Indeterminate required facts stay in the coverage denominator and make candidate-level dimension F1 null under the all-slot contract. A genuinely non-applicable dimension is N/A with null F1, never zero. N/A dimensions are omitted symmetrically from candidate-level Overall averaging. The **Formal Overall Code F1** is a separate dataset-level summary: the mean of the four pooled dimension F1 values; it is not a candidate-level score.

## Validated results

The final normal validation completed **120/120 candidates** (40 cases × 3), and the targeted control regression passed **65/65 checks**. Formal Overall Code F1 = **0.8499803891**. Pooled F1 by dimension: Action 0.9096153846, Flow 0.8942486085, Control Node 0.9260450161, Control Relation 0.6700125471. Remaining genuine indeterminate facts and human-review items are preserved; the validation did not optimize scores or Code–AI correlation.

The authoritative content freeze is [`freeze/thesis_final_v8_20261005/final_code_v8_freeze_manifest.json`](freeze/thesis_final_v8_20261005/final_code_v8_freeze_manifest.json), SHA-256 `cfcfc68de14208c0f7f10ed6f85e8e89a1ff7aa283c8fed24f2ea857439434ef`. It identifies the exact v8 code, corrected Flow and Action eligibility snapshots, frozen 120 graphs, sibling source archive, model snapshot, environment, and validated outputs. The frozen candidate result SHA-256 is `fc4cf409a789846a037cbb22f8816c5bac8f86302a05e2768a70ebd9491727b3`.

## Verify or replay

From the repository root, use the portable scripts in `portable_replay_v1/`:

```sh
python evaluation/friedrich_code_v3/portable_replay_v1/verify_frozen_v8.py --model-snapshot /path/to/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41
python evaluation/friedrich_code_v3/portable_replay_v1/replay_frozen_v8.py --model-snapshot /path/to/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41
```

Verification checks content without computing scores. The portable replay completed 120/120 candidates; all parsed candidate objects and aggregate metrics matched the frozen validation. Nine raw JSONL rows used a different diagnostic dictionary-key order, so their raw file hashes differ while their canonical candidate-object hashes match. See `portable_replay_v1/portable_replay_test_report.md`.

The sibling `studio-semantic-v2` runtime files are supplied by the verified archive and small hashed taxonomy addendum; a mutable sibling worktree is not required. The approximately 932 MB pinned sentence-transformer snapshot must be obtained separately and verified. Exact environment verification expects Python 3.12.14 on macOS arm64 and the 44 recorded package identities. See `portable_replay_v1/clean_checkout_requirements.md`. The older `run_full_construct_validation_v6.py` remains frozen validation provenance; its absolute-path historical preflight makes it unsuitable as the clean-checkout replay command.
