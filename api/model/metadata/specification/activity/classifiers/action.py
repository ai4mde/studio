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
    isAutomatic: bool = False
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
    def set_actor_node_name(self):
        if not getattr(self, "actorNode", None):
            self.actorNodeName = "Unknown actor"
            return self

        node = Node.objects.filter(id=self.actorNode).only("cls").first()
        if not node:
            self.actorNodeName = "Unknown actor"
            return self

        self.actorNodeName = node.cls.data.get("name", "Unknown actor") if node.cls else "Unknown actor"
        return self


ActionClassifier = Action

__all__ = [
    "Action",
    "ActionClassifier",
]