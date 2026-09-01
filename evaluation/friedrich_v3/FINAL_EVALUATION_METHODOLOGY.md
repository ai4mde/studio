# Final Friedrich Evaluation Methodology

- Methodology: `friedrich-unified-evaluation/v3.1.0`
- Evaluator: `friedrich-v3.1.0`
- Status: frozen for implementation

> This document is the frozen implementation contract for the evaluator. Production implementation must not change these rules without an explicit methodology revision and evaluator version change.

## Action

Action evaluates semantic equivalence of Action nodes only. Labels are normalized and compared with pinned `sentence-transformers/all-MiniLM-L6-v2` revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Similarity `>= 0.44` makes a pair eligible, not proven equivalent. The conservative deterministic `action-compatibility-v3` veto removes candidates with explicit direction/polarity conflict, incompatible primary operations, or explicit incompatible concrete objects.

For each reference Action `r`, let `best(r)` be the maximum similarity across its eligible generated candidates. Retain `(r,g)` only when `similarity(r,g) >= best(r) - delta_ref`, where `delta_ref = 0.10`. Perform deterministic one-to-one assignment over only the retained candidates, maximizing retained cardinality and then total similarity. Leave Actions unmatched when no retained one-to-one assignment is available. Generated-side mutual-best status is not required. Context remains a small occurrence tie-break only for exact/near-duplicate retained candidates; incomparable duplicates remain uncertain.

`delta_ref = 0.10` was selected on the five-case tuning cohort and then checked without retuning on the separate held-out cases `3-5/candidate_1`, `3-7/candidate_1`, and `5-1/candidate_1`. That held-out check was design validation only, not a formal thesis performance estimate.

Each accepted pair is one TP. Each unmatched generated Action is one FP and each unmatched reference Action is one FN. Possible merge/split granularity remains raw one-to-one scoring and creates review evidence only; no automatic many-to-many credit is allowed. Action-anchor coverage is `matched reference Actions / reference Actions`. Unresolved duplicate occurrence, merge/split granularity, or scope/anchor uncertainty triggers targeted review. Hard compatibility vetoes normally do not.

## Flow

Flow evaluates semantic strict precedence between comparable matched Action anchors. Strict precedence `A < B` means `A` reaches `B` and `B` does not reach `A`; parallel/exclusive siblings and same-cycle pairs therefore imply no strict precedence. Compute full reference strict reachability over all reference Actions, project it to matched anchors, and only then transitively reduce it. Unmatched intermediate reference Actions remain traversable.

For each reduced required reference relation, TP means the mapped generated source strictly reaches the mapped generated target; otherwise it is FN. Intermediate generated Actions do not invalidate reachability. Compute and reduce generated strict precedence over matched generated anchors; after mapping back, a generated relation is FP only when full reference strict reachability does not support that direction. A reversal therefore contributes the missing required FN and unsupported reverse FP. Flow coverage is `comparable required relations / all reduced reference required relations`; Action-anchor coverage is reported separately. Anchor-limited or genuinely indeterminate relations trigger review. Flow depends only on the final raw one-to-one Action mapping.

## Structure

Structure evaluates logical Exclusive, Parallel, and Loop regions, independent of gateway notation identity. Regions are aligned hierarchically using aligned parent region, owning parent branch, depth, entry/continuation boundaries, and descendant Action footprints. Parents align before children; mode is scored, not required for alignment. Boundary agreement precedes footprint overlap and depth agreement, with stable IDs only as a final deterministic tie-break. Alignment requires meaningful boundary or footprint evidence; boundary shifts are equivalent only through a control-neutral corridor.

Exclusive/Parallel components are mode, branch semantics, and closure/synchronization. Loop components are loop mode, loop body, and exit. A guard is an optional fourth component only when deterministically comparable; otherwise it is N/A and creates review evidence. Branches use maximum one-to-one Jaccard matching over descendant Action footprints; empty matches only empty. Internal order is exclusively a Flow concern.

For paired region similarity `s`, `TP=s`, `FP=1-s`, and `FN=1-s`. A missing reference region contributes `FN=1`; an extra generated region contributes `FP=1`. Region score is the arithmetic mean of scorable components. Anchor-dependent components with unmatched anchors are N/A, not automatically wrong. A region with no scorable components contributes no score mass and is reviewed. Report component coverage, scorable-region coverage, Action-anchor coverage, and anchor-limited rate. Unsupported or ambiguous regions, guard ambiguity, and anchor limitation trigger one region-centered review item.

## Human Review

Human Review does not re-evaluate every automatic item. It is limited to possible merge/split granularity, unresolved duplicate occurrence, anchor uncertainty, guard ambiguity, unsupported/ambiguous Structure regions, genuinely indeterminate Flow relations, and a deterministic seeded quality-control sample. Hard deterministic Action vetoes normally do not require review.

Raw automatic outputs are immutable. Review-adjusted/adjudicated sensitivity outputs are stored separately. Review may alter sensitivity counts for granularity but must not synthesize anchors, convert automatic matching to many-to-many, or automatically recompute Flow/Structure from adjudicated many-to-many mappings.

## Thesis Formulas

For Action and Flow integer counts, and Structure soft counts:

`Precision = TP / (TP + FP)`

`Recall = TP / (TP + FN)`

`F1 = 2 * Precision * Recall / (Precision + Recall) = 2TP / (2TP + FP + FN)`

When both compared sides contain no evaluation units, the metric is reported as empty/N/A rather than interpreted as evidence of quality. Coverage is always reported separately and never folded into TP, FP, FN, Precision, Recall, or F1.

## Cross-Stage Dependencies

Action runs first and produces the only raw one-to-one anchor map. Flow and Structure consume that frozen raw map and never rematch Actions. Flow does not depend on Structure; Structure does not score internal order and therefore does not duplicate Flow. Human Review consumes automatic evidence without mutating raw results. Granularity adjudication does not synthesize Flow or Structure anchors. Generated/reference models and historical V1/V2 outputs are immutable inputs.
