from __future__ import annotations

"""General-purpose refinement planner contract and reconciliation.

Planner responsibilities:
- interpret process_text + current artifacts + user instruction
- propose complete updated topology and semantic artifacts

Deterministic reconciliation responsibilities:
- treat updated topology as authoritative for required semantic coverage
- preserve planner-provided and unchanged semantic information when possible
- synthesize only the minimum missing semantic entries required for structural
  completeness
- remain refinement-type agnostic; no instruction-specific branching
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .handler import call_openai
from .refinement_generator import _prepare_json_payload
from .semantic_sketch_plan_model import (
    SemanticSketchPlan,
    apply_semantic_branch_plan_schema_constraints,
    find_invalid_semantic_branch_plans,
)
from .topology_artifact_model import TopologyArtifact, TopologyStructure
from .topology_to_sketch_compiler import validate_semantic_plan_against_topology

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

logger = logging.getLogger(__name__)
_MAX_CORRECTION_ATTEMPTS = 2
_VALID_STRUCTURE_TYPES = {"decision", "loop", "parallel"}
_STRUCTURE_TYPE_ALIASES = {
    "branch": "decision",
    "branching": "decision",
    "condition": "decision",
    "conditional": "decision",
    "gateway": "decision",
    "if": "decision",
    "iterative": "loop",
    "iteration": "loop",
    "repeat": "loop",
    "retry": "loop",
    "concurrent": "parallel",
    "concurrency": "parallel",
    "fork": "parallel",
    "parallel_block": "parallel",
}


class RefinementTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_instruction: str


class RefinementPlannerResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    updated_topology_artifact: TopologyArtifact
    updated_semantic_sketch_plan: SemanticSketchPlan
    refinement_trace: RefinementTrace = Field(default_factory=lambda: RefinementTrace(user_instruction=""))

    @model_validator(mode="after")
    def validate_artifact_consistency(self) -> "RefinementPlannerResult":
        expected_branch_keys = {
            (structure.id.strip(), branch.strip())
            for structure in self.updated_topology_artifact.structures
            for branch in structure.branches
        }
        actual_branch_keys = {
            (plan.structure_id.strip(), plan.branch.strip())
            for plan in self.updated_semantic_sketch_plan.branch_plans
        }
        if actual_branch_keys != expected_branch_keys:
            missing = sorted(expected_branch_keys - actual_branch_keys)
            extra = sorted(actual_branch_keys - expected_branch_keys)
            raise ValueError(
                "updated_semantic_sketch_plan must define exactly one branch plan for each topology branch. "
                f"missing={missing}, extra={extra}"
            )

        expected_root_slots = {"ROOT_START", *{
            f"AFTER_{structure.id.strip()}"
            for structure in self.updated_topology_artifact.structures
            if structure.parent == "ROOT"
        }}
        actual_root_slots = {
            action.slot_id.strip()
            for action in self.updated_semantic_sketch_plan.root_actions
        }
        if actual_root_slots != expected_root_slots:
            missing = sorted(expected_root_slots - actual_root_slots)
            extra = sorted(actual_root_slots - expected_root_slots)
            raise ValueError(
                "updated_semantic_sketch_plan must define exactly one root action for each root slot. "
                f"missing={missing}, extra={extra}"
            )

        if not self.refinement_trace.user_instruction.strip():
            raise ValueError("refinement_trace.user_instruction must be non-empty")

        return self


REFINEMENT_PLANNER_SCHEMA: Dict[str, Any] = apply_semantic_branch_plan_schema_constraints(
    RefinementPlannerResult.model_json_schema()
)


class RefinementPlannerError(Exception):
    def __init__(self, message: str, *, debug_artifacts: Dict[str, Any]) -> None:
        super().__init__(message)
        self.debug_artifacts = debug_artifacts


def _build_refinement_correction_prompt(
    *,
    base_prompt: str,
    process_text: str,
    current_topology_artifact: Dict[str, Any],
    current_semantic_sketch_plan: Dict[str, Any],
    instruction: str,
    invalid_planner_output: str,
    parsed_planner_output: Dict[str, Any] | None,
    validation_error: str,
    correction_attempt: int,
) -> str:
    parsed_pretty = (
        json.dumps(parsed_planner_output, ensure_ascii=False, indent=2)
        if parsed_planner_output is not None
        else "null"
    )
    current_topology_pretty = json.dumps(current_topology_artifact, ensure_ascii=False, indent=2)
    current_semantics_pretty = json.dumps(current_semantic_sketch_plan, ensure_ascii=False, indent=2)
    return (
        f"{base_prompt}\n"
        "\nCorrection attempt:\n"
        f"This is correction attempt {correction_attempt}.\n"
        "Your previous refinement result failed deterministic validation.\n"
        "Return one complete corrected JSON object only.\n"
        "Preserve unchanged valid semantic slots exactly when they are still compatible with the updated topology.\n"
        "Do not omit required root slots, do not shift unaffected root actions, and do not invent fallback actions.\n"
        "Do not add explanations outside the JSON object.\n"
        "\nOriginal process text:\n"
        f"{process_text}\n"
        "\nCurrent topology artifact:\n"
        f"{current_topology_pretty}\n"
        "\nCurrent semantic sketch plan:\n"
        f"{current_semantics_pretty}\n"
        "\nRefinement instruction:\n"
        f"{instruction}\n"
        "\nInvalid planner raw output:\n"
        f"{invalid_planner_output}\n"
        "\nInvalid planner parsed JSON:\n"
        f"{parsed_pretty}\n"
        "\nDeterministic validation diagnostics:\n"
        f"{validation_error}\n"
    )


def _call_refinement_planner(
    *,
    model: str,
    prompt: str,
) -> Dict[str, Any]:
    response_mode = "structured_output"
    fallback_reason = None
    try:
        raw_output = call_openai(
            model=model,
            prompt=prompt,
            response_format=refinement_planner_response_format(),
            require_structured_output=True,
        )
    except Exception as exc:
        response_mode = "fallback_json_mode"
        fallback_reason = str(exc)
        logger.warning(
            "Refinement planner structured output failed; falling back to unconstrained JSON mode.",
            exc_info=True,
        )
        fallback_prompt = (
            prompt
            + "\nFallback instruction:\n"
            + "If structured output is unavailable, still return the same JSON object only."
        )
        raw_output = call_openai(
            model=model,
            prompt=fallback_prompt,
        )
    return {
        "raw_output": raw_output,
        "response_mode": response_mode,
        "fallback_reason": fallback_reason,
    }


def _root_structures(artifact: TopologyArtifact) -> List[TopologyStructure]:
    return [structure for structure in artifact.structures if structure.parent == "ROOT"]


def _expected_root_slot_ids(artifact: TopologyArtifact) -> List[str]:
    return ["ROOT_START", *[f"AFTER_{structure.id}" for structure in _root_structures(artifact)]]


def _expected_branch_keys(artifact: TopologyArtifact) -> List[Tuple[str, str]]:
    return [
        (structure.id, branch)
        for structure in artifact.structures
        for branch in structure.branches
    ]


def _current_root_slots(artifact: TopologyArtifact) -> List[Dict[str, str]]:
    root_structures = _root_structures(artifact)
    slots: List[Dict[str, str]] = [
        {
            "slot_id": "ROOT_START",
            "description": (
                f"Action before the first root structure {root_structures[0].id}"
                if root_structures
                else "Primary root-scope action for a linear process"
            ),
        }
    ]
    for structure in root_structures:
        slots.append(
            {
                "slot_id": f"AFTER_{structure.id}",
                "description": f"Action after root structure {structure.id} completes",
            }
        )
    return slots


def _current_branch_slots(artifact: TopologyArtifact) -> List[Dict[str, Any]]:
    slots: List[Dict[str, Any]] = []
    for structure in artifact.structures:
        for branch in structure.branches:
            slots.append(
                {
                    "structure_id": structure.id,
                    "branch": branch,
                    "type": structure.type,
                    "purpose": structure.purpose,
                }
            )
    return slots


def _refinement_contract_text() -> str:
    return """
