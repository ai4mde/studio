from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .activity_model import ActivityModel


TerminalRef = Tuple[str, Optional[str]]
BlockRefs = Dict[str, List[TerminalRef]]
_FINAL_EDGE_KIND = "_final_edge_kind"


class ActivitySketchTechnicalError(ValueError):
    """Raised when a sketch reference cannot be represented deterministically."""


class _GraphBuilder:
    def __init__(self) -> None:
        self._nodes: List[Dict[str, Any]] = []
        self._edges: List[Dict[str, Any]] = []
        self._next_node_index = 1
        self._seen_edges: set[tuple[str, str, str]] = set()

    def add_node(self, node_type: str, **attrs: Any) -> str:
        node_id = f"n{self._next_node_index}"
        self._next_node_index += 1
        node = {"id": node_id, "type": node_type}
        for key, value in attrs.items():
            if value is not None:
                node[key] = value
        self._nodes.append(node)
        return node_id

    def add_edge(
        self,
        source: str,
        target: str,
        *,
        label: Optional[str] = None,
        final_edge_kind: Optional[str] = None,
    ) -> None:
        normalized_label = str(label).strip() if label is not None else ""
        signature = (source, target, normalized_label)
        if signature in self._seen_edges:
            return
        self._seen_edges.add(signature)
        edge: Dict[str, Any] = {
            "source": source,
            "target": target,
            "type": "control",
        }
        if normalized_label:
            edge["label"] = normalized_label
        if final_edge_kind:
            edge[_FINAL_EDGE_KIND] = final_edge_kind
        self._edges.append(edge)

    def export(self) -> Dict[str, Any]:
        graph = {
            "nodes": self._nodes,
            "edges": self._edges,
        }
        return graph

    def build(self) -> Dict[str, Any]:
        graph = self.export()
        return _sanitize_graph(graph)


def _sanitize_graph(graph: Dict[str, Any]) -> Dict[str, Any]:
    sanitized_graph = {
        "nodes": [dict(node) for node in graph.get("nodes") or []],
        "edges": [],
    }
    for edge in graph.get("edges") or []:
        sanitized_edge = {
            key: value
            for key, value in dict(edge).items()
            if key != _FINAL_EDGE_KIND
        }
        sanitized_graph["edges"].append(sanitized_edge)
    return ActivityModel.model_validate(sanitized_graph).model_dump(exclude_none=True)


def _main_flow_step_name(entry: Any) -> str:
    if isinstance(entry, dict):
        return str(entry.get("action") or "").strip()
    return str(entry or "").strip()


def _main_flow_step_id(entry: Any, index: int) -> str:
    if isinstance(entry, dict):
        text = str(entry.get("step_id") or "").strip()
        if text:
            return text
    return f"S{index}"


def _branch_step_name(entry: Any) -> str:
    if isinstance(entry, dict):
        return str(entry.get("action") or "").strip()
    return str(entry or "").strip()


def _branch_step_id(entry: Any, fallback: str) -> Optional[str]:
    if isinstance(entry, dict):
        text = str(entry.get("step_id") or "").strip()
        if text:
            return text
    return fallback


def _capitalize_phrase(text: str) -> str:
    normalized = " ".join(text.split()).strip()
    if not normalized:
        return normalized
    return normalized[0].upper() + normalized[1:]


def _normalized_loop_decision_label(block: Dict[str, Any]) -> Optional[str]:
    note = str(block.get("notes") or "").strip()
    if not note:
        return None

    normalized_note = " ".join(note.split())
    lowered = normalized_note.lower()

    if "all requirements are satisfied" in lowered:
        return "All requirements satisfied?"

    success_match = re.search(
        r"\b(?:retry|repeat)\s+(.+?)\s+until it succeeds\b",
        lowered,
    )
    if success_match:
        subject = _capitalize_phrase(success_match.group(1))
        if subject:
            return f"{subject} successful?"

    passes_match = re.search(r"\buntil\s+(.+?)\s+passes\b", lowered)
    if passes_match:
        subject = _capitalize_phrase(passes_match.group(1))
        if subject:
            return f"{subject} passed?"

    return None


