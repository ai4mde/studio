from app.section_utils import (
    _finalize_data_section_bindings,
    _infer_section_component,
    _normalize_activity_action_sections,
    _normalize_field_layout,
    _normalize_layout_alias,
)


def test_normalize_layout_alias_maps_common_llm_terms():
    assert _normalize_layout_alias("nav") == "nav-links"
    assert _normalize_layout_alias("navigation") == "nav-links"
    assert _normalize_layout_alias("table") == "table"


def test_infer_section_component_matches_layout():
    assert _infer_section_component({"layout": "table"}) == "DataTable"
    assert _infer_section_component({"layout": "form"}) == "ObjectForm"
    assert _infer_section_component({"layout": "nav-links"}) == "NavBar"


def test_normalize_field_layout_keeps_supported_slots_only():
    section = {
        "layout": "card",
        "component": "ObjectCardGrid",
        "primary_model": "Product",
        "attributes": ["name", "price", "secret"],
        "field_layout": {
            "title": "name",
            "primary": ["price"],
            "columns": ["name"],
            "made_up": ["secret"],
        },
    }

    field_layout = _normalize_field_layout(section)

    assert field_layout["title"] == "name"
    assert field_layout["primary"] == "price"
    assert "columns" not in field_layout
    assert "made_up" not in field_layout


def test_finalize_data_section_bindings_adds_fallback_attributes():
    sections = [{
        "id": "s1",
        "layout": "table",
        "primary_model": "Product",
        "attributes": [],
    }]

    result = _finalize_data_section_bindings(
        sections,
        {"Product": {"name", "price", "status"}},
    )

    assert result[0]["attributes"]
    assert {a["name"] if isinstance(a, dict) else a for a in result[0]["attributes"]} <= {
        "name",
        "price",
        "status",
    }


def test_normalize_activity_action_sections_adds_missing_action():
    pages = [
        {
            "id": "workflow",
            "name": "Workflow",
            "type": {"value": "activity"},
            "sections": [{"value": "action"}],
        }
    ]
    sections = [{"id": "action", "layout": "activity_action"}]

    result = _normalize_activity_action_sections(pages, sections)

    assert any(section.get("layout") == "activity_action" for section in result)
