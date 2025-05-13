from typing import Literal, Union
from metadata.specification.base import RelationBase


class ControlFlow(RelationBase):
    is_directed: bool = True
    guard: str = ""
    weight: str = ""
    type: Literal["controlflow"] = "controlflow"


class ObjectFlow(RelationBase):
    is_directed: bool = True
    guard: str = ""
    weight: str = ""
    cls: str = ""
    type: Literal["objectflow"] = "objectflow"


ActivityRelation = Union[ControlFlow, ObjectFlow]
