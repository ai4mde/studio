from pydantic import BaseModel, field_validator
from pydantic.fields import Field
from typing import Annotated, Union, Literal, List
from diagram.models import Node
from metadata.models import Classifier


def resolve_actor_name(actor_node_id: str) -> str:
    node = Node.objects.filter(id=actor_node_id).select_related("cls").first()
    if node:
        return node.cls.data.get("name", "Unknown actor")

    actor = Classifier.objects.filter(id=actor_node_id, data__type="actor").first()
    if actor:
        return actor.data.get("name", "Unknown actor")

    return "Unknown actor"


class SwimLane(BaseModel):
    type: Literal["swimlane"] = "swimlane"
    role: Literal["swimlane"] = "swimlane"
    actorNode: str
    actorNodeName: str = "Unknown actor"

    @field_validator("actorNodeName", mode="before")
    @classmethod
    def resolve_actorNodeName(cls, value, values):
        actor_node_id = values.data.get("actorNode")
        if actor_node_id:
            return resolve_actor_name(actor_node_id)
        return "Unknown actor"


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
