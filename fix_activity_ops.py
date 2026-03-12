"""
Fix activity page operations AND attributes for all actors.
Activity pages should only allow operations appropriate to each use case.
"""
import os, sys, django
sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
django.setup()

from metadata.models import Interface

system_id = "8ac86bfe-ec5d-4b2e-b381-d84392dc9f08"

# Per-actor, per-activity, per-model: which ops and attrs are allowed
ACTIVITY_RULES = {
    "Applicant": {
        "Fill in application": {
            "LoanApplication": {
                "attrs": ["loan_amount"],
                "ops": {"create": True, "update": True, "delete": False},
            },
            "ApplicationNote": None,  # remove (no attrs)
        },
        "Submit extra documents": {
            "Document": {
                "attrs": ["document_type", "file_content", "upload_date"],
                "ops": {"create": True, "update": True, "delete": False},
            },
        },
    },
    "Loan Officer": {
        "Decide on application": {
            "LoanApplication": {
                "attrs": ["status", "requires_additional_documents"],
                "ops": {"create": False, "update": True, "delete": False},
            },
            "ApplicationNote": {
                "attrs": ["comment"],
                "ops": {"create": True, "update": True, "delete": False},
            },
        },
    },
    "Document analyst": {
        "Analyze documents": {
            "Document": {
                "attrs": ["valid"],
                "ops": {"create": False, "update": True, "delete": False},
            },
        },
    },
    "System": {},  # no activity pages
}

for iface in Interface.objects.filter(system_id=system_id).select_related("actor"):
    actor_name = iface.actor.data.get("name", "?") if iface.actor else "?"
    rules = ACTIVITY_RULES.get(actor_name)
    if rules is None:
        print(f"[SKIP] No rules for '{actor_name}'")
        continue

    data = iface.data
    sections = data.get("sections", [])
    changed = False

    for section in sections:
        if section.get("page_type") != "activity":
            continue

        activity_name = section.get("activity_name", "")
        model_name = section.get("model_name", "")

        activity_rules = rules.get(activity_name, {})
        model_rules = activity_rules.get(model_name)

        if model_rules is None and model_name in activity_rules:
            # Explicitly None = remove section
            section["attributes"] = []
            section["operations"] = {"create": False, "update": False, "delete": False}
            section["class"] = None
            print(f"  [{actor_name}] REMOVED: {activity_name} -> {model_name}")
            changed = True
            continue

        if model_rules:
            # Filter attributes
            allowed_attrs = set(model_rules["attrs"])
            section["attributes"] = [
                a for a in section.get("attributes", [])
                if a.get("name") in allowed_attrs
            ]
            # Set correct operations
            section["operations"] = model_rules["ops"]
            actual_attrs = [a["name"] for a in section["attributes"]]
            print(f"  [{actor_name}] {activity_name} -> {model_name}: attrs={actual_attrs} ops={model_rules['ops']}")
            changed = True

    if changed:
        iface.data = data
        iface.save()
        print(f"  [SAVED] {actor_name}")
    else:
        print(f"  [{actor_name}] no activity changes needed")

print("\nDone!")
