from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RelationDirection = Literal["outgoing", "incoming"]


class ExistingMethodInfo(BaseModel):
    class_name: str
    method_name: str
    description: str = ""
    body: str = ""
    return_type: str | None = None


class RelatedClassInfo(BaseModel):
    class_name: str
    relation_type: str = "association"
    direction: RelationDirection
    multiplicity_source: str | None = None
    multiplicity_target: str | None = None
    attributes: list[dict] = Field(default_factory=list)
    methods: list[dict] = Field(default_factory=list)


class RetrievalContext(BaseModel):
    target_class_name: str
    target_class_attributes: list[dict] = Field(default_factory=list)
    related_classes: list[RelatedClassInfo] = Field(default_factory=list)
    existing_methods: list[ExistingMethodInfo] = Field(default_factory=list)

    def to_template_dict(self) -> dict:
        return self.model_dump()
