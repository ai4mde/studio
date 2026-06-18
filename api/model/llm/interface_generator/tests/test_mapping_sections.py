import unittest

from llm.interface_generator.uml_mapping.mapping_sections import (
    _apply_nav_methods,
    _dedupe_agent_header_shells,
    _drop_unreferenced_non_global_sections,
    _ensure_candidate_content_structure,
    _ensure_mapping_chrome_sections,
    _ensure_mapping_content_sections,
    _ensure_pre_workflow_content_sections,
    _ensure_usecase_pages,
    _ensure_workflow_entry_sections,
    _inject_chrome_sections,
    _materialize_nav_plan_sections,
    category_names_for_pages,
)


class MappingSectionTests(unittest.TestCase):
    def test_category_names_for_pages_handles_supported_shapes(self):
        """Verify that category names for pages handles supported shapes."""
        pages = [
            {"category": None},
            {"category": {"label": "Product", "value": {"id": "p", "name": "Product"}}},
            {"category": {"label": "Order"}},
            {"category": "Customer"},
            {"category": {"label": "Product", "value": {"id": "p", "name": "Product"}}},
        ]

        self.assertEqual(category_names_for_pages(pages), ["Product", "Order", "Customer"])

    def test_ensure_mapping_chrome_sections_adds_header_footer_and_nav_to_normal_pages(self):
        """Verify that ensure mapping chrome sections adds header footer and nav to normal pages."""
        pages = [{"id": "products", "name": "Products", "type": {"value": "normal"}, "sections": []}]

        next_pages, sections = _ensure_mapping_chrome_sections(pages, [])

        positions = {section["position"] for section in sections}
        self.assertIn("header", positions)
        self.assertIn("footer", positions)
        self.assertTrue(any(section.get("role") == "navigation" for section in sections))
        self.assertTrue(next_pages[0]["sections"])

    def test_ensure_mapping_content_sections_materializes_default_content(self):
        """Verify that ensure mapping content sections materializes default content."""
        pages = [{"id": "products", "name": "Products", "type": {"value": "normal"}, "sections": []}]

        next_pages, sections = _ensure_mapping_content_sections(
            pages,
            [],
            usecase_navigation={},
            model_attrs={"Product": ["name", "price"]},
            model_graph={},
        )

        self.assertEqual(next_pages[0]["primary_model"], "Product")
        self.assertTrue(any(section.get("primary_model") == "Product" for section in sections))

    def test_drop_unreferenced_non_global_sections_keeps_referenced_and_global_only(self):
        """Verify that drop unreferenced non global sections keeps referenced and global only."""
        pages = [{"sections": [{"value": "kept"}]}]
        sections = [
            {"id": "kept", "layout": "card"},
            {"id": "header", "position": "header", "layout": "main-header"},
            {"id": "dropped", "layout": "card"},
        ]

        self.assertEqual(
            [section["id"] for section in _drop_unreferenced_non_global_sections(pages, sections)],
            ["kept", "header"],
        )

    def test_dedupe_agent_header_shells_keeps_first_header_shell(self):
        """Verify that dedupe agent header shells keeps first header shell."""
        pages = [{"sections": [{"value": "header_a"}, {"value": "header_b"}, {"value": "content"}]}]
        sections = [
            {"id": "header_a", "position": "header", "layout": "main-header"},
            {"id": "header_b", "position": "header", "layout": "split-header"},
            {"id": "content", "layout": "card"},
        ]

        next_pages, next_sections = _dedupe_agent_header_shells(pages, sections)

        self.assertEqual([section["id"] for section in next_sections], ["header_a", "content"])
        self.assertEqual(next_pages[0]["sections"], [{"value": "header_a"}, {"value": "content"}])

    def test_inject_chrome_sections_dedupes_ids_and_prepends_refs(self):
        """Verify that inject chrome sections dedupes ids and prepends refs."""
        sections = [{"id": "app_header_template"}]
        section_map = {"app_header_template": sections[0]}
        pages = [{"sections": [{"value": "content"}]}]
        new_sections = [{"id": "app_header_template", "position": "header"}]

        _inject_chrome_sections(new_sections, sections, section_map, pages, prepend=True)

        self.assertEqual(new_sections[0]["id"], "app_header_template_2")
        self.assertEqual(pages[0]["sections"][0], {"value": "app_header_template_2"})

    def test_ensure_candidate_content_structure_dedupes_pages_and_adds_default_section(self):
        """Verify that ensure candidate content structure dedupes pages and adds default section."""
        pages = [
            {"id": "Products", "name": "Products", "type": {"value": "normal"}, "sections": []},
            {"id": "Products Copy", "name": "Products", "type": {"value": "normal"}, "sections": []},
        ]

        next_pages, sections = _ensure_candidate_content_structure(
            pages,
            [],
            model_attrs={"Product": ["name", "price"]},
            candidate_index=0,
            add_missing_content=True,
        )

        self.assertEqual(len(next_pages), 1)
        self.assertEqual(next_pages[0]["primary_model"], "Product")
        self.assertTrue(any(section.get("primary_model") == "Product" for section in sections))

    def test_ensure_usecase_pages_adds_non_background_pages(self):
        """Verify that ensure usecase pages adds non background pages."""
        pages = []
        usecase_navigation = {
            "usecases": [
                {"name": "Browse Products", "page_id": "products", "page_name": "Products", "primary_model": "Product"},
                {"name": "Sync", "page_id": "sync", "page_name": "Sync", "ui_mapping": {"role": "background"}},
            ]
        }

        next_pages = _ensure_usecase_pages(pages, usecase_navigation)

        self.assertEqual([page["id"] for page in next_pages], ["products"])
        self.assertEqual(next_pages[0]["primary_model"], "Product")

    def test_ensure_workflow_entry_sections_adds_start_section_to_page(self):
        """Verify that ensure workflow entry sections adds start section to page."""
        pages = [{"id": "checkout", "name": "Checkout", "sections": []}]
        entries = {"workflow_entry_points": [{"page_id": "checkout", "label": "Start Checkout"}]}

        next_pages, sections = _ensure_workflow_entry_sections(pages, [], entries)

        self.assertEqual(sections[0]["id"], "checkout_workflow_start")
        self.assertEqual(sections[0]["label"], "Start Checkout")
        self.assertEqual(next_pages[0]["sections"], [{"value": "checkout_workflow_start"}])

    def test_ensure_pre_workflow_content_sections_adds_related_collection_before_start(self):
        """Verify that ensure pre workflow content sections adds related collection before start."""
        pages = [{"id": "checkout", "name": "Checkout", "sections": [{"value": "checkout_workflow_start"}]}]
        sections = [{"id": "checkout_workflow_start", "layout": "activity_start", "position": "main"}]
        navigation = {
            "workflow_entry_points": [
                {"page_id": "checkout", "primary_model": "CartItem", "pre_workflow_collections": ["CartItem"]}
            ]
        }

        next_pages, next_sections = _ensure_pre_workflow_content_sections(
            pages,
            sections,
            navigation,
            model_attrs={"CartItem": ["quantity", "unit_price"]},
        )

        self.assertTrue(any(section.get("primary_model") == "CartItem" for section in next_sections))
        self.assertEqual(next_pages[0]["sections"][-1], {"value": "checkout_workflow_start"})

    def test_apply_nav_methods_updates_nav_sections_and_header_icon_links(self):
        """Verify that apply nav methods updates nav sections and header icon links."""
        pages = [{"id": "products", "name": "Products"}]
        sections = [
            {"id": "nav", "layout": "site-nav", "position": "header", "style": {}},
            {"id": "icons", "layout": "icon-actions", "position": "header", "style": {}},
        ]
        usecase_navigation = {
            "nav_bar_pages": ["products"],
            "workflow_entry_points": [{"page_id": "products", "label": "Start"}],
        }

        fixed = _apply_nav_methods(pages, sections, usecase_navigation)

        nav = next(section for section in fixed if section["id"] == "nav")
        self.assertEqual([method["name"] for method in nav["methods"]], ["Products"])
        self.assertIn("icon_links", next(section for section in fixed if section["id"] == "icons")["style"])

    def test_materialize_nav_plan_sections_adds_data_section_and_page_ref(self):
        """Verify that materialize nav plan sections adds data section and page ref."""
        pages = [{"id": "products", "name": "Products", "sections": []}]
        nav_plan = {
            "sections": [
                {
                    "id": "product_cards",
                    "page_id": "products",
                    "role": "object_collection",
                    "primary_model": "Product",
                    "layout": "card",
                    "visible_fields": ["name"],
                    "operations": ["read"],
                }
            ]
        }

        next_pages, sections = _materialize_nav_plan_sections(
            pages,
            [],
            nav_plan,
            model_attrs={"Product": ["name", "price"]},
        )

        self.assertEqual(sections[0]["id"], "product_cards")
        self.assertEqual(sections[0]["attributes"], ["name"])
        self.assertEqual(next_pages[0]["sections"], [{"value": "product_cards"}])


if __name__ == "__main__":
    unittest.main()
