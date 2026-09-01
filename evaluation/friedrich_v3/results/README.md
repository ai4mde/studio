# V3 Validation Results

The authoritative targeted validation for the frozen implementation is:

- `v3_final_action_validation_20260901_v1`

This run uses evaluator `friedrich-v3.1.0`, methodology
`friedrich-unified-evaluation/v3.1.0`, `action-compatibility-v3`, threshold
`0.44`, and reference-relative `delta_ref = 0.10`. All sibling validation
directories are superseded development or diagnostic runs and remain preserved
because result directories are never overwritten or silently deleted.

The separate held-out design check used frozen `candidate_1` models for cases
`3-5`, `3-7`, and `5-1`; it reproduced the approved read-only simulation
without changing any value. It is design validation, not a formal thesis
performance estimate.

No formal 40x3 evaluation has been run with V3.
