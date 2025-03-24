from pydantic import BaseModel, field_validator
from pydantic.fields import Field
from typing import Annotated, Union, Literal, List
from diagram.models import Node


class SwimLane(BaseModel):
    type: Literal["swimlane"] = "swimlane"
    role: Literal["swimlane"] = "swimlane"
    actorNode: str
    actorNodeName: str = "Unknown actor"

    @field_validator("actorNodeName", mode="before")
    @classmethod
    def resolve_actorNodeName(cls, value, values):
        actor_node_id = values.data.get("actorNode")
        if actor_node_id and Node.objects.filter(id=actor_node_id).exists():
            return Node.objects.get(id=actor_node_id).cls.data.get("name", "Unknown actor")
        return "Unknown actor"


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