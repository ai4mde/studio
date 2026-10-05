"""V3.2 structural endpoint presence, layered on the certified V3.1 scorer.

This module does not change source facts, gateway matching, or relation matching.
The endpoint checks are fixed diagram-format requirements, not source facts.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Any

from evaluation.friedrich_v3.action import ACTION_SIMILARITY_THRESHOLD, SimilarityProvider
from evaluation.friedrich_v3.adapters import load_generated_graph
from evaluation.friedrich_v3.core import Counts, EvalGraph

from .control import ControlComponentResult, ControlFactResult
from .evaluator import evaluate_candidate_file_v3, evaluate_inventory_candidate_v3
from .inventory import APPROVED_CORPUS_SHA256, FrozenCorpus, load_frozen_corpus


CONTRACT_PATH = Path(__file__).resolve().parent / "v3_2/structural_endpoint_contract.json"
SCHEMA_VERSION = "friedrich-code-v3.2/structural-endpoints-1"
ENDPOINT_TYPES = (("Start", "initial"), ("End", "final"))


def load_structural_contract() -> tuple[dict[str, Any], str]:
    data = CONTRACT_PATH.read_bytes()
    contract = json.loads(data)
    if (
        contract.get("contract_version") != "v3.2-structural-endpoint-presence-1"
        or contract.get("status") != "APPROVED_FOR_PREFLIGHT"
        or contract.get("base_v3_1_corpus_sha256") != APPROVED_CORPUS_SHA256
        or [(item.get("name"), item.get("parsed_node_type"), item.get("required_count"))
            for item in contract.get("structural_checks_per_candidate", [])]
        != [(name, node_type, 1) for name, node_type in ENDPOINT_TYPES]
    ):
        raise ValueError("V3.2 structural contract differs from the approved preflight rule")
    return contract, hashlib.sha256(data).hexdigest()


def score_structural_endpoints(case_id: str, graph: EvalGraph) -> ControlComponentResult:
    """Score two binary presence checks on an already validated generated graph."""
    if not isinstance(graph, EvalGraph):
        raise TypeError("malformed candidate: expected a validated EvalGraph")
    facts: list[ControlFactResult] = []
    for name, node_type in ENDPOINT_TYPES:
        observed = sorted(node.id for node in graph.nodes if node.type == node_type)
        facts.append(ControlFactResult(
            f"STRUCT-{case_id}-{name.upper()}", name,
            "TP" if observed else "FN", observed[0] if observed else None,
            "parsed endpoint type present" if observed else "parsed endpoint type absent",
            {"parsed_node_type": node_type, "observed_node_ids": observed,
             "presence_only": True, "additional_nodes_scored_as_fp": False},
        ))
    return ControlComponentResult(
        Counts(sum(f.status == "TP" for f in facts), 0,
               sum(f.status == "FN" for f in facts)),
        tuple(facts), 2, 0, 0, 0, 0,
    )


def combine_control_nodes(
    source_derived: ControlComponentResult,
    structural: ControlComponentResult,
) -> ControlComponentResult:
    """Add structural counts without changing V3.1 assignments or FP policy."""
    if structural.required_fact_count != 2 or structural.counts.fp or structural.candidate_abstention_count:
        raise ValueError("structural endpoints must be two determinate TP/FN checks")
    return replace(
        source_derived,
        counts=Counts(
            source_derived.counts.tp + structural.counts.tp,
            source_derived.counts.fp,
            source_derived.counts.fn + structural.counts.fn,
        ),
        facts=source_derived.facts + structural.facts,
        required_fact_count=source_derived.required_fact_count + 2,
    )


def evaluate_inventory_candidate_v3_2(
    case_id: str,
    candidate_id: str,
    generated: EvalGraph,
    similarity: SimilarityProvider,
    *,
    corpus: FrozenCorpus | None = None,
    threshold: float = ACTION_SIMILARITY_THRESHOLD,
) -> dict[str, Any]:
    """Run V3.1 verbatim, then add two independent structural Control Node facts."""
    corpus = corpus or load_frozen_corpus()
    _, contract_sha256 = load_structural_contract()
    if corpus.corpus_sha256 != APPROVED_CORPUS_SHA256:
        raise ValueError("V3.2 must use the certified V3.1 source corpus")
    base = evaluate_inventory_candidate_v3(
        case_id, candidate_id, generated, similarity, corpus=corpus, threshold=threshold,
    )
    structural = score_structural_endpoints(case_id, generated)
    combined = combine_control_nodes(base.control_node, structural)
    result = base.to_dict()
    result["schema_version"] = SCHEMA_VERSION
    result["v3_2_structural_contract_sha256"] = contract_sha256
    result["Control Node"] = combined.to_dict()
    result["Control Node Breakdown"] = {
        "source_derived": base.control_node.to_dict(),
        "structural_endpoints": structural.to_dict(),
        "combined": combined.to_dict(),
    }
    return result


def evaluate_candidate_file_v3_2(
    case_id: str, candidate_id: str, candidate_path: str | Path,
    similarity: SimilarityProvider, *, corpus: FrozenCorpus | None = None,
) -> dict[str, Any]:
    """Preserve V3.1 malformed-candidate handling and add fixed structural scope."""
    corpus = corpus or load_frozen_corpus()
    _, contract_sha256 = load_structural_contract()
    try:
        generated = load_generated_graph(candidate_path)
    except (OSError, UnicodeError, ValueError, TypeError):
        result = evaluate_candidate_file_v3(
            case_id, candidate_id, candidate_path, similarity, corpus=corpus,
        )
        result["schema_version"] = SCHEMA_VERSION
        result["v3_2_structural_contract_sha256"] = contract_sha256
        result["Control Node Breakdown"] = None
        result["structural_required_denominator"] = 2
        result["combined_control_node_denominator"] = result["source_denominators"]["Control Node"] + 2
        return result
    result = evaluate_inventory_candidate_v3_2(
        case_id, candidate_id, generated, similarity, corpus=corpus,
    )
    result["candidate_status"] = "EVALUATED"
    return result
