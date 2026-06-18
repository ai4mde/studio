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


class RelatedList:
    def __init__(self, items):
        """Initialize the test helper object."""
        self.items = list(items)

    def all(self):
        """Provide a fake queryset all helper for tests."""
        return list(self.items)


class Obj:
    def __init__(self, **kwargs):
        """Initialize the test helper object."""
        self.__dict__.update(kwargs)


def import_candidate_generation(interface_items=None):
    """Provide the import candidate generation test helper."""
    sys.modules.pop("llm.interface_generator.candidate_generation", None)
    sys.modules.pop("llm.interface_generator.uml_mapping.metadata_context", None)
    metadata_pkg = types.ModuleType("metadata")
    metadata_models = types.ModuleType("metadata.models")
    diagram_pkg = types.ModuleType("diagram")
    diagram_models = types.ModuleType("diagram.models")
    does_not_exist = type("DoesNotExist", (Exception,), {})

    class FakeInterface:
        DoesNotExist = does_not_exist
        objects = Manager(interface_items or [], does_not_exist)

    metadata_models.Interface = FakeInterface
    metadata_models.System = type("System", (), {"objects": Manager([])})
    diagram_models.Diagram = type("Diagram", (), {"objects": Manager([])})
    sys.modules["metadata"] = metadata_pkg
    sys.modules["metadata.models"] = metadata_models
    sys.modules["diagram"] = diagram_pkg
    sys.modules["diagram.models"] = diagram_models

    renderer = types.ModuleType("llm.template_renderer")
    renderer.render_layout = lambda **kwargs: [{"name": "index.html", "content": "<main>ok</main>"}]
    sys.modules["llm.template_renderer"] = renderer

    prompts = types.ModuleType("llm.prompts.candidates")
    prompts.GENERATE_CANDIDATES_SYSTEM_PROMPT = "generate"
    prompts.REGENERATE_CANDIDATES_SYSTEM_PROMPT = "regenerate"
    prompts.build_generate_candidates_prompt = lambda **kwargs: "generate prompt"
    prompts.build_regenerate_candidates_prompt = lambda **kwargs: "regenerate prompt"
    sys.modules["llm.prompts.candidates"] = prompts

    return importlib.import_module("llm.interface_generator.candidate_generation")


def make_interface(data=None):
    """Provide the make interface test helper."""
    classifier = Obj(id="product", data={"type": "class", "name": "Product", "attributes": [{"name": "name"}, {"name": "price"}]})
    relation = Obj(id="rel", source_id="product", target_id="product", data={})
    system = Obj(
        classifiers=RelatedList([classifier]),
        relations=RelatedList([relation]),
    )
    return Obj(
        id="iface",
        name="Shop UI",
        description="desc",
        system_id="system",
        actor_id="actor",
        system=system,
        data=data or {},
    )


def test_render_candidate_preview_local_updates_candidate_preview():
    """Verify that render candidate preview local updates candidate preview."""
    interface = make_interface({"candidates": [{"pages": [{"id": "p"}], "sections": []}]})
    cg = import_candidate_generation([interface])

    result = cg._render_candidate_preview_local("iface", 0)

    assert result == "OK: preview rendered for candidate 0."
    candidate = interface.data["candidates"][0]
    assert "preview_html" in candidate
    assert candidate["preview_files"][0]["content"] == "<main>ok</main>"
    assert "candidate 5 not found" in cg._render_candidate_preview_local("iface", 5)


def test_candidate_styling_and_tokens_normalize_json_and_aliases():
    """Verify that candidate styling and tokens normalize json and aliases."""
    cg = import_candidate_generation()

    styling = cg._norm_candidate_styling('{"accent_color":"#111","radius":"lg"}')
    assert styling["accentColor"] == "#111"
    assert styling["radius"] == 12

    tokens = cg._norm_candidate_tokens('{"x":"y"}', {"region.header.bg_hex": "#fff"})
    assert tokens["x"] == "y"
    assert tokens["region.header.bg_hex"] == "#fff"
    assert cg._norm_candidate_tokens("not-json") == {}


