import json, os
from metadata.models import System, Interface
from diagram.models import Diagram, Edge

SYSTEM_ID  = os.environ.get("STEP5_SYSTEM_ID", "7d735a07-b6cd-409d-9cc7-f3a07cbec983")
PROJECT_ID = "8cb1ece6-71a0-4e7e-8c0f-7baeed02601e"
OUT = os.environ.get("STEP5_METADATA_OUT", "/tmp/step5_generator_metadata_sent.json")

system = System.objects.select_related("project").get(id=SYSTEM_ID)
assert str(system.project_id) == PROJECT_ID
print(f"[step5-meta] system={system.id} project={system.project_id}")

# --- diagrams (same as Step 3: raw n.cls.data carries ai_config) ---
diagrams_meta = []
for diagram in Diagram.objects.filter(system=system):
    nodes = list(diagram.nodes.select_related("cls").all())
    node_id_by_cls = {str(n.cls_id): str(n.id) for n in nodes}
    meta_nodes = [{"id": str(n.id), "cls": n.cls.data, "cls_ptr": str(n.cls_id),
                   "data": n.data or {"position": {"x": 0, "y": 0}}} for n in nodes]
    meta_edges = []
    for e in Edge.objects.filter(diagram=diagram).select_related("rel"):
        src = node_id_by_cls.get(str(e.rel.source_id)); tgt = node_id_by_cls.get(str(e.rel.target_id))
        if src is None or tgt is None:
            continue
        meta_edges.append({"id": str(e.id), "rel": e.rel.data, "rel_ptr": str(e.rel_id),
                           "source_ptr": src, "target_ptr": tgt, "data": e.data or {}})
    diagrams_meta.append({"id": str(diagram.id), "type": diagram.type, "name": diagram.name,
                          "description": diagram.description or "", "nodes": meta_nodes, "edges": meta_edges})

# --- interfaces transformed to resolved ③ shape (label AND value.name both = interface name) ---
interfaces_meta = []
for iface in Interface.objects.filter(system=system):
    interfaces_meta.append({"label": iface.name, "value": {"name": iface.name, "data": iface.data}})

metadata = {"diagrams": diagrams_meta, "interfaces": interfaces_meta, "useAuthentication": True}

# --- assertions ---
assert metadata["useAuthentication"] is True
assert len(metadata["interfaces"]) == 1, "expected exactly one resolved interface"
i0 = metadata["interfaces"][0]
assert i0["label"] == "librarian" and i0["value"]["name"] == "librarian", "label/value.name must both be 'librarian'"
data0 = i0["value"]["data"]
assert data0["pages"] and data0["sections"], "resolved interface missing pages/sections"
assert data0["pages"][0]["type"]["value"] == "normal", "page should be normal type"

def find_attr(md, model, attr):
    for d in md["diagrams"]:
        if d.get("type") != "classes": continue
        for n in d["nodes"]:
            c = n.get("cls", {})
            if c.get("type") == "class" and c.get("name") == model:
                for a in c.get("attributes", []):
                    if a.get("name") == attr: return a
    return None
la = find_attr(metadata, "BookLoan", "late_risk")
assert la and la.get("ai_config", {}).get("ai_config_version") == "1.0", "ai_config missing in resolved metadata"
print("[PASS] resolved ③: useAuthentication=True, interface label/value.name='librarian', pages+sections present, BookLoan.late_risk.ai_config present")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)
print(f"[step5-meta] wrote {OUT}")
