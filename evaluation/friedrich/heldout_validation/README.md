# Held-out action-matcher validation

## Fixed method

This validation uses the previously fixed normalization, pinned
`all-MiniLM-L6-v2` revision, threshold `0.44`, operation compatibility, and
maximum-weight one-to-one assignment without tuning. The seven pilot case IDs
are excluded. `run_1.json` is used consistently for generated artifacts.

The five held-out cases are:

- `3-1`: simple sequence with repeated retrieval and storage actions
- `3-4`: reminder loop
- `8-2`: job-description decision and correction loop
- `10-7`: decision plus three repeated notifications
- `1-2`: parallel hardware/software work and repetition

## Artifacts

- `heldout_actions.csv`: all extracted reference and generated actions
- `heldout_candidate_matrix.csv`: every pair, score, compatibility decision,
  and raw global-assignment decision
- `heldout_matching_results.json`: inputs, checksums, method versions, raw
  matches, unmatched actions, and compatibility rejections
- `heldout_reviewed_matches.csv`: final matches after permitted topology
  tie-breaks and manual correctness assessment
- `heldout_missed_matches.csv`: manually confirmed equivalent pairs missed by
  the fixed threshold

## Topology tie-breaks

Topology was used only after multiple semantically plausible candidates
remained for repeated reference labels. It did not rescue any pair below the
semantic threshold.

In `3-1`, the two identical reference retrievals were aligned by nearest
matched predecessors and successors: the first retrieval precedes warrant
distribution, while the second follows storage and precedes attachment.

In `10-7`, the three identical reference notifications were aligned by their
sequence after the matched assignment: first MSPO, then MPO, then SP. This also
removes the raw assignment's false notification-to-examination correspondence.

These tie-breaks were reviewed manually because automatic topology tie-break
logic is not yet implemented in the evaluator. This is a freeze blocker.

## Manual assessment

Among the 20 final selected correspondences, 15 are correct, 4 are false, and
1 is a granularity mismatch. Four additional true correspondences in `10-7`
are missed because nominal reference labels (`registration`, `examination`,
`rejection`, and `confirmation`) score far below their verbal generated forms.

No operation-compatibility rejection occurred above the threshold. The fixed
method therefore avoids over-rejection in this sample, but it does not address
nominalized operations or several lifecycle-stage substitutions in `8-2`.

The matcher must not be tuned on these held-out outcomes. The results instead
show that the current method is not ready to freeze. Any revised method needs a
new, separately declared development/calibration step followed by another
untouched validation set.
