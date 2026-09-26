# Certified V3.1 scorable-fact reporting summary

The certified evaluator results and frozen scoring contract are unchanged. These are reporting-only calculations from `aggregate_summary.json`.

## Reporting on Scorable Facts

| Component | Determinate Coverage | Precision on Scorable Facts | Recall on Scorable Facts | F1 on Scorable Facts |
| --- | ---: | ---: | ---: | ---: |
| Action | 100.0% | 1.000 | 0.850 | 0.919 |
| Flow | 79.7% | 0.897 | 0.772 | 0.830 |
| Control Node | 89.5% | 1.000 | 0.702 | 0.825 |
| Control Relation | 82.0% | 0.816 | 0.479 | 0.604 |

The reporting-only metrics are calculated from the certified pooled counts:

- `determinate_coverage = (TP + FN) / D = (D - I) / D`
- `Precision on Scorable Facts = TP / (TP + FP)`
- `Recall on Scorable Facts = TP / (TP + FN)`
- `F1 on Scorable Facts = 2 × Precision × Recall / (Precision + Recall)`

Coverage reports the proportion of required facts for which the code-based evaluator could establish a determinate alignment. Precision, Recall, and F1 on Scorable Facts are calculated only over those determinate facts. Indeterminate facts are excluded rather than forced into TP or FN decisions.

These scorable-fact metrics describe evaluator-assessed quality within the determinate portion of the evaluation and should be interpreted together with coverage.

The frozen formal all-slot pooled P/R/F1 remain null for Flow, Control Node, and Control Relation because each has I > 0. The scorable-fact F1 is not an all-120 complete F1.

### Technical counts and formal pooled metrics

| Component | D | TP | FP | FN | I | Formal all-slot pooled P | Formal all-slot pooled R | Formal all-slot pooled F1 | Recall interval | Candidates with I | Fully determinate candidates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| Action | 1137 | 966 | 0 | 171 | 0 | 1.000 | 0.850 | 0.919 | [0.8496, 0.8496] | 0 | 120 |
| Flow | 1176 | 723 | 83 | 214 | 239 | null | null | null | [0.6148, 0.8180] | 55 | 65 |
| Control Node | 285 | 179 | 0 | 76 | 30 | null | null | null | [0.6281, 0.7333] | 21 | 99 |
| Control Relation | 588 | 231 | 52 | 251 | 106 | null | null | null | [0.3929, 0.5731] | 44 | 76 |

### Presentation-ready table

| Component | Coverage | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Action | 100.0% | 1.000 | 0.850 | 0.919 |
| Flow | 79.7% | 0.897 | 0.772 | 0.830 |
| Control Node | 89.5% | 1.000 | 0.702 | 0.825 |
| Control Relation | 82.0% | 0.816 | 0.479 | 0.604 |

Precision, Recall, and F1 are calculated over scorable/determinate facts only; Coverage shows the proportion of all required facts that could be evaluated.
