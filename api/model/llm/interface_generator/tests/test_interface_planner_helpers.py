import unittest

from llm.interface_generator.uml_mapping.interface_planner import (
    _activity_form_operations,
    _activity_layout_from_action,
    _actor_model_scope,
    _actor_owned_data_scope,
    _add_association_sections,
    _child_component,
    _collection_component,
    _detail_component,
    _field_category,
    _form_component,
    _is_actor_self_model,
    _is_actor_self_scope,
    _is_create_like_activity,
    _merge_field_names,
    _model_relation_data_scopes,
    _parent_page_data_scope,
    _pick_fields,
    _pick_fields_by_names,
    _pick_layout,
    _plural,
    _relation_data_scopes,
    _section,
    _section_actions,
    _section_data_role,
    _section_fields,
    _semantic_section_attrs,
    _should_add_filter,
    _subordinate_parent,
    _title,
    _workflow_semantics_payload,
    generate_interface_plan,
)


class InterfacePlannerPrimitiveTests(unittest.TestCase):
    def test_plural_and_title_format_page_names(self):
        """Verify that plural and title format page names."""
        self.assertEqual(_plural("Category"), "categories")
        self.assertEqual(_plural("Address"), "address")
        self.assertEqual(_plural("Product"), "products")
        self.assertEqual(_title("product_detail"), "Product Detail")

    def test_field_category_classifies_common_fields(self):
        """Verify that field category classifies common fields."""
        self.assertEqual(_field_category("image_url"), "image")
        self.assertEqual(_field_category("status"), "status")
        self.assertEqual(_field_category("email"), "contact")
        self.assertIsNone(_field_category("misc"))

    def test_pick_fields_by_names_orders_by_role_category(self):
        """Verify that pick fields by names orders by role category."""
        self.assertEqual(
            _pick_fields_by_names(
                ["price", "name", "status", "notes"],
                "object_collection",
                {"object_collection": ["name", "status", "metric"]},
                3,
            ),
            ["name", "status", "price"],
        )

    def test_pick_fields_removes_ids_and_form_audit_fields(self):
        """Verify that pick fields removes ids and form audit fields."""
        model_info = {"attributes": [{"name": "id"}, {"name": "name"}, {"name": "created_at"}, {"name": "price"}]}

        self.assertEqual(_pick_fields(model_info, "object_collection"), ["name", "price", "created_at"])
        self.assertEqual(_pick_fields(model_info, "object_form"), ["name", "price"])

    def test_component_helpers_choose_domain_components(self):
        """Verify that component helpers choose domain components."""
        self.assertEqual(_collection_component("Category", "gallery"), "CategoryTileGrid")
        self.assertEqual(_collection_component("Order", "table"), "DataTable")
        self.assertEqual(_detail_component("Customer"), "ProfilePanel")
        self.assertEqual(_detail_component("Invoice"), "DocumentPanel")
        self.assertEqual(_form_component("Address", "checkout"), "AddressForm")
        self.assertEqual(_child_component("OrderLine", "cart"), "LineItemList")

    def test_pick_layout_uses_role_override_and_model_semantics(self):
        """Verify that pick layout uses role override and model semantics."""
        self.assertEqual(_pick_layout({}, "detail_workspace"), "detail")
        self.assertEqual(_pick_layout({}, "collection_workspace", semantic_override="map"), "map")
        self.assertEqual(_pick_layout({"attributes": [{"name": "name"}]}, "collection_workspace", model="Customer"), "gallery")
        self.assertEqual(
            _pick_layout({"layout_score": {"table": 0.9, "list": 0.2}, "attributes": [{"name": f"f{i}"} for i in range(10)]}, "collection_workspace"),
            "table",
        )

    def test_activity_helpers_classify_action_layout_and_operations(self):
        """Verify that activity helpers classify action layout and operations."""
        self.assertEqual(_activity_layout_from_action("Review application", ""), ("detail", "object_detail", "DetailPanel"))
        self.assertEqual(_activity_layout_from_action("Select product", ""), ("list", "object_collection", "ObjectList"))
        self.assertEqual(_activity_form_operations("Update status"), ["update"])
        self.assertEqual(_activity_form_operations("Submit application"), ["create"])
        self.assertTrue(_is_create_like_activity("Book appointment"))

    def test_field_merge_and_semantic_attrs_preserve_order_and_readonly(self):
        """Verify that field merge and semantic attrs preserve order and readonly."""
        self.assertEqual(_merge_field_names(["status"], ["status", "name"]), ["status", "name"])
        attrs = _semantic_section_attrs([{"name": "status", "type": "str"}], ["status"], ["name"])
        self.assertEqual(attrs, [{"name": "status", "type": "str", "readonly": True}, {"name": "name", "readonly": False}])

    def test_workflow_semantics_payload_includes_non_empty_semantics_and_fields(self):
        """Verify that workflow semantics payload includes non empty semantics and fields."""
        payload = _workflow_semantics_payload(
            {"intent": "check", "condition": {"field": "status"}, "false_next": ""},
            ["status"],
            ["name"],
        )

        self.assertEqual(payload["intent"], "check")
        self.assertEqual(payload["condition"], {"field": "status"})
        self.assertEqual(payload["readonly_fields"], ["status"])
        self.assertEqual(payload["editable_fields"], ["name"])

    def test_actor_scope_helpers_use_semantic_override_or_identity(self):
        """Verify that actor scope helpers use semantic override or identity."""
        overrides = {"actor_model_scopes": {"Patient": "assigned"}}

        self.assertEqual(_actor_model_scope("Patient", "Patient"), "self_profile")
        self.assertEqual(_actor_model_scope("Doctor", "Patient", overrides), "assigned")
        self.assertTrue(_is_actor_self_scope("Patient", "Patient"))
        self.assertEqual(_actor_owned_data_scope("Patient", "Patient")["mode"], "actor_owned")
        self.assertTrue(_is_actor_self_model("Patient", "Patient"))

    def test_relation_scope_helpers_mark_actor_and_parent_page_context(self):
        """Verify that relation scope helpers mark actor and parent page context."""
        self.assertEqual(_parent_page_data_scope("Product", "Product")["mode"], "parent_page_instance")
        scopes = _relation_data_scopes("Customer", ["Customer", "Product"], page_primary_model="Product")
        self.assertEqual(scopes["Customer"]["mode"], "actor_owned")
        self.assertEqual(scopes["Product"]["mode"], "parent_page_instance")
        model_scopes = _model_relation_data_scopes(
            "Customer",
            {"attributes": [{"name": "Customer", "model": "Customer"}], "associations": [{"model": "Product"}]},
            page_primary_model="Product",
        )
        self.assertEqual(set(model_scopes), {"Customer", "Product"})

    def test_should_add_filter_for_large_or_status_collections(self):
        """Verify that should add filter for large or status collections."""
        self.assertFalse(_should_add_filter("gallery", {}, "collection_workspace"))
        self.assertTrue(_should_add_filter("list", {"attributes": [{"name": "status"}]}, "collection_workspace"))

    def test_section_data_role_and_actions_cover_main_modes(self):
        """Verify that section data role and actions cover main modes."""
        self.assertEqual(_section_data_role("object_form", "form", ["create"]), "create_record")
        self.assertEqual(_section_data_role("object_collection", "list", ["select"]), "select_existing")
        self.assertEqual(_section_actions("Product", "display_records", ["read"])[0]["type"], "navigate")
        self.assertEqual(_section_actions("Product", "select_existing", ["select"])[0]["type"], "select")
        self.assertEqual(_section_actions("Product", "create_record", ["create"])[0]["label"], "Create")

    def test_section_fields_marks_related_and_editable_modes(self):
        """Verify that section fields marks related and editable modes."""
        fields = _section_fields("Order", ["Product.name", "status"], ["status"], [], "show_record")

        self.assertEqual(fields[0], {"model": "Product", "name": "name", "mode": "readonly", "source": "related"})
        self.assertEqual(fields[1], {"model": "Order", "name": "status", "mode": "editable", "source": "primary"})

    def test_section_builds_complete_section_with_scope_and_actions(self):
        """Verify that section builds complete section with scope and actions."""
        section = _section(
            page_id="products",
            section_id="product_cards",
            role="object_collection",
            name="Products",
            layout="list",
            component="ObjectList",
            model="Product",
            visible=["name"],
            editable=[],
            operations=["read"],
            data_scope={"mode": "actor_owned"},
        )

        self.assertEqual(section["data_role"], "display_records")
        self.assertEqual(section["style"]["data_scope"], {"mode": "actor_owned"})
        self.assertEqual(section["actions"][0]["type"], "navigate")

    def test_subordinate_parent_detects_asset_child_models(self):
        """Verify that subordinate parent detects asset child models."""
        graph = {"ProductImage": {"associations": [{"model": "Product"}]}}

        self.assertEqual(_subordinate_parent("ProductImage", graph, {"Product"}), "Product")
        self.assertIsNone(_subordinate_parent("Seller", {}, {"Product"}))

    def test_add_association_sections_adds_composition_subordinate_and_related_sections(self):
        """Verify that add association sections adds composition subordinate and related sections."""
        added = []
        graph = {
            "ProductImage": {"attributes": [{"name": "image_url"}], "associations": [{"model": "Product"}]},
            "Review": {"attributes": [{"name": "rating"}]},
            "Spec": {"attributes": [{"name": "name"}]},
        }
        model_info = {
            "compositions_owned": [{"model": "Spec"}],
            "associations": [{"model": "Review", "cardinality": "1-many"}],
        }

        _add_association_sections(
            "product_detail",
            "Product",
            model_info,
            graph,
            accessible={"Review"},
            subordinate_models={"ProductImage"},
            existing_section_ids=set(),
            add_section_fn=added.append,
            max_sections=3,
        )

        self.assertEqual([section["primary_model"] for section in added], ["Spec", "ProductImage", "Review"])


class InterfacePlannerPlanTests(unittest.TestCase):
    def test_generate_interface_plan_builds_collection_and_sections(self):
        """Verify that generate interface plan builds collection and sections."""
        plan = generate_interface_plan(
            {
                "actor_name": "Customer",
                "actor_intel": {
                    "target_permissions": {"Product": ["read"]},
                    "target_use_cases": [
                        {
                            "name": "Browse Products",
                            "primary_model": "Product",
                            "permissions": ["read"],
                            "page_role": "collection_workspace",
                        }
                    ],
                },
                "model_graph": {
                    "Product": {
                        "attributes": [{"name": "name"}, {"name": "price"}],
                    }
                },
            }
        )

        self.assertEqual(plan["pages"][0]["primary_model"], "Product")
        self.assertEqual(plan["sections"][0]["primary_model"], "Product")
        self.assertEqual(plan["summary"]["page_count"], 1)


if __name__ == "__main__":
    unittest.main()
