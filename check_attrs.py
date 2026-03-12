import os, sys, django, json
sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
django.setup()
from metadata.models import Interface
for iface in Interface.objects.filter(system_id="8ac86bfe-ec5d-4b2e-b381-d84392dc9f08").select_related("actor"):
    actor = iface.actor.data.get("name", "?") if iface.actor else "?"
    pages = iface.data.get("pages", [])
    sections_all = iface.data.get("sections", [])
    print(f"\n{'='*60}")
    print(f"ACTOR: {actor}")
    print(f"{'='*60}")
    for p in pages:
        ptype = p.get("type", {})
        ptype_val = ptype.get("value", ptype) if isinstance(ptype, dict) else ptype
        print(f"\n  Page: {p['name']} (type={ptype_val})")
        for sec_ref in p.get("sections", []):
            sec_id = sec_ref.get("value") if isinstance(sec_ref, dict) else sec_ref
            sec = next((s for s in sections_all if s.get("id") == sec_id), None)
            if sec:
                model_name = sec.get("model_name", sec.get("name", ""))
                ops = sec.get("operations", {})
                attrs = sec.get("attributes", [])
                attr_names = [a.get("name", "?") for a in attrs]
                print(f"    Section: {sec['name']} -> model={model_name}")
                print(f"      ops: create={ops.get('create')}, update={ops.get('update')}, delete={ops.get('delete')}")
                print(f"      attributes: {attr_names}")
