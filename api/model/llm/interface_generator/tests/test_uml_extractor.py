import pytest

from llm.interface_generator.uml_mapping import uml_extractor as ux


def test_cardinality_detects_multiplicity_shapes():
    """Verify that cardinality detects multiplicity shapes."""
    assert ux._cardinality("*", "n") == "many-many"
    assert ux._cardinality("1", "*") == "1-many"
    assert ux._cardinality("+", "1") == "many-1"
    assert ux._cardinality("1", "1") == "1-1"


def test_ref_list_flattens_dict_values_and_iterables():
    """Verify that ref list flattens dict values and iterables."""
    assert ux._ref_list({"input": ["a"], "output": ["b", "c"]}) == ["a", "b", "c"]
    assert ux._ref_list(("x", "y")) == ["x", "y"]
    assert ux._ref_list(None) == []


def test_score_layout_uses_attribute_signals():
    """Verify that score layout uses attribute signals."""
    score = ux.score_layout({"image_url", "price", "status", "start_date", "end_date", "latitude"})
    assert score["gallery"] == pytest.approx(0.9)
    assert score["table"] == pytest.approx(0.85)
    assert score["map"] == pytest.approx(0.9)


def test_extract_class_diagram_builds_models_and_relationships():
    """Verify that extract class diagram builds models and relationships."""
    classifiers = {
        "order": {"type": "class", "name": "Order", "attributes": [{"name": "status"}]},
        "line": {"type": "class", "name": "OrderLine", "attributes": [{"name": "quantity"}]},
        "vip": {"type": "class", "name": "VipOrder", "attributes": []},
    }
    relations = {
        "r1": {"source": "order", "target": "line", "data": {"type": "composition", "target_multiplicity": "*"}},
        "r2": {"source": "line", "target": "order", "data": {"type": "association", "source_multiplicity": "*", "target_multiplicity": "1"}},
        "r3": {"source": "vip", "target": "order", "data": {"type": "generalization"}},
    }

    graph = ux.extract_class_diagram(classifiers, relations)

    assert graph["Order"]["compositions_owned"] == [{"model": "OrderLine", "cardinality": "1-many"}]
    assert graph["OrderLine"]["composition_parent"] == "Order"
    assert graph["OrderLine"]["associations"][0]["model"] == "Order"
    assert graph["VipOrder"]["specializes"] == ["Order"]
    assert graph["Order"]["specialized_by"] == ["VipOrder"]


def test_extract_class_diagram_reads_nested_multiplicity_shape():
    """Verify that nested relation multiplicity is used for association cardinality."""
    classifiers = {
        "product": {"type": "class", "name": "Product", "attributes": []},
        "seller": {"type": "class", "name": "Seller", "attributes": []},
    }
    relations = {
        "sold_by": {
            "source": "product",
            "target": "seller",
            "data": {
                "type": "association",
                "label": "sold by",
                "multiplicity": {"source": "*", "target": "1"},
            },
        },
    }

    graph = ux.extract_class_diagram(classifiers, relations)

    assert graph["Product"]["associations"] == [
        {"model": "Seller", "cardinality": "many-1", "name": "sold by", "navigable": True}
    ]
    assert graph["Seller"]["associations"] == [
        {"model": "Product", "cardinality": "1-many", "name": "sold by", "navigable": True}
    ]


def test_use_case_permission_and_role_helpers():
    """Verify that use case permission and role helpers."""
    assert ux._infer_permissions("Create and delete order") == ["create", "read", "delete"]
    assert ux._infer_page_role("Browse catalog", False) == "collection_workspace"
    assert ux._infer_page_role("Checkout order", True) == "workflow_entry"


def test_best_model_and_explicit_model_matching():
    """Verify that best model and explicit model matching."""
    assert ux._best_model_for_text("checkout basket", ["Cart", "Payment"]) == "Cart"
    assert ux._best_model_for_text("update delivery city", ["Address"], {"Address": {"delivery", "city"}}) == "Address"
    assert ux._model_name_explicit_in_text("View order line", "Order Line") is True
    assert ux._model_name_explicit_in_text("View order", "Order Line") is False


