# Revised Action matcher development validation

This directory records the single permitted matcher revision evaluated on the
frozen development cases `3-2`, `3-6`, `5-4`, `10-6`, and `10-8`. The protected
held-out cases were not loaded or scored.

The revision uses pinned spaCy `en_core_web_sm` 3.8.0 and WordNet derivational
links, preserves the full-label embedding score, and adds an inspectable
operation/object representation. Calibration did not support an additional
operation-similarity threshold, so operation similarity remains diagnostic and
the pre-existing small conflict map remains the only hard operation guard.

Topology is restricted to semantic candidates at or above `0.44`. It traverses
only routing/control nodes to the nearest already-matched action predecessor or
successor, requires a unique reciprocal winner, records all evidence, and is
followed by deterministic maximum-weight one-to-one assignment.

`development_comparison.json` is the authoritative before/after report and
topology audit log. `revised_candidate_matrix.csv` contains the complete scored
development matrix and linguistic representations.

The remaining errors are frozen development findings, not reasons to add more
rules. In particular, WordNet has no derivational verb for `deregistration` in
the pinned data, and several shared-object lifecycle confusions remain. The next
assessment must use a new untouched validation sample without further tuning.
