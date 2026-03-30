from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

StepDataType = Literal["str", "int", "bool", "datetime", "enum"]


class Step3ValidationIssue(BaseModel):
    issue_type: str
    description: str
    suggestion: str | None = None


class Step3CorrectedAttribute(BaseModel):
    name: str
    type: StepDataType
    enum: str | None = None
    derived: bool = False
    description: str | None = None
    body: str | None = None


class Step3CorrectedEntity(BaseModel):
    name: str
    type: Literal["class"] = "class"
    attributes: list[Step3CorrectedAttribute] = Field(default_factory=list)


class Step3CorrectedMultiplicity(BaseModel):
    source: str
    target: str


class Step3CorrectedRelation(BaseModel):
    source: str
    target: str
    type: Literal["association", "composition", "generalization", "dependency"] = (
        "association"
    )
    multiplicity: Step3CorrectedMultiplicity | None = None
    label: str = ""


class Step3ValidationOutput(BaseModel):
    issues_found: list[Step3ValidationIssue] = Field(default_factory=list)
    corrected_entities: list[Step3CorrectedEntity] = Field(default_factory=list)
    corrected_relations: list[Step3CorrectedRelation] = Field(default_factory=list)
