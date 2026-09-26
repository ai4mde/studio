# V3.1 final 11-blocker targeted preflight

The targeted rerun evaluated only 5-1, 8-2, and 9-5 candidates 1–3. The guard cohort reran the same 42 candidates used for the previous 77-fact audit. The approved amended-case preflight reran its fixed 18 candidates. There was no formal 120-candidate rerun.

## Candidate-level fact changes from the uncertified certification run

| Case/candidate | Fact | Before → after | Explanation |
| --- | --- | --- | --- |
| 5-1/candidate_1 | CF-5-1-R01 | TP → FN+FP | The frozen branch requires small loan AND low risk. The candidate's generic risk/amount question and approved outcome name neither required value on the selected branch. |
| 5-1/candidate_2 | CF-5-1-R01 | TP → FN+FP | The frozen branch requires small loan AND low risk. The candidate's generic risk/amount question and approved outcome name neither required value on the selected branch. |
| 5-1/candidate_3 | CF-5-1-R01 | TP → FN+FP | The frozen branch requires small loan AND low risk. The candidate's generic risk/amount question and approved outcome name neither required value on the selected branch. |
| 5-1/candidate_1 | CF-5-1-R02 | TP → FN+FP | The frozen branch requires high risk. A denied outcome after a generic risk/amount question does not establish high risk. |
| 5-1/candidate_2 | CF-5-1-R02 | TP → FN+FP | The frozen branch requires high risk. A denied outcome after a generic risk/amount question does not establish high risk. |
| 5-1/candidate_3 | CF-5-1-R02 | TP → FN+FP | The frozen branch requires high risk. A denied outcome after a generic risk/amount question does not establish high risk. |
| 8-2/candidate_1 | CF-8-2-N02 | indeterminate_alignment → FN | Neither n7 nor n9 returns to the accepted submission Action n3; no candidate Decision has the frozen correction/resubmission loop role. |
| 8-2/candidate_3 | CF-8-2-N02 | indeterminate_alignment → FN | Neither n7 nor n9 returns to the accepted submission Action n3; no candidate Decision has the frozen correction/resubmission loop role. |
| 9-5/candidate_1 | CF-9-5-R06 | indeterminate_alignment → TP | Approval/reimbursement branches at n6/n7 reach accepted Action n12. Deadline gateway n11 is unrelated and must not be an owner alternative. |
| 9-5/candidate_2 | CF-9-5-R06 | indeterminate_alignment → TP | Approval/reimbursement branches at n6/n7 reach accepted Action n12. Deadline gateway n11 is unrelated and must not be an owner alternative. |
| 9-5/candidate_2 | CF-9-5-N04 | indeterminate_alignment → TP | Once the unrelated approval owner no longer competes for n11, the seven-day deadline Node uniquely matches it. |
| 9-5/candidate_2 | CF-9-5-R08 | indeterminate_alignment → TP | The seven-day relation now has its correctly assigned n11 owner and reaches the accepted progress-email Action. |

The originally audited 9-5/candidate_2/N05 did **not** change: FN → FN. This is the final contract-consistent status. The two additional 9-5/candidate_2 changes (N04 and R08) follow from removing the unrelated approval owner; they do not change any frozen denominator.

## Stability and readiness

- All 77 guard-family relations remained stable: 71 TP and 6 FN+FP. All 42 guard-cohort candidates had no Control fact status regression.
- The fixed 18-candidate preflight reproduced the prior guard-fix preflight exactly.
- Action and Flow outputs were identical in every scoped comparison.
- All frozen source questions and required denominators were unchanged; 11 source questions remain unresolved.
- The only residual FN among the 11 audited rows reflects missing candidate evidence for a second distinct deadline Node. It is not evaluator indeterminacy and does not block a final certification rerun.

**Readiness: ready for a final certification rerun of the frozen 120; that rerun has not been performed here.**
