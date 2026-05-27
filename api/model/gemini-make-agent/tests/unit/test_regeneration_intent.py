"""Unit tests for the LLM-based regeneration intent parsing and execution."""
import json
from unittest.mock import patch, MagicMock
import pytest

from app.tools import (
    _parse_regeneration_intent,
    _apply_intent_colors_to_tokens,
    _prompt_requests_color_change,
    _prompt_requests_layout_change,
    regenerate_candidate_set,
)

# ── Helpers ────────────────────────────────────────────────────────────────────

def _gemini_response(payload: dict) -> MagicMock:
    """Build a mock requests.Response whose JSON looks like a Gemini API reply."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": json.dumps(payload)}]}}]
    }
    return resp


# ── _prompt_requests_color_change ──────────────────────────────────────────────

class TestPromptRequestsColorChange:
    def test_explicit_color_keyword(self):
        assert _prompt_requests_color_change("change the color to blue") is True

    def test_hex_code(self):
        assert _prompt_requests_color_change("use #1e3a5f for the header") is True

    def test_color_name_only(self):
        assert _prompt_requests_color_change("make it red") is True

    def test_chinese_color(self):
        assert _prompt_requests_color_change("把背景色改成蓝色") is True

    def test_no_color(self):
        assert _prompt_requests_color_change("add a sidebar navigation") is False

    def test_layout_only(self):
        assert _prompt_requests_color_change("compact table layout") is False

    def test_empty(self):
        assert _prompt_requests_color_change("") is False


# ── _prompt_requests_layout_change ─────────────────────────────────────────────

class TestPromptRequestsLayoutChange:
    def test_pure_layout_term(self):
        assert _prompt_requests_layout_change("change the layout to sidebar") is True

    def test_table_layout(self):
        assert _prompt_requests_layout_change("show as table") is True

    def test_gallery_layout(self):
        assert _prompt_requests_layout_change("use gallery view") is True

    def test_compact(self):
        assert _prompt_requests_layout_change("make it compact") is True

    # Key regression: color context should suppress ambiguous layout terms
    def test_header_color_not_layout(self):
        assert _prompt_requests_layout_change("change header color to blue") is False

    def test_nav_color_not_layout(self):
        assert _prompt_requests_layout_change("nav background red") is False

    def test_footer_color_not_layout(self):
        assert _prompt_requests_layout_change("footer color #333333") is False

    def test_header_alone_is_layout(self):
        assert _prompt_requests_layout_change("restructure the header") is True

    def test_empty(self):
        assert _prompt_requests_layout_change("") is False


# ── _apply_intent_colors_to_tokens ─────────────────────────────────────────────

class TestApplyIntentColorsToTokens:
    BASE = {"accent.hex": "#2563eb", "page.body.bg_hex": "#f9fafb"}

    def test_header_scope_sets_correct_token(self):
        result = _apply_intent_colors_to_tokens(
            dict(self.BASE),
            [{"scope": "header", "hex": "#1e3a5f", "name": "navy"}],
        )
        assert result["region.header.bg_hex"] == "#1e3a5f"

    def test_button_scope(self):
        result = _apply_intent_colors_to_tokens(
            dict(self.BASE),
            [{"scope": "button", "hex": "#7c3aed", "name": "purple"}],
        )
        assert result["button.primary.bg_hex"] == "#7c3aed"
        assert result["button.primary.border_hex"] == "#7c3aed"

    def test_multiple_scopes(self):
        result = _apply_intent_colors_to_tokens(
            dict(self.BASE),
            [
                {"scope": "header", "hex": "#1e3a5f", "name": "navy"},
                {"scope": "button", "hex": "#dc2626", "name": "red"},
            ],
        )
        assert result["region.header.bg_hex"] == "#1e3a5f"
        assert result["button.primary.bg_hex"] == "#dc2626"

    def test_base_tokens_preserved(self):
        result = _apply_intent_colors_to_tokens(
            dict(self.BASE),
            [{"scope": "button", "hex": "#7c3aed", "name": "purple"}],
        )
        assert result["page.body.bg_hex"] == "#f9fafb"

    def test_missing_hex_skipped(self):
        result = _apply_intent_colors_to_tokens(
            dict(self.BASE),
            [{"scope": "header", "hex": None, "name": ""}],
        )
        assert "region.header.bg_hex" not in result

    def test_empty_colors_returns_base(self):
        base = dict(self.BASE)
        result = _apply_intent_colors_to_tokens(base, [])
        assert result == base

    def test_color_name_without_hex_resolved(self):
        result = _apply_intent_colors_to_tokens(
            dict(self.BASE),
            [{"scope": "button", "hex": None, "name": "blue"}],
        )
        assert "button.primary.bg_hex" in result


# ── _parse_regeneration_intent ─────────────────────────────────────────────────

class TestParseRegenerationIntent:
    def _post_mock(self, payload):
        return patch("app.tools.requests.post", return_value=_gemini_response(payload))

    def test_color_only_request(self):
        llm_payload = {
            "change_color": True, "change_layout": False,
            "colors": [{"scope": "header", "hex": "#1e3a5f", "name": "navy"}],
            "layout": {},
        }
        with self._post_mock(llm_payload):
            with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
                result = _parse_regeneration_intent("change header to navy")
        assert result["change_color"] is True
        assert result["change_layout"] is False
        assert result["colors"][0]["scope"] == "header"
        assert result["colors"][0]["hex"] == "#1e3a5f"

    def test_layout_only_request(self):
        llm_payload = {
            "change_color": False, "change_layout": True,
            "colors": [],
            "layout": {"nav": "sidebar-left", "density": "compact"},
        }
        with self._post_mock(llm_payload):
            with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
                result = _parse_regeneration_intent("left sidebar compact")
        assert result["change_color"] is False
        assert result["change_layout"] is True
        assert result["layout"]["nav"] == "sidebar-left"
        assert result["layout"]["density"] == "compact"

    def test_combined_request(self):
        llm_payload = {
            "change_color": True, "change_layout": True,
            "colors": [{"scope": "accent", "hex": "#16a34a", "name": "green"}],
            "layout": {"data_display": "table", "nav": "sidebar-left"},
        }
        with self._post_mock(llm_payload):
            with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
                result = _parse_regeneration_intent("green table with left nav")
        assert result["change_color"] is True
        assert result["change_layout"] is True
        assert result["colors"][0]["scope"] == "accent"
        assert result["layout"]["data_display"] == "table"

    def test_empty_requirements(self):
        result = _parse_regeneration_intent("")
        assert result == {"change_color": False, "change_layout": False, "colors": [], "layout": {}}

    def test_fallback_on_api_error(self):
        with patch("app.tools.requests.post", side_effect=Exception("timeout")):
            with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
                result = _parse_regeneration_intent("blue header")
        # Fallback to string matching — "blue" is a color term
        assert result["change_color"] is True

    def test_fallback_no_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            result = _parse_regeneration_intent("change the layout to table")
        assert result["change_layout"] is True
        assert result["colors"] == []


# ── regenerate_candidate_set integration ───────────────────────────────────────

BASE_CANDIDATE = {
    "id": "cand-0",
    "name": "Original",
    "description": "",
    "pages": [{"id": "p1", "name": "Main", "layout": {"value": "default"}, "sections": [{"id": "s1"}]}],
    "sections": [
        {"id": "s1", "name": "ProductList", "primary_model": "Product",
         "layout": "card", "col_span": 12, "position": "main",
         "style": {"density": "normal"}}
    ],
    "tokens": {"accent.hex": "#2563eb", "region.header.bg_hex": "#2563eb"},
    "styling": {"variantIndex": 0},
    "design_spec": None,
    "variation_strategy": None,
}

REGEN_CONTEXT = {
    "interface_id": "iface-1",
    "selected_candidate_index": 0,
    "designer_requirements": "",
    "regeneration_contract": {},
    "current_interface": {"name": "Shop"},
    "base_candidate": BASE_CANDIDATE,
}


def _mock_regen_calls(intent_payload, *, save_result="OK: candidate 0 saved."):
    """Return a context manager that patches all external calls for regenerate_candidate_set."""
    from unittest.mock import call as _call

    def post_side_effect(url, **kwargs):
        if "generateContent" in url:
            return _gemini_response(intent_payload)
        # render call
        m = MagicMock(); m.ok = True; m.raise_for_status = MagicMock()
        return m

    ctx = patch("app.tools.requests.post", side_effect=post_side_effect)
    ctx2 = patch("app.tools.get_candidate_regeneration_context",
                 return_value=json.dumps(REGEN_CONTEXT))
    ctx3 = patch("app.tools.validate_and_save_candidate", return_value=save_result)
    ctx4 = patch("app.tools.render_candidate_preview_func", return_value="OK: rendered.")
    return ctx, ctx2, ctx3, ctx4


class TestRegenerateCandidateSet:
    def _run(self, intent_payload, requirements=""):
        ctxs = _mock_regen_calls(intent_payload)
        with ctxs[0], ctxs[1], ctxs[2] as mock_save, ctxs[3]:
            with patch.dict("os.environ", {"GEMINI_API_KEY": "key"}):
                result = regenerate_candidate_set("iface-1", 0, requirements)
        return result, mock_save

    def test_color_only_preserves_layout(self):
        intent = {
            "change_color": True, "change_layout": False,
            "colors": [{"scope": "header", "hex": "#1e3a5f", "name": "navy"}],
            "layout": {},
        }
        result, mock_save = self._run(intent, "change header to navy")
        assert result.startswith("OK:")
        # All 3 candidates saved
        assert mock_save.call_count == 3
        # tokens for all 3 should have the navy header applied
        for c in mock_save.call_args_list:
            tokens = json.loads(c.kwargs.get("tokens") or "{}")
            assert tokens.get("region.header.bg_hex") == "#1e3a5f"

    def test_layout_only_preserves_tokens(self):
        intent = {
            "change_color": False, "change_layout": True,
            "colors": [],
            "layout": {"nav": "sidebar-left"},
        }
        result, mock_save = self._run(intent, "left sidebar")
        assert result.startswith("OK:")
        # Base accent token must be preserved unchanged
        for c in mock_save.call_args_list:
            tokens = json.loads(c.kwargs.get("tokens") or "{}")
            assert tokens.get("accent.hex") == "#2563eb"

    def test_all_three_variants_saved(self):
        intent = {"change_color": False, "change_layout": False, "colors": [], "layout": {}}
        result, mock_save = self._run(intent, "")
        assert result.startswith("OK:")
        assert mock_save.call_count == 3
        indices = [c.kwargs["candidate_index"] for c in mock_save.call_args_list]
        assert indices == [0, 1, 2]

    # ── Multi-component color ──────────────────────────────────────────────────

    def test_multiple_color_targets_all_applied(self):
        """purple buttons + red badges + navy header — all three token groups set."""
        intent = {
            "change_color": True, "change_layout": False,
            "colors": [
                {"scope": "button", "hex": "#7c3aed", "name": "purple"},
                {"scope": "badge",  "hex": "#dc2626", "name": "red"},
                {"scope": "header", "hex": "#1e3a5f", "name": "navy"},
            ],
            "layout": {},
        }
        result, mock_save = self._run(intent, "purple buttons, red badges, navy header")
        assert result.startswith("OK:")
        for c in mock_save.call_args_list:
            tokens = json.loads(c.kwargs.get("tokens") or "{}")
            assert tokens.get("button.primary.bg_hex") == "#7c3aed"
            assert tokens.get("badge.info.bg_hex") == "#dc2626"
            assert tokens.get("region.header.bg_hex") == "#1e3a5f"

    def test_multiple_color_targets_same_across_all_variants(self):
        """All 3 variants must carry the identical multi-target color set."""
        intent = {
            "change_color": True, "change_layout": False,
            "colors": [
                {"scope": "nav",        "hex": "#111827", "name": "dark"},
                {"scope": "background", "hex": "#f0f4ff", "name": "light-blue"},
            ],
            "layout": {},
        }
        result, mock_save = self._run(intent, "dark nav, light blue background")
        assert result.startswith("OK:")
        # Collect per-variant token snapshots
        all_tokens = [json.loads(c.kwargs.get("tokens") or "{}") for c in mock_save.call_args_list]
        nav_colors = {t.get("nav.bg_hex") for t in all_tokens}
        # All 3 variants share the same nav color — no index-based drift
        assert nav_colors == {"#111827"}

    def test_global_accent_plus_specific_component(self):
        """Global accent color (affects many tokens) and a specific badge override."""
        intent = {
            "change_color": True, "change_layout": False,
            "colors": [
                {"scope": "accent", "hex": "#16a34a", "name": "green"},
                {"scope": "badge",  "hex": "#f97316", "name": "orange"},
            ],
            "layout": {},
        }
        result, mock_save = self._run(intent, "green accent, orange badges")
        assert result.startswith("OK:")
        for c in mock_save.call_args_list:
            tokens = json.loads(c.kwargs.get("tokens") or "{}")
            # accent scope sets input focus border too
            assert tokens.get("accent.hex") == "#16a34a"
            assert tokens.get("input.border_focus_hex") == "#16a34a"
            # badge override on top of accent
            assert tokens.get("badge.info.bg_hex") == "#f97316"

    # ── Multi-dimension layout ─────────────────────────────────────────────────

    def test_multiple_layout_dimensions(self):
        """sidebar-left + table + compact — all three layout specs applied."""
        intent = {
            "change_color": False, "change_layout": True,
            "colors": [],
            "layout": {"nav": "sidebar-left", "data_display": "table", "density": "compact"},
        }
        result, mock_save = self._run(intent, "left sidebar compact table")
        assert result.startswith("OK:")
        for c in mock_save.call_args_list:
            styling = json.loads(c.kwargs.get("styling") or "{}")
            li = styling.get("layoutIntent") or {}
            assert li.get("sidebar_side") == "left" or li.get("nav") in {"sidebar-left", "sidebar"}
            assert li.get("density") == "compact"
            assert li.get("forced_data_layout") == "table" or li.get("data_layout") == "table"

    def test_full_width_layout(self):
        intent = {
            "change_color": False, "change_layout": True,
            "colors": [],
            "layout": {"full_width": True},
        }
        result, mock_save = self._run(intent, "full width layout")
        assert result.startswith("OK:")
        for c in mock_save.call_args_list:
            styling = json.loads(c.kwargs.get("styling") or "{}")
            li = styling.get("layoutIntent") or {}
            assert li.get("main_width") == "full"
            assert li.get("header_width") == "full"

    # ── Global color + specific layout ────────────────────────────────────────

    def test_global_color_and_layout_change(self):
        """Blue theme (global accent) + table layout: color tokens updated AND
        layout changed, base tokens not reverted by layout pass."""
        intent = {
            "change_color": True, "change_layout": True,
            "colors": [{"scope": "accent", "hex": "#2563eb", "name": "blue"}],
            "layout": {"data_display": "table"},
        }
        result, mock_save = self._run(intent, "blue theme with table layout")
        assert result.startswith("OK:")
        for c in mock_save.call_args_list:
            tokens  = json.loads(c.kwargs.get("tokens")  or "{}")
            styling = json.loads(c.kwargs.get("styling") or "{}")
            li = styling.get("layoutIntent") or {}
            assert tokens.get("accent.hex") == "#2563eb"
            assert li.get("forced_data_layout") == "table" or li.get("data_layout") == "table"

    def test_multi_color_plus_sidebar_layout(self):
        """Navy header + purple buttons + right sidebar navigation."""
        intent = {
            "change_color": True, "change_layout": True,
            "colors": [
                {"scope": "header", "hex": "#1e3a5f", "name": "navy"},
                {"scope": "button", "hex": "#7c3aed", "name": "purple"},
            ],
            "layout": {"nav": "sidebar-right"},
        }
        result, mock_save = self._run(intent, "navy header, purple buttons, right sidebar")
        assert result.startswith("OK:")
        for c in mock_save.call_args_list:
            tokens  = json.loads(c.kwargs.get("tokens")  or "{}")
            styling = json.loads(c.kwargs.get("styling") or "{}")
            li = styling.get("layoutIntent") or {}
            assert tokens.get("region.header.bg_hex") == "#1e3a5f"
            assert tokens.get("button.primary.bg_hex") == "#7c3aed"
            assert li.get("sidebar_side") == "right" or li.get("nav") in {"sidebar-right", "sidebar"}

    def test_color_change_does_not_alter_layout_across_variants(self):
        """When only color changes, pages/sections for all 3 variants must be identical."""
        intent = {
            "change_color": True, "change_layout": False,
            "colors": [{"scope": "accent", "hex": "#16a34a", "name": "green"}],
            "layout": {},
        }
        result, mock_save = self._run(intent, "green accent")
        assert result.startswith("OK:")
        all_pages = [json.loads(c.kwargs.get("pages") or "[]") for c in mock_save.call_args_list]
        # All 3 variants produced from deep copy — structurally identical
        assert all_pages[0] == all_pages[1] == all_pages[2]

    def test_layout_change_does_not_alter_base_tokens_across_variants(self):
        """When only layout changes, base tokens must be identical across all 3 variants
        (only design.variant_index differs)."""
        intent = {
            "change_color": False, "change_layout": True,
            "colors": [],
            "layout": {"data_display": "gallery"},
        }
        result, mock_save = self._run(intent, "gallery layout")
        assert result.startswith("OK:")
        all_tokens = [json.loads(c.kwargs.get("tokens") or "{}") for c in mock_save.call_args_list]
        # Base accent unchanged from BASE_CANDIDATE
        for t in all_tokens:
            assert t.get("accent.hex") == "#2563eb"
        # variant_index differs across 3
        indices = [t.get("design.variant_index") for t in all_tokens]
        assert set(indices) == {"0", "1", "2"}
