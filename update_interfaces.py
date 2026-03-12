import os, sys, django
sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
django.setup()
from metadata.models import Interface, System
from metadata.api.views.interfaces import _get_system_metadata
from prose.api.views.utils import _convert_candidate_to_interface
system_id = "8ac86bfe-ec5d-4b2e-b381-d84392dc9f08"
system = System.objects.get(id=system_id)

for iface in Interface.objects.filter(system_id=system_id):
    actor_name = iface.actor.data.get("name") if iface.actor else None
    if not actor_name:
        print(f"Skipping interface with no actor")
        continue
    
    metadata = _get_system_metadata(system, actor_name=actor_name)
    
    # Use existing styling from the interface if available
    existing_styling = iface.data.get("styling", {})
    
    result = _convert_candidate_to_interface(
        {"styling": existing_styling, "page_overrides": []},
        metadata["classifier_data"],
        composition_groups=metadata.get("composition_groups", {}),
        activity_actions=metadata.get("activity_actions", []),
    )
    
    if result:
        iface.data = result
        iface.save()
        pages = [p["name"] for p in result["pages"]]
        print(f"Updated {actor_name}: {pages}")
    else:
        print(f"No sections for {actor_name}")
