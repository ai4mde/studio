"""Opt-in Code candidate v8 with evidence-gated shared Control roles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evaluation.friedrich_v3.action import ACTION_SIMILARITY_THRESHOLD, SimilarityProvider
from evaluation.friedrich_v3.core import EvalGraph
from evaluation.friedrich_semantic_v2.evaluator_adapter import project_reviewed_inventory
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory

from .action_operation_guard_v4 import evaluate_semantic_actions_with_operation_guard_v4
from .alignment import ActionAlignmentTable, build_action_alignment_table
from .anchor_evidence import ControlAnchorEvidence, build_control_anchor_evidence
from .candidate_reporting_v1 import project_candidate_output
from .control import ControlComponentResult, normalize_generated_control
from .control_node_shared_roles_v5 import match_control_nodes_shared_roles_v5
from .control_relation_shared_owner_v4 import score_control_relations_shared_owner_v4
from .flow import FlowResultV3
from .flow_inventory_store import load_fixed_flow_inventory
from .flow_matched_action_v1 import evaluate_flow_matched_action_v1
from .inventory import FrozenCorpus
from .reference import reference_action_nodes, reference_graph
from .v3_2 import combine_control_nodes, score_structural_endpoints


VERSION = "friedrich-code-combined-construct-candidate/8"
FLOW_SNAPSHOT = (Path(__file__).resolve().parent / "fixed_flow_inventory/corpus_v1"
                 / "v3_2_alignment_flow_facts_1")


@dataclass(frozen=True, slots=True)
class CombinedCandidateResult:
    case_id: str
    candidate_id: str
    action: Any
    alignment: ActionAlignmentTable
    control_evidence: ControlAnchorEvidence
    flow: FlowResultV3
    control_node_source: ControlComponentResult
    control_node: ControlComponentResult
    control_relation: ControlComponentResult
    owners: dict[str, str | None]

    def to_dict(self) -> dict[str, Any]:
        row = {
            "configuration_version": VERSION,
            "case_id": self.case_id,
            "candidate_id": self.candidate_id,
            "Action": self.action.counts.to_dict(),
            "Action Alignment Table": self.alignment.to_dict(),
            "Control Anchor Evidence": self.control_evidence.to_dict(),
            "Flow": self.flow.to_dict(),
            "Control Node": self.control_node.to_dict(),
            "Control Node Source": self.control_node_source.to_dict(),
            "Control Relation": self.control_relation.to_dict(),
            "control_owners": dict(self.owners),
        }
        return project_candidate_output(row)


def evaluate_combined_candidate_v8(
    case_id: str, candidate_id: str, generated: EvalGraph,
    similarity: SimilarityProvider, *, corpus: FrozenCorpus,
    threshold: float = ACTION_SIMILARITY_THRESHOLD,
) -> CombinedCandidateResult:
    """Evaluate one frozen candidate without changing the frozen default."""
    case = corpus.load_case(case_id)
    reviewed = SemanticInventory.from_dict(case.reviewed_action)
    projection = project_reviewed_inventory(reviewed, case.reference_evidence)
    action = evaluate_semantic_actions_with_operation_guard_v4(
        case_id, candidate_id, projection.action_graph, generated, similarity,
        threshold, source_text=case.source_text,
        semantic_activity_units=projection.action_units,
    )
    alignment = build_action_alignment_table(action)
    control_evidence = build_control_anchor_evidence(
        reviewed, generated, alignment, similarity, case.source_text,
        control=case.control, reference_evidence=case.reference_evidence,
    )
    flow_inventory = load_fixed_flow_inventory(case_id, corpus, root=FLOW_SNAPSHOT)
    flow = evaluate_flow_matched_action_v1(
        flow_inventory, generated, alignment, case.control, reviewed,
    )
    normalized = normalize_generated_control(generated)
    reference = reference_graph(case.reference_evidence)
    node_source, owners = match_control_nodes_shared_roles_v5(
        case.control, normalized, control_evidence,
        reference=reference,
        reference_unit_nodes=reference_action_nodes(reviewed, reference),
        reference_evidence=case.reference_evidence,
    )
    relation = score_control_relations_shared_owner_v4(
        case.control, normalized, control_evidence, owners,
        case.reference_evidence, reviewed,
        owner_alternatives=node_source.assignment_alternatives,
    )
    node = combine_control_nodes(node_source, score_structural_endpoints(case_id, generated))
    result = CombinedCandidateResult(
        case_id, candidate_id, action, alignment, control_evidence,
        flow, node_source, node, relation, dict(owners),
    )
    result.to_dict()  # Check every component's fixed-denominator contract.
    return result
