import os, sys, django, json
sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
django.setup()
from metadata.models import Interface
for iface in Interface.objects.filter(system_id="8ac86bfe-ec5d-4b2e-b381-d84392dc9f08").select_related("actor"):
    actor = iface.actor.data.get("name", "?") if iface.actor else "?"
    pages = iface.data.get("pages", [])
    sections_all = iface.data.get("sections", [])
    print(f"\n=== {actor} ===")
    for p in pages:
        ptype = p.get("type", {})
        ptype_val = ptype.get("value", ptype) if isinstance(ptype, dict) else ptype
        action = p.get("action", {})
        action_label = action.get("label", action) if isinstance(action, dict) else action
        print(f"  Page: {p['name']} | type={ptype_val} | action={action_label}")
        for sec_ref in p.get("sections", []):
            sec_id = sec_ref.get("value") if isinstance(sec_ref, dict) else sec_ref
            sec = next((s for s in sections_all if s.get("id") == sec_id), None)
            if sec:
                cls = sec.get("class")
                ops = sec.get("operations", {})
                model_name = sec.get("model_name", "")
                print(f"    Sec: {sec['name']} | class={'YES' if cls else 'NO'} | model={model_name} | ops={ops}")