Canonical refinement contract:
- TopologyArtifact is authoritative for control-flow structure, decisions, loops, parallel blocks, nesting, branch handles, and parent / parent_branch attachment
- SemanticSketchPlan is authoritative for root-scope actions, branch-local actions, and branch intent
- The current TopologyArtifact is the default output; start from the current artifact and apply only the minimum necessary edits
- Refinement must be locality-preserving by default: keep existing topology and semantics unchanged unless the user instruction explicitly requires a change
- Treat every existing structure as immutable unless the instruction explicitly requires changing it
- First decide the updated topology; then derive the required semantic coverage from that updated topology
- For the updated topology, required root slots are exactly: `ROOT_START` plus one `AFTER_<structure_id>` for every root-level structure in updated root order
- For the updated topology, required branch plans are exactly one `(structure_id, branch)` plan for every branch of every updated topology structure
- The updated semantic sketch plan must contain exactly that required coverage: no missing entries and no obsolete entries
- Preserve unchanged semantic information whenever it still matches the updated topology
- If topology changes, recompute only the semantic coverage required by the changed topology while preserving unaffected semantic entries exactly
- Do not redesign, improve, normalize, simplify, or rewrite the artifact for clarity or consistency
- Preserve existing structure ids, structure types, parent relationships, branch handles, and branch intents whenever the instruction does not explicitly require changing them
- Every unchanged structure must preserve exactly: `id`, `type`, `parent`, `parent_branch`, and `branches`
- Never delete, rename, retype, reparent, or replace an unrelated structure just because a local insertion or wording change is requested
- Never rename unrelated branches or modify unrelated branch intents
- Reuse existing structures whenever possible; if an existing structure already satisfies the instruction, keep it
- Only create new ids for genuinely new structures
- First classify the refinement intent as exactly one of: `Insert Action`, `Insert Decision`, `Insert Loop`, `Insert Parallel`, or a non-insert refinement type before deciding whether topology changes
- Distinguish refinement kinds from the user instruction before editing artifacts:
  - Insert Action: add exactly one business activity when the instruction asks for a step and does not imply branching, repetition, or concurrency
  - Insert Decision: add one `decision` structure when the instruction asks to check, decide, determine, classify, route, gate, or split flow based on a condition or outcome, even if the word `decision` is not used explicitly
  - Insert Loop: add one `loop` structure when the instruction asks to repeat, retry, rework until a condition holds, or iterate
  - Insert Parallel: add one `parallel` structure when the instruction asks to run paths concurrently, simultaneously, in parallel, or independently at the same time