def test_validate_and_save_candidate_normalizes_and_persists(monkeypatch):
    """Verify that validate and save candidate normalizes and persists."""
    interface = make_interface({"pages": [], "sections": [], "candidates": []})
    cg = import_candidate_generation([interface])
    monkeypatch.setattr(cg, "_fetch_system_context_data", lambda system_id: (_ for _ in ()).throw(RuntimeError("skip")))

    result = cg.validate_and_save_candidate(
        "iface",
        0,
        "",
        "desc",
        json.dumps([{"id": "p", "name": "Product", "sections": [{"value": "s"}], "primary_model": "Product"}]),
        json.dumps([{
            "id": "s",
            "layout": "unknown",
            "primary_model": "Product",
            "attributes": ["name", "invented"],
            "item_actions": [{"label": "Compare"}],
        }]),
        tokens='{"accent.hex":"#123"}',
        styling='{"radius":"sm"}',
        prompt="make it usable",
    )

    assert result.startswith("OK: candidate 0")
    candidate = interface.data["candidates"][0]
    assert candidate["name"] == "Agent Gallery"
    assert candidate["tokens"]["accent.hex"] == "#123"
    assert candidate["styling"]["radius"] == 4
    assert candidate["pages"][0]["category"]
    assert "item_actions" not in candidate["sections"][0]


def test_get_candidate_regeneration_context_uses_candidate_or_saved_base():
    """Verify that get candidate regeneration context uses candidate or saved base."""
    interface = make_interface({
        "tokens": {"base": "token"},
        "styling": {"base": "style"},
        "candidates": [{"id": "c0", "name": "Base", "pages": [{"id": "p"}], "sections": [{"id": "s"}]}],
        "regeneration_base_candidate": {"selected_candidate_index": 2, "candidate": {"id": "fallback", "pages": [], "sections": []}},
    })
    cg = import_candidate_generation([interface])

    context = json.loads(cg.get_candidate_regeneration_context("iface", 0, "brighter"))
    fallback = json.loads(cg.get_candidate_regeneration_context("iface", 2, "brighter"))

    assert context["base_candidate"]["id"] == "c0"
    assert context["designer_requirements"] == "brighter"
    assert fallback["base_candidate"]["id"] == "fallback"
    assert cg.get_candidate_regeneration_context("iface", 9).startswith("ERROR: candidate")


def test_candidate_variant_name_cycles_labels():
    """Verify that candidate variant name cycles labels."""
    cg = import_candidate_generation()

    assert cg._candidate_variant_name("ignored", 0) == "Agent Gallery"
    assert cg._candidate_variant_name("ignored", 1) == "Agent Table"
    assert cg._candidate_variant_name("ignored", 2) == "Agent Showcase"
    assert cg._candidate_variant_name("ignored", 3) == "Agent Gallery"


def test_parse_llm_json_handles_fences_embedded_json_and_repair():
    """Verify that parse LLM json handles fences embedded json and repair."""
    cg = import_candidate_generation()

    assert cg._parse_llm_json('```json\n{"a":1}\n```') == {"a": 1}
    assert cg._parse_llm_json('prefix {"candidates":[{"name":"A"}]} suffix') == {"candidates": [{"name": "A"}]}
    assert cg._candidate_list_from_llm_response('[{"name":"A"}]') == [{"name": "A"}]
    assert cg._candidate_list_from_llm_response('{"candidates":[{"name":"B"}]}') == [{"name": "B"}]


def test_guard_generated_page_widths_distributes_variants_and_respects_prompt():
    """Verify that guard generated page widths distributes variants and respects prompt."""
    cg = import_candidate_generation()
    candidate = {"pages": [{"id": "p", "layout": {}}]}

    assert cg._guard_generated_page_widths(candidate, "", 1)["pages"][0]["layout"]["main_width"] == "wide"
    explicit = cg._guard_generated_page_widths(candidate, "make it full width", 1)
    assert explicit["pages"][0]["layout"] == {}


