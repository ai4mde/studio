"""
Unit tests for generator agent nodes.

Covers:
  - _parse_json_response  — fence stripping
  - _synthesise_pages     — deterministic page clustering algorithm
  - parser_node           — metadata → ScreenInfo list
  - ui_designer_node      — LLM output schema + key validation

All LLM calls are mocked so no real API keys are needed.
"""

import json
import unittest
from typing import cast
from unittest.mock import patch, MagicMock

from generator.agents.nodes import (
    _parse_json_response,
    _extract_diagrams,
    _build_diagram_summary,
    _build_screens,
    _build_parser_dsl,
    _synthesise_pages,
    parser_node,
    ui_designer_node,
)
from generator.agents.state import PipelineState, ScreenInfo


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _screen(**kwargs) -> ScreenInfo:
    defaults: dict = dict(
        page_id="pg1",
        page_name="Foo List",
        screen_type="",
        has_create=False,
        has_update=False,
        has_delete=False,
        models=["Foo"],
        sections_count=1,
    )
    defaults.update(kwargs)
    return cast(ScreenInfo, defaults)


def _minimal_state(**kwargs) -> PipelineState:
    defaults: dict = dict(
        project_name="HospitalMgmt",
        application_name="wards",
        metadata="{}",
        system_id="abc-123",
        authentication_present=True,
        screens=[],
        diagram_summary={"usecase": [], "activity": [], "classes": []},
        parser_dsl={"domain": {"name": ""}, "actors": [], "entities": [], "actions": [], "workflow": {"nodes": [], "edges": []}},
        page_ir=None,
        ui_design=None,
    )
    defaults.update(kwargs)
    return cast(PipelineState, defaults)


# ─────────────────────────────────────────────────────────────────────────────
# _extract_diagrams
# ─────────────────────────────────────────────────────────────────────────────

_SAMPLE_DIAGRAMS_METADATA = {
    "diagrams": [
        {
            "type": "usecase",
            "name": "Ward Management",
            "nodes": [
                {"id": "n-nurse", "cls": {"type": "actor", "name": "Nurse"}},
                {"id": "n-doctor", "cls": {"type": "actor", "name": "Doctor"}},
                {"id": "n-assign", "cls": {
                    "type": "usecase",
                    "name": "Assign Patient",
                    "precondition": "Patient is admitted",
                    "postcondition": "Patient assigned to ward",
                    "trigger": "Admission form submitted",
                    "scenarios": ["Nurse assigns patient", "Doctor overrides assignment"],
                }},
                {"id": "n-discharge", "cls": {
                    "type": "usecase",
                    "name": "Discharge Patient",
                    "precondition": "",
                    "postcondition": "Ward bed freed",
                    "scenarios": [],
                }},
                {"id": "n-verify", "cls": {
                    "type": "usecase",
                    "name": "Verify Insurance",
                }},
            ],
            "edges": [
                # Nurse → Assign Patient (interaction)
                {"source_ptr": "n-nurse", "target_ptr": "n-assign", "rel": {"type": "interaction"}},
                # Assign Patient –« include »– Verify Insurance
                {"source_ptr": "n-assign", "target_ptr": "n-verify", "rel": {"type": "inclusion"}},
                # Discharge Patient –« extend »– Assign Patient
                {"source_ptr": "n-discharge", "target_ptr": "n-assign", "rel": {"type": "extension"}},
            ],
        },
        {
            "type": "activity",
            "name": "Patient Admission Flow",
            "nodes": [
                {"cls": {"type": "action", "name": "Register Patient", "actorNodeName": "Receptionist", "isAutomatic": False, "body": ""}},
                {"cls": {"type": "action", "name": "Verify Insurance", "actorNodeName": "System", "isAutomatic": True, "body": "call insurance API"}},
                {"cls": {"type": "action", "name": "Assign Ward", "actorNodeName": "Nurse", "isAutomatic": False, "localPrecondition": "Insurance verified", "localPostcondition": "Bed assigned"}},
                {"cls": {"type": "initial"}},
                {"cls": {"type": "final"}},
            ],
        },
        {
            "type": "classes",
            "name": "Domain Model",
            "nodes": [
                {"cls": {"type": "class", "name": "Ward", "attributes": [{"name": "name", "type": "str"}, {"name": "capacity", "type": "int"}]}},
                {"cls": {"type": "class", "name": "Patient", "attributes": [{"name": "full_name", "type": "str"}]}},
                {"cls": {"type": "enum", "name": "WardType"}},  # should be ignored
            ],
        },
    ]
}


