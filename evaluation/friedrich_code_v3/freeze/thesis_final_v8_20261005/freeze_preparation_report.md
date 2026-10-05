# Unchanged Code evaluator v8: final freeze preparation

## Content identity

The exact validated evaluator is `evaluation.friedrich_code_v3.combined_candidate_v8.evaluate_combined_candidate_v8`, exercised by `run_full_construct_validation_v6.py` in the completed 40-case × 3-candidate offline validation. No evaluator call or scoring was performed while preparing this freeze.

`final_code_v8_freeze_manifest.json` hashes 801 unique files and identifies their roles. It includes 44 imported evaluation Python modules (32 in this worktree and 12 in the sibling `studio-semantic-v2` worktree), including older-named modules that remain import dependencies. The preflight's 669 historical files were rechecked against `run_identity_before.json`: 669/669 matched. The catalog identifies all 40 frozen Control facts, 40 corrected Flow inventories, the source-eligibility record, Start/End contract, 40 process texts, 40 reviewed Action inventories, 40 reference files, 120 frozen ActivityGraphs, the frozen cohort manifests, historical preflight outputs, targeted evidence, and the final validated outputs.

The pinned model is `sentence-transformers/all-MiniLM-L6-v2` revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. The manifest records the SHA-256 of each of its 30 snapshot paths, symlink targets, sizes, and tree digest `009014871e587272d3d23c0c72142c015532b5e8c622d6dd2d594169e6297ba9`. It does not copy the roughly 932 MB cache. The environment record contains Python 3.12.14, platform/interpreter hash, and name/version/METADATA hashes for 44 installed distributions, including sentence-transformers 5.7.0, torch 2.13.0, transformers 5.15.0, numpy 2.5.2, scipy 1.18.0, and scikit-learn 1.9.0.

The final candidate result SHA-256 is `fc4cf409a789846a037cbb22f8816c5bac8f86302a05e2768a70ebd9491727b3`; the final run manifest SHA-256 is `80a918ba0df8de93ac5f4f0eff5524c4467c7544c411e9a66af2b1d0f9e6a1ac`. No historical result was changed.

## Sibling worktree state

The validated run used 12 sibling Python modules and 120 sibling case files. Among those 132 files, 2 imported modules are modified relative to the sibling worktree's Git HEAD and 121 required files are untracked (one imported module and all 120 case files). The sibling HEAD `937230a051db1c1baa6378e47d71e122b575da6f` alone is therefore insufficient to identify or retrieve the validated content.

`used_sibling_dirty_files.csv` lists every one of those 123 paths, SHA-256 values, Git statuses, archive members, and disposition. A deterministic, content-verified copy of all 132 required sibling files is stored in `studio_semantic_v2_runtime_snapshot.tar.gz` (SHA-256 `ae38dedf035a74650ffbebda162f4e8b17a068d983d055cde5d93d0ee04405fb`). This is freeze evidence only. The live sibling files and import paths were not moved or changed. Commit this small archive with the freeze record; a future setup step can restore the expected adjacent worktree layout and verify every file before execution.

## Repository portability limit

The content used by the validated run is now fully identified and hash-covered. A clean thesis-final branch checkout is **not yet able to replay the unchanged v6 command by itself**: that runner verifies 669 absolute-path historical files, including unrelated application files, and requires previous v5/V3.2 outputs plus the adjacent sibling path and external model cache. `branch_file_scope.csv` marks 278 local paths as MUST COMMIT, 160 external content paths as MUST PRESERVE AS FREEZE EVIDENCE, and 368 historical guard-only paths as HISTORICAL BUT KEEP. These counts describe this freeze catalog, not an instruction to stage everything automatically.

For a portable thesis-final branch, retain v6 as the exact validation/provenance runner. Provide a separately versioned portability runner that calls unchanged v8 and verifies this new freeze catalog using checkout-relative paths and the restored sibling snapshot, without requiring unrelated historical application files. Its output identity should be checked against the frozen result before it becomes a claimed reproduction path. This is a runner/provenance task, not an evaluator-methodology change; it was not done here. Alternatively, exact v6 replay would require reconstructing every one of its 669 absolute paths and prior outputs, which is a poor thesis repository interface.

## Minimal README proposal (not applied)

Create `evaluation/friedrich_code_v3/README.md` with a prominent first line: **Thesis-final validated Code evaluator: `combined_candidate_v8.evaluate_combined_candidate_v8`**. Then document: four constructs and boundaries; fact-based TP/FP/FN/F1; matched-Action Flow eligibility; N/A versus indeterminate and candidate Overall masking; the frozen corpus, corrected Flow and eligibility snapshots; the sibling source archive and pinned model retrieval/verification; a single-candidate call and the historical v6 validation command with its prerequisites; outputs and provenance manifest; final pooled metrics (Action 0.9096, Flow 0.8942, Control Node 0.9260, Control Relation 0.6700, Formal Overall 0.8499803891); and an explicit table saying older evaluator and runner names are historical or live compatibility helpers, not alternate thesis-final entry points.

## Minimal package initializer proposal (not applied)

`__init__.py` currently exports `evaluate_inventory_candidate_v3` and imports older evaluator/audit modules while extending `evaluation.__path__` to the sibling worktree. Do **not** edit it inside this frozen runtime snapshot. A later versioned package-interface change may keep the sibling path setup, stop exporting the old evaluator as the apparent default, and expose v8 explicitly. That would alter the import graph and hash, so it needs its own import/reproducibility verification before being called the same final package. Until then, the README must instruct users to import v8 from its explicit module path.

## Dedicated branch file scope

Use the exact `branch_file_scope.csv`, not `git add .`. MUST COMMIT covers the local imported code (including older-named live helpers), approved snapshots and exactly 120 candidate graphs, required final/prior/targeted evidence, and this complete freeze directory including the sibling archive. MUST PRESERVE AS FREEZE EVIDENCE covers original sibling paths (copied in the archive) and externally retrieved model contents. HISTORICAL BUT KEEP covers old guard-only and superseded material. Caches, `__pycache__`, `.DS_Store`, and unrelated app/AI files are safe to ignore, but no cleanup was performed.

The current checkout is the AI branch and the Code directory is untracked there. Prepare `codex/code-evaluator-thesis-final` in an isolated worktree based on the committed Code V3.1 preservation branch; copy/stage only the reviewed hash-matching scope. Preserve the old evaluator worktrees and branches, the certified V3.1 branch, and frozen V3.2. Do not push or describe the branch as independently reproducible until the external model setup and portable-runner question are resolved.
