import os, sys, django
sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
django.setup()
from metadata.models import Interface, System
from metadata.api.views.interfaces import _get_system_metadata
from prose.api.views.utils import _convert_candidate_to_interface
system_id = "8ac86bfe-ec5d-4b2e-b381-d84392dc9f08"
system = System.objects.get(id=system_id)

for actor_name in ["Applicant", "Document analyst", "Loan Officer", "System"]:
    metadata = _get_system_metadata(system, actor_name=actor_name)
    result = _convert_candidate_to_interface(
        {"styling": {}, "page_overrides": []},
        metadata["classifier_data"],
        composition_groups=metadata.get("composition_groups", {}),
        activity_actions=metadata.get("activity_actions", []),
    )
    print(f"=== {actor_name} ===")
    for sec in result["sections"]:
        pt = sec.get("page_type", "normal")
        print(f"  Section: {sec['name']}, class={sec.get('model_name')}, type={pt}, ops={sec.get('operations')}")
    for p in result["pages"]:
        ptype = p["type"]["value"] if isinstance(p["type"], dict) else p["type"]
        secs = [s["label"] for s in p["sections"]]
        print(f"  Page: {p['name']}, type={ptype}, sections={secs}")
    print()
