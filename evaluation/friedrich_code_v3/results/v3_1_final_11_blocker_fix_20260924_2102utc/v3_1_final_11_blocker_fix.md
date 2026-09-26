# V3.1 targeted final blocker fix

The pre-edit 11-row audit is in `v3_1_final_11_blocker_audit.md` and its full evidence CSV. This implementation changed only `evaluation/friedrich_code_v3/control.py`; the frozen V3.1 corpus, scoring contract, Action/Flow code, thresholds, candidates, and source questions were unchanged.

1. Compound branch guards now require each explicit `small`, `low`, and `high` source qualifier on candidate predicate evidence. Generic risk/amount wording and an approved/denied outcome alone cannot satisfy the frozen 5-1 guards.
2. A proposed loop owner is excluded when a required return target is missing, another accepted return Action lies upstream, and no graph cycle returns to it. This removes the artificial 8-2 n7/n9 assignment tie without assigning a nonexistent loop as TP.
3. An explicitly temporal timeout/deadline gateway is excluded from a source approval/rejection owner when that source owner has no temporal branch role. This removes 9-5 n11 from N03 owner alternatives. `approval_in_progress` also remains distinct from completed `approved`.

The 9-5/N05 preliminary expectation is corrected in the audit addendum. The one-to-one frozen Node rule assigns combined deadline gateway n11 to N04, supported by the accepted seven-day progress-email Action. N05 remains FN. N04 and its R08 change to TP as necessary dependent results; they are listed in the comparison CSV. No coalescence permission was added.

**Final classification of the 11 reviewed rows:** 10 implementation defects corrected; 0 genuine evaluator-indeterminate rows; 1 contract-consistent candidate FN (9-5/candidate_2/N05).
