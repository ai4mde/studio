# Step 5A Evidence - metadata gate

Canonical artifact: docs/evidence/step5_library_model.json  
Resolved metadata: docs/evidence/step5_generator_metadata_sent.json  
Build log: docs/evidence/step5a_build.log  
Import log: docs/evidence/step5a_import_verify.log  
Metadata log: docs/evidence/step5a_metadata.log

## Definition Of Done

- [x] `step5_library_model.json` equals Step 2 plus exactly one actor classifier and one `librarian` interface .... PASS
- [x] Section attributes contain only editor-facing fields and no `ai_config` .... PASS
- [x] Import succeeds via `Project.import_from_json` .... PASS
- [x] DB counts are 7 classifiers / 4 relations / 1 interface .... PASS
- [x] `BookLoan.late_risk.ai_config` remains intact after re-import .... PASS
- [x] Actor classifier exists with `data.type == "actor"` and `name == "librarian"` .... PASS
- [x] Interface `librarian` points to the librarian actor .... PASS
- [x] Interface section targets `BookLoan` with operations `{create: true, delete: false, update: true}` .... PASS
- [x] Resolved metadata has `useAuthentication == true` .... PASS
- [x] Resolved interface has `label == value.name == "librarian"` .... PASS
- [x] Resolved interface has pages and sections; page type is `normal` .... PASS
- [x] Resolved metadata still carries `BookLoan.late_risk.ai_config` .... PASS
- [x] No generation, migration, generator route, UI, compose edit, or repository operation was used .... PASS

## Structural Artifact Gate

```text
[PASS] step5 artifact = step2 + 1 actor classifier + 1 librarian interface
[PASS] librarian section attributes are editor-facing only; no ai_config copied into interface data
```

## Import Gate

```text
[counts] classifiers=7 relations=4 interfaces=1
[PASS] BookLoan.late_risk.ai_config intact
[PASS] actor classifier present: {'name': 'librarian', 'type': 'actor'}
[PASS] interface 'librarian' wired to actor + BookLoan section (create/update)
[DONE] Step 5A import + DB verification PASSED.
```

Actor/interface wiring:

```text
actor=c8078430-ab2c-4a37-83c1-4c4149460165
interface=67638059-6cad-41ae-8da5-d593efca3ba5
interface.actor=c8078430-ab2c-4a37-83c1-4c4149460165
section.class(BookLoan)=9f7df5b5-fde5-429e-982b-48c37e868613
operations={'create': True, 'delete': False, 'update': True}
```

## Resolved Metadata Gate

```text
[PASS] resolved metadata: useAuthentication=True, interface label/value.name='librarian', pages+sections present, BookLoan.late_risk.ai_config present
```

The page is a normal, uncategorized page: `category` is intentionally `null`.

Interface settings are exactly:

```json
{"managerAccess": false}
```

## Finding

The canonical artifact now carries a `librarian` actor and a normal CRUD interface over `BookLoan`.

`ai_config` survives alongside the actor/interface metadata: `BookLoan.late_risk.ai_config.ai_config_version == "1.0"` after re-import and in resolved generator metadata.

A correct resolved generator metadata artifact was produced for Step 5C: interface `{label, value}` both use `librarian`, and `useAuthentication` is `true`.

Step 5A does not generate code, does not migrate, does not run the app, and does not use `studio-prototypes`.
