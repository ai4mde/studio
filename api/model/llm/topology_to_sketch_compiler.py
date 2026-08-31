from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .activity_sketch_model import ActivitySketch
from .semantic_sketch_plan_model import SemanticSketchPlan
from .topology_artifact_model import TopologyArtifact, TopologyStructure


class SemanticPlanTopologyValidationError(ValueError):
    """Raised when a semantic plan does not satisfy a topology contract."""


def _normalize_artifact(topology_artifact: Dict[str, Any] | TopologyArtifact) -> TopologyArtifact:
    if isinstance(topology_artifact, TopologyArtifact):
        return topology_artifact
    return TopologyArtifact.model_validate(topology_artifact)


def _preorder_structures(artifact: TopologyArtifact) -> List[TopologyStructure]:
    by_id = {structure.id: structure for structure in artifact.structures}
    children_by_parent: Dict[str, List[TopologyStructure]] = defaultdict(list)
    for structure in artifact.structures:
        children_by_parent[structure.parent].append(structure)

    ordered: List[TopologyStructure] = []
    seen: set[str] = set()

    def visit(structure: TopologyStructure) -> None:
        if structure.id in seen:
            return
        seen.add(structure.id)
        ordered.append(structure)
        for child in children_by_parent.get(structure.id, []):
            visit(child)

    for root in children_by_parent.get("ROOT", []):
        visit(root)
    for structure in artifact.structures:
        visit(structure)
    return ordered


def _branch_children(structures: Iterable[TopologyStructure]) -> Dict[Tuple[str, str], List[TopologyStructure]]:
    mapping: Dict[Tuple[str, str], List[TopologyStructure]] = defaultdict(list)
    for structure in structures:
        if structure.parent == "ROOT" or structure.parent_branch is None:
            continue
        mapping[(structure.parent, structure.parent_branch)].append(structure)
    return mapping


def _root_structures(ordered_structures: Iterable[TopologyStructure]) -> List[TopologyStructure]:
    return [structure for structure in ordered_structures if structure.parent == "ROOT"]


def _root_step(index: int) -> Dict[str, str]:
    return {
        "step_id": f"S{index}",
        "action": f"root_scope_{index}",
    }


def _loop_branch_returns(label: str, branch_index: int, has_children: bool) -> bool:
    if has_children:
        return False
    normalized = str(label).strip().lower()
    positive_tokens = (
        "success",
        "complete",
        "completed",
        "approved",
        "no_",
        "not_required",
        "valid",
        "compliant",
        "resolved",
    )
    if any(token in normalized for token in positive_tokens):
        return True
    return branch_index != 0


def _decision_requires_merge(
    branches: List[Dict[str, Any]],
    *,
    exit_to: str | None,
    exit_to_step_id: str | None,
) -> bool:
    route_counts: Dict[Tuple[str, str], int] = {}
    shared_exit = str(exit_to_step_id or exit_to or "").strip()
    shared_exit_kind = "step" if exit_to_step_id else "text"

    for branch in branches:
        if branch.get("next_block_id") or branch.get("child_block_ids"):
            return bool(shared_exit)
        reconnect_step_id = str(branch.get("reconnect_to_step_id") or "").strip()
        if reconnect_step_id:
            target = ("step", reconnect_step_id)
        elif bool(branch.get("returns_to_main_flow")) and shared_exit:
            target = (shared_exit_kind, shared_exit)
        else:
            continue
        route_counts[target] = route_counts.get(target, 0) + 1

    return any(count >= 2 for count in route_counts.values())


def _root_slot_ids(root_structures: List[TopologyStructure]) -> List[str]:
    return ["ROOT_START", *[f"AFTER_{structure.id}" for structure in root_structures]]


def _slot_structure_id(slot_id: str) -> str | None:
    normalized = str(slot_id or "").strip()
    if normalized == "ROOT_START":
        return None
    if normalized.startswith("AFTER_") and len(normalized) > len("AFTER_"):
        return normalized[len("AFTER_"):]
    return None


def _branch_key_set(artifact: TopologyArtifact) -> set[Tuple[str, str]]:
    return {
        (structure.id.strip(), branch.strip())
        for structure in artifact.structures
        for branch in structure.branches
    }


