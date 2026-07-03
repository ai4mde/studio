import unittest

from llm.interface_generator.uml_mapping.usecase_workflow import (
    _activity_action_indexes,
    _activity_layout_for_step,
    _activity_models_for_step,
    _actor_refs,
    _build_activity_diagrams,
    _build_usecase_navigation,
    _humanize_action_label,
    _infer_usecase_model,
    _infer_usecase_permissions,
    _is_child_collection_model,
    _name_tokens,
    _nav_mapping_for_usecase,
    _plural_page_id,
    _rank_models_for_text,
    _ref_list,
    _ref_values,
    _usecase_has_workflow_entry,
    _workflow_plan,
)


class UsecaseWorkflowPrimitiveTests(unittest.TestCase):
    def test_ref_values_extracts_unique_refs_from_dicts_and_scalars(self):
        """Verify that ref values extracts unique refs from dicts and scalars."""
        self.assertEqual(_ref_values([{"id": "a"}, {"value": "b"}, "c", {"id": "a"}]), {"a", "b", "c"})

    def test_ref_list_preserves_order_and_dedupes(self):
        """Verify that ref list preserves order and dedupes."""
        self.assertEqual(_ref_list([{"id": "a"}, {"value": "b"}, "a"]), ["a", "b"])

    def test_name_tokens_splits_camel_case_and_singularizes(self):
        """Verify that name tokens splits camel case and singularizes."""
        self.assertEqual(_name_tokens("OrderLines"), {"order", "lines", "line"})

    def test_rank_models_for_text_uses_overlap_substring_and_collection_bonus(self):
        """Verify that rank models for text uses overlap substring and collection bonus."""
        self.assertEqual(
            _rank_models_for_text("Manage order line items", ["Product", "OrderLine"], prefer_collections=True)[0],
            "OrderLine",
        )

    def test_infer_usecase_model_prefers_explicit_class_then_text_rank(self):
        """Verify that infer usecase model prefers explicit class then text rank."""
        classifiers = {"product-id": {"name": "Product"}}

        self.assertEqual(_infer_usecase_model("Browse", ["product-id"], classifiers, {"Product"}), "Product")
        self.assertEqual(_infer_usecase_model("Browse Orders", [], {}, {"Order", "Product"}), "Order")

    def test_humanize_action_label_removes_generic_verbs_and_detects_workflow_starts(self):
        """Verify that humanize action label removes generic verbs and detects workflow starts."""
        self.assertEqual(_humanize_action_label("View Product Detail"), "Product Detail")
        self.assertEqual(_humanize_action_label("Submit Application"), "Start")
        self.assertEqual(_humanize_action_label("", "Go"), "Go")

    def test_is_child_collection_model_detects_line_item_models(self):
        """Verify that is child collection model detects line item models."""
        self.assertTrue(_is_child_collection_model("Order Line"))
        self.assertFalse(_is_child_collection_model("Product"))

    def test_plural_page_id_pluralizes_y_and_s_suffixes(self):
        """Verify that plural page id pluralizes y and s suffixes."""
        self.assertEqual(_plural_page_id("Category"), "categories")
        self.assertEqual(_plural_page_id("Address"), "address")
        self.assertEqual(_plural_page_id("Product"), "products")

    def test_nav_mapping_for_usecase_classifies_common_usecase_shapes(self):
        """Verify that nav mapping for usecase classifies common usecase shapes."""
        self.assertEqual(
            _nav_mapping_for_usecase({"name": "Browse Products", "primary_model": "Product"})["role"],
            "collection_workspace",
        )
        self.assertEqual(
            _nav_mapping_for_usecase({"name": "View Product Detail", "primary_model": "Product"})["role"],
            "detail_workspace",
        )
        self.assertEqual(
            _nav_mapping_for_usecase({"name": "Add Review", "primary_model": "Product", "class_names": ["Product", "Review"]})["role"],
            "inline_operation",
        )
        self.assertEqual(
            _nav_mapping_for_usecase({"name": "Submit Order", "primary_model": "Order"}, workflow_entry=True)["role"],
            "workflow_entry",
        )

    def test_usecase_has_workflow_entry_uses_refs_and_name_intent(self):
        """Verify that usecase has workflow entry uses refs and name intent."""
        self.assertTrue(_usecase_has_workflow_entry({"name": "Any", "activities": ["start"]}, True, {"start"}, {"start"}))
        self.assertFalse(_usecase_has_workflow_entry({"name": "Browse Products"}, True, set(), set()))
        self.assertTrue(_usecase_has_workflow_entry({"name": "Submit Application"}, True, set(), set()))

    def test_infer_usecase_permissions_maps_name_to_crud(self):
        """Verify that infer usecase permissions maps name to crud."""
        self.assertEqual(_infer_usecase_permissions("View Product"), ["view"])
        self.assertEqual(_infer_usecase_permissions("Submit Review"), ["view", "create"])
        self.assertEqual(_infer_usecase_permissions("Manage Order Items"), ["view", "create", "update", "delete"])
        self.assertEqual(_infer_usecase_permissions("Cancel Order"), ["view", "delete"])

    def test_activity_layout_for_step_maps_task_text_to_layout(self):
        """Verify that activity layout for step maps task text to layout."""
        self.assertEqual(_activity_layout_for_step("Select Product", "Product"), "card")
        self.assertEqual(_activity_layout_for_step("Enter Address", "Address"), "form")
        self.assertEqual(_activity_layout_for_step("Review Order Lines", "OrderLine"), "list")
        self.assertEqual(_activity_layout_for_step("Order Confirmation", "Order"), "detail")


