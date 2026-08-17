# Friedrich Action scorer freeze

## Freeze identity

- Version: `friedrich-action-scorer-v1.0.0`
- Freeze date: `2026-08-17`
- Branch: `feature/friedrich-evaluation`
- Scorer source SHA-256:
  `9e36e56661861ca7ebc6299d0a969d2e92a332f568b3afda51b1fc5215494ca3`
- Required matcher version: `friedrich-action-matcher-v1.0.0`
- Required matcher freeze record SHA-256:
  `90b8ab380fd8a1bf95a5654599874adeaaac9ab3210fae278c13ad6d10f9c112`

This scorer is frozen for formal Friedrich evaluation. The scorer must not be
modified in response to formal 47-case evaluation results unless a genuine
implementation correctness bug is found. Differences in system performance,
including low Precision, Recall, or F1 for an individual case, are evaluation
evidence and are not scorer defects.

## Scoring contract

For each case, let `R` be all reference nodes with `type = action`, `G` all
generated nodes with `type = action`, and `M` the accepted one-to-one matcher
pairs where `final_prediction = true`.

- `TP = |M|`
- `FP = |G - matched_generated(M)|`
- `FN = |R - matched_reference(M)|`
- `Precision = TP / (TP + FP)`
- `Recall = TP / (TP + FN)`
- `F1 = 2TP / (2TP + FP + FN)`

Every case must satisfy both accounting invariants:

- `TP + FN = reference_action_count`
- `TP + FP = generated_action_count`

Initial, final, decision, merge, fork, join, object, edge, branch-label, and
condition elements do not participate in Action scoring. An unlabeled Action
remains in its side's node set, may remain unmatched, and is reported through
the unlabeled-Action diagnostics.

## Zero-denominator policy

- No reference and no generated Actions: Precision, Recall, and F1 are `null`;
  mark the case empty and exclude it from macro-F1.
- Reference Actions but no generated Actions: all three metrics are `0`.
- Generated Actions but no reference Actions: all three metrics are `0`.

Machine-readable undefined values are JSON `null`, never `1`.

## Unresolved policy

- Each unique unresolved reference Action remains unmatched and counts once as
  FN.
- Each unique unresolved generated Action remains unmatched and counts once as
  FP.
- Candidate edges and the unresolved component itself add no metric penalty.
- Component and unique-node counts are retained as diagnostics.

## Granularity policy

- An accepted atomic one-to-one pair contributes at most one TP.
- Remaining unmatched reference and generated Actions contribute ordinary FN
  and FP counts.
- No fractional TP or extra granularity penalty is awarded.
- Confirmed one-reference-to-many-generated and
  many-reference-to-one-generated components are retained as diagnostics.

Granularity evidence is supplied explicitly; the scorer does not infer it from
labels or alter frozen matcher decisions.

## Dataset aggregation

Primary dataset metrics are micro-averaged from the sums of case TP, FP, and FN.
Macro-F1 is the arithmetic mean of defined per-case F1 values. Truly empty
cases are excluded from macro-F1, and the report records `case_count`,
`empty_case_count`, `defined_macro_case_count`, total reference Actions, and
total generated Actions. No weighted macro metric is used.

## Validation evidence

The five reviewed cases are scorer-validation diagnostics only. They are not
the formal 47-case thesis evaluation and must not be interpreted as such. Their
preserved aggregate is:

- TP: `41`
- FP: `10`
- FN: `11`
- Micro Precision: `0.803921568627451`
- Micro Recall: `0.7884615384615384`
- Micro F1: `0.7961165048543689`
- Macro F1: `0.7977032227032227`

Case `1-1` and all other reviewed outcomes remain unchanged as evaluation
evidence. No matcher or generator decision was manually corrected for scoring.

Validation files and SHA-256 hashes:

- `action_scorer_validation.json`:
  `1660359d61e292815d8a0f3a4600d7423a82ce90855531fb4c11b7a96992b8af`
- `test_action_scoring.py`:
  `2e819df44dbdccce1beff22b134a1fc2cf9178bc7a69891645a58560a911f49d`
- `validate_action_scoring.py`:
  `17029839036d3a3ea81b06e03db6dae3d6a5d92b5a83c15b79312da21e771dde`

The complete Friedrich evaluation suite passed `59` tests in the documented
Python `3.12.13` environment. All 13 Action scorer unit tests passed, and both
accounting invariants passed for each reviewed case.

## Known limitations

- A TP represents an accepted frozen matcher correspondence. The scorer does
  not independently correct semantic matcher errors.
- Granularity diagnostics require pre-existing explicit evidence and are not
  automatically inferred from text.
- Conservative unresolved handling can lower measured coverage; this is
  intentional and prevents ambiguous nodes from being silently excluded.
- The five-case diagnostic aggregation is not representative of, and must not
  be substituted for, the formal full-dataset result.
- The scorer evaluates Actions only. Control-flow and control-structure quality
  require separately frozen scoring contracts.