def _root_slot_actions(entry: Any) -> List[str]:
    normalized_actions: List[str] = []
    for step in getattr(entry, "actions", []) or []:
        action = str(getattr(step, "action", "") or "").strip()
        if action:
            normalized_actions.append(action)
    return normalized_actions


def validate_semantic_plan_against_topology(
    topology_artifact: Dict[str, Any] | TopologyArtifact,
    semantic_plan: Dict[str, Any] | SemanticSketchPlan,
) -> SemanticSketchPlan:
    artifact = _normalize_artifact(topology_artifact)
    semantics = _normalize_semantic_plan(semantic_plan)

    ordered_structures = _preorder_structures(artifact)
    root_structures = _root_structures(ordered_structures)
    expected_root_slot_ids = _root_slot_ids(root_structures)
    expected_root_slot_set = set(expected_root_slot_ids)

    actual_root_slot_ids = [entry.slot_id.strip() for entry in semantics.root_actions if entry.slot_id.strip()]
    actual_root_slot_set = set(actual_root_slot_ids)
    duplicate_root_slot_ids = sorted(
        {
            slot_id
            for slot_id in actual_root_slot_ids
            if actual_root_slot_ids.count(slot_id) > 1
        }
    )
    missing_root_slot_ids = [
        slot_id
        for slot_id in expected_root_slot_ids
        if slot_id not in actual_root_slot_set
    ]
    extra_root_slot_ids = sorted(actual_root_slot_set - expected_root_slot_set)
    placeholder_root_actions = [
        {
            "slot_id": entry.slot_id.strip(),
            "actions": [{"action": action} for action in _root_slot_actions(entry)],
        }
        for entry in semantics.root_actions
        if any(action.startswith("root_scope_") for action in _root_slot_actions(entry))
    ]

    misplaced_root_actions: List[Dict[str, str]] = []
    first_missing_index = next(
        (index for index, slot_id in enumerate(expected_root_slot_ids) if slot_id in missing_root_slot_ids),
        None,
    )
    if first_missing_index is not None:
        for later_slot_id in expected_root_slot_ids[first_missing_index + 1:]:
            matching_entry = next(
                (
                    entry
                    for entry in semantics.root_actions
                    if entry.slot_id.strip() == later_slot_id and _root_slot_actions(entry)
                ),
                None,
            )
            if matching_entry is None:
                continue
            misplaced_root_actions.append(
                {
                    "slot_id": later_slot_id,
                    "actions": [{"action": action} for action in _root_slot_actions(matching_entry)],
                    "earliest_missing_slot_id": expected_root_slot_ids[first_missing_index],
                }
            )

    expected_branch_keys = _branch_key_set(artifact)
    actual_branch_key_list = [
        (entry.structure_id.strip(), entry.branch.strip())
        for entry in semantics.branch_plans
    ]
    actual_branch_keys = set(actual_branch_key_list)
    duplicate_branch_plans = sorted(
        {
            branch_key
            for branch_key in actual_branch_key_list
            if actual_branch_key_list.count(branch_key) > 1
        }
    )
    missing_branch_keys = sorted(expected_branch_keys - actual_branch_keys)
    extra_branch_keys = sorted(actual_branch_keys - expected_branch_keys)

    if (
        missing_root_slot_ids
        or extra_root_slot_ids
        or duplicate_root_slot_ids
        or placeholder_root_actions
        or misplaced_root_actions
        or missing_branch_keys
        or extra_branch_keys
        or duplicate_branch_plans
    ):
        missing_root_structures = [
            structure_id
            for structure_id in (_slot_structure_id(slot_id) for slot_id in missing_root_slot_ids)
            if structure_id is not None
        ]
        raise SemanticPlanTopologyValidationError(
            "SemanticSketchPlan does not satisfy the topology contract. "
            f"missing_root_slots={missing_root_slot_ids}, "
            f"missing_root_structures={missing_root_structures}, "
            f"extra_root_slots={extra_root_slot_ids}, "
            f"duplicate_root_slots={duplicate_root_slot_ids}, "
            f"placeholder_root_actions={placeholder_root_actions}, "
            f"misplaced_root_actions={misplaced_root_actions}, "
            f"missing_branch_plans={missing_branch_keys}, "
            f"extra_branch_plans={extra_branch_keys}, "
            f"duplicate_branch_plans={duplicate_branch_plans}"
        )

    return semantics


