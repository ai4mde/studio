from pydantic import BaseModel, model_validator
from typing import Literal, Optional
from metadata.specification.kernel import Operation, NamespacedElement, NamedElement
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


class ActionClasses(BaseModel):
    input: list[str] = []  # TODO: Should refer to an existing class with uuid
    output: list[str] = []  # TODO: Should refer to an existing class with uuid

    @model_validator(mode="before")
    @classmethod
    def coerce_list(cls, v):
        if isinstance(v, list):
            return {"input": v, "output": []}
        return v


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
            values.actorNodeName = resolve_actor_name(values.actorNode)
        return values

ActionClassifier = Action

__all__ = [
    "Action",
    "ActionClassifier",
]
