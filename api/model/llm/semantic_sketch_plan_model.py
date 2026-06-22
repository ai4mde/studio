from __future__ import annotations

from typing import List, Literal, Tuple

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class SemanticSketchPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root_actions: List[SemanticRootAction] = Field(default_factory=list)
    branch_plans: List[SemanticBranchPlan] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_uniqueness(self) -> "SemanticSketchPlan":
        root_slots = [entry.slot_id.strip() for entry in self.root_actions]
        if len(root_slots) != len(set(root_slots)):
            raise ValueError("root_actions must use unique slot_id values")

        branch_keys: List[Tuple[str, str]] = [
            (entry.structure_id.strip(), entry.branch.strip())
            for entry in self.branch_plans
        ]
        if len(branch_keys) != len(set(branch_keys)):
            raise ValueError("branch_plans must use unique (structure_id, branch) pairs")
        return self


__all__ = [
    "SemanticBranchIntent",
    "SemanticBranchPlan",
    "SemanticBranchStep",
    "SemanticRootAction",
    "SemanticSketchPlan",
]