def compile_topology_artifact_to_activity_sketch(
    topology_artifact: Dict[str, Any] | TopologyArtifact,
) -> Dict[str, Any]:
    artifact = _normalize_artifact(topology_artifact)
    ordered_structures = _preorder_structures(artifact)
    root_structures = _root_structures(ordered_structures)
    nested_children = _branch_children(ordered_structures)

    main_flow = [_root_step(index + 1) for index in range(len(root_structures) + 1)]
    root_step_lookup = {
        structure.id: main_flow[index]
        for index, structure in enumerate(root_structures)
    }
    root_exit_lookup = {
        structure.id: main_flow[index + 1]
        for index, structure in enumerate(root_structures)
    }

    control_blocks: List[Dict[str, Any]] = []

    for structure in ordered_structures:
        if structure.parent == "ROOT":
            entry_step = root_step_lookup[structure.id]
            entry_after = entry_step["action"]
            entry_after_step_id = entry_step["step_id"]
            exit_step = root_exit_lookup[structure.id]
            exit_to = exit_step["action"]
            exit_to_step_id = exit_step["step_id"]
        else:
            entry_after = f"scope_{structure.parent}_{structure.parent_branch}"
            entry_after_step_id = None
            exit_to = None
            exit_to_step_id = None

        branches: List[Dict[str, Any]] = []
        for branch_index, branch_label in enumerate(structure.branches):
            direct_children = nested_children.get((structure.id, branch_label), [])
            branch_payload = {
                "label": branch_label,
                "returns_to_main_flow": True,
                "steps": [],
                "next_block_id": None,
                "child_block_ids": [child.id for child in direct_children],
            }
            if structure.type == "loop":
                branch_payload["returns_to_main_flow"] = _loop_branch_returns(
                    branch_label,
                    branch_index,
                    bool(direct_children),
                )
            elif direct_children:
                branch_payload["returns_to_main_flow"] = False
            branches.append(branch_payload)

        requires_merge = structure.type == "parallel"
        if structure.type == "decision":
            requires_merge = _decision_requires_merge(
                branches,
                exit_to=exit_to,
                exit_to_step_id=exit_to_step_id,
            )

        block = {
            "block_id": structure.id,
            "type": structure.type,
            "entry_after": entry_after,
            "entry_after_step_id": entry_after_step_id,
            "branches": branches,
            "requires_merge": requires_merge,
            "exit_to": exit_to,
            "exit_to_step_id": exit_to_step_id,
            "loop_back_to": entry_after if structure.type == "loop" else None,
            "loop_back_to_step_id": entry_after_step_id if structure.type == "loop" else None,
            "notes": structure.purpose,
        }
        control_blocks.append(block)

    sketch = ActivitySketch.model_validate(
        {
            "main_flow": main_flow,
            "control_blocks": control_blocks,
        }
    )
    return sketch.model_dump(mode="json")


def _normalize_semantic_plan(semantic_plan: Dict[str, Any] | SemanticSketchPlan) -> SemanticSketchPlan:
    if isinstance(semantic_plan, SemanticSketchPlan):
        return semantic_plan
    return SemanticSketchPlan.model_validate(semantic_plan)


def _root_action_map(
    semantic_plan: SemanticSketchPlan,
    root_structures: List[TopologyStructure],
) -> Dict[str, List[str]]:
    slot_ids = _root_slot_ids(root_structures)
    provided = {
        entry.slot_id: _root_slot_actions(entry)
        for entry in semantic_plan.root_actions
    }
    missing_slot_ids = [slot_id for slot_id in slot_ids if slot_id not in provided]
    if missing_slot_ids:
        raise SemanticPlanTopologyValidationError(
            "SemanticSketchPlan is incomplete for the topology contract. "
            f"missing_root_slots={missing_slot_ids}, "
            f"missing_root_structures={[slot_id[len('AFTER_'):] for slot_id in missing_slot_ids if slot_id.startswith('AFTER_')]}"
        )
    return {
        slot_id: provided[slot_id]
        for slot_id in slot_ids
    }


def _slot_entry_anchor(
    *,
    slot_id: str,
    slot_step_bounds: Dict[str, Dict[str, str | None]],
    root_slot_ids: List[str],
    root_structures: List[TopologyStructure],
) -> Tuple[str | None, str | None]:
    bounds = slot_step_bounds[slot_id]
    if bounds["last_action"] is not None:
        return bounds["last_action"], bounds["last_step_id"]
    slot_index = root_slot_ids.index(slot_id)
    if slot_index == 0:
        return None, None
    return root_structures[slot_index - 1].purpose, None


