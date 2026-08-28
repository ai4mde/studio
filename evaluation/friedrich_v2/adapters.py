from __future__ import annotations

from collections import Counter, defaultdict, deque
import json
from pathlib import Path
from typing import Any, Iterable, Mapping
import xml.etree.ElementTree as ET
import zipfile

from .core import EvalEdge, EvalGraph, EvalNode, normalize_label


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element: ET.Element, name: str) -> str | None:
    for child in element:
        if _local(child.tag) == name and child.text:
            return child.text.strip()
    return None


def _reference_xml(path: Path) -> bytes:
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            return archive.read("workflow/workflow.xml")
    return path.read_bytes()


def _project_edges(
    included: set[str], outgoing: Mapping[str, list[tuple[str, str | None]]]
) -> Iterable[EvalEdge]:
    for source in sorted(included):
        queue = deque(outgoing.get(source, []))
        visited: set[tuple[str, str | None]] = set()
        while queue:
            target, label = queue.popleft()
            if (target, label) in visited:
                continue
            visited.add((target, label))
            if target in included:
                yield EvalEdge(source, target, label)
            else:
                for next_target, next_label in outgoing.get(target, []):
                    queue.append((next_target, label or next_label))


def _gateway_type(family: str | None, incoming: int, outgoing: int) -> tuple[str | None, str | None]:
    if incoming > 1 and outgoing > 1:
        return "unsupported_control", "combined_gateway"
    if incoming <= 1 and outgoing <= 1:
        return None, None
    if family in {"ExclusiveDataBased", "ExclusiveEventBased", "ExclusiveGateway"}:
        return ("decision" if outgoing > 1 else "merge"), family
    if family in {"Parallel", "ParallelGateway"}:
        return ("fork" if outgoing > 1 else "join"), family
    return "unsupported_control", family or "unknown_gateway"


def _inubit(root: ET.Element) -> EvalGraph:
    modules = [element for element in root.iter() if _local(element.tag) == "WorkflowModule"]
    by_id = {node_id: module for module in modules if (node_id := _child_text(module, "ModuleId"))}
    outgoing: dict[str, list[tuple[str, str | None]]] = defaultdict(list)
    incoming_count: Counter[str] = Counter()
    outgoing_count: Counter[str] = Counter()
    for source, module in by_id.items():
        for connection in module:
            if _local(connection.tag) != "Connection" or connection.get("type") != "SequenceFlow":
                continue
            target = connection.get("moduleOutId")
            if target not in by_id:
                continue
            label = normalize_label(_child_text(connection, "ConnectionName"))
            outgoing[source].append((target, label))
            incoming_count[target] += 1
            outgoing_count[source] += 1
    nodes: list[EvalNode] = []
    for node_id, module in by_id.items():
        module_type = module.get("moduleType")
        node_type: str | None = None
        semantic_type: str | None = None
        if module_type == "Task":
            node_type = "action"
        elif module_type == "StartEvent":
            node_type = "initial"
        elif module_type == "StopEvent":
            node_type = "final"
        elif module_type == "Gateway":
            family = next(
                (prop.text.strip() for prop in module.iter() if _local(prop.tag) == "Property"
                 and prop.get("name") == "GatewayType" and prop.text), None,
            )
            node_type, semantic_type = _gateway_type(
                family, incoming_count[node_id], outgoing_count[node_id]
            )
        if node_type:
            nodes.append(EvalNode(node_id, node_type, normalize_label(_child_text(module, "ModuleName")), semantic_type))
    included = {node.id for node in nodes}
    return EvalGraph(tuple(nodes), tuple(_project_edges(included, outgoing)))


