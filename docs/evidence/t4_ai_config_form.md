# T4 AI Config Form Evidence

Date: 2026-07-07

## Summary

T4 is complete for `LibraryT4A`.

The Studio attribute editor now provides a preset-based `AI-managed attribute` form. It writes through the existing `partialUpdateNode` PATCH path and stores canonical `ai_config` objects in raw DB JSON.

Step 0 was committed separately:

- `db6f041a fix(studio): preserve interface option shape in CreatePrototype selector`

Main implementation files:

- `frontend/src/lib/features/diagram/components/modals/EditNodeModal/components/EditAttributes/EditAttribute.tsx`
- `frontend/src/lib/features/diagram/components/modals/EditNodeModal/components/EditAttributes/EditAttributes.tsx`
- `frontend/src/lib/features/diagram/components/modals/EditNodeModal/components/EditAttributes/AiConfigSection.tsx`
- `frontend/src/lib/features/diagram/components/modals/EditNodeModal/components/EditAttributes/aiPresets.ts`

Implementation note: `EditAttributes.tsx` now updates its local attributes array immutably. The previous in-place `s[idx] = v` could mutate `node.data.attributes` and keep the Save button disabled after AI form edits.

## Step 0

G0 / G0-source passed.

Evidence:

- `docs/evidence/scripts/t4_g0_selector_shape.mjs`
- `docs/evidence/t4_g0_selector_shape.json`
- `docs/evidence/t4_g0_default_shape.json`
- `docs/evidence/t4_g0_reselect_shape.json`
- `docs/evidence/t4_g0_selector_shape.log`

Result:

- default POST body interfaces are `{label, value}`
- default `/meta/` interfaces are `{label, value}`
- manual deselect/reselect POST body interfaces are `{label, value}`
- manual deselect/reselect `/meta/` interfaces are `{label, value}`
- reselect generation succeeded as `LibraryT4G0Reselect`

## Form Save Gates

Raw DB checks:

- `docs/evidence/t4_db_bookloan_canonical.json`
- `docs/evidence/t4_db_bookloan_safe_risky.json`
- `docs/evidence/t4_db_bookloan_model_strong.json`
- `docs/evidence/t4_db_bookloan_restored_canonical.json`
- `docs/evidence/t4_db_bookloan_off.json`
- `docs/evidence/t4_db_both_off.json`
- `docs/evidence/t4_db_both_canonical.json`

Passed:

- G-save-on: `BookLoan.late_risk.ai_config` deep-equals canonical late return risk config.
- G-dynamic: `trigger.class == "BookLoan"` and `output.write_back == "late_risk"`.
- G-values: `SAFE, RISKY` saved as array `["SAFE", "RISKY"]`, then restored to `["LOW", "MEDIUM", "HIGH"]`.
- G-edit: `model_profile` changed to `strong` in raw DB, then restored to `cheap`.
- G-save-off-DB: toggle-off saved raw `BookLoan.late_risk` without an `ai_config` key.
- G-save-off-API: typed API observed `ai_config: null` after raw omit.

Form screenshots:

- `docs/evidence/t4_form_toggle_off.png`
- `docs/evidence/t4_form_preset_five_groups.png`
- `docs/evidence/t4_form_allowed_values_edit.png`
- `docs/evidence/t4_form_saved_echo.png`
- `docs/evidence/t4_form_customer_reading_plan.png`

## Reset Safety

Reset script:

- `docs/evidence/scripts/t4_reset_ai_config.py`

Evidence:

- `docs/evidence/t4_reset_before.json`
- `docs/evidence/t4_reset_after_first.json`
- `docs/evidence/t4_restore_after.json`
- `docs/evidence/t4_reset_before_second.json`
- `docs/evidence/t4_reset_after_second.json`
- `docs/evidence/t4_reset_safety.log`

Result:

- reset removed target `ai_config` keys
- restore deep-matched the original snapshot
- second reset left both target attributes without `ai_config`

## UI Reconfiguration

From reset state, both target attributes were configured only through the Studio UI:

- `BookLoan.late_risk`: `Late return risk`
- `Customer.reading_plan`: `Reading plan`

Evidence:

- `docs/evidence/t4_form_bookloan_enable_after_reset.log`
- `docs/evidence/t4_form_customer_enable_reading_plan.log`
- `docs/evidence/t4_db_both_canonical.json`

## Prototype

Created through Studio UI:

- prototype: `LibraryT4A`
- prototype id: `365f41f4-3fd0-43cd-ae8c-5fbfd55a40d3`

Evidence:

- `docs/evidence/t4_ui_generate.log`
- `docs/evidence/t4_ui_result.json`
- `docs/evidence/t4_metadata_from_ui.json`
- `docs/evidence/t4_generation.log`
- `docs/evidence/t4_ui_create_done.png`

G-authority passed:

- `docs/evidence/t4_authority_metadata.json`
- final `/meta/` contains canonical `BookLoan.late_risk` and `Customer.reading_plan` configs
- `BookLoan.late_risk.output.allowed_values == ["LOW", "MEDIUM", "HIGH"]`

## Regression

Evidence:

- `docs/evidence/t4_g_jsonl_pre_smoke.log`
- `docs/evidence/t4_showmigrations.log`
- `docs/evidence/t4_seed_role_check.log`
- `docs/evidence/t4_t1_regression_v1_v5.log`
- `docs/evidence/t4_v6_smoke.log`

Passed:

- generated app JSONL absent/empty before smoke/browser
- migrations `[X]`
- seed counts and role flags match T3
- V1-V5 pass
- V6 fake post-save writes `BookLoan.late_risk == "LOW"`

## E2E

Post-V6 baseline:

```json
{
  "alice_id": 1,
  "alice_reading_plan": "",
  "bookloan_count": 6,
  "jsonl_lines": 1,
  "max_bookloan_id": 6
}
```

Browser evidence:

- `docs/evidence/t4_browser_librarian_e2e.log`
- `docs/evidence/t4_browser_librarian_e2e_result.json`
- `docs/evidence/t4_browser_member_action.log`
- `docs/evidence/t4_browser_member_action_result.json`
- `docs/evidence/t4_browser_runtime.log`

Screenshots:

- `docs/evidence/t4_browser_studio_run.png`
- `docs/evidence/t4_browser_librarian_create_form.png`
- `docs/evidence/t4_browser_librarian_list_late_risk.png`
- `docs/evidence/t4_browser_member_button.png`
- `docs/evidence/t4_browser_member_result.png`

Combined after-check:

- `docs/evidence/t4_e2e_after.log`

Result:

- BookLoan count `6 -> 7`
- new BookLoan row has `late_risk == "LOW"`
- alice `reading_plan` changed from empty to `1) Book A; 2) Book B; 3) Book C`
- JSONL lines `1 -> 3`
- the two new JSONL records are one fake `BookLoan.late_risk` invoke and one fake `Customer.reading_plan` `invoke_chain`

## Verification

Commands passed:

```bash
npm run build
python3 -m py_compile docs/evidence/scripts/t4_assert_ai_config.py docs/evidence/scripts/t4_assert_metadata.py docs/evidence/scripts/t4_reset_ai_config.py docs/evidence/scripts/t4_e2e_baseline.py docs/evidence/scripts/t4_e2e_after.py
node --check docs/evidence/scripts/t4_form_action.mjs
node --check docs/evidence/scripts/t4_g0_selector_shape.mjs
```

Known pre-existing local diff:

- `docker-compose.yaml` remains modified and was not touched for T4.