def _slot_exit_anchor(
    *,
    slot_id: str,
    slot_step_bounds: Dict[str, Dict[str, str | None]],
    root_slot_ids: List[str],
    root_structures: List[TopologyStructure],
) -> Tuple[str | None, str | None]:
    bounds = slot_step_bounds[slot_id]
    if bounds["first_action"] is not None:
        return bounds["first_action"], bounds["first_step_id"]
    slot_index = root_slot_ids.index(slot_id)
    if slot_index >= len(root_structures):
        return None, None
    return root_structures[slot_index].purpose, None


def _branch_plan_map(semantic_plan: SemanticSketchPlan) -> Dict[Tuple[str, str], Any]:
    return {
        (entry.structure_id, entry.branch): entry
        for entry in semantic_plan.branch_plans
    }


def _root_ancestor_map(ordered_structures: List[TopologyStructure]) -> Dict[str, str]:
    by_id = {structure.id: structure for structure in ordered_structures}
    ancestors: Dict[str, str] = {}
    for structure in ordered_structures:
        current = structure
        while current.parent != "ROOT":
            current = by_id[current.parent]
        ancestors[structure.id] = current.id
    return ancestors


def compile_topology_and_semantics_to_activity_sketch(
    topology_artifact: Dict[str, Any] | TopologyArtifact,
    semantic_plan: Dict[str, Any] | SemanticSketchPlan,
) -> Dict[str, Any]:
    artifact = _normalize_artifact(topology_artifact)
    semantics = validate_semantic_plan_against_topology(artifact, semantic_plan)
    ordered_structures = _preorder_structures(artifact)
    root_structures = _root_structures(ordered_structures)
    nested_children = _branch_children(ordered_structures)
    root_ancestors = _root_ancestor_map(ordered_structures)

    root_action_lookup = _root_action_map(semantics, root_structures)
    root_slot_ids = _root_slot_ids(root_structures)
    main_flow: List[Dict[str, str]] = []
    slot_step_bounds: Dict[str, Dict[str, str | None]] = {}
    step_index = 1
    for slot_id in root_slot_ids:
        slot_actions = root_action_lookup[slot_id]
        slot_step_bounds[slot_id] = {
            "first_action": slot_actions[0] if slot_actions else None,
            "first_step_id": f"S{step_index}" if slot_actions else None,
            "last_action": slot_actions[-1] if slot_actions else None,
            "last_step_id": f"S{step_index + len(slot_actions) - 1}" if slot_actions else None,
        }
        for action in slot_actions:
            main_flow.append(
                {
                    "step_id": f"S{step_index}",
                    "action": action,
                }
            )
            step_index += 1
    branch_plans = _branch_plan_map(semantics)
    root_index_by_structure = {
        structure.id: index
        for index, structure in enumerate(root_structures)
    }

    control_blocks: List[Dict[str, Any]] = []
    control_block_map: Dict[str, Dict[str, Any]] = {}

    for structure in ordered_structures:
        direct_children_by_branch = {
            branch: nested_children.get((structure.id, branch), [])
            for branch in structure.branches
        }
        if structure.parent == "ROOT":
            root_index = root_index_by_structure[structure.id]
            entry_slot = root_slot_ids[root_index]
            exit_slot = root_slot_ids[root_index + 1]
            entry_after, entry_after_step_id = _slot_entry_anchor(
                slot_id=entry_slot,
                slot_step_bounds=slot_step_bounds,
                root_slot_ids=root_slot_ids,
                root_structures=root_structures,
            )
            exit_to, exit_to_step_id = _slot_exit_anchor(
                slot_id=exit_slot,
                slot_step_bounds=slot_step_bounds,
                root_slot_ids=root_slot_ids,
                root_structures=root_structures,
            )
        else:
            parent_branch_plan = branch_plans.get((structure.parent, structure.parent_branch or ""))
            if parent_branch_plan and parent_branch_plan.steps:
                entry_after = parent_branch_plan.steps[-1].action
            else:
                entry_after = f"scope_{structure.parent}_{structure.parent_branch}"
            entry_after_step_id = None
            root_ancestor = root_ancestors[structure.id]
            exit_slot = f"AFTER_{root_ancestor}"
            exit_to, exit_to_step_id = _slot_exit_anchor(
                slot_id=exit_slot,
                slot_step_bounds=slot_step_bounds,
                root_slot_ids=root_slot_ids,
                root_structures=root_structures,
            )

        branches: List[Dict[str, Any]] = []
        for branch_label in structure.branches:
            plan = branch_plans.get((structure.id, branch_label))
            direct_children = direct_children_by_branch[branch_label]
            intent = plan.intent if plan is not None else "continue"
            reconnect_target = (
                slot_step_bounds.get(plan.target_slot_id)
                if plan is not None and plan.target_slot_id
                else None
            )
            steps = [
                {"action": step.action}
                for step in (plan.steps if plan is not None else [])
            ]
            branch_payload = {
                "label": branch_label,
                "returns_to_main_flow": intent == "continue" and not direct_children,
                "steps": steps,
                "next_block_id": None,
                "child_block_ids": [direct_children[0].id] if direct_children else [],
            }
            if reconnect_target is not None and reconnect_target["first_step_id"] is not None:
                branch_payload["reconnect_to_step_id"] = reconnect_target["first_step_id"]
            if intent in {"terminate", "loop_back"}:
                branch_payload["returns_to_main_flow"] = False
            if direct_children:
                branch_payload["returns_to_main_flow"] = False
            branches.append(branch_payload)

        requires_merge = structure.type == "parallel"
        if structure.type == "decision":
            requires_merge = _decision_requires_merge(
                branches,
                exit_to=exit_to,
                exit_to_step_id=exit_to_step_id,
            )

        block = {
            "block_id": structure.id,
            "type": structure.type,
            "entry_after": entry_after,
            "entry_after_step_id": entry_after_step_id,
            "branches": branches,
            "requires_merge": requires_merge,
            "exit_to": exit_to,
            "exit_to_step_id": exit_to_step_id,
            "loop_back_to": entry_after if structure.type == "loop" else None,
            "loop_back_to_step_id": entry_after_step_id if structure.type == "loop" else None,
            "notes": structure.purpose,
        }
        control_blocks.append(block)
        control_block_map[structure.id] = block

    for (parent_id, parent_branch), siblings in nested_children.items():
        if len(siblings) < 2:
            continue
        for current, nxt in zip(siblings, siblings[1:]):
            current_block = control_block_map[current.id]
            for branch_payload in current_block["branches"]:
                plan = branch_plans.get((current.id, branch_payload["label"]))
                intent = plan.intent if plan is not None else "continue"
                if branch_payload["child_block_ids"]:
                    continue
                if intent == "continue":
                    branch_payload["next_block_id"] = nxt.id
                    branch_payload["returns_to_main_flow"] = False

    sketch = ActivitySketch.model_validate(
        {
            "main_flow": main_flow,
            "control_blocks": control_blocks,
        }
    )
    return sketch.model_dump(mode="json")


