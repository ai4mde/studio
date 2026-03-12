import os, sys, django, json
sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
django.setup()
from metadata.models import Interface
for iface in Interface.objects.filter(system_id="8ac86bfe-ec5d-4b2e-b381-d84392dc9f08").select_related("actor"):
    actor = iface.actor.data.get("name", "?")
    if actor != "Applicant":
        continue
    pages = iface.data.get("pages", [])
    sections = iface.data.get("sections", [])
    print(f"=== {actor}: {len(pages)} pages, {len(sections)} sections ===")
    for p in pages:
        ptype = p.get("type", {})
        pname = p.get("name", "")
        sec_refs = p.get("sections", [])
        sec_ids = [s.get("value") for s in sec_refs]
        print(f'  PAGE: "{pname}" type={ptype} sections={len(sec_refs)}')
        for sid in sec_ids:
            sec = next((s for s in sections if s.get("id") == sid), None)
            if sec:
                mn = sec.get("model_name")
                pt = sec.get("page_type", "normal")
                cl = sec.get("class")
                ops = sec.get("operations", {})
                print(f"    -> model={mn}, page_type={pt}, class={'SET' if cl else 'None'}, ops={ops}")
