from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Dict, List, Tuple

from pydantic import ValidationError

from .activity_model import ActivityModel
from .normalization import normalize_activity_graph


TechnicalValidityReport = Dict[str, Any]


class TechnicalValidityError(ValueError):
    def __init__(self, message: str, *, report: TechnicalValidityReport) -> None:
        super().__init__(message)
        self.report = report


def _new_report() -> TechnicalValidityReport:
    return {
        "technical_accepted": False,
        "failure_reason": None,
        "normalization_applied": False,
        "normalizations": [],
        "dropped_edges": [],
        "quality_warnings": [],
        "conversion_result": "not_checked",
        "import_result": "not_checked",
    }


def _fail(report: TechnicalValidityReport, reason: str) -> None:
    report["failure_reason"] = reason
    raise TechnicalValidityError(reason, report=report)


def merge_technical_validity_reports(
    *reports: TechnicalValidityReport | None,
) -> TechnicalValidityReport:
    """Combine successive checks without erasing earlier normalization evidence."""
    merged = _new_report()
    present = [report for report in reports if report]
    if not present:
        return merged

    for key in ("normalizations", "dropped_edges", "quality_warnings"):
        seen: set[str] = set()
        for report in present:
            for item in report.get(key) or []:
                signature = json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
                if signature not in seen:
                    merged[key].append(deepcopy(item))
                    seen.add(signature)

    merged["normalization_applied"] = any(
        bool(report.get("normalization_applied")) for report in present
    )
    merged["technical_accepted"] = all(
        bool(report.get("technical_accepted")) for report in present
    )
    for key in ("failure_reason", "conversion_result", "import_result"):
        meaningful = [
            report.get(key)
            for report in present
            if report.get(key) not in (None, "not_checked")
        ]
        if meaningful:
            merged[key] = meaningful[-1]
    return merged


