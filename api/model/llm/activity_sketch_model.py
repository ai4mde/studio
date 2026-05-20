from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


ControlBlockType = Literal["decision", "loop", "parallel"]


class Branch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    returns_to_main_flow: bool = True


class ControlBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ControlBlockType
    entry_after: Optional[str] = None
    branches: List[Branch] = Field(default_factory=list)
    requires_merge: Optional[bool] = None
    exit_to: Optional[str] = None
    loop_back_to: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def apply_semantic_defaults(self) -> "ControlBlock":
        if self.requires_merge is None:
            self.requires_merge = False if self.type == "loop" else True
        return self


class ActivitySketch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    main_flow: List[str]
    control_blocks: List[ControlBlock] = Field(default_factory=list)


__all__ = ["ActivitySketch", "Branch", "ControlBlock", "ValidationError"]
