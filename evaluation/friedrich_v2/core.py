from __future__ import annotations

from collections import Counter, deque
from dataclasses import asdict, dataclass
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping


NodeType = Literal[
    "initial", "action", "decision", "merge", "fork", "join", "final",
    "unsupported_control",
]
ALLOWED_NODE_TYPES = frozenset(NodeType.__args__)
CONTROL_NODE_TYPES = frozenset(
    {"decision", "merge", "fork", "join", "unsupported_control"}
)


def normalize_label(value: Any) -> str | None:
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
    type: NodeType
    label: str | None = None
    semantic_type: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("EvalNode.id must not be empty")
        if self.type not in ALLOWED_NODE_TYPES:
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
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("EvalGraph node ids must be unique")
        known = set(ids)
        for edge in self.edges:
            if edge.source not in known or edge.target not in known:
                raise ValueError(f"Unknown node in edge {edge.source}->{edge.target}")

    @property
    def by_id(self) -> dict[str, EvalNode]:
        return {node.id: node for node in self.nodes}

    @property
    def outgoing(self) -> dict[str, tuple[str, ...]]:
        result: dict[str, list[str]] = {node.id: [] for node in self.nodes}
        for edge in self.edges:
            result[edge.source].append(edge.target)
        return {key: tuple(sorted(value)) for key, value in result.items()}

    @property
    def incoming(self) -> dict[str, tuple[str, ...]]:
        result: dict[str, list[str]] = {node.id: [] for node in self.nodes}
        for edge in self.edges:
            result[edge.target].append(edge.source)
        return {key: tuple(sorted(value)) for key, value in result.items()}

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [asdict(node) for node in self.nodes],
            "edges": [asdict(edge) for edge in self.edges],
        }


@dataclass(frozen=True, slots=True)
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def f1(self) -> float:
        total = 2 * self.tp + self.fp + self.fn
        return 2 * self.tp / total if total else 0.0

    def to_dict(self) -> dict[str, int | float]:
        return {
            "tp": self.tp, "fp": self.fp, "fn": self.fn,
            "precision": self.precision, "recall": self.recall, "f1": self.f1,
        }


@dataclass(frozen=True, slots=True)
class AutomaticItem:
    case_id: str
    candidate_id: str
    metric: str
    item_id: str
    label: str
    payload: Mapping[str, Any]
    evidence: Mapping[str, Any]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluation_item_id(case_id: str, candidate_id: str, *parts: str) -> str:
    return ":".join((case_id, candidate_id, *parts))


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def reachable(graph: EvalGraph, source: str, blocked: set[str] | None = None) -> set[str]:
    blocked = blocked or set()
    seen: set[str] = set()
    queue = deque([source])
    outgoing = graph.outgoing
    while queue:
        current = queue.popleft()
        for target in outgoing[current]:
            if target in blocked or target in seen:
                continue
            seen.add(target)
            queue.append(target)
    return seen


def strongly_connected_components(graph: EvalGraph) -> tuple[frozenset[str], ...]:
    outgoing = graph.outgoing
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    low: dict[str, int] = {}
    result: list[frozenset[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = low[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in outgoing[node]:
            if target not in indices:
                visit(target)
                low[node] = min(low[node], low[target])
            elif target in on_stack:
                low[node] = min(low[node], indices[target])
        if low[node] == indices[node]:
            component: set[str] = set()
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.add(member)
                if member == node:
                    break
            result.append(frozenset(component))

    for node in sorted(outgoing):
        if node not in indices:
            visit(node)
    return tuple(result)


def multiset_counts(reference: Iterable[Any], generated: Iterable[Any]) -> Counts:
    ref, gen = Counter(reference), Counter(generated)
    tp = sum((ref & gen).values())
    return Counts(tp=tp, fn=sum(ref.values()) - tp, fp=sum(gen.values()) - tp)