def test_extract_use_case_diagram_maps_actor_permissions_and_explicit_models():
    """Verify that extract use case diagram maps actor permissions and explicit models."""
    classifiers = {
        "actor": {"type": "actor", "name": "Customer"},
        "seller": {"type": "actor", "name": "Seller"},
        "uc": {"type": "usecase", "name": "Browse Product", "classes": ["product"]},
        "product": {"type": "class", "name": "Product"},
    }
    relations = {
        "rel": {"source": "actor", "target": "uc", "data": {"type": "interaction"}},
        "other": {"source": "seller", "target": "uc", "data": {"type": "interaction"}},
    }
    diagrams = [{"type": "usecase", "edges": [{"rel": "rel"}, {"rel": "other"}], "nodes": []}]

    result = ux.extract_use_case_diagram(
        classifiers, relations, diagrams, "actor", "Customer", {"Product"}, set()
    )

    assert result["target_permissions"] == {"Product": ["read"]}
    assert result["target_use_cases"][0]["explicit_models"] == ["Product"]
    assert result["all_actors"]["Customer"] == ["Browse Product"]
    assert result["all_actors"]["Seller"] == ["Browse Product"]


def test_non_primary_explicit_models_are_context_not_actor_permissions():
    """Verify that related context models do not become standalone actor permissions."""
    classifiers = {
        "actor": {"type": "actor", "name": "Customer"},
        "uc": {"type": "usecase", "name": "View Product Detail Page", "classes": ["product", "seller"]},
        "product": {"type": "class", "name": "Product"},
        "seller": {"type": "class", "name": "Seller"},
    }
    relations = {
        "rel": {"source": "actor", "target": "uc", "data": {"type": "interaction"}},
    }
    diagrams = [{"type": "usecase", "edges": [{"rel": "rel"}], "nodes": []}]

    result = ux.extract_use_case_diagram(
        classifiers, relations, diagrams, "actor", "Customer", {"Product", "Seller"}, set()
    )

    assert result["target_permissions"] == {"Product": ["read"]}
    assert result["target_use_cases"][0]["explicit_models"] == ["Product", "Seller"]
    assert result["target_use_cases"][0]["context_models"] == ["Seller"]


def test_action_component_selects_specific_component():
    """Verify that action component selects specific component."""
    assert ux._action_component("Upload product photo") == "FileUpload"
    assert ux._action_component("Confirm order summary") == "DetailPanel"
    assert ux._action_component("Enter address") == "AddressForm"
    assert ux._action_component("Do something custom") == "ObjectForm"


def test_extract_activity_diagrams_builds_ordered_workflow_steps():
    """Verify that extract activity diagrams builds ordered workflow steps."""
    classifiers = {
        "product": {"type": "class", "name": "Product"},
        "actor": {"type": "actor", "name": "Seller"},
        "a1": {"type": "action", "name": "Upload Product photo", "classes": {"models": ["product"]}, "actorNode": "actor"},
        "a2": {"type": "action", "name": "Review Product", "actorNodeName": "Manager"},
    }
    system_data = {
        "activity_diagrams": [{
            "name": "Publish Product",
            "nodes": [{"id": "n1", "cls_ptr": "a1"}, {"id": "n2", "cls_ptr": "a2"}],
            "edges": [{"source": "n1", "target": "n2"}],
        }]
    }

    result = ux.extract_activity_diagrams(classifiers, system_data, {"Product"}, {"Product": {"photo"}})

    assert result["uc_ids_with_workflows"] == {"a1", "a2"}
    assert [s["action"] for s in result["workflows"][0]["steps"]] == ["Upload Product photo", "Review Product"]
    assert result["workflows"][0]["steps"][0]["model"] == "Product"
    assert result["workflows"][0]["steps"][0]["component_hint"] == "FileUpload"


