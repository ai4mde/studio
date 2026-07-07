# T2 runtime bringup evidence

Date: 2026-07-06

Prototype: `LibraryT2A`
System: `7d735a07-b6cd-409d-9cc7-f3a07cbec983`

## Production changes

- `generator.sh` copies `demo_data/0002_library_demo_data.py` into generated `shared_models/migrations/` after `makemigrations` and before `migrate`.
- `0002_library_demo_data.py` seeds demo data with `bulk_create`; seeded historical `BookLoan` rows set `late_risk` directly before `bulk_create`.
- `SectionAttribute` carries `ai_managed`; loading cross-references section `class` with class-diagram `cls_ptr` and checks `ai_config.output.write_back`.
- Create/update forms and generated create/update view `fields` exclude AI-managed attributes; list/display table still renders them.
- `config/prototypes.env` contains exactly one tracked `AI_RUNTIME_FAKE=1` line.

## Demo credentials

- `demo_librarian / ai4mde-demo`
- `demo_member / ai4mde-demo`

## Gate results

- G-gen: `LibraryT2A` generated through the Studio Prototypes UI. The UI helper failed after generation while reading the CDP response body, but the prototype row, generated directory, Flask `/generate` 200, AI detection, and migration application are captured in `t2_generation.log`.
- G-seed JSONL pre-smoke: PASS. Immediately after generation and before smoke/browser actions, `ai_invocations.jsonl` was absent or empty. See `t2_g_seed_jsonl_pre_smoke.log`.
- G-seed DB: PASS. Counts were User 2, Author 3, Book 6, Customer 2, Loan 5, BookLoan 5; seeded BookLoan `late_risk` values were `LOW`, `LOW`, `MEDIUM`, `LOW`, `HIGH`. See `t2_seed_check.log`.
- Migrations: PASS. `shared_models.0002_library_demo_data` and workflow migrations are `[X]`. See `t2_showmigrations.log`.
- G-reg: PASS. T1 semantic V1-V5 passed for `LibraryT2A`; V6 fake smoke passed separately. See `t2_t1_regression_v1_v5.log` and `t2_v6_smoke.log`.
- G-form/G-form-source: PASS. Generated BookLoan create/update `fields = []`; rendered create HTML has no `name="late_risk"` input, while `late_risk` table header and seed values remain visible. See `t2_form_checks.log`.
- G-env: PASS. `studio-prototypes` environment has `AI_RUNTIME_FAKE=1`; browser e2e did not export it manually. See `t2_env_check.log` and `t2_browser_e2e_result.json`.
- G-e2e: PASS. Browser UI run/login/create flow created exactly one new BookLoan. Baseline count was 6/max id 6/JSONL 1; after browser action count was 7, new id 7 had `late_risk='LOW'`, and JSONL lines increased to 2 with a BookLoan `late_risk` LOW fake record. See `t2_e2e_baseline.json` and `t2_e2e_after.log`.

## Browser screenshots

- Studio Run: `docs/evidence/t2_browser_studio_run.png`
- Login page: `docs/evidence/t2_browser_login.png`
- Create form without `late_risk`: `docs/evidence/t2_browser_create_form.png`
- List page with `late_risk`: `docs/evidence/t2_browser_list_late_risk.png`

## Raw evidence files

- Generation/runtime: `t2_generation.log`, `t2_browser_runtime.log`, `t2_metadata_from_ui.json`
- Seed/migrations: `t2_g_seed_jsonl_pre_smoke.log`, `t2_showmigrations.log`, `t2_seed_check.log`
- Regression/form: `t2_t1_regression_v1_v5.log`, `t2_v6_smoke.log`, `t2_form_checks.log`
- Browser e2e: `t2_browser_e2e.log`, `t2_browser_e2e_result.json`, `t2_e2e_baseline.json`, `t2_e2e_after.log`, `t2_env_check.log`
