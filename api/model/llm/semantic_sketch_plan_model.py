from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_serializer, model_validator


SemanticBranchIntent = Literal["continue", "terminate", "loop_back"]


class SemanticRootAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slot_id: str
    actions: List["SemanticBranchStep"] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_action_shape(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if "actions" not in normalized:
            action = str(normalized.pop("action", "") or "").strip()
            normalized["actions"] = [{"action": action}] if action else []
        else:
            normalized.pop("action", None)
        return normalized


class SemanticBranchStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    source_action_ids: List[str] = Field(default_factory=list)

    @field_validator("source_action_ids", mode="before")
    @classmethod
    def normalize_source_action_ids(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            return value
        normalized: List[str] = []
        for source_action_id in value:
            if not isinstance(source_action_id, str):
                normalized.append(source_action_id)
                continue
            source_action_id = source_action_id.strip()
            if source_action_id and source_action_id not in normalized:
                normalized.append(source_action_id)
        return normalized

    @model_serializer(mode="wrap")
    def serialize_without_empty_source_action_ids(self, handler):
        data = handler(self)
        if not data.get("source_action_ids"):
            data.pop("source_action_ids", None)
        return data


class SemanticBranchPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    structure_id: str
    branch: str
    intent: SemanticBranchIntent
    steps: List[SemanticBranchStep] = Field(default_factory=list)
    target_slot_id: Optional[str] = None

    @model_serializer(mode="wrap")
    def serialize_without_unset_target(self, handler):
        data = handler(self)
        if data.get("target_slot_id") is None:
            data.pop("target_slot_id", None)
        return data


class SemanticSketchPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root_actions: List[SemanticRootAction] = Field(default_factory=list)
    branch_plans: List[SemanticBranchPlan] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_uniqueness(self, info: ValidationInfo) -> "SemanticSketchPlan":
        root_slots = [entry.slot_id.strip() for entry in self.root_actions]
        if len(root_slots) != len(set(root_slots)):
            raise ValueError("root_actions must use unique slot_id values")

        branch_keys: List[Tuple[str, str]] = [
            (entry.structure_id.strip(), entry.branch.strip())
            for entry in self.branch_plans
        ]
        if len(branch_keys) != len(set(branch_keys)):
            raise ValueError("branch_plans must use unique (structure_id, branch) pairs")

        require_explicit_branch_steps = True
        if isinstance(info.context, dict):
            require_explicit_branch_steps = bool(info.context.get("require_explicit_branch_steps", True))

        if require_explicit_branch_steps:
            missing_semantic_steps = sorted(
                f"{entry.structure_id.strip()}:{entry.branch.strip()}"
                for entry in self.branch_plans
                if entry.intent in {"terminate", "loop_back"} and not entry.steps
            )
            if missing_semantic_steps:
                raise ValueError(
                    "branch_plans with intent `terminate` or `loop_back` must include at least one branch-local "
                    "business action in `steps`; intent is control flow only. "
                    f"missing_steps={missing_semantic_steps}"
                )
        return self


_REQUIRED_BRANCH_STEP_CONDITIONAL: Dict[str, Any] = {
    "if": {
        "properties": {
            "intent": {
                "enum": ["terminate", "loop_back"],
            }
        },
        "required": ["intent"],
    },
    "then": {
        "properties": {
            "steps": {
                "minItems": 1,
            }
        },
        "required": ["steps"],
    },
}


def apply_semantic_branch_plan_schema_constraints(
    schema: Dict[str, Any],
    *,
    include_source_action_ids: bool = True,
) -> Dict[str, Any]:
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        return schema
    branch_plan_schema = defs.get("SemanticBranchPlan")
    if not isinstance(branch_plan_schema, dict):
        return schema

    properties = branch_plan_schema.setdefault("properties", {})
    steps_schema = properties.get("steps")
    if isinstance(steps_schema, dict):
        steps_schema.setdefault("default", [])

    required_fields = branch_plan_schema.setdefault("required", [])
    if "steps" not in required_fields:
        required_fields.append("steps")

    all_of = branch_plan_schema.setdefault("allOf", [])
    if _REQUIRED_BRANCH_STEP_CONDITIONAL not in all_of:
        all_of.append(_REQUIRED_BRANCH_STEP_CONDITIONAL)

    branch_step_schema = defs.get("SemanticBranchStep")
    if isinstance(branch_step_schema, dict):
        required_step_fields = branch_step_schema.setdefault("required", [])
        if include_source_action_ids:
            source_action_ids_schema = branch_step_schema.get("properties", {}).get("source_action_ids")
            if isinstance(source_action_ids_schema, dict):
                source_action_ids_schema.pop("default", None)
            if "source_action_ids" not in required_step_fields:
                required_step_fields.append("source_action_ids")
        else:
            branch_step_schema.get("properties", {}).pop("source_action_ids", None)
            required_step_fields[:] = [
                field for field in required_step_fields if field != "source_action_ids"
            ]
    return schema


def find_invalid_semantic_branch_plans(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    invalid_branch_plans: List[Dict[str, Any]] = []
    branch_plans = payload.get("branch_plans")
    if not isinstance(branch_plans, list):
        return invalid_branch_plans

    for entry in branch_plans:
        if not isinstance(entry, dict):
            continue
        structure_id = str(entry.get("structure_id") or "").strip()
        branch = str(entry.get("branch") or "").strip()
        intent = str(entry.get("intent") or "").strip()
        raw_steps = entry.get("steps")
        normalized_steps: List[Dict[str, str]] = []
        if isinstance(raw_steps, list):
            for step in raw_steps:
                if not isinstance(step, dict):
                    continue
                action = str(step.get("action") or "").strip()
                if action:
                    normalized_steps.append({"action": action})

        parsed_branch_plan: Dict[str, Any] = {
            "structure_id": structure_id,
            "branch": branch,
            "intent": intent,
            "steps": normalized_steps,
        }
        target_slot_id = str(entry.get("target_slot_id") or "").strip()
        if target_slot_id:
            parsed_branch_plan["target_slot_id"] = target_slot_id

        if intent in {"terminate", "loop_back"} and not normalized_steps:
            invalid_branch_plans.append(
                {
                    "structure_id": structure_id,
                    "branch": branch,
                    "intent": intent,
                    "parsed_branch_plan": parsed_branch_plan,
                }
            )

    return invalid_branch_plans


__all__ = [
    "apply_semantic_branch_plan_schema_constraints",
    "find_invalid_semantic_branch_plans",
    "SemanticBranchIntent",
    "SemanticBranchPlan",
    "SemanticBranchStep",
    "SemanticRootAction",
    "SemanticSketchPlan",
]
