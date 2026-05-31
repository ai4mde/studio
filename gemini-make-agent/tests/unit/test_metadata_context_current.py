import json
from unittest.mock import MagicMock

from app import metadata_context as mc


def _resp(payload, ok=True):
    response = MagicMock()
    response.ok = ok
    response.json.return_value = payload
    response.raise_for_status = MagicMock()
    return response


def test_build_known_attrs_from_system_context(monkeypatch):
    monkeypatch.setattr(
        mc,
        "_fetch_system_context_data",
        lambda _system_id: {
            "classifiers": [
                {
                    "id": "model_product",
                    "data": {
                        "name": "Product",
                        "attributes": [{"name": "name"}, {"name": "price"}],
                    },
                }
            ]
        },
    )

    assert mc._build_known_attrs("sys-1") == {"Product": {"name", "price"}}


def test_get_interface_full_context_contains_attribute_reference(monkeypatch):
    def fake_get(url, **kwargs):
        if "/interfaces/" in url:
            return _resp({
                "id": "iface-1",
                "name": "Shop",
                "system": "sys-1",
                "actor": "actor-1",
                "data": {"pages": [], "sections": [], "styling": {}},
            })
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(mc.requests, "get", fake_get)
    monkeypatch.setattr(
        mc,
        "_fetch_system_context_data",
        lambda _system_id: {
            "classifiers": [
                {
                    "id": "actor-1",
                    "data": {"name": "Customer", "type": "actor", "attributes": []},
                },
                {
                    "id": "model_product",
                    "data": {
                        "name": "Product",
                        "type": "class",
                        "attributes": [{"name": "name"}, {"name": "price"}],
                    },
                },
            ],
            "workflow_plan": [],
            "usecase_navigation": {},
        },
    )
    monkeypatch.setattr(mc, "_workflow_plan", lambda *_: [])
    monkeypatch.setattr(mc, "_build_usecase_navigation", lambda *_: {})

    data = json.loads(mc.get_interface_full_context("iface-1"))

    assert data["ATTRIBUTE_REFERENCE"]["models"]["Product"] == ["name", "price"]
    assert data["interface"]["actor_name"] == "Customer"
