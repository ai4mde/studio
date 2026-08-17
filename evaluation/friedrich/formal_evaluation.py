from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
from typing import Any, Iterable, Mapping

import numpy as np

from .action_matching import PROVISIONAL_THRESHOLD
from .action_scoring import (
    ActionCaseScore,
    GranularityMismatch,
    aggregate_action_scores,
    score_action_case,
)
from .adapters import activity_graph_to_eval_graph, friedrich_reference_to_eval_graph
from .calibrate_action_similarity import MODEL_NAME, MODEL_REVISION
from .control_flow_scoring import (
    ControlFlowCaseScore,
    aggregate_control_flow_scores,
    score_control_flow_case,
)
from .control_structure_scoring import (
    ControlStructureCaseScore,
    aggregate_control_structure_scores,
    score_control_structure_case,
)
from .eval_graph import EvalGraph
from .linguistic_operations import LinguisticOperationExtractor
from .prototype import _extract_activity_graph
from .revised_action_matching import apply_revised_matching


DECLARED_THESIS_SYSTEM_COMMIT = "e1d576c6bdf181a79dd9649f207f7fad4f89d714"
FORMAL_POLICY_VERSION = "friedrich-formal-policy-v1.0.0"
FORMAL_MANIFEST_SHA256 = "980e94f0f59834db994ec78600061e5a418e8fc67f032ed6caf45f42be7e13ea"
GENERATED_ARTIFACT_MANIFEST_SHA256 = (
    "59f5e7aa0d87e8c3844820450af12a400d9bb4c53268d9538a7a6feda239f398"
)
ALLOWED_GENERATED_NODE_TYPES = frozenset(
    {"initial", "action", "decision", "merge", "fork", "join", "final"}
)
METRIC_STATUSES = frozenset(
    {
        "scored",
        "unsupported",
        "reference_parse_failure",
        "generated_artifact_failure",
        "evaluation_error",
    }
)
UNSUPPORTED_CASES: Mapping[str, str] = {
    "1-3": "active inclusive gateway semantics are outside EvalGraph",
    "10-2": "active inclusive gateway semantics are outside EvalGraph",
    "10-3": "active inclusive gateway semantics are outside EvalGraph",
    "1-4": "combined converging/diverging gateway requires explicit expansion",
    "8-3": "combined converging/diverging gateway requires explicit expansion",
    "9-2": "combined converging/diverging gateway requires explicit expansion",
    "7-1": "reference uses an incompatible Frapu BPMN XML schema",
}
EXPECTED_CASE_IDS = frozenset(
    {
        "1-1", "1-2", "1-3", "1-4", "2-1", "2-2",
        "3-1", "3-2", "3-3", "3-4", "3-5", "3-6", "3-7", "3-8",
        "4-1", "5-1", "5-2", "5-3", "5-4",
        "6-1", "6-2", "6-3", "6-4", "7-1",
        "8-1", "8-2", "8-3",
        "9-1", "9-2", "9-3", "9-4", "9-5", "9-6",
        "10-1", "10-2", "10-3", "10-4", "10-5", "10-6", "10-7",
        "10-8", "10-9", "10-10", "10-11", "10-12", "10-13", "10-14",
    }
)
FROZEN_FILE_HASHES: Mapping[str, str] = {
    "action_matching.py": "9bab1ea7ed3c6eeb143c812bd1bb661eae875471295428649e32f1936422d164",
    "linguistic_operations.py": "83549846323b9d2216d590165f51836484e7bf099458149e5eece6fda4b5cd63",
    "revised_action_matching.py": "ab604fafbd51b679af7c1fb6de1c96302c07bc9c08a1051b89f3e800b8e3dde7",
    "eval_graph.py": "ae7828914d979c83ee6e7923eaa5df06022120f8a00818ee04051b7d2136f9e8",
    "adapters.py": "26bf97389ce3c26f59760668d43c6501b746b9430190d68748e5a9b1f9547628",
    "action_scoring.py": "9e36e56661861ca7ebc6299d0a969d2e92a332f568b3afda51b1fc5215494ca3",
    "control_flow_scoring.py": "abb199adff53a2c1b13dea76112088ee720a7dc9b14a4ebebcfd57311b126d4b",
    "control_structure_scoring.py": "30017752200f7e13ff0e7e70af30c3be42d942f41bdb54c010d1b3a8a9138867",
    "requirements-calibration.txt": "3856272bc96ef7767870694bdd64d2df2dec2aaa430ef058862572174b4bd1d5",
}
PACKAGE_VERSIONS: Mapping[str, str] = {
    "sentence-transformers": "5.7.0",
    "torch": "2.13.0",
    "transformers": "5.15.0",
    "numpy": "2.5.2",
    "scipy": "1.18.0",
    "spacy": "3.8.14",
    "en-core-web-sm": "3.8.0",
    "nltk": "3.10.0",
}
REVIEWED_GRANULARITY: Mapping[str, tuple[GranularityMismatch, ...]] = {
    "3-8": (
        GranularityMismatch(
            reference_ids=("456", "457"),
            generated_ids=("n2",),
            direction="many_reference_to_one_generated",
        ),
    ),
    "4-1": (
        GranularityMismatch(
            reference_ids=("2120552757", "2120552767"),
            generated_ids=("n15",),
            direction="many_reference_to_one_generated",
        ),
    ),
}


class FormalEvaluationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PreflightCase:
    case_id: str
    supported: bool
    reference_graph: EvalGraph | None
    generated_graph: EvalGraph


@dataclass(frozen=True, slots=True)
class PreflightResult:
    cases: tuple[PreflightCase, ...]
    formal_manifest_sha256: str
    generated_artifact_manifest_sha256: str

    @property
    def supported_cases(self) -> tuple[PreflightCase, ...]:
        return tuple(case for case in self.cases if case.supported)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FormalEvaluationError(f"Cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FormalEvaluationError(f"Expected a JSON object in {path}")
    return value


def validate_manifest_documents(
    formal: Mapping[str, Any], artifact: Mapping[str, Any]
) -> tuple[dict[str, Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    expected_metadata = {
        "dataset_case_count": 47,
        "supported_case_count": 40,
        "unsupported_case_count": 7,
        "generated_selection_rule": "use run_1.json for every case without exception",
        "declared_source_commit": DECLARED_THESIS_SYSTEM_COMMIT,
        "artifact_source_commit_verified": False,
        "artifact_identity_policy": "generated artifact SHA-256 is authoritative",
    }
    for document_name, document in (("formal", formal), ("artifact", artifact)):
        for key, expected in expected_metadata.items():
            if document.get(key) != expected:
                raise FormalEvaluationError(
                    f"{document_name} manifest has incorrect {key}: "
                    f"expected {expected!r}, got {document.get(key)!r}"
                )
    cases = formal.get("cases")
    artifacts = artifact.get("artifacts")
    if not isinstance(cases, list) or not isinstance(artifacts, list):
        raise FormalEvaluationError("Formal manifests require list-valued cases/artifacts")
    case_ids = [str(item.get("case_id")) for item in cases if isinstance(item, Mapping)]
    artifact_ids = [
        str(item.get("case_id")) for item in artifacts if isinstance(item, Mapping)
    ]
    if len(cases) != 47 or len(case_ids) != 47:
        raise FormalEvaluationError("Formal manifest must contain exactly 47 cases")
    if len(set(case_ids)) != len(case_ids):
        raise FormalEvaluationError("Formal manifest contains duplicate case IDs")
    if set(case_ids) != EXPECTED_CASE_IDS:
        missing = sorted(EXPECTED_CASE_IDS - set(case_ids))
        extra = sorted(set(case_ids) - EXPECTED_CASE_IDS)
        raise FormalEvaluationError(f"Formal case IDs differ: missing={missing}, extra={extra}")
    if len(artifacts) != 47 or len(artifact_ids) != 47:
        raise FormalEvaluationError("Artifact manifest must contain exactly 47 artifacts")
    if len(set(artifact_ids)) != len(artifact_ids) or set(artifact_ids) != EXPECTED_CASE_IDS:
        raise FormalEvaluationError("Artifact manifest IDs must be the same 47 unique cases")

    case_by_id = {str(item["case_id"]): item for item in cases}
    artifact_by_id = {str(item["case_id"]): item for item in artifacts}
    for case_id in sorted(EXPECTED_CASE_IDS):
        item = case_by_id[case_id]
        expected_supported = case_id not in UNSUPPORTED_CASES
        support = (
            item.get("action_supported"),
            item.get("flow_supported"),
            item.get("control_structure_supported"),
        )
        if support != (expected_supported, expected_supported, expected_supported):
            raise FormalEvaluationError(f"Case {case_id} has incorrect support flags")
        expected_reason = None if expected_supported else UNSUPPORTED_CASES[case_id]
        if item.get("unsupported_reason") != expected_reason:
            raise FormalEvaluationError(f"Case {case_id} has incorrect unsupported reason")
        if item.get("declared_source_commit") != DECLARED_THESIS_SYSTEM_COMMIT:
            raise FormalEvaluationError(f"Case {case_id} has incorrect declared commit")
        generated_path = Path(str(item.get("generated_path", "")))
        if generated_path.name != "run_1.json":
            raise FormalEvaluationError(f"Case {case_id} does not select run_1.json")
        artifact_item = artifact_by_id[case_id]
        if (
            artifact_item.get("generated_artifact_path") != str(generated_path)
            or artifact_item.get("sha256") != item.get("generated_sha256")
        ):
            raise FormalEvaluationError(f"Case {case_id} manifests disagree")

    if sum(bool(item["action_supported"]) for item in cases) != 40:
        raise FormalEvaluationError("Formal manifest must contain exactly 40 supported cases")
    if set(UNSUPPORTED_CASES) != {
        case_id for case_id, item in case_by_id.items() if not item["action_supported"]
    }:
        raise FormalEvaluationError("Formal manifest must contain exactly seven unsupported cases")
    return case_by_id, artifact_by_id


def _strict_generated_graph(path: Path, case_id: str) -> EvalGraph:
    artifact = _load_json(path)
    if str(artifact.get("case_id")) != case_id or artifact.get("run_number") != 1:
        raise FormalEvaluationError(f"Case {case_id} artifact identity/run mismatch")
    expected_configuration = {
        "pipeline_profile": "semantic_deterministic",
        "use_experimental_compiler": False,
        "mode": "baseline",
    }
    if artifact.get("request_configuration") != expected_configuration:
        raise FormalEvaluationError(f"Case {case_id} has unexpected generation configuration")
    if artifact.get("generation_status") != "completed" or artifact.get("api_status_code") != 200:
        raise FormalEvaluationError(f"Case {case_id} artifact is not completed successfully")

    try:
        raw_graph = _extract_activity_graph(artifact)
    except ValueError as exc:
        raise FormalEvaluationError(f"Case {case_id} has no generated ActivityGraph") from exc
    nodes = raw_graph.get("nodes")
    edges = raw_graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise FormalEvaluationError(f"Case {case_id} generated graph is malformed")
    node_ids: list[str] = []
    for node in nodes:
        if not isinstance(node, Mapping):
            raise FormalEvaluationError(f"Case {case_id} generated node is not an object")
        node_type = node.get("type")
        if node_type not in ALLOWED_GENERATED_NODE_TYPES:
            raise FormalEvaluationError(
                f"Case {case_id} has unknown generated node type {node_type!r}"
            )
        node_id = str(node.get("id") or "")
        if not node_id:
            raise FormalEvaluationError(f"Case {case_id} generated node has no ID")
        node_ids.append(node_id)
    if len(node_ids) != len(set(node_ids)):
        raise FormalEvaluationError(f"Case {case_id} has duplicate generated node IDs")
    known_ids = set(node_ids)
    for edge in edges:
        if not isinstance(edge, Mapping):
            raise FormalEvaluationError(f"Case {case_id} generated edge is not an object")
        if edge.get("type", "control") != "control":
            continue
        if str(edge.get("source") or "") not in known_ids or str(edge.get("target") or "") not in known_ids:
            raise FormalEvaluationError(f"Case {case_id} generated edge has unknown endpoint")
    graph = activity_graph_to_eval_graph(raw_graph)
    if not graph.nodes:
        raise FormalEvaluationError(f"Case {case_id} generated EvalGraph is empty")
    return graph


def preflight_case(entry: Mapping[str, Any]) -> PreflightCase:
    case_id = str(entry["case_id"])
    reference_path = Path(str(entry["reference_path"]))
    generated_path = Path(str(entry["generated_path"]))
    for label, path, expected_hash in (
        ("reference", reference_path, str(entry["reference_sha256"])),
        ("generated", generated_path, str(entry["generated_sha256"])),
    ):
        if not path.is_file():
            raise FormalEvaluationError(f"Case {case_id} {label} input is missing: {path}")
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise FormalEvaluationError(
                f"Case {case_id} {label} hash mismatch: expected {expected_hash}, got {actual_hash}"
            )
    generated_graph = _strict_generated_graph(generated_path, case_id)
    supported = bool(entry["action_supported"])
    if not supported:
        return PreflightCase(case_id, False, None, generated_graph)
    try:
        reference_graph = friedrich_reference_to_eval_graph(reference_path)
    except Exception as exc:
        raise FormalEvaluationError(
            f"Supported case {case_id} reference adapter failed: {exc}"
        ) from exc
    if not reference_graph.nodes:
        raise FormalEvaluationError(f"Supported case {case_id} reference EvalGraph is empty")
    return PreflightCase(case_id, True, reference_graph, generated_graph)


def _verify_runtime(base: Path, model_cache: Path, wordnet_data: Path) -> None:
    if platform.python_version() != "3.12.13":
        raise FormalEvaluationError(
            f"Expected Python 3.12.13, got {platform.python_version()}"
        )
    for package, expected in PACKAGE_VERSIONS.items():
        actual = importlib.metadata.version(package)
        if actual != expected:
            raise FormalEvaluationError(
                f"Package {package} mismatch: expected {expected}, got {actual}"
            )
    for relative, expected in FROZEN_FILE_HASHES.items():
        path = base / relative
        actual = sha256_file(path)
        if actual != expected:
            raise FormalEvaluationError(
                f"Frozen evaluator hash mismatch for {relative}: expected {expected}, got {actual}"
            )
    model_snapshot = (
        model_cache
        / "models--sentence-transformers--all-MiniLM-L6-v2"
        / "snapshots"
        / MODEL_REVISION
    )
    if not model_snapshot.is_dir():
        raise FormalEvaluationError(f"Pinned embedding snapshot is unavailable: {model_snapshot}")
    wordnet_archive = wordnet_data / "corpora" / "wordnet.zip"
    expected_wordnet = "cbda5ea6eef7f36a97a43d4a75f85e07fccbb4f23657d27b4ccbc93e2646ab59"
    if not wordnet_archive.is_file() or sha256_file(wordnet_archive) != expected_wordnet:
        raise FormalEvaluationError("Pinned WordNet archive is unavailable or changed")


def run_preflight(
    manifest_path: Path,
    artifact_manifest_path: Path,
    model_cache: Path,
    wordnet_data: Path,
) -> PreflightResult:
    base = Path(__file__).resolve().parent
    _verify_runtime(base, model_cache, wordnet_data)
    manifest_hash = sha256_file(manifest_path)
    artifact_manifest_hash = sha256_file(artifact_manifest_path)
    if manifest_hash != FORMAL_MANIFEST_SHA256:
        raise FormalEvaluationError(
            "Formal manifest identity changed: "
            f"expected {FORMAL_MANIFEST_SHA256}, got {manifest_hash}"
        )
    if artifact_manifest_hash != GENERATED_ARTIFACT_MANIFEST_SHA256:
        raise FormalEvaluationError(
            "Generated artifact manifest identity changed: "
            f"expected {GENERATED_ARTIFACT_MANIFEST_SHA256}, got {artifact_manifest_hash}"
        )
    formal = _load_json(manifest_path)
    artifacts = _load_json(artifact_manifest_path)
    case_by_id, _ = validate_manifest_documents(formal, artifacts)
    catalog_path = Path(str(formal.get("source_catalog_path", "")))
    if not catalog_path.is_file() or sha256_file(catalog_path) != formal.get("source_catalog_sha256"):
        raise FormalEvaluationError("Source catalog is missing or its hash changed")
    cases = tuple(preflight_case(case_by_id[case_id]) for case_id in sorted(case_by_id))
    if len(cases) != 47 or sum(case.supported for case in cases) != 40:
        raise FormalEvaluationError("Preflight support counts violate the frozen policy")
    return PreflightResult(
        cases=cases,
        formal_manifest_sha256=manifest_hash,
        generated_artifact_manifest_sha256=artifact_manifest_hash,
    )


def unsupported_case_record(case_id: str, reason: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "action_status": "unsupported",
        "flow_status": "unsupported",
        "control_structure_status": "unsupported",
        "status_reason": reason,
        "included_in_action_aggregate": False,
        "included_in_flow_aggregate": False,
        "included_in_control_structure_aggregate": False,
        "action": None,
        "flow": None,
        "control_structure": None,
    }


def _candidate_rows(
    cases: Iterable[PreflightCase], model_cache: Path, wordnet_data: Path
) -> tuple[list[dict[str, Any]], dict[str, EvalGraph], dict[str, EvalGraph]]:
    import torch
    from sentence_transformers import SentenceTransformer

    supported = tuple(cases)
    reference_graphs = {
        case.case_id: case.reference_graph
        for case in supported
        if case.reference_graph is not None
    }
    generated_graphs = {case.case_id: case.generated_graph for case in supported}
    labels = sorted(
        {
            node.label
            for graph in (*reference_graphs.values(), *generated_graphs.values())
            for node in graph.nodes
            if node.type == "action" and node.label is not None
        }
    )
    extractor = LinguisticOperationExtractor(wordnet_data)
    representations = {label: extractor.extract(label) for label in labels}
    texts = sorted(
        {
            text
            for representation in representations.values()
            for text in (
                representation.original_normalized_label,
                representation.canonical_label,
                representation.canonical_operation,
            )
        }
    )
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    torch.manual_seed(0)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    model = SentenceTransformer(
        MODEL_NAME,
        revision=MODEL_REVISION,
        device="cpu",
        cache_folder=str(model_cache),
        local_files_only=True,
    )
    vectors = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    embeddings = dict(zip(texts, vectors))

    rows: list[dict[str, Any]] = []
    for case in supported:
        reference = reference_graphs[case.case_id]
        generated = generated_graphs[case.case_id]
        reference_actions = sorted(
            (node for node in reference.nodes if node.type == "action" and node.label),
            key=lambda node: node.id,
        )
        generated_actions = sorted(
            (node for node in generated.nodes if node.type == "action" and node.label),
            key=lambda node: node.id,
        )
        for reference_node in reference_actions:
            for generated_node in generated_actions:
                reference_rep = representations[reference_node.label]
                generated_rep = representations[generated_node.label]
                original = float(
                    np.dot(embeddings[reference_node.label], embeddings[generated_node.label])
                )
                canonical = float(
                    np.dot(
                        embeddings[reference_rep.canonical_label],
                        embeddings[generated_rep.canonical_label],
                    )
                )
                operation = float(
                    np.dot(
                        embeddings[reference_rep.canonical_operation],
                        embeddings[generated_rep.canonical_operation],
                    )
                )
                rows.append(
                    {
                        "pair_id": f"{case.case_id}:{reference_node.id}:{generated_node.id}",
                        "case_id": case.case_id,
                        "reference_id": reference_node.id,
                        "reference_label": reference_node.label,
                        "reference_normalized": reference_node.label,
                        "generated_id": generated_node.id,
                        "generated_label": generated_node.label,
                        "generated_normalized": generated_node.label,
                        "cosine_similarity": original,
                        "canonical_similarity": canonical,
                        "semantic_similarity": max(original, canonical),
                        "operation_similarity": operation,
                        "reference_representation": reference_rep.to_dict(),
                        "generated_representation": generated_rep.to_dict(),
                    }
                )
    return rows, reference_graphs, generated_graphs


def _metric_dict(value: Any) -> dict[str, Any]:
    result = value.to_dict()
    for upper, lower in (("TP", "tp"), ("FP", "fp"), ("FN", "fn")):
        if upper in result:
            result[lower] = result.pop(upper)
    return result


def _case_record(
    case_id: str,
    action: ActionCaseScore,
    flow: ControlFlowCaseScore,
    structure: ControlStructureCaseScore,
) -> dict[str, Any]:
    granularity = REVIEWED_GRANULARITY.get(case_id)
    action_result = _metric_dict(action)
    action_result["unresolved_reference_count"] = (
        action.unresolved_reference_node_count
    )
    action_result["unresolved_generated_count"] = (
        action.unresolved_generated_node_count
    )
    action_result["granularity_diagnostic"] = {
        "evidence_status": "reviewed" if granularity is not None else "not_reviewed",
        "mismatch_count": len(granularity) if granularity is not None else None,
        "mismatches": [asdict(item) for item in granularity] if granularity else [],
    }
    flow_result = _metric_dict(flow)
    flow_result["unmatched_or_unresolved_incident_diagnostics"] = {
        "unmatched_reference": len(
            flow.flows_incident_to_unmatched_reference_actions
        ),
        "unmatched_generated": len(
            flow.flows_incident_to_unmatched_generated_actions
        ),
        "unresolved_reference": len(
            flow.flows_incident_to_unresolved_reference_actions
        ),
        "unresolved_generated": len(
            flow.flows_incident_to_unresolved_generated_actions
        ),
        "granularity_incident": flow.granularity_incident_flow_count,
    }
    return {
        "case_id": case_id,
        "action_status": "scored",
        "flow_status": "scored",
        "control_structure_status": "scored",
        "status_reason": None,
        "included_in_action_aggregate": True,
        "included_in_flow_aggregate": True,
        "included_in_control_structure_aggregate": True,
        "action": action_result,
        "flow": flow_result,
        "control_structure": _metric_dict(structure),
    }


def _git_value(args: list[str], cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def _verify_execution_repository(repository: Path) -> None:
    branch = _git_value(["branch", "--show-current"], repository)
    if branch != "feature/friedrich-evaluation":
        raise FormalEvaluationError(
            "Formal execution requires branch feature/friedrich-evaluation; "
            f"current branch is {branch or '<detached>'}"
        )
    status = _git_value(["status", "--porcelain=v1"], repository)
    if status:
        raise FormalEvaluationError(
            "Formal execution requires a clean worktree so recorded Git provenance "
            "fully identifies the evaluator"
        )


def build_reproducibility_metadata(
    preflight: PreflightResult, repository: Path
) -> dict[str, Any]:
    return {
        "formal_policy_version": FORMAL_POLICY_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "branch": _git_value(["branch", "--show-current"], repository),
        "evaluation_git_commit": _git_value(["rev-parse", "HEAD"], repository),
        "declared_thesis_system_commit": DECLARED_THESIS_SYSTEM_COMMIT,
        "artifact_source_commit_verified": False,
        "formal_manifest_sha256": preflight.formal_manifest_sha256,
        "generated_artifact_manifest_sha256": preflight.generated_artifact_manifest_sha256,
        "source_catalog_sha256": (
            "ead162d62c1785909941f8faa8a6eda9628453008101fef4f93f8e28a82ea311"
        ),
        "dataset_case_count": 47,
        "supported_case_count": 40,
        "unsupported_case_count": 7,
        "action_matcher_version": "friedrich-action-matcher-v1.0.0",
        "action_matcher_hash": FROZEN_FILE_HASHES["revised_action_matching.py"],
        "action_scorer_version": "friedrich-action-scorer-v1.0.0",
        "action_scorer_hash": FROZEN_FILE_HASHES["action_scoring.py"],
        "control_flow_scorer_version": "friedrich-control-flow-scorer-v1.0.0",
        "control_flow_scorer_hash": FROZEN_FILE_HASHES["control_flow_scoring.py"],
        "control_structure_scorer_version": "friedrich-control-structure-scorer-v1.0.0",
        "control_structure_scorer_hash": FROZEN_FILE_HASHES["control_structure_scoring.py"],
        "embedding_model": MODEL_NAME,
        "embedding_model_revision": MODEL_REVISION,
        "threshold": PROVISIONAL_THRESHOLD,
        "python_version": platform.python_version(),
        "package_versions": dict(PACKAGE_VERSIONS),
        "generated_selection_rule": "run_1.json for every case without exception",
        "unsupported_case_policy": dict(UNSUPPORTED_CASES),
    }


def build_dataset_summary(
    records: list[dict[str, Any]],
    action_scores: list[ActionCaseScore],
    flow_scores: list[ControlFlowCaseScore],
    structure_scores: list[ControlStructureCaseScore],
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    if len(records) != 47 or len(action_scores) != 40 or len(flow_scores) != 40 or len(structure_scores) != 40:
        raise FormalEvaluationError("Formal output counts violate the frozen denominator")
    unsupported = [record for record in records if record["action_status"] == "unsupported"]
    if len(unsupported) != 7:
        raise FormalEvaluationError("Formal output must retain seven unsupported records")
    action = aggregate_action_scores(action_scores).to_dict()
    flow = aggregate_control_flow_scores(flow_scores).to_dict()
    structure = aggregate_control_structure_scores(structure_scores).to_dict()
    return {
        "metadata": dict(metadata),
        "dataset_total_cases": 47,
        "supported_cases": 40,
        "unsupported_cases": 7,
        "unsupported_case_ids": sorted(UNSUPPORTED_CASES),
        "action": action,
        "control_flow": flow,
        "control_structure": structure,
        "diagnostics": {
            "unresolved_component_count": sum(
                score.unresolved_component_count for score in action_scores
            ),
            "unresolved_reference_count": sum(
                score.unresolved_reference_node_count for score in action_scores
            ),
            "unresolved_generated_count": sum(
                score.unresolved_generated_node_count for score in action_scores
            ),
            "unscorable_reference_structure_count": sum(
                score.unscorable_reference_structure_count for score in structure_scores
            ),
            "unscorable_generated_structure_count": sum(
                score.unscorable_generated_structure_count for score in structure_scores
            ),
            "granularity_reviewed_case_count": len(REVIEWED_GRANULARITY),
            "granularity_not_reviewed_supported_case_count": 40 - len(REVIEWED_GRANULARITY),
            "granularity_reviewed_mismatch_count": sum(
                len(items) for items in REVIEWED_GRANULARITY.values()
            ),
            "evaluation_failure_count": 0,
        },
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.floating):
        return float(value)
    return value


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(_json_ready(value), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _write_candidate_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (
                        json.dumps(_json_ready(value), sort_keys=True)
                        if isinstance(value, (dict, list, tuple))
                        else value
                    )
                    for key, value in row.items()
                }
            )


def _write_case_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "case_id", "action_status", "flow_status", "control_structure_status",
        "status_reason", "action_tp", "action_fp", "action_fn", "action_precision",
        "action_recall", "action_f1", "flow_tp", "flow_fp", "flow_fn",
        "flow_precision", "flow_recall", "flow_f1", "structure_tp", "structure_fp",
        "structure_fn", "structure_precision", "structure_recall", "structure_f1",
        "structure_coverage", "granularity_evidence_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            action = record["action"] or {}
            flow = record["flow"] or {}
            structure = record["control_structure"] or {}
            granularity = action.get("granularity_diagnostic", {})
            writer.writerow(
                {
                    "case_id": record["case_id"],
                    "action_status": record["action_status"],
                    "flow_status": record["flow_status"],
                    "control_structure_status": record["control_structure_status"],
                    "status_reason": record["status_reason"] or "",
                    **{f"action_{key}": action.get(key) for key in ("tp", "fp", "fn", "precision", "recall", "f1")},
                    **{f"flow_{key}": flow.get(key) for key in ("tp", "fp", "fn", "precision", "recall", "f1")},
                    **{f"structure_{key}": structure.get(key) for key in ("tp", "fp", "fn", "precision", "recall", "f1")},
                    "structure_coverage": structure.get("structure_coverage"),
                    "granularity_evidence_status": granularity.get("evidence_status", "not_applicable"),
                }
            )


def _metric_lines(title: str, metric: Mapping[str, Any], coverage: bool = False) -> list[str]:
    lines = [
        f"## {title}",
        "",
        f"- Micro Precision: `{metric.get('micro_precision')}`",
        f"- Micro Recall: `{metric.get('micro_recall')}`",
        f"- Micro F1: `{metric.get('micro_f1')}`",
        f"- Macro F1: `{metric.get('macro_f1')}`",
    ]
    if coverage:
        lines.append(f"- Structure coverage: `{metric.get('structure_coverage')}`")
    return lines + [""]


def _write_report(path: Path, summary: Mapping[str, Any]) -> None:
    diagnostics = summary["diagnostics"]
    lines = [
        "# Formal Friedrich evaluation report",
        "",
        "- Total cases: `47`",
        "- Scored cases: `40`",
        "- Unsupported cases: `7`",
        "",
        "## Unsupported cases",
        "",
        *[f"- `{case_id}`: {UNSUPPORTED_CASES[case_id]}" for case_id in sorted(UNSUPPORTED_CASES)],
        "",
        *_metric_lines("Action", summary["action"]),
        *_metric_lines("Control Flow", summary["control_flow"]),
        *_metric_lines("Control Structure", summary["control_structure"], coverage=True),
        "## Diagnostics",
        "",
        f"- Unresolved components: `{diagnostics['unresolved_component_count']}`",
        f"- Unresolved reference Actions: `{diagnostics['unresolved_reference_count']}`",
        f"- Unresolved generated Actions: `{diagnostics['unresolved_generated_count']}`",
        f"- Unscorable reference structures: `{diagnostics['unscorable_reference_structure_count']}`",
        f"- Unscorable generated structures: `{diagnostics['unscorable_generated_structure_count']}`",
        f"- Granularity reviewed cases: `{diagnostics['granularity_reviewed_case_count']}`",
        f"- Granularity not-reviewed supported cases: `{diagnostics['granularity_not_reviewed_supported_case_count']}`",
        f"- Evaluation failures: `{diagnostics['evaluation_failure_count']}`",
        "",
        "Granularity evidence is partial diagnostic evidence only and does not alter primary metrics.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _publish_outputs(
    output_dir: Path,
    manifest_path: Path,
    artifact_manifest_path: Path,
    records: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    summary: Mapping[str, Any],
) -> None:
    if output_dir.exists():
        raise FormalEvaluationError(f"Formal output directory already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent))
    try:
        shutil.copyfile(manifest_path, temporary / "formal_manifest.json")
        shutil.copyfile(artifact_manifest_path, temporary / "generated_artifact_manifest.json")
        _write_json(temporary / "per_case_results.json", records)
        _write_case_csv(temporary / "per_case_results.csv", records)
        _write_candidate_csv(temporary / "action_candidate_matrix.csv", candidates)
        _write_json(temporary / "dataset_summary.json", summary)
        _write_report(temporary / "formal_report.md", summary)
        temporary.rename(output_dir)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def execute_formal(
    preflight: PreflightResult,
    manifest_path: Path,
    artifact_manifest_path: Path,
    output_dir: Path,
    model_cache: Path,
    wordnet_data: Path,
) -> dict[str, Any]:
    if output_dir.exists():
        raise FormalEvaluationError(f"Formal output directory already exists: {output_dir}")
    repository = Path(__file__).resolve().parents[2]
    _verify_execution_repository(repository)
    supported = preflight.supported_cases
    candidate_rows, reference_graphs, generated_graphs = _candidate_rows(
        supported, model_cache, wordnet_data
    )
    evaluated_rows, _ = apply_revised_matching(
        candidate_rows, reference_graphs, generated_graphs
    )
    records: list[dict[str, Any]] = []
    action_scores: list[ActionCaseScore] = []
    flow_scores: list[ControlFlowCaseScore] = []
    structure_scores: list[ControlStructureCaseScore] = []
    by_case = {case.case_id: case for case in preflight.cases}
    for case_id in sorted(EXPECTED_CASE_IDS):
        if case_id in UNSUPPORTED_CASES:
            records.append(unsupported_case_record(case_id, UNSUPPORTED_CASES[case_id]))
            continue
        case = by_case[case_id]
        assert case.reference_graph is not None
        action = score_action_case(
            case_id,
            case.reference_graph,
            case.generated_graph,
            evaluated_rows,
            granularity_mismatches=REVIEWED_GRANULARITY.get(case_id, ()),
        )
        flow = score_control_flow_case(
            case_id, case.reference_graph, case.generated_graph, action
        )
        structure = score_control_structure_case(
            case_id, case.reference_graph, case.generated_graph, action
        )
        action_scores.append(action)
        flow_scores.append(flow)
        structure_scores.append(structure)
        records.append(_case_record(case_id, action, flow, structure))
    metadata = build_reproducibility_metadata(preflight, repository)
    summary = build_dataset_summary(
        records, action_scores, flow_scores, structure_scores, metadata
    )
    _publish_outputs(
        output_dir,
        manifest_path,
        artifact_manifest_path,
        records,
        evaluated_rows,
        summary,
    )
    return summary


def _parser() -> argparse.ArgumentParser:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Run the frozen formal Friedrich evaluation")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--execute-formal", action="store_true")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=base / "formal_inputs" / "v1" / "formal_manifest.json",
    )
    parser.add_argument(
        "--artifact-manifest",
        type=Path,
        default=base / "formal_inputs" / "v1" / "generated_artifact_manifest.json",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=base / "formal_results" / "v1"
    )
    parser.add_argument(
        "--model-cache", type=Path, default=Path("/private/tmp/friedrich-hf-cache")
    )
    parser.add_argument(
        "--wordnet-data", type=Path, default=Path("/private/tmp/friedrich-nltk-data")
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    preflight = run_preflight(
        args.manifest, args.artifact_manifest, args.model_cache, args.wordnet_data
    )
    if args.preflight_only:
        print(
            json.dumps(
                {
                    "status": "ready",
                    "dataset_total_cases": len(preflight.cases),
                    "supported_cases": len(preflight.supported_cases),
                    "unsupported_cases": len(preflight.cases) - len(preflight.supported_cases),
                    "unsupported_case_ids": sorted(UNSUPPORTED_CASES),
                    "formal_manifest_sha256": preflight.formal_manifest_sha256,
                    "generated_artifact_manifest_sha256": preflight.generated_artifact_manifest_sha256,
                    "formal_scoring_executed": False,
                },
                indent=2,
                ensure_ascii=True,
            )
        )
        return
    summary = execute_formal(
        preflight,
        args.manifest,
        args.artifact_manifest,
        args.output_dir,
        args.model_cache,
        args.wordnet_data,
    )
    print(json.dumps(_json_ready(summary), indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
