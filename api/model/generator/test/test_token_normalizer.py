"""Tests for llm.interface_generator.token_normalizer — all pure functions, no DB needed."""

from django.test import SimpleTestCase

from llm.interface_generator.token_normalizer import (
    _as_list,
    _contrast_ratio,
    _expand_design_tokens,
    _hex_to_rgb,
    _is_dark_hex,
    _name_id,
    _needs_contrast_fix,
    _page_name,
    _relative_luminance,
    _section_id,
    _set_readable_token,
    _sid,
    _text_on_color,
    _workflow_page_name,
)


class AsListTests(SimpleTestCase):
    def test_dict_with_key(self):
        self.assertEqual(_as_list({"items": [1, 2]}, "items"), [1, 2])

    def test_dict_missing_key(self):
        self.assertEqual(_as_list({"other": [1]}, "items"), [])

    def test_dict_key_is_none(self):
        self.assertEqual(_as_list({"items": None}, "items"), [])

    def test_list_passthrough(self):
        self.assertEqual(_as_list([1, 2, 3], "ignored"), [1, 2, 3])

    def test_none_returns_empty(self):
        self.assertEqual(_as_list(None, "key"), [])


class NameIdTests(SimpleTestCase):
    def test_basic_string(self):
        self.assertEqual(_name_id("hello world"), "hello_world")

    def test_hyphens(self):
        self.assertEqual(_name_id("my-component"), "my_component")

    def test_strips_special_chars(self):
        self.assertEqual(_name_id("hello!@#world"), "helloworld")

    def test_empty_string_fallback(self):
        self.assertEqual(_name_id(""), "workflow_step")

    def test_none_fallback(self):
        self.assertEqual(_name_id(None), "workflow_step")

    def test_consecutive_spaces(self):
        self.assertEqual(_name_id("hello   world"), "hello_world")

    def test_leading_trailing_whitespace(self):
        self.assertEqual(_name_id("  hello  "), "hello")


class PageNameTests(SimpleTestCase):
    def test_capitalizes_words(self):
        self.assertEqual(_page_name("order list"), "Order_List")

    def test_handles_hyphen(self):
        self.assertEqual(_page_name("my-page"), "My_Page")

    def test_already_capitalized(self):
        self.assertEqual(_page_name("Orders"), "Orders")


class WorkflowPageNameTests(SimpleTestCase):
    def test_prefixes_workflow(self):
        self.assertEqual(_workflow_page_name("submit form"), "Workflow_Submit_Form")


class SectionIdTests(SimpleTestCase):
    def test_lowercases(self):
        self.assertEqual(_section_id("OrderList"), "orderlist")

    def test_spaces_to_underscores(self):
        self.assertEqual(_section_id("order list"), "order_list")

    def test_empty_fallback(self):
        self.assertEqual(_section_id(""), "workflow_step")


class SidTests(SimpleTestCase):
    def test_basic(self):
        self.assertEqual(_sid("Order List"), "order_list")

    def test_special_chars_replaced(self):
        self.assertEqual(_sid("order--list"), "order_list")

    def test_empty_fallback(self):
        self.assertEqual(_sid(""), "section")

    def test_none_fallback(self):
        self.assertEqual(_sid(None), "section")

    def test_strips_leading_trailing_underscore(self):
        self.assertEqual(_sid("__order__"), "order")

    def test_consecutive_non_alnum(self):
        # Multiple consecutive non-alphanumeric chars collapse to one underscore
        self.assertEqual(_sid("a...b"), "a_b")


class HexToRgbTests(SimpleTestCase):
    def test_6_char_hex(self):
        self.assertEqual(_hex_to_rgb("#ffffff"), (255, 255, 255))

    def test_black(self):
        self.assertEqual(_hex_to_rgb("#000000"), (0, 0, 0))

    def test_3_char_hex_expands(self):
        self.assertEqual(_hex_to_rgb("#fff"), (255, 255, 255))

    def test_3_char_color(self):
        self.assertEqual(_hex_to_rgb("#abc"), (0xAA, 0xBB, 0xCC))

    def test_no_hash_returns_none(self):
        self.assertIsNone(_hex_to_rgb("ffffff"))

    def test_invalid_chars_returns_none(self):
        self.assertIsNone(_hex_to_rgb("#zzzzzz"))

    def test_wrong_length_returns_none(self):
        self.assertIsNone(_hex_to_rgb("#ffff"))

    def test_non_string_returns_none(self):
        self.assertIsNone(_hex_to_rgb(None))
        self.assertIsNone(_hex_to_rgb(123))


class RelativeLuminanceTests(SimpleTestCase):
    def test_white_is_1(self):
        self.assertAlmostEqual(_relative_luminance("#ffffff"), 1.0, places=4)

    def test_black_is_0(self):
        self.assertAlmostEqual(_relative_luminance("#000000"), 0.0, places=4)

    def test_invalid_returns_none(self):
        self.assertIsNone(_relative_luminance("notacolor"))

    def test_mid_value(self):
        lum = _relative_luminance("#808080")
        self.assertIsNotNone(lum)
        self.assertGreater(lum, 0.0)
        self.assertLess(lum, 1.0)


