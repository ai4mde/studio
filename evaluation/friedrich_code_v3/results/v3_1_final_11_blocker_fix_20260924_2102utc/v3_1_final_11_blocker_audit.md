# V3.1 final 11 certification-blocker audit

Completed before any implementation edit. The audit reads the frozen V3.1 facts, source excerpts, unchanged cohort graphs, locked Action mappings, broken completed results, and the uncertified 120-candidate run. The companion CSV preserves each exact fact definition, candidate controls and edges, owned relations, accepted anchors, diagnostics, and implementation path.

| Case/candidate | Fact | Classification | Broken → certification | Expected under frozen contract |
| --- | --- | --- | --- | --- |
| `5-1/candidate_1` | `CF-5-1-R01` | `GUARD_SPECIFICITY_BUG` | FN+FP → TP | FN+FP |
| `5-1/candidate_2` | `CF-5-1-R01` | `GUARD_SPECIFICITY_BUG` | FN+FP → TP | FN+FP |
| `5-1/candidate_3` | `CF-5-1-R01` | `GUARD_SPECIFICITY_BUG` | FN+FP → TP | FN+FP |
| `5-1/candidate_1` | `CF-5-1-R02` | `GUARD_SPECIFICITY_BUG` | FN+FP → TP | FN+FP |
| `5-1/candidate_2` | `CF-5-1-R02` | `GUARD_SPECIFICITY_BUG` | FN+FP → TP | FN+FP |
| `5-1/candidate_3` | `CF-5-1-R02` | `GUARD_SPECIFICITY_BUG` | FN+FP → TP | FN+FP |
| `8-2/candidate_1` | `CF-8-2-N02` | `NODE_ROLE_ASSIGNMENT_BUG` | TP → indeterminate_alignment | FN |
| `8-2/candidate_3` | `CF-8-2-N02` | `NODE_ROLE_ASSIGNMENT_BUG` | TP → indeterminate_alignment | FN |
| `9-5/candidate_1` | `CF-9-5-R06` | `OWNER_SCOPE_BUG` | TP → indeterminate_alignment | TP |
| `9-5/candidate_2` | `CF-9-5-R06` | `OWNER_SCOPE_BUG` | TP → indeterminate_alignment | TP |
| `9-5/candidate_2` | `CF-9-5-N05` | `DEADLINE_ROLE_BUG` | indeterminate_alignment → FN | indeterminate_alignment |

## Source-grounded findings

### 5-1/candidate_1/CF-5-1-R01

- Frozen guard or structural role: `small and low risk`.
- Expected: **FN+FP**. The frozen branch requires small loan AND low risk. The candidate's generic risk/amount question and approved outcome name neither required value on the selected branch.
- Implementation path: `_guard_context_matches -> _branch_relation: generic gateway context and reached outcome replace required risk/amount qualifiers.`

### 5-1/candidate_2/CF-5-1-R01

- Frozen guard or structural role: `small and low risk`.
- Expected: **FN+FP**. The frozen branch requires small loan AND low risk. The candidate's generic risk/amount question and approved outcome name neither required value on the selected branch.
- Implementation path: `_guard_context_matches -> _branch_relation: generic gateway context and reached outcome replace required risk/amount qualifiers.`

### 5-1/candidate_3/CF-5-1-R01

- Frozen guard or structural role: `small and low risk`.
- Expected: **FN+FP**. The frozen branch requires small loan AND low risk. The candidate's generic risk/amount question and approved outcome name neither required value on the selected branch.
- Implementation path: `_guard_context_matches -> _branch_relation: generic gateway context and reached outcome replace required risk/amount qualifiers.`

### 5-1/candidate_1/CF-5-1-R02

- Frozen guard or structural role: `high risk`.
- Expected: **FN+FP**. The frozen branch requires high risk. A denied outcome after a generic risk/amount question does not establish high risk.
- Implementation path: `_guard_context_matches -> _branch_relation: generic gateway context and reached outcome replace required risk/amount qualifiers.`

### 5-1/candidate_2/CF-5-1-R02

