from pydantic import BaseModel, model_validator
from typing import Literal, Union, Optional
from metadata.specification.base import RelationBase

from diagram.models import Node

class ControlFlowCondition(BaseModel):
    isElse: bool
    target_class: Optional[str] = None
    target_attribute: Optional[str] = None
    target_attribute_type: Optional[str] = None
    operator: Optional[str] = None
    aggregator: Optional[str] = None
    threshold: Optional[str] = None
    target_class_name: Optional[str] = None

    @model_validator(mode="after")
    def set_target_class_name(self):
        if self.target_class:
            self.target_class_name = Node.objects.get(id=self.target_class).cls.data.get("name", "Unknown class")
        return self

class ControlFlow(RelationBase):
    is_directed: bool = True
    guard: str = ""
    weight: str = ""
    condition: Optional[ControlFlowCondition] = None
    type: Literal["controlflow"] = "controlflow"


class ObjectFlow(RelationBase):
    is_directed: bool = True
    guard: str = ""
    weight: str = ""
    cls: str = ""
    type: Literal["objectflow"] = "objectflow"


ActivityRelation = Union[ControlFlow, ObjectFlow]
