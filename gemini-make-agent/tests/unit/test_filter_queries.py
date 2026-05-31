"""Unit tests for _resolve_filter_field and _apply_section_query from query_helpers."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "prototypes/backend/generation/templates/helpers"))
from query_helpers import _resolve_filter_field, _apply_section_query


# ── Mock queryset ──────────────────────────────────────────────────────────────

class MockQS:
    """Minimal queryset mock that records filter/exclude/order_by calls.

    If a lookup key (before any __ suffix) is not in ``valid_fields``, the
    method raises an Exception to simulate Django's FieldError for unknown fields.
    """

    def __init__(self, items=None, valid_fields=None):
        self._items = list(items or [])
        self.valid_fields = set(valid_fields or [])
        self.filter_calls = []
        self.exclude_calls = []
        self.order_by_calls = []
        self._slice_start = None
        self._slice_stop = None

    # ── internal helpers ──

    def _check_fields(self, kwargs):
        for key in kwargs:
            # extract the root field name (before the first __)
            root = key.split('__')[0]
            if self.valid_fields and root not in self.valid_fields:
                raise Exception(f"Invalid field: {root}")

    def _clone(self):
        clone = MockQS(self._items, self.valid_fields)
        clone.filter_calls = list(self.filter_calls)
        clone.exclude_calls = list(self.exclude_calls)
        clone.order_by_calls = list(self.order_by_calls)
        return clone

    # ── queryset API ──

    def filter(self, **kwargs):
        self._check_fields(kwargs)
        clone = self._clone()
        clone.filter_calls.append(kwargs)
        return clone

    def exclude(self, **kwargs):
        self._check_fields(kwargs)
        clone = self._clone()
        clone.exclude_calls.append(kwargs)
        return clone

    def order_by(self, *args):
        clone = self._clone()
        clone.order_by_calls.append(list(args))
        return clone

    def __getitem__(self, key):
        clone = self._clone()
        if isinstance(key, slice):
            clone._slice_start = key.start
            clone._slice_stop = key.stop
        return clone


# ── _resolve_filter_field ──────────────────────────────────────────────────────

class TestResolveFilterField:
    def test_direct_field_passthrough(self):
        assert _resolve_filter_field("name") == "name"

    def test_one_hop_uppercase_fk(self):
        assert _resolve_filter_field("Seller.name") == "Seller__name"

    def test_one_hop_lowercase_case_preserved(self):
        # case is preserved — caller must use correct FK name (capital for forward FK)
        assert _resolve_filter_field("seller.name") == "seller__name"

    def test_multi_hop_dot_notation(self):
        assert _resolve_filter_field("Seller.Category.name") == "Seller__Category__name"

    def test_already_dunder_passthrough(self):
        assert _resolve_filter_field("Seller__name") == "Seller__name"

    def test_empty_string_passthrough(self):
        assert _resolve_filter_field("") == ""

    def test_none_passthrough(self):
        assert _resolve_filter_field(None) is None


# ── _apply_section_query ───────────────────────────────────────────────────────

class TestApplySectionQuery:
    def _qs(self, valid_fields=None):
        return MockQS(valid_fields=valid_fields or [])

    # direct field filter
    def test_direct_field_filter_applied(self):
        qs = self._qs(valid_fields=["status"])
        result = _apply_section_query(qs, {"filters": [{"field": "status", "operator": "eq", "value": "active"}]})
        assert len(result.filter_calls) == 1
        assert result.filter_calls[0] == {"status": "active"}

    # one-hop FK via dot-notation
    def test_one_hop_fk_dot_notation_filter(self):
        qs = self._qs(valid_fields=["Seller"])
        result = _apply_section_query(qs, {"filters": [{"field": "Seller.name", "operator": "eq", "value": "Acme"}]})
        assert len(result.filter_calls) == 1
        assert "Seller__name" in result.filter_calls[0]

    # lowercase FK — case preserved, caller must use exact field name
    def test_lowercase_fk_case_preserved(self):
        qs = self._qs(valid_fields=["seller"])
        result = _apply_section_query(qs, {"filters": [{"field": "seller.name", "operator": "eq", "value": "Acme"}]})
        assert len(result.filter_calls) == 1
        assert "seller__name" in result.filter_calls[0]

    # invalid direct field — exception silently skipped
    def test_invalid_direct_field_silently_skipped(self):
        qs = self._qs(valid_fields=["name"])  # "ghost_field" not valid
        result = _apply_section_query(qs, {"filters": [{"field": "ghost_field", "operator": "eq", "value": "x"}]})
        # filter call raises → silently swallowed, result still a queryset
        assert len(result.filter_calls) == 0

    # multi-hop filter — passed through to Django (Django decides validity)
    def test_multi_hop_filter_passed_through(self):
        qs = self._qs(valid_fields=["Seller"])
        result = _apply_section_query(qs, {"filters": [{"field": "Seller.Category.name", "operator": "eq", "value": "Electronics"}]})
        # The field resolves to "Seller__Category__name"; root is "Seller" which is valid
        assert len(result.filter_calls) == 1
        assert "Seller__Category__name" in result.filter_calls[0]

    # reverse relation filter using lowercase accessor
    def test_reverse_relation_filter_lowercase_accessor(self):
        qs = self._qs(valid_fields=["product"])
        result = _apply_section_query(qs, {"filters": [{"field": "product.name", "operator": "eq", "value": "Widget"}]})
        assert len(result.filter_calls) == 1
        assert "product__name" in result.filter_calls[0]

    # order_by as plain strings
    def test_order_by_strings(self):
        qs = self._qs()
        result = _apply_section_query(qs, {"order_by": ["name", "-price"]})
        assert result.order_by_calls == [["name", "-price"]]

    # order_by as dicts with direction
    def test_order_by_dicts_asc(self):
        qs = self._qs()
        result = _apply_section_query(qs, {"order_by": [{"field": "name", "direction": "asc"}]})
        assert result.order_by_calls == [["name"]]

    def test_order_by_dicts_desc(self):
        qs = self._qs()
        result = _apply_section_query(qs, {"order_by": [{"field": "price", "direction": "desc"}]})
        assert result.order_by_calls == [["-price"]]

    # exclude_source
    def test_exclude_source_applied(self):
        qs = self._qs()

        class FakeObj:
            id = 42

        result = _apply_section_query(qs, {"exclude_source": True}, source_obj=FakeObj())
        assert len(result.exclude_calls) == 1
        assert result.exclude_calls[0] == {"id": 42}

    def test_exclude_source_not_applied_when_none(self):
        qs = self._qs()
        result = _apply_section_query(qs, {"exclude_source": True}, source_obj=None)
        assert len(result.exclude_calls) == 0

    # limit / offset slicing
    def test_limit_produces_slice(self):
        qs = self._qs()
        result = _apply_section_query(qs, {"limit": 10, "offset": 0})
        assert result._slice_stop == 10
        assert result._slice_start == 0

    def test_offset_only_produces_slice(self):
        qs = self._qs()
        result = _apply_section_query(qs, {"offset": 5})
        assert result._slice_start == 5

    def test_limit_and_offset_together(self):
        qs = self._qs()
        result = _apply_section_query(qs, {"limit": 10, "offset": 20})
        assert result._slice_start == 20
        assert result._slice_stop == 30

    # neq uses exclude
    def test_neq_operator_uses_exclude(self):
        qs = self._qs(valid_fields=["status"])
        result = _apply_section_query(qs, {"filters": [{"field": "status", "operator": "neq", "value": "archived"}]})
        assert len(result.exclude_calls) == 1
        assert result.exclude_calls[0] == {"status": "archived"}

    # no query dict
    def test_empty_query_returns_qs_unchanged(self):
        qs = self._qs()
        result = _apply_section_query(qs, None)
        assert result.filter_calls == []
        assert result.exclude_calls == []
        assert result.order_by_calls == []