- If the refinement is classified as `Insert Action`, keep `updated_topology_artifact` identical to the current topology artifact and model exactly one business action in semantics
- If the refinement is classified as `Insert Decision`, `Insert Loop`, or `Insert Parallel`, update `updated_topology_artifact` to add that control-flow structure and then derive the required updated semantics from the new topology
- Do not apply the `Insert Action` rule to instructions that are classified as `Insert Decision`, `Insert Loop`, or `Insert Parallel`, even when the instruction also mentions an activity, action, task, review step, or other business step
- If an inserted decision is placed before an existing activity, rewire control flow so the new decision occurs first and the referenced existing activity remains after the decision on the appropriate continuing branch or branches
- Branch labels are names only; never infer `continue`, `terminate`, or `loop_back` from words like `retry`, `reject`, `approve`, or similar labels
- Choose branch intent from the updated control-flow role designed by the updated topology and preserved semantics
- `branch_plans.intent` is a control-flow enum only and must always be exactly one of: `continue`, `terminate`, `loop_back`
- Put all business meaning, business actions, review steps, approval steps, compliance steps, and descriptive semantics into `branch_plans.steps`, never into `branch_plans.intent`
- For loop structures, preserve existing valid `loop_back` behavior when it still applies; if loop behavior changes, express that explicitly in the updated semantics
- Semantic entries must not encode topology ownership, topology ordering, or structural decisions
- The deterministic builder/compiler expects artifacts that already satisfy the coverage rules above
""".strip()


def _default_branch_steps(branch: str) -> List[Dict[str, str]]:
    normalized = str(branch).strip().lower()
    if not normalized:
        return []
    action = normalized.replace("_", " ").replace("-", " ").strip()
    if action == normalized and " " not in action and len(action) <= 3:
        return []
    return [{"action": action}] if action else []


def _default_branch_intents_for_structure(
    structure: TopologyStructure,
    branch_keys_missing_plan: List[Tuple[str, str]],
    preserved_branch_plan_map: Dict[Tuple[str, str], Any],
) -> Dict[Tuple[str, str], str]:
    """Assign topology-driven default intents for missing branch plans.

    Rules:
    - non-loop structures default to `continue`
    - loop structures must expose at least one `loop_back` branch; preserve any
      existing loop_back intents and, if none exist, assign the first missing
      branch as `loop_back` and the rest as `continue`
    """
    defaults: Dict[Tuple[str, str], str] = {}
    if structure.type != "loop":
        for branch_key in branch_keys_missing_plan:
            defaults[branch_key] = "continue"
        return defaults

    structure_branch_keys = [
        (structure.id, branch)
        for branch in structure.branches
    ]
    def _branch_plan_intent(plan: Any) -> str | None:
        if plan is None:
            return None
        if isinstance(plan, dict):
            intent = plan.get("intent")
        else:
            intent = getattr(plan, "intent", None)
        normalized_intent = str(intent).strip()
        return normalized_intent or None

    has_existing_loop_back = any(
        preserved_branch_plan_map.get(branch_key) is not None
        and _branch_plan_intent(preserved_branch_plan_map[branch_key]) == "loop_back"
        for branch_key in structure_branch_keys
    )
    loop_back_assigned = has_existing_loop_back
    for branch_key in branch_keys_missing_plan:
        if not loop_back_assigned:
            defaults[branch_key] = "loop_back"
            loop_back_assigned = True
        else:
            defaults[branch_key] = "continue"
    return defaults


def _normalize_structure_type(
    raw_type: Any,
    *,
    current_type: str | None = None,
) -> Any:
    normalized = str(raw_type or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in _VALID_STRUCTURE_TYPES:
        return normalized
    if normalized in _STRUCTURE_TYPE_ALIASES:
        return _STRUCTURE_TYPE_ALIASES[normalized]
    if current_type in _VALID_STRUCTURE_TYPES:
        return current_type
    return raw_type


def _normalize_updated_topology_artifact(
    updated_topology_artifact: Dict[str, Any] | TopologyArtifact,
    *,
    current_topology_artifact: Dict[str, Any] | TopologyArtifact,
) -> Dict[str, Any]:
    current_topology = TopologyArtifact.model_validate(current_topology_artifact)
    current_structure_map = {
        structure.id.strip(): structure
        for structure in current_topology.structures
    }
    if isinstance(updated_topology_artifact, TopologyArtifact):
        payload = updated_topology_artifact.model_dump(mode="json")
    else:
        payload = dict(updated_topology_artifact or {})

    structures = payload.get("structures")
    if not isinstance(structures, list):
        return payload

    normalized_structures: List[Any] = []
    for structure in structures:
        if not isinstance(structure, dict):
            normalized_structures.append(structure)
            continue
        normalized_structure = dict(structure)
        structure_id = str(normalized_structure.get("id") or "").strip()
        current_structure = current_structure_map.get(structure_id)
        normalized_structure["type"] = _normalize_structure_type(
            normalized_structure.get("type"),
            current_type=current_structure.type if current_structure is not None else None,
        )
        normalized_structures.append(normalized_structure)

    payload["structures"] = normalized_structures
    return payload


def _normalize_updated_root_action_entries(entries: Any) -> List[Dict[str, Any]]:
    normalized_entries: List[Dict[str, Any]] = []
    seen_entries: set[tuple[str, tuple[str, ...]]] = set()
    if not isinstance(entries, list):
        return normalized_entries
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        slot_id = str(entry.get("slot_id") or "").strip()
        if not slot_id:
            continue
        actions_payload = entry.get("actions")
        normalized_actions: List[Dict[str, str]] = []
        if isinstance(actions_payload, list):
            for step in actions_payload:
                if not isinstance(step, dict):
                    continue
                action = str(step.get("action") or "").strip()
                if action:
                    normalized_actions.append({"action": action})
        elif entry.get("action") is not None:
            action = str(entry.get("action") or "").strip()
            if action:
                normalized_actions.append({"action": action})
        entry_key = (slot_id, tuple(step["action"] for step in normalized_actions))
        if entry_key in seen_entries:
            continue
        seen_entries.add(entry_key)
        normalized_entries.append(
            {
                "slot_id": slot_id,
                "actions": normalized_actions,
            }
        )
    return normalized_entries


def _current_step_payloads(steps: Any) -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []
    if not isinstance(steps, list):
        return payloads
    for step in steps:
        if hasattr(step, "action"):
            action = str(step.action or "").strip()
            source_action_ids = list(getattr(step, "source_action_ids", []) or [])
        elif isinstance(step, dict):
            action = str(step.get("action") or "").strip()
            source_action_ids = [
                str(source_action_id).strip()
                for source_action_id in step.get("source_action_ids", []) or []
                if str(source_action_id).strip()
            ]
        else:
            continue
        if action:
            payloads.append(
                {
                    "action": action,
                    "source_action_ids": source_action_ids,
                }
            )
    return payloads


def _instruction_requests_direct_action_rename(instruction: str) -> bool:
    normalized_instruction = " ".join(str(instruction or "").split())
    return bool(
        re.search(r"\b(?:rename|relabel)\b.+\bto\b", normalized_instruction, re.IGNORECASE)
        or re.search(
            r"\bchange\s+(?:the\s+)?(?:name|label|wording)\b.+\bto\b",
            normalized_instruction,
            re.IGNORECASE,
        )
    )


def _reconcile_step_traceability(
    *,
    updated_steps: Any,
    current_steps: Any,
    instruction: str,
) -> List[Dict[str, Any]]:
    normalized_updated_steps = _current_step_payloads(updated_steps)
    normalized_current_steps = _current_step_payloads(current_steps)
    unmatched_current_indexes = list(range(len(normalized_current_steps)))
    reconciled_steps: List[Dict[str, Any] | None] = [None] * len(normalized_updated_steps)

    for updated_index, updated_step in enumerate(normalized_updated_steps):
        updated_key = " ".join(updated_step["action"].split()).casefold()
        matching_current_index = next(
            (
                current_index
                for current_index in unmatched_current_indexes
                if " ".join(normalized_current_steps[current_index]["action"].split()).casefold()
                == updated_key
            ),
            None,
        )
        if matching_current_index is None:
            continue
        unmatched_current_indexes.remove(matching_current_index)
        reconciled_steps[updated_index] = {
            "action": updated_step["action"],
            "source_action_ids": list(
                normalized_current_steps[matching_current_index]["source_action_ids"]
            ),
        }

    unmatched_updated_indexes = [
        index
        for index, reconciled_step in enumerate(reconciled_steps)
        if reconciled_step is None
    ]
    if (
        _instruction_requests_direct_action_rename(instruction)
        and len(unmatched_updated_indexes) == 1
        and len(unmatched_current_indexes) == 1
    ):
        updated_index = unmatched_updated_indexes.pop()
        current_index = unmatched_current_indexes.pop()
        reconciled_steps[updated_index] = {
            "action": normalized_updated_steps[updated_index]["action"],
            "source_action_ids": list(normalized_current_steps[current_index]["source_action_ids"]),
        }

    return [
        reconciled_step
        if reconciled_step is not None
        else {
            "action": normalized_updated_steps[index]["action"],
            "source_action_ids": [],
        }
        for index, reconciled_step in enumerate(reconciled_steps)
    ]


def _current_root_action_sequence(
    *,
    expected_root_slot_ids: List[str],
    current_semantic_sketch_plan: SemanticSketchPlan,
) -> List[List[Dict[str, Any]]]:
    current_root_action_map = {
        entry.slot_id.strip(): _current_step_payloads(entry.actions)
        for entry in current_semantic_sketch_plan.root_actions
    }
    return [current_root_action_map.get(slot_id, []) for slot_id in expected_root_slot_ids]


def _planner_root_action_hints(
    *,
    expected_root_slot_ids: List[str],
    updated_root_action_entries: List[Dict[str, Any]],
) -> List[int | None]:
    slot_index_map = {
        slot_id: index
        for index, slot_id in enumerate(expected_root_slot_ids)
    }
    valid_slot_counts: Dict[str, int] = {}
    for entry in updated_root_action_entries:
        slot_id = entry["slot_id"]
        if slot_id in slot_index_map:
            valid_slot_counts[slot_id] = valid_slot_counts.get(slot_id, 0) + 1
    hints: List[int | None] = []
    for entry in updated_root_action_entries:
        slot_id = entry["slot_id"]
        slot_index = slot_index_map.get(slot_id)
        if slot_index is None or valid_slot_counts.get(slot_id) != 1:
            hints.append(None)
            continue
        hints.append(slot_index)
    return hints


def _planner_actions_match_current_sequence(
    *,
    planner_actions: List[Tuple[str, ...]],
    current_root_actions: List[Tuple[str, ...]],
) -> bool:
    if len(planner_actions) != len(current_root_actions):
        return False
    return planner_actions == current_root_actions


def _planner_actions_match_current_prefix(
    *,
    planner_actions: List[Tuple[str, ...]],
    current_root_actions: List[Tuple[str, ...]],
) -> bool:
    if not planner_actions or len(planner_actions) >= len(current_root_actions):
        return False
    return current_root_actions[: len(planner_actions)] == planner_actions


def _instruction_requests_action_removal(instruction: str) -> bool:
    normalized_instruction = str(instruction or "").strip().lower()
    return any(
        token in normalized_instruction
        for token in (" remove ", " delete ", " drop ", " eliminate ")
    ) or normalized_instruction.startswith(("remove ", "delete ", "drop ", "eliminate "))


def _assign_planner_root_actions_to_slots(
    *,
    expected_root_slot_ids: List[str],
    planner_actions: List[Tuple[str, ...]],
    planner_slot_hints: List[int | None],
    current_root_actions: List[Tuple[str, ...]],
) -> List[Tuple[str, ...]]:
    slot_count = len(expected_root_slot_ids)
    action_count = len(planner_actions)
    if slot_count == 0:
        return []
    if action_count == 0:
        return [tuple() for _ in range(slot_count)]

    best_score_by_state: Dict[Tuple[int, int], int] = {}
    best_choice_by_state: Dict[Tuple[int, int], int] = {}

    def _placement_score(*, action_index: int, slot_index: int, next_slot_index: int) -> int:
        score = 4
        skipped_slots = slot_index - next_slot_index
        score -= skipped_slots * 4

        hint_index = planner_slot_hints[action_index]
        if hint_index is not None:
            if hint_index == slot_index:
                score += 2
            else:
                score -= abs(hint_index - slot_index)

        if planner_actions[action_index] == current_root_actions[slot_index]:
            score += 2
        return score

    def _skip_score(*, action_index: int) -> int:
        return -12 + (2 * min(action_index, 4))

    def _best_score(action_index: int, next_slot_index: int) -> int:
        state = (action_index, next_slot_index)
        if state in best_score_by_state:
            return best_score_by_state[state]
        if action_index >= action_count:
            best_score_by_state[state] = 0
            return 0

        skip_candidate_score = _skip_score(action_index=action_index) + _best_score(action_index + 1, next_slot_index)
        best_score = skip_candidate_score
        best_slot_index = -1
        for slot_index in range(next_slot_index, slot_count):
            candidate_score = _placement_score(
                action_index=action_index,
                slot_index=slot_index,
                next_slot_index=next_slot_index,
            ) + _best_score(action_index + 1, slot_index + 1)
            if candidate_score >= best_score:
                best_score = candidate_score
                best_slot_index = slot_index
        best_score_by_state[state] = best_score
        best_choice_by_state[state] = best_slot_index
        return best_score

    _best_score(0, 0)
    assigned_actions: List[Tuple[str, ...]] = [tuple() for _ in range(slot_count)]
    action_index = 0
    next_slot_index = 0
    while action_index < action_count:
        slot_index = best_choice_by_state[(action_index, next_slot_index)]
        if slot_index < 0:
            action_index += 1
            continue
        assigned_actions[slot_index] = planner_actions[action_index]
        action_index += 1
        next_slot_index = slot_index + 1
    return assigned_actions


def _reconcile_root_action_sequence(
    *,
    expected_root_slot_ids: List[str],
    updated_root_action_entries: List[Dict[str, Any]],
    current_root_actions: List[List[Dict[str, Any]]],
    instruction: str,
) -> List[Dict[str, Any]]:
    if not expected_root_slot_ids:
        return []
    normalized_current_actions = list(current_root_actions[: len(expected_root_slot_ids)])
    if len(normalized_current_actions) < len(expected_root_slot_ids):
        normalized_current_actions.extend([[] for _ in range(len(expected_root_slot_ids) - len(normalized_current_actions))])

    exact_slot_ids = [entry["slot_id"] for entry in updated_root_action_entries]
    if exact_slot_ids == expected_root_slot_ids and len(set(exact_slot_ids)) == len(expected_root_slot_ids):
        return [
            {
                "slot_id": entry["slot_id"],
                "actions": _reconcile_step_traceability(
                    updated_steps=entry["actions"],
                    current_steps=normalized_current_actions[index],
                    instruction=instruction,
                ),
            }
            for index, entry in enumerate(updated_root_action_entries)
        ]

    compressed_entries: List[Dict[str, Any]] = []
    seen_slot_ids: set[str] = set()
    for entry in updated_root_action_entries:
        slot_id = entry["slot_id"]
        if slot_id not in expected_root_slot_ids or slot_id in seen_slot_ids:
            continue
        compressed_entries.append(
            {
                "slot_id": slot_id,
                "actions": entry["actions"],
            }
        )
        seen_slot_ids.add(slot_id)
    if [entry["slot_id"] for entry in compressed_entries] == expected_root_slot_ids:
        return [
            {
                "slot_id": entry["slot_id"],
                "actions": _reconcile_step_traceability(
                    updated_steps=entry["actions"],
                    current_steps=normalized_current_actions[index],
                    instruction=instruction,
                ),
            }
            for index, entry in enumerate(compressed_entries)
        ]

    if len(updated_root_action_entries) < len(expected_root_slot_ids):
        present_slot_ids = [entry["slot_id"] for entry in updated_root_action_entries]
        missing_slot_ids = [
            slot_id
            for slot_id in expected_root_slot_ids
            if slot_id not in present_slot_ids
        ]
        raise ValueError(
            "Refinement planner produced an incomplete root action sequence for the updated topology. "
            f"missing_root_slots={missing_slot_ids}, "
            f"missing_root_structures={[slot_id[len('AFTER_'):] for slot_id in missing_slot_ids if slot_id.startswith('AFTER_')]}"
        )

    compressed_entries: List[Dict[str, Any]] = []
    seen_slot_ids: set[str] = set()
    for entry in updated_root_action_entries:
        slot_id = entry["slot_id"]
        if slot_id not in expected_root_slot_ids or slot_id in seen_slot_ids:
            continue
        compressed_entries.append(
            {
                "slot_id": slot_id,
                "actions": entry["actions"],
            }
        )
        seen_slot_ids.add(slot_id)
    if [entry["slot_id"] for entry in compressed_entries] == expected_root_slot_ids:
        return compressed_entries

    if len(updated_root_action_entries) < len(expected_root_slot_ids):
        present_slot_ids = [entry["slot_id"] for entry in updated_root_action_entries]
        missing_slot_ids = [
            slot_id
            for slot_id in expected_root_slot_ids
            if slot_id not in present_slot_ids
        ]
        raise ValueError(
            "Refinement planner produced an incomplete root action sequence for the updated topology. "
            f"missing_root_slots={missing_slot_ids}, "
            f"missing_root_structures={[slot_id[len('AFTER_'):] for slot_id in missing_slot_ids if slot_id.startswith('AFTER_')]}"
        )

    planner_actions = [tuple(step["action"] for step in entry["actions"]) for entry in updated_root_action_entries]
    normalized_current_action_tuples = [
        tuple(step["action"] for step in actions)
        for actions in normalized_current_actions
    ]
    if _planner_actions_match_current_sequence(
        planner_actions=planner_actions,
        current_root_actions=normalized_current_action_tuples,
    ):
        reconciled_actions = list(normalized_current_action_tuples)
    else:
        planner_slot_hints = _planner_root_action_hints(
            expected_root_slot_ids=expected_root_slot_ids,
            updated_root_action_entries=updated_root_action_entries,
        )
        reconciled_actions = _assign_planner_root_actions_to_slots(
            expected_root_slot_ids=expected_root_slot_ids,
            planner_actions=planner_actions,
            planner_slot_hints=planner_slot_hints,
            current_root_actions=normalized_current_action_tuples,
        )

    return [
        {
            "slot_id": slot_id,
            "actions": _reconcile_step_traceability(
                updated_steps=[{"action": action} for action in actions],
                current_steps=normalized_current_actions[index],
                instruction=instruction,
            ),
        }
        for index, (slot_id, actions) in enumerate(zip(expected_root_slot_ids, reconciled_actions))
    ]


def _normalize_updated_branch_plan(entry: Any) -> Dict[str, Any] | None:
    if not isinstance(entry, dict):
        return None
    structure_id = str(entry.get("structure_id") or "").strip()
    branch = str(entry.get("branch") or "").strip()
    intent = str(entry.get("intent") or "").strip()
    if not structure_id or not branch or not intent:
        return None
    steps_payload = entry.get("steps") or []
    steps = []
    if isinstance(steps_payload, list):
        for step in steps_payload:
            if not isinstance(step, dict):
                continue
            action = str(step.get("action") or "").strip()
            if not action:
                continue
            steps.append({"action": action})
    normalized: Dict[str, Any] = {
        "structure_id": structure_id,
        "branch": branch,
        "intent": intent,
        "steps": steps,
    }
    target_slot_id = str(entry.get("target_slot_id") or "").strip()
    if target_slot_id:
        normalized["target_slot_id"] = target_slot_id
    return normalized


def _normalize_reconnect_text(value: str) -> str:
    normalized = re.sub(r"[\"'`]", "", str(value or "").strip().lower())
    normalized = re.sub(r"\b(existing|decision|action|activity|task|node)\b", " ", normalized)
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    return " ".join(normalized.split())


def _root_structure_entry_slot_map(artifact: TopologyArtifact) -> Dict[str, str]:
    root_structures = _root_structures(artifact)
    root_slot_ids = _expected_root_slot_ids(artifact)
    return {
        structure.id: root_slot_ids[index]
        for index, structure in enumerate(root_structures)
    }


def _existing_target_node_map(
    *,
    current_topology_artifact: Dict[str, Any] | TopologyArtifact,
    current_semantic_sketch_plan: Dict[str, Any] | SemanticSketchPlan,
) -> Dict[str, str]:
    topology = TopologyArtifact.model_validate(current_topology_artifact)
    semantics = SemanticSketchPlan.model_validate(current_semantic_sketch_plan)
    node_map: Dict[str, str] = {}

    for root_action in semantics.root_actions:
        for step in root_action.actions:
            action_name = str(step.action or "").strip()
            if not action_name:
                continue
            node_map[action_name] = root_action.slot_id
            normalized = _normalize_reconnect_text(action_name)
            if normalized:
                node_map.setdefault(normalized, root_action.slot_id)

    entry_slot_by_structure = _root_structure_entry_slot_map(topology)
    for structure in _root_structures(topology):
        purpose = str(structure.purpose or "").strip()
        if not purpose:
            continue
        entry_slot_id = entry_slot_by_structure.get(structure.id)
        if not entry_slot_id:
            continue
        node_map[purpose] = entry_slot_id
        normalized = _normalize_reconnect_text(purpose)
        if normalized:
            node_map.setdefault(normalized, entry_slot_id)

    return node_map


def _resolve_existing_target_slot_id(
    *,
    current_topology_artifact: Dict[str, Any] | TopologyArtifact,
    current_semantic_sketch_plan: Dict[str, Any] | SemanticSketchPlan,
    target_text: str,
) -> str | None:
    target_lookup = _existing_target_node_map(
        current_topology_artifact=current_topology_artifact,
        current_semantic_sketch_plan=current_semantic_sketch_plan,
    )
    exact_target = str(target_text or "").strip()
    if exact_target in target_lookup:
        return target_lookup[exact_target]
    normalized_target = _normalize_reconnect_text(target_text)
    return target_lookup.get(normalized_target)


def _step_is_generated_reconnect_paraphrase(*, step_action: str, target_text: str) -> bool:
    normalized_step = _normalize_reconnect_text(step_action)
    normalized_target = _normalize_reconnect_text(target_text)
    if not normalized_step or not normalized_target:
        return False
    if normalized_step == normalized_target:
        return True

    reconnect_verbs = {"return", "go", "back", "reconnect", "connect", "resume"}
    step_tokens = set(normalized_step.split())
    target_tokens = set(normalized_target.split())
    if reconnect_verbs.intersection(step_tokens) and target_tokens and target_tokens.issubset(step_tokens):
        return True
    content_stopwords = {
        "a", "an", "the", "if", "is", "are", "to", "of", "and", "or", "do", "does",
        "did", "be", "existing", "decision", "action", "activity", "task", "node",
        "determine", "check",
    }
    step_content_tokens = step_tokens - reconnect_verbs - content_stopwords
    target_content_tokens = target_tokens - content_stopwords
    if reconnect_verbs.intersection(step_tokens):
        shared_tokens = step_content_tokens.intersection(target_content_tokens)
        if len(shared_tokens) >= 2:
            return True
    return False


def _infer_reconnect_targets_from_instruction(
    *,
    current_topology_artifact: Dict[str, Any] | TopologyArtifact,
    current_semantic_sketch_plan: Dict[str, Any] | SemanticSketchPlan,
    updated_topology_artifact: Dict[str, Any] | TopologyArtifact,
    updated_semantic_sketch_plan: Dict[str, Any] | SemanticSketchPlan,
    instruction: str,
) -> Dict[str, Any]:
    topology = TopologyArtifact.model_validate(updated_topology_artifact)
    semantics = SemanticSketchPlan.model_validate(updated_semantic_sketch_plan).model_dump(mode="json")
    branch_plan_map = {
        (entry["structure_id"], entry["branch"]): entry
        for entry in semantics.get("branch_plans") or []
    }
    connect_matches = re.finditer(
        r"connect\s+(?:the\s+)?(?P<branch>.+?)\s+(?:path|branch)\s+to\s+(?:the\s+)?(?:existing\s+)?['\"]?(?P<target>.+?)['\"]?(?:\.|$)",
        str(instruction or ""),
        flags=re.IGNORECASE,
    )

    for match in connect_matches:
        normalized_branch = _normalize_reconnect_text(match.group("branch"))
        target_slot_id = _resolve_existing_target_slot_id(
            current_topology_artifact=current_topology_artifact,
            current_semantic_sketch_plan=current_semantic_sketch_plan,
            target_text=match.group("target"),
        )
        if not normalized_branch or not target_slot_id:
            continue
        candidate_branch_keys = [
            (structure.id, branch)
            for structure in topology.structures
            for branch in structure.branches
            if _normalize_reconnect_text(branch) == normalized_branch
            and branch_plan_map.get((structure.id, branch)) is not None
            and not branch_plan_map[(structure.id, branch)].get("target_slot_id")
        ]
        if len(candidate_branch_keys) > 1:
            raise ValueError(
                "Refinement reconnect target is ambiguous across multiple branches. "
                f"branch_reference={match.group('branch')!r}, "
                f"candidate_branches={candidate_branch_keys}"
            )
        for structure in topology.structures:
            for branch in structure.branches:
                if _normalize_reconnect_text(branch) != normalized_branch:
                    continue
                branch_plan = branch_plan_map.get((structure.id, branch))
                if branch_plan is None or branch_plan.get("target_slot_id"):
                    continue
                branch_plan["target_slot_id"] = target_slot_id
                branch_steps = branch_plan.get("steps") or []
                branch_plan["steps"] = [
                    step
                    for step in branch_steps
                    if not _step_is_generated_reconnect_paraphrase(
                        step_action=str(step.get("action") or ""),
                        target_text=match.group("target"),
                    )
                ]

    return semantics


def _reconcile_semantic_plan_to_topology(
    *,
    updated_topology_artifact: Dict[str, Any] | TopologyArtifact,
    updated_semantic_sketch_plan: Dict[str, Any] | SemanticSketchPlan,
    current_semantic_sketch_plan: Dict[str, Any] | SemanticSketchPlan,
    instruction: str,
) -> Dict[str, Any]:
    topology = TopologyArtifact.model_validate(updated_topology_artifact)
    current_semantics = SemanticSketchPlan.model_validate(current_semantic_sketch_plan)
    expected_root_slot_ids = _expected_root_slot_ids(topology)
    updated_semantic_payload = (
        updated_semantic_sketch_plan.model_dump(mode="json")
        if isinstance(updated_semantic_sketch_plan, SemanticSketchPlan)
        else dict(updated_semantic_sketch_plan or {})
    )
    updated_root_action_entries = _normalize_updated_root_action_entries(
        updated_semantic_payload.get("root_actions")
    )
    current_root_actions = _current_root_action_sequence(
        expected_root_slot_ids=expected_root_slot_ids,
        current_semantic_sketch_plan=current_semantics,
    )
    reconciled_root_actions = _reconcile_root_action_sequence(
        expected_root_slot_ids=expected_root_slot_ids,
        updated_root_action_entries=updated_root_action_entries,
        current_root_actions=current_root_actions,
        instruction=instruction,
    )

    updated_branch_plan_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for entry in updated_semantic_payload.get("branch_plans") or []:
        normalized_entry = _normalize_updated_branch_plan(entry)
        if normalized_entry is None:
            continue
        branch_key = (normalized_entry["structure_id"], normalized_entry["branch"])
        updated_branch_plan_map.setdefault(branch_key, normalized_entry)
    current_branch_plan_map = {
        (entry.structure_id.strip(), entry.branch.strip()): entry
        for entry in current_semantics.branch_plans
    }
    reconciled_branch_plans: List[Dict[str, Any]] = []
    preserved_branch_plan_map = {
        branch_key: updated_branch_plan_map.get(branch_key) or current_branch_plan_map.get(branch_key)
        for branch_key in _expected_branch_keys(topology)
    }
    for structure in topology.structures:
        missing_branch_keys = [
            (structure.id, branch)
            for branch in structure.branches
            if preserved_branch_plan_map.get((structure.id, branch)) is None
        ]
        default_intents = _default_branch_intents_for_structure(
            structure,
            missing_branch_keys,
            preserved_branch_plan_map,
        )
        for branch in structure.branches:
            structure_id = structure.id
            branch_key = (structure_id, branch)
            updated_branch_plan = updated_branch_plan_map.get(branch_key)
            current_branch_plan = current_branch_plan_map.get(branch_key)
            if updated_branch_plan is not None:
                reconciled_branch_plan = dict(updated_branch_plan)
                reconciled_branch_plan["steps"] = _reconcile_step_traceability(
                    updated_steps=updated_branch_plan.get("steps") or [],
                    current_steps=current_branch_plan.steps if current_branch_plan is not None else [],
                    instruction=instruction,
                )
                reconciled_branch_plans.append(reconciled_branch_plan)
                continue
            if current_branch_plan is not None:
                reconciled_branch_plans.append(current_branch_plan.model_dump(mode="json"))
                continue
            reconciled_branch_plans.append(
                {
                    "structure_id": structure_id,
                    "branch": branch,
                    "intent": default_intents[branch_key],
                    "steps": _default_branch_steps(branch),
                }
            )

    reconciled = SemanticSketchPlan.model_validate(
        {
            "root_actions": reconciled_root_actions,
            "branch_plans": reconciled_branch_plans,
        }
    )
    return validate_semantic_plan_against_topology(
        topology,
        reconciled,
    ).model_dump(mode="json")


def _reconcile_refinement_planner_payload(
    parsed_json: Dict[str, Any],
    *,
    current_topology_artifact: Dict[str, Any] | TopologyArtifact,
    current_semantic_sketch_plan: Dict[str, Any] | SemanticSketchPlan,
    instruction: str,
) -> Dict[str, Any]:
    updated_topology = _normalize_updated_topology_artifact(
        parsed_json.get("updated_topology_artifact", {}),
        current_topology_artifact=current_topology_artifact,
    )
    parsed_json["updated_topology_artifact"] = updated_topology
    updated_semantics = parsed_json.get("updated_semantic_sketch_plan", {})
    reconciled_semantics = _reconcile_semantic_plan_to_topology(
        updated_topology_artifact=updated_topology,
        updated_semantic_sketch_plan=updated_semantics,
        current_semantic_sketch_plan=current_semantic_sketch_plan,
        instruction=instruction,
    )
    parsed_json["updated_semantic_sketch_plan"] = _infer_reconnect_targets_from_instruction(
        current_topology_artifact=current_topology_artifact,
        current_semantic_sketch_plan=current_semantic_sketch_plan,
        updated_topology_artifact=updated_topology,
        updated_semantic_sketch_plan=reconciled_semantics,
        instruction=instruction,
    )
    return parsed_json


def build_refinement_planner_prompt(
    process_text: str,
    *,
    current_topology_artifact: Dict[str, Any] | TopologyArtifact,
    current_semantic_sketch_plan: Dict[str, Any] | SemanticSketchPlan,
    instruction: str,
) -> str:
    topology = TopologyArtifact.model_validate(current_topology_artifact)
    semantic_plan = SemanticSketchPlan.model_validate(current_semantic_sketch_plan).model_dump(mode="json")
    template = _env.get_template("activity_refinement_planner_prompt.jinja")
    return template.render(
        process_text=process_text,
        current_topology_artifact=topology.model_dump(mode="json"),
        current_semantic_sketch_plan=semantic_plan,
        current_root_slots=_current_root_slots(topology),
        current_branch_slots=_current_branch_slots(topology),
        refinement_contract_text=_refinement_contract_text(),
        instruction=instruction,
    ).rstrip() + "\n"


def refinement_planner_response_format() -> Dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "refinement_planner_result",
            "schema": REFINEMENT_PLANNER_SCHEMA,
            "strict": True,
        },
    }


def parse_refinement_planner_json(raw_output: str) -> Dict[str, Any]:
    parsed_json = json.loads(_prepare_json_payload(raw_output))
    if not isinstance(parsed_json, dict):
        raise ValueError("Refinement planner payload must be a JSON object")
    updated_semantic_payload = parsed_json.get("updated_semantic_sketch_plan")
    if isinstance(updated_semantic_payload, dict):
        invalid_branch_plans = find_invalid_semantic_branch_plans(updated_semantic_payload)
        for invalid_branch_plan in invalid_branch_plans:
            logger.error(
                "Refinement planner produced invalid branch plan: structure_id=%s branch=%s intent=%s "
                "parsed_branch_plan=%s raw_planner_output=%s",
                invalid_branch_plan["structure_id"],
                invalid_branch_plan["branch"],
                invalid_branch_plan["intent"],
                invalid_branch_plan["parsed_branch_plan"],
                raw_output,
            )
    validated = RefinementPlannerResult.model_validate(parsed_json)
    return validated.model_dump(mode="json")


def generate_refinement_plan(
    process_text: str,
    *,
    current_topology_artifact: Dict[str, Any] | TopologyArtifact,
    current_semantic_sketch_plan: Dict[str, Any] | SemanticSketchPlan,
    instruction: str,
    model: str = "gpt-4o",
) -> Dict[str, Any]:
    normalized_topology_artifact = TopologyArtifact.model_validate(current_topology_artifact).model_dump(mode="json")
    normalized_semantic_plan = SemanticSketchPlan.model_validate(current_semantic_sketch_plan).model_dump(mode="json")
    prompt = build_refinement_planner_prompt(
        process_text,
        current_topology_artifact=normalized_topology_artifact,
        current_semantic_sketch_plan=normalized_semantic_plan,
        instruction=instruction,
    )
    planner_attempts: List[Dict[str, Any]] = []
    current_prompt = prompt
    parsed_json: Dict[str, Any] | None = None
    invalid_branch_plans: List[Dict[str, Any]] = []
    reconciled_json: Dict[str, Any] | None = None
    artifact: Dict[str, Any] | None = None
    raw_output = ""
    response_mode = "structured_output"
    fallback_reason = None
    last_exc: Exception | None = None
    for correction_attempt in range(_MAX_CORRECTION_ATTEMPTS + 1):
        planner_call = _call_refinement_planner(
            model=model,
            prompt=current_prompt,
        )
        raw_output = planner_call["raw_output"]
        response_mode = planner_call["response_mode"]
        fallback_reason = planner_call["fallback_reason"]
        parsed_json = None
        invalid_branch_plans = []
        reconciled_json = None
        try:
            parsed_json = json.loads(_prepare_json_payload(raw_output))
            if not isinstance(parsed_json, dict):
                raise ValueError("Refinement planner payload must be a JSON object")
            updated_semantic_payload = parsed_json.get("updated_semantic_sketch_plan")
            if isinstance(updated_semantic_payload, dict):
                invalid_branch_plans = find_invalid_semantic_branch_plans(updated_semantic_payload)
                for invalid_branch_plan in invalid_branch_plans:
                    logger.error(
                        "Refinement planner produced invalid branch plan: structure_id=%s branch=%s intent=%s "
                        "parsed_branch_plan=%s raw_planner_output=%s",
                        invalid_branch_plan["structure_id"],
                        invalid_branch_plan["branch"],
                        invalid_branch_plan["intent"],
                        invalid_branch_plan["parsed_branch_plan"],
                        raw_output,
                    )
            reconciled_json = _reconcile_refinement_planner_payload(
                parsed_json,
                current_topology_artifact=normalized_topology_artifact,
                current_semantic_sketch_plan=normalized_semantic_plan,
                instruction=instruction,
            )
            artifact = RefinementPlannerResult.model_validate(reconciled_json).model_dump(mode="json")
            planner_attempts.append(
                {
                    "attempt_index": correction_attempt,
                    "prompt": current_prompt,
                    "raw_output": raw_output,
                    "parsed_output": parsed_json,
                    "reconciled_output": reconciled_json,
                    "response_mode": response_mode,
                    "fallback_reason": fallback_reason,
                    "validation_error": None,
                }
            )
            break
        except Exception as exc:
            last_exc = exc
            planner_attempts.append(
                {
                    "attempt_index": correction_attempt,
                    "prompt": current_prompt,
                    "raw_output": raw_output,
                    "parsed_output": parsed_json,
                    "reconciled_output": reconciled_json,
                    "response_mode": response_mode,
                    "fallback_reason": fallback_reason,
                    "validation_error": str(exc),
                }
            )
            if correction_attempt >= _MAX_CORRECTION_ATTEMPTS:
                break
            current_prompt = _build_refinement_correction_prompt(
                base_prompt=prompt,
                process_text=process_text,
                current_topology_artifact=normalized_topology_artifact,
                current_semantic_sketch_plan=normalized_semantic_plan,
                instruction=instruction,
                invalid_planner_output=raw_output,
                parsed_planner_output=parsed_json,
                validation_error=str(exc),
                correction_attempt=correction_attempt + 1,
            )

    if artifact is None:
        exc = last_exc or ValueError("Refinement planner validation failed")
        raise RefinementPlannerError(
            f"Refinement planner validation failed: {exc}",
            debug_artifacts={
                "process_text": process_text,
                "current_topology_artifact": normalized_topology_artifact,
                "current_semantic_sketch_plan": normalized_semantic_plan,
                "instruction": instruction,
                "planner_prompt": prompt,
                "planner_raw_output": raw_output,
                "planner_parsed_output": parsed_json,
                "planner_invalid_branch_plans": invalid_branch_plans,
                "planner_reconciled_output": reconciled_json,
                "planner_response_mode": response_mode,
                "planner_fallback_reason": fallback_reason,
                "planner_validation_error": str(exc),
                "planner_attempts": planner_attempts,
            },
        ) from exc
    artifact["refinement_trace"] = {"user_instruction": instruction}
    return {
        "prompt": current_prompt,
        "raw_output": raw_output,
        "artifact": artifact,
        "response_mode": response_mode,
        "fallback_reason": fallback_reason,
        "planner_attempts": planner_attempts,
    }


__all__ = [
    "REFINEMENT_PLANNER_SCHEMA",
    "RefinementPlannerError",
    "RefinementPlannerResult",
    "RefinementTrace",
    "build_refinement_planner_prompt",
    "generate_refinement_plan",
    "parse_refinement_planner_json",
    "refinement_planner_response_format",
]