class ExtractDiagramsTests(unittest.TestCase):

    def setUp(self):
        self.result = _extract_diagrams(_SAMPLE_DIAGRAMS_METADATA)

    def test_returns_three_keys(self):
        self.assertIn("usecase", self.result)
        self.assertIn("activity", self.result)
        self.assertIn("classes", self.result)

    # —— Use Case ——
    def test_usecase_diagram_extracted(self):
        self.assertEqual(len(self.result["usecase"]), 1)
        uc_diagram = self.result["usecase"][0]
        self.assertEqual(uc_diagram["name"], "Ward Management")

    def test_usecase_actors_extracted(self):
        actors = self.result["usecase"][0]["actors"]
        self.assertIn("Nurse", actors)
        self.assertIn("Doctor", actors)

    def test_usecase_names_extracted(self):
        usecases = self.result["usecase"][0]["usecases"]
        names = [u["name"] for u in usecases]
        self.assertIn("Assign Patient", names)
        self.assertIn("Discharge Patient", names)

    def test_usecase_precondition_included_when_non_empty(self):
        assign = next(u for u in self.result["usecase"][0]["usecases"] if u["name"] == "Assign Patient")
        self.assertEqual(assign["precondition"], "Patient is admitted")

    def test_usecase_empty_precondition_excluded(self):
        discharge = next(u for u in self.result["usecase"][0]["usecases"] if u["name"] == "Discharge Patient")
        self.assertNotIn("precondition", discharge)

    def test_usecase_scenarios_included(self):
        assign = next(u for u in self.result["usecase"][0]["usecases"] if u["name"] == "Assign Patient")
        self.assertEqual(assign["scenarios"], ["Nurse assigns patient", "Doctor overrides assignment"])

    def test_usecase_empty_scenarios_excluded(self):
        discharge = next(u for u in self.result["usecase"][0]["usecases"] if u["name"] == "Discharge Patient")
        self.assertNotIn("scenarios", discharge)

    # —— Activity ——
    def test_activity_diagram_extracted(self):
        self.assertEqual(len(self.result["activity"]), 1)
        self.assertEqual(self.result["activity"][0]["name"], "Patient Admission Flow")

    def test_activity_only_action_nodes_as_steps(self):
        """Initial and Final control nodes must not appear in steps."""
        steps = self.result["activity"][0]["steps"]
        step_names = [s["name"] for s in steps]
        self.assertIn("Register Patient", step_names)
        self.assertIn("Verify Insurance", step_names)
        self.assertIn("Assign Ward", step_names)
        self.assertEqual(len(steps), 3)  # no initial/final

    def test_activity_actor_assigned_to_step(self):
        steps = self.result["activity"][0]["steps"]
        register = next(s for s in steps if s["name"] == "Register Patient")
        self.assertEqual(register["actor"], "Receptionist")

    def test_activity_automatic_flag_set(self):
        steps = self.result["activity"][0]["steps"]
        verify = next(s for s in steps if s["name"] == "Verify Insurance")
        self.assertTrue(verify.get("automatic"))

    def test_activity_body_included_when_non_empty(self):
        steps = self.result["activity"][0]["steps"]
        verify = next(s for s in steps if s["name"] == "Verify Insurance")
        self.assertEqual(verify["body"], "call insurance API")

    def test_activity_precondition_postcondition_included(self):
        steps = self.result["activity"][0]["steps"]
        assign = next(s for s in steps if s["name"] == "Assign Ward")
        self.assertEqual(assign["precondition"], "Insurance verified")
        self.assertEqual(assign["postcondition"], "Bed assigned")

    def test_activity_actors_list_deduplicated(self):
        actors = self.result["activity"][0]["actors"]
        self.assertIn("Receptionist", actors)
        self.assertIn("Nurse", actors)
        self.assertIn("System", actors)
        self.assertEqual(len(actors), len(set(actors)))  # no duplicates

    # —— Class ——
    def test_class_diagram_extracted(self):
        self.assertEqual(len(self.result["classes"]), 1)
        self.assertEqual(self.result["classes"][0]["name"], "Domain Model")

    def test_class_only_class_nodes_not_enums(self):
        classes = self.result["classes"][0]["classes"]
        names = [c["name"] for c in classes]
        self.assertIn("Ward", names)
        self.assertIn("Patient", names)
        self.assertNotIn("WardType", names)  # enum should be excluded

    def test_class_attributes_extracted(self):
        classes = self.result["classes"][0]["classes"]
        ward = next(c for c in classes if c["name"] == "Ward")
        attr_names = [a["name"] for a in ward["attributes"]]
        self.assertIn("name", attr_names)
        self.assertIn("capacity", attr_names)

    def test_empty_metadata_returns_empty_lists(self):
        result = _extract_diagrams({})
        self.assertEqual(result, {"usecase": [], "activity": [], "classes": []})

    def test_unknown_diagram_type_ignored(self):
        meta = {"diagrams": [{"type": "component", "name": "X", "nodes": []}]}
        result = _extract_diagrams(meta)
        self.assertEqual(result["usecase"], [])
        self.assertEqual(result["activity"], [])
        self.assertEqual(result["classes"], [])

    # —— Relations (Include / Extend / Interaction) ——
    def test_usecase_relations_extracted(self):
        relations = self.result["usecase"][0].get("relations", [])
        self.assertTrue(len(relations) > 0)

    def test_usecase_inclusion_relation(self):
        relations = self.result["usecase"][0]["relations"]
        incl = next((r for r in relations if r["type"] == "inclusion"), None)
        self.assertIsNotNone(incl)
        self.assertEqual(incl["source"], "Assign Patient")
        self.assertEqual(incl["target"], "Verify Insurance")

    def test_usecase_extension_relation(self):
        relations = self.result["usecase"][0]["relations"]
        ext = next((r for r in relations if r["type"] == "extension"), None)
        self.assertIsNotNone(ext)
        self.assertEqual(ext["source"], "Discharge Patient")
        self.assertEqual(ext["target"], "Assign Patient")

    def test_usecase_interaction_relation(self):
        relations = self.result["usecase"][0]["relations"]
        interact = next((r for r in relations if r["type"] == "interaction"), None)
        self.assertIsNotNone(interact)
        self.assertEqual(interact["source"], "Nurse")
        self.assertEqual(interact["target"], "Assign Patient")

    def test_no_relations_key_when_empty(self):
        meta = {"diagrams": [{"type": "usecase", "name": "X",
                              "nodes": [{"id": "n1", "cls": {"type": "actor", "name": "A"}}],
                              "edges": []}]}
        result = _extract_diagrams(meta)
        self.assertNotIn("relations", result["usecase"][0])


# ─────────────────────────────────────────────────────────────────────────────
# _parse_json_response
# ─────────────────────────────────────────────────────────────────────────────

class ParseJsonResponseTests(unittest.TestCase):

    def test_plain_json(self):
        raw = '{"a": 1}'
        self.assertEqual(_parse_json_response(raw), {"a": 1})

    def test_json_code_fence(self):
        raw = '```json\n{"a": 1}\n```'
        self.assertEqual(_parse_json_response(raw), {"a": 1})

    def test_generic_code_fence(self):
        raw = '```\n{"a": 1}\n```'
        self.assertEqual(_parse_json_response(raw), {"a": 1})

    def test_trailing_whitespace(self):
        raw = '  {"a": 1}  '
        self.assertEqual(_parse_json_response(raw), {"a": 1})

    def test_array_response(self):
        raw = '```json\n[1, 2, 3]\n```'
        self.assertEqual(_parse_json_response(raw), [1, 2, 3])

    def test_invalid_json_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            _parse_json_response("not json")


# ─────────────────────────────────────────────────────────────────────────────
# parser_node
# ─────────────────────────────────────────────────────────────────────────────

_SAMPLE_METADATA = {
    "classifiers": [
        # Actors
        {"id": "a1", "data": {"type": "actor", "parentNode": None, "name": "Nurse"}, "system_id": "s1", "system_name": "Test"},
        {"id": "sys1", "data": {"type": "actor", "parentNode": None, "name": "System"}, "system_id": "s1", "system_name": "Test"},
        # Use case
        {
            "id": "uc1",
            "data": {
                "type": "usecase", "parentNode": "sb1", "name": "Assign Patient",
                "precondition": "", "postcondition": "", "trigger": "",
                "scenarios": [], "activities": [], "actions": [], "classes": [], "application_model": [],
            },
            "system_id": "s1", "system_name": "Test",
        },
        # Class
        {
            "id": "cls1",
            "data": {
                "type": "class", "name": "Ward",
                "attributes": [{"name": "name", "type": "str", "enum": None, "derived": False, "description": None, "body": None}],
                "methods": [], "abstract": False, "leaf": False,
            },
            "system_id": "s1", "system_name": "Test",
        },
        # Non-automatic action → becomes a screen
        {
            "id": "act1",
            "data": {
                "type": "action", "role": "action", "name": "Add Ward",
                "isAutomatic": False, "actorNode": "a1", "actorNodeName": "Nurse",
                "customCode": None, "localPrecondition": "", "localPostcondition": "",
                "body": "", "operation": None, "publish": None, "subscribe": None,
                "classes": None, "application_models": None, "page": None,
            },
            "system_id": "s1", "system_name": "Test",
        },
        # Automatic action → excluded from screens (but appears in diagram_summary steps)
        {
            "id": "act2",
            "data": {
                "type": "action", "role": "action", "name": "Send Notification",
                "isAutomatic": True, "actorNode": "sys1", "actorNodeName": "System",
                "customCode": None, "localPrecondition": "", "localPostcondition": "",
                "body": "", "operation": None, "publish": None, "subscribe": None,
                "classes": None, "application_models": None, "page": None,
            },
            "system_id": "s1", "system_name": "Test",
        },
        # Object produced by act1 (for model extraction via controlflow)
        {"id": "obj1", "data": {"type": "object", "role": "object", "name": "Ward", "cls": "cls1", "clsName": "Ward", "state": "Created"}, "system_id": "s1", "system_name": "Test"},
    ],
    "relations": [
        # Interaction: Nurse → Assign Patient
        {"id": "r1", "data": {"type": "interaction", "position_handlers": []}, "source": "a1", "target": "uc1"},
        # Controlflow: Add Ward → Ward[Created]
        {"id": "r2", "data": {"type": "controlflow", "guard": "", "weight": "", "condition": None, "is_directed": True, "position_handlers": []}, "source": "act1", "target": "obj1"},
    ],
}


