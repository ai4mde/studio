"""Offline unit tests for AI4MDE converter output (no LLM, HTTP, or DB)."""

import os
import sys
import uuid
from pathlib import Path

import pytest

MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from llm.converter import convert_to_ai4mde, unwrap_ai4mde_systems_export, validate_ai4mde_json
from llm._test_helpers import create_test_project, import_and_validate_system, setup_django


def test_convert_emits_classifiers_relations_and_passes_validate() -> None:
    clean = {
        "nodes": [
            {"id": "n1", "type": "initial", "name": None},
            {"id": "n2", "type": "action", "name": "Do work"},
            {"id": "n3", "type": "final", "name": None},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "controlflow"},
            {"source": "n2", "target": "n3", "type": "controlflow"},
        ],
    }
    pid, sid, did = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    export = convert_to_ai4mde(
        clean_model=clean,
        system_id=sid,
        diagram_id=did,
        name="T",
        description="D",
        project_id=pid,
    )
    validate_ai4mde_json(export)
    out = unwrap_ai4mde_systems_export(export)
    assert out is not None
    assert len(out["classifiers"]) == 3
    assert len(out["relations"]) == 2
    assert out["imported_classifiers"] == []
    assert out["project"] == pid
    cls_ids = {c["id"] for c in out["classifiers"]}
    for n in out["diagrams"][0]["nodes"]:
        assert n["cls"] in cls_ids
    rel_ids = {r["id"] for r in out["relations"]}
    for e in out["diagrams"][0]["edges"]:
        assert e["rel"] in rel_ids
    assert out["classifiers"][0]["data"]["type"] in {"initial", "action", "final"}
    for c in out["classifiers"]:
        assert c["project"] == pid
        assert c.get("original_system_id") is None


def test_convert_maps_clean_edge_types_to_ai4mde_relation_types() -> None:
    clean = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "Act"},
            {"id": "n3", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "control"},
            {"source": "n2", "target": "n3"},
        ],
    }
    export = convert_to_ai4mde(
        clean_model=clean,
        system_id=str(uuid.uuid4()),
        diagram_id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
    )
    out = unwrap_ai4mde_systems_export(export)
    assert [relation["data"]["type"] for relation in out["relations"]] == [
        "controlflow",
        "controlflow",
    ]
    validate_ai4mde_json(out)


def test_convert_preserves_controlflow_edge_labels() -> None:
    clean = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "Review request"},
            {"id": "n3", "type": "decision", "label": "approved?"},
            {"id": "n4", "type": "action", "name": "Process request"},
            {"id": "n5", "type": "action", "name": "Reject request"},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "control"},
            {"source": "n2", "target": "n3", "type": "control"},
            {"source": "n3", "target": "n4", "type": "control", "label": "Approved"},
            {"source": "n3", "target": "n5", "type": "control", "label": "Rejected"},
        ],
    }
    export = convert_to_ai4mde(
        clean_model=clean,
        system_id=str(uuid.uuid4()),
        diagram_id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
    )
    out = unwrap_ai4mde_systems_export(export)
    relation_labels = {relation["data"].get("label") for relation in out["relations"]}

    assert "Approved" in relation_labels
    assert "Rejected" in relation_labels
    validate_ai4mde_json(out)


def test_convert_preserves_decision_semantic_text() -> None:
    clean = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "decision", "name": "Approve request?"},
            {"id": "n3", "type": "action", "name": "Process request"},
            {"id": "n4", "type": "action", "name": "Reject request"},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "control"},
            {"source": "n2", "target": "n3", "type": "control", "label": "Approved"},
            {"source": "n2", "target": "n4", "type": "control", "label": "Rejected"},
        ],
    }
    export = convert_to_ai4mde(
        clean_model=clean,
        system_id=str(uuid.uuid4()),
        diagram_id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
    )
    out = unwrap_ai4mde_systems_export(export)
    decision_classifiers = [
        classifier["data"]
        for classifier in out["classifiers"]
        if classifier["data"].get("type") == "decision"
    ]

    assert len(decision_classifiers) == 1
    assert decision_classifiers[0].get("name") == "Approve request?"
    assert decision_classifiers[0].get("label") == "Approve request?"
    validate_ai4mde_json(out)


def test_convert_maps_object_edges_to_objectflow() -> None:
    clean = {
        "nodes": [
            {"id": "n1", "type": "object"},
            {"id": "n2", "type": "action", "name": "Use object"},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "object"},
        ],
    }
    export = convert_to_ai4mde(
        clean_model=clean,
        system_id=str(uuid.uuid4()),
        diagram_id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
    )
    out = unwrap_ai4mde_systems_export(export)
    relation = out["relations"][0]["data"]
    assert relation["type"] == "objectflow"
    assert relation["cls"] == out["diagrams"][0]["nodes"][0]["cls"]
    validate_ai4mde_json(out)


def test_convert_with_project_id_matches_system_and_classifiers_and_array_wrap() -> None:
    clean = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "Act"},
            {"id": "n3", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
        ],
    }
    pid = str(uuid.uuid4())
    sid, did = str(uuid.uuid4()), str(uuid.uuid4())
    wrapped = convert_to_ai4mde(
        clean_model=clean,
        system_id=sid,
        diagram_id=did,
        project_id=pid,
    )
    assert isinstance(wrapped, list) and len(wrapped) == 1
    out = wrapped[0]
    assert out is not None
    assert "classifiers" in out
    assert "relations" in out
    validate_ai4mde_json(out)
    assert out["project"] == pid
    for c in out["classifiers"]:
        assert c["project"] == pid
        assert c.get("original_system_id") is None