def install_fake_genai(response_text):
    """Provide the install fake genai test helper."""
    google_pkg = types.ModuleType("google")
    genai = types.ModuleType("google.genai")

    class Models:
        def generate_content(self, **kwargs):
            """Provide the generate content test helper."""
            return Obj(text=response_text)

    class Client:
        def __init__(self, api_key=""):
            """Initialize the test helper object."""
            self.models = Models()

    genai.Client = Client
    sys.modules["google"] = google_pkg
    sys.modules["google.genai"] = genai


def test_llm_generate_and_regenerate_candidates_use_genai(monkeypatch):
    """Verify that LLM generate and regenerate candidates use genai."""
    cg = import_candidate_generation()
    install_fake_genai('{"candidates":[{"pages":[{"id":"p","layout":{}}]},{"pages":[{"id":"p","layout":{}}]},{"pages":[{"id":"p","layout":{}}]}]}')

    generated = cg._llm_generate_3_candidates([{"id": "p"}], [{"id": "s"}], "")
    regenerated = cg._llm_regenerate_3_candidates([{"id": "p"}], [{"id": "s"}], "", {})

    assert len(generated) == 3
    assert generated[2]["pages"][0]["layout"]["main_width"] == "full"
    assert len(regenerated) == 3


def test_allowed_layout_protects_role_locked_sections():
    """Verify that allowed layout protects role locked sections."""
    cg = import_candidate_generation()

    assert cg._allowed_layout("object_form", "form", "table") == "form"
    assert cg._allowed_layout("object_detail", "detail", "gallery") == "detail"
    assert cg._allowed_layout("navigation", "site-nav", "card") == "site-nav"
    assert cg._allowed_layout("activity_action", "activity_action", "form") == "activity_action"
    assert cg._allowed_layout("object_collection", "card", "table") == "table"


def test_merge_llm_candidate_preserves_base_data_and_applies_allowed_changes():
    """Verify that merge LLM candidate preserves base data and applies allowed changes."""
    cg = import_candidate_generation()
    pages = [{"id": "p", "layout": {"main_width": "contained"}}]
    sections = [
        {"id": "form", "role": "object_form", "layout": "form", "style": {"color": "neutral"}},
        {"id": "cards", "role": "object_collection", "layout": "card"},
    ]
    llm = {
        "pages": [{"id": "p", "layout": {"main_width": "wide"}, "gap": "lg"}],
        "sections": [
            {"id": "form", "layout": "table", "component": "DataTable", "style": {"tone": "soft"}},
            {"id": "cards", "layout": "table", "component": "DataTable", "col_span": 6},
        ],
    }

    merged_pages, merged_sections = cg._merge_llm_candidate(pages, sections, llm)

    assert merged_pages[0]["layout"]["main_width"] == "wide"
    assert merged_pages[0]["gap"] == "lg"
    assert merged_sections[0]["layout"] == "form"
    assert merged_sections[0]["style"] == {"color": "neutral", "tone": "soft"}
    assert merged_sections[1]["layout"] == "table"
    assert merged_sections[1]["component"] == "DataTable"


def test_tokens_from_llm_styling_and_schema_merge_non_empty_values():
    """Verify that tokens from LLM styling and schema merge non empty values."""
    cg = import_candidate_generation()

    tokens = cg._tokens_from_llm_styling(
        {"accentColor": "#111", "accentSecondary": "#222", "backgroundColor": "#fff", "textColor": "#000", "textSize": "lg"},
        {"base": "x"},
        "",
        2,
    )
    assert tokens["base"] == "x"
    assert tokens["accent.hex"] == "#111"
    assert tokens["typography.hero.size"] == "64px"
    assert tokens["design.variant_index"] == "2"

    schema_tokens = cg._tokens_from_llm_schema(
        {"styling": '{"accentColor":"#333"}', "tokens": {"accent.hex": "#444", "empty": ""}},
        {},
        "",
        1,
    )
    assert schema_tokens["accent.hex"] == "#444"
    assert "empty" not in schema_tokens
    assert schema_tokens["design.variant_index"] == "1"


