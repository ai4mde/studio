from pydantic import BaseModel, field_validator
from pydantic.fields import Field
from typing import Annotated, Union, Literal, List
from metadata.specification.activity.classifiers.actor_resolution import UNKNOWN_ACTOR, resolve_actor_name


class SwimLane(BaseModel):
    type: Literal["swimlane"] = "swimlane"
    role: Literal["swimlane"] = "swimlane"
    actorNode: str
    actorNodeName: str = UNKNOWN_ACTOR

    @field_validator("actorNodeName", mode="before")
    @classmethod
    def resolve_actorNodeName(cls, value, values):
        actor_node_id = values.data.get("actorNode")
        if actor_node_id:
            return resolve_actor_name(actor_node_id)
        return UNKNOWN_ACTOR


class SwimLaneGroup(BaseModel):
    type: Literal["swimlanegroup"] = "swimlanegroup"
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