def test_detect_semantic_decisions_for_calendar_timeline_and_map():
    """Verify that detect semantic decisions for calendar timeline and map."""
    assert ux.detect_semantic_decisions(
        "Appointment",
        {"attributes": [{"name": "start_time"}, {"name": "end_time"}], "layout_score": {}},
        "collection_workspace",
    )["default"] == "DataTable"
    assert ux.detect_semantic_decisions(
        "AuditLog",
        {"attributes": [{"name": "created_at"}], "layout_score": {}},
        "collection_workspace",
    )["default"] == "TimelineList"
    assert ux.detect_semantic_decisions(
        "StoreLocation",
        {"attributes": [{"name": "latitude"}], "layout_score": {"map": 0.9}},
        "collection_workspace",
    )["default"] == "MapView"
    assert ux.detect_semantic_decisions("Product", {"attributes": [], "layout_score": {}}, "x") is None


def test_sys_as_list_accepts_wrapped_lists():
    """Verify that sys as list accepts wrapped lists."""
    assert ux._sys_as_list({"classifiers": {"classifiers": [1]}}, "classifiers") == [1]
    assert ux._sys_as_list({"classifiers": {"items": [2]}}, "classifiers") == [2]
    assert ux._sys_as_list({"classifiers": "bad"}, "classifiers") == []


def test_expand_actor_scope_traverses_relevant_relationships():
    """Verify that expand actor scope traverses relevant relationships."""
    graph = {
        "Order": {
            "compositions_owned": [{"model": "OrderLine"}],
            "aggregations_owned": [{"model": "Coupon"}],
            "associations": [{"model": "Shipment", "cardinality": "1-many"}],
        },
        "OrderLine": {"composition_parent": "Order", "compositions_owned": [{"model": "Tax"}], "aggregations_owned": [], "associations": []},
        "Coupon": {},
        "Shipment": {},
    }

    expanded = ux._expand_actor_scope(graph, {"Order": ["read"]})

    assert expanded["Order"] == ["read"]
    assert expanded["OrderLine"] == ["read"]
    assert expanded["Coupon"] == ["read"]
    assert expanded["Shipment"] == ["read"]


def test_expand_actor_scope_does_not_add_many_to_one_context_parent():
    """Verify that many-to-one context models do not become actor workspaces."""
    graph = {
        "Product": {
            "compositions_owned": [],
            "aggregations_owned": [],
            "associations": [{"model": "Seller", "cardinality": "many-1", "name": "sold by"}],
        },
        "Seller": {
            "composition_parent": None,
            "compositions_owned": [],
            "aggregations_owned": [],
            "associations": [{"model": "Product", "cardinality": "1-many", "name": "sold by"}],
        },
    }

    expanded = ux._expand_actor_scope(graph, {"Product": ["read"]})

    assert expanded == {"Product": ["read"]}


def test_extract_uml_intelligence_combines_models_actor_workflow_and_decisions():
    """Verify that extract UML intelligence combines models actor workflow and decisions."""
    system_data = {
        "classifiers": [
            {"id": "actor", "data": {"type": "actor", "name": "Customer"}},
            {"id": "product", "data": {"type": "class", "name": "Product", "attributes": [{"name": "image_url"}, {"name": "price"}]}},
            {"id": "order", "data": {"type": "class", "name": "Order", "attributes": [{"name": "status"}]}},
            {"id": "uc", "data": {"type": "usecase", "name": "Browse Product", "classes": ["product"]}},
            {"id": "act", "data": {"type": "action", "name": "Review Product", "usecase": "uc"}},
        ],
        "relations": [
            {"id": "rel", "source": "actor", "target": "uc", "data": {"type": "interaction"}},
            {"id": "assoc", "source": "product", "target": "order", "data": {"type": "association", "target_multiplicity": "*"}},
        ],
        "diagrams": [{"type": "usecase", "nodes": [], "edges": [{"rel": "rel"}]}],
        "activity_diagrams": [{"name": "Browse Flow", "nodes": [{"id": "n1", "cls_ptr": "act"}], "edges": []}],
    }

    intel = ux.extract_uml_intelligence(system_data, "actor", "Customer")

    assert set(intel["model_graph"]) == {"Product", "Order"}
    assert intel["actor_intel"]["target_permissions"]["Product"] == ["read"]
    assert intel["workflow_intel"]["workflows"][0]["steps"][0]["action"] == "Review Product"
    assert intel["_meta"]["total_models"] == 2
