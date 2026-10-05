# Code evaluator navigation

## CURRENT THESIS CODE EVALUATOR

- **Branch:** `thesis-code-evaluator-final`.
- **Validated scoring entry point:** `evaluation.friedrich_code_v3.combined_candidate_v8.evaluate_combined_candidate_v8` in [`combined_candidate_v8.py`](../evaluation/friedrich_code_v3/combined_candidate_v8.py).
- **Final evaluator README:** [`evaluation/friedrich_code_v3/README.md`](../evaluation/friedrich_code_v3/README.md).
- **Freeze manifest:** [`final_code_v8_freeze_manifest.json`](../evaluation/friedrich_code_v3/freeze/thesis_final_v8_20261005/final_code_v8_freeze_manifest.json), SHA-256 `cfcfc68de14208c0f7f10ed6f85e8e89a1ff7aa283c8fed24f2ea857439434ef`.
- **Validated Formal Overall Code F1:** `0.8499803891` for 40 cases and 120 candidates. This is the mean of four pooled dimension F1 values, not a candidate-level Overall score.
- **Verification and replay:** [`portable_replay_v1/`](../evaluation/friedrich_code_v3/portable_replay_v1/) contains the content verifier, replay wrapper, and clean-checkout requirements. Replay needs the separately verified model snapshot described there.

**Do not use generic package imports or old runner entry points as the thesis-final evaluator. Use the explicit `combined_candidate_v8` entry point.** The current package-level export in [`__init__.py`](../evaluation/friedrich_code_v3/__init__.py) names an older evaluator; it has not been changed because it is part of the frozen runtime dependency graph. A future interface-only change is described in the [public-export proposal](code-evaluator-public-export-proposal.md).

## HISTORICAL / PROVENANCE ONLY

| Material | Role now |
| --- | --- |
| V3.1 evaluator implementation, certification bundle, and branch `codex/code-evaluator-v3-1-certified` | Certified earlier milestone; retain for reproducibility and historical comparison. |
| V3.2 formal results | Historical formal evidence; retain. Frozen inventories that v8 still reads are active v8 inputs, even if their paths contain earlier version names. |
| `combined_candidate_v2.py` and `combined_candidate_v3.py` and their earlier configurations | Developmental entry points and replay/provenance dependencies where imported; do not select them for thesis-final scoring. |
| Earlier Action, Control Node, and Control Relation component versions | Superseded as public scoring choices; **some older-named modules remain live helper dependencies of v8**. Preserve every imported helper recorded in the freeze manifest. |
| `run_full_construct_validation_v6.py` and older validation runners | Validation provenance; use the portable v8 verification/replay tools for a clean checkout. |
| `feature/final-evaluator-v3`, `feature/friedrich-v3-local-correction`, `feature/friedrich-evaluation`, and the older semantic-evaluator branches | Historical branch pointers, not the current thesis Code evaluator. Do not delete them as part of navigation cleanup. |

The final package README and freeze manifest control the exact v8 dependency and evidence scope. A historical **entry point** can coexist with a **live helper dependency**: the latter remains necessary even if its filename contains an earlier version number. This navigation guide changes no scoring contract, data, inventory, or freeze record.
