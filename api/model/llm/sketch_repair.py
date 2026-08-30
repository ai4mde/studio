from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


SketchRepairReport = Dict[str, Any]

_REWORK_TERMS = (
    "retry",
    "rework",
    "correct",
    "fix",
    "update",
    "missing",
    "document",
    "documents",
    "error",
    "errors",
    "additional",
)
_APPROVAL_TERMS = (
    "approve",
    "approved",
    "approval",
    "reject",
    "rejected",
    "rejection",
    "accept",
    "accepted",
    "decline",
    "declined",
)


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _step_text_to_id(entries: Iterable[Any]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        step_id = str(entry.get("step_id") or "").strip()
        action = _normalize_text(entry.get("action"))
        if step_id and action:
            lookup[action] = step_id
    return lookup


def _step_id_to_text(entries: Iterable[Any]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        step_id = str(entry.get("step_id") or "").strip()
        action = str(entry.get("action") or "").strip()
        if step_id and action:
            lookup[step_id] = action
    return lookup


def _all_step_text_to_id(sketch: Dict[str, Any]) -> Dict[str, str]:
    candidates: Dict[str, Set[str]] = {}

    def add(step: Any) -> None:
        if not isinstance(step, dict):
            return
        step_id = str(step.get("step_id") or "").strip()
        action = _normalize_text(step.get("action"))
        if step_id and action:
            candidates.setdefault(action, set()).add(step_id)

    for step in sketch.get("main_flow") or []:
        add(step)
    for control_block in sketch.get("control_blocks") or []:
        if not isinstance(control_block, dict):
            continue
        for branch in control_block.get("branches") or []:
            if not isinstance(branch, dict):
                continue
            for step in branch.get("steps") or []:
                add(step)
    return {
        action: next(iter(step_ids))
        for action, step_ids in candidates.items()
        if len(step_ids) == 1
    }


def _main_flow_step_ids(main_flow: List[Any]) -> List[str]:
    step_ids: List[str] = []
    for entry in main_flow:
        if not isinstance(entry, dict):
            continue
        step_id = str(entry.get("step_id") or "").strip()
        if step_id:
            step_ids.append(step_id)
    return step_ids


def _all_step_ids(sketch: Dict[str, Any]) -> Set[str]:
    step_ids: Set[str] = set()
    for entry in sketch.get("main_flow") or []:
        if isinstance(entry, dict):
            step_id = str(entry.get("step_id") or "").strip()
            if step_id:
                step_ids.add(step_id)
    for block in sketch.get("control_blocks") or []:
        if not isinstance(block, dict):
            continue
        for branch in block.get("branches") or []:
            if not isinstance(branch, dict):
                continue
            for step in branch.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                step_id = str(step.get("step_id") or "").strip()
                if step_id:
                    step_ids.add(step_id)
    return step_ids


def _block_ids(sketch: Dict[str, Any]) -> Set[str]:
    ids: Set[str] = set()
    for block in sketch.get("control_blocks") or []:
        if not isinstance(block, dict):
            continue
        block_id = str(block.get("block_id") or "").strip()
        if block_id:
            ids.add(block_id)
    return ids


def _structural_reference_texts(sketch: Dict[str, Any]) -> Set[str]:
    references: Set[str] = set()
    for block in sketch.get("control_blocks") or []:
        if not isinstance(block, dict):
            continue
        block_id = str(block.get("block_id") or "").strip()
        purpose = _normalize_text(block.get("notes"))
        if purpose:
            references.add(purpose)
        for branch in block.get("branches") or []:
            if not isinstance(branch, dict):
                continue
            branch_label = str(branch.get("label") or "").strip()
            if block_id and branch_label:
                references.add(_normalize_text(f"scope_{block_id}_{branch_label}"))
            for step in branch.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                action = _normalize_text(step.get("action"))
                if action:
                    references.add(action)
    return references


def _coerce_reference_to_valid_step_id(
    block: Dict[str, Any],
    *,
    text_key: str,
    step_id_key: str,
    valid_step_ids: Set[str],
    text_lookup: Dict[str, str],
    valid_text_references: Set[str],
) -> bool:
    step_id = str(block.get(step_id_key) or "").strip()
    if step_id and step_id in valid_step_ids:
        return True

    text_value = _normalize_text(block.get(text_key))
    mapped_step_id = text_lookup.get(text_value)
    if mapped_step_id and mapped_step_id in valid_step_ids:
        block[step_id_key] = mapped_step_id
        return True

    if text_value and text_value in valid_text_references:
        block.pop(step_id_key, None)
        return True

    block.pop(step_id_key, None)
    if step_id or text_value:
        block.pop(text_key, None)
    return False


def _classify_branch_label(label: Any) -> str:
    normalized = _normalize_text(label)
    if any(term in normalized for term in _REWORK_TERMS):
        return "rework"
    if any(term in normalized for term in _APPROVAL_TERMS):
        return "approval"
    return "other"


def repair_activity_sketch(sketch: Optional[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], SketchRepairReport]:
    if not sketch:
        return sketch, {
            "metrics": {
                "invalid_reference_count": 0,
                "reconnect_repair_count": 0,
                "merge_normalization_count": 0,
                "dead_end_repair_count": 0,
                "child_block_repair_count": 0,
                "planner_retry_triggered": False,
            },
            "critical_defects": [],
            "repairs": [],
            "used_retry": False,
        }

    repaired = deepcopy(sketch)
    main_flow = repaired.get("main_flow") or []
    main_flow_step_ids = _main_flow_step_ids(main_flow)
    main_flow_step_id_set = set(main_flow_step_ids)
    all_step_ids = _all_step_ids(repaired)
    step_text_lookup = _step_text_to_id(main_flow)
    all_step_text_lookup = _all_step_text_to_id(repaired)
    step_id_text_lookup = _step_id_to_text(main_flow)
    valid_block_ids = _block_ids(repaired)
    structural_reference_texts = _structural_reference_texts(repaired)

    invalid_reference_count = 0
    reconnect_repair_count = 0
    merge_normalization_count = 0
    dead_end_repair_count = 0
    child_block_repair_count = 0
    repairs: List[str] = []
    critical_defects: List[str] = []

    def next_main_flow_step(step_id: Optional[str]) -> Optional[str]:
        if not step_id:
            return None
        try:
            index = main_flow_step_ids.index(step_id)
        except ValueError:
            return None
        if index + 1 < len(main_flow_step_ids):
            return main_flow_step_ids[index + 1]
        return None

    for block in repaired.get("control_blocks") or []:
        if not isinstance(block, dict):
            continue

        block_id = str(block.get("block_id") or "").strip()

        had_entry_reference = "entry_after_step_id" in block or "entry_after" in block
        if not _coerce_reference_to_valid_step_id(
            block,
            text_key="entry_after",
            step_id_key="entry_after_step_id",
            valid_step_ids=main_flow_step_id_set,
            text_lookup=step_text_lookup,
            valid_text_references=structural_reference_texts,
        ):
            if had_entry_reference:
                invalid_reference_count += 1
                repairs.append(f"{block_id or 'block'}:removed_invalid_entry_after")
            critical_defects.append(f"{block_id or 'block'}:missing_entry_after")

        had_exit_reference = "exit_to_step_id" in block or "exit_to" in block
        if not _coerce_reference_to_valid_step_id(
            block,
            text_key="exit_to",
            step_id_key="exit_to_step_id",
            valid_step_ids=main_flow_step_id_set,
            text_lookup=step_text_lookup,
            valid_text_references=structural_reference_texts,
        ):
            if had_exit_reference:
                invalid_reference_count += 1
                reconnect_repair_count += 1
                repairs.append(f"{block_id or 'block'}:removed_invalid_exit_to")
            replacement_step_id = next_main_flow_step(str(block.get("entry_after_step_id") or "").strip())
            if replacement_step_id:
                block["exit_to_step_id"] = replacement_step_id
                block["exit_to"] = step_id_text_lookup.get(replacement_step_id, replacement_step_id)
                reconnect_repair_count += 1
                repairs.append(f"{block_id or 'block'}:normalized_exit_to_to_next_main_flow")

        loop_step_id = str(block.get("loop_back_to_step_id") or "").strip()
        loop_block_id = str(block.get("loop_back_to_block_id") or "").strip()
        loop_text = _normalize_text(block.get("loop_back_to"))
        if not loop_step_id and not loop_block_id and loop_text:
            mapped_loop_step_id = all_step_text_lookup.get(loop_text)
            if mapped_loop_step_id:
                block["loop_back_to_step_id"] = mapped_loop_step_id
                loop_step_id = mapped_loop_step_id
                repairs.append(f"{block_id or 'block'}:normalized_loop_back_to_step_id")

        unresolved_loop_target = False
        if loop_step_id:
            unresolved_loop_target = loop_step_id not in all_step_ids
            if not unresolved_loop_target:
                block.pop("loop_back_to_block_id", None)
        elif loop_block_id:
            unresolved_loop_target = loop_block_id not in valid_block_ids or loop_block_id != block_id
            if not unresolved_loop_target:
                block.pop("loop_back_to", None)
                block.pop("loop_back_to_step_id", None)
        elif loop_text:
            unresolved_loop_target = True

        if unresolved_loop_target:
            invalid_reference_count += 1
            repairs.append(f"{block_id or 'block'}:unresolved_loop_back")
            critical_defects.append(f"{block_id or 'block'}:unresolved_loop_back")

        if str(block.get("type") or "") == "loop" and bool(block.get("requires_merge")):
            block["requires_merge"] = False
            merge_normalization_count += 1
            repairs.append(f"{block_id or 'block'}:loop_requires_merge_false")

        branch_categories: Set[str] = set()
        branch_next_block_ids: List[str] = []
        for branch in block.get("branches") or []:
            if not isinstance(branch, dict):
                continue
            category = _classify_branch_label(branch.get("label"))
            if category != "other":
                branch_categories.add(category)

            next_block_id = str(branch.get("next_block_id") or "").strip()
            if next_block_id:
                if next_block_id in valid_block_ids:
                    branch_next_block_ids.append(next_block_id)
                else:
                    invalid_reference_count += 1
                    branch.pop("next_block_id", None)
                    repairs.append(f"{block_id or 'block'}:removed_invalid_next_block")

            child_block_ids: List[str] = []
            for child_block_id in branch.get("child_block_ids") or []:
                normalized_child_block_id = str(child_block_id).strip()
                if not normalized_child_block_id:
                    continue
                if normalized_child_block_id in valid_block_ids:
                    child_block_ids.append(normalized_child_block_id)
                else:
                    invalid_reference_count += 1
                    child_block_repair_count += 1
                    repairs.append(f"{block_id or 'block'}:removed_invalid_child_block")
            branch["child_block_ids"] = child_block_ids

            reconnect_step_id = str(branch.get("reconnect_to_step_id") or "").strip()
            if reconnect_step_id:
                if reconnect_step_id not in all_step_ids:
                    invalid_reference_count += 1
                    reconnect_repair_count += 1
                    branch.pop("reconnect_to_step_id", None)
                    repairs.append(f"{block_id or 'block'}:removed_invalid_reconnect_to_step")

            # Continuation is semantic intent, not proof of a direct local target.
            # Invalid references can be removed without converting that intent to termination.

        if "rework" in branch_categories and "approval" in branch_categories:
            critical_defects.append(f"{block_id or 'block'}:mixed_decision_semantics")

        if branch_next_block_ids and bool(block.get("requires_merge")):
            if all(
                not bool(branch.get("returns_to_main_flow"))
                for branch in block.get("branches") or []
                if isinstance(branch, dict)
            ):
                block["requires_merge"] = False
                merge_normalization_count += 1
                repairs.append(f"{block_id or 'block'}:disabled_conflicting_merge")

        if branch_next_block_ids and str(block.get("exit_to_step_id") or "").strip():
            if all(
                str(branch.get("next_block_id") or "").strip()
                for branch in block.get("branches") or []
                if isinstance(branch, dict)
            ):
                block.pop("exit_to_step_id", None)
                block.pop("exit_to", None)
                reconnect_repair_count += 1
                repairs.append(f"{block_id or 'block'}:removed_conflicting_exit_to")

    report: SketchRepairReport = {
        "metrics": {
            "invalid_reference_count": invalid_reference_count,
            "reconnect_repair_count": reconnect_repair_count,
            "merge_normalization_count": merge_normalization_count,
            "dead_end_repair_count": dead_end_repair_count,
            "child_block_repair_count": child_block_repair_count,
            "planner_retry_triggered": False,
        },
        "critical_defects": list(dict.fromkeys(critical_defects)),
        "repairs": repairs,
        "used_retry": False,
    }
    return repaired, report


def sketch_requires_retry(report: Optional[SketchRepairReport]) -> bool:
    if not report:
        return False
    metrics = report.get("metrics") or {}
    if report.get("critical_defects"):
        return True
    return bool(metrics.get("invalid_reference_count", 0) > 0 and metrics.get("reconnect_repair_count", 0) > 0)


__all__ = ["SketchRepairReport", "repair_activity_sketch", "sketch_requires_retry"]
