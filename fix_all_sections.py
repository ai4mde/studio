"""
Comprehensive fix: ALL sections (normal + activity) for all actors.
Sets both attributes AND operations correctly in one pass.
"""
import os, sys, django, json
sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
django.setup()

from metadata.models import Interface

system_id = "8ac86bfe-ec5d-4b2e-b381-d84392dc9f08"

# Complete rules: for each actor, for each (page_type, model_name) or (activity_name, model_name)
RULES = {
    "Applicant": {
        "normal": {
            "LoanApplication":  {"attrs": ["loan_amount"], "ops": {"create": True, "update": True, "delete": False}, "name": "My Application"},
            "Applicant":        {"attrs": ["name", "email", "credit_score"], "ops": {"create": True, "update": True, "delete": False}, "name": "My Profile"},
            "Document":         {"attrs": ["document_type", "file_content", "upload_date"], "ops": {"create": True, "update": True, "delete": True}, "name": "My Documents"},
            "ApplicationNote":  {"attrs": ["comment"], "ops": {"create": False, "update": False, "delete": False}, "name": "Notes"},
        },
        "activity": {
            ("Submit extra documents", "Document"):       {"attrs": ["document_type", "file_content", "upload_date"], "ops": {"create": True, "update": True, "delete": False}},
            ("Fill in application", "LoanApplication"):   {"attrs": ["loan_amount"], "ops": {"create": True, "update": True, "delete": False}},
            ("Fill in application", "ApplicationNote"):   {"attrs": [], "ops": {"create": False, "update": False, "delete": False}},  # remove
        },
    },
    "Loan Officer": {
        "normal": {
            "LoanApplication":  {"attrs": ["loan_amount", "requires_additional_documents", "status", "risk"], "ops": {"create": False, "update": True, "delete": False}, "name": "Application Overview"},
            "Applicant":        {"attrs": ["name", "email", "age", "credit_score"], "ops": {"create": False, "update": False, "delete": False}, "name": "Applicant Info"},
            "Document":         {"attrs": ["document_type", "upload_date", "valid"], "ops": {"create": False, "update": False, "delete": False}, "name": "Documents"},
            "ApplicationNote":  {"attrs": ["comment"], "ops": {"create": True, "update": True, "delete": True}, "name": "Notes"},
        },
        "activity": {
            ("Decide on application", "LoanApplication"):   {"attrs": ["status", "requires_additional_documents"], "ops": {"create": False, "update": True, "delete": False}},
            ("Decide on application", "ApplicationNote"):   {"attrs": ["comment"], "ops": {"create": True, "update": True, "delete": False}},
        },
    },
    "Document analyst": {
        "normal": {
            "LoanApplication":  {"attrs": ["loan_amount", "status"], "ops": {"create": False, "update": False, "delete": False}, "name": "Application"},
            "Applicant":        {"attrs": ["name", "email"], "ops": {"create": False, "update": False, "delete": False}, "name": "Applicant"},
            "Document":         {"attrs": ["document_type", "file_content", "upload_date", "valid"], "ops": {"create": False, "update": True, "delete": False}, "name": "Documents"},
            "ApplicationNote":  {"attrs": ["comment"], "ops": {"create": True, "update": False, "delete": False}, "name": "Notes"},
        },
        "activity": {
            ("Analyze documents", "Document"):   {"attrs": ["valid"], "ops": {"create": False, "update": True, "delete": False}},
        },
    },
    "System": {
        "normal": {
            "LoanApplication":  {"attrs": ["loan_amount", "requires_additional_documents", "status", "risk"], "ops": {"create": False, "update": True, "delete": False}, "name": "LoanApplication"},
            "Applicant":        {"attrs": ["name", "email", "age", "credit_score"], "ops": {"create": False, "update": False, "delete": False}, "name": "Applicant"},
            "Document":         {"attrs": ["document_type", "file_content", "upload_date", "valid"], "ops": {"create": False, "update": False, "delete": False}, "name": "Document"},
            "ApplicationNote":  {"attrs": ["comment"], "ops": {"create": False, "update": False, "delete": False}, "name": "Notes"},
        },
        "activity": {},
    },
}

for iface in Interface.objects.filter(system_id=system_id).select_related("actor"):
    actor_name = iface.actor.data.get("name", "?") if iface.actor else "?"
    actor_rules = RULES.get(actor_name)
    if not actor_rules:
        print(f"[SKIP] {actor_name}")
        continue

    data = iface.data
    sections = data.get("sections", [])

    for section in sections:
        model_name = section.get("model_name", "")
        page_type = section.get("page_type", "")

        if page_type == "activity":
            activity_name = section.get("activity_name", "")
            key = (activity_name, model_name)
            rule = actor_rules.get("activity", {}).get(key)
        else:
            rule = actor_rules.get("normal", {}).get(model_name)

        if not rule:
            continue

        # Filter attributes
        allowed = set(rule["attrs"])
        section["attributes"] = [
            a for a in section.get("attributes", [])
            if a.get("name") in allowed
        ]
        # Set operations
        section["operations"] = rule["ops"]
        # Set name if provided
        if "name" in rule:
            section["name"] = rule["name"]

        prefix = f"[{page_type or 'normal'}]" if page_type == "activity" else "[normal]"
        actual_attrs = [a["name"] for a in section["attributes"]]
        print(f"  {actor_name} {prefix} {model_name}: attrs={actual_attrs} ops={rule['ops']}")

    iface.data = data
    iface.save()
    print(f"  [SAVED] {actor_name}\n")

print("Done! All interfaces comprehensively fixed.")
