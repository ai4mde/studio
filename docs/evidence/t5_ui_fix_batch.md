# T5 UI Fix Batch Evidence

Date: 2026-07-09

## Summary

Track A is implemented in the allowed frontend write set only.

Changed production files:

- `frontend/src/lib/features/diagram/components/modals/EditNodeModal/components/EditAttributes/aiPresets.ts`
- `frontend/src/lib/features/diagram/components/modals/EditNodeModal/components/EditAttributes/AiConfigSection.tsx`
- `frontend/src/lib/features/diagram/components/modals/EditNodeModal/EditNodeModal.tsx`
- `frontend/src/lib/features/prototypes/queries.ts`
- `frontend/src/lib/features/prototypes/components/CreatePrototype.tsx`
- `frontend/src/lib/features/prototypes/components/ShowPrototypes.tsx`

No backend, generator, template, or `EditAttribute.tsx` changes were made for Track A.

## Fixes

- B01: prototype list query invalidation now uses `prototypeQueryKey(systemId)` everywhere; delete/delete-all no longer call `window.location.reload()`.
- B03: Output group now labels chips as `Writes to` and `Format`.
- B05/B06: presets declare `applicableTo`; non-applicable empty attributes self-hide; preset dropdown only lists the applicable preset.
- B07: Raw JSON editor state follows `node.data` after query refetch, so stale raw snapshots cannot overwrite saved `ai_config`.
- B08: `allowed_values` is now a draft while typing and commits on blur, then the parent Attributes Save persists it.
- B11: unknown existing `ai_config` renders unsupported read-only UI and never falls back to `late_return_risk`.

## Evidence

Static gate:

- `docs/evidence/scripts/t5_static_checks.mjs`
- `docs/evidence/t5_static_checks.json`
- `docs/evidence/t5_static_checks.log`

UI probe:

- `docs/evidence/scripts/t5_ui_probe.mjs`
- `docs/evidence/t5_ui_panel.json`
- `docs/evidence/t5_ui_panel_safe_risky.json`
- `docs/evidence/t5_ui_unsupported.json`

Screenshots:

- `docs/evidence/t5_non_applicable_book.png`
- `docs/evidence/t5_applicable_bookloan.png`
- `docs/evidence/t5_allowed_values_draft.png`
- `docs/evidence/t5_raw_json_after_save.png`
- `docs/evidence/t5_customer_reading_plan.png`
- `docs/evidence/t5_unsupported_bookloan.png`

DB evidence:

- `docs/evidence/scripts/t5_ai_config_db_gate.py`
- `docs/evidence/t5_db_clear_stray.json`
- `docs/evidence/t5_db_safe_risky.json`
- `docs/evidence/t5_db_set_unsupported.json`
- `docs/evidence/t5_db_assert_unsupported.json`
- `docs/evidence/t5_db_restore_canonical.json`
- `docs/evidence/t5_db_assert_canonical.json`

Build/check logs:

- `docs/evidence/t5_frontend_build.log`

## Gate Results

- G-B01: static check confirms helper key use and no prototype-list `window.location.reload`.
- G-B03: UI screenshots/results show `Writes to` and `Format` output labels.
- G-B05/06: `Book` shows no AI switch; `BookLoan.late_risk` and `Customer.reading_plan` show exactly one applicable preset each.
- G-B07: Raw JSON editor shows saved `ai_config`; Raw Save is disabled after refetch.
- G-B08: draft preserves `SAFE, ` and `SAFE, RISKY`; DB raw stores `["SAFE", "RISKY"]`; final DB restored to canonical `["LOW", "MEDIUM", "HIGH"]`.
- G-B11: unsupported config shows read-only unsupported UI, no preset dropdown, no dirty Save, and DB remains byte-for-byte unchanged until explicit restore.
- G-reg: final DB assertion confirms canonical `BookLoan.late_risk` and `Customer.reading_plan` configs are present.

## Notes

During B05/B06 setup, existing non-target attributes carried stale `ai_config: null` keys and `Book.isbn` carried a wrong test config. `t5_db_clear_stray.json` records cleanup of non-target `ai_config` keys before checking the "non-applicable empty attribute" UI gate.

Per T5 spec workflow, no git commit was created by Codex.
