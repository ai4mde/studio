"""Complete reference EvalGraph from reviewed reference evidence.

Unlike V2's occurrence projection, this graph does not add boundary-constraint
edges between alternative Action anchors. Every original sequence-flow gateway
remains traversable during V3 Flow extraction.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from typing import Any, Mapping, Sequence

from evaluation.friedrich_v3.core import EvalEdge, EvalGraph, EvalNode
from evaluation.friedrich_semantic.action import SemanticActivityUnit
from evaluation.friedrich_semantic_v2.semantic_inventory import SemanticInventory


def reference_graph(evidence: Mapping[str, Any]) -> EvalGraph:
    raw_nodes = {
        str(node["node_id"]): node for node in evidence["nodes"]
        if node["node_type"] in {"Task", "SubProcess", "IntermediateEvent", "Gateway",
                                 "StartEvent", "StopEvent"}
    }
    raw_edges = [
        edge for edge in evidence["edges"]
        if edge.get("edge_type") == "SequenceFlow"
        and str(edge.get("source_id")) in raw_nodes
        and str(edge.get("target_id")) in raw_nodes
    ]
    incoming = Counter(str(edge["target_id"]) for edge in raw_edges)
    outgoing = Counter(str(edge["source_id"]) for edge in raw_edges)
    nodes: list[EvalNode] = []
    for node_id, raw in raw_nodes.items():
        kind = raw["node_type"]
        if kind == "StartEvent":
            node_type = "initial"
        elif kind == "StopEvent":
            node_type = "final"
        elif kind in {"Task", "SubProcess", "IntermediateEvent"}:
            node_type = "action"
        elif kind == "Gateway":
            parallel = raw.get("gateway_type") == "Parallel"
            if outgoing[node_id] > 1 and incoming[node_id] > 1:
                node_type = "unsupported_control"
            elif outgoing[node_id] > 1:
                node_type = "fork" if parallel else "decision"
            else:
                node_type = "join" if parallel else "merge"
        else:
            raise ValueError(f"unsupported raw reference node type {kind}")
        nodes.append(EvalNode(node_id, node_type, raw.get("label") or None,
                              raw.get("gateway_type") if kind == "Gateway" else None))
    edges = tuple(EvalEdge(str(edge["source_id"]), str(edge["target_id"]),
                           edge.get("label") or None) for edge in raw_edges)
    return EvalGraph(tuple(nodes), edges)


def reference_action_nodes(
    inventory: SemanticInventory, graph: EvalGraph,
) -> dict[str, tuple[str, ...]]:
    units: dict[str, set[str]] = {}
    for occurrence in inventory.occurrences:
        if occurrence.evidence_status == "text_only" or not occurrence.source_text_evidence:
            continue
        valid = set(occurrence.reference_node_ids) & set(graph.by_id)
        if valid:
            units.setdefault(occurrence.semantic_unit_id, set()).update(valid)
    return {unit: tuple(sorted(nodes)) for unit, nodes in units.items()}


def reference_flow_units(
    action_units: Sequence[SemanticActivityUnit],
    unit_nodes: Mapping[str, tuple[str, ...]],
) -> tuple[SemanticActivityUnit, ...]:
    return tuple(
        replace(unit, reference_ids=unit_nodes[unit.unit_id],
                reference_labels=tuple(unit.meaning for _ in unit_nodes[unit.unit_id]))
        for unit in action_units if unit.unit_id in unit_nodes
    )
