import unittest

from llm.interface_generator.section_utils import (
    _append_query_filter,
    _attr_name,
    _attr_type,
    _bridge_child_model,
    _canonical_model_name,
    _canonical_page_type,
    _default_join_for_models,
    _ensure_default_section_methods,
    _ensure_item_click_navigation,
    _ensure_logical_related_sections,
    _ensure_section_data_relationships,
    _ensure_workflow_pages,
    _fallback_model_for_page,
    _field_kind,
    _field_list,
    _finalize_data_section_bindings,
    _guess_relation_field,
    _infer_page_type_value,
    _infer_section_component,
    _infer_section_layout,
    _is_direct_child_relation,
    _is_direct_single_relation,
    _is_select_existing_text,
    _merge_section_attrs,
    _model_field_names,
    _model_graph_attr_names,
    _navigation_methods,
    _normalize_activity_action_sections,
    _normalize_chrome_sections,
    _normalize_field_layout,
    _normalize_layout_alias,
    _normalize_section_operations,
    _normalize_select_existing_sections,
    _page_type_value,
    _query_filter_exists,
    _readonly_related_attr,
    _ref_id,
    _related_models_from_attrs,
    _relation_cardinality,
    _section_is_collection,
    _section_is_data,
    _snake_name,
    _supported_field_slots,
    _workflow_icon_links,
    _workflow_task_section,
)


