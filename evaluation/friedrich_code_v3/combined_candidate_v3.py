"""Opt-in combined candidate with source-grounded Action eligibility v1.

The reviewed corpus remains frozen. The versioned overlay retains a standalone
reference-only Action for provenance but excludes it from primary Action scoring.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

from evaluation.friedrich_v3.action import ACTION_SIMILARITY_THRESHOLD, SimilarityProvider
from evaluation.friedrich_v3.core import EvalGraph

from .combined_candidate_v2 import CombinedCandidateResult, evaluate_combined_candidate_v2
from .inventory import FrozenCorpus


VERSION = "friedrich-code-combined-construct-candidate/3"
SNAPSHOT = Path(__file__).resolve().parent / "source_action_eligibility/corpus_v1/v1"


class SourceEligibilityCorpus:
    """Read-only view over the frozen corpus with a verified eligibility overlay."""

    def __init__(self, frozen: FrozenCorpus) -> None:
        self.frozen = frozen
        self.manifest = frozen.manifest
        self.source_root = frozen.source_root
        self.corpus_sha256 = frozen.corpus_sha256
        self.case_ids = frozen.case_ids
        self.eligibility = json.loads((SNAPSHOT / "manifest.json").read_text())
        if self.eligibility["version"] != "source-action-eligibility/1":
            raise ValueError("unexpected source eligibility snapshot")
        if self.eligibility["frozen_corpus_sha256"] != frozen.corpus_sha256:
            raise ValueError("source eligibility corpus mismatch")
        if tuple(self.eligibility["excluded_primary_units"]) != ("SU-6-4-16",):
            raise ValueError("unexpected excluded Action units")
        source = frozen.load_case("6-4")
        digest = hashlib.sha256(json.dumps(source.reviewed_action, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        if digest != self.eligibility["reviewed_inventory_canonical_sha256"]:
            raise ValueError("reviewed source inventory mismatch")
        item = next(u for u in source.reviewed_action["units"] if u["semantic_unit_id"] == "SU-6-4-16")
        occurrences = [o for o in source.reviewed_action["occurrences"] if o["semantic_unit_id"] == "SU-6-4-16"]
        if len(occurrences) != 1 or occurrences[0]["evidence_status"] != "reference_only" or occurrences[0]["source_text_evidence"]:
            raise ValueError("reference-only evidence changed")
        if item["canonical_meaning"] != "Import an Excel sheet with customer data":
            raise ValueError("reference-only Action identity changed")

    def load_case(self, case_id: str):
        case = self.frozen.load_case(case_id)
        if case_id != "6-4":
            return case
        reviewed = dict(case.reviewed_action)
        reviewed["units"] = [u for u in reviewed["units"] if u["semantic_unit_id"] != "SU-6-4-16"]
        reviewed["occurrences"] = [o for o in reviewed["occurrences"] if o["semantic_unit_id"] != "SU-6-4-16"]
        return replace(case, reviewed_action=reviewed)


def evaluate_combined_candidate_v3(
    case_id: str, candidate_id: str, generated: EvalGraph, similarity: SimilarityProvider,
    *, corpus: SourceEligibilityCorpus, threshold: float = ACTION_SIMILARITY_THRESHOLD,
) -> CombinedCandidateResult:
    return evaluate_combined_candidate_v2(case_id, candidate_id, generated, similarity,
                                          corpus=corpus, threshold=threshold)