class ParserNodeTests(unittest.TestCase):

    def _run(self, metadata=None):
        state = _minimal_state(metadata=json.dumps(metadata or _SAMPLE_METADATA))
        return parser_node(state)

    def test_returns_screens_key(self):
        result = self._run()
        self.assertIn("screens", result)

    def test_screen_count(self):
        """Only non-automatic actions become screens."""
        result = self._run()
        self.assertEqual(len(result["screens"]), 1)

    def test_first_page_name(self):
        result = self._run()
        names = [s["page_name"] for s in result["screens"]]
        self.assertIn("Add Ward", names)

    def test_automatic_actions_excluded(self):
        """isAutomatic=True actions must not produce a screen."""
        result = self._run()
        names = [s["page_name"] for s in result["screens"]]
        self.assertNotIn("Send Notification", names)

    def test_crud_flags_extracted(self):
        """'Add Ward' contains 'add' → has_create=True; no update/delete keywords."""
        result = self._run()
        ward = next(s for s in result["screens"] if s["page_name"] == "Add Ward")
        self.assertTrue(ward["has_create"])
        self.assertFalse(ward["has_update"])
        self.assertFalse(ward["has_delete"])

    def test_model_extracted(self):
        """Models are extracted from object classifiers reachable via controlflow."""
        result = self._run()
        ward = next(s for s in result["screens"] if s["page_name"] == "Add Ward")
        self.assertIn("Ward", ward["models"])

    def test_diagram_summary_extracted(self):
        """diagram_summary contains correct usecase, activity, and class data."""
        result = self._run()
        ds = result["diagram_summary"]
        self.assertIn("usecase", ds)
        self.assertIn("activity", ds)
        self.assertIn("classes", ds)
        # Use case: Nurse actor, Assign Patient use case
        uc = ds["usecase"][0]
        self.assertIn("Nurse", uc["actors"])
        self.assertTrue(any(u["name"] == "Assign Patient" for u in uc["usecases"]))
        # Class: Ward
        self.assertEqual(ds["classes"][0]["classes"][0]["name"], "Ward")
        # Activity: both actions (including automatic) appear as steps
        step_names = [s["name"] for s in ds["activity"][0]["steps"]]
        self.assertIn("Add Ward", step_names)
        self.assertIn("Send Notification", step_names)

    def test_invalid_metadata_returns_empty(self):
        state = _minimal_state(metadata="not valid json")
        result = parser_node(state)
        self.assertEqual(result["screens"], [])
        self.assertIsNotNone(result["error"])

    def test_parser_dsl_key_present(self):
        result = self._run()
        self.assertIn("parser_dsl", result)
        dsl = result["parser_dsl"]
        for key in ("domain", "actors", "entities", "actions", "workflow"):
            self.assertIn(key, dsl)

    def test_parser_dsl_actors(self):
        result = self._run()
        actor_names = [a["name"] for a in result["parser_dsl"]["actors"]]
        self.assertIn("Nurse", actor_names)
        self.assertIn("System", actor_names)

    def test_parser_dsl_entities(self):
        result = self._run()
        entity_names = [o["name"] for o in result["parser_dsl"]["entities"]]
        self.assertIn("Ward", entity_names)

    def test_parser_dsl_actions_include_automatic(self):
        result = self._run()
        act_names = [a["name"] for a in result["parser_dsl"]["actions"]]
        self.assertIn("Add Ward", act_names)
        self.assertIn("Send Notification", act_names)

    def test_parser_dsl_automatic_action_has_auto_flag(self):
        result = self._run()
        auto = next(a for a in result["parser_dsl"]["actions"] if a["name"] == "Send Notification")
        self.assertTrue(auto.get("auto"))


# ─────────────────────────────────────────────────────────────────────────────
# _build_parser_dsl
# ─────────────────────────────────────────────────────────────────────────────

class BuildParserDSLTests(unittest.TestCase):

    def _dsl(self):
        return _build_parser_dsl(
            _SAMPLE_METADATA["classifiers"],
            _SAMPLE_METADATA["relations"],
        )

    # ── actors ───────────────────────────────────────────────────────────────

    def test_actors_extracted(self):
        actors = self._dsl()["actors"]
        ids = {a["id"] for a in actors}
        self.assertIn("a1", ids)
        self.assertIn("sys1", ids)

    def test_actor_names(self):
        actors = self._dsl()["actors"]
        names = {a["name"] for a in actors}
        self.assertIn("Nurse", names)
        self.assertIn("System", names)

    # ── entities ──────────────────────────────────────────────────────────────

    def test_entities_extracted(self):
        entities = self._dsl()["entities"]
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0]["id"], "cls1")
        self.assertEqual(entities[0]["name"], "Ward")

    def test_entity_fields_extracted(self):
        entities = self._dsl()["entities"]
        self.assertIn("name", entities[0]["fields"])

    # ── actions ───────────────────────────────────────────────────────────────

    def test_actions_count(self):
        actions = self._dsl()["actions"]
        self.assertEqual(len(actions), 2)

    def test_actions_actor_binding(self):
        actions = {a["name"]: a for a in self._dsl()["actions"]}
        self.assertEqual(actions["Add Ward"]["actor"], "a1")
        self.assertEqual(actions["Send Notification"]["actor"], "sys1")

    def test_auto_action_has_auto_flag(self):
        actions = {a["name"]: a for a in self._dsl()["actions"]}
        self.assertTrue(actions["Send Notification"].get("auto"))
        self.assertNotIn("auto", actions["Add Ward"])

    def test_manual_action_no_auto_flag(self):
        actions = {a["name"]: a for a in self._dsl()["actions"]}
        self.assertNotIn("auto", actions["Add Ward"])

    # ── domain ────────────────────────────────────────────────────────────────

    def test_domain_present(self):
        self.assertIn("domain", self._dsl())
        self.assertIn("name", self._dsl()["domain"])

    # ── workflow ─────────────────────────────────────────────────────────────

    def test_workflow_no_states_key(self):
        self.assertNotIn("states", self._dsl()["workflow"])

    def test_workflow_has_nodes_and_edges(self):
        wf = self._dsl()["workflow"]
        self.assertIn("nodes", wf)
        self.assertIn("edges", wf)
        self.assertIsInstance(wf["nodes"], list)
        self.assertIsInstance(wf["edges"], list)

    def test_workflow_no_action_to_action_edges(self):
        # Sample only has act1 → obj1 (object, not action), so no action→action edges
        self.assertEqual(self._dsl()["workflow"]["edges"], [])


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# ui_designer_node
# ─────────────────────────────────────────────────────────────────────────────

