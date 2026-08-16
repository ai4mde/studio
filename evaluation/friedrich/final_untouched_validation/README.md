# Final untouched Action-matcher validation

The final sample was fixed from structural catalog metadata before action labels
or scores were inspected. The usable cases are `9-3`, `6-1`, `2-1`, `9-4`, and
`5-3`. Initial metadata selections containing unsupported inclusive gateways or
no convertible EvalGraph nodes were replaced before scoring.

The corrected matcher used threshold `0.44`, the pinned embedding and linguistic
models, the frozen conflict map, and unchanged semantic/topology ranking. The
complete matrix and raw evidence are in `untouched_candidate_matrix.csv` and
`untouched_raw_results.json`; `final_manual_review.csv` records the post-run
manual assessment.

## Diagnostics

The binary correspondence subset contains 33 correct matches, 14 false matches,
and 9 missed available true matches. Two granularity mismatches and one
unresolved ambiguity are excluded from binary diagnostics. Precision is 0.7021,
recall is 0.7857, and F1 is 0.7416.

All five recorded topology decisions had real ambiguity on at least one side.
Four were correct and one was a lifecycle-stage error. Topology never admitted a
below-threshold or operation-incompatible candidate.

## Freeze decision

Do not freeze the Action matcher yet. The sample reveals a systematic correctness
problem in the interaction between unresolved repeated labels and global
assignment: semantically tied `analyze problem` and `create trouble report`
activities were not topology-resolved, but assignment still forced a deterministic
cross-branch swap. This is not a reason for label-specific tuning. Under the stop
rule, it should first be documented and reviewed as a general unresolved-tie
policy problem; no corrective change was made during this validation.
