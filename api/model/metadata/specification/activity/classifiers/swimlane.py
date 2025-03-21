from pydantic import BaseModel
from pydantic.fields import Field
from typing import Annotated, Union, Literal, List


class SwimLane(BaseModel):
    type: Literal["swimlane"] = "swimlane"
    role: Literal["swimlane"] = "swimlane"
    actorNode: str
    actorNodeName: str


class SwimLaneGroup(BaseModel):
    type: Literal["swimlanegroup"] = "swimlanegroup"
    role: Literal["swimlane"] = "swimlane"
    height: int = 1000
    width: int = 300
    horizontal: bool = False
    swimlanes: List[SwimLane]


SwimLaneClassifier = Annotated[
    Union[
        SwimLane,
        SwimLaneGroup,
    ],
    Field(
        discriminator="type",
    ),
]


__all__ = [
    "SwimLaneGroup",
    "SwimLaneClassifier",
]