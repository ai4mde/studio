# T3 Member Reading Plan Evidence

Date: 2026-07-07

## Summary

T3 is complete for `LibraryT3A`.

The generated app supports the member flow:

1. Log in as `demo_member / ai4mde-demo`.
2. Open the member Customer page.
3. Click alice row `generate_reading_plan`.
4. Fake AI runtime writes `Customer.reading_plan`.
5. The button response page immediately shows the generated summary.

No conditional `shared_views.py.jinja2` fix was required because G-fresh passed directly.

T2 precondition was satisfied first by commit `002631e9 feat(t2): demo seed migration, fake env, ai-managed read-only fields`.

## Reproducible Interface Data

Member interface was applied through:

- `docs/evidence/scripts/t3_apply_member_interface.py`
- `docs/evidence/t3_member_interface_patch.log`
- `docs/evidence/t3_member_interface.json`
- `docs/evidence/t3_member_interface_before.json`
- `docs/evidence/t3_member_interface_after.json`

Stable ids:

- member interface: `c7a2acd3-1e1d-5cbe-a0fa-4ac850a2e5ff`
- member page: `4f934d64-a4c0-5692-b913-78acdfe03624`
- member Customer section: `330f864f-410b-5e12-b20c-a81c20ce1594`

The metadata API update endpoint was:

`http://localhost:8000/api/v1/metadata/interfaces/c7a2acd3-1e1d-5cbe-a0fa-4ac850a2e5ff/`

Required method entry is present with both fields:

```json
{
  "body": "def generate_reading_plan(self):\n    pass",
  "name": "generate_reading_plan"
}
```

Note: the Studio DB has no separate `member` actor classifier. The replay script logs this and uses the existing actor only to satisfy the `Interface.actor` foreign key. Generated role fields still derive from interface names; `is_member` and `demo_member.is_member == True` are verified below.

## Prototype

Created through the Studio UI:

- prototype name: `LibraryT3A`
- prototype id: `ee40bbac-ca04-4e42-83a6-589b24f8d8e0`
- system id: `7d735a07-b6cd-409d-9cc7-f3a07cbec983`

Evidence:

- `docs/evidence/t3_ui_generate.log`
- `docs/evidence/t3_ui_result.json`
- `docs/evidence/t3_metadata_from_ui.json`
- `docs/evidence/t3_generation.log`
- `docs/evidence/t3_ui_create_done.png`

## Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| G-iface | PASS | `t3_member_interface_patch.log` has Customer `reading_plan` and method `name` + `body`; `t3_member_interface.json` exported |
| G-gen/reg | PASS | `t3_t1_regression_v1_v5.log`, `t3_showmigrations.log`, `t3_seed_role_check.log` |
| G-jsonl-pre | PASS | `t3_g_jsonl_pre_smoke.log`: `ai_invocations.jsonl` absent or empty immediately after generation, before smoke/browser |
| V6 smoke | PASS | `t3_v6_smoke.log`: fake post-save writes `BookLoan.late_risk='LOW'` |
| G-run | PASS | `t3_run_check.json`: active prototype id `ee40bbac-ca04-4e42-83a6-589b24f8d8e0`, login page has `LibraryT3A` and member radio |
| G-btn | PASS | `t3_browser_member_action.log` and `t3_browser_member_button.png`: alice row has blank `reading_plan` and `generate_reading_plan` button |
| G-action | PASS | `t3_action_after.log`: alice `reading_plan` changed from empty to non-empty; JSONL line count went from 1 to 2 |
| G-fresh | PASS | `t3_browser_member_action.log` and `t3_browser_member_result.png`: response page immediately shows `1) Book A; 2) Book B; 3) Book C` |

## Seed And Role Check

From `docs/evidence/t3_seed_role_check.log`:

- User count: 2
- Author count: 3
- Book count: 6
- Customer count: 2
- Loan count: 5
- BookLoan count: 5
- User fields include `is_librarian` and `is_member`
- `demo_librarian` password valid: True
- `demo_member` password valid: True
- `demo_librarian.is_librarian`: True
- `demo_member.is_member`: True
- seeded `BookLoan.late_risk` values populated: `LOW`, `LOW`, `MEDIUM`, `LOW`, `HIGH`
- alice `reading_plan` starts empty

## Browser Action

Before click baseline, after V6 smoke:

```json
{
  "alice_id": 1,
  "alice_reading_plan": "",
  "jsonl_lines": 1
}
```

After clicking alice row `generate_reading_plan`:

- alice `reading_plan` before: empty
- alice `reading_plan` after: `1) Book A; 2) Book B; 3) Book C`
- JSONL baseline: 1
- JSONL after: 2
- last JSONL record:
  - `event`: `invoke_chain`
  - `mode`: `fake`
  - `model`: `Customer`
  - `status`: `success`
  - `trigger`: `user_action`
  - `write_back.field`: `reading_plan`

Evidence:

- `docs/evidence/t3_action_baseline.json`
- `docs/evidence/t3_browser_member_action.log`
- `docs/evidence/t3_browser_member_action_result.json`
- `docs/evidence/t3_action_after.log`
- `docs/evidence/t3_browser_runtime.log`

Screenshots:

- `docs/evidence/t3_browser_run_login.png`
- `docs/evidence/t3_browser_member_login.png`
- `docs/evidence/t3_browser_member_button.png`
- `docs/evidence/t3_browser_member_result.png`

## Verification Commands

Syntax checks passed:

```bash
python3 -m py_compile docs/evidence/scripts/t3_action_baseline.py docs/evidence/scripts/t3_action_after.py docs/evidence/scripts/t3_seed_role_check.py docs/evidence/scripts/t3_apply_member_interface.py
node --check docs/evidence/scripts/t3_browser_run.mjs
node --check docs/evidence/scripts/t3_browser_member_action.mjs
```

Production code diff check:

- `prototypes/backend/generation/templates/shared_views.py.jinja2` has no diff.
- The only tracked production diff observed after T3 is the pre-existing local `docker-compose.yaml` modification.

## Limitations Recorded

- Member can see all `Customer` rows; no row-level ownership is added in T3.
- The custom action is triggered by GET query parameters in the generated prototype.
- The interface editor still cannot select AI actions from a method dropdown.
- `reading_plan` is displayed as a raw compact summary string.
- `reading_plan` write-back remains bounded by the existing 255-character `CharField` design.
