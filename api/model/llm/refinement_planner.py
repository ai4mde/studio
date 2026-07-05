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
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .handler import call_openai
from .semantic_sketch_plan_model import (
    SemanticSketchPlan,
)
from .topology_artifact_model import TopologyArtifact, TopologyStructure

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

logger = logging.getLogger(__name__)


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


REFINEMENT_PLANNER_SCHEMA: Dict[str, Any] = RefinementPlannerResult.model_json_schema()


class RefinementPlannerError(Exception):
    def __init__(self, message: str, *, debug_artifacts: Dict[str, Any]) -> None:
        super().__init__(message)
        self.debug_artifacts = debug_artifacts


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
- If the instruction explicitly asks to add, insert, create, or rename an activity, action, or task, model exactly one business action in semantics unless the instruction explicitly requests a decision, loop, parallel block, branch, or other control-flow structure
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
    has_existing_loop_back = any(
        preserved_branch_plan_map.get(branch_key) is not None
        and preserved_branch_plan_map[branch_key].intent == "loop_back"
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


def _reconcile_semantic_plan_to_topology(
    *,
    updated_topology_artifact: Dict[str, Any] | TopologyArtifact,
    updated_semantic_sketch_plan: Dict[str, Any] | SemanticSketchPlan,
    current_semantic_sketch_plan: Dict[str, Any] | SemanticSketchPlan,
) -> Dict[str, Any]:
    topology = TopologyArtifact.model_validate(updated_topology_artifact)
    updated_semantics = SemanticSketchPlan.model_validate(updated_semantic_sketch_plan)
    current_semantics = SemanticSketchPlan.model_validate(current_semantic_sketch_plan)

    updated_root_action_map = {
        entry.slot_id.strip(): entry.action
        for entry in updated_semantics.root_actions
    }
    current_root_action_map = {
        entry.slot_id.strip(): entry.action
        for entry in current_semantics.root_actions
    }
    reconciled_root_actions: List[Dict[str, str]] = []
    for index, slot_id in enumerate(_expected_root_slot_ids(topology), start=1):
        action = (
            updated_root_action_map.get(slot_id)
            or current_root_action_map.get(slot_id)
            or f"root_scope_{index}"
        )
        reconciled_root_actions.append(
            {
                "slot_id": slot_id,
                "action": str(action).strip() or f"root_scope_{index}",
            }
        )

    updated_branch_plan_map = {
        (entry.structure_id.strip(), entry.branch.strip()): entry
        for entry in updated_semantics.branch_plans
    }
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
            branch_plan = preserved_branch_plan_map.get(branch_key)
            if branch_plan is not None:
                reconciled_branch_plans.append(branch_plan.model_dump(mode="json"))
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
    return reconciled.model_dump(mode="json")


def _reconcile_refinement_planner_payload(
    parsed_json: Dict[str, Any],
    *,
    current_semantic_sketch_plan: Dict[str, Any] | SemanticSketchPlan,
) -> Dict[str, Any]:
    updated_topology = parsed_json.get("updated_topology_artifact", {})
    updated_semantics = parsed_json.get("updated_semantic_sketch_plan", {})
    parsed_json["updated_semantic_sketch_plan"] = _reconcile_semantic_plan_to_topology(
        updated_topology_artifact=updated_topology,
        updated_semantic_sketch_plan=updated_semantics,
        current_semantic_sketch_plan=current_semantic_sketch_plan,
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
    parsed_json = json.loads(raw_output)
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
    try:
        parsed_json = json.loads(raw_output)
        reconciled_json = _reconcile_refinement_planner_payload(
            parsed_json,
            current_semantic_sketch_plan=normalized_semantic_plan,
        )
        artifact = RefinementPlannerResult.model_validate(reconciled_json).model_dump(mode="json")
    except Exception as exc:
        raise RefinementPlannerError(
            f"Refinement planner validation failed: {exc}",
            debug_artifacts={
                "process_text": process_text,
                "current_topology_artifact": normalized_topology_artifact,
                "current_semantic_sketch_plan": normalized_semantic_plan,
                "instruction": instruction,
                "planner_prompt": prompt,
                "planner_raw_output": raw_output,
                "planner_reconciled_output": (
                    reconciled_json if "reconciled_json" in locals() else None
                ),
                "planner_response_mode": response_mode,
                "planner_fallback_reason": fallback_reason,
                "planner_validation_error": str(exc),
            },
        ) from exc
    artifact["refinement_trace"] = {"user_instruction": instruction}
    return {
        "prompt": prompt,
        "raw_output": raw_output,
        "artifact": artifact,
        "response_mode": response_mode,
        "fallback_reason": fallback_reason,
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
