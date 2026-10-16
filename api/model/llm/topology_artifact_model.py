from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


TopologyStructureType = Literal["decision", "loop", "parallel"]


class TopologyStructure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: TopologyStructureType
    parent: str
    parent_branch: Optional[str] = None
    branches: List[str] = Field(default_factory=list)
    purpose: Optional[str] = None

    @model_validator(mode="after")
    def validate_topology_shape(self) -> "TopologyStructure":
        self.parent = str(self.parent).strip()
        if self.parent_branch is not None:
            self.parent_branch = str(self.parent_branch).strip() or None
        self.branches = [str(branch).strip() for branch in self.branches if str(branch).strip()]

        if not self.parent:
            raise ValueError("parent must not be empty")
        if self.parent == "ROOT" and self.parent_branch is not None:
            raise ValueError("root-level structures must not declare parent_branch")
        if self.parent != "ROOT" and self.parent_branch is None:
            raise ValueError("nested structures must declare parent_branch")
        if len(self.branches) < 2:
            raise ValueError("control structures must declare at least two branch handles")
        if len(set(self.branches)) != len(self.branches):
            raise ValueError("branch handles must be unique within a structure")
        return self


class TopologyArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    structures: List[TopologyStructure] = Field(default_factory=list)


__all__ = [
    "TopologyArtifact",
    "TopologyStructure",
    "TopologyStructureType",
]
