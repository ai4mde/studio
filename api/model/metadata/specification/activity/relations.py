from pydantic import BaseModel
from typing import Literal, Union


class ControlFlow(BaseModel):
    is_directed: bool = True
    guard: str = ""
    weight: str = ""
    type: Literal["controlflow"] = "controlflow"


class ObjectFlow(BaseModel):
    is_directed: bool = True
    guard: str = ""
    weight: str = ""
    cls: str = ""
    type: Literal["objectflow"] = "objectflow"


ActivityRelation = Union[ControlFlow, ObjectFlow]
