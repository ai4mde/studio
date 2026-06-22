import copy
import json
from pathlib import Path

s2 = json.loads(Path("docs/evidence/step2_library_model.json").read_text())
s5 = json.loads(Path("docs/evidence/step5_library_model.json").read_text())
sys2, sys5 = s2["systems"][0], s5["systems"][0]

# the two added objects
added_actor = [c for c in sys5["classifiers"] if c["data"].get("type") == "actor"]
assert len(added_actor) == 1, "expected exactly one actor classifier"
assert added_actor[0]["data"].get("name") == "librarian", "actor classifier name must be librarian"
assert len(sys5.get("interfaces", [])) == 1, "expected exactly one interface"
assert len(sys2.get("interfaces", [])) == 0, "step2 unexpectedly already had interfaces"

iface = sys5["interfaces"][0]
assert iface["name"] == "librarian", "interface name must be librarian"
assert iface["actor"] == added_actor[0]["id"], "interface.actor must point to the librarian actor"
assert iface["data"]["pages"][0]["type"] == {"label": "Normal", "value": "normal"}, "page must be normal"
assert iface["data"]["pages"][0]["category"] is None, "page must be uncategorized"
assert iface["data"]["settings"] == {"managerAccess": False}, "unexpected interface settings"
section = iface["data"]["sections"][0]
assert section["operations"] == {"create": True, "delete": False, "update": True}, "unexpected section operations"
assert len(section["attributes"]) == 1, "expected exactly one section attribute"
assert set(section["attributes"][0]) == {"body", "enum", "name", "type", "derived", "description"}, (
    "section attribute must contain only editor-facing fields"
)
assert "ai_config" not in section["attributes"][0], "section attribute must not contain ai_config"

actor_ids = {c["id"] for c in added_actor}
for diagram in sys5.get("diagrams", []):
    node_class_ids = {n.get("cls") for n in diagram.get("nodes", [])}
    assert not (node_class_ids & actor_ids), "actor classifier must not be placed on a diagram"

# remove the additions and compare the rest to step2
s5n = copy.deepcopy(s5)
sys5n = s5n["systems"][0]
sys5n["classifiers"] = [c for c in sys5n["classifiers"] if c["data"].get("type") != "actor"]
sys5n["interfaces"] = []
assert s5n == s2, "step5 differs from step2 beyond the added actor + interface"
print("[PASS] step5 artifact = step2 + 1 actor classifier + 1 librarian interface")
print("[PASS] librarian section attributes are editor-facing only; no ai_config copied into interface data")
