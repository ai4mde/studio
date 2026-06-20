"""
Step 2 - ai_config persistence verification for BookLoan.late_risk.
Run inside the studio-api Django shell. Prints structured PASS/INFO lines.
Capture stdout/stderr to docs/evidence/step2_aiconfig_persistence.log.
"""
import json

SYSTEM_ID = "7d735a07-b6cd-409d-9cc7-f3a07cbec983"
PROJECT_ID = "8cb1ece6-71a0-4e7e-8c0f-7baeed02601e"
ARTIFACT = "/tmp/step2_library_model.json"

from metadata.models import Classifier, Project, System


def ok(tag, msg):
    print(f"[PASS] {tag}: {msg}")


def info(tag, msg):
    print(f"[INFO] {tag}: {msg}")


# ---------- PREFLIGHT: confirm clean Step 1 baseline ----------
sysobj = System.objects.get(id=SYSTEM_ID)
nc0, nr0 = sysobj.classifiers.count(), sysobj.relations.count()
info("preflight", f"system={sysobj.id} project={sysobj.project_id} classifiers={nc0} relations={nr0}")
assert str(sysobj.id) == SYSTEM_ID, "system id mismatch"
assert str(sysobj.project_id) == PROJECT_ID, "system is not under the expected Library project"
assert nc0 == 6 and nr0 == 4, f"baseline drift BEFORE import: expected 6/4, got {nc0}/{nr0}"

bl0 = Classifier.objects.get(system_id=SYSTEM_ID, data__name="BookLoan", data__type="class")
attrs0 = bl0.data.get("attributes", [])
info("preflight", f"BookLoan initial attributes={attrs0}")

assert attrs0 == [], (
    "BookLoan already has attributes before Step 2 import. "
    "Restore/re-import Step 1 baseline first, or explicitly treat this as a rerun."
)
ok("preflight", "Step 1 baseline intact (6 classifiers, 4 relations; BookLoan has no attributes)")

# ---------- IMPORT (mirror step1_import_library.py) ----------
with open(ARTIFACT, "r", encoding="utf-8") as f:
    data = json.load(f)
project = Project.import_from_json(data)
assert str(project.id) == PROJECT_ID, "import produced an unexpected project id"
ok("import", f"Project.import_from_json ok, project={project.id}")
sysobj = System.objects.get(id=SYSTEM_ID)

# ---------- LOCATE BookLoan ----------
bl = Classifier.objects.get(system_id=SYSTEM_ID, data__name="BookLoan", data__type="class")
late = next((a for a in bl.data.get("attributes", []) if a.get("name") == "late_risk"), None)
assert late is not None, "late_risk attribute not present in BookLoan.data"
assert late.get("type") == "str", "late_risk type must be str"
assert late.get("derived") is False, "late_risk must be stored (derived false)"
ok("attribute", f"late_risk present; type={late.get('type')} derived={late.get('derived')}")

# ---------- POSITIVE: ai_config survives the import path ----------
ai = late.get("ai_config")
assert ai is not None, "ai_config stripped on import path (UNEXPECTED - contradicts ImportClassifier.data:dict)"
assert ai.get("ai_config_version") == "1.0", "ai_config_version mismatch"
assert ai.get("output", {}).get("write_back") == "late_risk", "output.write_back mismatch"
ok("positive", f"ai_config intact via import path; keys={sorted(ai.keys())}")

# ---------- STRUCTURAL: no drift (full-replace hazard) ----------
nc, nr = sysobj.classifiers.count(), sysobj.relations.count()
assert nc == 6 and nr == 4, f"structural drift AFTER import: expected 6/4, got {nc}/{nr}"
ok("structural", f"no drift (classifiers={nc} relations={nr})")

# ---------- NEGATIVE: kernel typed path strips ai_config ----------
# Class is the exact model ClassifierSchema.data resolves to for type=="class".
# It mirrors the Studio read endpoint and any UI edit-save.
from metadata.specification.classes.classifiers import Class

validated = Class.model_validate(bl.data).model_dump()
late_v = next((a for a in validated["attributes"] if a.get("name") == "late_risk"), None)
assert late_v is not None, "late_risk lost entirely through kernel Class schema"
assert "ai_config" not in late_v, "ai_config UNEXPECTEDLY survived kernel schema (design assumption broken)"
ok("negative", f"ai_config stripped by kernel Class schema (expected); surviving attr keys={sorted(late_v.keys())}")

# ---------- IDEMPOTENCY: re-import upserts, no duplication ----------
Project.import_from_json(data)
sysobj = System.objects.get(id=SYSTEM_ID)
nc2, nr2 = sysobj.classifiers.count(), sysobj.relations.count()
bl2 = Classifier.objects.get(system_id=SYSTEM_ID, data__name="BookLoan", data__type="class")
late2 = next((a for a in bl2.data.get("attributes", []) if a.get("name") == "late_risk"), None)
assert nc2 == 6 and nr2 == 4, f"re-import structural drift: expected 6/4, got {nc2}/{nr2}"
assert late2 and late2.get("type") == "str" and late2.get("derived") is False, "re-import corrupted late_risk"
assert late2.get("ai_config", {}).get("ai_config_version") == "1.0", "re-import lost ai_config"
ok("idempotent", f"re-import upserted cleanly (classifiers={nc2}, relations={nr2}, ai_config intact)")

print("[DONE] Step 2 ai_config persistence VERIFIED.")
