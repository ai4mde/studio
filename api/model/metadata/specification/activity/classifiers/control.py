from pydantic import BaseModel
from pydantic.fields import Field
from typing import Annotated, Union, Literal


class Decision(BaseModel):
    type: Literal["control"] = "control"
    subtype: Literal["decision"] = "decision"
    decisionInput: str = ""
    decisionInputFlow: str = ""
    page: str = ""  # TODO: In reality a page is more complex than just a string


class Final(BaseModel):
    type: Literal["control"] = "control"
    subtype: Literal["final"] = "final"
    activity_scope: Literal["flow", "activity"] = "activity"


class Fork(BaseModel):
    type: Literal["control"] = "control"
    subtype: Literal["fork"] = "fork"
    height: int = 8
    width: int = 56


class Initial(BaseModel):
    type: Literal["control"] = "control"
    subtype: Literal["initial"] = "initial"
    activity_scope: Literal["flow", "activity"] = "activity"
    scheduled: bool = False
    schedule: str = ""


class Join(BaseModel):
    type: Literal["control"] = "control"
    subtype: Literal["join"] = "join"
    join_spec: str = ""
    height: int = 8
    width: int = 56
    is_combine_duplicate: bool = False


class Merge(BaseModel):
    type: Literal["control"] = "control"
    subtype: Literal["merge"] = "merge"
    merge_spec: str = ""
    is_combine_duplicate: bool = False
    page: str = ""  # TODO: In reality a page is more complex than just a string


ControlClassifier = Annotated[
    Union[
        Decision,
        Final,
        Fork,
        Initial,
        Join,
        Merge,
    ],
    Field(
        discriminator="subtype",
    ),
]

__all__ = [
    "Decision",
    "Final",
    "Fork",
    "Initial",
    "Join",
    "Merge",
    "ControlClassifier",
]
