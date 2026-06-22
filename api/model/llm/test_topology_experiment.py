from __future__ import annotations

from llm.topology_experiment import parse_topology_artifact_json


def test_parse_topology_artifact_json_canonicalizes_retry_to_loop() -> None:
    raw_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "parallel",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["budget_review", "supplier_review"]
        },
        {
          "id": "T2",
          "type": "retry",
          "parent": "T1",
          "parent_branch": "budget_review",
          "branches": ["retry", "success"],
          "purpose": "repeat budget review until it succeeds"
        }
      ]
    }
    """

    artifact = parse_topology_artifact_json(raw_output)

    assert artifact["structures"][1]["type"] == "loop"


def test_parse_topology_artifact_json_keeps_existing_control_types() -> None:
    raw_output = """
    {
      "structures": [
        {
          "id": "T1",
          "type": "decision",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["approved", "rejected"]
        },
        {
          "id": "T2",
          "type": "parallel",
          "parent": "ROOT",
          "parent_branch": null,
          "branches": ["track_a", "track_b"]
        },
        {
          "id": "T3",
          "type": "loop",
          "parent": "T2",
          "parent_branch": "track_a",
          "branches": ["retry", "success"]
        }
      ]
    }
    """

    artifact = parse_topology_artifact_json(raw_output)

    assert [structure["type"] for structure in artifact["structures"]] == [
        "decision",
        "parallel",
        "loop",
    ]
