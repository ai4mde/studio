"""
T0 verification helper - Attribute schema ai_config round-trip.

Run inside the studio-api container through manage.py shell, for example:

    T0_MODE=g0 /usr/src/.venv/bin/python manage.py shell -c \
      "exec(open('/tmp/t0_verify_roundtrip.py').read())"

Modes:
  g0 - before the schema change, prove API serialization strips ai_config.
  g1 - after the schema change, prove API serialization preserves ai_config.
  g2 - after the schema change, simulate UI GET -> PATCH and verify DB retention.
  g3 - after the schema change, run backend regression spot checks.
  frontend_context - print transient browser-test context; do not store as evidence.

The JWT minting code intentionally mirrors docs/evidence/scripts/step1_generate_prototype.py.
"""
import copy
import datetime
import json
import os
import time

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from jwt import encode as jwt_encode

from diagram.models import Diagram
from metadata.models import Classifier, Project


API_BASE = os.environ.get("T0_API_BASE", "http://localhost:8000/api/v1")
PROJECT_NAME = os.environ.get("T0_PROJECT_NAME", "Library")
SYSTEM_NAME = os.environ.get("T0_SYSTEM_NAME", "Library")
MODE = os.environ.get("T0_MODE", "g1").lower()


def emit(label, payload):
    print(f"\n[T0][{label}]")
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def bearer_token():
    admin = get_user_model().objects.filter(is_superuser=True).order_by("id").first()
    assert admin is not None, "no superuser found - create one with manage.py create_admin"
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
    if isinstance(token, bytes):
        token = token.decode()
    return token


def request_json(method, path, **kwargs):
    url = f"{API_BASE}{path}"
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {bearer_token()}"
    last_error = None
    for _ in range(20):
        try:
            response = requests.request(
                method, url, headers=headers, timeout=30, **kwargs
            )
            break
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(1)
    else:
        raise AssertionError(f"{method} {url} failed after retries: {last_error}")

    print(f"[T0][http] {method} {url} -> {response.status_code}")
    print(response.text[:4000])
    response.raise_for_status()
    return response.json()


def locate_system():
    project = Project.objects.filter(name=PROJECT_NAME).order_by("-id").first()
    assert project is not None, f"project {PROJECT_NAME!r} not found"
    system = project.systems.filter(name=SYSTEM_NAME).order_by("-id").first()
    if system is None:
        system = project.systems.order_by("-id").first()
    assert system is not None, f"system not found under project {PROJECT_NAME!r}"
    print(f"[T0][system] project={project.id} system={system.id} name={system.name}")
    return system


def db_classifier(system, name):
    return Classifier.objects.get(system=system, data__name=name, data__type="class")


def db_attr(system, classifier_name, attr_name):
    classifier = db_classifier(system, classifier_name)
    attr = next(
        (
            item
            for item in (classifier.data or {}).get("attributes", [])
            if item.get("name") == attr_name
        ),
        None,
    )
    assert attr is not None, f"{classifier_name}.{attr_name} not found in DB"
    return classifier, attr


def get_system_diagrams(system):
    return request_json("GET", f"/diagram/system/{system.id}/")


def iter_nodes(diagrams):
    for diagram in diagrams:
        for node in diagram.get("nodes", []):
            yield diagram, node


def find_node(diagrams, classifier_name):
    for diagram, node in iter_nodes(diagrams):
        cls = node.get("cls") or {}
        if cls.get("type") == "class" and cls.get("name") == classifier_name:
            return diagram, node
    raise AssertionError(f"node for class {classifier_name!r} not found in API response")


def find_api_attr(diagrams, classifier_name, attr_name):
    _, node = find_node(diagrams, classifier_name)
    attrs = (node.get("cls") or {}).get("attributes", [])
    attr = next((item for item in attrs if item.get("name") == attr_name), None)
    assert attr is not None, f"{classifier_name}.{attr_name} not found in API response"
    return attr


def find_non_ai_attr(diagrams):
    for _, node in iter_nodes(diagrams):
        cls = node.get("cls") or {}
        for attr in cls.get("attributes", []):
            if attr.get("name") not in {"late_risk", "reading_plan"}:
                return cls.get("name"), attr
    return None, None


def raw_db_precheck(system):
    _, late = db_attr(system, "BookLoan", "late_risk")
    _, reading_plan = db_attr(system, "Customer", "reading_plan")
    assert late.get("ai_config"), "DB precheck failed: BookLoan.late_risk lacks ai_config"
    assert reading_plan.get("ai_config"), (
        "DB precheck failed: Customer.reading_plan lacks ai_config"
    )
    emit(
        "db_precheck",
        {
            "BookLoan.late_risk.ai_config.keys": sorted(late["ai_config"].keys()),
            "Customer.reading_plan.ai_config.keys": sorted(
                reading_plan["ai_config"].keys()
            ),
        },
    )


def run_g0(system):
    raw_db_precheck(system)
    diagrams = get_system_diagrams(system)
    late = find_api_attr(diagrams, "BookLoan", "late_risk")
    reading_plan = find_api_attr(diagrams, "Customer", "reading_plan")
    emit(
        "g0_api_attrs",
        {"BookLoan.late_risk": late, "Customer.reading_plan": reading_plan},
    )
    assert "ai_config" not in late, (
        "G0 stop: BookLoan.late_risk.ai_config is already present in typed API response"
    )
    assert "ai_config" not in reading_plan, (
        "G0 stop: Customer.reading_plan.ai_config is already present in typed API response"
    )
    print("[T0][PASS] G0 baseline: DB has ai_config, typed API response strips it")


