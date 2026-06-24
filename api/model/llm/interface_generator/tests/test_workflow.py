import json
import os
import sys
import types
from unittest.mock import patch
from unittest import TestCase

metadata_pkg = types.ModuleType("metadata")
metadata_models = types.ModuleType("metadata.models")
diagram_pkg = types.ModuleType("diagram")
diagram_models = types.ModuleType("diagram.models")


class _Manager:
    def filter(self, **kwargs):
        """Provide a fake queryset filter helper for tests."""
        return []

    def get(self, **kwargs):
        """Provide a fake queryset get helper for tests."""
        raise LookupError(kwargs)

    def prefetch_related(self, *args):
        """Provide a fake queryset prefetch_related helper for tests."""
        return self


metadata_models.Interface = type("Interface", (), {"DoesNotExist": type("DoesNotExist", (Exception,), {}), "objects": _Manager()})
metadata_models.Classifier = type("Classifier", (), {"objects": _Manager()})
metadata_models.System = type("System", (), {"objects": _Manager()})
diagram_models.Diagram = type("Diagram", (), {"objects": _Manager()})
sys.modules.setdefault("metadata", metadata_pkg)
sys.modules.setdefault("metadata.models", metadata_models)
sys.modules.setdefault("diagram", diagram_pkg)
sys.modules.setdefault("diagram.models", diagram_models)


