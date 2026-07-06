# T1 Evidence - UI generation path preserves ai_config

Date: 2026-07-06

## Pre-clean

- T0 commits present:
  - `d63a7688 feat(t0): preserve ai_config through Attribute schema`
  - `6051845a docs(t0): add ai_config schema roundtrip evidence`
- `BookLoan.late_risk.description` was restored before T1:
  `AI-generated late-return risk label (LOW/MEDIUM/HIGH).`

## Frontend/Backend Preconditions

Capture point A is available and used.

- `create_prototype` persists `Prototype.metadata` as a JSONField.
- `GET /api/v1/generator/prototypes/{id}/meta/` returns that stored metadata.
- T1 capture file: `docs/evidence/t1_metadata_from_ui.json`

`CreatePrototype.tsx` submits metadata with:

- `diagrams`
- `interfaces`
- `useAuthentication`

The generator consumes `useAuthentication` via:

- Flask `/generate` writes the submitted metadata to a temporary JSON file.
- `generator.sh` sets `AUTH_PRESENT` from `get_globals.py get_auth`.
- `authentication_is_present()` reads `metadata["useAuthentication"]`.
- `AUTH_PRESENT=True` enables `AUTH_USER_MODEL = "shared_models.User"` and creates the authentication app instead of `noauth_home`.

Known UI selector defect recorded, not fixed in T1:

- The interface selector `onChange` strips `{label, value}` wrappers if touched.
- T1 avoided the defect by not touching the selector.
- Captured metadata kept `interfaces[0] = {"label": "librarian", "value": ...}`.

## UI Generation

- Prototype name: `LibraryT1A`
- Prototype id: `56022de9-a562-4ad7-8b29-c2b7206e2f53`
- System id: `7d735a07-b6cd-409d-9cc7-f3a07cbec983`
- Generated path:
  `prototypes/generated_prototypes/7d735a07-b6cd-409d-9cc7-f3a07cbec983/LibraryT1A`
- Route:
  Studio Prototypes UI -> Create Prototype modal -> A2 Django route -> Flask `/generate` -> `generator.sh`
- UI observation:
  `librarian` was visible as the default selected interface, and the selector was not changed.
- Auth observation:
  the authentication switch was left checked; captured metadata has `useAuthentication: true`.

## Gate Results

V1 metadata and detection: PASS.

- `BookLoan.late_risk.ai_config.trigger.type == "post_save"`
- `Customer.reading_plan.ai_config.trigger.type == "user_action"`
- `metadata.interfaces[*]` kept `{label, value}` shape.
- `value.name == "librarian"` exists.
- `t1_generation.log` contains both `[AI4MDE][ai_config]` lines and `detected 2 AI-managed attribute(s)`.

V2 AI artifacts: PASS.

- `shared_models/ai_hooks.py` exists.
- `shared_models/ai_actions.py` exists.
- `ai_runtime/` exists.
- `ai_runtime/` file set matches the Step 8 generated runtime file set.

V3 trigger split: PASS.

- `ai_hooks.py` post_save receiver is only for `BookLoan`.
- `reading_plan` and `Customer` receiver do not appear in hooks.
- `ai_actions.py` attaches `Customer.generate_reading_plan`.
- `late_risk` does not appear in actions.

V4 domain models: PASS.

- `Author`, `Book`, `Customer`, `Loan`, `BookLoan` exist.
- `Book.Category` enum contains the five expected literals.
- `BookLoan` contains `late_risk`, `Loan` FK, and `Book` FK.
- `Customer` contains `reading_plan`.
- Domain class bodies match Step 8 evidence order-independently.
- Non-gate auth observation: generated `User` has `is_librarian`.

V5 migrations: PASS.

- `shared_models [X] 0001_initial`
- `workflow_engine [X] 0001_initial`
- `workflow_engine [X] 0002_populate_workflow_engine`
- Generation log shows `POST /generate` 200.

V6 fake runtime smoke: PASS.

- `AI_RUNTIME_FAKE=1`
- Created a `BookLoan` instance.
- `late_risk` was written back as `LOW`.
- `ai_invocations.jsonl` contains one `post_save` invocation record for `BookLoan.late_risk`.

## Observations

UI metadata and script metadata are semantically aligned, but not byte-identical.

- UI metadata has the same top-level keys as Step 8: `diagrams`, `interfaces`, `useAuthentication`.
- UI metadata kept the interface wrapper shape: `{label, value}`.
- T0 causes non-AI attributes in typed API responses to carry `ai_config: null`; T1 captured 11 null `ai_config` values.
- The AI-managed attributes still carry full configs.
- Node/order and wrapper details should be treated as transport-shape differences, not semantic differences.

Generation timing baseline:

- Headless UI command returned after about 10 seconds.
- The isolated generator log segment runs from AI detection at `05:06:06Z` to `POST /generate` 200 at `05:06:08Z`.

## Evidence Files

- `docs/evidence/t1_metadata_from_ui.json`
- `docs/evidence/t1_generation.log`
- `docs/evidence/t1_showmigrations.log`
- `docs/evidence/t1_semantic_verify.log`
- `docs/evidence/t1_v6_smoke.log`
- `docs/evidence/t1_ai_invocations.jsonl`
- `docs/evidence/t1_ui_result.json`
- `docs/evidence/scripts/t1_semantic_verify.py`
- `docs/evidence/scripts/t1_ui_generate.mjs`
