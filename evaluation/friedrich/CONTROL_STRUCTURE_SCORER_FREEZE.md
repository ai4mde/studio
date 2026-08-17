# Friedrich Control-structure scorer freeze

## Freeze identity

- Version: `friedrich-control-structure-scorer-v1.0.0`
- Freeze date: `2026-08-17`
- Branch: `feature/friedrich-evaluation`
- Scorer source SHA-256:
  `30017752200f7e13ff0e7e70af30c3be42d942f41bdb54c010d1b3a8a9138867`
- Required Action matcher version: `friedrich-action-matcher-v1.0.0`
- Required Action matcher freeze record SHA-256:
  `90b8ab380fd8a1bf95a5654599874adeaaac9ab3210fae278c13ad6d10f9c112`
- Required Action scorer version: `friedrich-action-scorer-v1.0.0`
- Required Action scorer source SHA-256:
  `9e36e56661861ca7ebc6299d0a969d2e92a332f568b3afda51b1fc5215494ca3`
- Required Control-flow scorer version: `friedrich-control-flow-scorer-v1.0.0`
- Required Control-flow scorer source SHA-256:
  `abb199adff53a2c1b13dea76112088ee720a7dc9b14a4ebebcfd57311b126d4b`

The Control-structure scorer must not be modified in response to the formal
47-case evaluation unless a genuine implementation correctness bug is found.
Low Control-structure Precision, Recall, F1, or coverage is evaluation evidence
and is not by itself a scorer, matcher, or generator defect.

## Control Structure Summary

A Control Structure Summary is the hashable, notation-neutral representation
of one scorable control structure. It is anchored to frozen matched reference
Actions rather than raw gateway IDs or diagram layout. Generated Action anchors
are mapped through the frozen one-to-one Action correspondences.

The frozen primary structure types are:

- `exclusive_split`: one entry anchor and an unordered multiset of branch-head
  anchor groups.
- `parallel_region`: one entry anchor, unordered branch-head and branch-tail
  groups, and synchronization state `paired`, `none`, or `orphan`.
- `loop`: entry, body-entry, back-source, repeat-target, and exit anchors.

Valid anchors are `ref:<reference-action-id>`, `INITIAL`, and `FINAL`. Branch
order and guard labels do not affect identity. Branch grouping, cardinality,
and duplicate summaries are preserved.

## Extraction policies

An acyclic `decision` with at least two outgoing branches is an
`exclusive_split`. A decision inside a cycle is excluded from split extraction
when it participates in loop control. Ordinary exclusive `merge` nodes are
transparent and retained only as diagnostics.

A `fork` and its unique nearest join reachable from all branches form one
`parallel_region`. Branch heads and tails before synchronization are retained.
A fork without a join has synchronization `none`; a join without a valid fork
is represented as an orphan structural case. A paired join is not scored again
as an independent structure.

Loops are found through deterministic strongly connected components. A unique
decision with an internal continuation and an external exit is the controller.
Cycles without a valid controller and cycles with multiple plausible
controllers are unscorable rather than guessed.

Traversal may continue through unmatched or unresolved Actions while seeking
the nearest matched Action or boundary. A structure is scorable only when all
required anchors are available and unique. Frozen Action correspondences are
never changed. Granularity evidence is diagnostic; no fractional structural
credit or extra metric penalty is added.

## Scoring contract

Let `R_struct` and `G_struct` be the multisets of scorable reference and mapped
generated Control Structure Summaries.

- `TP = sum(min(R_struct[x], G_struct[x]))`
- `FP = sum(max(G_struct[x] - R_struct[x], 0))`
- `FN = sum(max(R_struct[x] - G_struct[x], 0))`
- `Precision = TP / (TP + FP)`
- `Recall = TP / (TP + FN)`
- `F1 = 2TP / (2TP + FP + FN)`

Every supported case must satisfy:

- `TP + FN = scorable_reference_structure_count`
- `TP + FP = scorable_generated_structure_count`
- `reference_structure_count = scorable reference + unscorable reference`
- `generated_structure_count = scorable generated + unscorable generated`

If both scorable multisets are empty, Precision, Recall, and F1 are JSON
`null`, and the case is excluded from macro-F1. If exactly one side is empty,
all three metrics are `0`.

## Coverage and aggregation

Per-case structure coverage is the combined number of scorable reference and
generated structures divided by the combined total number of extracted
scorable and unscorable structures. A structurally empty supported case has
coverage `1.0`. Unsupported cases have undefined coverage.

Primary dataset metrics are micro-averaged from summed supported-case TP, FP,
and FN. Macro-F1 is the arithmetic mean of defined supported-case F1 values.
Subtype TP, FP, and FN for exclusive, parallel, and loop structures are
diagnostics only. Unsupported cases do not enter metric aggregation.

## Unsupported and unscorable policy

Incompatible cases are explicitly unsupported and are never scored as empty:

- `1-3`, `10-2`, `10-3`: active inclusive gateway semantics.
- `1-4`, `8-3`, `9-2`: combined converging/diverging gateways.
- `7-1`: incompatible Frapu BPMN XML schema.

Event-based gateways contribute only mutually exclusive split structure where
representable; event-trigger semantics are outside scope. Message flows and
data associations are ignored. Subprocess flattening is a documented
limitation. Unknown generated control types fail validation explicitly.

Unscorable structures remain in total and coverage counts, with reasons and
incident unmatched, unresolved, and granularity diagnostics. They do not enter
TP, FP, or FN because no reliable Control Structure Summary exists.

## Validation evidence

The reviewed cases `3-8`, `9-6`, `4-1`, `1-1`, `6-1`, and `2-2` are scorer-
validation diagnostics only. They are not formal thesis evaluation results.
Their preserved aggregate is:

- Reference structures: `21` total, `14` scorable, `7` unscorable.
- Generated structures: `17` total, `15` scorable, `2` unscorable.
- Structure coverage: `0.7631578947368421`.
- TP: `1`; FP: `14`; FN: `13`.
- Micro Precision: `0.06666666666666667`.
- Micro Recall: `0.07142857142857142`.
- Micro F1: `0.06896551724137931`.
- Macro F1: `0.16666666666666666`.

No structure rule, Action correspondence, matcher decision, Flow relation, or
generator output was changed to improve these diagnostics.

Validation files and SHA-256 hashes:

- `control_structure_scorer_validation.json`:
  `d2ee410643c208331a9b37edb240948f0c027beba9eb83e7b26edbe39cf864e4`
- `test_control_structure_scoring.py`:
  `991dfba67399a1851d802e616536ed726284e0b9aa5ff93ebc8e969f9a980d0e`
- `validate_control_structure_scoring.py`:
  `c9f6b7e12de10216c472d5cd7f3a0d502c20a9f35bd817a3ad8d68e1faf262f3`

Two independent report generations were byte-identical. The complete
Friedrich evaluation suite passed `90` tests in Python `3.12.13`. All 16
Control-structure test methods passed, covering the 21 required synthetic
scenarios, and all accounting and coverage invariants passed for every reviewed
case.

## Known limitations

- Structural scoring depends on frozen Action correspondence quality and
  coverage.
- Traversal through unmatched or unresolved Actions can collapse several paths
  onto a boundary anchor; low coverage remains visible when anchors are not
  unique or available.
- Fork/join pairing uses the nearest unique common join and marks ambiguous
  pairings unscorable.
- SCC loop extraction requires a unique decision controller with a distinct
  continuation and exit; unstructured cycles are not coerced into loops.
- Guard meaning, event-trigger semantics, message flows, data associations,
  subprocess hierarchy, and inclusive semantics are outside the primary score.
- The six-case diagnostic aggregate is not representative of, and must not be
  substituted for, the formal full-dataset result.