class UsecaseWorkflowStructuredTests(unittest.TestCase):
    def test_build_activity_diagrams_resolves_nodes_edges_and_actor_names(self):
        """Verify that build activity diagrams resolves nodes edges and actor names."""
        system_data = {
            "classifiers": [
                {"id": "actor", "data": {"type": "actor", "name": "Customer"}},
                {"id": "action", "data": {"type": "action", "name": "Submit Order", "actorNode": "actor"}},
                {"id": "final", "data": {"type": "final", "name": "Final"}},
            ],
            "relations": [
                {"id": "rel", "source": "action", "target": "final", "data": {"type": "controlflow"}}
            ],
            "diagrams": [
                {
                    "id": "activity",
                    "type": "activity",
                    "nodes": [{"id": "n1", "cls": "action"}, {"id": "n2", "cls": "final"}],
                    "edges": [{"id": "edge", "rel": "rel"}],
                }
            ],
        }

        diagrams = _build_activity_diagrams(system_data)

        self.assertEqual(diagrams[0]["nodes"][0]["cls"]["actorNodeName"], "Customer")
        self.assertEqual(diagrams[0]["edges"][0]["source_ptr"], "n1")

    def test_actor_refs_includes_actor_classifier_and_usecase_node_refs(self):
        """Verify that actor refs includes actor classifier and usecase node refs."""
        system_data = {
            "classifiers": [{"id": "actor-cls", "data": {"type": "actor", "name": "Customer"}}],
            "diagrams": [{"type": "usecase", "nodes": [{"id": "actor-node", "cls": "actor-cls"}]}],
        }

        self.assertEqual(_actor_refs(system_data, "actor-cls", "Customer"), {"actor-cls", "actor-node"})

    def test_activity_action_indexes_finds_first_actions(self):
        """Verify that activity action indexes finds first actions."""
        diagram = {
            "id": "activity",
            "nodes": [
                {"id": "initial", "cls": {"type": "initial"}},
                {"id": "action", "cls_ptr": "action-cls", "cls": {"type": "action", "name": "Submit"}},
            ],
            "edges": [{"source_ptr": "initial", "target_ptr": "action"}],
        }

        by_id, first_ids, all_ids = _activity_action_indexes({"activity_diagrams": [diagram]})

        self.assertEqual(by_id["action"]["name"], "Submit")
        self.assertIn("action", first_ids)
        self.assertIn("action-cls", all_ids)

    def test_build_usecase_navigation_creates_pages_permissions_and_nav_plan(self):
        """Verify that build usecase navigation creates pages permissions and nav plan."""
        system_data = {
            "classifiers": [
                {"id": "actor", "data": {"type": "actor", "name": "Customer"}},
                {"id": "uc", "data": {"type": "usecase", "name": "Browse Products", "classes": ["product"]}},
                {"id": "product", "data": {"type": "class", "name": "Product", "attributes": [{"name": "name"}]}},
            ],
            "relations": [
                {"id": "interact", "source": "actor", "target": "uc", "data": {"type": "interaction"}}
            ],
            "diagrams": [
                {
                    "type": "usecase",
                    "nodes": [{"id": "actor-node", "cls": "actor"}, {"id": "uc-node", "cls": "uc"}],
                    "edges": [{"rel": "interact"}],
                }
            ],
            "activity_diagrams": [],
        }

        navigation = _build_usecase_navigation(system_data, "actor", "Customer")

        self.assertEqual(navigation["pages"][0]["primary_model"], "Product")
        self.assertEqual(navigation["actor_permissions"]["Product"], ["view"])
        self.assertTrue(navigation["nav_plan"]["pages"])

    def test_workflow_plan_filters_steps_by_actor_and_resolves_classes(self):
        """Verify that workflow plan filters steps by actor and resolves classes."""
        system_data = {
            "classifiers": [
                {"id": "actor", "data": {"type": "actor", "name": "Customer"}},
                {"id": "product", "data": {"type": "class", "name": "Product"}},
            ],
            "activity_diagrams": [
                {
                    "id": "activity",
                    "nodes": [
                        {
                            "id": "action",
                            "cls_ptr": "action-cls",
                            "cls": {"type": "action", "name": "Select Product", "actorNode": "actor", "classes": ["product"]},
                        }
                    ],
                    "edges": [],
                }
            ],
        }

        steps = _workflow_plan(system_data, "actor", "Customer")

        self.assertEqual(steps[0]["activity_node_name"], "Select Product")
        self.assertEqual(steps[0]["classes"], ["Product"])

    def test_activity_models_for_step_prefers_explicit_then_entry_related_models(self):
        """Verify that activity models for step prefers explicit then entry related models."""
        self.assertEqual(_activity_models_for_step({"classes": ["Product"]}, [], {"Product"}), ["Product"])
        self.assertEqual(
            _activity_models_for_step(
                {"activity_node_name": "Select Cart Items", "diagram_id": "d"},
                [{"diagram_id": "d", "pre_workflow_collections": ["CartItem"], "related_models": ["Product"]}],
                {"CartItem", "Product"},
            )[0],
            "CartItem",
        )


if __name__ == "__main__":
    unittest.main()
