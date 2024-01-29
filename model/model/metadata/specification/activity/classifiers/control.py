from pydantic import BaseModel
from pydantic.fields import Literal
from pydantic.types import Annotated, Union, Field

class Decision(BaseModel):
    type: Literal["decision"] = "decision"
    role: Literal["control"] = "control"
    decisionInput: str = ""
    decisionInputFlow: str = ""
    page: str = "" # TODO: In reality a page is more complex than just a string

class Final(BaseModel):
    type: Literal["final"] = "final"
    role: Literal["control"] = "control"
    activity_scope: Literal["flow", "activity"] = "activity"

class Fork(BaseModel):
    type: Literal["fork"] = "fork"
    role: Literal["control"] = "control"

class Initial(BaseModel):
    type: Literal["initial"] = "initial"
    role: Literal["control"] = "control"
    activity_scope: Literal["flow", "activity"] = "activity"

class Join(BaseModel):
    type: Literal["join"] = "join"
    role: Literal["control"] = "control"
    join_spec: str = ""
    is_combine_duplicate: bool = False

class Merge(BaseModel):
    type: Literal["merge"] = "merge"
    role: Literal["control"] = "control"
    merge_spec: str = ""
    is_combine_duplicate: bool = False
    page: str = "" # TODO: In reality a page is more complex than just a string

ControlClassifier = Annotated[
    Union[
        Decision, Final, Fork, Initial, Join, Merge,
    ],
    Field(
        discriminator="type",
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
