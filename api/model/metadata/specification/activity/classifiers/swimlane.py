from pydantic import BaseModel
from pydantic.fields import Field
from typing import Annotated, Literal, Optional, List, Union, Dict, Any

class SwimLane(BaseModel):
    type: Literal["swimlane"] = "swimlane"
    role: Literal["swimlane"] = "swimlane"
    actorNode: str
    height: int = 400
    width: int = 150
    vertical: bool = True
    actorNodeName: Optional[str] = ""

class SwimLaneGroup(BaseModel):
    type: Literal["swimlanegroup"] = "swimlanegroup"
    role: Literal["swimlane"] = "swimlane"
    swimlanes: List[SwimLane]

SwimLaneClassifier = Annotated[
    Union[
        SwimLane,
        SwimLaneGroup,
    ],
    Field(
        discriminator="type",
    )
]
SwimLaneGroupClassifier = SwimLaneGroup

__all__ = [
    "SwimLane",
    "SwimLaneGroup",
    "SwimLaneClassifier",
]