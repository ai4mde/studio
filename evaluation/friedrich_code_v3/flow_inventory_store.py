"""Build and load the fixed, source-only V3 Flow precedence inventory."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from evaluation.friedrich_semantic_v2.evaluator_adapter import project_reviewed_inventory
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory

from .flow import FlowInventoryV3, build_flow_inventory
from .inventory import FrozenCorpus, FrozenCorpusError, load_frozen_corpus
from .reference import reference_action_nodes, reference_flow_units, reference_graph


DEFAULT_FLOW_ROOT = Path(__file__).resolve().parent / "fixed_flow_inventory/corpus_v1/v3_1"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _inventory_dict(value: FlowInventoryV3) -> dict[str, Any]:
    return {
        "required_precedence": [list(pair) for pair in value.required_precedence],
        "unresolved_cycle_pairs": [list(pair) for pair in value.unresolved_cycle_pairs],
        "removed_recurrence_edges": [list(pair) for pair in value.removed_recurrence_edges],
    }


def build_fixed_flow_corpus(
    *, corpus: FrozenCorpus | None = None, root: str | Path = DEFAULT_FLOW_ROOT
) -> Mapping[str, Any]:
    """Source-only build. Refuses to overwrite an existing derived inventory."""
    corpus = corpus or load_frozen_corpus()
    root = Path(root)
    if root.exists():
        raise FileExistsError(f"fixed Flow inventory already exists: {root}")
    root.mkdir(parents=True)
    cases: dict[str, dict[str, Any]] = {}
    total_required = total_unresolved = 0
    for case_id in corpus.case_ids:
        case = corpus.load_case(case_id)
        reviewed = SemanticInventory.from_dict(case.reviewed_action)
        projection = project_reviewed_inventory(reviewed, case.reference_evidence)
        raw_reference = reference_graph(case.reference_evidence)
        unit_nodes = reference_action_nodes(reviewed, raw_reference)
        units = reference_flow_units(projection.action_units, unit_nodes)
        inventory = build_flow_inventory(raw_reference, units, case.control)
        total_required += len(inventory.required_precedence)
        total_unresolved += len(inventory.unresolved_cycle_pairs)
        relative = f"cases/{case_id}/flow_inventory.json"
        output = root / relative
        output.parent.mkdir(parents=True)
        output.write_bytes(_json_bytes({"case_id": case_id, **_inventory_dict(inventory)}))
        source_dir = corpus.source_root / case_id
        cases[case_id] = {
            "relative_path": relative,
            "flow_inventory_sha256": _sha(output.read_bytes()),
            "reference_evidence_sha256": _sha((source_dir / "reference_evidence.json").read_bytes()),
            "frozen_control_sha256": corpus.manifest["components"]["cases"][case_id]["control_inventory_sha256"],
            "reviewed_action_sha256": corpus.manifest["components"]["cases"][case_id]["reviewed_action_inventory_sha256"],
        }
    components = {"cases": cases, "frozen_control_corpus_sha256": corpus.corpus_sha256}
    digest = _sha(json.dumps(components, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
    manifest = {
        "status": "FIXED_SOURCE_DERIVATION",
        "derivation_version": "friedrich-v3-flow-precedence-1",
        "candidate_graphs_or_scores_accessed": False,
        "case_count": len(cases),
        "required_precedence_count": total_required,
        "unresolved_cycle_pair_count": total_unresolved,
        "components_sha256": digest,
        "components": components,
    }
    (root / "manifest.json").write_bytes(_json_bytes(manifest))
    return manifest


def load_fixed_flow_inventory(
    case_id: str, corpus: FrozenCorpus, *, root: str | Path = DEFAULT_FLOW_ROOT
) -> FlowInventoryV3:
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_bytes())
    components = manifest["components"]
    digest = _sha(json.dumps(components, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
    if (
        manifest.get("status") != "FIXED_SOURCE_DERIVATION"
        or manifest.get("candidate_graphs_or_scores_accessed") is not False
        or components["frozen_control_corpus_sha256"] != corpus.corpus_sha256
        or digest != manifest["components_sha256"]
    ):
        raise FrozenCorpusError("fixed Flow inventory source identity mismatch")
    try:
        item = components["cases"][case_id]
    except KeyError as exc:
        raise FrozenCorpusError(f"fixed Flow inventory missing case {case_id}") from exc
    source = corpus.manifest["components"]["cases"][case_id]
    if (
        item["frozen_control_sha256"] != source["control_inventory_sha256"]
        or item["reviewed_action_sha256"] != source["reviewed_action_inventory_sha256"]
        or _sha((corpus.source_root / case_id / "reference_evidence.json").read_bytes())
        != item["reference_evidence_sha256"]
    ):
        raise FrozenCorpusError(f"fixed Flow inventory dependency changed: {case_id}")
    data = (root / item["relative_path"]).read_bytes()
    if _sha(data) != item["flow_inventory_sha256"]:
        raise FrozenCorpusError(f"fixed Flow inventory changed: {case_id}")
    value = json.loads(data)
    if value["case_id"] != case_id:
        raise FrozenCorpusError(f"fixed Flow case identity mismatch: {case_id}")
    return FlowInventoryV3(
        tuple(tuple(pair) for pair in value["required_precedence"]),
        tuple(tuple(pair) for pair in value["unresolved_cycle_pairs"]),
        tuple(tuple(pair) for pair in value["removed_recurrence_edges"]),
    )


if __name__ == "__main__":
    built = build_fixed_flow_corpus()
    print(json.dumps({key: built[key] for key in (
        "status", "case_count", "required_precedence_count",
        "unresolved_cycle_pair_count", "components_sha256"
    )}, indent=2))