class ContrastRatioTests(SimpleTestCase):
    def test_white_on_black_is_21(self):
        ratio = _contrast_ratio("#ffffff", "#000000")
        self.assertAlmostEqual(ratio, 21.0, places=1)

    def test_same_color_is_1(self):
        ratio = _contrast_ratio("#ffffff", "#ffffff")
        self.assertAlmostEqual(ratio, 1.0, places=4)

    def test_invalid_returns_none(self):
        self.assertIsNone(_contrast_ratio("invalid", "#ffffff"))


class NeedsContrastFixTests(SimpleTestCase):
    def test_white_on_black_no_fix_needed(self):
        self.assertFalse(_needs_contrast_fix("#ffffff", "#000000", 4.5))

    def test_light_gray_on_white_fix_needed(self):
        # #d1d5db on #ffffff has ratio ≈ 1.6, below 4.5
        self.assertTrue(_needs_contrast_fix("#d1d5db", "#ffffff", 4.5))

    def test_invalid_color_returns_false(self):
        self.assertFalse(_needs_contrast_fix("invalid", "#ffffff", 4.5))


class IsDarkHexTests(SimpleTestCase):
    def test_black_is_dark(self):
        self.assertTrue(_is_dark_hex("#000000"))

    def test_white_is_not_dark(self):
        self.assertFalse(_is_dark_hex("#ffffff"))

    def test_dark_blue_is_dark(self):
        self.assertTrue(_is_dark_hex("#1e40af"))

    def test_light_blue_is_not_dark(self):
        self.assertFalse(_is_dark_hex("#93c5fd"))

    def test_invalid_returns_false(self):
        self.assertFalse(_is_dark_hex("notacolor"))


class TextOnColorTests(SimpleTestCase):
    def test_dark_bg_returns_white(self):
        self.assertEqual(_text_on_color("#000000"), "#ffffff")

    def test_light_bg_returns_dark(self):
        self.assertEqual(_text_on_color("#ffffff"), "#111827")

    def test_dark_blue_returns_white(self):
        self.assertEqual(_text_on_color("#1e3a5f"), "#ffffff")


class SetReadableTokenTests(SimpleTestCase):
    def test_keeps_value_when_contrast_ok(self):
        tokens = {}
        result = _set_readable_token(tokens, ("text",), "#111827", "#ffffff", 4.5)
        self.assertEqual(result, "#111827")
        self.assertEqual(tokens["text"], "#111827")

    def test_uses_fallback_when_contrast_fails(self):
        tokens = {"text": "#cccccc"}  # low contrast on white
        result = _set_readable_token(tokens, ("text",), "#111827", "#ffffff", 4.5)
        self.assertEqual(result, "#111827")

    def test_sets_all_keys(self):
        tokens = {}
        _set_readable_token(tokens, ("key1", "key2"), "#111827", "#ffffff", 4.5)
        self.assertIn("key1", tokens)
        self.assertIn("key2", tokens)


class EnsureReadableTextTokensTests(SimpleTestCase):
    def test_no_change_on_light_bg(self):
        tokens = {"page.body.bg_hex": "#ffffff"}
        from llm.interface_generator.token_normalizer import _ensure_readable_text_tokens
        _ensure_readable_text_tokens(tokens)
        # Light background: function returns early, no new keys injected
        self.assertNotIn("page.body.text", tokens)

    def test_dark_bg_injects_light_text(self):
        tokens = {
            "page.body.bg_hex": "#0f172a",
            "region.main.bg_hex": "#0f172a",
            "component.card.bg_hex": "#1e293b",
        }
        from llm.interface_generator.token_normalizer import _ensure_readable_text_tokens
        _ensure_readable_text_tokens(tokens)
        self.assertIn("page.body.text", tokens)


class ExpandDesignTokensTests(SimpleTestCase):
    def test_empty_dict_fills_defaults(self):
        tokens = _expand_design_tokens({})
        self.assertIn("page.bg.hex", tokens)
        self.assertIn("button.primary.bg_hex", tokens)
        self.assertIn("input.bg_hex", tokens)
        self.assertIn("nav.bg_hex", tokens)

    def test_accent_propagates_to_button_and_nav(self):
        tokens = _expand_design_tokens({"accent.hex": "#e11d48"})
        self.assertEqual(tokens["button.primary.bg_hex"], "#e11d48")
        self.assertEqual(tokens["nav.bg_hex"], "#e11d48")

    def test_existing_values_not_overwritten(self):
        tokens = _expand_design_tokens({"button.primary.bg_hex": "#custom"})
        self.assertEqual(tokens["button.primary.bg_hex"], "#custom")

    def test_returns_same_dict(self):
        d = {}
        result = _expand_design_tokens(d)
        self.assertIs(result, d)
