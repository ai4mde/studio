# Friedrich Control-flow scorer freeze

## Freeze identity

- Version: `friedrich-control-flow-scorer-v1.0.0`
- Freeze date: `2026-08-17`
- Branch: `feature/friedrich-evaluation`
- Scorer source SHA-256:
  `abb199adff53a2c1b13dea76112088ee720a7dc9b14a4ebebcfd57311b126d4b`
- Required Action matcher version: `friedrich-action-matcher-v1.0.0`
- Required Action matcher freeze record SHA-256:
  `90b8ab380fd8a1bf95a5654599874adeaaac9ab3210fae278c13ad6d10f9c112`
- Required Action scorer version: `friedrich-action-scorer-v1.0.0`
- Required Action scorer freeze record SHA-256:
  `87d7a0d2e7147cbefb6c91681e9237b525a761519fe9acd6c4c1983ce69d2921`

The Control-flow scorer must not be modified in response to the formal 47-case
evaluation unless a genuine implementation correctness bug is found. Low Flow
Precision, Recall, or F1 is evaluation evidence and is not by itself a scorer,
matcher, or generator defect.

## Flow representation

Each EvalGraph is projected independently to a set of notation-neutral
immediate next-Action relations. Starting from every Action, traversal follows
each outgoing path through zero or more `decision`, `merge`, `fork`, or `join`
nodes. The first subsequent Action emits one directed relation and terminates
that path. An intervening Action is never skipped, and duplicate relations are
deduplicated.

Initial and final nodes are boundaries rather than transparent intermediaries.
Branch labels, conditions, and edge-only labels do not participate in primary
Flow identity. Unsupported node types fail validation explicitly. Routing-only
cycles terminate through a deterministic visited-node strategy.

Projection preserves directed loop back-relations and valid self-loops without
loop unrolling or graph isomorphism.

## Frozen Action mapping

After independent projection, each matched generated Action ID is mapped to its
frozen reference Action ID. Reference endpoints use the `ref` namespace.
Unmatched generated endpoints remain in the separate `gen` namespace. This
prevents accidental identifier collisions and does not recompute or reinterpret
Action matching.

## Scoring contract

Let `R_flow` be the projected reference relation set and `G_flow` the projected
generated relation set after frozen Action-ID mapping.

- `TP = |R_flow intersection G_flow|`
- `FP = |G_flow - R_flow|`
- `FN = |R_flow - G_flow|`
- `Precision = TP / (TP + FP)`
- `Recall = TP / (TP + FN)`
- `F1 = 2TP / (2TP + FP + FN)`

Each distinct directed relation contributes at most once. Every case must
satisfy:

- `TP + FN = reference_flow_count`
- `TP + FP = generated_flow_count`

## Zero-denominator policy

- Both projected relation sets empty: Precision, Recall, and F1 are `null`;
  mark the case flow-empty and exclude it from macro-F1.
- Exactly one relation set empty: Precision, Recall, and F1 are `0`.

Machine-readable undefined values are JSON `null`, never `1`.

## Unmatched and unresolved policy

Unmatched and unresolved Actions are never bridged. Their incident relations
remain ordinary FN on the reference side or FP on the generated side. The
unresolved component and its candidate edges add no metric penalty. Incident
relation sets are retained as diagnostics only.

## Granularity policy

Frozen Action correspondences are used unchanged. Granularity differences
receive ordinary relation-set accounting, no fractional credit, and no extra
penalty. Reference-side and generated-side incident relation sets are retained
separately; their combined count is diagnostic only.

## Parallelism and structural scope

Fork and join nodes are traversable only to establish Action adjacency. Flow F1
does not score parallel-versus-exclusive semantics, synchronization, split/join
pairing, branch grouping, structural reconvergence, or loop guards. Those
properties belong to the separately designed Control-structure scorer.

## Dataset aggregation

Primary dataset metrics are micro-averaged from summed case TP, FP, and FN.
Macro-F1 is the arithmetic mean of defined per-case F1 values. Truly empty-flow
cases are excluded from macro-F1. Reports also retain case counts, empty-flow
case counts, defined macro case counts, and total reference/generated flows. No
weighted macro metric is used.

## Validation evidence

The six reviewed cases are Control-flow scorer validation diagnostics only.
They are not formal 47-case thesis results. Their preserved aggregate is:

- TP: `21`
- FP: `25`
- FN: `41`
- Micro Precision: `0.45652173913043476`
- Micro Recall: `0.3387096774193548`
- Micro F1: `0.3888888888888889`
- Macro F1: `0.48819444444444443`

The low results for cases `1-1`, `2-2`, and `6-1` remain unchanged for later
error analysis. No Flow relation, Action correspondence, matcher decision, or
generator output was manually corrected.

Validation files and SHA-256 hashes:

- `control_flow_scorer_validation.json`:
  `e3d89eb0d16fc5e2591aa601ed6828bd1df4760ab334f439284662cfa55a9d8f`
- `test_control_flow_scoring.py`:
  `c16046b1d2963f882b65145c5efb3dfe3aa77ce0f0c13b518a0b9e46daf9187b`
- `validate_control_flow_scoring.py`:
  `9a8335f280d08d7ab01dc832755750c3b8159912983cf550d9ad3f9a15744554`

The complete Friedrich evaluation suite passed `74` tests in Python `3.12.13`
with the pinned evaluation dependencies. All 15 Control-flow scorer tests
passed, and both accounting invariants passed for every reviewed case.

## Known limitations

- Flow F1 depends on frozen Action correspondence quality and coverage.
- Conservative no-bridging can turn one unmatched Action into multiple
  incident relation errors; each remains a distinct process-ordering fact.
- Initial-to-first-Action and last-Action-to-final boundary relations are not
  scored.
- Branch labels and guards are deliberately excluded from primary Flow identity.
- Equivalent Action adjacency does not imply equivalent routing semantics.
- The six-case validation aggregate is not representative of, and must not be
  substituted for, the formal full-dataset result.
