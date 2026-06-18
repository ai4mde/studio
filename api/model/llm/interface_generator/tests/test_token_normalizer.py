"""Tests for llm.interface_generator.token_normalizer — all pure functions, no DB needed."""

from unittest import TestCase

from llm.interface_generator.token_normalizer import (
    _as_list,
    _name_id,
    _page_name,
    _section_id,
    _sid,
    _workflow_page_name,
)


class AsListTests(TestCase):
    def test_dict_with_key(self):
        """Verify that dict with key."""
        self.assertEqual(_as_list({"items": [1, 2]}, "items"), [1, 2])

    def test_dict_missing_key(self):
        """Verify that dict missing key."""
        self.assertEqual(_as_list({"other": [1]}, "items"), [])

    def test_dict_key_is_none(self):
        """Verify that dict key is none."""
        self.assertEqual(_as_list({"items": None}, "items"), [])

    def test_list_passthrough(self):
        """Verify that list passthrough."""
        self.assertEqual(_as_list([1, 2, 3], "ignored"), [1, 2, 3])

    def test_none_returns_empty(self):
        """Verify that none returns empty."""
        self.assertEqual(_as_list(None, "key"), [])


class NameIdTests(TestCase):
    def test_basic_string(self):
        """Verify that basic string."""
        self.assertEqual(_name_id("hello world"), "hello_world")

    def test_hyphens(self):
        """Verify that hyphens."""
        self.assertEqual(_name_id("my-component"), "my_component")

    def test_strips_special_chars(self):
        """Verify that strips special chars."""
        self.assertEqual(_name_id("hello!@#world"), "helloworld")

    def test_empty_string_fallback(self):
        """Verify that empty string fallback."""
        self.assertEqual(_name_id(""), "workflow_step")

    def test_none_fallback(self):
        """Verify that none fallback."""
        self.assertEqual(_name_id(None), "workflow_step")

    def test_consecutive_spaces(self):
        """Verify that consecutive spaces."""
        self.assertEqual(_name_id("hello   world"), "hello_world")

    def test_leading_trailing_whitespace(self):
        """Verify that leading trailing whitespace."""
        self.assertEqual(_name_id("  hello  "), "hello")


class PageNameTests(TestCase):
    def test_capitalizes_words(self):
        """Verify that capitalizes words."""
        self.assertEqual(_page_name("order list"), "Order_List")

    def test_handles_hyphen(self):
        """Verify that handles hyphen."""
        self.assertEqual(_page_name("my-page"), "My_Page")

    def test_already_capitalized(self):
        """Verify that already capitalized."""
        self.assertEqual(_page_name("Orders"), "Orders")


class WorkflowPageNameTests(TestCase):
    def test_prefixes_workflow(self):
        """Verify that prefixes workflow."""
        self.assertEqual(_workflow_page_name("submit form"), "Workflow_Submit_Form")


class SectionIdTests(TestCase):
    def test_lowercases(self):
        """Verify that lowercases."""
        self.assertEqual(_section_id("OrderList"), "orderlist")

    def test_spaces_to_underscores(self):
        """Verify that spaces to underscores."""
        self.assertEqual(_section_id("order list"), "order_list")

    def test_empty_fallback(self):
        """Verify that empty fallback."""
        self.assertEqual(_section_id(""), "workflow_step")


class SidTests(TestCase):
    def test_basic(self):
        """Verify that basic."""
        self.assertEqual(_sid("Order List"), "order_list")

    def test_special_chars_replaced(self):
        """Verify that special chars replaced."""
        self.assertEqual(_sid("order--list"), "order_list")

    def test_empty_fallback(self):
        """Verify that empty fallback."""
        self.assertEqual(_sid(""), "section")

    def test_none_fallback(self):
        """Verify that none fallback."""
        self.assertEqual(_sid(None), "section")

    def test_strips_leading_trailing_underscore(self):
        """Verify that strips leading trailing underscore."""
        self.assertEqual(_sid("__order__"), "order")

    def test_consecutive_non_alnum(self):
        # Multiple consecutive non-alphanumeric chars collapse to one underscore
        """Verify that consecutive non alnum."""
        self.assertEqual(_sid("a...b"), "a_b")
