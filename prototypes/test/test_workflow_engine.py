import sys
import unittest
from pathlib import Path


class WorkflowEngineGenerationTests(unittest.TestCase):
    def test_activity_guard_available_generates_exclusive_condition_rule(self):
        generation_scripts = (
            Path(__file__).resolve().parents[1]
            / "backend"
            / "generation"
            / "generation_scripts"
        )
        sys.path.insert(0, str(generation_scripts))
        try:
            from utils.workflow_engine.data_generation import ActivityDiagramParser
        finally:
            try:
                sys.path.remove(str(generation_scripts))
            except ValueError:
                pass

        metadata = {
            "interfaces": [],
            "diagrams": [
                {
                    "id": "classes",
                    "type": "classes",
                    "nodes": [{
                        "id": "book-node",
                        "cls": {"data": {
                            "type": "class",
                            "name": "Book",
                            "attributes": [{"name": "copies_available", "type": "int"}],
                        }},
                    }],
                    "edges": [],
                },
                {
                    "id": "activity",
                    "name": "Borrowing",
                    "type": "activity",
                    "nodes": [
                        {"id": "initial", "cls": {"data": {"type": "initial", "name": "Initial"}}},
                        {"id": "check", "cls": {"data": {"type": "action", "name": "Check Availability", "actorNodeName": "Librarian"}}},
                        {"id": "decision", "cls": {"data": {"type": "decision", "name": "Decision"}}},
                        {"id": "create", "cls": {"data": {"type": "action", "name": "Create Loan Record", "actorNodeName": "Librarian"}}},
                        {"id": "notify", "cls": {"data": {"type": "action", "name": "Notify Unavailable", "actorNodeName": "Librarian"}}},
                        {"id": "final", "cls": {"data": {"type": "final", "name": "Final"}}},
                    ],
                    "edges": [
                        {"id": "e1", "source_ptr": "initial", "target_ptr": "check", "rel": {"data": {"type": "controlflow"}}},
                        {"id": "e2", "source_ptr": "check", "target_ptr": "decision", "rel": {"data": {"type": "controlflow"}}},
                        {"id": "e3", "source_ptr": "decision", "target_ptr": "create", "rel": {"data": {"type": "controlflow", "guard": "[available]"}}},
                        {"id": "e4", "source_ptr": "decision", "target_ptr": "notify", "rel": {"data": {"type": "controlflow", "guard": "[unavailable]"}}},
                        {"id": "e5", "source_ptr": "create", "target_ptr": "final", "rel": {"data": {"type": "controlflow"}}},
                        {"id": "e6", "source_ptr": "notify", "target_ptr": "final", "rel": {"data": {"type": "controlflow"}}},
                    ],
                },
            ],
        }

        _, workflow_data = ActivityDiagramParser(metadata).get_workflow_engine_data()
        check_action = next(node for node in workflow_data["action_nodes"] if node["name"] == "Check Availability")
        check_rule = next(rule for rule in workflow_data["rules"] if rule["action_node"] == check_action["id"])
        branch = check_rule["condition"][0]["next"]

        self.assertEqual(branch[0]["condition"]["target_class_name"], "Book")
        self.assertEqual(branch[0]["condition"]["target_attribute"], "copies_available")
        self.assertEqual(branch[0]["condition"]["operator"], ">")
        self.assertEqual(branch[0]["condition"]["threshold"], "0")
        self.assertEqual(len(branch), 2)
        self.assertNotIn("condition", branch[1])

    def test_activity_update_view_reassociates_updated_instance(self):
        from jinja2 import Environment, FileSystemLoader

        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        env = Environment(loader=FileSystemLoader(str(templates)))
        template = env.get_template("views.py.jinja2")

        class Attr:
            name = "copies_available"
            updatable = True
            derived = False
            type = 1

            def __str__(self):
                return self.name

        class Section:
            id = "update-book"
            name = "Update_Book_Status"
            display_name = "Update Book Status"
            primary_model = "Book"
            parent_models = []
            attributes = [Attr()]
            has_create_operation = False
            has_update_operation = True
            has_delete_operation = False
            has_select_operation = False
            template_name = "Librarian_Update_Book_Status.html"
            style = {}
            custom_methods = []
            related_to_section_id = None
            component_type = "data"
            position = "main"
            role = "object_form"
            layout = "form"
            query_literal = "{}"

            def __str__(self):
                return self.name

        class Page:
            name = "Update_Book_Status"
            display_name = "Update Book Status"
            type = "activity"
            section_components = [Section()]
            is_task_page = False

            def __str__(self):
                return self.name

        page = Page()
        rendered = template.render(
            application_name="Librarian",
            application_namespace="Librarian",
            pages=[page],
            models_on_pages={
                page: {
                    "parent_models": [],
                    "primary_models": ["Book"],
                }
            },
            authentication_present=True,
            AttributeType=type("AttributeType", (), {
                "BOOLEAN": 3,
                "STRING": 2,
                "ENUM": 4,
                "VIDEO": 6,
                "IMAGE": 5,
            }),
        )

        update_class_start = rendered.index("class Update_Book_Status_Update_Book_Status_UpdateView")
        update_class_end = rendered.index("class Librarian_Update_Book_Status_ListView")
        update_class = rendered[update_class_start:update_class_end]

        self.assertIn("instance.save()", update_class)
        self.assertIn("active_process_node.active_process.add_associated_instance(instance)", update_class)
        self.assertIn("return _complete_activity_form_step(self.request, active_process_node)", update_class)

    def test_activity_list_view_exposes_workflow_instance_generically(self):
        from jinja2 import Environment, FileSystemLoader

        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        env = Environment(loader=FileSystemLoader(str(templates)))
        template = env.get_template("views.py.jinja2")

        class Section:
            id = "review-order"
            name = "Review_Order"
            display_name = "Review Order"
            primary_model = "Order"
            parent_models = ["Customer"]
            attributes = []
            has_create_operation = False
            has_update_operation = False
            has_delete_operation = False
            has_select_operation = False
            template_name = "Staff_Review_Order.html"
            style = {}
            custom_methods = []
            related_to_section_id = None
            component_type = "data"
            position = "main"
            role = "object_detail"
            layout = "detail"
            query = {}
            query_literal = "{}"

            def __str__(self):
                return self.name

        class Page:
            name = "Review_Order"
            display_name = "Review Order"
            type = "activity"
            section_components = [Section()]
            is_task_page = False

            def __str__(self):
                return self.name

        page = Page()
        rendered = template.render(
            application_name="Staff",
            application_namespace="staff",
            pages=[page],
            models_on_pages={
                page: {
                    "parent_models": ["Customer"],
                    "primary_models": ["Order"],
                }
            },
            authentication_present=True,
            AttributeType=type("AttributeType", (), {
                "BOOLEAN": 3,
                "STRING": 2,
                "ENUM": 4,
                "VIDEO": 6,
                "IMAGE": 5,
            }),
        )

        list_class_start = rendered.index("class Staff_Review_Order_ListView")
        list_class = rendered[list_class_start:]

        self.assertIn("context['workflow_instance_Order']", list_class)
        self.assertIn("ContentType.objects.get_for_model(Order)", list_class)
        self.assertIn("active_process.associated_model_instances", list_class)

    def test_activity_detail_template_reads_workflow_instance_and_relation_ids(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "page_unified.html.jinja2").read_text(encoding="utf-8")

        self.assertIn("workflow_instance_{{ section_component.primary_model }}", source)
        self.assertIn("relation_attr.model", source)
        self.assertIn("detail_obj.{{ relation_attr.model }}|default:''", source)
        self.assertIn("detail_obj.{{ attr }}|default:''", source)

    def test_actor_self_model_uses_profile_page_not_collection_page(self):
        from api.model.llm.gemini_make_agent.uml_mapping.interface_planner import generate_interface_plan

        uml_intelligence = {
            "actor_name": "Patient",
            "actor_intel": {
                "target_permissions": {"Patient": ["read"], "Appointment": ["create", "read"]},
                "target_use_cases": [],
            },
            "model_graph": {
                "Patient": {
                    "attributes": [
                        {"name": "first_name"},
                        {"name": "last_name"},
                        {"name": "email"},
                    ],
                    "associations": [],
                },
                "Appointment": {
                    "attributes": [
                        {"name": "time"},
                        {"name": "reason"},
                        {"name": "Patient", "model": "Patient"},
                    ],
                    "associations": [{"model": "Patient"}],
                },
            },
            "workflow_intel": {"workflows": []},
        }

        plan = generate_interface_plan(uml_intelligence)
        page_ids = {page["id"] for page in plan["pages"]}

        self.assertNotIn("patients", page_ids)
        self.assertIn("patient_detail", page_ids)
        patient_page = next(page for page in plan["pages"] if page["id"] == "patient_detail")
        self.assertTrue(patient_page["nav"])
        patient_section = next(
            section for section in plan["sections"]
            if section["primary_model"] == "Patient" and section["role"] == "object_detail"
        )

        self.assertEqual(patient_section["style"]["data_scope"]["mode"], "actor_owned")
        self.assertEqual(patient_section["style"]["data_scope"]["source"], "current_actor")
        appointment_section = next(
            section for section in plan["sections"]
            if section["primary_model"] == "Appointment"
        )
        self.assertEqual(
            appointment_section["style"]["relation_data_scopes"]["Patient"]["mode"],
            "actor_owned",
        )

    def test_other_actors_can_still_get_patient_collection_page(self):
        from api.model.llm.gemini_make_agent.uml_mapping.interface_planner import generate_interface_plan

        uml_intelligence = {
            "actor_name": "Doctor",
            "actor_intel": {
                "target_permissions": {"Patient": ["read"]},
                "target_use_cases": [],
            },
            "model_graph": {
                "Patient": {
                    "attributes": [
                        {"name": "first_name"},
                        {"name": "last_name"},
                        {"name": "email"},
                    ],
                    "associations": [],
                },
            },
            "workflow_intel": {"workflows": []},
        }

        plan = generate_interface_plan(uml_intelligence)
        page_ids = {page["id"] for page in plan["pages"]}
        self.assertIn("patients", page_ids)
        self.assertTrue(any(
            section["primary_model"] == "Patient" and section["role"] == "object_collection"
            for section in plan["sections"]
        ))

    def test_list_template_uses_actor_scope_only_when_section_requests_it(self):
        from jinja2 import Environment, FileSystemLoader

        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        env = Environment(loader=FileSystemLoader(str(templates)))
        template = env.get_template("views.py.jinja2")

        class Section:
            id = "patients"
            name = "Patients"
            display_name = "Patients"
            primary_model = "Patient"
            parent_models = []
            attributes = []
            has_create_operation = False
            has_update_operation = False
            has_delete_operation = False
            has_select_operation = False
            template_name = "Admin_Patients.html"
            style = {}
            custom_methods = []
            related_to_section_id = None
            component_type = "data"
            position = "main"
            role = "object_collection"
            layout = "list"
            query = {}
            query_literal = "{}"

            def __str__(self):
                return self.name

        class Page:
            name = "Patients"
            display_name = "Patients"
            type = "normal"
            section_components = [Section()]
            is_task_page = False

            def __str__(self):
                return self.name

        page = Page()
        rendered = template.render(
            application_name="Admin",
            application_namespace="Admin",
            pages=[page],
            models_on_pages={page: {"parent_models": [], "primary_models": ["Patient"]}},
            authentication_present=True,
            AttributeType=type("AttributeType", (), {
                "BOOLEAN": 3,
                "STRING": 2,
                "ENUM": 4,
                "VIDEO": 6,
                "IMAGE": 5,
            }),
        )
        list_class = rendered[rendered.index("class Admin_Patients_ListView"):]

        self.assertIn("qs = Patient.objects.all()", list_class)
        self.assertNotIn("qs = self._actor_owned_queryset(Patient, create_missing=True)", list_class)


if __name__ == "__main__":
    unittest.main()