class SectionUtilsPrimitiveTests(unittest.TestCase):
    def test_normalize_section_operations_accepts_dict_string_and_list(self):
        """Verify that normalize section operations accepts dict string and list."""
        self.assertEqual(_normalize_section_operations({"add": "yes", "remove": True}), {"create": True, "update": False, "delete": True, "select": False})
        self.assertEqual(_normalize_section_operations("create edit select"), {"create": True, "update": True, "delete": False, "select": True})
        self.assertEqual(_normalize_section_operations(["remove"]), {"create": False, "update": False, "delete": True, "select": False})

    def test_normalize_layout_alias_maps_aliases_and_calendar(self):
        """Verify that normalize layout alias maps aliases and calendar."""
        self.assertEqual(_normalize_layout_alias("nav"), "nav-links")
        self.assertEqual(_normalize_layout_alias("calendar"), "list")
        self.assertEqual(_normalize_layout_alias(["unknown", "table"]), "table")

    def test_page_type_helpers_normalize_and_infer(self):
        """Verify that page type helpers normalize and infer."""
        self.assertEqual(_page_type_value({"type": {"value": "Activity"}}), "activity")
        self.assertEqual(_infer_page_type_value({"name": "Workflow Step"}), "activity")
        self.assertEqual(_infer_page_type_value({"name": "Home"}), "normal")
        self.assertEqual(_canonical_page_type("activity"), {"value": "activity", "label": "Activity"})

    def test_ref_navigation_and_workflow_links_helpers(self):
        """Verify that ref navigation and workflow links helpers."""
        self.assertEqual(_ref_id({"value": "section"}), "section")
        self.assertEqual(_navigation_methods(["Products"])[0]["action"], "navigate")
        links = _workflow_icon_links({"workflow_entry_points": [{"page_id": "checkout", "button_label": "Start"}]}, {"checkout": {"name": "Checkout"}})
        self.assertEqual(links, [{"page": "Checkout", "label": "Start", "icon": "task"}])

    def test_infer_section_component_uses_layout_and_model_traits(self):
        """Verify that infer section component uses layout and model traits."""
        self.assertEqual(_infer_section_component({"layout": "main-header"}), "HeaderTemplate")
        self.assertEqual(_infer_section_component({"layout": "form", "primary_model": "Address"}), "AddressForm")
        self.assertEqual(_infer_section_component({"layout": "gallery", "attributes": ["image"]}), "ImageCardGrid")
        self.assertEqual(_infer_section_component({"layout": "table"}), "DataTable")

    def test_select_existing_helpers_convert_search_forms_to_select_cards(self):
        """Verify that select existing helpers convert search forms to select cards."""
        self.assertTrue(_is_select_existing_text("Select existing product"))
        pages = [{"id": "select_product", "sections": [{"value": "form"}]}]
        sections = [{"id": "form", "layout": "form", "role": "object_form", "primary_model": "Product", "attributes": ["name"]}]

        fixed = _normalize_select_existing_sections(pages, sections)

        self.assertEqual(fixed[0]["layout"], "card")
        self.assertEqual(fixed[0]["operations"], {"create": False, "update": False, "delete": False, "select": True})

    def test_attr_and_field_helpers_classify_fields(self):
        """Verify that attr and field helpers classify fields."""
        self.assertEqual(_attr_name({"name": "image_url"}), "image_url")
        self.assertEqual(_attr_type({"type": "IMAGE"}), "image")
        self.assertEqual(_field_kind("image_url"), "media")
        self.assertEqual(_field_kind("password"), "hidden")
        self.assertEqual(_field_kind("name"), "title")
        self.assertEqual(_supported_field_slots({"component": "DataTable"}), {"columns", "hidden"})
        self.assertEqual(_field_list([{"field": "name"}, "price", {}]), ["name", "price"])

    def test_normalize_field_layout_derives_slots_and_cleans_styles(self):
        """Verify that normalize field layout derives slots and cleans styles."""
        section = {
            "layout": "card",
            "component": "CardGrid",
            "primary_model": "Product",
            "attributes": [{"name": "image_url", "type": "image"}, {"name": "name"}, {"name": "price"}, {"name": "internal_token"}],
            "field_layout": {"field_styles": {"name": {"order": "2", "align": "center"}, "missing": {"order": 1}}},
        }

        layout = _normalize_field_layout(section)

        self.assertEqual(layout["image"], "image_url")
        self.assertEqual(layout["title"], "name")
        self.assertEqual(layout["primary"], "price")
        self.assertIn("internal_token", layout["hidden"])
        self.assertEqual(layout["field_styles"]["name"], {"order": 2, "align": "center"})

    def test_model_field_names_prefers_media_and_named_fields(self):
        """Verify that model field names prefers media and named fields."""
        self.assertEqual(
            _model_field_names({"Product": ["id", "description", "price", "name", "image_url"]}, "Product", 4),
            ["image_url", "name", "price", "description"],
        )

    def test_finalize_data_section_bindings_normalizes_model_attrs_component_and_field_layout(self):
        """Verify that finalize data section bindings normalizes model attrs component and field layout."""
        sections = [{"id": "s", "layout": "calendar", "primary_model": "product", "attributes": ["bad"]}]

        fixed = _finalize_data_section_bindings(sections, {"Product": ["name", "price"]})

        self.assertEqual(fixed[0]["layout"], "list")
        self.assertEqual(fixed[0]["primary_model"], "Product")
        self.assertEqual(fixed[0]["attributes"], ["name", "price"])
        self.assertEqual(fixed[0]["component"], "ObjectList")

    def test_model_graph_and_relation_helpers(self):
        """Verify that model graph and relation helpers."""
        graph = {
            "OrderLine": {"attributes": [{"name": "quantity"}], "associations": [{"model": "Order", "cardinality": "many-1"}, {"model": "Product", "cardinality": "many-1"}]},
            "Order": {"associations": [{"model": "OrderLine", "cardinality": "1-many"}]},
            "Product": {},
        }

        self.assertEqual(_model_graph_attr_names(graph, "OrderLine"), {"quantity"})
        self.assertEqual(_canonical_model_name("order_line", graph), "OrderLine")
        self.assertEqual(_relation_cardinality(graph, "Order", "OrderLine"), "1-many")
        self.assertTrue(_is_direct_single_relation(graph, "OrderLine", "Order"))
        self.assertTrue(_is_direct_child_relation(graph, "Order", "OrderLine"))
        self.assertEqual(_bridge_child_model(graph, "Order", "Product"), "OrderLine")

    def test_related_attr_and_attr_merge_helpers(self):
        """Verify that related attr and attr merge helpers."""
        self.assertTrue(_readonly_related_attr("Product.name")["readonly"])
        self.assertEqual(_merge_section_attrs(["name"], [{"name": "name"}, "price"]), ["name", "price"])

    def test_snake_relation_and_join_helpers(self):
        """Verify that snake relation and join helpers."""
        self.assertEqual(_snake_name("OrderLine"), "order_line")
        self.assertEqual(_guess_relation_field("OrderLine", "Order", {"OrderLine": ["order_id"]}), "order_id")
        self.assertEqual(_related_models_from_attrs({"primary_model": "OrderLine", "attributes": ["Product.name"]}, {"Product": ["name"]}), ["Product"])
        self.assertEqual(_default_join_for_models("OrderLine", "Product")["on"], "OrderLine.product_id = Product.id")

    def test_section_and_query_helpers(self):
        """Verify that section and query helpers."""
        section = {"layout": "card", "primary_model": "Product", "attributes": ["name"]}
        self.assertTrue(_section_is_data(section))
        self.assertTrue(_section_is_collection(section))
        query = {}
        _append_query_filter(query, "product_id", "request.GET.instance_id_Product")
        self.assertTrue(_query_filter_exists(query, "product_id", "request.GET.instance_id_Product"))
        _ensure_item_click_navigation(section, "Product Detail")
        self.assertEqual(section["behavior"]["item_click"]["target_page"], "Product Detail")
        _ensure_default_section_methods(section)
        self.assertEqual(section["methods"][0]["name"], "Export CSV")

    def test_infer_section_layout_and_fallback_model(self):
        """Verify that infer section layout and fallback model."""
        self.assertEqual(_infer_section_layout({"name": "Product Detail"}), "detail")
        self.assertEqual(_infer_section_layout({"name": "Search Products"}, 0), "card")
        self.assertEqual(_fallback_model_for_page({"name": "Products"}, {"Product", "User"}), "Product")


