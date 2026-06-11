import json
from unittest.mock import patch

from rest_framework.test import APITestCase


class WorkflowSemanticTests(APITestCase):
    def test_semantic_resolver_keeps_only_valid_workflow_semantics(self):
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
            set(a["name"] if isinstance(a, dict) else a for a in loan_section["attributes"]),
            {"loan_date", "status"},
        )
        self.assertIn(
            loan_section["id"],
            [_ref_id(ref) for ref in fixed_pages[0]["sections"]],
        )
