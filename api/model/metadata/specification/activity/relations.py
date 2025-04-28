from pydantic import BaseModel, model_validator, ValidationError, field_validator
from typing import Literal, Union, Optional

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
    def validate_condition(cls, values):
        if values.isElse:
            return values
        required_fields = ['target_class', 'target_attribute', 'target_attribute_type', 'operator', 'threshold']
        missing_fields = [field for field in required_fields if not getattr(values, field)]
        if missing_fields:
            raise ValidationError(f"The following fields are required for a condition: {', '.join(missing_fields)}")
        return values
    
    @model_validator(mode="after")
    def set_target_class_name(cls, values):
        if values.target_class:
            values.target_class_name = Node.objects.get(id=values.target_class).cls.data.get("name", "Unknown class")
        return values

class ControlFlow(BaseModel):
    is_directed: bool = True
    guard: str = ""
    weight: str = ""
    condition: Optional[ControlFlowCondition] = None
    type: Literal["controlflow"] = "controlflow"


class ObjectFlow(BaseModel):
    is_directed: bool = True
    guard: str = ""
    weight: str = ""
    cls: str = ""
    type: Literal["objectflow"] = "objectflow"


ActivityRelation = Union[ControlFlow, ObjectFlow]
