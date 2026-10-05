"""Versioned Flow eligibility rule for reliably matched semantic Actions.

Frozen V3.2 Flow remains unchanged. This adapter preserves its precedence
assessment for every assessable pair and reclassifies only required pairs
whose accepted Action anchor is missing. An absent accepted alignment alone
does not establish whether the activity is absent or matching was uncertain.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from evaluation.friedrich_v3.core import Counts, EvalGraph
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory

from .alignment import ActionAlignmentTable
from .flow import FlowInventoryV3, FlowResultV3, evaluate_flow_v3


VERSION = "friedrich-code-flow-matched-action/1"
_MISSING_ANCHOR_REASON = "required Action anchor missing"


def evaluate_flow_matched_action_v1(
    inventory: FlowInventoryV3,
    generated: EvalGraph,
    alignment: ActionAlignmentTable,
    control: Mapping[str, Any] | None = None,
    reviewed: SemanticInventory | None = None,
) -> FlowResultV3:
    """Score precedence only for pairs with accepted, unambiguous Action anchors."""
    baseline = evaluate_flow_v3(inventory, generated, alignment, control, reviewed)
    facts = []
    converted = 0
    for fact in baseline.facts:
        if fact.status != "FN" or fact.reason != _MISSING_ANCHOR_REASON:
            facts.append(fact)
            continue
        missing = tuple(unit for unit in (fact.source_unit_id, fact.target_unit_id)
                        if not alignment.generated(unit))
        if not missing or any(alignment.is_ambiguous(unit) for unit in missing):
            raise ValueError("Missing-anchor Flow fact conflicts with Action alignment")
        diagnostics = {
            **fact.diagnostics,
            "reason_code": "FLOW_ACTION_ANCHOR_UNMATCHED",
            "unmatched_source_action_unit_ids": list(missing),
            "accepted_generated_anchor_ids": {
                unit: sorted(alignment.generated(unit))
                for unit in (fact.source_unit_id, fact.target_unit_id)
            },
            "underlying_cause": "absence_or_matching_failure_not_determined_by_alignment",
        }
        facts.append(replace(
            fact,
            status="indeterminate_alignment",
            reason="required Action anchor has no accepted semantic match",
            diagnostics=diagnostics,
        ))
        converted += 1
    if not converted:
        return baseline
    if converted > baseline.counts.fn:
        raise ValueError("Converted Flow facts exceed frozen FN count")
    result = replace(
        baseline,
        counts=Counts(baseline.counts.tp, baseline.counts.fp,
                      baseline.counts.fn - converted),
        facts=tuple(facts),
        candidate_unresolved_count=baseline.candidate_unresolved_count + converted,
    )
    # The existing fixed-denominator scoring contract checks the invariant
    # and makes candidate precision, recall, and F1 null when I > 0.
    result.to_dict()
    return result
