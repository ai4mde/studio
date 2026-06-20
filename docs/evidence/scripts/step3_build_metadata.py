"""Step 3 - build RESOLVED generator metadata (shape 3) from the current Studio DB.
Run inside the studio-api Django shell. Resolves by fixed SYSTEM_ID, writes the
metadata to a file, and asserts BookLoan.late_risk.ai_config is present
(raw n.cls.data passthrough). No POST / generate / migrate."""
import json, os
from metadata.models import System
from diagram.models import Diagram, Edge

SYSTEM_ID  = os.environ.get("STEP3_SYSTEM_ID", "7d735a07-b6cd-409d-9cc7-f3a07cbec983")
PROJECT_ID = "8cb1ece6-71a0-4e7e-8c0f-7baeed02601e"
OUT = os.environ.get("STEP3_METADATA_OUT", "/tmp/step3_generator_metadata_sent.json")

system = System.objects.select_related("project").get(id=SYSTEM_ID)
project = system.project
assert str(project.id) == PROJECT_ID, f"system {SYSTEM_ID} not under expected Library project (got {project.id})"
print(f"[step3-meta] project={project.id} ({project.name}) system={system.id}")

diagrams_meta = []
for diagram in Diagram.objects.filter(system=system):          # mirror Step 1 (no order_by)
    nodes = list(diagram.nodes.select_related("cls").all())
    node_id_by_cls = {str(n.cls_id): str(n.id) for n in nodes}
    meta_nodes = [{
        "id": str(n.id),
        "cls": n.cls.data,            # RAW classifier data -> carries ai_config verbatim
        "cls_ptr": str(n.cls_id),
        "data": n.data or {"position": {"x": 0, "y": 0}},
    } for n in nodes]
    meta_edges = []
    for e in Edge.objects.filter(diagram=diagram).select_related("rel"):
        src = node_id_by_cls.get(str(e.rel.source_id)); tgt = node_id_by_cls.get(str(e.rel.target_id))
        if src is None or tgt is None:
            continue
        meta_edges.append({"id": str(e.id), "rel": e.rel.data, "rel_ptr": str(e.rel_id),
                           "source_ptr": src, "target_ptr": tgt, "data": e.data or {}})
    diagrams_meta.append({"id": str(diagram.id), "type": diagram.type, "name": diagram.name,
                          "description": diagram.description or "", "nodes": meta_nodes, "edges": meta_edges})

metadata = {"diagrams": diagrams_meta, "interfaces": [], "useAuthentication": False}

def find_attr(md, model, attr):
    for d in md["diagrams"]:
        if d.get("type") != "classes":
            continue
        for n in d["nodes"]:
            c = n.get("cls", {})
            if c.get("type") == "class" and c.get("name") == model:
                for a in c.get("attributes", []):
                    if a.get("name") == attr:
                        return a
    return None

la = find_attr(metadata, "BookLoan", "late_risk")
assert la is not None, "BookLoan.late_risk not in resolved metadata (run Step 2 first)"
assert la.get("ai_config", {}).get("ai_config_version") == "1.0", "ai_config missing/stripped in resolved metadata"
print(f"[step3-meta][PASS] BookLoan.late_risk.ai_config present in metadata: keys={sorted(la['ai_config'].keys())}")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)
print(f"[step3-meta] wrote resolved metadata -> {OUT}")
