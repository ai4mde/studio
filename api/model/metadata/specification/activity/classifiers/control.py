from pydantic import BaseModel
from pydantic.fields import Field
from typing import Annotated, Union, Literal


class Decision(BaseModel):
    type: Literal["decision"] = "decision"
    role: Literal["control"] = "control"
    decisionInput: str = ""
    decisionInputFlow: str = ""
    page: str = ""  # TODO: In reality a page is more complex than just a string


class Final(BaseModel):
    type: Literal["final"] = "final"
    role: Literal["control"] = "control"
    activity_scope: Literal["flow", "activity"] = "activity"


class Fork(BaseModel):
    type: Literal["fork"] = "fork"
    role: Literal["control"] = "control"
    height: int = 8
    width: int = 56


class Initial(BaseModel):
    type: Literal["initial"] = "initial"
    role: Literal["control"] = "control"
    activity_scope: Literal["flow", "activity"] = "activity"
    scheduled: bool = False
    schedule: str = ""


class Join(BaseModel):
    type: Literal["join"] = "join"
    role: Literal["control"] = "control"
    join_spec: str = ""
    height: int = 8
    width: int = 56
    is_combine_duplicate: bool = False


class Merge(BaseModel):
    type: Literal["merge"] = "merge"
    role: Literal["control"] = "control"
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
