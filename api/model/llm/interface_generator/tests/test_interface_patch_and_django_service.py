import importlib
import json
import sys
import types


class QuerySet(list):
    def update(self, **kwargs):
        """Provide a fake queryset update helper for tests."""
        for item in self:
            for key, value in kwargs.items():
                setattr(item, key, value)
        return len(self)

    def order_by(self, *args):
        """Provide a fake queryset order_by helper for tests."""
        return self

    def first(self):
        """Provide a fake queryset first helper for tests."""
        return self[0] if self else None


class Manager:
    def __init__(self, items=None, exc=None):
        """Initialize the test helper object."""
        self.items = list(items or [])
        self.exc = exc or type("DoesNotExist", (Exception,), {})

    def get(self, **kwargs):
        """Provide a fake queryset get helper for tests."""
        for item in self.items:
            if all(str(getattr(item, key)) == str(value) for key, value in kwargs.items()):
                return item
        raise self.exc()

    def filter(self, **kwargs):
        """Provide a fake queryset filter helper for tests."""
        return QuerySet([
            item
            for item in self.items
            if all(str(getattr(item, key)) == str(value) for key, value in kwargs.items())
        ])

    def prefetch_related(self, *args):
        """Provide a fake queryset prefetch_related helper for tests."""
        return self


class Obj:
    def __init__(self, **kwargs):
        """Initialize the test helper object."""
        self.__dict__.update(kwargs)


class RelatedList:
    def __init__(self, items):
        """Initialize the test helper object."""
        self.items = list(items)

    def all(self):
        """Provide a fake queryset all helper for tests."""
        return list(self.items)


def install_fake_modules(interfaces=None, classifiers=None, systems=None):
    """Provide the install fake modules test helper."""
    metadata_pkg = types.ModuleType("metadata")
    metadata_models = types.ModuleType("metadata.models")
    diagram_pkg = types.ModuleType("diagram")
    diagram_models = types.ModuleType("diagram.models")
    iface_exc = type("InterfaceDoesNotExist", (Exception,), {})

    class FakeInterface:
        objects = Manager(interfaces or [], iface_exc)

    setattr(FakeInterface, "DoesNotExist", iface_exc)

    class FakeClassifier:
        objects = Manager(classifiers or [])

    class FakeSystem:
        objects = Manager(systems or [])

    metadata_models.Interface = FakeInterface
    metadata_models.Classifier = FakeClassifier
    metadata_models.System = FakeSystem
    diagram_models.Diagram = type("Diagram", (), {"objects": Manager([])})
    sys.modules["metadata"] = metadata_pkg
    sys.modules["metadata.models"] = metadata_models
    sys.modules["diagram"] = diagram_pkg
    sys.modules["diagram.models"] = diagram_models

    edit_prompt = types.ModuleType("llm.prompts.interface_edit")
    edit_prompt.build_interface_edit_prompt = lambda **kwargs: "edit prompt"
    semantics_prompt = types.ModuleType("llm.prompts.semantics")
    semantics_prompt.build_resolve_interface_semantics_prompt = lambda **kwargs: "semantics prompt"
    sys.modules["llm.prompts.interface_edit"] = edit_prompt
    sys.modules["llm.prompts.semantics"] = semantics_prompt

    return metadata_models


def import_fresh(module_name):
    """Provide the import fresh test helper."""
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def make_interface(data=None):
    """Provide the make interface test helper."""
    return Obj(
        id="iface",
        name="Customer UI",
        description="desc",
        system_id="system",
        actor_id="actor",
        data=data or {},
    )


def test_build_known_attrs_from_orm_collects_classifier_fields():
    """Verify that build known attrs from orm collects classifier fields."""
    classifiers = [
        Obj(system_id="system", data={"name": "Product", "attributes": [{"name": "name"}, {"name": "price"}]}),
        Obj(system_id="system", data={"name": "", "attributes": [{"name": "ignored"}]}),
    ]
    install_fake_modules(classifiers=classifiers)
    patcher = import_fresh("llm.interface_generator.interface_patch")

    assert patcher._build_known_attrs_from_orm("system") == {"Product": {"name", "price"}}


