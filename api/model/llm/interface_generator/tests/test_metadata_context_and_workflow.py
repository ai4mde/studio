import importlib
import sys
import types


class RelatedList:
    def __init__(self, items):
        """Initialize the test helper object."""
        self._items = items

    def all(self):
        """Provide a fake queryset all helper for tests."""
        return list(self._items)


class QuerySet(list):
    def prefetch_related(self, *args):
        """Provide a fake queryset prefetch_related helper for tests."""
        return self

    def first(self):
        """Provide a fake queryset first helper for tests."""
        return self[0] if self else None


class Manager:
    def __init__(self, items=None, getter=None):
        """Initialize the test helper object."""
        self.items = list(items or [])
        self.getter = getter
        self.updated = []

    def prefetch_related(self, *args):
        """Provide a fake queryset prefetch_related helper for tests."""
        return self

    def get(self, **kwargs):
        """Provide a fake queryset get helper for tests."""
        if self.getter:
            return self.getter(**kwargs)
        for item in self.items:
            if all(str(getattr(item, key)) == str(value) for key, value in kwargs.items()):
                return item
        raise LookupError(kwargs)

    def filter(self, **kwargs):
        """Provide a fake queryset filter helper for tests."""
        found = []
        for item in self.items:
            if all(getattr(item, key) == value for key, value in kwargs.items()):
                found.append(item)
        return QuerySet(found)

    def update(self, **kwargs):
        """Provide a fake queryset update helper for tests."""
        self.updated.append(kwargs)
        return 1


class Obj:
    def __init__(self, **kwargs):
        """Initialize the test helper object."""
        self.__dict__.update(kwargs)


def install_fake_django_modules(system=None, diagrams=None):
    """Provide the install fake Django modules test helper."""
    diagram_pkg = types.ModuleType("diagram")
    diagram_models = types.ModuleType("diagram.models")
    metadata_pkg = types.ModuleType("metadata")
    metadata_models = types.ModuleType("metadata.models")

    class FakeDiagram:
        objects = Manager(diagrams or [])

    class FakeSystem:
        objects = Manager([system] if system else [])

    diagram_models.Diagram = FakeDiagram
    metadata_models.System = FakeSystem
    metadata_models.Classifier = type("Classifier", (), {"objects": Manager([])})
    metadata_models.Interface = type("Interface", (), {"objects": Manager([])})

    sys.modules["diagram"] = diagram_pkg
    sys.modules["diagram.models"] = diagram_models
    sys.modules["metadata"] = metadata_pkg
    sys.modules["metadata.models"] = metadata_models
    return metadata_models, diagram_models


def import_fresh(module_name):
    """Provide the import fresh test helper."""
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_node_position_prefers_position_object_and_falls_back_to_coordinates():
    """Verify that node position prefers position object and falls back to coordinates."""
    install_fake_django_modules()
    mc = import_fresh("llm.interface_generator.uml_mapping.metadata_context")

    assert mc._node_position(Obj(data={"position": {"x": 10, "y": 20}, "x": 1, "y": 2})) == (10, 20)
    assert mc._node_position(Obj(data={"x": 3, "y": 4})) == (3, 4)


def test_fetch_system_context_data_builds_full_context_from_orm_shape(monkeypatch):
    """Verify that fetch system context data builds full context from orm shape."""
    classifier = Obj(
        id="actor",
        project_id="project",
        system_id="system",
        original_system_id=None,
        data={"type": "actor", "name": "Customer"},
    )
    relation = Obj(id="rel", system_id="system", source_id="actor", target_id="uc", data={"type": "interaction"})
    interface = Obj(id="iface", name="Customer UI", description="desc", system_id="system", actor_id="actor", data={"pages": []})
    node = Obj(id="node", diagram_id="diagram", cls_id="actor", data={"position": {"x": 7, "y": 8}})
    edge = Obj(id="edge", diagram_id="diagram", rel_id="rel", data={"label": "uses"})
    diagram = Obj(
        id="diagram",
        name="Use Cases",
        description="desc",
        type="usecase",
        system_id="system",
        system=None,
        nodes=RelatedList([node]),
        edges=RelatedList([edge]),
    )
    system = Obj(
        id="system",
        name="Shop",
        description="desc",
        project_id="project",
        classifiers=RelatedList([classifier]),
        relations=RelatedList([relation]),
        interfaces=RelatedList([interface]),
    )
    diagram.system = system
    install_fake_django_modules(system=system, diagrams=[diagram])
    mc = import_fresh("llm.interface_generator.uml_mapping.metadata_context")
    monkeypatch.setattr(mc, "_build_activity_diagrams", lambda context: [{"name": "Activity"}])

    context = mc._fetch_system_context_data("system")

    assert context["id"] == "system"
    assert context["classifiers"][0]["data"]["name"] == "Customer"
    assert context["relations"][0]["source"] == "actor"
    assert context["diagrams"][0]["nodes"][0]["x"] == 7
    assert context["nodes"][0]["y"] == 8
    assert context["interfaces"][0]["actor"] == "actor"
    assert context["activity_diagrams"] == [{"name": "Activity"}]


def test_actor_name_from_context_finds_classifier_name():
    """Verify that actor name from context finds classifier name."""
    install_fake_django_modules()
    mc = import_fresh("llm.interface_generator.uml_mapping.metadata_context")

    assert mc._actor_name_from_context({"classifiers": [{"id": "a", "data": {"name": "Seller"}}]}, "a") == "Seller"
    assert mc._actor_name_from_context({"classifiers": []}, "missing") is None


def test_apply_builtin_workflow_logic_fetches_context_and_normalizes(monkeypatch):
    """Verify that apply builtin workflow logic fetches context and normalizes."""
    system_context = {
        "classifiers": [{"id": "actor", "data": {"type": "actor", "name": "Customer"}}],
    }
    install_fake_django_modules()
    wa = import_fresh("llm.interface_generator.workflow_application")
    monkeypatch.setattr(wa, "_fetch_system_context_data", lambda system_id: system_context)
    monkeypatch.setattr(wa, "_actor_name_from_context", lambda context, actor_id: "Customer")
    monkeypatch.setattr(
        wa,
        "_build_usecase_navigation",
        lambda context, actor_id, actor_name: {"workflow_steps": [{"page_id": "checkout"}]},
    )
    monkeypatch.setattr(
        wa,
        "_ensure_workflow_pages",
        lambda pages, sections, steps, attrs, nav: (
            pages + [{"id": "checkout", "name": "Checkout", "type": {"value": "activity", "label": "Activity"}, "sections": []}],
            sections + [{"id": "action", "layout": "activity_action", "position": "main"}],
        ),
    )

    result = wa._apply_builtin_workflow_logic({"pages": [], "sections": []}, "system", "actor")

    assert result["pages"][0]["id"] == "checkout"
    assert result["sections"][0]["id"] == "action"


def test_apply_builtin_workflow_logic_accepts_precomputed_context(monkeypatch):
    """Verify that apply builtin workflow logic accepts precomputed context."""
    install_fake_django_modules()
    wa = import_fresh("llm.interface_generator.workflow_application")
    called = {"fetch": False}
    monkeypatch.setattr(wa, "_fetch_system_context_data", lambda system_id: called.__setitem__("fetch", True))

    result = wa._apply_builtin_workflow_logic(
        {"pages": [{"id": "p", "sections": []}], "sections": []},
        None,
        None,
        system_context={"classifiers": []},
        usecase_navigation={"workflow_steps": []},
        model_attrs={},
    )

    assert called["fetch"] is False
    assert result["pages"][0]["id"] == "p"
