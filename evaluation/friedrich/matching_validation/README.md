# Action matcher pilot validation

## Method under test

1. Keep pairs with cosine similarity at or above the provisional threshold
   `0.44`.
2. Reject only high-confidence conflicts between the small operation families
   declared in `action_matching.py`.
3. Within each case, select the maximum-total-similarity bipartite assignment.
   Reference and generated node IDs are sorted before assignment, and each node
   may be selected at most once.

The operation rule is deliberately asymmetric in certainty: a declared
conflict rejects a pair, while an unclassified operation does not imply either
equivalence or difference. Context-sensitive verbs including `register`,
`submit`, `transfer`, and `enter` are intentionally unclassified.

## Frozen-pilot result

The threshold-only result was 19 TP, 2 FP, 0 FN, and 8 TN (F1 `0.95`). The
operation filter rejects only P018 (`send` versus `receive`) and P025 (`create`
versus `send`). The final result is 19 TP, 0 FP, 0 FN, and 10 TN (F1 `1.0`).
No surviving pilot candidate was changed by one-to-one assignment.

## Interpretation limit

This result must not be reported as independent generalization performance.
The compatibility rule was designed after inspecting this same calibration
pilot, and the pilot CSV contains selected candidate pairs rather than complete
reference-by-generated candidate matrices. Therefore the operation rule and
`0.44` remain provisional until they are validated without modification on
complete candidate matrices for a separate held-out validation sample.

The detailed pair decisions are in `action_matching_validation.csv`; the
machine-readable method, metrics, and changed decisions are in
`action_matching_validation_summary.json`.
