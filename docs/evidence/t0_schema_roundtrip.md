# T0 Evidence - Attribute schema preserves ai_config

Date: 2026-07-06

## Code change

- Changed `api/model/metadata/specification/kernel/__init__.py`
- Added `Attribute.ai_config: Optional[dict] = None`
- No typed submodel was added for `ai_config`.

## Static audit

No stop condition was found.

- `metadata/api/schemas/meta.py`: uses `ClassifierSchema` / raw import-export dicts; no Attribute field whitelist.
- `metadata/api/views/systems/classifiers.py`: returns ORM classifiers through response schema; no dump exclusion.
- `metadata/api/views/systems/relations.py`: relation-only path; no Attribute field whitelist.
- `metadata/specification/applications/classifiers.py`: references kernel `Attribute`; no re-declared Attribute fields.
- `diagram/api/schemas/edge.py`: relation schema only; no Attribute whitelist.
- `diagram/api/views/node.py`: `update_node` validates merged class data but stores the raw merged dict; `model_dump()` only touches node layout data.
- `diagram/api/views/edge.py`: `model_dump(exclude_unset=True, exclude_none=True)` only touches edge layout data.
- `metadata/specification/__init__.py`: `ClassifierSchema` serializes `data` through the typed classifier union; no extra exclusion.
- `diagram/api/schemas/diagram.py`: `FullDiagram` uses `NodeSchema`; `RelatedClassAttribute` is only a light related-diagram summary.
- `diagram/api/views/system.py`: `GET /diagram/system/{id}/` returns `FullDiagram`.
- `frontend/src/lib/features/prototypes/queries.ts`: `useSystemDiagrams` returns response data unchanged.
- `frontend/src/lib/features/prototypes/components/CreatePrototype.tsx`: submits `metadata.diagrams = diagrams` unchanged.

## G0 baseline

Log: `docs/evidence/t0_g0_baseline.log`

Result: PASS.

- DB precheck: `BookLoan.late_risk` and `Customer.reading_plan` both had `ai_config`.
- `GET /api/v1/diagram/system/7d735a07-b6cd-409d-9cc7-f3a07cbec983/` returned both attributes without `ai_config`.
- This proves the pre-change typed API response stripped the field.

## G1 serialization

Log: `docs/evidence/t0_g1_serialization.log`

Result: PASS.

- `BookLoan.late_risk.ai_config.trigger.type == "post_save"`
- `Customer.reading_plan.ai_config.trigger.type == "user_action"`
- Non-AI attribute observation: serialized with `"ai_config": null`.

## G2 UI-style roundtrip

Log: `docs/evidence/t0_g2_roundtrip.log`

Result: PASS.

- Source path: GET full diagram response.
- Mutation: PATCH node with complete `cls.attributes`, changing only `BookLoan.late_risk.description`.
- New description: `T0 roundtrip description 1783311640`
- DB read after PATCH: `late_risk.ai_config` matched the pre-PATCH object exactly.

## G3 regression spot checks

Backend log: `docs/evidence/t0_g3_backend.log`

Result: PASS.

- `GET /api/v1/metadata/systems/7d735a07-b6cd-409d-9cc7-f3a07cbec983/classes/` returned 200 and 5 class classifiers.
- Project export via `/api/v1/metadata/projects/export/8cb1ece6-71a0-4e7e-8c0f-7baeed02601e/` retained `BookLoan.late_risk.ai_config`.

Frontend log: `docs/evidence/t0_g3_frontend_console.log`

Result: PASS.

- Headless Chrome opened `http://ai4mde.localhost/diagram/a9cb6660-0a0c-423a-9830-ec80067f459f`.
- Page title: `AI4MDE - Editor`
- Page text included `Customer.reading_plan` and `BookLoan.late_risk`.
- `consoleErrorCount: 0`
- Screenshot: `docs/evidence/t0_frontend_class_diagram.png`

## Scripts

- `docs/evidence/scripts/t0_verify_roundtrip.py`
- `docs/evidence/scripts/t0_frontend_console_check.mjs`

## Syntax checks

- `python3 -m py_compile studio/api/model/metadata/specification/kernel/__init__.py studio/docs/evidence/scripts/t0_verify_roundtrip.py`
- `node --check docs/evidence/scripts/t0_frontend_console_check.mjs`
