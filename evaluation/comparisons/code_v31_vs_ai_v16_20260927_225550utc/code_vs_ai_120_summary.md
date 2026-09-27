# Certified Code V3.1 versus frozen AI v1.6: 120 candidates

The AI overall score is a holistic semantic judgment. Code V3.1 reports four separate dimensions: Action, Flow, Control Node, and Control Relation. The latter three also report determinate coverage and indeterminate counts. No Code overall score is defined or calculated here.

## Candidate-level associations

Tie-aware Spearman rho uses average ranks and only candidates with both values. Null and non-applicable Code dimensions are excluded. Scorable F1 is derived from certified TP/FP/FN counts using the certified reporting formula; official null scalars remain null in the master table.

| Code dimension | N | Spearman rho | Excluded | Mean coverage, usable | Usable candidates with I |
|---|---:|---:|---:|---:|---:|
| Action | 120 | 0.419783947612 | 0 | 1.000 | 0 |
| Flow | 120 | 0.491470062781 | 0 | 0.846 | 55 |
| Control Node | 96 | 0.314186457426 | 24 | 0.922 | 18 |
| Control Relation | 96 | 0.299747042711 | 24 | 0.870 | 41 |

Pairwise completeness changes N by dimension. Each Control dimension excludes 21 no-control candidate slots with D=0 and three slots for which every required fact is indeterminate. The corresponding official Code scalar remains visible separately in the master table. These associations describe ranking patterns; the AI score and Code F1 are not interchangeable measurements.

## AI score variation with Code metrics and coverage

The following descriptive groups use each applicable dimension's observed median F1 or coverage, and the natural distinction between zero and positive indeterminate counts. Empty groups remain empty; no significance or quality threshold is applied. Full min, median, mean, and max values are in `code_vs_ai_120_descriptive.csv`.

| Variable | Group | N | Median AI score | Mean AI score |
|---|---|---:|---:|---:|
| Action F1 | below_median_scorable_F1 | 58 | 0.745 | 0.7216 |
| Action F1 | at_median_scorable_F1 | 3 | 1 | 1.0000 |
| Action F1 | above_median_scorable_F1 | 59 | 1 | 0.8625 |
| Flow F1 | below_median_scorable_F1 | 59 | 0.71 | 0.6988 |
| Flow F1 | at_median_scorable_F1 | 2 | 0.925 | 0.9250 |
| Flow F1 | above_median_scorable_F1 | 59 | 1 | 0.8925 |
| Flow indeterminate count | I=0 | 65 | 1 | 0.8966 |
| Flow indeterminate count | I>0 | 55 | 0.69 | 0.6811 |
| Flow coverage | below_median_coverage | 55 | 0.69 | 0.6811 |
| Flow coverage | at_median_coverage | 65 | 1 | 0.8966 |
| Flow coverage | above_median_coverage | 0 | N/A | N/A |
| Control Node F1 | below_median_scorable_F1 | 42 | 0.705 | 0.6571 |
| Control Node F1 | at_median_scorable_F1 | 54 | 1 | 0.8437 |
| Control Node F1 | above_median_scorable_F1 | 0 | N/A | N/A |
| Control Node indeterminate count | I=0 | 78 | 0.83 | 0.7894 |
| Control Node indeterminate count | I>0 | 21 | 0.62 | 0.6386 |
| Control Node coverage | below_median_coverage | 21 | 0.62 | 0.6386 |
| Control Node coverage | at_median_coverage | 78 | 0.83 | 0.7894 |
| Control Node coverage | above_median_coverage | 0 | N/A | N/A |
| Control Relation F1 | below_median_scorable_F1 | 45 | 0.7 | 0.6802 |
| Control Relation F1 | at_median_scorable_F1 | 0 | N/A | N/A |
| Control Relation F1 | above_median_scorable_F1 | 51 | 0.88 | 0.8343 |
| Control Relation indeterminate count | I=0 | 55 | 1 | 0.8540 |
| Control Relation indeterminate count | I>0 | 44 | 0.675 | 0.6366 |
| Control Relation coverage | below_median_coverage | 44 | 0.675 | 0.6366 |
| Control Relation coverage | at_median_coverage | 55 | 1 | 0.8540 |
| Control Relation coverage | above_median_coverage | 0 | N/A | N/A |

## Disagreement review

The sortable table contains AI and Code percentile positions and four separate absolute rank gaps. The largest available gaps per dimension are documented in `code_vs_ai_120_largest_disagreements.md`. No direct AI-minus-Code score difference or combined gap is calculated.

## Secondary oracle analysis

**POST-HOC ORACLE ANALYSIS — NOT DEPLOYABLE CANDIDATE-SELECTION PERFORMANCE**

All 40 cases are summarized separately by AI maximum and by each applicable Code dimension. The Code joint-best set is the intersection of dimension-best sets, with unscorable applicable dimensions preventing a joint-best finding. It is a post-hoc reference summary, not automatic selection performance.

## Integrity

All 120 candidate identities and ActivityGraph hashes matched. Certified Code results and frozen AI results were read only. No evaluator was rerun, no Code composite was constructed, no null or non-applicable value was substituted with zero, and continuous AI scores were copied exactly.
