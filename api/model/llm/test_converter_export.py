"""Offline unit tests for AI4MDE converter output (no LLM, HTTP, or DB)."""

import sys
import uuid
from pathlib import Path

import pytest

MODEL_ROOT = Path(__file__).resolve().parents[1]
if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))

from llm.converter import convert_to_ai4mde, unwrap_ai4mde_systems_export, validate_ai4mde_json


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