def _normalize_sketch(activity_sketch: Dict[str, Any] | ActivitySketch) -> ActivitySketch:
    if isinstance(activity_sketch, ActivitySketch):
        return activity_sketch
    return ActivitySketch.model_validate(activity_sketch)


def _infer_sketch_ownership(activity_sketch: ActivitySketch) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    ownership: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    block_ids = {
        block.block_id
        for block in activity_sketch.control_blocks
        if block.block_id
    }

    for block in activity_sketch.control_blocks:
        if not block.block_id:
            continue
        for branch in block.branches:
            for child_block_id in branch.child_block_ids:
                if child_block_id in block_ids:
                    ownership[child_block_id].append(
                        {
                            "parent": block.block_id,
                            "parent_branch": branch.label,
                            "via": "child_block_ids",
                        }
                    )
            if branch.next_block_id and branch.next_block_id in block_ids:
                ownership[branch.next_block_id].append(
                    {
                        "parent": block.block_id,
                        "parent_branch": branch.label,
                        "via": "next_block_id",
                    }
                )

    inferred: Dict[str, Dict[str, Any]] = {}
    ownership_conflicts: List[str] = []
    for block in activity_sketch.control_blocks:
        block_id = block.block_id
        if not block_id:
            continue
        candidates = ownership.get(block_id, [])
        if not candidates:
            inferred[block_id] = {"parent": "ROOT", "parent_branch": None, "via": "unowned"}
            continue
        inferred[block_id] = candidates[0]
        if len(candidates) > 1:
            ownership_conflicts.append(block_id)
    return inferred, ownership_conflicts


