import json
from metadata.models import Project, System, Classifier, Interface

SYSTEM_ID  = "7d735a07-b6cd-409d-9cc7-f3a07cbec983"
PROJECT_ID = "8cb1ece6-71a0-4e7e-8c0f-7baeed02601e"
ARTIFACT   = "/tmp/step5_library_model.json"

with open(ARTIFACT) as f:
    data = json.load(f)
project = Project.import_from_json(data)
assert str(project.id) == PROJECT_ID, "unexpected project id after import"
print(f"[import] ok project={project.id}")

system = System.objects.get(id=SYSTEM_ID)
nc, nr, ni = system.classifiers.count(), system.relations.count(), system.interfaces.count()
print(f"[counts] classifiers={nc} relations={nr} interfaces={ni}")
assert nc == 7, f"expected 7 classifiers (5 class + 1 enum + 1 actor), got {nc}"
assert nr == 4, f"expected 4 relations, got {nr}"
assert ni == 1, f"expected 1 interface, got {ni}"

# ai_config still intact
bl = Classifier.objects.get(system_id=SYSTEM_ID, data__name="BookLoan", data__type="class")
late = next(a for a in bl.data["attributes"] if a["name"] == "late_risk")
assert late.get("ai_config", {}).get("ai_config_version") == "1.0", "ai_config lost after re-import"
print("[PASS] BookLoan.late_risk.ai_config intact")

# actor classifier
actor = Classifier.objects.get(system_id=SYSTEM_ID, data__type="actor")
assert actor.data.get("name") == "librarian", "actor classifier name != librarian"
print(f"[PASS] actor classifier present: {actor.data}")

# interface wiring
iface = system.interfaces.get()
assert iface.name == "librarian", f"interface name != librarian: {iface.name}"
assert str(iface.actor_id) == str(actor.id), "interface.actor does not point to the librarian actor"
sec = iface.data["sections"][0]
assert sec["class"] == str(bl.id) or sec["class"] == bl.id, "section.class != BookLoan classifier id"
assert sec["operations"] == {"create": True, "delete": False, "update": True}, "unexpected section operations"
print(f"[PASS] interface 'librarian' wired to actor + BookLoan section (create/update)")
print("[DONE] Step 5A import + DB verification PASSED.")