def run_g1(system):
    raw_db_precheck(system)
    diagrams = get_system_diagrams(system)
    late = find_api_attr(diagrams, "BookLoan", "late_risk")
    reading_plan = find_api_attr(diagrams, "Customer", "reading_plan")
    non_ai_cls, non_ai_attr = find_non_ai_attr(diagrams)
    emit(
        "g1_api_attrs",
        {
            "BookLoan.late_risk": late,
            "Customer.reading_plan": reading_plan,
            "non_ai_observation": {
                "class": non_ai_cls,
                "attribute": non_ai_attr,
                "ai_config_presence": (
                    "missing"
                    if non_ai_attr is not None and "ai_config" not in non_ai_attr
                    else "null"
                    if non_ai_attr is not None and non_ai_attr.get("ai_config") is None
                    else "other"
                ),
            },
        },
    )
    assert late.get("ai_config", {}).get("trigger", {}).get("type") == "post_save", late
    assert (
        reading_plan.get("ai_config", {}).get("trigger", {}).get("type")
        == "user_action"
    ), reading_plan
    assert non_ai_attr is not None, "no non-AI attribute available for serialization check"
    print("[T0][PASS] G1 serialization: AI attrs preserved; non-AI attr serialized")


def run_g2(system):
    diagrams = get_system_diagrams(system)
    diagram, node = find_node(diagrams, "BookLoan")
    attrs_before = copy.deepcopy((node.get("cls") or {}).get("attributes", []))
    late_before = next(item for item in attrs_before if item.get("name") == "late_risk")
    ai_before = copy.deepcopy(late_before.get("ai_config"))
    assert ai_before, "G2 precheck failed: API response lacks late_risk.ai_config"

    description = f"T0 roundtrip description {int(time.time())}"
    attrs_after = copy.deepcopy(attrs_before)
    for attr in attrs_after:
        if attr.get("name") == "late_risk":
            attr["description"] = description
            break

    patch_body = {"cls": {"attributes": attrs_after}}
    emit(
        "g2_patch_input",
        {
            "diagram_id": diagram.get("id"),
            "node_id": node.get("id"),
            "description": description,
            "late_risk.ai_config": ai_before,
        },
    )
    request_json(
        "PATCH",
        f"/diagram/{diagram['id']}/node/{node['id']}/",
        json=patch_body,
    )

    classifier, late_db = db_attr(system, "BookLoan", "late_risk")
    emit(
        "g2_db_after",
        {
            "classifier_id": str(classifier.id),
            "late_risk.description": late_db.get("description"),
            "late_risk.ai_config": late_db.get("ai_config"),
        },
    )
    assert late_db.get("ai_config") == ai_before, {
        "before": ai_before,
        "after": late_db.get("ai_config"),
    }
    assert late_db.get("description") == description, late_db
    print("[T0][PASS] G2 roundtrip: description updated and ai_config retained")


def run_g3(system):
    classes = request_json("GET", f"/metadata/systems/{system.id}/classes/")
    classifiers = classes.get("classifiers")
    assert isinstance(classifiers, list) and classifiers, classes
    bookloan = next(
        (
            item
            for item in classifiers
            if (item.get("data") or {}).get("name") == "BookLoan"
        ),
        None,
    )
    assert bookloan is not None, "BookLoan missing from classes endpoint"

    exported = request_json("GET", f"/metadata/projects/export/{system.project_id}/")
    export_late = None
    for exported_system in exported.get("systems", []):
        if str(exported_system.get("id")) != str(system.id):
            continue
        for classifier in exported_system.get("classifiers", []):
            data = classifier.get("data") or {}
            if data.get("name") != "BookLoan":
                continue
            export_late = next(
                (
                    attr
                    for attr in data.get("attributes", [])
                    if attr.get("name") == "late_risk"
                ),
                None,
            )
            break
    assert export_late is not None, "BookLoan.late_risk missing from project export"
    assert export_late.get("ai_config", {}).get("trigger", {}).get("type") == "post_save", (
        export_late
    )
    emit(
        "g3_backend",
        {
            "classes_count": len(classifiers),
            "classes_bookloan_keys": sorted((bookloan.get("data") or {}).keys()),
            "export_late_risk": export_late,
        },
    )
    print("[T0][PASS] G3 backend: classes endpoint and project export OK")


def run_frontend_context(system):
    diagram = Diagram.objects.filter(system=system, type="classes").order_by("id").first()
    assert diagram is not None, "class diagram not found"
    print(
        "T0_FRONTEND_CONTEXT="
        + json.dumps(
            {
                "token": bearer_token(),
                "system_id": str(system.id),
                "diagram_id": str(diagram.id),
            },
            sort_keys=True,
        )
    )


system = locate_system()
if MODE == "g0":
    run_g0(system)
elif MODE == "g1":
    run_g1(system)
elif MODE == "g2":
    run_g2(system)
elif MODE == "g3":
    run_g3(system)
elif MODE == "frontend_context":
    run_frontend_context(system)
else:
    raise AssertionError(
        f"unknown T0_MODE={MODE!r}; expected g0, g1, g2, g3, or frontend_context"
    )
