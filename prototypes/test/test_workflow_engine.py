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
        self.assertIn("self._workflow_instance_for_model(Order)", list_class)

    def test_activity_update_only_form_uses_workflow_instance_as_update_instance(self):
        from jinja2 import Environment, FileSystemLoader

        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        env = Environment(loader=FileSystemLoader(str(templates)))
        template = env.get_template("views.py.jinja2")

        class Attr:
            name = "status"
            updatable = True
            derived = False
            type = 1

            def __str__(self):
                return self.name

        class Section:
            id = "review-appointment"
            name = "Review_Appointment"
            display_name = "Review Appointment"
            primary_model = "Appointment"
            parent_models = []
            attributes = [Attr()]
            has_create_operation = False
            has_update_operation = True
            has_delete_operation = False
            has_select_operation = False
            template_name = "Doctor_Review_Appointment.html"
            style = {"workflow_semantics": {"intent": "update_record", "target_model": "Appointment"}}
            custom_methods = []
            related_to_section_id = None
            component_type = "data"
            position = "main"
            role = "object_form"
            layout = "form"
            query = {}
            query_literal = "{}"

            def __str__(self):
                return self.name

        class Page:
            name = "Review_Appointment"
            display_name = "Review Appointment"
            type = "activity"
            section_components = [Section()]
            is_task_page = False

            def __str__(self):
                return self.name

        page = Page()
        rendered = template.render(
            application_name="Doctor",
            application_namespace="doctor",
            pages=[page],
            models_on_pages={page: {"parent_models": [], "primary_models": ["Appointment"]}},
            authentication_present=True,
            AttributeType=type("AttributeType", (), {
                "BOOLEAN": 3,
                "STRING": 2,
                "ENUM": 4,
                "VIDEO": 6,
                "IMAGE": 5,
            }),
        )

        list_class_start = rendered.index("class Doctor_Review_Appointment_ListView")
        list_class = rendered[list_class_start:]

        self.assertIn("context['workflow_instance_Appointment']", list_class)
        self.assertIn("context['update_instance'] = self._workflow_instance_for_model(Appointment)", list_class)
        self.assertIn("_workflow_instance_Appointment = self._workflow_instance_for_model(Appointment)", list_class)

    def test_activity_context_binding_comes_from_section_workflow_semantics(self):
        from jinja2 import Environment, FileSystemLoader

        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        env = Environment(loader=FileSystemLoader(str(templates)))
        template = env.get_template("views.py.jinja2")

        class Section:
            id = "update-medical-record"
            name = "Update_Medical_Record"
            display_name = "Update Medical Record"
            primary_model = "MedicalRecord"
            parent_models = []
            attributes = []
            has_create_operation = True
            has_update_operation = False
            has_delete_operation = False
            has_select_operation = False
            template_name = "Doctor_Update_Medical_Record.html"
            style = {
                "workflow_semantics": {
                    "intent": "create_record",
                    "target_model": "MedicalRecord",
                    "context_binding": {"model": "Appointment", "mode": "readonly"},
                }
            }
            custom_methods = []
            related_to_section_id = None
            component_type = "data"
            position = "main"
            role = "object_form"
            layout = "form"
            query = {}
            query_literal = "{}"

            def __str__(self):
                return self.name

        class Page:
            name = "Update_Medical_Record"
            display_name = "Update Medical Record"
            type = "activity"
            section_components = [Section()]
            is_task_page = False

            def __str__(self):
                return self.name

        page = Page()
        rendered = template.render(
            application_name="Doctor",
            application_namespace="doctor",
            pages=[page],
            models_on_pages={page: {"parent_models": [], "primary_models": ["MedicalRecord"]}},
            authentication_present=True,
            AttributeType=type("AttributeType", (), {
                "BOOLEAN": 3,
                "STRING": 2,
                "ENUM": 4,
                "VIDEO": 6,
                "IMAGE": 5,
            }),
        )

        list_class_start = rendered.index("class Doctor_Update_Medical_Record_ListView")
        list_class = rendered[list_class_start:]

        self.assertIn("context['workflow_instance_MedicalRecord']", list_class)
        self.assertIn("context['workflow_instance_Appointment']", list_class)
        self.assertIn("_workflow_context_instance_Appointment = self._workflow_instance_for_model(Appointment)", list_class)

    def test_activity_detail_template_reads_workflow_instance_and_relation_ids(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "page_unified.html.jinja2").read_text(encoding="utf-8")

        self.assertIn("workflow_instance_{{ section_component.primary_model }}", source)
        self.assertIn("relation_attr.model", source)
        self.assertIn("detail_obj.{{ relation_attr.model }}|default:''", source)
        self.assertIn("detail_obj.{{ attr }}|default:''", source)

    def test_generic_list_view_has_workflow_instance_lookup_helper(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "shared_views.py.jinja2").read_text(encoding="utf-8")

        self.assertIn("def _workflow_instance_for_model(self, model):", source)
        self.assertIn("active_process_node.active_process.associated_model_instances.filter", source)
        self.assertIn("model.objects.filter(pk=association.instance_id).first()", source)

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

    def test_role_actor_gets_document_collection_not_self_profile(self):
        from api.model.llm.gemini_make_agent.uml_mapping.interface_planner import generate_interface_plan

        uml_intelligence = {
            "actor_name": "Document Analyst",
            "actor_intel": {
                "target_permissions": {"Document": ["read", "update"]},
                "target_use_cases": [
                    {
                        "name": "Review Documents",
                        "primary_model": "Document",
                        "page_role": "object_workspace",
                        "permissions": ["read", "update"],
                    }
                ],
            },
            "model_graph": {
                "Document": {
                    "attributes": [
                        {"name": "title"},
                        {"name": "status"},
                        {"name": "uploaded_at"},
                    ],
                    "associations": [],
                },
            },
            "workflow_intel": {"workflows": []},
        }

        plan = generate_interface_plan(
            uml_intelligence,
            semantic_overrides={"actor_model_scopes": {"Document": "collection"}},
        )
        page_ids = {page["id"] for page in plan["pages"]}
        document_section = next(
            section for section in plan["sections"]
            if section["primary_model"] == "Document"
        )

        self.assertIn("documents", page_ids)
        self.assertNotIn("document", page_ids)
        self.assertEqual(document_section["role"], "object_collection")
        self.assertNotIn("data_scope", document_section["style"])

    def test_semantics_prompt_requests_actor_model_scope(self):
        from api.model.llm.prompts.semantics import build_resolve_interface_semantics_prompt

        prompt = build_resolve_interface_semantics_prompt(
            allowed={"actor_model_scopes": ["self_profile", "collection", "assigned", "hidden"]},
            actor_permissions={"Document": ["read"]},
            model_graph={"Document": {"attributes": [{"name": "title"}]}},
            workflow_intel={"workflows": []},
            decisions=[],
            interface_plan={"pages": [], "sections": []},
        )

        self.assertIn("actor_model_scopes", prompt)
        self.assertIn("Document Analyst + Document = collection", prompt)
        self.assertIn("self_profile only when the actor", prompt)

    def test_workflow_component_semantics_are_defined_by_mapping_sections(self):
        from api.model.llm.gemini_make_agent.uml_mapping.interface_planner import generate_interface_plan

        model_graph = {
            "Patient": {
                "attributes": [
                    {"name": "first_name"},
                    {"name": "email"},
                ],
                "associations": [],
            },
            "Doctor": {
                "attributes": [
                    {"name": "name"},
                    {"name": "specialization"},
                ],
                "associations": [],
            },
            "Appointment": {
                "attributes": [
                    {"name": "time"},
                    {"name": "reason"},
                    {"name": "status"},
                    {"name": "notes"},
                    {"name": "Patient", "model": "Patient"},
                    {"name": "Doctor", "model": "Doctor"},
                ],
                "associations": [
                    {"model": "Patient"},
                    {"model": "Doctor"},
                ],
            },
        }
        workflow_intel = {
            "workflows": [{
                "name": "Patient Workflow",
                "is_multi_step": True,
                "steps": [
                    {
                        "action": "Request Appointment",
                        "model": "Appointment",
                        "component_hint": "ObjectForm",
                        "actor_node_name": "Patient",
                    },
                    {
                        "action": "Review Appointment",
                        "model": "Appointment",
                        "component_hint": "ObjectForm",
                        "actor_node_name": "Doctor",
                    },
                ],
            }]
        }

        patient_plan = generate_interface_plan(
            {
                "actor_name": "Patient",
                "actor_intel": {"target_permissions": {"Patient": ["read"], "Appointment": ["create", "read"], "Doctor": ["read"]}},
                "model_graph": model_graph,
                "workflow_intel": workflow_intel,
            },
            semantic_overrides={
                "workflow_steps": {
                    "Request Appointment": {
                        "intent": "create_record",
                        "target_model": "Appointment",
                        "context_binding": {"model": "Patient", "mode": "hidden"},
                        "readonly_fields": ["Patient"],
                        "editable_fields": ["Doctor", "time", "reason", "notes"],
                    }
                }
            },
        )
        request_section = next(
            section for section in patient_plan["sections"]
            if section["name"] == "Request Appointment" and section["role"] == "object_form"
        )

        self.assertEqual(request_section["primary_model"], "Appointment")
        self.assertEqual(request_section["operations"], ["create"])
        self.assertEqual(request_section["editable_fields"], ["Doctor", "time", "reason", "notes"])
        self.assertEqual(
            request_section["style"]["workflow_semantics"]["context_binding"],
            {"model": "Patient", "mode": "hidden"},
        )
        self.assertEqual(
            request_section["style"]["relation_data_scopes"]["Patient"]["mode"],
            "actor_owned",
        )

        doctor_plan = generate_interface_plan(
            {
                "actor_name": "Doctor",
                "actor_intel": {"target_permissions": {"Doctor": ["read"], "Patient": ["read"], "Appointment": ["read", "update"]}},
                "model_graph": model_graph,
                "workflow_intel": workflow_intel,
            },
            semantic_overrides={
                "workflow_steps": {
                    "Review Appointment": {
                        "intent": "update_record",
                        "target_model": "Appointment",
                        "context_binding": {"model": "Patient", "mode": "readonly"},
                        "readonly_fields": ["Patient", "Doctor", "time", "reason"],
                        "editable_fields": ["status", "notes"],
                    }
                }
            },
        )
        review_section = next(
            section for section in doctor_plan["sections"]
            if section["name"] == "Review Appointment" and section["role"] == "object_form"
        )

        self.assertEqual(review_section["primary_model"], "Appointment")
        self.assertEqual(review_section["operations"], ["update"])
        self.assertEqual(review_section["editable_fields"], ["status", "notes"])
        self.assertEqual(
            review_section["style"]["workflow_semantics"]["readonly_fields"],
            ["Patient", "Doctor", "time", "reason"],
        )
        self.assertEqual(
            review_section["style"]["workflow_semantics"]["context_binding"],
            {"model": "Patient", "mode": "readonly"},
        )

    def test_autologin_can_infer_role_from_next_url_when_username_is_person_name(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "authentication" / "auth_views.py.jinja2").read_text(encoding="utf-8")
        patch_source = (Path(__file__).resolve().parents[1] / "backend" / "api.py").read_text(encoding="utf-8")

        for content in (source, patch_source):
            self.assertIn("candidates.append(_norm(value))", content)
            self.assertIn("candidates.append(_norm(next_url.strip('/').split('/', 1)[0]))", content)
            self.assertIn("for wanted in candidates:", content)
            self.assertNotIn("if not wanted and next_url", content)

    def test_activity_frontend_posts_actions_to_workflow_engine(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "page_unified.html.jinja2").read_text(encoding="utf-8")

        self.assertIn("url 'workflow_engine:complete_process_step' active_process_node_id", source)
        self.assertIn("url 'workflow_engine:redirect_to_process_page' active_process_node_id", source)
        self.assertIn("{% csrf_token %}", source)
        self.assertIn('name="next_url"', source)
        self.assertIn('name="next"', source)

    def test_activity_create_form_submits_to_actor_route_and_carries_workflow_node(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "page_unified.html.jinja2").read_text(encoding="utf-8")

        self.assertIn(
            "url '{{ application_namespace }}:{{ page }}_{{ section_component }}_create' {% if page.type == 'activity' %}active_process_node_id{% endif %}",
            source,
        )
        self.assertIn(
            "url '{{ application_namespace }}:{{ page }}_{{ section_component }}_update' {% if page.type == 'activity' %}active_process_node_id{% endif %} update_instance.id",
            source,
        )
        self.assertIn("parent_{{ parent_model }}_list", source)
        self.assertIn("request.GET.instance_id_", source)

    def test_workflow_completion_persists_selected_instances_and_cross_actor_link(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "workflow_engine" / "views.py.jinja2").read_text(encoding="utf-8")
        base_source = (templates / "base.html.jinja2").read_text(encoding="utf-8")

        self.assertIn("def _associate_posted_instances(request, active_process):", source)
        self.assertIn("key.startswith(\"instance_id_\")", source)
        self.assertIn("active_process.add_associated_instance(instance)", source)
        self.assertIn("_associate_posted_instances(request, active_process)", source)
        self.assertIn("return _redirect_success_for_node(request, next_active_process_node)", source)
        self.assertIn("workflow_next_login", source)
        self.assertIn("workflow_next_login", base_source)
        self.assertIn("Open next task", base_source)

    def test_activity_form_views_use_workflow_context_for_following_actor_forms(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "views.py.jinja2").read_text(encoding="utf-8")

        self.assertIn("self.request.POST.get('instance_id_{{ parent_model }}')", source)
        self.assertIn("active_process_node.active_process.associated_model_instances.filter", source)
        self.assertIn("instance.{{ parent_model }}_id = _ami_{{ parent_model }}.instance_id", source)
        self.assertIn("active_process_node.active_process.add_associated_instance(instance)", source)
        self.assertIn("active_process_node.active_process.add_associated_instance(instance.{{ parent_model }})", source)

    def test_activity_create_and_update_forms_persist_database_changes(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "views.py.jinja2").read_text(encoding="utf-8")

        create_start = source.index("class {{ page }}_{{ section_component }}_CreateView")
        update_start = source.index("class {{ page }}_{{ section_component }}_UpdateView")
        delete_start = source.index("class {{ page }}_{{ section_component }}_DeleteView")
        create_class = source[create_start:update_start]
        update_class = source[update_start:delete_start]

        self.assertIn("instance = form.save(commit=False)", create_class)
        self.assertIn("self._assign_posted_relation_fields(instance)", create_class)
        self.assertIn("instance.save()", create_class)
        self.assertIn("active_process_node.active_process.add_associated_instance(instance)", create_class)
        self.assertIn("return _complete_activity_form_step(self.request, active_process_node)", create_class)

        self.assertIn("instance = form.save(commit=False)", update_class)
        self.assertIn("instance.save()", update_class)
        self.assertIn("active_process_node.active_process.add_associated_instance(instance)", update_class)
        self.assertIn("return _complete_activity_form_step(self.request, active_process_node)", update_class)

    def test_activity_action_completion_does_not_directly_mutate_domain_records(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "workflow_engine" / "views.py.jinja2").read_text(encoding="utf-8")

        complete_start = source.index("class CompleteProcessStepView")
        delete_start = source.index("class DeleteProcessView")
        complete_class = source[complete_start:delete_start]

        self.assertIn("_associate_posted_instances(request, active_process)", complete_class)
        self.assertIn("active_process_node.complete_node(request.user)", complete_class)
        self.assertNotIn(".save()", complete_class)
        self.assertNotIn("setattr(", complete_class)

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
