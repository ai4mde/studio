from __future__ import annotations

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_serializer, model_validator


ControlBlockType = Literal["decision", "loop", "parallel"]


class MainFlowStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str
    action: str


class BranchStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: Optional[str] = None
    action: str


class Branch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    returns_to_main_flow: bool = True
    steps: List[BranchStep] = Field(default_factory=list)
    next_block_id: Optional[str] = None
    child_block_ids: List[str] = Field(default_factory=list)
    reconnect_to_step_id: Optional[str] = None

    @model_serializer(mode="wrap")
    def serialize_without_unset_reconnect(self, handler):
        data = handler(self)
        if data.get("reconnect_to_step_id") is None:
            data.pop("reconnect_to_step_id", None)
        return data


class ControlBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block_id: Optional[str] = None
    type: ControlBlockType
    entry_after: Optional[str] = None
    entry_after_step_id: Optional[str] = None
    branches: List[Branch] = Field(default_factory=list)
    requires_merge: Optional[bool] = None
    exit_to: Optional[str] = None
    exit_to_step_id: Optional[str] = None
    loop_back_to: Optional[str] = None
    loop_back_to_step_id: Optional[str] = None
    loop_back_to_block_id: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def apply_semantic_defaults(self) -> "ControlBlock":
        if self.requires_merge is None:
            self.requires_merge = False if self.type == "loop" else True
        return self

    @model_serializer(mode="wrap")
    def serialize_without_empty_block_loop_target(self, handler):
        data = handler(self)
        if data.get("loop_back_to_block_id") is None:
            data.pop("loop_back_to_block_id", None)
        return data


class ActivitySketch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    main_flow: List[Union[str, MainFlowStep]]
    control_blocks: List[ControlBlock] = Field(default_factory=list)

__all__ = [
    "ActivitySketch",
    "Branch",
    "BranchStep",
    "ControlBlock",
    "MainFlowStep",
    "ValidationError",
]
