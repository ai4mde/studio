import unittest

from llm.interface_generator.uml_mapping.navigation_planner import (
    _activity_layout,
    _child_section,
    _component_for_section,
    _editable_fields_for_model,
    _field_layout_for_component,
    _is_strict_child_collection_model,
    _layout_for_page_role,
    _operations_for_model,
    _operations_for_page,
    _page_name,
    _pick_fields,
    _section_for_page,
    _section_id,
    _sections_for_activity_step,
    build_navigation_plan,
)


class NavigationPlannerPrimitiveTests(unittest.TestCase):
    def test_section_id_normalizes_names(self):
        """Verify that section id normalizes names."""
        self.assertEqual(_section_id("Order Detail"), "order_detail")
        self.assertEqual(_section_id(""), "section")

    def test_page_name_humanizes_page_id(self):
        """Verify that page name humanizes page id."""
        self.assertEqual(_page_name("order_detail"), "Order_Detail")

    def test_is_strict_child_collection_model_detects_line_items(self):
        """Verify that is strict child collection model detects line items."""
        self.assertTrue(_is_strict_child_collection_model("OrderLine"))
        self.assertFalse(_is_strict_child_collection_model("Product"))

    def test_pick_fields_prioritizes_role_fields_and_excludes_id(self):
        """Verify that pick fields prioritizes role fields and excludes id."""
        self.assertEqual(
            _pick_fields({"Product": ["id", "name", "price", "status"]}, "Product", "object_collection", 3),
            ["name", "status", "price"],
        )

    def test_layout_for_page_role_uses_roles_and_page_id(self):
        """Verify that layout for page role uses roles and page id."""
        self.assertEqual(_layout_for_page_role({"roles": ["detail_workspace"]}), "detail")
        self.assertEqual(_layout_for_page_role({"roles": ["collection_workspace"], "id": "product_catalog"}), "gallery")
        self.assertEqual(_layout_for_page_role({"roles": ["collection_workspace"], "id": "order_history"}), "list")

    def test_operations_for_model_maps_permissions_to_crud(self):
        """Verify that operations for model maps permissions to crud."""
        self.assertEqual(
            _operations_for_model("Product", {"Product": ["create", "delete"]}),
            ["view", "create", "delete"],
        )

    def test_operations_for_page_select_existing_limits_to_view_select(self):
        """Verify that operations for page select existing limits to view select."""
        self.assertEqual(
            _operations_for_page(
                "Product",
                {"Product": ["create", "update"]},
                {"roles": ["collection_workspace"], "name": "Select Product", "operation_kind": "select_existing"},
            ),
            ["view", "select"],
        )

    def test_editable_fields_for_model_requires_create_or_update(self):
        """Verify that editable fields for model requires create or update."""
        attrs = {"Product": ["id", "name", "price", "created_at"]}

        self.assertEqual(_editable_fields_for_model(attrs, "Product", "object_form", ["view"]), [])
        self.assertEqual(_editable_fields_for_model(attrs, "Product", "object_form", ["update"]), ["name", "price"])

    def test_component_for_section_uses_role_layout_and_model(self):
        """Verify that component for section uses role layout and model."""
        self.assertEqual(_component_for_section("child_collection", "list", "OrderLine"), "LineItemList")
        self.assertEqual(_component_for_section("object_detail", "detail", "Customer"), "ProfilePanel")
        self.assertEqual(_component_for_section("object_form", "form", "Address"), "AddressForm")
        self.assertEqual(_component_for_section("object_collection", "gallery", "Category"), "CategoryTileGrid")
        self.assertEqual(_component_for_section("object_collection", "table", "Product"), "DataTable")

    def test_field_layout_for_component_maps_known_slots(self):
        """Verify that field layout for component maps known slots."""
        card = _field_layout_for_component("CardGrid", ["image_url", "name", "brand", "price", "rating"])
        self.assertEqual(card["image"], "image_url")
        self.assertEqual(card["title"], "name")
        self.assertEqual(card["primary"], "price")

        table = _field_layout_for_component("DataTable", ["name", "price"])
        self.assertEqual(table["columns"][0], {"field": "name", "label": "Name"})

        form = _field_layout_for_component("ObjectForm", ["name"])
        self.assertEqual(form["groups"], [{"title": "Details", "fields": ["name"]}])