def test_generate_candidate_set_saves_three_candidates(monkeypatch):
    """Verify that generate candidate set saves three candidates."""
    interface = make_interface({"pages": [{"id": "p"}], "sections": [{"id": "s"}], "tokens": {}, "styling": {}})
    cg = import_candidate_generation([interface])
    monkeypatch.setattr(cg, "_llm_generate_3_candidates", lambda pages, sections, prompt: [
        {"name": f"C{i}", "pages": [{"id": "p"}], "sections": [{"id": "s"}], "styling": {}, "tokens": {}}
        for i in range(3)
    ])
    monkeypatch.setattr(cg, "validate_and_save_candidate", lambda **kwargs: f"OK: saved {kwargs['candidate_index']}")
    monkeypatch.setattr(cg, "_render_candidate_preview_local", lambda interface_id, index: "OK")

    result = cg.generate_candidate_set("iface", "fresh")

    assert result.startswith("OK: generated and saved 3 candidates.")


def test_generate_candidate_set_reports_missing_data_and_llm_failure(monkeypatch):
    """Verify that generate candidate set reports missing data and LLM failure."""
    cg = import_candidate_generation([make_interface({"pages": [], "sections": []})])

    assert "no pages/sections" in cg.generate_candidate_set("iface")
    cg = import_candidate_generation([make_interface({"pages": [{"id": "p"}], "sections": [{"id": "s"}]})])
    monkeypatch.setattr(cg, "_llm_generate_3_candidates", lambda pages, sections, prompt: None)
    assert "LLM failed" in cg.generate_candidate_set("iface")


def test_regenerate_candidate_set_saves_three_candidates(monkeypatch):
    """Verify that regenerate candidate set saves three candidates."""
    cg = import_candidate_generation()
    context = {
        "base_candidate": {
            "pages": [{"id": "p"}],
            "sections": [{"id": "s"}],
            "tokens": {},
            "styling": {},
        }
    }
    monkeypatch.setattr(cg, "get_candidate_regeneration_context", lambda *args: json.dumps(context))
    monkeypatch.setattr(cg, "_llm_regenerate_3_candidates", lambda pages, sections, reqs, styling: [
        {"name": f"R{i}", "pages": [{"id": "p"}], "sections": [{"id": "s"}], "styling": {}, "tokens": {}}
        for i in range(3)
    ])
    monkeypatch.setattr(cg, "validate_and_save_candidate", lambda **kwargs: f"OK: saved {kwargs['candidate_index']}")
    monkeypatch.setattr(cg, "_render_candidate_preview_local", lambda interface_id, index: "OK")

    result = cg.regenerate_candidate_set("iface", 0, "denser")

    assert result.startswith("OK: regenerated and saved 3 candidates.")


def test_regenerate_candidate_set_reports_context_and_llm_errors(monkeypatch):
    """Verify that regenerate candidate set reports context and LLM errors."""
    cg = import_candidate_generation()
    monkeypatch.setattr(cg, "get_candidate_regeneration_context", lambda *args: "ERROR: missing")
    assert cg.regenerate_candidate_set("iface", 0) == "ERROR: missing"

    monkeypatch.setattr(
        cg,
        "get_candidate_regeneration_context",
        lambda *args: json.dumps({"base_candidate": {"pages": [{"id": "p"}], "sections": [{"id": "s"}], "styling": {}}}),
    )
    monkeypatch.setattr(cg, "_llm_regenerate_3_candidates", lambda *args: None)
    assert "LLM failed" in cg.regenerate_candidate_set("iface", 0)