_VALID_UI_DESIGN = {
    "ui_ir": {
        "apps": [
            {
                "actor_id": "a1",
                "pages": [
                    {
                        "name": "NurseDashboard",
                        "ast": [
                            {
                                "tag": "form",
                                "htmx": {"post": "/action/act1", "target": "#result"},
                                "children": [
                                    {"tag": "input", "attrs": {"type": "text", "name": "name"}},
                                    {"tag": "button", "attrs": {"type": "submit"}, "text": "Submit"},
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
        "routing": {
            "auth_role_map": {"a1": "/nurse"},
        },
    },
}


class UIDesignerNodeTests(unittest.TestCase):

    @patch("generator.agents.nodes.call_openai")
    def test_success_output_schema(self, mock_llm):
        mock_llm.return_value = json.dumps(_VALID_UI_DESIGN)
        state = _minimal_state(
            screens=[_screen()],
        )
        result = ui_designer_node(state)
        self.assertIn("ui_design", result)
        self.assertIn("ui_ir", result["ui_design"])

    @patch("generator.agents.nodes.call_openai")
    def test_missing_required_key_returns_none(self, mock_llm):
        mock_llm.return_value = "not valid json {"
        state = _minimal_state(screens=[_screen()])
        result = ui_designer_node(state)
        self.assertIsNone(result["ui_design"])

    @patch("generator.agents.nodes.call_openai")
    def test_llm_failure_returns_none_non_fatal(self, mock_llm):
        mock_llm.side_effect = Exception("context too long")
        state = _minimal_state(screens=[_screen()])
        result = ui_designer_node(state)
        self.assertIsNone(result["ui_design"])
        self.assertIsNone(result.get("error"))  # non-fatal, error not propagated

    @patch("generator.agents.nodes.call_openai")
    def test_parser_dsl_injected_into_prompt(self, mock_llm):
        """parser_dsl must appear in the UI Designer prompt so the LLM can decide components."""
        mock_llm.return_value = json.dumps(_VALID_UI_DESIGN)
        state = _minimal_state(
            screens=[_screen()],
            parser_dsl={"domain": {"name": "Test"}, "actors": [{"id": "a1", "name": "Nurse"}], "entities": [], "actions": [], "workflow": {"nodes": [], "edges": []}},
        )
        ui_designer_node(state)
        prompt_arg = mock_llm.call_args[0][1]
        self.assertIn("PARSER DSL", prompt_arg)
        self.assertIn("Nurse", prompt_arg)

    @patch("generator.agents.nodes.call_openai")
    def test_ui_ir_present_when_llm_returns_it(self, mock_llm):
        """When the LLM returns ui_ir, it must appear in ui_design with apps/routing/ast format."""
        mock_llm.return_value = json.dumps(_VALID_UI_DESIGN)
        state = _minimal_state(screens=[_screen()])
        result = ui_designer_node(state)
        self.assertIn("ui_ir", result["ui_design"])
        ui_ir = result["ui_design"]["ui_ir"]
        self.assertIn("apps", ui_ir)
        self.assertIn("routing", ui_ir)
        self.assertEqual(ui_ir["apps"][0]["actor_id"], "a1")
        page = ui_ir["apps"][0]["pages"][0]
        self.assertIn("ast", page)
        self.assertIsInstance(page["ast"], list)
        self.assertGreater(len(page["ast"]), 0)
        self.assertIn("tag", page["ast"][0])

    @patch("generator.agents.nodes.call_openai")
    def test_ui_ir_defaults_when_llm_omits_it(self, mock_llm):
        """When LLM omits ui_ir, node must still provide apps/routing structure."""
        design_no_ir = {k: v for k, v in _VALID_UI_DESIGN.items() if k != "ui_ir"}
        mock_llm.return_value = json.dumps(design_no_ir)
        state = _minimal_state(screens=[_screen()])
        result = ui_designer_node(state)
        ui_ir = result["ui_design"]["ui_ir"]
        self.assertIn("apps", ui_ir)
        self.assertIn("routing", ui_ir)
        self.assertIsInstance(ui_ir["apps"], list)


# ─────────────────────────────────────────────────────────────────────────────
# Loan Application — output format integration tests
# ─────────────────────────────────────────────────────────────────────────────

_LOAN_METADATA = {
    "classifiers": [
        # Actors
        {"id": "la1", "data": {"type": "actor", "parentNode": None, "name": "Applicant"}, "system_id": "s1", "system_name": "Loan"},
        {"id": "la2", "data": {"type": "actor", "parentNode": None, "name": "Loan Officer"}, "system_id": "s1", "system_name": "Loan"},
        {"id": "la3", "data": {"type": "actor", "parentNode": None, "name": "System"}, "system_id": "s1", "system_name": "Loan"},
        # Classes
        {
            "id": "lc1",
            "data": {
                "type": "class", "name": "LoanApplication",
                "attributes": [
                    {"name": "amount", "type": "decimal", "enum": None, "derived": False, "description": None, "body": None},
                    {"name": "status", "type": "str", "enum": None, "derived": False, "description": None, "body": None},
                    {"name": "purpose", "type": "str", "enum": None, "derived": False, "description": None, "body": None},
                ],
                "methods": [], "abstract": False, "leaf": False,
            },
            "system_id": "s1", "system_name": "Loan",
        },
        {
            "id": "lc2",
            "data": {
                "type": "class", "name": "CreditReport",
                "attributes": [
                    {"name": "score", "type": "int", "enum": None, "derived": False, "description": None, "body": None},
                ],
                "methods": [], "abstract": False, "leaf": False,
            },
            "system_id": "s1", "system_name": "Loan",
        },
        # Actions — manual (become screens)
        {
            "id": "lact1",
            "data": {
                "type": "action", "role": "action", "name": "Fill Application",
                "isAutomatic": False, "actorNode": "la1", "actorNodeName": "Applicant",
                "customCode": None, "localPrecondition": "", "localPostcondition": "",
                "body": "", "operation": None, "publish": None, "subscribe": None,
                "classes": None, "application_models": None, "page": None,
            },
            "system_id": "s1", "system_name": "Loan",
        },
        {
            "id": "lact2",
            "data": {
                "type": "action", "role": "action", "name": "Review Application",
                "isAutomatic": False, "actorNode": "la2", "actorNodeName": "Loan Officer",
                "customCode": None, "localPrecondition": "", "localPostcondition": "",
                "body": "", "operation": None, "publish": None, "subscribe": None,
                "classes": None, "application_models": None, "page": None,
            },
            "system_id": "s1", "system_name": "Loan",
        },
        {
            "id": "lact3",
            "data": {
                "type": "action", "role": "action", "name": "Approve Loan",
                "isAutomatic": False, "actorNode": "la2", "actorNodeName": "Loan Officer",
                "customCode": None, "localPrecondition": "", "localPostcondition": "",
                "body": "", "operation": None, "publish": None, "subscribe": None,
                "classes": None, "application_models": None, "page": None,
            },
            "system_id": "s1", "system_name": "Loan",
        },
        # Action — automatic (excluded from screens)
        {
            "id": "lact4",
            "data": {
                "type": "action", "role": "action", "name": "Verify Credit Score",
                "isAutomatic": True, "actorNode": "la3", "actorNodeName": "System",
                "customCode": None, "localPrecondition": "", "localPostcondition": "",
                "body": "", "operation": None, "publish": None, "subscribe": None,
                "classes": None, "application_models": None, "page": None,
            },
            "system_id": "s1", "system_name": "Loan",
        },
        {
            "id": "lact5",
            "data": {
                "type": "action", "role": "action", "name": "Notify Applicant",
                "isAutomatic": True, "actorNode": "la3", "actorNodeName": "System",
                "customCode": None, "localPrecondition": "", "localPostcondition": "",
                "body": "", "operation": None, "publish": None, "subscribe": None,
                "classes": None, "application_models": None, "page": None,
            },
            "system_id": "s1", "system_name": "Loan",
        },
        # Decision / merge control nodes
        {"id": "ldec1", "data": {"type": "decision", "role": "decision", "name": ""}, "system_id": "s1", "system_name": "Loan"},
        {"id": "lmrg1", "data": {"type": "merge", "role": "merge", "name": ""}, "system_id": "s1", "system_name": "Loan"},
        # Object nodes
        {
            "id": "lobj1",
            "data": {"type": "object", "role": "object", "name": "LoanApplication", "cls": "lc1", "clsName": "LoanApplication", "state": "Submitted"},
            "system_id": "s1", "system_name": "Loan",
        },
        {
            "id": "lobj2",
            "data": {"type": "object", "role": "object", "name": "LoanApplication", "cls": "lc1", "clsName": "LoanApplication", "state": "Approved"},
            "system_id": "s1", "system_name": "Loan",
        },
        {
            "id": "lobj3",
            "data": {"type": "object", "role": "object", "name": "CreditReport", "cls": "lc2", "clsName": "CreditReport", "state": "Checked"},
            "system_id": "s1", "system_name": "Loan",
        },
    ],
    "relations": [
        # Fill Application → LoanApplication[Submitted]
        {"id": "lr1", "data": {"type": "controlflow", "guard": "", "weight": "", "condition": None, "is_directed": True, "position_handlers": []}, "source": "lact1", "target": "lobj1"},
        # LoanApplication[Submitted] → Verify Credit Score
        {"id": "lr2", "data": {"type": "controlflow", "guard": "", "weight": "", "condition": None, "is_directed": True, "position_handlers": []}, "source": "lobj1", "target": "lact4"},
        # Verify Credit Score → CreditReport[Checked]
        {"id": "lr3", "data": {"type": "controlflow", "guard": "", "weight": "", "condition": None, "is_directed": True, "position_handlers": []}, "source": "lact4", "target": "lobj3"},
        # CreditReport[Checked] → Review Application
        {"id": "lr4", "data": {"type": "controlflow", "guard": "", "weight": "", "condition": None, "is_directed": True, "position_handlers": []}, "source": "lobj3", "target": "lact2"},
        # Review Application → decision
        {"id": "lr5", "data": {"type": "controlflow", "guard": "", "weight": "", "condition": None, "is_directed": True, "position_handlers": []}, "source": "lact2", "target": "ldec1"},
        # decision → Approve Loan [approved]
        {"id": "lr6", "data": {"type": "controlflow", "guard": "approved", "weight": "", "condition": None, "is_directed": True, "position_handlers": []}, "source": "ldec1", "target": "lact3"},
        # decision → Notify Applicant [rejected]
        {"id": "lr7", "data": {"type": "controlflow", "guard": "rejected", "weight": "", "condition": None, "is_directed": True, "position_handlers": []}, "source": "ldec1", "target": "lact5"},
        # Approve Loan → LoanApplication[Approved]
        {"id": "lr8", "data": {"type": "controlflow", "guard": "", "weight": "", "condition": None, "is_directed": True, "position_handlers": []}, "source": "lact3", "target": "lobj2"},
    ],
}


class LoanApplicationOutputFormatTests(unittest.TestCase):
    """Output format tests using a loan application domain.

    Tests are scoped to parser_node inputs and outputs only.
    All assertions are deterministic — no LLM calls are made.
    """

    # ── parser_node ───────────────────────────────────────────────────────────

    def test_parser_screens_schema(self):
        """parser_node returns ScreenInfo list with required keys."""
        state = _minimal_state(metadata=json.dumps(_LOAN_METADATA))
        result = parser_node(state)
        self.assertEqual(result.get("error"), None)
        for screen in result["screens"]:
            for key in ("page_id", "page_name", "has_create", "has_update", "has_delete", "models"):
                self.assertIn(key, screen, msg=f"screen missing key '{key}'")

    def test_parser_only_manual_actions_become_screens(self):
        """Automatic actions (Verify Credit Score, Notify Applicant) must not appear as screens."""
        state = _minimal_state(metadata=json.dumps(_LOAN_METADATA))
        result = parser_node(state)
        names = [s["page_name"] for s in result["screens"]]
        self.assertNotIn("Verify Credit Score", names)
        self.assertNotIn("Notify Applicant", names)
        self.assertIn("Fill Application", names)
        self.assertIn("Review Application", names)
        self.assertIn("Approve Loan", names)

    def test_parser_dsl_structure(self):
        """parser_dsl has all five top-level keys with correct types."""
        state = _minimal_state(metadata=json.dumps(_LOAN_METADATA))
        result = parser_node(state)
        dsl = result["parser_dsl"]
        self.assertIsInstance(dsl["domain"], dict)
        self.assertIsInstance(dsl["actors"], list)
        self.assertIsInstance(dsl["entities"], list)
        self.assertIsInstance(dsl["actions"], list)
        self.assertIsInstance(dsl["workflow"], dict)
        self.assertNotIn("states", dsl["workflow"])
        self.assertIn("nodes", dsl["workflow"])
        self.assertIn("edges", dsl["workflow"])

    def test_parser_dsl_actors(self):
        state = _minimal_state(metadata=json.dumps(_LOAN_METADATA))
        dsl = parser_node(state)["parser_dsl"]
        actor_names = {a["name"] for a in dsl["actors"]}
        self.assertIn("Applicant", actor_names)
        self.assertIn("Loan Officer", actor_names)
        self.assertIn("System", actor_names)

    def test_parser_dsl_entities_with_fields(self):
        state = _minimal_state(metadata=json.dumps(_LOAN_METADATA))
        dsl = parser_node(state)["parser_dsl"]
        obj_map = {o["name"]: o for o in dsl["entities"]}
        self.assertIn("LoanApplication", obj_map)
        self.assertIn("amount", obj_map["LoanApplication"]["fields"])
        self.assertIn("status", obj_map["LoanApplication"]["fields"])
        self.assertIn("CreditReport", obj_map)
        self.assertIn("score", obj_map["CreditReport"]["fields"])

    def test_parser_dsl_actions_all_present(self):
        """All five actions (3 manual + 2 auto) must appear as actions."""
        state = _minimal_state(metadata=json.dumps(_LOAN_METADATA))
        dsl = parser_node(state)["parser_dsl"]
        act_names = {a["name"] for a in dsl["actions"]}
        for expected in ("Fill Application", "Review Application", "Approve Loan",
                         "Verify Credit Score", "Notify Applicant"):
            self.assertIn(expected, act_names)

    def test_parser_dsl_auto_actions_have_auto_flag(self):
        state = _minimal_state(metadata=json.dumps(_LOAN_METADATA))
        dsl = parser_node(state)["parser_dsl"]
        auto_acts = {a["name"]: a for a in dsl["actions"] if a.get("auto") is True}
        self.assertIn("Verify Credit Score", auto_acts)
        self.assertIn("Notify Applicant", auto_acts)

    def test_parser_dsl_workflow_no_states_key(self):
        state = _minimal_state(metadata=json.dumps(_LOAN_METADATA))
        dsl = parser_node(state)["parser_dsl"]
        self.assertNotIn("states", dsl["workflow"])

    def test_parser_dsl_workflow_edges_action_to_action(self):
        """Decision node (ldec1) must be skipped; edges link Review→Approve and Review→Notify."""
        state = _minimal_state(metadata=json.dumps(_LOAN_METADATA))
        dsl = parser_node(state)["parser_dsl"]
        edges = dsl["workflow"]["edges"]
        # Each edge is [from, to] or [from, to, condition]
        pairs = {(e[0], e[1]) for e in edges}
        self.assertIn(("lact2", "lact3"), pairs)
        self.assertIn(("lact2", "lact5"), pairs)

    def test_parser_dsl_decision_edge_has_condition(self):
        """Edges born from a guarded controlflow edge carry the condition as 3rd element."""
        state = _minimal_state(metadata=json.dumps(_LOAN_METADATA))
        dsl = parser_node(state)["parser_dsl"]
        edges = {(e[0], e[1]): e for e in dsl["workflow"]["edges"]}
        approve_edge = edges.get(("lact2", "lact3"))
        self.assertIsNotNone(approve_edge)
        self.assertEqual(len(approve_edge), 3)
        self.assertEqual(approve_edge[2], "approved")


# ─────────────────────────────────────────────────────────────────────────────
# Unguarded decision node fallback
# ─────────────────────────────────────────────────────────────────────────────

_UNGUARDED_DECISION_METADATA = {
    "classifiers": [
        {
            "id": "ua1",
            "data": {
                "type": "actor", "role": "actor", "name": "User",
                "isAbstract": False, "attributes": [], "operations": [],
            },
            "system_id": "s1", "system_name": "Test",
        },
        {
            "id": "uact1",
            "data": {
                "type": "action", "role": "action", "name": "Start Process",
                "isAutomatic": False, "actorNode": "ua1", "actorNodeName": "User",
                "customCode": None, "localPrecondition": "", "localPostcondition": "",
                "body": "", "operation": None, "publish": None, "subscribe": None,
                "classes": None, "application_models": None, "page": None,
            },
            "system_id": "s1", "system_name": "Test",
        },
        {
            "id": "uact2",
            "data": {
                "type": "action", "role": "action", "name": "Path Alpha",
                "isAutomatic": False, "actorNode": "ua1", "actorNodeName": "User",
                "customCode": None, "localPrecondition": "", "localPostcondition": "",
                "body": "", "operation": None, "publish": None, "subscribe": None,
                "classes": None, "application_models": None, "page": None,
            },
            "system_id": "s1", "system_name": "Test",
        },
        {
            "id": "uact3",
            "data": {
                "type": "action", "role": "action", "name": "Path Beta",
                "isAutomatic": False, "actorNode": "ua1", "actorNodeName": "User",
                "customCode": None, "localPrecondition": "", "localPostcondition": "",
                "body": "", "operation": None, "publish": None, "subscribe": None,
                "classes": None, "application_models": None, "page": None,
            },
            "system_id": "s1", "system_name": "Test",
        },
        {
            "id": "udec1",
            "data": {"type": "decision", "role": "decision", "name": ""},
            "system_id": "s1", "system_name": "Test",
        },
    ],
    "relations": [
        # Start → decision (no guard)
        {"id": "ur1", "data": {"type": "controlflow", "guard": "", "weight": "", "condition": None, "is_directed": True, "position_handlers": []}, "source": "uact1", "target": "udec1"},
        # decision → Path Alpha (no guard, no condition — edge index 0 → branch_1)
        {"id": "ur2", "data": {"type": "controlflow", "guard": "", "weight": "", "condition": None, "is_directed": True, "position_handlers": []}, "source": "udec1", "target": "uact2"},
        # decision → Path Beta  (no guard, no condition — edge index 1 → branch_2)
        {"id": "ur3", "data": {"type": "controlflow", "guard": "", "weight": "", "condition": None, "is_directed": True, "position_handlers": []}, "source": "udec1", "target": "uact3"},
    ],
}


class UnguardedDecisionFallbackTests(unittest.TestCase):
    """Decision node with two exits carrying no guard and no condition.

    Both transitions must still receive a distinct condition label so
    the LLM can tell them apart.
    """

    def _dsl(self):
        from generator.agents.nodes import _build_parser_dsl
        return _build_parser_dsl(
            _UNGUARDED_DECISION_METADATA["classifiers"],
            _UNGUARDED_DECISION_METADATA["relations"],
        )

    def test_both_transitions_present(self):
        edges = self._dsl()["workflow"]["edges"]
        pairs = {(e[0], e[1]) for e in edges}
        self.assertIn(("uact1", "uact2"), pairs)
        self.assertIn(("uact1", "uact3"), pairs)

    def test_transitions_have_distinct_conditions(self):
        edges = {(e[0], e[1]): e for e in self._dsl()["workflow"]["edges"]}
        edge_alpha = edges[("uact1", "uact2")]
        edge_beta = edges[("uact1", "uact3")]
        # Both edges with fallback conditions must have 3 elements
        self.assertEqual(len(edge_alpha), 3, "branch with no guard must still get a fallback condition")
        self.assertEqual(len(edge_beta), 3, "branch with no guard must still get a fallback condition")
        self.assertNotEqual(edge_alpha[2], edge_beta[2], "fallback conditions must be distinct")

    def test_fallback_condition_labels(self):
        edges = {(e[0], e[1]): e for e in self._dsl()["workflow"]["edges"]}
        self.assertEqual(edges[("uact1", "uact2")][2], "branch_1")
        self.assertEqual(edges[("uact1", "uact3")][2], "branch_2")


# ─────────────────────────────────────────────────────────────────────────────
# _synthesise_pages
# ─────────────────────────────────────────────────────────────────────────────

_LOAN_DSL = {
    "domain": {"name": "Loan Application"},
    "actors": [
        {"id": "applicant", "name": "Applicant"},
        {"id": "officer",   "name": "Loan Officer"},
    ],
    "entities": [
        {"id": "lc1", "name": "LoanApplication", "fields": ["amount", "status"]},
    ],
    "actions": [
        {"id": "lact1", "name": "Fill in application",  "actor": "applicant", "input": ["lc1"]},
        {"id": "lact2", "name": "Submit application",   "actor": "applicant", "input": ["lc1"]},
        {"id": "lact3", "name": "Verify credit",        "actor": "applicant", "auto": True},
        {"id": "lact4", "name": "Review application",  "actor": "officer",   "input": ["lc1"]},
        {"id": "lact5", "name": "Final decision",      "actor": "officer",   "input": ["lc1"]},
    ],
    "workflow": {
        "nodes": ["lact1", "lact2", "lact3", "lact4", "lact5"],
        "edges": [
            ["lact1", "lact2"],
            ["lact2", "lact3"],
            ["lact3", "lact4"],
            ["lact4", "lact5", "approved"],
            ["lact4", "lact5", "rejected"],
        ],
    },
}


class SynthesisePagesTests(unittest.TestCase):

    _EMPTY = {"apps": [], "routing": {"auth_role_map": {}}}

    def test_empty_dsl_returns_empty(self):
        self.assertEqual(_synthesise_pages({}), self._EMPTY)

    def test_empty_actions_returns_empty(self):
        dsl = {"actors": [{"id": "a", "name": "A"}], "actions": [], "entities": [], "workflow": {"nodes": [], "edges": []}}
        self.assertEqual(_synthesise_pages(dsl), self._EMPTY)

    def test_auto_actions_produce_no_pages(self):
        dsl = {
            "actors": [{"id": "a", "name": "A"}],
            "entities": [],
            "actions": [{"id": "act1", "name": "Auto step", "actor": "a", "auto": True}],
            "workflow": {"nodes": ["act1"], "edges": []},
        }
        self.assertEqual(_synthesise_pages(dsl), self._EMPTY)

    def test_returns_ui_ir_dict(self):
        result = _synthesise_pages(_LOAN_DSL)
        self.assertIsInstance(result, dict)
        self.assertIn("apps", result)
        self.assertIn("routing", result)
        for app in result["apps"]:
            self.assertIsInstance(app, dict)

    def test_required_keys_present(self):
        result = _synthesise_pages(_LOAN_DSL)
        for app in result["apps"]:
            self.assertIn("actor_id", app)
            self.assertIn("pages", app)
            for page in app["pages"]:
                self.assertIn("name", page)
                self.assertIn("action_ids", page)

    def test_actors_never_mixed_on_same_page(self):
        result = _synthesise_pages(_LOAN_DSL)
        action_actor = {a["id"]: a.get("actor") for a in _LOAN_DSL["actions"]}
        for app in result["apps"]:
            for page in app["pages"]:
                for aid in page["action_ids"]:
                    self.assertEqual(action_actor.get(aid), app["actor_id"])

    def test_auto_actions_excluded_from_pages(self):
        result = _synthesise_pages(_LOAN_DSL)
        all_ids = [aid for app in result["apps"] for page in app["pages"] for aid in page["action_ids"]]
        self.assertNotIn("lact3", all_ids, "Auto action must not appear on any page")

    def test_actor_id_field_matches_dsl_actor_ids(self):
        result = _synthesise_pages(_LOAN_DSL)
        valid_actor_ids = {a["id"] for a in _LOAN_DSL["actors"]}
        for app in result["apps"]:
            self.assertIn(app["actor_id"], valid_actor_ids)

    def test_applicant_actions_grouped_together(self):
        """lact1 and lact2 share the same actor and are adjacent — expect them on the same page."""
        result = _synthesise_pages(_LOAN_DSL)
        applicant_ids = {
            aid
            for app in result["apps"] if app["actor_id"] == "applicant"
            for page in app["pages"]
            for aid in page["action_ids"]
        }
        self.assertIn("lact1", applicant_ids)
        self.assertIn("lact2", applicant_ids)

    def test_officer_actions_grouped_together(self):
        result = _synthesise_pages(_LOAN_DSL)
        officer_ids = {
            aid
            for app in result["apps"] if app["actor_id"] == "officer"
            for page in app["pages"]
            for aid in page["action_ids"]
        }
        self.assertIn("lact4", officer_ids)
        self.assertIn("lact5", officer_ids)

    def test_page_name_is_pascal_case(self):
        result = _synthesise_pages(_LOAN_DSL)
        for app in result["apps"]:
            for page in app["pages"]:
                self.assertRegex(page["name"], r'^[A-Z][A-Za-z0-9]*$',
                                 f"Page name not PascalCase: {page['name']}")

    def test_single_manual_action_becomes_one_page(self):
        dsl = {
            "actors": [{"id": "a1", "name": "Agent"}],
            "entities": [],
            "actions": [{"id": "act1", "name": "Do thing", "actor": "a1", "input": []}],
            "workflow": {"nodes": ["act1"], "edges": []},
        }
        result = _synthesise_pages(dsl)
        self.assertEqual(len(result["apps"]), 1)
        self.assertEqual(len(result["apps"][0]["pages"]), 1)
        self.assertEqual(result["apps"][0]["pages"][0]["action_ids"][0], "act1")

    def test_deterministic_same_input_same_output(self):
        pages_a = _synthesise_pages(_LOAN_DSL)
        pages_b = _synthesise_pages(_LOAN_DSL)
        self.assertEqual(pages_a, pages_b)

    def test_max_actions_per_page_respected(self):
        """6 connected actions for same actor must not all end up on one page."""
        actors = [{"id": "big", "name": "BigActor"}]
        entities = [{"id": "e1", "name": "Thing", "fields": ["x"]}]
        actions = [
            {"id": f"a{i}", "name": f"Step {i}", "actor": "big", "input": ["e1"]}
            for i in range(6)
        ]
        edges = [[f"a{i}", f"a{i+1}"] for i in range(5)]
        dsl = {"actors": actors, "entities": entities, "actions": actions,
               "workflow": {"nodes": [a["id"] for a in actions], "edges": edges}}
        result = _synthesise_pages(dsl)
        for app in result["apps"]:
            for page in app["pages"]:
                self.assertLessEqual(len(page["action_ids"]), 5, f"Page too large: {page}")

    def test_routing_contains_all_actors_with_pages(self):
        result = _synthesise_pages(_LOAN_DSL)
        actor_ids_in_apps = {app["actor_id"] for app in result["apps"]}
        auth_role_map = result["routing"]["auth_role_map"]
        self.assertEqual(set(auth_role_map.keys()), actor_ids_in_apps)

    def test_ui_designer_node_emits_page_ir(self):
        """ui_designer_node must store synthesised pages in state even when LLM fails."""
        with patch("generator.agents.nodes.call_openai") as mock_llm:
            mock_llm.side_effect = Exception("timeout")
            state = _minimal_state(
                parser_dsl=_LOAN_DSL,
                screens=[],
            )
            result = ui_designer_node(state)
        self.assertIn("page_ir", result)
        self.assertIsInstance(result["page_ir"], dict)
        self.assertIn("apps", result["page_ir"])
        # Auto action lact3 must be absent
        all_ids = [aid for app in result["page_ir"]["apps"]
                   for page in app["pages"] for aid in page["action_ids"]]
        self.assertNotIn("lact3", all_ids)

    def test_ui_designer_node_page_ir_in_prompt(self):
        """PAGE IR must appear in the prompt sent to the LLM."""
        with patch("generator.agents.nodes.call_openai") as mock_llm:
            mock_llm.return_value = json.dumps(_VALID_UI_DESIGN)
            state = _minimal_state(
                parser_dsl=_LOAN_DSL,
                screens=[],
            )
            ui_designer_node(state)
        prompt_arg = mock_llm.call_args[0][1]
        self.assertIn("PAGE IR", prompt_arg)
        self.assertIn("lact1", prompt_arg)


# ─────────────────────────────────────────────────────────────────────────────
# Parser → UI Designer integration tests
# ─────────────────────────────────────────────────────────────────────────────

class ParserToUIDesignerIntegrationTests(unittest.TestCase):
    """End-to-end integration tests: raw metadata → parser_node → ui_designer_node.

    All LLM calls are mocked.  Assertions cover page_ir structure and
    the relationship between parser output and ui_designer input/output.
    """

    def _build_state(self):
        """Build a full PipelineState from _LOAN_METADATA via the real parser helpers."""
        dsl = _build_parser_dsl(
            _LOAN_METADATA["classifiers"],
            _LOAN_METADATA["relations"],
        )
        screens = _build_screens(
            _LOAN_METADATA["classifiers"],
            _LOAN_METADATA["relations"],
        )
        return _minimal_state(
            project_name="LoanCo",
            application_name="loans",
            parser_dsl=dsl,
            screens=screens,
        )

    # ── page_ir presence and basic structure ─────────────────────────────────

    def test_page_ir_produced_from_loan_metadata(self):
        """ui_designer_node must emit a non-empty page_ir for the loan domain."""
        state = self._build_state()
        with patch("generator.agents.nodes.call_openai") as mock_llm:
            mock_llm.return_value = json.dumps(_VALID_UI_DESIGN)
            result = ui_designer_node(state)
        self.assertIn("page_ir", result)
        page_ir = result["page_ir"]
        self.assertIsInstance(page_ir, dict)
        self.assertIn("apps", page_ir)
        self.assertGreater(len(page_ir["apps"]), 0)

    def test_page_ir_entries_have_required_keys(self):
        """Every app entry must have actor_id + pages; every page must have name + action_ids."""
        state = self._build_state()
        with patch("generator.agents.nodes.call_openai") as mock_llm:
            mock_llm.return_value = json.dumps(_VALID_UI_DESIGN)
            result = ui_designer_node(state)
        for app in result["page_ir"]["apps"]:
            self.assertIn("actor_id", app, msg=f"App missing 'actor_id': {app}")
            self.assertIn("pages", app, msg=f"App missing 'pages': {app}")
            for page in app["pages"]:
                self.assertIn("name", page)
                self.assertIn("action_ids", page)

    def test_page_ir_action_ids_structure(self):
        """Each page must have a non-empty action_ids list of strings."""
        state = self._build_state()
        with patch("generator.agents.nodes.call_openai") as mock_llm:
            mock_llm.return_value = json.dumps(_VALID_UI_DESIGN)
            result = ui_designer_node(state)
        for app in result["page_ir"]["apps"]:
            for page in app["pages"]:
                self.assertIn("action_ids", page)
                self.assertGreater(len(page["action_ids"]), 0, msg=f"Page has no action_ids: {page}")
                for aid in page["action_ids"]:
                    self.assertIsInstance(aid, str)

    # ── actor isolation ───────────────────────────────────────────────────────

    def test_page_ir_actors_isolated(self):
        """Applicant actions (lact1) must not share a page with Loan Officer actions (lact2, lact3)."""
        state = self._build_state()
        with patch("generator.agents.nodes.call_openai") as mock_llm:
            mock_llm.return_value = json.dumps(_VALID_UI_DESIGN)
            result = ui_designer_node(state)
        for app in result["page_ir"]["apps"]:
            all_ids = {aid for page in app["pages"] for aid in page["action_ids"]}
            has_applicant = "lact1" in all_ids
            has_officer = bool(all_ids & {"lact2", "lact3"})
            self.assertFalse(
                has_applicant and has_officer,
                msg=f"Applicant and Loan Officer actions mixed in app: {app}",
            )

    def test_page_ir_actor_ids_match_parser(self):
        """actor_id fields must be actor ids that actually appear in the parser DSL."""
        state = self._build_state()
        dsl_actor_ids = {a["id"] for a in state["parser_dsl"]["actors"]}
        with patch("generator.agents.nodes.call_openai") as mock_llm:
            mock_llm.return_value = json.dumps(_VALID_UI_DESIGN)
            result = ui_designer_node(state)
        for app in result["page_ir"]["apps"]:
            self.assertIn(
                app["actor_id"],
                dsl_actor_ids,
                msg=f"actor_id '{app['actor_id']}' not in DSL actor ids {dsl_actor_ids}",
            )

    # ── auto-action exclusion ─────────────────────────────────────────────────

    def test_auto_actions_not_in_page_ir(self):
        """Automatic actions (lact4 Verify Credit Score, lact5 Notify Applicant) must be absent."""
        state = self._build_state()
        with patch("generator.agents.nodes.call_openai") as mock_llm:
            mock_llm.return_value = json.dumps(_VALID_UI_DESIGN)
            result = ui_designer_node(state)
        all_ids = [aid for app in result["page_ir"]["apps"]
                   for page in app["pages"] for aid in page["action_ids"]]
        self.assertNotIn("lact4", all_ids, "Auto action lact4 must not appear in page_ir")
        self.assertNotIn("lact5", all_ids, "Auto action lact5 must not appear in page_ir")

    def test_page_ir_actions_cover_all_manual_actions(self):
        """All three manual actions (lact1, lact2, lact3) must appear somewhere in page_ir."""
        state = self._build_state()
        with patch("generator.agents.nodes.call_openai") as mock_llm:
            mock_llm.return_value = json.dumps(_VALID_UI_DESIGN)
            result = ui_designer_node(state)
        all_ids = {aid for app in result["page_ir"]["apps"]
                   for page in app["pages"] for aid in page["action_ids"]}
        for manual_id in ("lact1", "lact2", "lact3"):
            self.assertIn(manual_id, all_ids, msg=f"Manual action {manual_id} missing from page_ir")

    # ── ui_design output ─────────────────────────────────────────────────────

    def test_ui_design_present_when_llm_succeeds(self):
        """result['ui_design'] must be non-None when LLM returns valid JSON."""
        state = self._build_state()
        with patch("generator.agents.nodes.call_openai") as mock_llm:
            mock_llm.return_value = json.dumps(_VALID_UI_DESIGN)
            result = ui_designer_node(state)
        self.assertIsNotNone(result.get("ui_design"))

    def test_page_ir_persisted_even_on_llm_failure(self):
        """page_ir must be written to state even when the LLM call raises."""
        state = self._build_state()
        with patch("generator.agents.nodes.call_openai") as mock_llm:
            mock_llm.side_effect = RuntimeError("network error")
            result = ui_designer_node(state)
        self.assertIn("page_ir", result)
        self.assertIsInstance(result["page_ir"], dict)
        self.assertGreater(len(result["page_ir"]["apps"]), 0)

    # ── prompt content ────────────────────────────────────────────────────────

    def test_pages_in_prompt_reflect_synthesised_structure(self):
        """The LLM prompt must contain 'PAGE IR' and actor ids la1/la2."""
        state = self._build_state()
        with patch("generator.agents.nodes.call_openai") as mock_llm:
            mock_llm.return_value = json.dumps(_VALID_UI_DESIGN)
            ui_designer_node(state)
        prompt_arg = mock_llm.call_args[0][1]
        self.assertIn("PAGE IR", prompt_arg)
        # Actor ids from _LOAN_METADATA — la1 owns lact1, la2 owns lact2/lact3
        self.assertIn("la1", prompt_arg)
        self.assertIn("la2", prompt_arg)

