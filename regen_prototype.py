import os, sys, django, json, requests, shutil
sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
django.setup()

from diagram.models import Diagram, Node, Edge
from metadata.models import System, Interface

system_id = "8ac86bfe-ec5d-4b2e-b381-d84392dc9f08"
system = System.objects.get(id=system_id)

# Build diagrams in the exact format FullDiagram/NodeSchema/EdgeSchema produces
diagrams = []
for diagram in Diagram.objects.filter(system=system).prefetch_related("nodes__cls", "edges__rel"):
    nodes = []
    for node in diagram.nodes.select_related("cls").all():
        nodes.append({
            "id": str(node.id),
            "cls": node.cls.data,
            "cls_ptr": str(node.cls_id),
            "data": node.data,  # {"position": {"x": ..., "y": ...}}
        })
    edges = []
    for edge in diagram.edges.select_related("rel").all():
        # source_ptr/target_ptr are NODE UUIDs (not classifier UUIDs)
        src_node = diagram.nodes.filter(cls=edge.rel.source).first()
        tgt_node = diagram.nodes.filter(cls=edge.rel.target).first()
        edges.append({
            "id": str(edge.id),
            "rel": edge.rel.data,
            "rel_ptr": str(edge.rel_id),
            "source_ptr": str(src_node.id) if src_node else None,
            "target_ptr": str(tgt_node.id) if tgt_node else None,
            "data": edge.data,
        })
    diagrams.append({
        "id": str(diagram.id),
        "name": diagram.name,
        "type": diagram.type,
        "description": diagram.description or "",
        "project": str(diagram.system.project_id),
        "system": str(diagram.system_id),
        "system_id": str(diagram.system_id),
        "system_name": diagram.system.name,
        "nodes": nodes,
        "edges": edges,
        "related_diagrams": [],
    })

print(f"Got {len(diagrams)} diagrams")
for d in diagrams:
    print(f"  - {d['name']} ({d['type']}): {len(d['nodes'])} nodes, {len(d['edges'])} edges")

# Build interfaces as {label, value: {id, name, data, actor, ...}}
selected_interfaces = []
for iface in Interface.objects.filter(system=system).select_related("actor"):
    actor_name = iface.actor.data.get("name", "Unknown") if iface.actor else "Unknown"
    selected_interfaces.append({
        "label": actor_name,
        "value": {
            "id": str(iface.id),
            "name": actor_name,
            "description": iface.description or "",
            "system": str(iface.system_id),
            "actor": str(iface.actor_id) if iface.actor_id else None,
            "data": iface.data,
        },
    })
    pages = iface.data.get("pages", [])
    sections = iface.data.get("sections", [])
    print(f"  - {actor_name}: {len(pages)} pages, {len(sections)} sections")

metadata = {
    "diagrams": diagrams,
    "interfaces": selected_interfaces,
    "useAuthentication": True,
}

# (old prototype dir must be deleted from prototypes container before calling)

# Call the prototypes Flask service
PROTOTYPES_URL = "http://studio-prototypes:8010/generate"
data = {
    "id": "regen-final",
    "name": "applicants",
    "system": system_id,
    "metadata": json.dumps(metadata),
}
print(f"\nCalling {PROTOTYPES_URL}...")
resp = requests.post(PROTOTYPES_URL, json=data, timeout=300)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")
