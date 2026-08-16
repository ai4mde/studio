# Untouched validation of the revised Action matcher

The sample was selected from catalog-level structure before action labels or
matcher scores were inspected. Cases `8-1`, `1-1`, `2-2`, `3-8`, and `10-9`
have no overlap with the pilot, first held-out sample, or development set.

The matcher was run without changing threshold `0.44`, linguistic extraction,
the fixed conflict map, assignment, or topology logic. Source hashes are stored
in `untouched_raw_results.json`. `untouched_candidate_matrix.csv` contains the
complete candidate matrix, and `untouched_manual_review.csv` records the manual
classification made after the raw run.

## Diagnostic result

The binary correspondence subset contains 25 correct matches, 5 false matches,
and 2 missed available true matches. Three selected correspondences are
granularity mismatches and are excluded from binary precision/recall. No pair
was left unresolved. Diagnostic precision is 0.8333, recall is 0.9259, and F1
is 0.8772. These are matcher-validation diagnostics, not the final dataset
Action F1.

## Validation finding

The raw matcher records nine topology-assisted selections. Six had only one
remaining candidate, so topology was not actually resolving ambiguity; global
assignment would have been the appropriate stage. Of the three genuine
multi-candidate topology decisions, two are granularity correspondences and one
is a false lifecycle-stage match (`check customer's first registration` to
`receive customer data`).

Because this is a systematic stage-semantics and auditability issue, the matcher
should not yet be declared frozen. No fix was applied using these cases. Any
approved general correction must be made without label or case exceptions and
then assessed on another untouched sample, not this validation set.
