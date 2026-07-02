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
