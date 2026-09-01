# Friedrich V3 Implementation Self-Audit

Contract: FINAL_EVALUATION_METHODOLOGY.md

## Action

- **IMPLEMENTED EXACTLY**: Action nodes only, normalized labels, pinned MiniLM revision, and 0.44 eligibility threshold.
- **IMPLEMENTED EXACTLY**: conservative `action-compatibility-v3` veto for explicit operation, direction/polarity, and concrete-object conflicts, with no case-specific exceptions.
- **IMPLEMENTED EXACTLY**: each reference Action retains eligible candidates within `delta_ref = 0.10` of its strongest eligible similarity.
- **IMPLEMENTED EXACTLY**: deterministic one-to-one assignment maximizes retained cardinality and then total similarity; no generated-side mutual-best condition is applied.
- **IMPLEMENTED WITH DOCUMENTED TECHNICAL DETAIL**: exact/near-duplicate clusters use token-set Jaccard >= 0.8; occurrence order may replace the semantic assignment only within the frozen 0.01 total-similarity tolerance.
- **IMPLEMENTED EXACTLY**: merge/split evidence requires multiple gate-compatible candidates plus compound-label or adjacency evidence; raw counts remain one-to-one.
- **IMPLEMENTED EXACTLY**: hard vetoes do not create review rows.

## Flow

- **IMPLEMENTED EXACTLY**: strict precedence is reachability in one direction only; same-cycle pairs are excluded.
- **IMPLEMENTED EXACTLY**: full reference reachability is projected to matched Action anchors before transitive reduction.
- **IMPLEMENTED EXACTLY**: required relations use generated strict reachability for TP/FN, so generated intermediate Actions remain traversable.
- **IMPLEMENTED EXACTLY**: generated nonredundant precedence is FP only when unsupported by full reference strict reachability.
- **IMPLEMENTED EXACTLY**: Flow coverage and Action-anchor coverage are separate; empty Flow has N/A quality.
- **IMPLEMENTED EXACTLY**: Flow consumes the raw one-to-one Action map and does not rematch.

## Structure

- **IMPLEMENTED EXACTLY**: the primary units are logical Exclusive, Parallel, and Loop regions, not gateway identities.
- **IMPLEMENTED WITH DOCUMENTED TECHNICAL DETAIL**: regions are extracted from branching controls and cyclic strongly connected components; control-neutral single-path corridors permit shifted boundaries.
- **IMPLEMENTED EXACTLY**: parent-first alignment uses parent region, owning branch footprint, boundaries, descendant Action footprint, depth agreement, and stable ID tie-breaking; mode is not an alignment prerequisite.
- **IMPLEMENTED EXACTLY**: branch semantics uses maximum one-to-one Jaccard matching over descendant Action footprints; internal order is not scored.
- **IMPLEMENTED EXACTLY**: Exclusive/Parallel score mode, branches, and closure/synchronization; Loop scores mode, body, and exit.
- **IMPLEMENTED EXACTLY**: guard is scored only when fully deterministic; otherwise it is N/A with region review evidence.
- **IMPLEMENTED EXACTLY**: paired region similarity yields TP=s, FP=1-s, FN=1-s; missing reference and extra generated regions contribute one full FN or FP.
- **IMPLEMENTED EXACTLY**: unmatched-anchor-dependent components are N/A; component, region, Action-anchor, and anchor-limited coverage are separate.
- **IMPLEMENTED EXACTLY**: Structure review evidence is one row per logical region.

## Human Review And Dependencies

- **IMPLEMENTED EXACTLY**: review selection is limited to granularity, duplicate occurrence, anchor/scope limitations, guard/alignment ambiguity, unsupported regions, and deterministic seeded audit.
- **IMPLEMENTED EXACTLY**: automatic items and counts are immutable and separate from review_adjusted_sensitivity.json.
- **IMPLEMENTED WITH DOCUMENTED TECHNICAL DETAIL**: adjudicators provide explicit TP/FP/FN sensitivity deltas; the sensitivity layer changes counts only and cannot create anchors or recompute Flow/Structure topology.
- **IMPLEMENTED EXACTLY**: Action runs first; Flow and Structure consume only its raw one-to-one anchors; Structure does not score internal order.
- **IMPLEMENTED EXACTLY**: historical V1/V2 models and results are read-only inputs, and each V3 run requires a new output directory.
- **IMPLEMENTED EXACTLY**: run-shape validation is configuration-only; each config declares expected cases, candidates per case, and total candidates without changing metric behavior.

## Result

Targeted tests: 59 passed, including exact 5x3 and 40x3 run-shape validation.

Authoritative frozen 5-case/15-candidate validation:
`results/v3_final_action_validation_20260901_v1`.

Held-out design reproduction: `3-5/candidate_1`, `3-7/candidate_1`, and
`5-1/candidate_1` exactly reproduced the approved simulation without retuning.

No methodology conflict was found. No formal 40x3 evaluation was run.
