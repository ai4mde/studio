import unittest

from llm.interface_generator.candidate_defaults import (
    _assign_default_page_categories,
    _default_category_for_model,
    _default_section_for_page,
    _ensure_normal_page_navigation,
    _footer_sections_for_candidate,
    _header_sections_for_candidate,
    _merge_page_categories,
    _model_for_page_category,
    _sidebar_nav_section_for_candidate,
    _top_nav_section_for_candidate,
)


class CandidateDefaultCategoryTests(unittest.TestCase):
    def test_default_category_for_model_returns_none_for_blank_model(self):
        """Verify that default category for model returns none for blank model."""
        self.assertIsNone(_default_category_for_model(""))

    def test_default_category_for_model_uses_model_id_map(self):
        """Verify that default category for model uses model id map."""
        self.assertEqual(
            _default_category_for_model("Product", {"Product": "product-id"}),
            {"label": "Product", "value": {"id": "product-id", "name": "Product"}},
        )

    def test_model_for_page_category_prefers_explicit_primary_model(self):
        """Verify that model for page category prefers explicit primary model."""
        self.assertEqual(
            _model_for_page_category(
                {"primary_model": "Product", "sections": [{"value": "seller_section"}]},
                {"seller_section": {"primary_model": "Seller"}},
                {"Product", "Seller"},
            ),
            "Product",
        )

    def test_model_for_page_category_uses_first_section_model(self):
        """Verify that model for page category uses first section model."""
        self.assertEqual(
            _model_for_page_category(
                {"name": "Product Detail", "sections": [{"value": "product_section"}]},
                {"product_section": {"primary_model": "Product"}},
                {"Product"},
            ),
            "Product",
        )

    def test_assign_default_page_categories_skips_activity_pages(self):
        """Verify that assign default page categories skips activity pages."""
        pages = [{"name": "Checkout", "type": {"value": "activity"}, "primary_model": "Order"}]

        self.assertEqual(
            _assign_default_page_categories(pages, [], {"Order": "order-id"})[0]["category"],
            None,
        )

    def test_assign_default_page_categories_keeps_existing_category(self):
        """Verify that assign default page categories keeps existing category."""
        pages = [{"name": "Products", "primary_model": "Product", "category": {"label": "Existing"}}]

        self.assertEqual(
            _assign_default_page_categories(pages, [], {"Product": "product-id"})[0]["category"],
            {"label": "Existing"},
        )

    def test_assign_default_page_categories_sets_model_category(self):
        """Verify that assign default page categories sets model category."""
        pages = [{"name": "Products", "primary_model": "Product"}]

        self.assertEqual(
            _assign_default_page_categories(pages, [], {"Product": "product-id"})[0]["category"],
            {"label": "Product", "value": {"id": "product-id", "name": "Product"}},
        )

    def test_merge_page_categories_keeps_existing_and_adds_page_categories(self):
        """Verify that merge page categories keeps existing and adds page categories."""
        categories = [{"id": "product-id", "name": "Product"}]
        pages = [
            {"category": {"value": {"id": "product-id", "name": "Product"}}},
            {"category": {"value": {"id": "order-id", "name": "Order"}}},
        ]

        self.assertEqual(
            _merge_page_categories(categories, pages),
            [{"id": "product-id", "name": "Product"}, {"id": "order-id", "name": "Order"}],
        )


class CandidateDefaultSectionTests(unittest.TestCase):
    def test_default_section_for_page_builds_model_bound_section(self):
        """Verify that default section for page builds model bound section."""
        section = _default_section_for_page(
            {"id": "Products", "name": "Products"},
            "Product",
            {"Product": ["name", "price"]},
            0,
        )

        self.assertEqual(section["id"], "products_product_card")
        self.assertEqual(section["primary_model"], "Product")
        self.assertEqual(section["attributes"], ["name", "price"])
        self.assertEqual(section["position"], "main")

    def test_header_sections_for_candidate_builds_single_header_with_nav_methods(self):
        """Verify that header sections for candidate builds single header with nav methods."""
        header = _header_sections_for_candidate([{"name": "Products"}, {"name": "Orders"}], 0)[0]

        self.assertEqual(header["position"], "header")
        self.assertEqual(header["role"], "header")
        self.assertEqual([method["name"] for method in header["methods"]], ["Products", "Orders"])

    def test_footer_sections_for_candidate_builds_footer_with_nav_methods(self):
        """Verify that footer sections for candidate builds footer with nav methods."""
        footer = _footer_sections_for_candidate(0, [{"name": "Products"}])[0]

        self.assertEqual(footer["position"], "footer")
        self.assertEqual(footer["role"], "footer")
        self.assertEqual([method["name"] for method in footer["methods"]], ["Products"])

    def test_top_nav_section_for_candidate_builds_header_nav(self):
        """Verify that top nav section for candidate builds header nav."""
        nav = _top_nav_section_for_candidate([{"name": "Products"}], 1)

        self.assertEqual(nav["position"], "header")
        self.assertEqual(nav["layout"], "site-nav")
        self.assertEqual([method["name"] for method in nav["methods"]], ["Products"])

    def test_sidebar_nav_section_for_candidate_builds_sidebar_nav(self):
        """Verify that sidebar nav section for candidate builds sidebar nav."""
        nav = _sidebar_nav_section_for_candidate([{"name": "Products"}], 2)

        self.assertEqual(nav["position"], "sidebar")
        self.assertEqual(nav["style"]["sidebar_side"], "left")
        self.assertEqual([method["name"] for method in nav["methods"]], ["Products"])

    def test_ensure_normal_page_navigation_adds_nav_when_missing(self):
        """Verify that ensure normal page navigation adds nav when missing."""
        pages = [{"id": "products", "name": "Products", "sections": []}]
        sections = []

        next_pages, next_sections = _ensure_normal_page_navigation(pages, sections, pages, 0)

        self.assertEqual(len(next_sections), 1)
        self.assertEqual(next_sections[0]["id"], "app_page_nav")
        self.assertEqual(next_sections[0]["position"], "header")
        self.assertEqual(next_pages[0]["sections"], [])

    def test_ensure_normal_page_navigation_keeps_single_existing_header_nav(self):
        """Verify that ensure normal page navigation keeps single existing header nav."""
        pages = [{"id": "products", "name": "Products", "sections": [{"value": "nav_one"}, {"value": "nav_two"}]}]
        sections = [
            {"id": "nav_one", "layout": "site-nav", "position": "header", "methods": []},
            {"id": "nav_two", "layout": "site-nav", "position": "header", "methods": []},
        ]

        next_pages, next_sections = _ensure_normal_page_navigation(pages, sections, pages, 0)

        self.assertEqual([section["id"] for section in next_sections], ["nav_one"])
        self.assertEqual(next_pages[0]["sections"], [{"value": "nav_one"}])


if __name__ == "__main__":
    unittest.main()