def _properties(element: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for prop in element.iter():
        name = prop.get("name")
        value = prop.get("value") if name else None
        if name and (value is not None or prop.text):
            result[name] = value if value is not None else prop.text.strip()
    return result


def _process_editor(root: ET.Element) -> EvalGraph:
    raw_nodes: dict[str, tuple[ET.Element, dict[str, str]]] = {}
    for element in root.iter():
        if _local(element.tag) != "node":
            continue
        props = _properties(element)
        node_id = props.get("#id") or element.get("id")
        if node_id:
            raw_nodes[node_id] = (element, props)
    raw_edges: list[tuple[str, str, str | None]] = []
    for element in root.iter():
        props = _properties(element)
        source = props.get("#sourceNode") or element.get("source")
        target = props.get("#targetNode") or element.get("target")
        if source in raw_nodes and target in raw_nodes:
            raw_edges.append((source, target, normalize_label(props.get("text"))))
    incoming, outgoing = Counter(t for _, t, _ in raw_edges), Counter(s for s, _, _ in raw_edges)
    nodes: list[EvalNode] = []
    for node_id, (_, props) in raw_nodes.items():
        class_name = props.get("#type", "").rsplit(".", 1)[-1]
        node_type: str | None = None
        semantic: str | None = None
        if class_name.endswith("Task"):
            node_type = "action"
        elif class_name in {"StartEvent", "StartNode"}:
            node_type = "initial"
        elif class_name in {"EndEvent", "StopEvent", "EndNode"}:
            node_type = "final"
        elif "Gateway" in class_name:
            node_type, semantic = _gateway_type(class_name, incoming[node_id], outgoing[node_id])
        if node_type:
            nodes.append(EvalNode(node_id, node_type, normalize_label(props.get("text")), semantic))
    included = {node.id for node in nodes}
    adjacency: dict[str, list[tuple[str, str | None]]] = defaultdict(list)
    for source, target, label in raw_edges:
        adjacency[source].append((target, label))
    return EvalGraph(tuple(nodes), tuple(_project_edges(included, adjacency)))


def friedrich_reference_to_eval_graph(path: str | Path) -> EvalGraph:
    path = Path(path)
    root = ET.fromstring(_reference_xml(path))
    if any(_local(element.tag) == "WorkflowModule" for element in root.iter()):
        return _inubit(root)
    return _process_editor(root)


def friedrich_reference_review_evidence(path: str | Path) -> tuple[dict[str, Any], ...]:
    """Extract ignored BPMN-specific evidence without promoting it to EvalGraph actions."""
    root = ET.fromstring(_reference_xml(Path(path)))
    evidence: list[dict[str, Any]] = []
    modules = [element for element in root.iter() if _local(element.tag) == "WorkflowModule"]
    names = {
        module_id: normalize_label(_child_text(module, "ModuleName"))
        for module in modules if (module_id := _child_text(module, "ModuleId"))
    }
    for module in modules:
        source = _child_text(module, "ModuleId")
        module_type = module.get("moduleType")
        if module_type in {"StartEvent", "StopEvent", "IntermediateEvent", "Pool", "Participant"}:
            evidence.append({
                "kind": normalize_label(module_type) or "event_or_participant",
                "id": source or "", "label": names.get(source or ""),
            })
        for connection in module:
            if _local(connection.tag) != "Connection" or connection.get("type") == "SequenceFlow":
                continue
            target = connection.get("moduleOutId") or ""
            evidence.append({
                "kind": normalize_label(connection.get("type")) or "ignored_connection",
                "label": normalize_label(_child_text(connection, "ConnectionName")),
                "source_id": source or "", "source_label": names.get(source or ""),
                "target_id": target, "target_label": names.get(target),
            })
    if not modules:
        for element in root.iter():
            props = _properties(element)
            class_name = props.get("#type", "").rsplit(".", 1)[-1]
            if any(token in class_name for token in ("Event", "Pool", "Participant", "MessageFlow")):
                evidence.append({
                    "kind": normalize_label(class_name) or "bpmn_specific",
                    "id": props.get("#id", ""), "label": normalize_label(props.get("text")),
                })
    return tuple(sorted(evidence, key=lambda item: tuple(str(item.get(key) or "") for key in sorted(item))))


def activity_graph_to_eval_graph(payload: Mapping[str, Any]) -> EvalGraph:
    if "activity_graph" in payload:
        nested = payload["activity_graph"]
        if not isinstance(nested, Mapping):
            raise ValueError("activity_graph must be an object")
        payload = nested
    raw_nodes, raw_edges = payload.get("nodes"), payload.get("edges")
    if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
        raise ValueError("ActivityGraph requires list-valued nodes and edges")
    nodes: list[EvalNode] = []
    for item in raw_nodes:
        if not isinstance(item, Mapping):
            raise ValueError("ActivityGraph nodes must be objects")
        node_type, node_id = item.get("type"), str(item.get("id") or "")
        if node_type not in {"initial", "action", "decision", "merge", "fork", "join", "final"}:
            raise ValueError(f"Unsupported generated node type: {node_type!r}")
        nodes.append(EvalNode(node_id, node_type, normalize_label(item.get("name") or item.get("label"))))
    known = {node.id for node in nodes}
    edges: list[EvalEdge] = []
    for item in raw_edges:
        if not isinstance(item, Mapping):
            raise ValueError("ActivityGraph edges must be objects")
        if item.get("type", "control") != "control":
            continue
        source, target = str(item.get("source") or ""), str(item.get("target") or "")
        if source not in known or target not in known:
            raise ValueError(f"Generated edge {source}->{target} references an unknown node")
        edges.append(EvalEdge(source, target, normalize_label(item.get("condition") or item.get("label"))))
    return EvalGraph(tuple(nodes), tuple(edges))


def load_generated_graph(path: str | Path) -> EvalGraph:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Generated model JSON must be an object")
    return activity_graph_to_eval_graph(payload)
