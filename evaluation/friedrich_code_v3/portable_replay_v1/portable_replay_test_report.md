# Portable v8 replay test, 2026-10-05

## Content verification

PASS in the current checkout and in a temporary clean checkout containing only the 278 `MUST_COMMIT` files, the complete unchanged freeze directory, and this replay package. Both used the pinned external model snapshot and existing `.venv-friedrich-v2` environment. The verifier checked 120 unique candidates across 40 cases, 132 archived sibling files, the taxonomy addendum, 30 model snapshot paths, and 44 Python package identities. No score was computed in verification mode.

An additional import-only check assembled a temporary checkout from the same 278 files, extracted the archive, overlaid the taxonomy, imported unchanged v8, and loaded the 40-case `FrozenCorpus` through the portable source path. It passed without scoring a candidate.

## One scored replay

Output: `evaluation/friedrich_code_v3/results/portable_v8_replay_20261005_184708_148260utc_1485a55d/`.

All 120 candidates completed from the frozen roster. The parsed candidate objects match the frozen v6 results exactly under sorted-key canonical JSON. Canonical SHA-256 for both is `578be1c0639864b9b12292850a292eda73efe3f673fb3f6f6543b44f1548969d`. The four aggregate dimension summaries match exactly. There were no candidate-level scoring differences.

The raw JSONL SHA-256 differs: frozen `fc4cf409a789846a037cbb22f8816c5bac8f86302a05e2768a70ebd9491727b3`, replay `3d765c7cf8674a880f459137bb5669ab684359da8ca071fd874bc8b58539f274`. Nine rows differ only in key insertion order within diagnostic dictionaries. Key order does not change their parsed values. The nine affected rows are 4-1/candidate_1, 4-1/candidate_3, 5-3/candidate_1-3, 5-4/candidate_1, 6-1/candidate_1-2, and 9-6/candidate_1. The comparison and run provenance are in the replay output directory.

An earlier bootstrap attempt created `portable_v8_replay_20261005_184645_289454utc_505712dd` and stopped before any candidate was scored because direct script invocation lacked the checkout root on `sys.path`. It is left untouched as technical provenance. The wrapper now inserts the checkout root before importing the unchanged evaluator.

After the scored replay, only comparison reporting and a guard ensuring sibling modules come from the temporary verified overlay were added to the wrapper. The saved comparison was recalculated offline from the existing replay and frozen JSONL; no candidate was reevaluated.

## Portability decision

The planned thesis-final branch can include the exact source/data and this replay package without a mutable sibling worktree or the historical absolute-path v6 guard. A fresh machine still needs the pinned ~932 MB model snapshot and a compatible Python/package environment. Package metadata is recorded and checked, but the branch does not bundle the interpreter or all wheel binaries. The original freeze package is unchanged.
