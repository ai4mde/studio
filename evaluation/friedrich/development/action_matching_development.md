# Friedrich action-matching development set

## Scope

This is development data, not formal validation data. It contains cases `3-2`,
`3-6`, `5-4`, `10-6`, and `10-8`. It excludes the seven calibration-pilot
cases and the protected held-out cases `3-1`, `3-4`, `8-2`, `10-7`, and `1-2`.

The annotations in `action_matching_development_pairs.csv` were established
from the reference and generated `run_1.json` action sets and local topology
before implementing the revised matcher. Every unlisted pair is considered a
non-match; the CSV explicitly includes difficult negatives, granularity cases,
duplicate-branch ambiguity, and repeated-occurrence topology alternatives.

## Annotation policy

The category, granularity, topology, and binary-match rules are identical to
the frozen pilot. `operation_calibration_eligible=yes` is limited to
text-resolvable `equivalent` and `different` rows with no topology use.
Granularity, structurally resolved, and unresolved rows are excluded from
operation-threshold calibration.

For matcher assessment, `equivalent` and `structurally_resolvable` are expected
positive correspondences. A selected `granularity_mismatch` is reported
separately and does not receive a complete TP. `unresolved_ambiguous` remains
unscored rather than being forced into a one-to-one match.

## Freeze rule

After the checksum is recorded, these annotations must not be changed merely
to improve the revised matcher's results. Any genuine annotation correction
requires an explicit new development-set version and checksum.

Frozen SHA-256:

`4e5ea31e8d18690edb9891a35d1ecb4d4de748460e0d5128d23b245e1d989c6e`