- Frozen guard or structural role: `high risk`.
- Expected: **FN+FP**. The frozen branch requires high risk. A denied outcome after a generic risk/amount question does not establish high risk.
- Implementation path: `_guard_context_matches -> _branch_relation: generic gateway context and reached outcome replace required risk/amount qualifiers.`

### 5-1/candidate_3/CF-5-1-R02

- Frozen guard or structural role: `high risk`.
- Expected: **FN+FP**. The frozen branch requires high risk. A denied outcome after a generic risk/amount question does not establish high risk.
- Implementation path: `_guard_context_matches -> _branch_relation: generic gateway context and reached outcome replace required risk/amount qualifiers.`

### 8-2/candidate_1/CF-8-2-N02

- Frozen guard or structural role: `Correct and resubmit rejected job description`.
- Expected: **FN**. Neither n7 nor n9 returns to the accepted submission Action n3; no candidate Decision has the frozen correction/resubmission loop role.
- Implementation path: `_anchor_context_score -> _case_wide_assignment: broad downstream Action context admits n7 and n9 without validating owned loop recurrence/exit.`

### 8-2/candidate_3/CF-8-2-N02

- Frozen guard or structural role: `Correct and resubmit rejected job description`.
- Expected: **FN**. Neither n7 nor n9 returns to the accepted submission Action n3; no candidate Decision has the frozen correction/resubmission loop role.
- Implementation path: `_anchor_context_score -> _case_wide_assignment: broad downstream Action context admits n7 and n9 without validating owned loop recurrence/exit.`

### 9-5/candidate_1/CF-9-5-R06

- Frozen guard or structural role: `approved`.
- Expected: **TP**. Approval/reimbursement branches at n6/n7 reach accepted Action n12. Deadline gateway n11 is unrelated and must not be an owner alternative.
- Implementation path: `_anchor_context_score -> _case_wide_assignment -> score_control_relations: n11 enters approval owner alternatives through broad reachability, then conflicting outcomes force I.`

### 9-5/candidate_2/CF-9-5-R06

- Frozen guard or structural role: `approved`.
- Expected: **TP**. Approval/reimbursement branches at n6/n7 reach accepted Action n12. Deadline gateway n11 is unrelated and must not be an owner alternative.
- Implementation path: `_anchor_context_score -> _case_wide_assignment -> score_control_relations: n11 enters approval owner alternatives through broad reachability, then conflicting outcomes force I.`

### 9-5/candidate_2/CF-9-5-N05

- Frozen guard or structural role: `Cancel and require resubmission after 30 days unfinished`.
- Expected: **indeterminate_alignment**. n11 explicitly carries both seven- and thirty-day conditions. The frozen inventory requires two distinct Decision facts and has no coalescence permission; one-to-one assignment cannot give both TP. The present FN is driven by n11 being offered to an unrelated approval owner.
- Implementation path: `_anchor_context_score -> _case_wide_assignment: unrelated approval owner competes for n11; combined 7/30-day gateway needs role evidence and one-to-one handling.`

## Methodological boundary

- `8-2`: the graphs do not contain a return path to accepted submission Action n3. Resolving the n7/n9 tie to TP would invent a loop; the registered loop role must be absent (FN).
- `9-5`: one physical gateway n11 labels both time windows. The frozen 9-5 permitted equivalences concern branch drawing order and equivalent End nodes; neither permits two required logical Decision Nodes to share one physical gateway. The thirty-day Node can remain evaluator-indeterminate if n11 could be assigned to either deadline role, but it cannot be counted as an extra TP.
- No source fact, status, denominator, Action mapping, or candidate was changed during this audit.

## Post-fix audit correction: CF-9-5-N05

The pre-edit audit recorded an expected `indeterminate_alignment` for candidate_2/N05. Targeted evidence and the frozen one-to-one rule correct that preliminary expectation to **FN**. Candidate n11 combines seven-day and thirty-day wording, but N04 has the accepted seven-day progress-email target at n13, while N05’s required thirty-day Action target has no accepted Action mapping. The single candidate gateway is allocated to N04. The frozen permitted equivalences do not allow one gateway to satisfy both required Nodes. N05 stays required in the unchanged denominator; its FN is candidate-missing structural evidence, not evaluator indeterminacy. No source question was resolved.
