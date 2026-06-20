# Step 2 Evidence - ai_config persistence (BookLoan.late_risk)

Artifact: docs/evidence/step2_library_model.json  
Import entry: Project.import_from_json  (ORM, mirrors step1_import_library.py)  
Run: 2026-06-15 17:46:54 CEST, studio-api service image, /usr/src/.venv/bin/python

## Host-side artifact diff
- [x] step2 differs from step1 by exactly one added BookLoan.late_risk attribute .... PASS

## Results
- [x] PREFLIGHT  baseline 6 classifiers / 4 relations, BookLoan has no attributes .... PASS
- [x] IMPORT     project id == 8cb1ece6-71a0-4e7e-8c0f-7baeed02601e ................. PASS
- [x] ATTRIBUTE  late_risk stored, str, derived=false ................................ PASS
- [x] POSITIVE   ai_config intact in Classifier.data ................................. PASS
- [x] STRUCTURAL no drift (6 classifiers / 4 relations) .............................. PASS
- [x] NEGATIVE   ai_config stripped by kernel Class schema ........................... PASS
- [x] IDEMPOTENT re-import clean, ai_config intact .................................... PASS

## Finding (limitation)

ai_config declared on a domain attribute persists through the import/export raw-dict path into Classifier.data.  
The kernel typed schema path strips ai_config silently. Therefore, for now, ai_config must be maintained in the canonical artifact JSON and imported through the official import path.

BookLoan must not be edited through the Studio UI after this step, because the UI read/edit-save path would drop ai_config.

## Raw log

See:

docs/evidence/step2_aiconfig_persistence.log
