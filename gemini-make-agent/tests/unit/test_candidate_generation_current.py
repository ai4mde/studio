import json
from unittest.mock import MagicMock

from app import candidate_generation as cg


def test_candidate_list_parser_prefers_outer_candidates_container():
    raw = 'noise {"id":"inner"} {"candidates":[{"name":"A"},{"name":"B"},{"name":"C"}]}'

    candidates = cg._candidate_list_from_llm_response(raw)

    assert [c["name"] for c in candidates] == ["A", "B", "C"]


def test_tokens_from_llm_schema_prefers_llm_tokens_without_prompt_rewrite():
    candidate = {
        "styling": {"accentColor": "#111827", "textSize": "lg"},
        "tokens": {
            "region.header.bg_hex": "#000000",
            "input.bg_hex": "#ffffff",
            "button.primary.bg_hex": "#ffffff",
        },
    }

    tokens = cg._tokens_from_llm_schema(
        candidate,
        {},
        "header blue search bar green button pink",
        2,
    )

    assert tokens["region.header.bg_hex"] == "#000000"
    assert tokens["input.bg_hex"] == "#ffffff"
    assert tokens["button.primary.bg_hex"] == "#ffffff"
    assert tokens["design.variant_index"] == "2"
    assert tokens["typography.body.size"] == "18px"


def test_merge_llm_candidate_preserves_data_bindings_and_role_locked_layouts():
    base_pages = [{"id": "p1", "layout": {"value": "vertical"}}]
    base_sections = [
        {
            "id": "form",
            "role": "object_form",
            "layout": "form",
            "component": "ObjectForm",
            "primary_model": "Product",
            "attributes": ["name"],
        },
        {
            "id": "cards",
            "role": "object_collection",
            "layout": "card",
            "component": "ObjectCardGrid",
            "primary_model": "Product",
            "attributes": ["name", "price"],
        },
    ]
    llm_candidate = {
        "pages": [{"id": "p1", "layout": {"main_width": "wide"}}],
        "sections": [
            {"id": "form", "layout": "table", "component": "DataTable"},
            {"id": "cards", "layout": "table", "component": "DataTable"},
        ],
    }

    pages, sections = cg._merge_llm_candidate(base_pages, base_sections, llm_candidate)

    by_id = {s["id"]: s for s in sections}
    assert pages[0]["layout"]["main_width"] == "wide"
    assert by_id["form"]["layout"] == "form"
    assert by_id["form"]["attributes"] == ["name"]
    assert by_id["cards"]["layout"] == "table"
    assert by_id["cards"]["attributes"] == ["name", "price"]


def test_generate_candidate_set_saves_three_llm_candidates(monkeypatch):
    iface = {
        "id": "iface-1",
        "name": "Shop",
        "description": "",
        "system": "sys-1",
        "actor": "actor-1",
        "data": {
            "pages": [{"id": "products", "name": "Products", "sections": [{"value": "s1"}]}],
            "sections": [
                {
                    "id": "s1",
                    "role": "object_collection",
                    "layout": "card",
                    "component": "ObjectCardGrid",
                    "primary_model": "Product",
                    "attributes": ["name"],
                    "style": {},
                }
            ],
            "tokens": {},
            "styling": {},
        },
    }
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = iface
    monkeypatch.setattr(cg.requests, "get", lambda *_, **__: response)
    monkeypatch.setattr(
        cg,
        "_llm_generate_3_candidates",
        lambda *_: [
            {
                "name": f"Candidate {i}",
                "pages": [{"id": "products", "layout": {"main_width": "wide"}}],
                "sections": [{"id": "s1", "style": {"density": "compact"}}],
                "tokens": {"region.header.bg_hex": "#2563eb"},
                "styling": {"accentColor": "#db2777"},
            }
            for i in range(3)
        ],
    )
    save_calls = []
    monkeypatch.setattr(
        cg,
        "validate_and_save_candidate",
        lambda **kwargs: save_calls.append(kwargs) or f"OK: candidate {kwargs['candidate_index']} saved",
    )
    render_calls = []
    monkeypatch.setattr(cg, "render_candidate_preview_func", lambda iid, idx: render_calls.append((iid, idx)))

    result = cg.generate_candidate_set("iface-1", "header blue")

    assert result.startswith("OK: generated and saved 3 candidates")
    assert [c["candidate_index"] for c in save_calls] == [0, 1, 2]
    assert render_calls == [("iface-1", 0), ("iface-1", 1), ("iface-1", 2)]
    first_tokens = json.loads(save_calls[0]["tokens"])
    assert first_tokens["region.header.bg_hex"] == "#2563eb"
