from pydantic import BaseModel, model_validator
from typing import Literal, Optional
from metadata.specification.kernel import Operation, NamespacedElement, NamedElement
from diagram.models import Node


class ActionClasses(BaseModel):
    input: list[str] = []  # TODO: Should refer to an existing class with uuid
    output: list[str] = []  # TODO: Should refer to an existing class with uuid


class Action(NamedElement, NamespacedElement, BaseModel):
    type: Literal["action"] = "action"
    role: Literal["action"] = "action"
    isAutomatic: bool
    customCode: Optional[str] = None
    localPrecondition: Optional[str] = ""
    localPostcondition: Optional[str] = ""
    body: Optional[str] = ""
    operation: Optional[Operation] = None
    publish: Optional[list[str]] = None  # TODO: Should refer to an event
    subscribe: Optional[list[str]] = None  # TODO: Should refer to an event
    classes: Optional[ActionClasses] = None
    application_models: Optional[list[str]] = None  # TODO: Should refer to an application model
    page: Optional[str] = None  # TODO: In reality a page is more complex than just a string
    actorNode: Optional[str] = None
    actorNodeName: Optional[str] = None

    @model_validator(mode="after")
    def set_actor_node_name(cls, values):
        if values.actorNode:
            values.actorNodeName = Node.objects.get(id=values.actorNode).cls.data.get("name", "Unknown actor")
        return values

ActionClassifier = Action

__all__ = [
    "Action",
    "ActionClassifier",
]