def compare_topology_artifact_to_activity_sketch(
    topology_artifact: Dict[str, Any] | TopologyArtifact,
    activity_sketch: Dict[str, Any] | ActivitySketch,
) -> Dict[str, Any]:
    artifact = _normalize_artifact(topology_artifact)
    sketch = _normalize_sketch(activity_sketch)
    ordered_structures = _preorder_structures(artifact)
    sketch_blocks = [block for block in sketch.control_blocks if block.block_id]
    sketch_by_id = {str(block.block_id): block for block in sketch_blocks}
    ownership_map, ownership_conflicts = _infer_sketch_ownership(sketch)

    structure_to_block_id: Dict[str, Optional[str]] = {}
    if all(structure.id in sketch_by_id for structure in ordered_structures):
        for structure in ordered_structures:
            structure_to_block_id[structure.id] = structure.id
    else:
        for index, structure in enumerate(ordered_structures):
            structure_to_block_id[structure.id] = (
                str(sketch_blocks[index].block_id) if index < len(sketch_blocks) else None
            )

    reports: List[Dict[str, Any]] = []
    preserved_type_count = 0
    preserved_parent_count = 0
    preserved_parent_branch_count = 0
    root_promotions = 0
    missing_structures = 0

    for structure in ordered_structures:
        sketch_block_id = structure_to_block_id.get(structure.id)
        block = sketch_by_id.get(sketch_block_id or "")
        inferred_owner = ownership_map.get(sketch_block_id or "", {"parent": None, "parent_branch": None, "via": "missing"})
        expected_parent_block_id = (
            "ROOT"
            if structure.parent == "ROOT"
            else structure_to_block_id.get(structure.parent)
        )

        type_preserved = bool(block and block.type == structure.type)
        parent_preserved = expected_parent_block_id == inferred_owner.get("parent")
        parent_branch_preserved = structure.parent_branch == inferred_owner.get("parent_branch")

        if type_preserved:
            preserved_type_count += 1
        if parent_preserved:
            preserved_parent_count += 1
        if parent_branch_preserved:
            preserved_parent_branch_count += 1
        if sketch_block_id is None or block is None:
            missing_structures += 1
        if structure.parent != "ROOT" and inferred_owner.get("parent") == "ROOT":
            root_promotions += 1

        reports.append(
            {
                "structure_id": structure.id,
                "structure_type": structure.type,
                "expected_parent": structure.parent,
                "expected_parent_branch": structure.parent_branch,
                "matched_block_id": sketch_block_id,
                "matched_block_type": getattr(block, "type", None),
                "actual_parent": inferred_owner.get("parent"),
                "actual_parent_branch": inferred_owner.get("parent_branch"),
                "ownership_binding": inferred_owner.get("via"),
                "type_preserved": type_preserved,
                "parent_preserved": parent_preserved,
                "parent_branch_preserved": parent_branch_preserved,
            }
        )

    return {
        "metrics": {
            "topology_structure_count": len(ordered_structures),
            "sketch_control_block_count": len(sketch_blocks),
            "preserved_type_count": preserved_type_count,
            "preserved_parent_count": preserved_parent_count,
            "preserved_parent_branch_count": preserved_parent_branch_count,
            "missing_structure_count": missing_structures,
            "root_promotion_count": root_promotions,
            "ownership_conflict_count": len(ownership_conflicts),
        },
        "summary": {
            "type_sequence_match": preserved_type_count == len(ordered_structures),
            "parent_preservation_ratio": preserved_parent_count / len(ordered_structures) if ordered_structures else 1.0,
            "parent_branch_preservation_ratio": (
                preserved_parent_branch_count / len(ordered_structures) if ordered_structures else 1.0
            ),
        },
        "ownership_conflicts": ownership_conflicts,
        "structures": reports,
    }


__all__ = [
    "compare_topology_artifact_to_activity_sketch",
    "compile_topology_and_semantics_to_activity_sketch",
    "compile_topology_artifact_to_activity_sketch",
]