class NavigationPlannerSectionTests(unittest.TestCase):
    def test_section_for_page_returns_none_without_model(self):
        """Verify that section for page returns none without model."""
        self.assertIsNone(_section_for_page({"id": "home"}, {}))

    def test_section_for_page_builds_primary_section(self):
        """Verify that section for page builds primary section."""
        section = _section_for_page(
            {"id": "products", "name": "Products", "roles": ["collection_workspace"], "primary_model": "Product"},
            {"Product": ["name", "price"]},
            {"Product": ["read"]},
        )

        self.assertEqual(section["id"], "products_product_object_collection")
        self.assertEqual(section["layout"], "gallery")
        self.assertEqual(section["component"], "CardGrid")
        self.assertEqual(section["visible_fields"], ["name", "price"])

    def test_child_section_adds_related_product_fields_and_query_source(self):
        """Verify that child section adds related product fields and query source."""
        section = _child_section(
            "cart",
            "CartItem",
            {"CartItem": ["quantity", "unit_price"], "Product": ["name", "image_url", "price"]},
            related_models=["Product"],
        )

        self.assertEqual(section["component"], "LineItemList")
        self.assertIn("Product.name", section["related_visible_fields"])
        self.assertEqual(section["data_source"]["from"], {"model": "CartItem"})

    def test_activity_layout_detects_list_form_and_detail(self):
        """Verify that activity layout detects list form and detail."""
        self.assertEqual(_activity_layout("Select product"), "list")
        self.assertEqual(_activity_layout("Enter shipping address"), "form")
        self.assertEqual(_activity_layout("Confirm status"), "form")

    def test_sections_for_activity_step_builds_sections_for_known_models(self):
        """Verify that sections for activity step builds sections for known models."""
        sections = _sections_for_activity_step(
            {"page_id": "checkout", "activity_node_name": "Enter Address", "classes": ["Address"]},
            {"Address": ["street", "city"]},
        )

        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]["role"], "object_form")
        self.assertEqual(sections[0]["editable_fields"], ["street", "city"])

    def test_build_navigation_plan_creates_pages_sections_operations_and_workflows(self):
        """Verify that build navigation plan creates pages sections operations and workflows."""
        plan = build_navigation_plan(
            {
                "actor_permissions": {"Product": ["read"], "CartItem": ["read", "update"]},
                "nav_bar_pages": ["products"],
                "pages": [
                    {
                        "page_id": "products",
                        "page_name": "Products",
                        "roles": ["collection_workspace"],
                        "primary_model": "Product",
                    }
                ],
                "workflow_entry_points": [
                    {
                        "page_id": "cart",
                        "label": "Checkout",
                        "button_label": "Start Checkout",
                        "pre_workflow_collections": ["CartItem"],
                        "related_models": ["Product"],
                    }
                ],
                "usecases": [
                    {
                        "name": "Add to Cart",
                        "primary_model": "Product",
                        "ui_mapping": {"role": "inline_operation", "page_id": "products", "target_model": "CartItem"},
                    }
                ],
            },
            model_attrs={
                "Product": ["name", "price", "image_url"],
                "CartItem": ["quantity", "unit_price"],
            },
            workflow_steps=[{"page_id": "checkout_step", "page_name": "Checkout Step", "activity_node_name": "Enter Address", "classes": ["CartItem"]}],
        )

        self.assertIn("products", [page["id"] for page in plan["pages"]])
        self.assertTrue(any(section["primary_model"] == "Product" for section in plan["sections"]))
        self.assertEqual(plan["operations"][0]["usecase"], "Add to Cart")
        self.assertEqual(plan["workflows"][0]["entry_label"], "Start Checkout")


if __name__ == "__main__":
    unittest.main()