def test_apply_interface_patch_merges_pages_sections_tokens_and_rejects_unknown_attrs(monkeypatch):
    """Verify that apply interface patch merges pages sections tokens and rejects unknown attrs."""
    interface = make_interface({
        "pages": [{"id": "p", "name": "Old", "sections": []}],
        "sections": [{"id": "s", "layout": "card", "primary_model": "Product", "attributes": ["name"]}],
        "tokens": {"base": "x"},
        "styling": {"radius": 4},
    })
    classifiers = [Obj(system_id="system", data={"name": "Product", "attributes": [{"name": "name"}]})]
    install_fake_modules(interfaces=[interface], classifiers=classifiers)
    patcher = import_fresh("llm.interface_generator.interface_patch")
    monkeypatch.setattr(patcher, "_apply_builtin_workflow_logic", lambda data, system_id, actor_id: data)

    warning = patcher.apply_interface_patch("iface", {
        "sections": [{"id": "s", "primary_model": "Product", "attributes": ["invented"]}],
    })
    assert warning.startswith("WARNING")

    result = patcher.apply_interface_patch("iface", {
        "pages": [{"id": "p", "name": "New", "sections": ["s"]}, {"id": "p2", "sections": [{"type": "card", "sections": ["s"]}]}],
        "sections": [{"id": "s", "style": {"color": "accent"}, "attributes": ["name"], "item_actions": [{"label": "Compare"}]}],
        "tokens": {"accent.hex": "#123"},
        "styling": {"radius": 8},
    })

    assert result == "Patched interface iface successfully."
    assert interface.data["pages"][0]["name"] == "New"
    assert interface.data["pages"][0]["sections"] == [{"value": "s"}]
    assert interface.data["sections"][0]["style"]["color"] == "accent"
    assert "item_actions" not in interface.data["sections"][0]
    assert interface.data["tokens"]["accent.hex"] == "#123"
    assert interface.data["styling"]["radius"] == 8


def test_interface_to_agent_dict_serializes_interface():
    """Verify that interface to agent dict serializes interface."""
    interface = make_interface({"pages": []})
    install_fake_modules()
    ds = import_fresh("llm.interface_generator.django_service")

    assert ds._interface_to_agent_dict(interface) == {
        "id": "iface",
        "name": "Customer UI",
        "description": "desc",
        "system": "system",
        "actor": "actor",
        "data": {"pages": []},
    }


def test_sync_method_to_interface_sections_updates_matching_sections():
    """Verify that sync method to interface sections updates matching sections."""
    interface = make_interface({
        "sections": [
            {"id": "a", "class": "product", "methods": [{"name": "restock"}]},
            {"id": "b", "class": "Product", "methods": []},
        ]
    })
    install_fake_modules(interfaces=[interface])
    ds = import_fresh("llm.interface_generator.django_service")

    ds._sync_method_to_interface_sections("product", "Product", {"name": "restock", "body": "return 1"}, "system")

    assert interface.data["sections"][0]["methods"][0]["body"] == "return 1"
    assert interface.data["sections"][1]["methods"][0]["name"] == "restock"


def test_generate_missing_method_bodies_updates_classifier_and_syncs(monkeypatch):
    """Verify that generate missing method bodies updates classifier and syncs."""
    classifier = Obj(
        id="product",
        system_id="system",
        data={"type": "class", "name": "Product", "methods": [{"name": "score", "description": "Score it"}]},
    )
    install_fake_modules(classifiers=[classifier])
    ds = import_fresh("llm.interface_generator.django_service")
    handler_mod = types.ModuleType("llm.handler")
    handler_mod.llm_handler = lambda **kwargs: "def score(self):\n    return 1"
    handler_mod.remove_reply_markdown = lambda text: text
    sys.modules["llm.handler"] = handler_mod

    ds._generate_missing_method_bodies(
        {"classifiers": [{"id": "product", "data": classifier.data}]},
        {"Product": {"attributes": [{"name": "name", "type": "str"}], "associations": []}},
        "system",
    )

    assert classifier.data["methods"][0]["body"] == "def score(self):\n    return 1"


def test_sync_all_classifier_methods_to_interfaces_calls_sync(monkeypatch):
    """Verify that sync all classifier methods to interfaces calls sync."""
    classifier = Obj(
        id="product",
        system_id="system",
        data={"type": "class", "name": "Product", "methods": [{"name": "score", "body": "return 1"}]},
    )
    install_fake_modules(classifiers=[classifier])
    ds = import_fresh("llm.interface_generator.django_service")
    calls = []
    monkeypatch.setattr(ds, "_sync_method_to_interface_sections", lambda *args: calls.append(args))

    ds._sync_all_classifier_methods_to_interfaces("system")

    synced_call = next(iter(calls), None)
    assert synced_call is not None
    assert tuple(synced_call[0:3]) == ("product", "Product", {"name": "score", "body": "return 1"})


