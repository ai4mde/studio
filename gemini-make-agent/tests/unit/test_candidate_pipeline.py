import json
from unittest.mock import MagicMock

from app.candidate_generation import validate_and_save_candidate
from app.metadata_context import get_interface_full_context
from app.tools import render_candidate_preview


IFACE = {
    "id": "iface-1",
    "name": "Shop Interface",
    "description": "Customer shop",
    "system": "sys-1",
    "actor": "actor-1",
    "data": {"sections": [], "pages": [], "candidates": []},
}

CLASSIFIERS = [
    {
        "id": "actor-1",
        "data": {"name": "Customer", "type": "actor", "attributes": []},
    },
    {
        "id": "c1",
        "data": {
            "name": "Product",
            "type": "class",
            "attributes": [{"name": "name"}, {"name": "price"}, {"name": "status"}],
        },
    },
    {
        "id": "c2",
        "data": {
            "name": "Seller",
            "type": "class",
            "attributes": [{"name": "business_name"}, {"name": "email"}],
        },
    },
]

PAGES = [{"id": "products", "name": "Products", "sections": [{"value": "s1"}]}]

SECTIONS = [
    {
        "id": "s1",
        "name": "Products",
        "primary_model": "Product",
        "class": "Product",
        "layout": "card",
        "col_span": 12,
        "position": "main",
        "attributes": ["name", "price"],
        "field_layout": {"title": "name", "primary": ["price"]},
        "operations": {"create": False, "update": False, "delete": False},
        "style": {"color": "blue", "display_mode": "grid"},
    }
]


def _response(payload, ok=True):
    response = MagicMock()
    response.ok = ok
    response.status_code = 200 if ok else 500
    response.text = ""
    response.json.return_value = payload
    response.raise_for_status = MagicMock()
    return response


def _mock_get(url, **kwargs):
    if "/interfaces/" in url:
        return _response(IFACE)
    if "/classifiers/" in url:
        return _response(CLASSIFIERS)
    if "/relations/" in url:
        return _response([])
    if "/systems/export/" in url:
        return _response([{"classifiers": CLASSIFIERS, "relations": [], "diagrams": []}])
    if "/systems/" in url:
        return _response({"id": "sys-1", "name": "Shop"})
    return _response({})


def _run_save(monkeypatch, sections=None, pages=None, tokens=None, styling=None):
    put_calls = []
    monkeypatch.setattr("app.candidate_generation.requests.get", _mock_get)
    monkeypatch.setattr(
        "app.candidate_generation.requests.put",
        lambda *_, **kwargs: put_calls.append(kwargs["json"]) or _response({}),
    )
    result = validate_and_save_candidate(
        interface_id="iface-1",
        candidate_index=0,
        name="Candidate A",
        description="layout",
        pages=json.dumps(pages or PAGES),
        sections=json.dumps(sections or SECTIONS),
        tokens=json.dumps(tokens or {}),
        styling=json.dumps(styling or {}),
    )
    return result, put_calls


def test_get_interface_full_context_embeds_attribute_reference(monkeypatch):
    monkeypatch.setattr("app.metadata_context.requests.get", _mock_get)

    result = json.loads(get_interface_full_context("iface-1"))

    assert result["ATTRIBUTE_REFERENCE"]["models"]["Product"] == [
        "name",
        "price",
        "status",
    ]
    assert result["interface"]["actor_name"] == "Customer"


def test_validate_and_save_candidate_persists_candidate(monkeypatch):
    result, put_calls = _run_save(monkeypatch)

    assert result.startswith("OK:")
    candidate = put_calls[0]["data"]["candidates"][0]
    assert candidate["id"] == "c0"
    assert candidate["name"] == "Candidate A"
    assert candidate["pages"][0]["sections"] == [{"value": "s1"}]


def test_validate_and_save_candidate_strips_unknown_attributes(monkeypatch):
    sections = [{**SECTIONS[0], "attributes": ["name", "ghost"]}]

    result, put_calls = _run_save(monkeypatch, sections=sections)

    assert result.startswith("OK:")
    attrs = put_calls[0]["data"]["candidates"][0]["sections"][0]["attributes"]
    names = [a.get("name") if isinstance(a, dict) else a for a in attrs]
    assert "name" in names
    assert "ghost" not in names


def test_validate_and_save_candidate_normalizes_invalid_layout_and_style(monkeypatch):
    sections = [{**SECTIONS[0], "layout": "flyingpig", "style": {"color": "rainbow"}}]

    result, put_calls = _run_save(monkeypatch, sections=sections)

    assert result.startswith("OK:")
    section = put_calls[0]["data"]["candidates"][0]["sections"][0]
    assert section["layout"] == "card"
    assert section["style"]["color"] == "accent"


def test_validate_and_save_candidate_preserves_fine_grained_tokens(monkeypatch):
    result, put_calls = _run_save(
        monkeypatch,
        tokens={
            "region.header.bg_hex": "#2563eb",
            "input.bg_hex": "#16a34a",
            "button.primary.bg_hex": "#db2777",
        },
    )

    assert result.startswith("OK:")
    candidate = put_calls[0]["data"]["candidates"][0]
    assert candidate["tokens"]["region.header.bg_hex"] == "#2563eb"
    assert candidate["tokens"]["input.bg_hex"] == "#16a34a"
    assert candidate["tokens"]["button.primary.bg_hex"] == "#db2777"


def test_render_candidate_preview_success(monkeypatch):
    monkeypatch.setattr("app.service_clients.requests.post", lambda *_, **__: _response({}))

    assert render_candidate_preview("iface-1", 2).startswith("OK:")
