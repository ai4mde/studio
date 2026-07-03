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
        env = Environment(loader=FileSystemLoader(str(templates)), autoescape=True)
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
        env = Environment(loader=FileSystemLoader(str(templates)), autoescape=True)
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
        env = Environment(loader=FileSystemLoader(str(templates)), autoescape=True)
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
        env = Environment(loader=FileSystemLoader(str(templates)), autoescape=True)
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

    def test_unified_page_template_has_no_known_mojibake_fragments(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "page_unified.html.jinja2").read_text(encoding="utf-8")

        bad_fragments = [
            "?/a",
            "?/button",
            "?/span",
            "茅",
            "鈹",
            "鈥",
            "毬",
            "艩",
            "庐",
        ]
        for fragment in bad_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)

    def test_unified_page_template_loads_with_jinja(self):
        from jinja2 import Environment, FileSystemLoader

        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        env = Environment(loader=FileSystemLoader(str(templates)), autoescape=True)

        env.get_template("page_unified.html.jinja2")

    def test_unified_page_preview_and_sync_live_helper_placement(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "page_unified.html.jinja2").read_text(encoding="utf-8")

        badge = '{% include "helpers/unified_page_badge_script.html.jinja2" %}'
        section_selection = '{% include "helpers/unified_page_section_selection_script.html.jinja2" %}'
        multiselect = '{% include "helpers/unified_page_multiselect_script.html.jinja2" %}'
        context_menu = '{% include "helpers/unified_page_context_menu_script.html.jinja2" %}'

        self.assertEqual(source.count(badge), 2)
        self.assertEqual(source.count(section_selection), 1)
        self.assertEqual(source.count(multiselect), 1)
        self.assertEqual(source.count(context_menu), 1)

        preview_layout_pos = source.index("document.querySelector('main > .grid')")
        sync_live_layout_pos = source.index("document.getElementById('page-sections-grid')")
        preview_editor_block = source[preview_layout_pos:sync_live_layout_pos]
        sync_live_block = source[sync_live_layout_pos:]

        self.assertIn(section_selection, preview_editor_block)
        self.assertIn(multiselect, preview_editor_block)
        self.assertIn(context_menu, preview_editor_block)
        self.assertIn(badge, preview_editor_block)
        self.assertIn(badge, sync_live_block)
        self.assertNotIn(section_selection, sync_live_block)
        self.assertNotIn(multiselect, sync_live_block)
        self.assertNotIn(context_menu, sync_live_block)

    def test_unified_page_preview_and_sync_live_layout_helpers_match(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        preview = (templates / "helpers" / "unified_page_preview_layout_script.html.jinja2").read_text(encoding="utf-8")
        sync_live = (templates / "helpers" / "unified_page_sync_live_layout_script.html.jinja2").read_text(encoding="utf-8")

        normalized_preview = preview.replace(
            "document.querySelector('main > .grid')",
            "document.getElementById('page-sections-grid')",
        )
        self.assertEqual(normalized_preview, sync_live)

    def test_unified_page_cta_buttons_preserve_contextual_colors(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "page_unified.html.jinja2").read_text(encoding="utf-8")
        styles = (templates / "helpers" / "unified_page_styles.css.jinja2").read_text(encoding="utf-8")

        macro_start = source.index("{%- macro btn_cls(color) -%}")
        macro_end = source.index("{%- endmacro %}", macro_start)
        btn_macro = source[macro_start:macro_end]

        self.assertIn("_cm.get(color", btn_macro)
        self.assertNotIn("si-btn-primary{% endif %}", btn_macro)
        self.assertIn("si-product-cta", source)
        self.assertIn(".si-product-cta", styles)
        self.assertNotIn('style="background:#ffd700;"', source)

    def test_unified_page_method_buttons_do_not_inherit_primary_accent_color(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "page_unified.html.jinja2").read_text(encoding="utf-8")
        styles = (templates / "helpers" / "unified_page_styles.css.jinja2").read_text(encoding="utf-8")

        self.assertIn("si-method-action", source)
        self.assertIn(".si-method-action", styles)
        self.assertIn("--method-action-bg", styles)
        self.assertIn("method.action.bg_hex", styles)
        self.assertIn("button.method.bg_hex", styles)
        self.assertNotIn("section_method_buttons(section_component, section_methods, d.text ~ ' ' ~ btn_cls", source)

    def test_unified_page_item_click_navigates_with_current_model_id(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "page_unified.html.jinja2").read_text(encoding="utf-8")

        macro_start = source.index("{%- macro item_target_href_attrs(target_page, model_name) -%}")
        macro_end = source.index("{%- endmacro %}", macro_start)
        item_target_macro = source[macro_start:macro_end]

        self.assertIn("postMessage({type:'navigate-page',page:'{{ target_page }}'},'*')", item_target_macro)
        self.assertIn("?instance_id_{{ model_name }}=", item_target_macro)
        self.assertIn("{{ model_name }}.id", item_target_macro)

        self.assertIn(
            "?instance_id_' + _m + '={{ ' + _m + '.id }}",
            source,
        )

    def test_unified_page_uses_bulk_section_actions_for_selected_items(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "page_unified.html.jinja2").read_text(encoding="utf-8")
        shared_views = (templates / "shared_views.py.jinja2").read_text(encoding="utf-8")
        multiselect = (templates / "helpers" / "unified_page_multiselect_script.html.jinja2").read_text(encoding="utf-8")

        self.assertNotIn("macro item_action_buttons", source)
        self.assertIn('data-bulk-section="{{ section_component.id }}"', source)
        self.assertIn('name="selected_{{ section_component.primary_model }}"', source)
        self.assertIn('data-item-id="{{ \'{{\' }}{{ section_component.primary_model }}.id{{ \'}}\' }}"', source)
        self.assertIn("window.siSelSubmitAction", multiselect)
        self.assertIn("selectedInput.value = ids.join(',')", multiselect)
        self.assertIn("selected_values = [", shared_views)
        self.assertIn("for target_id in target_ids:", shared_views)

    def test_item_and_section_custom_actions_are_executable(self):
        generation = Path(__file__).resolve().parents[1] / "backend" / "generation"
        model_generator = (generation / "generation_scripts" / "generate_models.py").read_text(encoding="utf-8")
        shared_views = (generation / "templates" / "shared_views.py.jinja2").read_text(encoding="utf-8")
        schema_path = Path(__file__).resolve().parents[2] / "api" / "model" / "llm" / "interface_generator" / "interface_schemas.py"

        self.assertIn('for method_field in ("methods",):', model_generator)
        self.assertNotIn('("methods", "item_actions")', model_generator)
        self.assertNotIn("instance = model_instance.objects.order_by('pk').first()", shared_views)
        self.assertIn("if 'request' in signature.parameters and 'request' not in kwargs:", shared_views)
        self.assertIn("kwargs['request'] = self.request", shared_views)
        if schema_path.exists():
            schema = schema_path.read_text(encoding="utf-8")
            self.assertIn("Do not use item_actions", schema)
            self.assertIn("enable operations.select", schema)

    def test_query_helpers_support_request_value_from_filters(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "helpers" / "query_helpers.py").read_text(encoding="utf-8")

        self.assertIn("def _resolve_query_value_from(value_from, request=None, source_obj=None):", source)
        self.assertIn('key.startswith("request.GET.")', source)
        self.assertIn("condition.get('value_from')", source)
        self.assertIn("continue", source)

    def test_generated_views_pass_request_to_section_query(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "views.py.jinja2").read_text(encoding="utf-8")

        self.assertIn("_apply_section_query(qs, {{ page.section_components[0].query_literal if page.section_components else '{}' }}, request=self.request)", source)
        self.assertIn("_apply_section_query(_qs_{{ section.name }}, {{ section.query_literal }}, _primary_obj, self.request)", source)
        self.assertIn("_apply_section_query(_qs_{{ section.name }}, {{ section.query_literal }}, request=self.request)", source)

    def test_generic_list_view_has_workflow_instance_lookup_helper(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "shared_views.py.jinja2").read_text(encoding="utf-8")

        self.assertIn("def _workflow_instance_for_model(self, model):", source)
        self.assertIn("active_process_node.active_process.associated_model_instances.filter", source)
        self.assertIn("model.objects.filter(pk=association.instance_id).first()", source)

    def test_related_section_modes_are_inferred_for_same_parent_and_direct_relationships(self):
        section_utils = (
            Path(__file__).resolve().parents[2]
            / "api"
            / "model"
            / "llm"
            / "interface_generator"
            / "section_utils.py"
        )
        if not section_utils.exists():
            self.skipTest("interface_generator source is not mounted in this test environment")
        source = section_utils.read_text(encoding="utf-8")

        self.assertIn('relationship.setdefault("mode", "same_parent")', source)
        self.assertIn('query.setdefault("exclude_source", True)', source)
        self.assertIn('relationship.setdefault("mode", "direct")', source)
        self.assertIn('relation_field = section.get("relation_field") or _guess_relation_field(model, source_model, model_attrs)', source)
        self.assertIn('section["relation_field"] = relation_field', source)

    def test_related_section_views_filter_same_parent_and_direct_relationships(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "views.py.jinja2").read_text(encoding="utf-8")

        self.assertIn("{% if section.relation_field -%}", source)
        self.assertIn("{% set _ns.same_model = (section.primary_model == _src.primary_model) -%}", source)
        self.assertIn("{% elif section.primary_model == _src.primary_model -%}", source)
        self.assertIn("{% elif _src.primary_model in section.parent_models -%}", source)
        self.assertIn(".exclude(id=_src_{{ _src.primary_model }}.id)", source)
        self.assertIn("objects.filter(**{_related_lookup_{{ section.name }}: _related_value_{{ section.name }}})", source)
        self.assertIn("context['related_{{ section.name }}_list']", source)

    def test_actor_self_model_uses_profile_page_not_collection_page(self):
        from api.model.llm.interface_generator.uml_mapping.interface_planner import generate_interface_plan

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
        from api.model.llm.interface_generator.uml_mapping.interface_planner import generate_interface_plan

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
        from api.model.llm.interface_generator.uml_mapping.interface_planner import generate_interface_plan

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
        from api.model.llm.interface_generator.uml_mapping.interface_planner import generate_interface_plan

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

    def test_workflow_redirect_page_falls_back_to_target_url_or_actor_handoff(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "workflow_engine" / "views.py.jinja2").read_text(encoding="utf-8")

        self.assertIn("if _user_can_visit_url(request, target_url):", source)
        self.assertIn("return redirect(target_url)", source)
        self.assertIn("return _redirect_home_success(request, target_url, _actor_from_url(target_url))", source)

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
        env = Environment(loader=FileSystemLoader(str(templates)), autoescape=True)
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

    def test_base_template_renders_full_dsl_token_styles_in_live_head(self):
        templates = Path(__file__).resolve().parents[1] / "backend" / "generation" / "templates"
        source = (templates / "base.html.jinja2").read_text(encoding="utf-8")

        self.assertIn('helpers/unified_page_styles.css.jinja2', source)
        self.assertIn("_tokens.get('accent.hex'", source)
        self.assertIn("_styling.get('accentColor'", source)
        self.assertIn("_styling.accent_color", source)

    def test_visual_check_signature_tracks_all_rendered_dsl_token_vars(self):
        source = (
            Path(__file__).resolve().parents[2]
            / "api"
            / "model"
            / "generator"
            / "api"
            / "views"
            / "prototypes.py"
        ).read_text(encoding="utf-8")

        self.assertIn("token_css_vars = {", source)
        for css_var in (
            "--region-header-bg",
            "--region-footer-bg",
            "--button-secondary-bg",
            "--button-link-text",
            "--method-action-bg",
            "--method-action-text",
            "--method-action-border",
            "--component-list-bg",
            "--component-workflow-bg",
            "--card-bg",
            "--input-border-focus",
            "--table-header-bg",
            "--badge-success-bg",
            "--nav-bg",
        ):
            self.assertIn(css_var, source)


if __name__ == "__main__":
    unittest.main()