def test_ensure_action_panel_sections_adds_detail_page_actions():
    """Verify that ensure action panel sections adds detail page actions."""
    interface = make_interface({
        "pages": [{"id": "detail", "sections": [{"value": "detail_sec"}]}],
        "sections": [{"id": "detail_sec", "role": "object_detail", "class": "Product"}],
    })
    classifier = Obj(
        id="product",
        system_id="system",
        data={"type": "class", "name": "Product", "methods": [{"name": "score", "body": "return 1"}]},
    )
    install_fake_modules(interfaces=[interface], classifiers=[classifier])
    ds = import_fresh("llm.interface_generator.django_service")

    ds._ensure_action_panel_sections("iface", "system")

    assert interface.data["sections"][-1]["id"] == "detail_product_action_panel"
    assert interface.data["pages"][0]["sections"][-1] == {"value": "detail_product_action_panel"}


def test_resolve_interface_semantics_with_llm_filters_model_and_step_overrides(monkeypatch):
    """Verify that resolve interface semantics with LLM filters model and step overrides."""
    install_fake_modules()
    ds = import_fresh("llm.interface_generator.django_service")
    monkeypatch.setenv("GEMINI_API_KEY", "key")
    response_payload = {
        "actor_model_scopes": {"Product": "collection", "Hidden": "collection"},
        "models": {"Product": {"layout": "table", "component": "DataTable"}, "Hidden": {"layout": "map", "component": "MapView"}},
        "activity_steps": {"Review": {"layout": "detail", "component": "DetailPanel", "role": "object_detail", "model": "Product", "readonly_fields": ["name", "bad"]}},
        "workflow_steps": {"Review": {"intent": "check", "target_model": "Product", "editable_fields": ["price"], "condition": {"model": "Product", "field": "price", "operator": ">", "threshold": "0"}}},
    }

    class Response:
        def raise_for_status(self):
            """Provide the raise for status test helper."""
            return None

        def json(self):
            """Provide the json test helper."""
            return {"candidates": [{"content": {"parts": [{"text": json.dumps(response_payload)}]}}]}

    monkeypatch.setattr(ds._req, "post", lambda *args, **kwargs: Response())

    result = ds.resolve_interface_semantics_with_llm(
        {
            "semantic_decisions": [{"question": "q"}],
            "actor_intel": {"target_permissions": {"Product": ["read"]}},
            "model_graph": {"Product": {"attributes": [{"name": "name"}, {"name": "price"}]}},
            "workflow_intel": {"workflows": [{"steps": [{"action": "Review"}]}]},
        },
        {"pages": []},
    )

    assert result["actor_model_scopes"] == {"Product": "collection"}
    assert result["models"] == {"Product": {"layout": "table", "component": "DataTable"}}
    assert result["activity_steps"]["Review"]["readonly_fields"] == ["name"]
    assert result["workflow_steps"]["Review"]["condition"]["field"] == "price"
    assert ds.resolve_interface_semantics_with_llm({"semantic_decisions": []}, {}) == {}


def test_debug_uml_extract_returns_diagnostics(monkeypatch):
    """Verify that debug UML extract returns diagnostics."""
    interface = make_interface()
    install_fake_modules(interfaces=[interface])
    ds = import_fresh("llm.interface_generator.django_service")
    monkeypatch.setattr(ds, "_fetch_system_context_data", lambda system_id: {"relations": [{"data": {"type": "association"}}]})
    monkeypatch.setattr(ds, "_actor_name_from_context", lambda data, actor: "Customer")
    monkeypatch.setattr(ds, "extract_uml_intelligence", lambda data, actor_id, actor_name: {
        "model_graph": {"Product": {"compositions_owned": [], "associations": []}},
        "actor_intel": {"target_permissions": {"Product": ["read"]}, "target_use_cases": [{"name": "Browse", "primary_model": "Product", "page_role": "collection"}]},
        "workflow_intel": {"workflows": [{"name": "Flow", "step_count": 1, "steps": [{"action": "Review", "model": "Product"}]}]},
        "semantic_decisions": [],
    })
    monkeypatch.setattr(ds, "generate_interface_plan", lambda intel: {"pages": [{"id": "p", "primary_model": "Product", "sections": ["s"]}], "sections": [{"id": "s", "component": "DataTable"}]})

    result = ds.debug_uml_extract("iface")

    assert result["actor"] == "Customer"
    assert result["rel_types_in_data"] == ["association"]
    assert result["plan_sections"] == [{"id": "s", "component": "DataTable"}]