class SectionUtilsWorkflowAndRelationshipTests(unittest.TestCase):
    def test_workflow_task_section_builds_task_content(self):
        """Verify that workflow task section builds task content."""
        section = _workflow_task_section(
            {"page_id": "checkout", "activity_node_name": "Enter Address"},
            "Address",
            {"Address": ["street", "city"]},
        )

        self.assertEqual(section["id"], "checkout_address_task_content")
        self.assertEqual(section["layout"], "form")
        self.assertTrue(section["operations"]["create"])

    def test_ensure_workflow_pages_adds_activity_page_content_and_continue_action(self):
        """Verify that ensure workflow pages adds activity page content and continue action."""
        pages, sections = _ensure_workflow_pages(
            [],
            [],
            [{"activity_node_id": "node1", "activity_node_name": "Enter Address", "page_id": "enter_address", "page_name": "Workflow_Enter_Address", "classes": ["Address"]}],
            model_attrs={"Address": ["street", "city"]},
        )

        self.assertEqual(pages[0]["type"], {"value": "activity", "label": "Activity"})
        self.assertTrue(any(section.get("primary_model") == "Address" for section in sections))
        self.assertTrue(any(section.get("layout") == "activity_action" for section in sections))

    def test_normalize_activity_action_sections_normalizes_and_dedupes_buttons(self):
        """Verify that normalize activity action sections normalizes and dedupes buttons."""
        pages = [{"type": {"value": "activity"}, "sections": [{"value": "a1"}, {"value": "a2"}]}]
        sections = [
            {"id": "a1", "layout": "activity_action", "workflow": {"action": "complete"}},
            {"id": "a2", "layout": "activity_action", "workflow": {"action": "other"}},
            {"id": "data_action", "layout": "activity_action", "primary_model": "Product", "operations": {"update": True}},
        ]

        fixed = _normalize_activity_action_sections(pages, sections)

        self.assertEqual([section["id"] for section in fixed], ["a1", "data_action"])
        self.assertEqual(fixed[1]["layout"], "list")

    def test_normalize_chrome_sections_removes_data_shape_from_chrome(self):
        """Verify that normalize chrome sections removes data shape from chrome."""
        fixed = _normalize_chrome_sections(
            [{"id": "h", "position": "header", "layout": "card", "primary_model": "Product", "attributes": ["name"], "operations": {"update": True}}]
        )

        self.assertEqual(fixed[0]["layout"], "main-header")
        self.assertEqual(fixed[0]["primary_model"], "")
        self.assertEqual(fixed[0]["component"], "HeaderTemplate")

    def test_ensure_logical_related_sections_moves_one_to_many_fields_to_child_section(self):
        """Verify that ensure logical related sections moves one to many fields to child section."""
        pages = [{"id": "member_detail", "sections": [{"value": "member_detail"}]}]
        sections = [
            {
                "id": "member_detail",
                "page_id": "member_detail",
                "layout": "detail",
                "role": "object_detail",
                "primary_model": "Member",
                "attributes": ["name", "Book.title"],
            }
        ]
        graph = {
            "Member": {"attributes": [{"name": "name"}], "associations": [{"model": "Loan", "cardinality": "1-many"}]},
            "Loan": {"attributes": [{"name": "loan_date"}], "associations": [{"model": "Member", "cardinality": "many-1"}, {"model": "Book", "cardinality": "many-1"}]},
            "Book": {"attributes": [{"name": "title"}]},
        }

        fixed_pages, fixed_sections = _ensure_logical_related_sections(pages, sections, graph)

        self.assertEqual(fixed_sections[0]["attributes"], ["name"])
        self.assertTrue(any(section.get("primary_model") == "Loan" for section in fixed_sections))
        self.assertEqual(fixed_pages[0]["sections"][1]["value"], "member_detail_loan_child_collection")

    def test_ensure_section_data_relationships_populates_queries_joins_and_navigation(self):
        """Verify that ensure section data relationships populates queries joins and navigation."""
        pages = [
            {"id": "product_list", "name": "Products", "primary_model": "Product", "sections": [{"value": "cards"}]},
            {"id": "product_detail", "name": "Product Detail", "primary_model": "Product", "sections": [{"value": "detail"}, {"value": "reviews"}]},
        ]
        sections = [
            {"id": "cards", "layout": "card", "role": "object_collection", "primary_model": "Product", "attributes": ["name"], "query": {}},
            {"id": "detail", "layout": "detail", "role": "object_detail", "primary_model": "Product", "attributes": ["name"], "query": {}},
            {"id": "reviews", "layout": "list", "role": "child_collection", "primary_model": "Review", "attributes": ["Product.name", "rating"], "query": {}},
        ]

        _, fixed_sections = _ensure_section_data_relationships(
            pages,
            sections,
            {"Product": ["name"], "Review": ["product_id", "rating"]},
        )

        cards = next(section for section in fixed_sections if section["id"] == "cards")
        reviews = next(section for section in fixed_sections if section["id"] == "reviews")
        self.assertEqual(cards["behavior"]["item_click"]["target_page"], "Product Detail")
        self.assertEqual(reviews["relation_field"], "product_id")
        self.assertEqual(reviews["data_source"]["joins"][0]["model"], "Product")


if __name__ == "__main__":
    unittest.main()
