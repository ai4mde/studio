from __future__ import annotations

# Responsibility:
# - conservative vocabulary normalization for ActivityGraph payloads only
# - align legacy aliases onto the current clean-layer field and type vocabulary
#
# Must NOT:
# - repair topology
# - redesign graph semantics
# - infer missing merges, joins, or loops
# - convert semantic branch conditions into display labels

from copy import deepcopy
from typing import Any, Dict, Iterable, Optional


NODE_TEXT_ALIASES: tuple[str, ...] = ("label", "title", "text")
EDGE_LABEL_ALIASES: tuple[str, ...] = ("label", "branch", "text", "title")
EDGE_SOURCE_ALIASES: tuple[str, ...] = ("source", "from", "src", "source_id")
EDGE_TARGET_ALIASES: tuple[str, ...] = ("target", "to", "dst", "target_id")

NODE_TYPE_NORMALIZATION: Dict[str, str] = {
    "initialnode": "initial",
    "start": "initial",
    "startnode": "initial",
    "activity": "action",
    "task": "action",
    # LLMs sometimes emit semantic node types like "loop".
    # Normalize them into valid UML Activity Diagram constructs
    # before strict schema validation.
    "loop": "decision",
    "decisionnode": "decision",
    "merge node": "merge",
    "mergenode": "merge",
    "fork node": "fork",
    "forknode": "fork",
    "join node": "join",
    "joinnode": "join",
    "end": "final",
    "endnode": "final",
    "finalnode": "final",
    "datanode": "object",
    "objectnode": "object",
}

EDGE_TYPE_NORMALIZATION: Dict[str, str] = {
    "control": "control",
    "controlflow": "control",
    "control_flow": "control",
    "control-flow": "control",
    "object": "object",
    "objectflow": "object",
    "object_flow": "object",
    "object-flow": "object",
}


def _normalized_token(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def _normalized_lookup_key(value: Any) -> Optional[str]:
    text = _normalized_token(value)
    if text is None:
        return None
    return text.lower().replace(" ", "").replace("-", "").replace("_", "")


def _first_text_value(payload: Dict[str, Any], aliases: Iterable[str]) -> Optional[str]:
    for alias in aliases:
        text = _normalized_token(payload.get(alias))
        if text:
            return text
    return None


def _ensure_question_text(value: Optional[str]) -> Optional[str]:
    text = _normalized_token(value)
    if not text:
        return None
    if text.endswith("?"):
        return text
    return text.rstrip(".!") + "?"


def _normalize_node(node: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(node)

    node_type_key = _normalized_lookup_key(normalized.get("type"))
    if node_type_key and node_type_key in NODE_TYPE_NORMALIZATION:
        normalized["type"] = NODE_TYPE_NORMALIZATION[node_type_key]
    elif node_type_key:
        normalized["type"] = node_type_key

    node_type = normalized.get("type")

    label_text = _first_text_value(normalized, NODE_TEXT_ALIASES)
    if label_text and not _normalized_token(normalized.get("label")):
        normalized["label"] = label_text

    if node_type == "action":
        action_name = _first_text_value(
            normalized,
            ("name", "label", "title", "text"),
        )
        if action_name and not _normalized_token(normalized.get("name")):
            normalized["name"] = action_name
    elif node_type == "decision":
        decision_text = _first_text_value(
            normalized,
            ("label", "name", "title", "text"),
        )
        if decision_text:
            normalized["label"] = _ensure_question_text(decision_text)

    origin_step_id = _normalized_token(
        normalized.get("origin_step_id", normalized.get("originStepId"))
    )
    if origin_step_id and not _normalized_token(normalized.get("origin_step_id")):
        normalized["origin_step_id"] = origin_step_id

    origin_block_id = _normalized_token(
        normalized.get("origin_block_id", normalized.get("originBlockId"))
    )
    if origin_block_id and not _normalized_token(normalized.get("origin_block_id")):
        normalized["origin_block_id"] = origin_block_id

    normalized.pop("title", None)
    normalized.pop("text", None)
    normalized.pop("originStepId", None)
    normalized.pop("originBlockId", None)
    return normalized


def _normalize_edge(edge: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(edge)

    source_id = _first_text_value(normalized, EDGE_SOURCE_ALIASES)
    if source_id and not _normalized_token(normalized.get("source")):
        normalized["source"] = source_id

    target_id = _first_text_value(normalized, EDGE_TARGET_ALIASES)
    if target_id and not _normalized_token(normalized.get("target")):
        normalized["target"] = target_id

    edge_type_key = _normalized_lookup_key(normalized.get("type"))
    if edge_type_key and edge_type_key in EDGE_TYPE_NORMALIZATION:
        normalized["type"] = EDGE_TYPE_NORMALIZATION[edge_type_key]

    label_text = _first_text_value(normalized, EDGE_LABEL_ALIASES)
    if label_text and not _normalized_token(normalized.get("label")):
        normalized["label"] = label_text

    normalized.pop("branch", None)
    normalized.pop("text", None)
    normalized.pop("title", None)
    normalized.pop("from", None)
    normalized.pop("to", None)
    normalized.pop("src", None)
    normalized.pop("dst", None)
    normalized.pop("source_id", None)
    normalized.pop("target_id", None)
    return normalized


def normalize_activity_graph(data: Any) -> Any:
    """
    Return a lightly normalized ActivityGraph payload.

    This function is intentionally conservative:
    - normalize vocabulary/field aliases
    - do not invent graph structure
    - do not convert semantic fields such as ``condition`` into ``label``
    """
    if not isinstance(data, dict):
        return data

    normalized = deepcopy(data)

    nodes = normalized.get("nodes")
    if isinstance(nodes, list):
        normalized["nodes"] = [
            _normalize_node(node) if isinstance(node, dict) else node
            for node in nodes
        ]

    edges = normalized.get("edges")
    if isinstance(edges, list):
        normalized["edges"] = [
            _normalize_edge(edge) if isinstance(edge, dict) else edge
            for edge in edges
        ]

    return normalized


__all__ = ["normalize_activity_graph"]
