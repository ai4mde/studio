from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

StepDataType = Literal["str", "int", "bool", "datetime", "enum"]


class Step1EntityAttribute(BaseModel):
    name: str
    type: StepDataType
    description: str | None = None


class Step1Entity(BaseModel):
    name: str
    type: Literal["class"] = "class"
    attributes: list[Step1EntityAttribute] = Field(default_factory=list)
    description: str | None = None


class Step1EntitiesOutput(BaseModel):
    entities: list[Step1Entity] = Field(default_factory=list)
