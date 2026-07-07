import datetime
import difflib
import json
import os
import uuid
from pathlib import Path

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from jwt import encode as jwt_encode

from metadata.models import Classifier, Interface, System


SYSTEM_ID = os.environ.get("T3_SYSTEM_ID", "7d735a07-b6cd-409d-9cc7-f3a07cbec983")
API_BASE = os.environ.get("T3_API_BASE", "http://localhost:8000")
OUT_DIR = Path(os.environ.get("T3_OUT_DIR", "/tmp"))

METHOD_ENTRY = {
    "name": "generate_reading_plan",
    "body": "def generate_reading_plan(self):\n    pass",
}


def stable_uuid(label: str) -> uuid.UUID:
    return uuid.uuid5(uuid.UUID(SYSTEM_ID), label)


def json_ready_interface(interface: Interface | None):
    if interface is None:
        return None
    return {
        "id": str(interface.id),
        "name": interface.name,
        "description": interface.description,
        "system": str(interface.system_id),
        "actor": str(interface.actor_id) if interface.actor_id else None,
        "data": interface.data,
    }


def dump_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def section_attribute(customer: Classifier, name: str) -> dict:
    for attr in customer.data.get("attributes", []):
        if attr.get("name") != name:
            continue
        return {
            "body": attr.get("body"),
            "enum": attr.get("enum"),
            "name": attr.get("name"),
            "type": attr.get("type"),
            "derived": attr.get("derived", False),
            "description": attr.get("description"),
        }
    raise AssertionError(f"Customer.{name} missing")


def auth_token() -> str:
    admin = get_user_model().objects.filter(is_superuser=True).order_by("id").first()
    assert admin is not None, "no superuser found"
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    token = jwt_encode(
        {
            "exp": now + datetime.timedelta(hours=1),
            "nbf": now,
            "iss": "urn:ai4mdestudio",
            "iat": now,
            "uid": admin.id,
        },
        settings.SECRET_KEY,
    )
    return token.decode() if isinstance(token, bytes) else token


system = System.objects.get(id=SYSTEM_ID)
customer = Classifier.objects.get(system=system, data__name="Customer", data__type="class")
member_actor = (
    Classifier.objects.filter(system=system, data__type="actor", data__name="member").first()
)
actor = member_actor or Classifier.objects.filter(system=system, data__type="actor").order_by("id").first()
assert actor is not None, "no actor classifier available for Interface.actor"
if member_actor is None:
    print("[INFO] no member actor classifier exists; using existing actor for Interface.actor FK")
print(f"[INFO] actor id={actor.id} name={actor.data.get('name')}")

interface_id = stable_uuid("t3/member/interface")
page_id = str(stable_uuid("t3/member/page/customers"))
section_id = str(stable_uuid("t3/member/section/customers"))

member_data = {
    "pages": [
        {
            "id": page_id,
            "name": "customers",
            "type": {"label": "Normal", "value": "normal"},
            "action": None,
            "category": None,
            "sections": [{"label": "customers", "value": section_id}],
        }
    ],
    "styling": {
        "radius": 0,
        "textColor": "#000000",
        "accentColor": "#F5F5F4",
        "selectedStyle": "modern",
        "backgroundColor": "#FFFFFF",
    },
    "sections": [
        {
            "id": section_id,
            "name": "customers",
            "text": "Customers",
            "class": str(customer.id),
            "attributes": [
                section_attribute(customer, "name"),
                section_attribute(customer, "email"),
                section_attribute(customer, "reading_plan"),
            ],
            "operations": {"create": False, "delete": False, "update": False},
            "methods": [METHOD_ENTRY],
        }
    ],
    "settings": {"managerAccess": False},
    "categories": [],
}

existing = Interface.objects.filter(name="member", system=system).order_by("id").first()
before = json_ready_interface(existing)
dump_json(OUT_DIR / "t3_member_interface_before.json", before)

if existing is None:
    existing = Interface.objects.create(
        id=interface_id,
        name="member",
        description="member application",
        system=system,
        actor=actor,
        data={"pages": [], "sections": [], "categories": [], "styling": {}},
    )
    print(f"[INFO] created deterministic member Interface skeleton id={existing.id}")
elif existing.id != interface_id:
    print(f"[INFO] existing member Interface id={existing.id}; preserving existing primary key")

body = {
    "id": str(existing.id),
    "name": "member",
    "description": "member application",
    "system": str(system.id),
    "system_id": str(system.id),
    "actor": str(actor.id),
    "data": member_data,
}
endpoint = f"{API_BASE}/api/v1/metadata/interfaces/{existing.id}/"

print(f"[INFO] member interface id={existing.id}")
print(f"[INFO] member page id={page_id}")
print(f"[INFO] member section id={section_id}")
print("[INFO] update endpoint (metadata API uses PUT for interface updates):")
print(endpoint)
print("[INFO] update body:")
print(json.dumps(body, indent=2, sort_keys=True))

response = requests.put(
    endpoint,
    json=body,
    headers={"Authorization": f"Bearer {auth_token()}"},
    timeout=30,
)
print(f"[INFO] update response status={response.status_code}")
print(response.text[:1000])
response.raise_for_status()

after = json_ready_interface(Interface.objects.get(id=existing.id))
dump_json(OUT_DIR / "t3_member_interface_after.json", after)
dump_json(OUT_DIR / "t3_member_interface.json", after)

before_lines = json.dumps(before, indent=2, sort_keys=True).splitlines()
after_lines = json.dumps(after, indent=2, sort_keys=True).splitlines()
print("[INFO] before/after diff:")
print(
    "\n".join(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile="before/member",
            tofile="after/member",
            lineterm="",
        )
    )
)

section = after["data"]["sections"][0]
assert section["class"] == str(customer.id)
assert any(attr["name"] == "reading_plan" for attr in section["attributes"])
assert section["methods"] == [METHOD_ENTRY]
print("[PASS] member interface contains Customer.reading_plan and method name+body")