def _decision_label(block_id: str, block: Dict[str, Any]) -> str:
    note = str(block.get("notes") or "").strip()
    if str(block.get("type") or "").strip() == "loop":
        normalized = _normalized_loop_decision_label(block)
        if normalized:
            return normalized
    if note.endswith("?"):
        return note
    if note:
        return f"{note}?"
    return f"{block_id or 'decision'}?"


def _dedupe_edges(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[tuple[str, str, str, str]] = set()
    deduped: List[Dict[str, Any]] = []
    for edge in edges:
        signature = (
            str(edge.get("source") or ""),
            str(edge.get("target") or ""),
            str(edge.get("label") or ""),
            str(edge.get("condition") or ""),
        )
        if signature in seen:
            continue
        seen.add(signature)
        deduped.append(edge)
    return deduped


def _incoming_edges(edges: List[Dict[str, Any]], node_id: str) -> List[Dict[str, Any]]:
    return [edge for edge in edges if str(edge.get("target") or "") == node_id]


def _outgoing_edges(edges: List[Dict[str, Any]], node_id: str) -> List[Dict[str, Any]]:
    return [edge for edge in edges if str(edge.get("source") or "") == node_id]


def _canonicalize_merge_chains(graph: Dict[str, Any]) -> Dict[str, Any]:
    nodes = [dict(node) for node in graph.get("nodes") or []]
    edges = [dict(edge) for edge in graph.get("edges") or []]

    while True:
        node_by_id = {str(node.get("id")): node for node in nodes}
        changed = False

        for node in list(nodes):
            node_id = str(node.get("id") or "")
            if str(node.get("type") or "") != "merge":
                continue

            outgoing = _outgoing_edges(edges, node_id)
            if len(outgoing) != 1:
                continue
            bridge_edge = outgoing[0]
            if str(bridge_edge.get("label") or "").strip() or str(bridge_edge.get("condition") or "").strip():
                continue

            downstream_id = str(bridge_edge.get("target") or "")
            downstream = node_by_id.get(downstream_id)
            if downstream is None or str(downstream.get("type") or "") != "merge":
                continue

            incoming = _incoming_edges(edges, node_id)
            if not incoming:
                continue

            redirected: List[Dict[str, Any]] = []
            for edge in incoming:
                redirected_edge = dict(edge)
                redirected_edge["target"] = downstream_id
                redirected.append(redirected_edge)

            edges = [
                edge
                for edge in edges
                if str(edge.get("source") or "") != node_id and str(edge.get("target") or "") != node_id
            ]
            edges.extend(redirected)
            edges = _dedupe_edges(edges)
            nodes = [candidate for candidate in nodes if str(candidate.get("id") or "") != node_id]
            changed = True
            break

        if changed:
            continue

        if not changed:
            break

    canonical_graph = {
        "nodes": nodes,
        "edges": edges,
    }
    return _sanitize_graph(canonical_graph)


def compile_activity_sketch(sketch: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not sketch:
        builder = _GraphBuilder()
        initial_id = builder.add_node("initial")
        final_id = builder.add_node("final")
        builder.add_edge(initial_id, final_id)
        return builder.build()

    builder = _GraphBuilder()
    main_flow = sketch.get("main_flow") or []
    control_blocks = sketch.get("control_blocks") or []

    block_by_id: Dict[str, Dict[str, Any]] = {}
    block_sequence: List[str] = []
    for index, block in enumerate(control_blocks, start=1):
        block_id = str(block.get("block_id") or f"B{index}").strip()
        normalized = dict(block)
        normalized["block_id"] = block_id
        block_by_id[block_id] = normalized
        block_sequence.append(block_id)

    main_step_names: Dict[str, str] = {}
    main_step_nodes: Dict[str, str] = {}
    for index, entry in enumerate(main_flow, start=1):
        step_id = _main_flow_step_id(entry, index)
        action_name = _main_flow_step_name(entry) or step_id
        main_step_names[step_id] = action_name
        main_step_nodes[step_id] = builder.add_node(
            "action",
            name=action_name,
            origin_step_id=step_id,
        )

    branch_step_nodes: Dict[str, str] = {}
    referenced_block_ids: set[str] = set()
    for block in control_blocks:
        for branch in block.get("branches") or []:
            next_block_id = str(branch.get("next_block_id") or "").strip()
            if next_block_id:
                referenced_block_ids.add(next_block_id)
            for child_block_id in branch.get("child_block_ids") or []:
                child_id = str(child_block_id).strip()
                if child_id:
                    referenced_block_ids.add(child_id)

    root_block_ids = [block_id for block_id in block_sequence if block_id not in referenced_block_ids]
    compiled_blocks: set[str] = set()
    active_stack: set[str] = set()
    entry_attach_nodes_by_block: Dict[str, str] = {}
    terminal_refs_by_block: Dict[str, BlockRefs] = {}

    def empty_block_refs() -> BlockRefs:
        return {"continuation": [], "terminal": []}

    def connect_refs(refs: Iterable[TerminalRef], target_id: str) -> None:
        for source_id, label in refs:
            builder.add_edge(source_id, target_id, label=label)

    def distinct_refs(refs: Iterable[TerminalRef]) -> List[TerminalRef]:
        seen: set[TerminalRef] = set()
        distinct: List[TerminalRef] = []
        for source_id, label in refs:
            normalized_ref = (source_id, label)
            if normalized_ref in seen:
                continue
            seen.add(normalized_ref)
            distinct.append(normalized_ref)
        return distinct

    def connect_refs_to_final(refs: Iterable[TerminalRef], kind: str, final_id: str) -> None:
        for source_id, label in refs:
            builder.add_edge(source_id, final_id, label=label, final_edge_kind=kind)

    def ensure_branch_step_node(step: Any, fallback_key: str) -> str:
        step_id = _branch_step_id(step, fallback_key)
        action_name = _branch_step_name(step) or (step_id or fallback_key)
        if step_id and step_id in main_step_nodes:
            return main_step_nodes[step_id]
        if step_id and step_id in branch_step_nodes:
            return branch_step_nodes[step_id]
        node_id = builder.add_node(
            "action",
            name=action_name,
            origin_step_id=step_id,
        )
        if step_id:
            branch_step_nodes[step_id] = node_id
        return node_id

    def ensure_local_anchor(
        block: Dict[str, Any],
        incoming_refs: List[TerminalRef],
        reference_kind: str,
    ) -> tuple[List[TerminalRef], Optional[str]]:
        if reference_kind != "child":
            return incoming_refs, None
        step_id = str(block.get("entry_after_step_id") or "").strip()
        if not step_id:
            return incoming_refs, None
        action_name = str(block.get("entry_after") or main_step_names.get(step_id) or step_id).strip()
        local_anchor_id = builder.add_node(
            "action",
            name=action_name,
            origin_step_id=step_id,
        )
        connect_refs(incoming_refs, local_anchor_id)
        return [(local_anchor_id, None)], local_anchor_id

    def step_lookup_node(step_id: Optional[str], step_name: Optional[str]) -> Optional[str]:
        normalized_step_id = str(step_id or "").strip()
        if normalized_step_id:
            if normalized_step_id in branch_step_nodes:
                return branch_step_nodes[normalized_step_id]
            if normalized_step_id in main_step_nodes:
                return main_step_nodes[normalized_step_id]
        normalized_name = str(step_name or "").strip().lower()
        if normalized_name:
            for node in builder._nodes:
                if str(node.get("type")) != "action":
                    continue
                if str(node.get("name") or "").strip().lower() == normalized_name:
                    return str(node.get("id"))
        return None

    def realize_block(
        block_id: str,
        incoming_refs: List[TerminalRef],
        *,
        reference_kind: str,
    ) -> BlockRefs:
        if block_id in compiled_blocks:
            attach_node_id = entry_attach_nodes_by_block.get(block_id)
            if attach_node_id is not None:
                connect_refs(incoming_refs, attach_node_id)
            return terminal_refs_by_block.get(
                block_id,
                {"continuation": incoming_refs, "terminal": []},
            )
        if block_id in active_stack or block_id not in block_by_id:
            return {"continuation": incoming_refs, "terminal": []}

        block = block_by_id[block_id]
        active_stack.add(block_id)
        working_refs, local_anchor_id = ensure_local_anchor(block, incoming_refs, reference_kind)
        block_type = str(block.get("type") or "")
        if block_type == "parallel":
            entry_node_id = builder.add_node("fork", origin_block_id=block_id)
        else:
            entry_node_id = builder.add_node(
                "decision",
                label=_decision_label(block_id, block),
                origin_block_id=block_id,
            )
        connect_refs(working_refs, entry_node_id)
        entry_attach_nodes_by_block[block_id] = local_anchor_id or entry_node_id

        branch_outputs: List[List[TerminalRef]] = []
        terminal_branch_outputs: List[List[TerminalRef]] = []
        reconnect_outputs: Dict[str, List[TerminalRef]] = {}
        for branch_index, branch in enumerate(block.get("branches") or [], start=1):
            branch_label = None if block_type == "parallel" else (str(branch.get("label") or "").strip() or None)
            refs: List[TerminalRef] = [(entry_node_id, branch_label)]
            branch_terminal_refs: List[TerminalRef] = []

            steps = branch.get("steps") or []
            for step_index, step in enumerate(steps, start=1):
                fallback_key = f"{block_id}_branch_{branch_index}_step_{step_index}"
                step_node_id = ensure_branch_step_node(step, fallback_key)
                connect_refs(refs, step_node_id)
                refs = [(step_node_id, None)]

            next_block_id = str(branch.get("next_block_id") or "").strip()
            if next_block_id:
                next_block_refs = realize_block(next_block_id, refs, reference_kind="next")
                refs = next_block_refs["continuation"]
                branch_terminal_refs.extend(next_block_refs["terminal"])

            child_block_ids = [
                str(child_block_id).strip()
                for child_block_id in branch.get("child_block_ids") or []
                if str(child_block_id).strip()
            ]
            for child_offset, child_block_id in enumerate(child_block_ids, start=1):
                normalized_child_id = str(child_block_id).strip()
                if not normalized_child_id:
                    continue
                child_block_refs = realize_block(normalized_child_id, refs, reference_kind="child")
                refs = child_block_refs["continuation"]
                branch_terminal_refs.extend(child_block_refs["terminal"])

            reconnect_step_id = str(branch.get("reconnect_to_step_id") or "").strip()
            if reconnect_step_id:
                reconnect_target_id = step_lookup_node(reconnect_step_id, None)
                if reconnect_target_id is not None:
                    if block_type == "decision":
                        reconnect_outputs.setdefault(reconnect_target_id, []).extend(refs)
                    else:
                        connect_refs(refs, reconnect_target_id)
                    terminal_branch_outputs.append(branch_terminal_refs)
                    continue

            has_explicit_continuation = bool(next_block_id or child_block_ids)
            if (
                block_type == "loop"
                and not bool(branch.get("returns_to_main_flow", True))
                and not has_explicit_continuation
            ):
                loop_step_id = str(block.get("loop_back_to_step_id") or "").strip()
                loop_block_id = str(block.get("loop_back_to_block_id") or "").strip()
                legacy_loop_text = str(block.get("loop_back_to") or "").strip()
                loop_target_id = step_lookup_node(loop_step_id, None) if loop_step_id else None
                if loop_target_id is None and loop_block_id == block_id:
                    loop_target_id = entry_node_id
                has_explicit_target = bool(loop_step_id or loop_block_id or legacy_loop_text)
                if has_explicit_target and loop_target_id is None:
                    raise ActivitySketchTechnicalError(
                        f"loop block {block_id!r} has unresolved loop-back target "
                        f"step_id={loop_step_id!r}, block_id={loop_block_id!r}"
                    )
                if loop_target_id is not None:
                    connect_refs(refs, loop_target_id)
                terminal_branch_outputs.append(branch_terminal_refs)
                continue

            if not bool(branch.get("returns_to_main_flow", True)) and not has_explicit_continuation:
                terminal_branch_outputs.append(branch_terminal_refs + refs)
                continue

            if refs:
                branch_outputs.append(refs)
            terminal_branch_outputs.append(branch_terminal_refs)

        requires_merge = bool(block.get("requires_merge", False))
        has_shared_nonterminal_continuation = bool(
            str(block.get("exit_to_step_id") or block.get("exit_to") or "").strip()
        )
        realized_branch_outputs = [refs for refs in branch_outputs if refs]
        effective_continuation_refs = distinct_refs(
            ref
            for refs in realized_branch_outputs
            for ref in refs
        )
        if (
            block_type == "decision"
            and requires_merge
            and has_shared_nonterminal_continuation
            and len(effective_continuation_refs) >= 2
        ):
            merge_id = builder.add_node("merge", origin_block_id=block_id)
            connect_refs(effective_continuation_refs, merge_id)
            continuation_refs = [(merge_id, None)]
        elif block_type == "parallel" and requires_merge and realized_branch_outputs:
            join_id = builder.add_node("join", origin_block_id=block_id)
            for refs in realized_branch_outputs:
                connect_refs(refs, join_id)
            continuation_refs = [(join_id, None)]
        else:
            continuation_refs = effective_continuation_refs

        for reconnect_target_id, reconnect_refs in reconnect_outputs.items():
            effective_reconnect_refs = distinct_refs(reconnect_refs)
            if requires_merge and len(effective_reconnect_refs) >= 2:
                merge_id = builder.add_node("merge", origin_block_id=block_id)
                connect_refs(effective_reconnect_refs, merge_id)
                builder.add_edge(merge_id, reconnect_target_id)
            else:
                connect_refs(effective_reconnect_refs, reconnect_target_id)

        block_refs = {
            "continuation": continuation_refs,
            "terminal": [ref for refs in terminal_branch_outputs for ref in refs],
        }
        terminal_refs_by_block[block_id] = block_refs
        compiled_blocks.add(block_id)
        active_stack.remove(block_id)
        return block_refs

    initial_id = builder.add_node("initial")
    final_id = builder.add_node("final")

    if not main_flow and not root_block_ids:
        builder.add_edge(initial_id, final_id)
        return builder.build()

    ordered_step_ids = list(main_step_nodes.keys())
    step_index_by_node = {
        node_id: index
        for index, step_id in enumerate(ordered_step_ids)
        for node_id in [main_step_nodes[step_id]]
    }
    next_step_index = 0
    root_refs: List[TerminalRef] = [(initial_id, None)]

    def connect_main_steps_through(end_index: int) -> None:
        nonlocal next_step_index, root_refs
        for index in range(next_step_index, end_index + 1):
            step_node_id = main_step_nodes[ordered_step_ids[index]]
            connect_refs(root_refs, step_node_id)
            root_refs = [(step_node_id, None)]
        next_step_index = max(next_step_index, end_index + 1)

    for block_id in root_block_ids:
        block = block_by_id[block_id]
        entry_step_id = str(block.get("entry_after_step_id") or "").strip()
        entry_target_id = step_lookup_node(entry_step_id, block.get("entry_after"))
        entry_step_index = step_index_by_node.get(entry_target_id or "")
        if entry_step_index is not None and entry_step_index >= next_step_index:
            connect_main_steps_through(entry_step_index)

        block_refs = realize_block(block_id, root_refs, reference_kind="root")
        root_refs = block_refs["continuation"]
        if block_refs["terminal"]:
            connect_refs_to_final(block_refs["terminal"], "terminal", final_id)

    if next_step_index < len(ordered_step_ids):
        connect_main_steps_through(len(ordered_step_ids) - 1)
    if root_refs:
        connect_refs_to_final(root_refs, "continuation", final_id)

    return _canonicalize_merge_chains(builder.export())


__all__ = ["ActivitySketchTechnicalError", "compile_activity_sketch"]
