"""Detect frozen facts that the accepted V2 Action mapping cannot represent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from evaluation.friedrich_semantic_v2.evaluator_adapter import project_reviewed_inventory
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory

from .inventory import FrozenCorpus


ANCHOR_FIELDS = (
    "anchor_action_ids", "target_action_ids", "incoming_action_ids",
    "excluded_action_ids", "required_on_branch_action_ids",
)


class FrozenSpecificationConflict(RuntimeError):
    """The frozen scoring facts cannot be evaluated under the requested method."""


@dataclass(frozen=True, slots=True)
class UnalignableRequiredFact:
    case_id: str
    fact_id: str
    component: str
    unit_ids: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id, "fact_id": self.fact_id,
            "component": self.component, "unit_ids": list(self.unit_ids),
            "reason": self.reason,
        }


def audit_action_anchor_coverage(corpus: FrozenCorpus) -> tuple[UnalignableRequiredFact, ...]:
    findings: list[UnalignableRequiredFact] = []
    for case_id in corpus.case_ids:
        case = corpus.load_case(case_id)
        reviewed = SemanticInventory.from_dict(case.reviewed_action)
        projection = project_reviewed_inventory(reviewed, case.reference_evidence)
        eligible = {unit.unit_id for unit in projection.action_units}
        units = {unit.semantic_unit_id: unit for unit in reviewed.units}
        occurrences = {
            unit_id: tuple(o for o in reviewed.occurrences if o.semantic_unit_id == unit_id)
            for unit_id in units
        }
        for component, facts in (("Control Node", case.control["control_nodes"]),
                                 ("Control Relation", case.control["control_relations"])):
            for fact in facts:
                if fact["status"] != "required":
                    continue
                missing = sorted({
                    unit for field in ANCHOR_FIELDS for unit in fact.get(field, [])
                    if unit not in eligible
                })
                if missing:
                    reasons = {
                        "researcher_ambiguous" if units[unit].provenance.review_state == "ambiguous"
                        else "text_only_excluded_by_v2_action_projection"
                        if all(o.evidence_status == "text_only" for o in occurrences[unit])
                        else "excluded_by_v2_action_projection"
                        for unit in missing
                    }
                    findings.append(UnalignableRequiredFact(
                        case_id, fact["fact_id"], component, tuple(missing),
                        ", ".join(sorted(reasons)),
                    ))
    return tuple(findings)


def require_action_anchor_coverage(corpus: FrozenCorpus) -> None:
    affected = audit_action_anchor_coverage(corpus)
    if affected:
        cases = ", ".join(sorted({item.case_id for item in affected}))
        raise FrozenSpecificationConflict(
            f"{len(affected)} required frozen Control facts in {len(set(item.case_id for item in affected))} "
            f"cases have Action units excluded from V2 accepted mappings ({cases}). "
            "The frozen Action-anchor contradiction must be adjudicated before any V3 scoring."
        )
