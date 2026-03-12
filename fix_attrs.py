"""
Fix attribute access per actor for the Loan Approval system.
Based on use case analysis:
- Applicant: Fill in application -> loan_amount; Submit extra documents -> document
- Loan Officer: Decide on application -> status, risk; Views documents read-only
- Document analyst: Analyze documents -> valid; Views loan applications read-only
- System: automatic tasks only, no form interaction
"""
import os, sys, django
sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
django.setup()

from metadata.models import Interface

system_id = "8ac86bfe-ec5d-4b2e-b381-d84392dc9f08"

# Define per-actor attribute access rules
ACTOR_RULES = {
    "Applicant": {
        "normal_pages": {
            "LoanApplication": {
                "page_name": "My Application",
                "attributes": ["loan_amount"],  # Applicant sets loan amount, NOT status/risk
                "operations": {"create": True, "update": True, "delete": False},
            },
            "Applicant": {
                "page_name": "My Profile",
                "attributes": ["name", "email", "credit_score"],
                "operations": {"create": True, "update": True, "delete": False},
            },
            "Document": {
                "page_name": "My Documents",
                "attributes": ["document_type", "file_content", "upload_date"],  # NOT 'valid' (analyst sets it)
                "operations": {"create": True, "update": True, "delete": True},
            },
            "ApplicationNote": {
                "page_name": "Notes",
                "attributes": ["comment"],
                "operations": {"create": False, "update": False, "delete": False},  # read-only
            },
        },
        "activity_pages": {
            "Fill in application": {
                "LoanApplication": ["loan_amount"],  # Only fill in loan amount
                "ApplicationNote": None,  # remove - applicant doesn't write notes
            },
            "Submit extra documents": {
                "Document": ["document_type", "file_content", "upload_date"],  # NOT 'valid'
            },
        },
    },
    "Loan Officer": {
        "normal_pages": {
            "LoanApplication": {
                "page_name": "Application Overview",
                "attributes": ["loan_amount", "requires_additional_documents", "status", "risk"],  # can see all
                "operations": {"create": False, "update": True, "delete": False},  # update only
            },
            "Applicant": {
                "page_name": "Applicant Info",
                "attributes": ["name", "email", "age", "credit_score"],
                "operations": {"create": False, "update": False, "delete": False},  # read-only
            },
            "Document": {
                "page_name": "Documents",
                "attributes": ["document_type", "upload_date", "valid"],
                "operations": {"create": False, "update": False, "delete": False},  # read-only
            },
            "ApplicationNote": {
                "page_name": "Notes",
                "attributes": ["comment"],
                "operations": {"create": True, "update": True, "delete": True},
            },
        },
        "activity_pages": {
            "Decide on application": {
                "LoanApplication": ["status", "requires_additional_documents"],  # Officer decides status + whether more docs needed
                "ApplicationNote": ["comment"],  # Can add decision notes
            },
        },
    },
    "Document analyst": {
        "normal_pages": {
            "LoanApplication": {
                "page_name": "Application",
                "attributes": ["loan_amount", "status"],
                "operations": {"create": False, "update": False, "delete": False},  # read-only
            },
            "Applicant": {
                "page_name": "Applicant",
                "attributes": ["name", "email"],
                "operations": {"create": False, "update": False, "delete": False},  # read-only
            },
            "Document": {
                "page_name": "Documents",
                "attributes": ["document_type", "file_content", "upload_date", "valid"],
                "operations": {"create": False, "update": True, "delete": False},  # can update validity
            },
            "ApplicationNote": {
                "page_name": "Notes",
                "attributes": ["comment"],
                "operations": {"create": True, "update": False, "delete": False},  # can add notes
            },
        },
        "activity_pages": {
            "Analyze documents": {
                "Document": ["valid"],  # Analyst marks validity
            },
        },
    },
    "System": {
        "normal_pages": {
            "LoanApplication": {
                "page_name": "LoanApplication",
                "attributes": ["loan_amount", "requires_additional_documents", "status", "risk"],
                "operations": {"create": False, "update": True, "delete": False},
            },
            "Applicant": {
                "page_name": "Applicant",
                "attributes": ["name", "email", "age", "credit_score"],
                "operations": {"create": False, "update": False, "delete": False},
            },
            "Document": {
                "page_name": "Document",
                "attributes": ["document_type", "file_content", "upload_date", "valid"],
                "operations": {"create": False, "update": False, "delete": False},
            },
            "ApplicationNote": {
                "page_name": "Notes",
                "attributes": ["comment"],
                "operations": {"create": False, "update": False, "delete": False},
            },
        },
        "activity_pages": {},  # System actions are automatic
    },
}

for iface in Interface.objects.filter(system_id=system_id).select_related("actor"):
    actor_name = iface.actor.data.get("name", "?") if iface.actor else "?"
    rules = ACTOR_RULES.get(actor_name)
    if not rules:
        print(f"[SKIP] No rules for actor '{actor_name}'")
        continue

    data = iface.data
    sections = data.get("sections", [])
    pages = data.get("pages", [])

    # Update normal page sections
    for section in sections:
        model_name = section.get("model_name", "")
        page_type = section.get("page_type", "")

        if page_type == "activity":
            # Find which activity page this belongs to
            activity_name = section.get("activity_name", "")
            activity_rules = rules.get("activity_pages", {}).get(activity_name, {})
            model_attrs_filter = activity_rules.get(model_name)

            if model_attrs_filter is None and model_name in activity_rules:
                # Explicitly set to None means remove this section
                # We'll handle removal by setting class to None
                section["class"] = None
                section["attributes"] = []
                section["operations"] = {"create": False, "update": False, "delete": False}
                print(f"  [{actor_name}] Removed activity section '{activity_name}' -> {model_name}")
                continue

            if model_attrs_filter:
                # Filter attributes
                section["attributes"] = [
                    a for a in section.get("attributes", [])
                    if a.get("name") in model_attrs_filter
                ]
                print(f"  [{actor_name}] Activity '{activity_name}' -> {model_name}: {model_attrs_filter}")
        else:
            # Normal page section
            normal_rules = rules.get("normal_pages", {}).get(model_name)
            if normal_rules:
                attrs_filter = normal_rules.get("attributes")
                if attrs_filter:
                    section["attributes"] = [
                        a for a in section.get("attributes", [])
                        if a.get("name") in attrs_filter
                    ]
                section["operations"] = normal_rules["operations"]
                section["name"] = normal_rules.get("page_name", section["name"])
                print(f"  [{actor_name}] Normal '{model_name}': attrs={attrs_filter}, ops={normal_rules['operations']}")

    # Update page names to match section names
    for page in pages:
        page_sections = page.get("sections", [])
        if page_sections:
            sec_id = page_sections[0].get("value")
            sec = next((s for s in sections if s.get("id") == sec_id), None)
            if sec and sec.get("name"):
                page["name"] = sec["name"]

    # Remove activity sections that were nullified (class set to None for activity pages)
    # These won't generate any views anyway since class is None

    iface.data = data
    iface.save()
    print(f"[SAVED] {actor_name}")

print("\nDone! All interfaces updated with per-actor attribute access control.")