def _alias_change_records(before: Dict[str, Any], after: Dict[str, Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for collection in ("nodes", "edges"):
        before_items = before.get(collection)
        after_items = after.get(collection)
        if not isinstance(before_items, list) or not isinstance(after_items, list):
            continue
        for index, (before_item, after_item) in enumerate(
            zip(before_items, after_items), start=1
        ):
            if not isinstance(before_item, dict) or not isinstance(after_item, dict):
                continue
            changes = {
                key: {"before": before_item.get(key), "after": after_item.get(key)}
                for key in sorted(set(before_item) | set(after_item))
                if before_item.get(key) != after_item.get(key)
            }
            if changes:
                records.append(
                    {"kind": "known_field_or_type_aliases", "collection": collection, "index": index, "changes": changes}
                )
    return records


def _quality_warnings(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    nodes = graph["nodes"]
    edges = graph["edges"]
    node_ids = {str(node["id"]) for node in nodes}
    node_type = {str(node["id"]): str(node["type"]) for node in nodes}
    adjacency = {node_id: set() for node_id in node_ids}
    reverse = {node_id: set() for node_id in node_ids}
    for edge in edges:
        source = str(edge["source"])
        target = str(edge["target"])
        adjacency[source].add(target)
        reverse[target].add(source)

    warnings: List[Dict[str, Any]] = []
    initial_ids = sorted(node_id for node_id, kind in node_type.items() if kind == "initial")
    final_ids = sorted(node_id for node_id, kind in node_type.items() if kind == "final")
    if not initial_ids:
        warnings.append({"code": "missing_initial_node", "node_ids": []})
    if not final_ids:
        warnings.append({"code": "missing_final_node", "node_ids": []})

    dead_ends = sorted(
        node_id
        for node_id, kind in node_type.items()
        if kind != "final" and not adjacency[node_id]
    )
    if dead_ends:
        warnings.append({"code": "non_final_dead_end", "node_ids": dead_ends})

    if initial_ids:
        reachable = set(initial_ids)
        stack = list(initial_ids)
        while stack:
            current = stack.pop()
            for target in adjacency[current] - reachable:
                reachable.add(target)
                stack.append(target)
        unreachable_actions = sorted(
            node_id
            for node_id, kind in node_type.items()
            if kind == "action" and node_id not in reachable
        )
        if unreachable_actions:
            warnings.append({"code": "unreachable_executable_node", "node_ids": unreachable_actions})

    if final_ids:
        can_reach_final = set(final_ids)
        stack = list(final_ids)
        while stack:
            current = stack.pop()
            for source in reverse[current] - can_reach_final:
                can_reach_final.add(source)
                stack.append(source)
        missing_final_reachability = sorted(
            node_id
            for node_id, kind in node_type.items()
            if kind != "final" and node_id not in can_reach_final
        )
        if missing_final_reachability:
            warnings.append(
                {"code": "missing_final_reachability", "node_ids": missing_final_reachability}
            )
    return warnings


def normalize_and_validate_activity_graph(
    graph: Any,
) -> Tuple[Dict[str, Any], TechnicalValidityReport]:
    """Apply one conservative representability pass without repairing behavior."""
    report = _new_report()
    if not isinstance(graph, dict):
        _fail(report, "ActivityGraph must be a JSON object")

    normalized = normalize_activity_graph(deepcopy(graph))
    if normalized != graph:
        report["normalizations"].extend(_alias_change_records(graph, normalized))

    nodes = normalized.get("nodes")
    edges = normalized.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        _fail(report, "ActivityGraph nodes and edges must be lists")
    if any(not isinstance(node, dict) for node in nodes):
        _fail(report, "ActivityGraph contains a non-object node")
    if any(not isinstance(edge, dict) for edge in edges):
        _fail(report, "ActivityGraph contains a non-object edge")

    edge_endpoint_ids = {
        str(edge.get(key) or "").strip()
        for edge in edges
        for key in ("source", "target")
        if str(edge.get(key) or "").strip()
    }
    known_ids: set[str] = set()
    for index, node in enumerate(nodes, start=1):
        legacy_id = str(node.get("node_id") or "").strip()
        raw_node_id = str(node.get("id") or "")
        node_id = raw_node_id.strip()
        if not node_id and legacy_id:
            node["id"] = legacy_id
            node_id = legacy_id
            report["normalizations"].append(
                {"kind": "node_id_alias", "node_index": index, "assigned_id": node_id}
            )
        node.pop("node_id", None)
        if not node_id:
            candidate = f"technical_node_{index}"
            while candidate in known_ids or candidate in edge_endpoint_ids:
                candidate = f"_{candidate}"
            node["id"] = candidate
            node_id = candidate
            report["normalizations"].append(
                {"kind": "assigned_isolated_node_id", "node_index": index, "assigned_id": node_id}
            )
        elif raw_node_id != node_id:
            node["id"] = node_id
            report["normalizations"].append(
                {"kind": "canonicalized_node_id", "node_index": index, "node_id": node_id}
            )
        if node_id in known_ids:
            _fail(report, f"duplicate node identity {node_id!r} is ambiguous")
        known_ids.add(node_id)

    deduplicated_edges: List[Dict[str, Any]] = []
    seen_edges: set[str] = set()
    for index, edge in enumerate(edges, start=1):
        for endpoint in ("source", "target"):
            raw_endpoint = str(edge.get(endpoint) or "")
            canonical_endpoint = raw_endpoint.strip()
            if canonical_endpoint and raw_endpoint != canonical_endpoint:
                edge[endpoint] = canonical_endpoint
                report["normalizations"].append(
                    {"kind": f"canonicalized_edge_{endpoint}", "edge_index": index}
                )
        signature = json.dumps(edge, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        if signature in seen_edges:
            report["normalizations"].append({"kind": "removed_exact_duplicate_edge", "edge_index": index})
            continue
        seen_edges.add(signature)
        source = str(edge.get("source") or "").strip()
        target = str(edge.get("target") or "").strip()
        if not source or not target:
            _fail(report, f"edge {index} has a missing source or target identity")
        source_known = source in known_ids
        target_known = target in known_ids
        if source_known != target_known:
            report["dropped_edges"].append(
                {"edge_index": index, "edge": deepcopy(edge), "reason": "one_sided_dangling_reference"}
            )
            report["normalizations"].append({"kind": "dropped_one_sided_dangling_edge", "edge_index": index})
            continue
        if not source_known and not target_known:
            _fail(report, f"edge {index} has two unknown endpoint identities")
        deduplicated_edges.append(edge)
    normalized["edges"] = deduplicated_edges

    try:
        validated = ActivityModel.model_validate(normalized).model_dump(exclude_none=True)
        json.dumps(validated, ensure_ascii=True, allow_nan=False)
    except (ValidationError, TypeError, ValueError) as exc:
        _fail(report, f"ActivityGraph is not technically representable: {exc}")

    report["normalization_applied"] = bool(report["normalizations"])
    report["quality_warnings"] = _quality_warnings(validated)
    report["technical_accepted"] = True
    return validated, report


__all__ = [
    "merge_technical_validity_reports",
    "TechnicalValidityError",
    "TechnicalValidityReport",
    "normalize_and_validate_activity_graph",
]
