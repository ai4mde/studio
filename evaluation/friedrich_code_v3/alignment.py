"""Expose the accepted V2 Action mappings as a many-to-many V3 alignment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from evaluation.friedrich_semantic.action import SemanticActionResult


@dataclass(frozen=True, slots=True)
class AlignmentEntry:
    mapping_id: str
    kind: str
    unit_ids: tuple[str, ...]
    reference_ids: tuple[str, ...]
    generated_ids: tuple[str, ...]
    evidence: Mapping[str, Any]
    review_triggers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ActionAlignmentTable:
    entries: tuple[AlignmentEntry, ...]
    unit_to_generated: Mapping[str, frozenset[str]]
    generated_to_units: Mapping[str, frozenset[str]]
    ambiguous_unit_ids: frozenset[str]
    ambiguous_candidates: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    def generated(self, unit_id: str) -> frozenset[str]:
        return self.unit_to_generated.get(unit_id, frozenset())

    def is_ambiguous(self, unit_id: str) -> bool:
        return unit_id in self.ambiguous_unit_ids

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [
                {"mapping_id": e.mapping_id, "kind": e.kind, "unit_ids": list(e.unit_ids),
                 "reference_ids": list(e.reference_ids), "generated_ids": list(e.generated_ids),
                 "evidence": dict(e.evidence), "review_triggers": list(e.review_triggers)}
                for e in self.entries
            ],
            "ambiguous_unit_ids": sorted(self.ambiguous_unit_ids),
            "ambiguous_candidate_ids": {
                key: list(value) for key, value in sorted(self.ambiguous_candidates.items())
            },
        }


def build_action_alignment_table(action: SemanticActionResult) -> ActionAlignmentTable:
    entries = tuple(
        AlignmentEntry(m.mapping_id, m.kind, tuple(m.unit_ids), tuple(m.reference_ids),
                       tuple(m.generated_ids), m.evidence, tuple(m.review_triggers))
        for m in action.accepted_mappings
    )
    by_unit: dict[str, set[str]] = {}
    by_generated: dict[str, set[str]] = {}
    for entry in entries:
        for unit_id in entry.unit_ids:
            by_unit.setdefault(unit_id, set()).update(entry.generated_ids)
        for generated_id in entry.generated_ids:
            by_generated.setdefault(generated_id, set()).update(entry.unit_ids)
    ambiguous = {
        str(item["unit_id"]) for item in action.ambiguous_mappings
        if item.get("unit_id") and str(item["unit_id"]) not in by_unit
    }
    ambiguous_candidates = {
        str(item["unit_id"]): tuple(sorted({str(candidate["generated_id"])
            for candidate in item.get("candidates", ()) if candidate.get("generated_id")}))
        for item in action.ambiguous_mappings if str(item.get("unit_id", "")) in ambiguous
    }
    return ActionAlignmentTable(
        entries,
        {key: frozenset(value) for key, value in by_unit.items()},
        {key: frozenset(value) for key, value in by_generated.items()},
        frozenset(ambiguous),
        ambiguous_candidates,
    )