class WorkflowSemanticTests(TestCase):
    def test_semantic_resolver_keeps_only_valid_workflow_semantics(self):
        """Verify that semantic resolver keeps only valid workflow semantics."""
        from llm.interface_generator.django_service import resolve_interface_semantics_with_llm

        uml_intel = {
            "semantic_decisions": [{"kind": "activity"}],
            "actor_intel": {"target_permissions": {"Book": ["read", "update"], "Loan": ["create"]}},
            "model_graph": {
                "Book": {"attributes": [{"name": "copies_available"}, {"name": "title"}]},
                "Loan": {"attributes": [{"name": "due_date"}, {"name": "status"}]},
            },
            "workflow_intel": {
                "workflows": [{
                    "steps": [
                        {"action": "Check Availability"},
                        {"action": "Create Loan Record"},
                        {"action": "Update Book Status"},
                        {"action": "Notify Unavailable"},
                    ]
                }]
            },
        }
        raw_response = {
            "activity_steps": {
                "Create Loan Record": {
                    "model": "Loan",
                    "editable_fields": ["due_date", "made_up"],
                    "readonly_fields": ["status", "fake_readonly"],
                    "layout": "form",
                    "component": "ObjectForm",
                    "role": "object_form",
                }
            },
            "workflow_steps": {
                "Check Availability": {
                    "intent": "check",
                    "context_model": "Book",
                    "target_model": "Book",
                    "condition": {
                        "model": "Book",
                        "field": "copies_available",
                        "operator": ">",
                        "threshold": "0",
                    },
                    "true_next": "Create Loan Record",
                    "false_next": "Notify Unavailable",
                },
                "Create Loan Record": {
                    "intent": "create_record",
                    "context_model": "Book",
                    "target_model": "Loan",
                    "readonly_fields": ["status", "fake_readonly"],
                    "editable_fields": ["due_date", "fake_editable"],
                    "context_binding": {"model": "Book", "mode": "hidden"},
                    "output_models": ["Loan"],
                },
                "Update Book Status": {
                    "intent": "update_record",
                    "context_model": "Book",
                    "target_model": "Book",
                    "readonly_fields": ["title", "fake_readonly"],
                    "editable_fields": ["copies_available", "fake_editable"],
                    "context_binding": {"model": "Book", "mode": "readonly"},
                    "field_updates": [
                        {"field": "copies_available", "operation": "decrement", "value": "1"},
                        {"field": "made_up", "operation": "decrement", "value": "1"},
                    ],
                },
                "Fake Step": {
                    "intent": "check",
                    "context_model": "Imaginary",
                },
            },
        }

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}), \
             patch("llm.interface_generator.django_service._req.post") as mock_post:
            mock_post.return_value.json.return_value = {
                "candidates": [{
                    "content": {"parts": [{"text": json.dumps(raw_response)}]}
                }]
            }
            mock_post.return_value.raise_for_status.return_value = None

            clean = resolve_interface_semantics_with_llm(uml_intel, {"pages": [], "sections": []})

        self.assertEqual(
            clean["activity_steps"]["Create Loan Record"]["editable_fields"],
            ["due_date"],
        )
        self.assertEqual(
            clean["activity_steps"]["Create Loan Record"]["readonly_fields"],
            ["status"],
        )
        self.assertEqual(
            clean["workflow_steps"]["Check Availability"]["condition"],
            {
                "model": "Book",
                "field": "copies_available",
                "operator": ">",
                "threshold": "0",
            },
        )
        self.assertEqual(clean["workflow_steps"]["Check Availability"]["true_next"], "Create Loan Record")
        self.assertEqual(clean["workflow_steps"]["Check Availability"]["false_next"], "Notify Unavailable")
        self.assertEqual(clean["workflow_steps"]["Create Loan Record"]["intent"], "create_record")
        self.assertEqual(clean["workflow_steps"]["Create Loan Record"]["target_model"], "Loan")
        self.assertEqual(clean["workflow_steps"]["Create Loan Record"]["readonly_fields"], ["status"])
        self.assertEqual(clean["workflow_steps"]["Create Loan Record"]["editable_fields"], ["due_date"])
        self.assertEqual(
            clean["workflow_steps"]["Create Loan Record"]["context_binding"],
            {"model": "Book", "mode": "hidden"},
        )
        self.assertEqual(clean["workflow_steps"]["Update Book Status"]["readonly_fields"], ["title"])
        self.assertEqual(clean["workflow_steps"]["Update Book Status"]["editable_fields"], ["copies_available"])
        self.assertEqual(
            clean["workflow_steps"]["Update Book Status"]["context_binding"],
            {"model": "Book", "mode": "readonly"},
        )
        self.assertNotIn("Fake Step", clean["workflow_steps"])

    def test_planner_materializes_workflow_semantics_for_update_record(self):
        """Verify that planner materializes workflow semantics for update record."""
        from llm.interface_generator.uml_mapping.interface_planner import generate_interface_plan

        uml_intel = {
            "actor_name": "Librarian",
            "actor_intel": {"target_permissions": {"Book": ["read", "update"]}},
            "model_graph": {
                "Book": {
                    "attributes": [
                        {"name": "isbn", "type": "str"},
                        {"name": "title", "type": "str"},
                        {"name": "copies_available", "type": "int"},
                    ],
                }
            },
            "workflow_intel": {
                "workflows": [{
                    "name": "Borrowing",
                    "is_multi_step": True,
                    "steps": [{
                        "action": "Update Book Status",
                        "model": "Book",
                        "actor_node_name": "Librarian",
                        "component_hint": "ObjectForm",
                    }],
                }]
            },
        }

        plan = generate_interface_plan(
            uml_intel,
            {
                "workflow_steps": {
                    "Update Book Status": {
                        "intent": "update_record",
                        "target_model": "Book",
                        "context_model": "Book",
                        "readonly_fields": ["isbn", "title"],
                        "editable_fields": ["copies_available"],
                    }
                }
            },
        )

        section = next(s for s in plan["sections"] if s["name"] == "Update Book Status")
        self.assertEqual(section["operations"], ["update"])
        self.assertEqual(section["visible_fields"], ["isbn", "title", "copies_available"])
        self.assertEqual(section["editable_fields"], ["copies_available"])
        self.assertEqual(
            [(attr["name"], attr.get("readonly")) for attr in section["attributes"]],
            [("isbn", True), ("title", True), ("copies_available", False)],
        )

    def test_planner_materializes_workflow_semantics_for_create_record(self):
        """Verify that planner materializes workflow semantics for create record."""
        from llm.interface_generator.uml_mapping.interface_planner import generate_interface_plan

        uml_intel = {
            "actor_name": "Librarian",
            "actor_intel": {"target_permissions": {"Book": ["read"], "Loan": ["create"]}},
            "model_graph": {
                "Book": {"attributes": [{"name": "isbn", "type": "str"}, {"name": "title", "type": "str"}]},
                "Loan": {
                    "attributes": [
                        {"name": "loan_date", "type": "str"},
                        {"name": "due_date", "type": "str"},
                        {"name": "status", "type": "str"},
                    ],
                },
            },
            "workflow_intel": {
                "workflows": [{
                    "name": "Borrowing",
                    "is_multi_step": True,
                    "steps": [{
                        "action": "Create Loan Record",
                        "model": "Loan",
                        "actor_node_name": "Librarian",
                        "component_hint": "ObjectForm",
                    }],
                }]
            },
        }

        plan = generate_interface_plan(
            uml_intel,
            {
                "workflow_steps": {
                    "Create Loan Record": {
                        "intent": "create_record",
                        "context_model": "Book",
                        "target_model": "Loan",
                        "readonly_fields": ["status"],
                        "editable_fields": ["loan_date", "due_date"],
                        "context_binding": {"model": "Book", "mode": "hidden"},
                    }
                }
            },
        )

        section = next(s for s in plan["sections"] if s["name"] == "Create Loan Record")
        self.assertEqual(section["operations"], ["create"])
        self.assertEqual(section["visible_fields"], ["status", "loan_date", "due_date"])
        self.assertEqual(section["editable_fields"], ["loan_date", "due_date"])
        self.assertEqual(
            [(attr["name"], attr.get("readonly")) for attr in section["attributes"]],
            [("status", True), ("loan_date", False), ("due_date", False)],
        )
        self.assertEqual(
            section["style"]["workflow_semantics"]["context_binding"],
            {"model": "Book", "mode": "hidden"},
        )

    def test_invalid_related_readonly_fields_become_child_collection(self):
        """Verify that invalid related readonly fields become child collection."""
        from llm.interface_generator.section_utils import _ensure_logical_related_sections, _ref_id

        pages = [{
            "id": "member_detail",
            "name": "Member Detail",
            "primary_model": "Member",
            "sections": [{"value": "member_detail_member_object_detail"}],
        }]
        sections = [{
            "id": "member_detail_member_object_detail",
            "name": "Member Detail",
            "page_id": "member_detail",
            "role": "object_detail",
            "layout": "detail",
            "primary_model": "Member",
            "class": "Member",
            "attributes": [
                {"name": "member_id"},
                {"name": "name"},
                {"name": "book.title", "readonly": True, "source": "related"},
                {"name": "loan.status", "readonly": True, "source": "related"},
            ],
            "operations": {"create": False, "update": False, "delete": False},
        }]
        model_graph = {
            "Member": {
                "attributes": [{"name": "member_id"}, {"name": "name"}],
                "associations": [{"model": "Loan", "cardinality": "1-many"}],
            },
            "Book": {
                "attributes": [{"name": "title"}, {"name": "publisher"}],
                "associations": [{"model": "Loan", "cardinality": "1-many"}],
            },
            "Loan": {
                "attributes": [{"name": "loan_date"}, {"name": "status"}],
                "associations": [
                    {"model": "Member", "cardinality": "many-1"},
                    {"model": "Book", "cardinality": "many-1"},
                ],
            },
        }

        fixed_pages, fixed_sections = _ensure_logical_related_sections(pages, sections, model_graph)

        member_section = next(s for s in fixed_sections if s["id"] == "member_detail_member_object_detail")
        self.assertEqual([a["name"] for a in member_section["attributes"]], ["member_id", "name"])

        loan_section = next(s for s in fixed_sections if s.get("primary_model") == "Loan")
        self.assertEqual(loan_section["role"], "child_collection")
        self.assertEqual(
            {a["name"] if isinstance(a, dict) else a for a in loan_section["attributes"]},
            {"loan_date", "status"},
        )
        self.assertIn(
            loan_section["id"],
            [_ref_id(ref) for ref in fixed_pages[0]["sections"]],
        )

    def test_section_data_relationships_populate_query_and_item_navigation(self):
        """Verify that section data relationships populate query and item navigation."""
        from llm.interface_generator.section_utils import _ensure_section_data_relationships

        pages = [
            {
                "id": "product_gallery",
                "name": "Product Gallery",
                "primary_model": "Product",
                "sections": [{"value": "product_cards"}],
            },
            {
                "id": "product_detail",
                "name": "Product Detail",
                "primary_model": "Product",
                "sections": [{"value": "product_detail_panel"}, {"value": "product_reviews"}],
            },
        ]
        sections = [
            {
                "id": "product_cards",
                "name": "Products",
                "role": "object_collection",
                "layout": "gallery",
                "primary_model": "Product",
                "class": "Product",
                "attributes": ["name", "price"],
                "query": {},
            },
            {
                "id": "product_detail_panel",
                "name": "Product Detail",
                "role": "object_detail",
                "layout": "detail",
                "primary_model": "Product",
                "class": "Product",
                "attributes": ["name", "price"],
                "query": {},
            },
            {
                "id": "product_reviews",
                "name": "Reviews",
                "role": "child_collection",
                "layout": "list",
                "primary_model": "Review",
                "class": "Review",
                "attributes": ["rating", "comment"],
                "query": {},
            },
        ]

        _, fixed_sections = _ensure_section_data_relationships(
            pages,
            sections,
            {
                "Product": ["name", "price"],
                "Review": ["product_id", "rating", "comment"],
            },
        )

        product_cards = next(section for section in fixed_sections if section["id"] == "product_cards")
        self.assertEqual(product_cards["data_source"]["from"], {"model": "Product"})
        self.assertEqual(product_cards["behavior"]["item_click"], {"type": "navigate", "target_page": "Product Detail"})
        self.assertNotIn("item_actions", product_cards)
        self.assertEqual(
            [method["name"] for method in product_cards["methods"]],
            ["Export CSV"],
        )
        self.assertEqual(product_cards["methods"][0]["call_name"], "export_csv")
        self.assertIn("def export_csv(self, request=None):", product_cards["methods"][0]["body"])
        self.assertEqual(product_cards["query"]["limit"], 12)

        detail = next(section for section in fixed_sections if section["id"] == "product_detail_panel")
        self.assertEqual([method["name"] for method in detail["methods"]], ["Export CSV"])
        self.assertNotIn("item_actions", detail)

        reviews = next(section for section in fixed_sections if section["id"] == "product_reviews")
        self.assertNotIn("item_actions", reviews)
        self.assertEqual([method["name"] for method in reviews["methods"]], ["Export CSV"])
        self.assertIn(
            {"field": "product_id", "operator": "eq", "value_from": "request.GET.instance_id_Product"},
            reviews["query"]["filters"],
        )
        self.assertEqual(reviews["query"]["limit"], 4)

    def test_mapper_category_names_for_pages_uses_actual_page_categories(self):
        """Verify that mapper category names for pages uses actual page categories."""
        from llm.interface_generator.uml_mapping.mapping_sections import category_names_for_pages

        pages = [
            {"name": "Browse Products", "category": None},
            {
                "name": "Product Detail",
                "category": {"label": "Product", "value": {"id": "product-id", "name": "Product"}},
            },
            {
                "name": "Product Mirror",
                "category": {"label": "Product", "value": {"id": "product-id", "name": "Product"}},
            },
            {"name": "Order Detail", "category": {"label": "Order"}},
            {"name": "Account", "category": "Customer"},
        ]

        category_names = category_names_for_pages(pages)

        self.assertEqual(category_names, ["Product", "Order", "Customer"])
        self.assertNotIn("Seller", category_names)

    def test_customer_product_seller_relation_does_not_create_seller_workspace(self):
        """Verify that customer product seller relation does not create seller workspace."""
        from llm.interface_generator.uml_mapping.interface_planner import generate_interface_plan

        plan = generate_interface_plan(
            {
                "actor_name": "Customer",
                "actor_intel": {
                    "target_permissions": {
                        "Product": ["read"],
                    },
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
                        "attributes": [
                            {"name": "name", "type": "str"},
                            {"name": "price", "type": "str"},
                            {"name": "Seller", "type": "fk", "model": "Seller"},
                        ],
                        "associations": [{"model": "Seller", "cardinality": "many-1"}],
                    },
                    "Seller": {
                        "attributes": [
                            {"name": "business_name", "type": "str"},
                            {"name": "rating", "type": "str"},
                        ]
                    },
                },
            }
        )

        self.assertEqual(
            [page["primary_model"] for page in plan["pages"]],
            ["Product"],
        )
        self.assertNotIn("Seller", [page["primary_model"] for page in plan["pages"]])
        self.assertNotIn("Seller", [section["primary_model"] for section in plan["sections"]])

    def test_mapper_materializes_only_models_referenced_by_pages_or_sections(self):
        """Verify that mapper materializes only models referenced by pages or sections."""
        from llm.interface_generator.uml_mapping.mapping_sections import _ensure_mapping_content_sections

        pages = [
            {
                "id": "products",
                "name": "Products",
                "primary_model": "Product",
                "type": {"value": "normal", "label": "Normal"},
                "sections": [],
            }
        ]
        sections = []
        model_attrs = {
            "Product": ["name", "price", "Seller"],
            "Seller": ["business_name", "rating"],
        }
        model_graph = {
            "Product": {
                "attributes": [
                    {"name": "name", "type": "str"},
                    {"name": "price", "type": "str"},
                    {"name": "Seller", "type": "fk", "model": "Seller"},
                ],
                "associations": [{"model": "Seller", "cardinality": "many-1"}],
            },
            "Seller": {"attributes": [{"name": "business_name", "type": "str"}]},
        }

        fixed_pages, fixed_sections = _ensure_mapping_content_sections(
            pages,
            sections,
            usecase_navigation={},
            model_attrs=model_attrs,
            model_graph=model_graph,
        )

        self.assertEqual([page["primary_model"] for page in fixed_pages], ["Product"])
        self.assertNotIn("Seller", [section.get("primary_model") for section in fixed_sections])
        nav_sections = [
            section for section in fixed_sections
            if section.get("layout") in {"nav-links", "nav-bar", "site-nav"}
        ]
        nav_labels = [
            method.get("name")
            for section in nav_sections
            for method in section.get("methods") or []
        ]
        self.assertNotIn("Seller", nav_labels)
