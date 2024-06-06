from pydantic import BaseModel
from typing import Literal
from metadata.specification.kernel import Operation, NamespacedElement, NamedElement


class ActionClasses(BaseModel):
    input: list[str] = []  # TODO: Should refer to an existing class with uuid
    output: list[str] = []  # TODO: Should refer to an existing class with uuid


class Action(NamedElement, NamespacedElement, BaseModel):
    type: Literal["action"] = "action"
    role: Literal["action"] = "action"
    localPrecondition: str = ""
    localPostcondition: str = ""
    body: str = ""
    operation: Operation
    publish: list[str] = []  # TODO: Should refer to an event
    subscribe: list[str] = []  # TODO: Should refer to an event
    classes: ActionClasses = ActionClasses(input=[], output=[])
    application_models: list[str] = []  # TODO: Should refer to an application model
    page: str = ""  # TODO: In reality a page is more complex than just a string


ActionClassifier = Action

__all__ = [
    "Action",
    "ActionClassifier",
]
