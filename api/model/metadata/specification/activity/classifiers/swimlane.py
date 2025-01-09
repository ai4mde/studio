from pydantic import BaseModel
from typing import Literal
from metadata.specification.kernel import NamedElement

class SwimLane(NamedElement, BaseModel):
    type: Literal["swimlane"] = "swimlane"
    role: Literal["swimlane"] = "swimlane"
    height: int = 400
    width: int = 150
    vertical: bool = True

SwimLaneClassifier = SwimLane

__all__ = [
    "SwimLane",
    "SwimLaneClassifier",
]