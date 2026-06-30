import json

SYSTEM_ID = "7d735a07-b6cd-409d-9cc7-f3a07cbec983"
PROJECT_ID = "8cb1ece6-71a0-4e7e-8c0f-7baeed02601e"
ARTIFACT = "/tmp/step8_library_model.json"

from metadata.models import Classifier, Project, System

with open(ARTIFACT, "r", encoding="utf-8") as f:
    data = json.load(f)

project = Project.import_from_json(data)
assert str(project.id) == PROJECT_ID, f"unexpected project id: {project.id}"

sysobj = System.objects.get(id=SYSTEM_ID)
assert str(sysobj.project_id) == PROJECT_ID

cust = Classifier.objects.get(system_id=SYSTEM_ID, data__name="Customer", data__type="class")
attrs = cust.data.get("attributes", [])
rp = next((a for a in attrs if a.get("name") == "reading_plan"), None)

assert rp is not None, "Customer.reading_plan missing after import"
assert rp.get("type") == "str", rp
assert rp.get("derived") is False, rp

ai = rp.get("ai_config")
assert ai is not None, "reading_plan.ai_config stripped during import"
assert ai.get("trigger", {}).get("type") == "user_action", ai
assert ai.get("model_profile") == "strong", ai
assert ai.get("output", {}).get("write_back") == "reading_plan", ai
assert "reading_plan_analyze_taste_v1" in json.dumps(ai), ai

print("[PASS] Step 8 raw import: Customer.reading_plan + ai_config survived")
print(f"[INFO] system={sysobj.id} project={sysobj.project_id}")