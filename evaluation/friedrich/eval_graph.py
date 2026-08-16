from __future__ import annotations

from dataclasses import asdict, dataclass
import re
import unicodedata
from typing import Any, Literal


EvalNodeType = Literal[
    "initial", "action", "decision", "merge", "fork", "join", "final"
]

SCORING_NODE_TYPES = frozenset({"action", "decision", "merge", "fork", "join"})
_ALLOWED_NODE_TYPES = SCORING_NODE_TYPES | {"initial", "final"}


def normalize_label(value: Any) -> str | None:
    """Return a deterministic lexical form without attempting semantic matching."""
    if value is None:
        return None
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = re.sub(r"[_\-]+", " ", text)
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


@dataclass(frozen=True, slots=True)
class EvalNode:
    id: str
    type: EvalNodeType
    label: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("EvalNode.id must not be empty")
        if self.type not in _ALLOWED_NODE_TYPES:
            raise ValueError(f"Unsupported EvalNode type: {self.type}")


@dataclass(frozen=True, slots=True)
class EvalEdge:
    source: str
    target: str
    label: str | None = None


@dataclass(frozen=True, slots=True)
class EvalGraph:
    nodes: tuple[EvalNode, ...]
    edges: tuple[EvalEdge, ...]

    def __post_init__(self) -> None:
        node_ids = [node.id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("EvalGraph node ids must be unique")

        known_ids = set(node_ids)
        for edge in self.edges:
            if edge.source not in known_ids or edge.target not in known_ids:
                raise ValueError(
                    f"EvalEdge {edge.source}->{edge.target} references an unknown node"
                )

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "nodes": [asdict(node) for node in self.nodes],
            "edges": [asdict(edge) for edge in self.edges],
        }