def test_map_uml_to_interface_runs_mapping_pipeline(monkeypatch):
    """Verify that map UML to interface runs mapping pipeline."""
    interface = make_interface({"existing": True})
    install_fake_modules(interfaces=[interface])
    ds = import_fresh("llm.interface_generator.django_service")
    monkeypatch.setattr(ds, "_fetch_system_context_data", lambda system_id: {"classifiers": []})
    monkeypatch.setattr(ds, "_actor_name_from_context", lambda context, actor_id: "Customer")
    monkeypatch.setattr(ds, "extract_uml_intelligence", lambda context, actor_id, actor_name: {"model_graph": {}, "actor_intel": {}, "workflow_intel": {}})
    monkeypatch.setattr(ds, "_generate_missing_method_bodies", lambda *args: None)
    monkeypatch.setattr(ds, "generate_interface_plan", lambda intel, overrides=None: {"pages": [{"id": "p", "sections": ["s"]}], "sections": [{"id": "s", "layout": "card", "attributes": []}]})
    monkeypatch.setattr(ds, "resolve_interface_semantics_with_llm", lambda *args: {})
    monkeypatch.setattr(ds, "_build_usecase_navigation", lambda *args: {"workflow_steps": []})
    monkeypatch.setattr(ds, "_apply_builtin_workflow_logic", lambda data, *args, **kwargs: data)
    monkeypatch.setattr(ds, "_ensure_mapping_content_sections", lambda pages, sections, nav, attrs, graph: (pages, sections))
    monkeypatch.setattr(ds, "_ensure_mapping_chrome_sections", lambda pages, sections: (pages, sections))
    monkeypatch.setattr(ds, "_drop_unreferenced_non_global_sections", lambda pages, sections: sections)
    monkeypatch.setattr(ds, "_sync_all_classifier_methods_to_interfaces", lambda system_id: None)
    monkeypatch.setattr(ds, "_ensure_action_panel_sections", lambda interface_id, system_id: None)

    result = ds.map_uml_to_interface("iface")

    assert result["status"] == "ok"
    assert interface.data["pages"][0]["id"] == "p"
    assert interface.data["sections"][0]["id"] == "s"
    assert ds.map_uml_to_interface("")["status"] == "error"


def test_map_uml_to_all_interfaces_aggregates_results(monkeypatch):
    """Verify that map UML to all interfaces aggregates results."""
    interfaces = [make_interface(), Obj(id="iface2", name="Seller UI", description="", system_id="system", actor_id="seller", data={})]
    install_fake_modules(interfaces=interfaces)
    ds = import_fresh("llm.interface_generator.django_service")
    monkeypatch.setattr(ds, "map_uml_to_interface", lambda interface_id: {"status": "ok", "message": f"mapped {interface_id}"})

    result = ds.map_uml_to_all_interfaces("system")

    assert result["message"] == "Mapped 2/2 interfaces."
    assert result["results"][1]["interface_id"] == "iface2"
    assert ds.map_uml_to_all_interfaces("")["status"] == "error"


def install_fake_genai_patch(text):
    """Provide the install fake genai patch test helper."""
    google_pkg = types.ModuleType("google")
    genai = types.ModuleType("google.genai")

    class Models:
        def generate_content(self, **kwargs):
            """Provide the generate content test helper."""
            return Obj(text=text)

    class Client:
        def __init__(self, api_key=""):
            """Initialize the test helper object."""
            self.models = Models()

    genai.Client = Client
    sys.modules["google"] = google_pkg
    sys.modules["google.genai"] = genai


def test_apply_prompt_to_interface_uses_llm_patch(monkeypatch):
    """Verify that apply prompt to interface uses LLM patch."""
    interface = make_interface({"pages": [], "sections": []})
    install_fake_modules(interfaces=[interface])
    ds = import_fresh("llm.interface_generator.django_service")

    assert ds.apply_prompt_to_interface("", "system", "edit")["status"] == "error"
    assert ds.apply_prompt_to_interface("iface", "system", "")["status"] == "error"
    monkeypatch.setenv("GEMINI_API_KEY", "key")
    install_fake_genai_patch('{"tokens":{"accent.hex":"#123"}}')
    monkeypatch.setattr(ds, "_fetch_system_context_data", lambda system_id: {"classifiers": []})
    monkeypatch.setattr(ds, "_actor_name_from_context", lambda context, actor_id: "Customer")
    monkeypatch.setattr(ds, "apply_interface_patch", lambda interface_id, patch: f"Patched interface {interface_id} successfully.")

    result = ds.apply_prompt_to_interface("iface", "system", "change accent")

    assert result["status"] == "ok"
    assert result["patch"] == {"tokens": {"accent.hex": "#123"}}
