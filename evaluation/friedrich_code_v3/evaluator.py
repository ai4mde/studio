"""Four-component Friedrich V3 Code-based Evaluator entry point.

The evaluator reads the frozen source inventory, reuses V2's accepted Action
matching convention, and never writes candidate results or source facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evaluation.friedrich_v3.action import ACTION_SIMILARITY_THRESHOLD, SimilarityProvider
from evaluation.friedrich_v3.core import EvalGraph
from evaluation.friedrich_v3.adapters import load_generated_graph
from evaluation.friedrich_semantic.action import SemanticActionResult, evaluate_semantic_actions
from evaluation.friedrich_semantic_v2.evaluator_adapter import project_reviewed_inventory
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory

from .alignment import ActionAlignmentTable, build_action_alignment_table
from .anchor_evidence import ControlAnchorEvidence, build_control_anchor_evidence
from .control import ControlComponentResult, match_control_nodes, normalize_generated_control, score_control_relations
from .flow import FlowResultV3, evaluate_flow_v3
from .flow_inventory_store import load_fixed_flow_inventory
from .inventory import FrozenCorpus, load_frozen_corpus
from .reference import reference_action_nodes, reference_graph


@dataclass(frozen=True, slots=True)
class InventoryEvaluationResultV3:
    case_id: str
    candidate_id: str
    corpus_sha256: str
    action: SemanticActionResult
    alignment: ActionAlignmentTable
    control_anchor_evidence: ControlAnchorEvidence
    flow: FlowResultV3
    control_node: ControlComponentResult
    control_relation: ControlComponentResult
    source_unresolved_questions: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "friedrich-code-v3.1/four-components-1",
            "case_id": self.case_id,
            "candidate_id": self.candidate_id,
            "frozen_corpus_sha256": self.corpus_sha256,
            "Action": self.action.counts.to_dict(),
            "Action Alignment Table": self.alignment.to_dict(),
            "Control Anchor Evidence": self.control_anchor_evidence.to_dict(),
            "Flow": self.flow.to_dict(),
            "Control Node": self.control_node.to_dict(),
            "Control Relation": self.control_relation.to_dict(),
            "source_unresolved_questions": list(self.source_unresolved_questions),
        }


def evaluate_inventory_candidate_v3(
    case_id: str,
    candidate_id: str,
    generated: EvalGraph,
    similarity: SimilarityProvider,
    *,
    corpus: FrozenCorpus | None = None,
    threshold: float = ACTION_SIMILARITY_THRESHOLD,
) -> InventoryEvaluationResultV3:
    """Evaluate one graph against immutable V3 source facts, with no batch run."""
    corpus = corpus or load_frozen_corpus()
    if not isinstance(generated, EvalGraph):
        raise TypeError("malformed candidate: expected a validated EvalGraph")
    case = corpus.load_case(case_id)
    reviewed = SemanticInventory.from_dict(case.reviewed_action)
    projection = project_reviewed_inventory(reviewed, case.reference_evidence)
    action = evaluate_semantic_actions(
        case_id, candidate_id, projection.action_graph, generated, similarity,
        threshold, source_text=case.source_text,
        semantic_activity_units=projection.action_units,
    )
    alignment = build_action_alignment_table(action)
    control_evidence = build_control_anchor_evidence(
        reviewed, generated, alignment, similarity, case.source_text,
        control=case.control, reference_evidence=case.reference_evidence,
    )
    flow_inventory = load_fixed_flow_inventory(case_id, corpus)
    flow = evaluate_flow_v3(flow_inventory, generated, alignment, case.control, reviewed)
    normalized_generated = normalize_generated_control(generated)
    raw_reference = reference_graph(case.reference_evidence)
    reference_unit_nodes = reference_action_nodes(reviewed, raw_reference)
    node_result, matched_nodes = match_control_nodes(
        case.control, normalized_generated, control_evidence,
        reference=raw_reference, reference_unit_nodes=reference_unit_nodes,
        reference_evidence=case.reference_evidence,
    )
    relation_result = score_control_relations(
        case.control, normalized_generated, control_evidence, matched_nodes,
        case.reference_evidence, owner_alternatives=node_result.assignment_alternatives,
    )
    return InventoryEvaluationResultV3(
        case_id, candidate_id, corpus.corpus_sha256, action, alignment, control_evidence, flow,
        node_result, relation_result,
        tuple(dict(question) for question in case.control["unresolved_facts"]),
    )


def evaluate_candidate_file_v3(
    case_id: str, candidate_id: str, candidate_path: str | Path,
    similarity: SimilarityProvider, *, corpus: FrozenCorpus | None = None,
) -> dict[str, Any]:
    """Report malformed candidates without inventing component scores."""
    corpus = corpus or load_frozen_corpus()
    try:
        generated = load_generated_graph(candidate_path)
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        case = corpus.load_case(case_id)
        flow = load_fixed_flow_inventory(case_id, corpus)
        reviewed = SemanticInventory.from_dict(case.reviewed_action)
        projected = project_reviewed_inventory(reviewed, case.reference_evidence)
        return {
            "schema_version": "friedrich-code-v3.1/four-components-1",
            "case_id": case_id,
            "candidate_id": candidate_id,
            "frozen_corpus_sha256": corpus.corpus_sha256,
            "candidate_status": "MALFORMED",
            "malformed_reason": f"{type(exc).__name__}: {exc}",
            "component_scores": None,
            "source_denominators": {
                "Action": len(projected.action_units),
                "Flow": len(flow.required_precedence),
                "Control Node": sum(f["status"] == "required" for f in case.control["control_nodes"]),
                "Control Relation": sum(f["status"] == "required" for f in case.control["control_relations"]),
            },
            "source_unresolved_questions": [dict(item) for item in case.control["unresolved_facts"]],
        }
    result = evaluate_inventory_candidate_v3(
        case_id, candidate_id, generated, similarity, corpus=corpus,
    ).to_dict()
    result["candidate_status"] = "EVALUATED"
    return result
