"""
Test that the interface generation pipeline generically respects
operations + attributes from the LLM page_overrides, including activity pages.
"""
import os, sys, django, json, re
from uuid import uuid4

sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
django.setup()

from prose.api.views.utils import _convert_candidate_to_interface

mock_classes = [
    {
        "id": str(uuid4()),
        "data": {
            "name": "Order",
            "type": "class",
            "attributes": [
                {"name": "total", "type": "float", "derived": False},
                {"name": "status", "type": "enum", "derived": False},
                {"name": "notes", "type": "str", "derived": False},
            ],
            "methods": [],
        },
    },
    {
        "id": str(uuid4()),
        "data": {
            "name": "Product",
            "type": "class",
            "attributes": [
                {"name": "name", "type": "str", "derived": False},
                {"name": "price", "type": "float", "derived": False},
                {"name": "stock", "type": "int", "derived": False},
            ],
            "methods": [],
        },
    },
]

mock_relationships = []

mock_activity_actions = [
    {"name": "Place order", "id": str(uuid4()), "is_automatic": False,
     "input_classes": ["Order"], "output_classes": []},
    {"name": "Review order", "id": str(uuid4()), "is_automatic": False,
     "input_classes": ["Order"], "output_classes": []},
]

violations = []

# TEST 1: Customer — can create/update Order (no delete, no status), Product read-only
print("=" * 60)
print("TEST 1: Customer actor")
print("=" * 60)

customer_candidate = {
    "style": "Modern",
    "styling": {"radius": 8, "textColor": "#333", "accentColor": "#007bff",
                "backgroundColor": "#fff", "selectedStyle": "modern", "layoutType": "sidebar"},
    "page_overrides": [
        {"class_name": "Order", "page_name": "My Orders", "category": "Shopping",
         "operations": ["create", "update"], "attributes": ["total", "notes"],
         "activity_attributes": ["total", "notes"], "activity_operations": ["create", "update"]},
        {"class_name": "Product", "page_name": "Products", "category": "Shopping",
         "operations": [], "attributes": ["name", "price"]},
    ],
}

r = _convert_candidate_to_interface(
    candidate_data=customer_candidate, classifiers=mock_classes,
    activity_actions=mock_activity_actions)

for s in r["sections"]:
    mn, pt = s.get("model_name",""), s.get("page_type","")
    ops = s.get("operations",{})
    attrs = [a["name"] for a in s.get("attributes",[])]
    print(f"  [{pt or 'normal'}] {mn}: attrs={attrs} ops={ops}")

    if mn == "Order":
        if ops.get("delete"):
            violations.append(f"Customer Order {pt}: delete=True (should be False)")
        if "status" in attrs:
            violations.append(f"Customer Order {pt}: has 'status' (should be excluded)")

    if mn == "Product" and pt != "activity":
        if any(ops.get(o) for o in ("create","update","delete")):
            violations.append(f"Customer Product: should be read-only, got {ops}")

# TEST 2: Manager — update-only Order, activity shows only status
print("\n" + "=" * 60)
print("TEST 2: Manager actor")
print("=" * 60)

manager_candidate = {
    "style": "Pro",
    "styling": {"radius": 4, "textColor": "#222", "accentColor": "#28a745",
                "backgroundColor": "#f8f9fa", "selectedStyle": "basic", "layoutType": "topnav"},
    "page_overrides": [
        {"class_name": "Order", "page_name": "Order Review", "category": "Mgmt",
         "operations": ["update"], "attributes": ["total", "status", "notes"],
         "activity_attributes": ["status"], "activity_operations": ["update"]},
        {"class_name": "Product", "page_name": "Catalog", "category": "Mgmt",
         "operations": [], "attributes": ["name", "price", "stock"]},
    ],
}

r2 = _convert_candidate_to_interface(
    candidate_data=manager_candidate, classifiers=mock_classes,
    activity_actions=mock_activity_actions)

for s in r2["sections"]:
    mn, pt = s.get("model_name",""), s.get("page_type","")
    ops = s.get("operations",{})
    attrs = [a["name"] for a in s.get("attributes",[])]
    print(f"  [{pt or 'normal'}] {mn}: attrs={attrs} ops={ops}")

    if mn == "Order":
        if ops.get("create"):
            violations.append(f"Manager Order {pt}: create=True (should be False)")
        if ops.get("delete"):
            violations.append(f"Manager Order {pt}: delete=True (should be False)")
        if pt == "activity" and attrs != ["status"]:
            violations.append(f"Manager Order activity: attrs={attrs} (should be ['status'])")
    if mn == "Product" and pt != "activity":
        if any(ops.get(o) for o in ("create","update","delete")):
            violations.append(f"Manager Product: should be read-only")

print("\n" + "=" * 60)
if violations:
    print(f"FAILED — {len(violations)} violation(s):")
    for v in violations:
        print(f"  !! {v}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED — pipeline is generic!")
    sys.exit(0)
