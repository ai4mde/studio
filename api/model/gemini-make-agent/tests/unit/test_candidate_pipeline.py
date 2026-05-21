"""Unit tests for candidate pipeline tools: get_interface_full_context,
validate_and_save_candidate, render_candidate_preview."""
import json
from unittest.mock import patch, MagicMock, call
import pytest
from app.tools import (
    get_interface_full_context,
    validate_and_save_candidate,
    render_candidate_preview,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

IFACE = {
    "id": "iface-1",
    "name": "Shop Interface",
    "description": "Customer shop",
    "system": "sys-1",
    "actor": "actor-1",
    "data": {"sections": [], "pages": [], "candidates": []},
}

CLASSIFIERS = [
    {"id": "c1", "data": {"name": "Product", "attributes": [
        {"name": "name"}, {"name": "price"}, {"name": "status"},
    ]}},
    {"id": "c2", "data": {"name": "Seller", "attributes": [
        {"name": "business_name"}, {"name": "email"},
    ]}},
]

SYSTEM = {
    "id": "sys-1",
    "name": "Shop",
    "classifiers": CLASSIFIERS,
    "relations": [],
}

PAGES = [
    {"id": "p1", "name": "Browse_Products"},
    {"id": "p2", "name": "Product_Detail"},
]

SECTIONS = [
    {
        "id": "s1",
        "name": "ProductList",
        "primary_model": "Product",
        "layout": "card",
        "col_span": 12,
        "position": "main",
        "attributes": ["name", "price"],
        "view_detail_page": "Product_Detail",
        "operations": {"create": False, "update": False, "delete": False},
        "style": {"color": "blue", "display_mode": "grid"},
    }
]


def _mock_get(url, **kwargs):
    m = MagicMock()
    m.raise_for_status = MagicMock()
    m.ok = True
    if "/interfaces/" in url:
        m.json.return_value = IFACE
    elif "/classifiers/" in url:
        m.json.return_value = CLASSIFIERS
    elif "/relations/" in url:
        m.json.return_value = []
    elif "/systems/" in url:
        m.json.return_value = SYSTEM
    else:
        m.json.return_value = {}
    return m


def _mock_put(url, **kwargs):
    m = MagicMock()
    m.raise_for_status = MagicMock()
    m.ok = True
    return m


# ── get_interface_full_context ─────────────────────────────────────────────────

class TestGetInterfaceFullContext:
    def test_returns_interface_and_system(self):
        with patch("requests.get", side_effect=_mock_get):
            result = get_interface_full_context("iface-1")
        data = json.loads(result)
        assert data["interface"]["id"] == "iface-1"
        assert "system" in data
        assert data["system"]["id"] == "sys-1"

    def test_error_on_http_failure(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.raise_for_status.side_effect = Exception("404 Not Found")
            result = get_interface_full_context("bad-id")
        assert result.startswith("Error fetching full context:")

    def test_system_context_embedded(self):
        with patch("requests.get", side_effect=_mock_get):
            result = get_interface_full_context("iface-1")
        data = json.loads(result)
        # classifiers must be embedded in system
        assert len(data["system"]["classifiers"]) == 2
        assert data["system"]["classifiers"][0]["data"]["name"] == "Product"


# ── validate_and_save_candidate ───────────────────────────────────────────────

class TestValidateAndSaveCandidate:
    def _run(self, pages=None, sections=None, idx=0):
        with patch("requests.get", side_effect=_mock_get), \
             patch("requests.put", side_effect=_mock_put) as mock_put:
            result = validate_and_save_candidate(
                interface_id="iface-1",
                candidate_index=idx,
                name="Candidate A",
                description="card-forward layout",
                pages=pages or PAGES,
                sections=sections or SECTIONS,
            )
        return result, mock_put

    def test_valid_candidate_saved_ok(self):
        result, mock_put = self._run()
        assert result.startswith("OK:")
        assert mock_put.call_count == 1

    def test_saved_data_contains_candidate(self):
        _, mock_put = self._run(idx=0)
        sent = mock_put.call_args.kwargs["json"]
        candidates = sent["data"]["candidates"]
        assert len(candidates) >= 1
        assert candidates[0]["name"] == "Candidate A"
        assert candidates[0]["id"] == "c0"

    def test_second_candidate_appended(self):
        iface_with_c0 = {
            **IFACE,
            "data": {**IFACE["data"], "candidates": [{"id": "c0", "name": "A"}]},
        }
        def mock_get_c1(url, **kwargs):
            m = _mock_get(url, **kwargs)
            if "/interfaces/" in url:
                m.json.return_value = iface_with_c0
            return m

        with patch("requests.get", side_effect=mock_get_c1), \
             patch("requests.put", side_effect=_mock_put) as mock_put:
            result = validate_and_save_candidate(
                "iface-1", 1, "Candidate B", "table layout", PAGES, SECTIONS
            )
        assert result.startswith("OK:")
        sent = mock_put.call_args.kwargs["json"]
        candidates = sent["data"]["candidates"]
        assert candidates[0]["id"] == "c0"
        assert candidates[1]["id"] == "c1"
        assert candidates[1]["name"] == "Candidate B"

    def test_invalid_layout_reported(self):
        bad_sections = [{**SECTIONS[0], "layout": "flyingpig"}]
        result, _ = self._run(sections=bad_sections)
        assert "invalid layout" in result

    def test_unknown_primary_model_reported(self):
        bad_sections = [{**SECTIONS[0], "primary_model": "Ghost"}]
        result, _ = self._run(sections=bad_sections)
        assert "unknown primary_model" in result

    def test_unknown_attribute_auto_stripped(self):
        sections_with_bad_attr = [{
            **SECTIONS[0],
            "attributes": ["name", "nonexistent_field"],
        }]
        result, mock_put = self._run(sections=sections_with_bad_attr)
        # Save still proceeds
        assert mock_put.call_count == 1
        sent = mock_put.call_args.kwargs["json"]
        saved_attrs = sent["data"]["candidates"][0]["sections"][0]["attributes"]
        assert "nonexistent_field" not in saved_attrs
        assert "name" in saved_attrs

    def test_dot_notation_valid_prefix(self):
        sections_with_dot = [{
            **SECTIONS[0],
            "attributes": ["name", "Seller.business_name"],
        }]
        result, _ = self._run(sections=sections_with_dot)
        # "Seller" is a known model — no error for dot-notation
        assert "dot-notation prefix 'Seller' not a known model" not in result

    def test_dot_notation_unknown_prefix_reported(self):
        sections_with_bad_dot = [{
            **SECTIONS[0],
            "attributes": ["Ghost.name"],
        }]
        result, _ = self._run(sections=sections_with_bad_dot)
        assert "dot-notation prefix 'Ghost' not a known model" in result

    def test_view_detail_page_not_in_pages_reported(self):
        bad_sections = [{**SECTIONS[0], "view_detail_page": "Nonexistent_Page"}]
        result, _ = self._run(sections=bad_sections)
        assert "view_detail_page" in result

    def test_success_page_not_in_pages_reported(self):
        sections_with_bad_sp = [{
            **SECTIONS[0],
            "layout": "form",
            "style": {"success_page": "Missing_Page"},
        }]
        result, _ = self._run(sections=sections_with_bad_sp)
        assert "success_page" in result

    def test_invalid_style_color_reported(self):
        bad_sections = [{**SECTIONS[0], "style": {"color": "rainbow"}}]
        result, _ = self._run(sections=bad_sections)
        assert "style.color" in result

    def test_valid_style_values_no_error(self):
        good_sections = [{
            **SECTIONS[0],
            "style": {
                "color": "purple",
                "density": "compact",
                "shadow": "lg",
                "display_mode": "carousel",
                "card_style": "product",
            },
        }]
        result, _ = self._run(sections=good_sections)
        assert result.startswith("OK:")

    def test_http_error_returns_error_string(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.raise_for_status.side_effect = Exception("500")
            result = validate_and_save_candidate("iface-1", 0, "x", "y", [], [])
        assert result.startswith("Error saving candidate:")


# ── render_candidate_preview ──────────────────────────────────────────────────

class TestRenderCandidatePreview:
    def test_success_returns_ok(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.raise_for_status = MagicMock()
            result = render_candidate_preview("iface-1", 0)
        assert result.startswith("OK:")
        assert "0" in result

    def test_calls_correct_endpoint(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = True
            render_candidate_preview("iface-1", 2)
        url_called = mock_post.call_args.args[0]
        assert "iface-1/candidates/2/render" in url_called

    def test_non_200_returns_error(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = False
            mock_post.return_value.status_code = 404
            mock_post.return_value.text = "Not found"
            result = render_candidate_preview("iface-1", 0)
        assert "Render failed" in result
        assert "404" in result

    def test_network_exception_returns_error(self):
        with patch("requests.post", side_effect=Exception("timeout")):
            result = render_candidate_preview("iface-1", 0)
        assert result.startswith("Error rendering preview:")
        assert "timeout" in result
