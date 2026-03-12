"""
Re-convert all interfaces for the Loan Approval system using the fixed pipeline.
This re-runs _convert_candidate_to_interface with proper duplicate-page removal,
activity_operations support, and attribute filtering.
"""
import os, sys, django, json
sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
django.setup()

from metadata.models import System, Interface
from metadata.api.views.interfaces import _get_system_metadata
from prose.api.views.utils import _convert_candidate_to_interface

system_id = "8ac86bfe-ec5d-4b2e-b381-d84392dc9f08"
system = System.objects.get(id=system_id)

metadata = _get_system_metadata(system)
classifiers = metadata.get("classifier_data", [])
compositions = metadata.get("composition_groups", {})
all_activity_actions = metadata.get("activity_actions", [])

print(f"Classes: {[c['data']['name'] for c in classifiers]}")
print(f"Activity actions: {[(a['name'], a['actor']) for a in all_activity_actions]}")

ACTOR_OVERRIDES = {
    "Applicant": [
        {"class_name": "LoanApplication", "page_name": "My Application", "category": "My Data",
         "operations": ["create", "update"], "attributes": ["loan_amount"],
         "activity_attributes": ["loan_amount"], "activity_operations": ["create", "update"]},
        {"class_name": "Applicant", "page_name": "My Profile", "category": "My Data",
         "operations": ["create", "update"], "attributes": ["name", "email", "credit_score"]},
        {"class_name": "Document", "page_name": "My Documents", "category": "My Data",
         "operations": ["create", "update", "delete"], "attributes": ["document_type", "file_content", "upload_date"],
         "activity_attributes": ["document_type", "file_content", "upload_date"], "activity_operations": ["create", "update"]},
        {"class_name": "ApplicationNote", "page_name": "Notes", "category": "My Data",
         "operations": [], "attributes": ["comment"]},
    ],
    "Loan Officer": [
        {"class_name": "LoanApplication", "page_name": "Application Overview", "category": "Case Management",
         "operations": ["update"], "attributes": ["loan_amount", "requires_additional_documents", "status", "risk"],
         "activity_attributes": ["status", "requires_additional_documents"], "activity_operations": ["update"]},
        {"class_name": "Applicant", "page_name": "Applicant Info", "category": "Case Management",
         "operations": [], "attributes": ["name", "email", "age", "credit_score"]},
        {"class_name": "Document", "page_name": "Documents", "category": "Case Management",
         "operations": [], "attributes": ["document_type", "upload_date", "valid"]},
        {"class_name": "ApplicationNote", "page_name": "Notes", "category": "Case Management",
         "operations": ["create", "update", "delete"], "attributes": ["comment"],
         "activity_attributes": ["comment"], "activity_operations": ["create", "update"]},
    ],
    "Document analyst": [
        {"class_name": "LoanApplication", "page_name": "Application", "category": "Analysis",
         "operations": [], "attributes": ["loan_amount", "status"]},
        {"class_name": "Applicant", "page_name": "Applicant", "category": "Analysis",
         "operations": [], "attributes": ["name", "email"]},
        {"class_name": "Document", "page_name": "Documents", "category": "Analysis",
         "operations": ["update"], "attributes": ["document_type", "file_content", "upload_date", "valid"],
         "activity_attributes": ["valid"], "activity_operations": ["update"]},
        {"class_name": "ApplicationNote", "page_name": "Notes", "category": "Analysis",
         "operations": ["create"], "attributes": ["comment"]},
    ],
    "System": [
        {"class_name": "LoanApplication", "page_name": "LoanApplication", "category": "System Data",
         "operations": ["update"], "attributes": ["loan_amount", "requires_additional_documents", "status", "risk"]},
        {"class_name": "Applicant", "page_name": "Applicant", "category": "System Data",
         "operations": [], "attributes": ["name", "email", "age", "credit_score"]},
        {"class_name": "Document", "page_name": "Document", "category": "System Data",
         "operations": [], "attributes": ["document_type", "file_content", "upload_date", "valid"]},
        {"class_name": "ApplicationNote", "page_name": "Notes", "category": "System Data",
         "operations": [], "attributes": ["comment"]},
    ],
}

for iface in Interface.objects.filter(system=system).select_related("actor"):
    actor_name = iface.actor.data.get("name", "?") if iface.actor else "?"
    overrides = ACTOR_OVERRIDES.get(actor_name)
    if not overrides:
        print(f"[SKIP] {actor_name}")
        continue

    actor_activities = [a for a in all_activity_actions if a.get('actor') == actor_name]
    print(f"\n=== {actor_name} ({len(actor_activities)} activities) ===")

    candidate_data = {
        "style": "Professional",
        "styling": {
            "radius": 8, "textColor": "#1a1a2e", "accentColor": "#0f3460",
            "backgroundColor": "#ffffff", "selectedStyle": "modern", "layoutType": "sidebar",
        },
        "page_overrides": overrides,
    }

    result = _convert_candidate_to_interface(
        candidate_data=candidate_data,
        classifiers=classifiers,
        composition_groups=compositions,
        activity_actions=actor_activities,
    )

    if result is None:
        print(f"  ERROR: conversion returned None")
        continue

    for p in result["pages"]:
        pname = p["name"]
        ptype = p["type"]["value"]
        sec_refs = p.get("sections", [])
        print(f"  PAGE: \"{pname}\" type={ptype} sections={len(sec_refs)}")
        for sref in sec_refs:
            sid = sref["value"]
            sec = next((s for s in result["sections"] if s.get("id") == sid), None)
            if sec:
                mn = sec.get("model_name")
                pt = sec.get("page_type", "normal")
                ops = sec.get("operations", {})
                attrs = [a["name"] for a in sec.get("attributes", [])]
                print(f"    -> [{pt}] {mn}: attrs={attrs} ops={ops}")

    page_names = [p["name"] for p in result["pages"]]
    dupes = [n for n in page_names if page_names.count(n) > 1]
    if dupes:
        print(f"  !! DUPLICATE PAGES: {set(dupes)}")
    else:
        print(f"  OK: No duplicate pages")

    iface.data = result
    iface.save()
    print(f"  [SAVED]")

print("\nDone!")
