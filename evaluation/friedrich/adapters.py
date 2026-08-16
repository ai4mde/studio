from __future__ import annotations

from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping
import xml.etree.ElementTree as ET
import zipfile

from .eval_graph import EvalEdge, EvalGraph, EvalNode, normalize_label


class UnsupportedReferenceElement(ValueError):
    """Raised when a BPMN construct cannot be represented without semantic loss."""


def _child_text(element: ET.Element, tag: str) -> str | None:
    child = element.find(tag)
    return child.text.strip() if child is not None and child.text else None


def _gateway_family(module: ET.Element) -> str | None:
    for prop in module.findall(".//Property"):
        if prop.get("name") == "GatewayType":
            return prop.text.strip() if prop.text else None
    return None


def _reference_xml(path: str | Path) -> bytes:
    reference_path = Path(path)
    if reference_path.suffix == ".zip":
        with zipfile.ZipFile(reference_path) as archive:
            return archive.read("workflow/workflow.xml")
    return reference_path.read_bytes()


def _classify_gateway(
    gateway_id: str,
    family: str | None,
    incoming: int,
    outgoing: int,
) -> str | None:
    if incoming > 1 and outgoing > 1:
        raise UnsupportedReferenceElement(
            f"Gateway {gateway_id} is both converging and diverging; it requires "
            "an explicit two-node expansion policy"
        )
    if incoming <= 1 and outgoing <= 1:
        return None

    if family in {"ExclusiveDataBased", "ExclusiveEventBased"}:
        return "decision" if outgoing > 1 else "merge"
    if family == "Parallel":
        return "fork" if outgoing > 1 else "join"
    raise UnsupportedReferenceElement(
        f"Gateway {gateway_id} has unsupported family {family!r}; inclusive and "
        "complex gateways have no equivalent in the initial EvalGraph vocabulary"
    )


def _project_edges(
    included_ids: set[str],
    outgoing_edges: Mapping[str, list[tuple[str, str | None]]],
) -> Iterable[EvalEdge]:
    """Contract non-evaluated nodes while preserving sequence-flow reachability."""
    for source in sorted(included_ids):
        queue = deque(outgoing_edges.get(source, []))
        visited: set[tuple[str, str | None]] = set()
        while queue:
            target, label = queue.popleft()
            state = (target, label)
            if state in visited:
                continue
            visited.add(state)
            if target in included_ids:
                yield EvalEdge(source=source, target=target, label=label)
                continue
            for next_target, next_label in outgoing_edges.get(target, []):
                queue.append((next_target, label or next_label))


def friedrich_reference_to_eval_graph(path: str | Path) -> EvalGraph:
    """Convert a Friedrich inubit workflow reference into an EvalGraph."""
    root = ET.fromstring(_reference_xml(path))
    modules = root.findall(".//WorkflowModule")
    by_id = {
        module_id: module
        for module in modules
        if (module_id := _child_text(module, "ModuleId")) is not None
    }

    outgoing_edges: dict[str, list[tuple[str, str | None]]] = defaultdict(list)
    incoming_counts: Counter[str] = Counter()
    outgoing_counts: Counter[str] = Counter()
    for source_id, module in by_id.items():
        for connection in module.findall("Connection"):
            if connection.get("type") != "SequenceFlow":
                continue
            target_id = connection.get("moduleOutId")
            if not target_id or target_id not in by_id:
                continue
            label = normalize_label(_child_text(connection, "ConnectionName"))
            outgoing_edges[source_id].append((target_id, label))
            incoming_counts[target_id] += 1
            outgoing_counts[source_id] += 1

    nodes: list[EvalNode] = []
    for node_id, module in by_id.items():
        module_type = module.get("moduleType")
        eval_type: str | None = None
        if module_type == "Task":
            eval_type = "action"
        elif module_type == "StartEvent":
            eval_type = "initial"
        elif module_type == "StopEvent":
            eval_type = "final"
        elif module_type == "Gateway":
            eval_type = _classify_gateway(
                node_id,
                _gateway_family(module),
                incoming_counts[node_id],
                outgoing_counts[node_id],
            )

        if eval_type is not None:
            nodes.append(
                EvalNode(
                    id=node_id,
                    type=eval_type,  # type: ignore[arg-type]
                    label=normalize_label(_child_text(module, "ModuleName")),
                )
            )

    included_ids = {node.id for node in nodes}
    edges = tuple(_project_edges(included_ids, outgoing_edges))
    return EvalGraph(nodes=tuple(nodes), edges=edges)


def activity_graph_to_eval_graph(payload: Mapping[str, Any]) -> EvalGraph:
    """Convert a validated-style ActivityGraph mapping without importing production code."""
    nodes: list[EvalNode] = []
    included_ids: set[str] = set()
    allowed_types = {"initial", "action", "decision", "merge", "fork", "join", "final"}

    raw_nodes = payload.get("nodes")
    raw_edges = payload.get("edges")
    if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
        raise ValueError("ActivityGraph must contain list-valued nodes and edges")

    for raw_node in raw_nodes:
        if not isinstance(raw_node, Mapping):
            raise ValueError("Each ActivityGraph node must be an object")
        node_type = raw_node.get("type")
        if node_type not in allowed_types:
            continue
        node_id = str(raw_node.get("id") or "")
        label_source = (
            raw_node.get("name") or raw_node.get("label")
            if node_type == "action"
            else raw_node.get("label") or raw_node.get("name")
        )
        nodes.append(
            EvalNode(
                id=node_id,
                type=node_type,
                label=normalize_label(label_source),
            )
        )
        included_ids.add(node_id)

    edges: list[EvalEdge] = []
    for raw_edge in raw_edges:
        if not isinstance(raw_edge, Mapping) or raw_edge.get("type", "control") != "control":
            continue
        source = str(raw_edge.get("source") or "")
        target = str(raw_edge.get("target") or "")
        if source not in included_ids or target not in included_ids:
            continue
        edges.append(
            EvalEdge(
                source=source,
                target=target,
                label=normalize_label(raw_edge.get("label") or raw_edge.get("condition")),
            )
        )

    return EvalGraph(nodes=tuple(nodes), edges=tuple(edges))
