from pydantic import BaseModel
from typing import Literal, Optional

class SwimLane(BaseModel):
    type: Literal["swimlane"] = "swimlane"
    role: Literal["swimlane"] = "swimlane"
    actorNode: str
    height: int = 400
    width: int = 150
    vertical: bool = True
    actorNodeName: Optional[str] = ""

SwimLaneClassifier = SwimLane

__all__ = [
    "SwimLane",
    "SwimLaneClassifier",
]