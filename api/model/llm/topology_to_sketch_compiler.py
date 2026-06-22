from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .activity_sketch_model import ActivitySketch
from .semantic_sketch_plan_model import SemanticSketchPlan
from .topology_artifact_model import TopologyArtifact, TopologyStructure


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


def _root_slot_ids(root_structures: List[TopologyStructure]) -> List[str]:
    return ["ROOT_START", *[f"AFTER_{structure.id}" for structure in root_structures]]


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

        block = {
            "block_id": structure.id,
            "type": structure.type,
            "entry_after": entry_after,
            "entry_after_step_id": entry_after_step_id,
            "branches": branches,
            "requires_merge": False if structure.type == "loop" else True,
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
) -> Dict[str, str]:
    slot_ids = _root_slot_ids(root_structures)
    provided = {
        entry.slot_id: entry.action.strip()
        for entry in semantic_plan.root_actions
        if entry.action.strip()
    }
    return {
        slot_id: provided.get(slot_id, f"root_scope_{index + 1}")
        for index, slot_id in enumerate(slot_ids)
    }


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
    semantics = _normalize_semantic_plan(semantic_plan)
    ordered_structures = _preorder_structures(artifact)
    root_structures = _root_structures(ordered_structures)
    nested_children = _branch_children(ordered_structures)
    root_ancestors = _root_ancestor_map(ordered_structures)

    root_action_lookup = _root_action_map(semantics, root_structures)
    root_slot_ids = _root_slot_ids(root_structures)
    main_flow = [
        {
            "step_id": f"S{index + 1}",
            "action": root_action_lookup[slot_id],
        }
        for index, slot_id in enumerate(root_slot_ids)
    ]
    step_by_slot = {
        slot_id: main_flow[index]
        for index, slot_id in enumerate(root_slot_ids)
    }
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
            entry_after = step_by_slot[entry_slot]["action"]
            entry_after_step_id = step_by_slot[entry_slot]["step_id"]
            exit_to = step_by_slot[exit_slot]["action"]
            exit_to_step_id = step_by_slot[exit_slot]["step_id"]
        else:
            parent_branch_plan = branch_plans.get((structure.parent, structure.parent_branch or ""))
            if parent_branch_plan and parent_branch_plan.steps:
                entry_after = parent_branch_plan.steps[-1].action
            else:
                entry_after = f"scope_{structure.parent}_{structure.parent_branch}"
            entry_after_step_id = None
            root_ancestor = root_ancestors[structure.id]
            exit_slot = f"AFTER_{root_ancestor}"
            exit_to = step_by_slot[exit_slot]["action"]
            exit_to_step_id = step_by_slot[exit_slot]["step_id"]

        branches: List[Dict[str, Any]] = []
        for branch_label in structure.branches:
            plan = branch_plans.get((structure.id, branch_label))
            direct_children = direct_children_by_branch[branch_label]
            intent = plan.intent if plan is not None else "continue"
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
            if intent in {"terminate", "loop_back"}:
                branch_payload["returns_to_main_flow"] = False
            if direct_children:
                branch_payload["returns_to_main_flow"] = False
            branches.append(branch_payload)

        block = {
            "block_id": structure.id,
            "type": structure.type,
            "entry_after": entry_after,
            "entry_after_step_id": entry_after_step_id,
            "branches": branches,
            "requires_merge": False if structure.type == "loop" else True,
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
