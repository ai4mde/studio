"""Friedrich V3 evaluator against the immutable Control Fact Inventory."""

from pathlib import Path
import evaluation as _evaluation_package

# Reuse the adjacent, unchanged semantic Action implementation in this process.
_semantic_evaluation = Path(__file__).resolve().parents[3] / "studio-semantic-v2" / "evaluation"
if _semantic_evaluation.is_dir() and str(_semantic_evaluation) not in _evaluation_package.__path__:
    _evaluation_package.__path__.append(str(_semantic_evaluation))

from .evaluator import evaluate_inventory_candidate_v3
from .inventory import FrozenCorpus, load_frozen_corpus
from .specification_audit import FrozenSpecificationConflict, audit_action_anchor_coverage

__all__ = [
    "FrozenCorpus", "FrozenSpecificationConflict", "audit_action_anchor_coverage",
    "evaluate_inventory_candidate_v3", "load_frozen_corpus",
]
