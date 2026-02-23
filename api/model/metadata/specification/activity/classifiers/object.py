from uuid import UUID
from typing import Literal, Optional
from pydantic import BaseModel, model_validator

from diagram.models import Node
from metadata.specification.kernel import NamedElement, NamespacedElement

class Object(NamedElement, NamespacedElement, BaseModel):
    type: Literal["object"] = "object"
    role: Literal["object"] = "object"
    cls: UUID
    state: Optional[str] = None
    actorNode: Optional[str] = None
    actorNodeName: Optional[str] = None

    @model_validator(mode="after")
    def set_actor_node_name(cls, values):
        if values.actorNode:
            values.actorNodeName = Node.objects.get(id=values.actorNode).cls.data.get("name", "Unknown actor")
        return values
    
ObjectClassifier = Object

__all__ = ["ObjectClassifier"]
