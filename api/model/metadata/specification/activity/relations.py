from pydantic import BaseModel
from typing import Literal, Union


class PositionHandlers(BaseModel):
    x: int
    y: int


class ControlFlow(BaseModel):
    is_directed: bool = True
    guard: str = ""
    weight: str = ""
    position_handlers: list[PositionHandlers]
    type: Literal["controlflow"] = "controlflow"


class ObjectFlow(BaseModel):
    is_directed: bool = True
    guard: str = ""
    weight: str = ""
    cls: str = ""
    type: Literal["objectflow"] = "objectflow"


ActivityRelation = Union[ControlFlow, ObjectFlow]