def test_validate_rejects_bad_edge_reference() -> None:
    cid = str(uuid.uuid4())
    rid = str(uuid.uuid4())
    did, sid = str(uuid.uuid4()), str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    bad = [
        {
            "id": sid,
            "name": "S",
            "description": "",
            "project": project_id,
            "imported_classifiers": [],
            "interfaces": [],
            "classifiers": [
                {
                    "id": cid,
                    "project": project_id,
                    "system": sid,
                    "original_system_id": None,
                    "data": {
                        "body": "",
                        "isAutomatic": False,
                        "localPostcondition": "",
                        "localPrecondition": "",
                        "name": "A",
                        "namespace": "",
                        "role": "action",
                        "type": "action",
                    },
                },
            ],
            "relations": [
                {
                    "id": rid,
                    "system": sid,
                    "source": cid,
                    "target": cid,
                    "data": {
                        "condition": None,
                        "guard": "",
                        "is_directed": True,
                        "position_handlers": [],
                        "type": "controlflow",
                        "weight": "",
                    },
                },
            ],
            "diagrams": [
                {
                    "id": did,
                    "type": "activity",
                    "name": "D",
                    "description": "",
                    "system": sid,
                    "nodes": [
                        {
                            "id": str(uuid.uuid4()),
                            "diagram": did,
                            "cls": cid,
                            "data": {"position": {"x": 0, "y": 0}},
                        },
                    ],
                    "edges": [
                        {
                            "id": str(uuid.uuid4()),
                            "diagram": did,
                            "rel": str(uuid.uuid4()),
                            "data": {},
                        },
                    ],
                },
            ],
        }
    ]
    with pytest.raises(ValueError, match="not listed in relations"):
        validate_ai4mde_json(bad)


def test_convert_raises_on_dangling_edge() -> None:
    clean = {
        "nodes": [{"id": "n1", "type": "initial"}],
        "edges": [{"source": "n1", "target": "missing", "type": "controlflow"}],
    }
    with pytest.raises(ValueError, match="unknown target"):
        convert_to_ai4mde(
            clean_model=clean,
            system_id=str(uuid.uuid4()),
            diagram_id=str(uuid.uuid4()),
            project_id=str(uuid.uuid4()),
        )


@pytest.mark.skipif(
    not os.environ.get("RUN_BASELINE_IMPORT_INTEGRATION"),
    reason="Set RUN_BASELINE_IMPORT_INTEGRATION=1 to run DB/API import integration.",
)
def test_controlflow_labels_survive_import_and_diagram_api() -> None:
    setup_django()

    from django.contrib.auth import get_user_model
    from django.db.utils import OperationalError
    from django.test import Client
    from model.auth import create_token
    from metadata.models import Relation

    clean = {
        "nodes": [
            {"id": "n1", "type": "initial"},
            {"id": "n2", "type": "action", "name": "Review request"},
            {"id": "n3", "type": "decision", "label": "approved?"},
            {"id": "n4", "type": "action", "name": "Process request"},
            {"id": "n5", "type": "action", "name": "Reject request"},
            {"id": "n6", "type": "final"},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "control"},
            {"source": "n2", "target": "n3", "type": "control"},
            {"source": "n3", "target": "n4", "type": "control", "label": "Approved"},
            {"source": "n3", "target": "n5", "type": "control", "label": "Rejected"},
            {"source": "n4", "target": "n6", "type": "control"},
            {"source": "n5", "target": "n6", "type": "control"},
        ],
    }

    try:
        project = create_test_project()
    except OperationalError as exc:
        pytest.skip(f"Database unavailable for import/API integration test: {exc}")
    export = convert_to_ai4mde(
        clean_model=clean,
        system_id=str(uuid.uuid4()),
        diagram_id=str(uuid.uuid4()),
        name="LabelPropagation",
        description="label propagation integration",
        project_id=str(project.id),
    )
    system_json = unwrap_ai4mde_systems_export(export)
    relation_labels = {relation["data"].get("label") for relation in system_json["relations"]}
    assert "Approved" in relation_labels
    assert "Rejected" in relation_labels

    _, imported = import_and_validate_system(project, export)
    diagram = imported.diagrams.first()
    assert diagram is not None

    db_labels = {
        relation.data.get("label")
        for relation in Relation.objects.filter(system=imported)
        if isinstance(relation.data, dict)
    }
    assert "Approved" in db_labels
    assert "Rejected" in db_labels

    user_cls = get_user_model()
    username = f"label-prop-{uuid.uuid4().hex[:8]}"
    password = "test-pass-123"
    user_cls.objects.create_user(username=username, password=password)
    _, token = create_token(username, password)
    assert token

    client = Client(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = client.get(f"/api/v1/diagram/{diagram.id}")
    assert response.status_code == 200, response.content.decode()

    payload = response.json()
    api_labels = {edge.get("rel", {}).get("label") for edge in payload.get("edges", [])}
    assert "Approved" in api_labels
    assert "Rejected" in api_labels
