from __future__ import annotations

from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, model_serializer, model_validator


SemanticBranchIntent = Literal["continue", "terminate", "loop_back"]


class SemanticRootAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slot_id: str
    action: str


class SemanticBranchStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str


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


__all__ = [
    "SemanticBranchIntent",
    "SemanticBranchPlan",
    "SemanticBranchStep",
    "SemanticRootAction",
    "SemanticSketchPlan",
]
