# Proposal: thesis evaluator package export

**Proposal only.** No package initializer or frozen evaluator file changes in this documentation revision.

## Current misleading export

[`evaluation/friedrich_code_v3/__init__.py`](../evaluation/friedrich_code_v3/__init__.py) currently imports and lists `evaluate_inventory_candidate_v3` from `.evaluator` in `__all__`. A caller using `from evaluation.friedrich_code_v3 import evaluate_inventory_candidate_v3` therefore receives an older evaluator entry point, while the validated thesis scoring entry point is `evaluation.friedrich_code_v3.combined_candidate_v8.evaluate_combined_candidate_v8`. The initializer also performs package-path setup used by the frozen runtime; it must not be edited casually.

## Desired future public interface

In a **separate, versioned interface revision**, consider exporting `evaluate_combined_candidate_v8` explicitly from the package and making it the documented public scoring function. Decide whether to retain the old export under a clearly historical name for compatibility. Avoid changing the v8 scoring function, its components, inventories, or validated evidence. Until that revision is verified, import v8 explicitly from `combined_candidate_v8`.

## Required verification before any initializer change

1. Record the original initializer hash and preserve the existing thesis-final commit and freeze manifest unchanged.
2. Check the import graph and circular-import behavior, including the sibling semantic runtime and older-named live helper modules.
3. Verify both the explicit v8 import and the proposed package-level import resolve to the same callable without selecting the older evaluator.
4. Recheck frozen code/data/model hashes and the 120-candidate roster, then run the portable content verifier. If an execution replay is used to validate the changed import path, write outputs to a new directory and compare canonical results and metrics with the frozen v8 run.
5. Issue a new interface revision and provenance/hash record for any changed `__init__.py`; do not present the old freeze manifest as covering changed bytes.

The current documentation update does **not** make this interface change or rerun evaluation.
