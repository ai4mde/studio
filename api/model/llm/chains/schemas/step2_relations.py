from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Step2Multiplicity(BaseModel):
    source: str
    target: str


class Step2Relation(BaseModel):
    source: str
    target: str
    type: Literal["association", "composition", "generalization", "dependency"] = (
        "association"
    )
    multiplicity: Step2Multiplicity | None = None
    label: str = ""
    reasoning: str | None = None


class Step2RelationsOutput(BaseModel):
    relations: list[Step2Relation] = Field(default_factory=list)
