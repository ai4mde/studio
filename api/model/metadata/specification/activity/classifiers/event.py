from uuid import UUID
from typing import Literal, Optional
from pydantic import BaseModel, model_validator

from diagram.models import Node
from metadata.specification.kernel import NamedElement, NamespacedElement

class Event(NamedElement, NamespacedElement, BaseModel):
    type: Literal["event"] = "event"
    signal: UUID
    subtype: Literal["raised"] = "raised"
    actorNode: Optional[str] = None
    actorNodeName: Optional[str] = None

    @model_validator(mode="after")
    def set_actor_node_name(cls, values):
        if values.actorNode:
            values.actorNodeName = Node.objects.get(id=values.actorNode).cls.data.get("name", "Unknown actor")
        return values
    
EventClassifier = Event

__all__ = ["EventClassifier"]