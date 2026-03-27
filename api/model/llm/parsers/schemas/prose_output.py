from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

DataType = Literal["str", "int", "bool", "datetime", "enum"]


class ProseAttribute(BaseModel):
    name: str
    type: DataType
    enum: str | None = None
    derived: bool = False
    description: str | None = None
    body: str | None = None


class ProseMultiplicity(BaseModel):
    source: str
    target: str


class ProseClassifier(BaseModel):
    name: str
    type: Literal["class"] = "class"
    attributes: list[ProseAttribute] = Field(default_factory=list)


class ProseRelation(BaseModel):
    source: str
    target: str
    type: Literal["association", "composition", "generalization", "dependency"] = (
        "association"
    )
    multiplicity: ProseMultiplicity | None = None


class ProseGenerationOutput(BaseModel):
    classifiers: list[ProseClassifier]
    relations: list[ProseRelation] = Field(default_factory=list)
