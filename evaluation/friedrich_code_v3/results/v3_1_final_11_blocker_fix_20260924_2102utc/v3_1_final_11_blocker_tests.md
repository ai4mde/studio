# V3.1 final blocker tests

- Unit/regression suite: **62/62 passed** (56 existing plus 6 focused tests). Focused tests cover compound guards with positive and negative controls, missing return cycle vs separate approval Decision, approval owner vs deadline gateway, separate seven-day and thirty-day gateways, the one-gateway/two-required-deadlines constraint, and approval-in-progress versus completed approval.
- Targeted nine candidates: **9/9 EVALUATED**, 12 changed Control fact statuses, all recorded in the comparison CSV. Action and Flow outputs equal the uncertified certification run for all nine.
- Guard cohort: **42/42 EVALUATED**; all Control fact statuses match the uncertified certification run. The prior 77 audited relations remain **71 TP, 6 FN+FP**, with zero changed statuses. Action and Flow also match.
- Approved preflight: **18/18 EVALUATED**; parsed result JSON equals the prior guard-fix preflight exactly, including roster, per-fact results, denominators, Action, Flow, and source questions.
- For every targeted and guard-cohort candidate, each Control required denominator is unchanged and `D = TP + FN + I`.
- Frozen corpus loader verified all 40 case inventories and dependencies. Corpus SHA-256: `5f9765bda2ea5d9d9f4a78603207bb0a2ed6532fd0c935149c275595c7d5be8a`. Unresolved source questions: **11**, unchanged.
- Only these 9 + 42 + 18 scoped reruns occurred; the formal 120 was not rerun.
