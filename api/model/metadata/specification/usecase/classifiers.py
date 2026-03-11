from pydantic import BaseModel
from typing import Union, Literal
from metadata.specification.kernel import NamedElement, NamespacedElement, ParentNode


class Actor(NamedElement, ParentNode, BaseModel):
    type: Literal["actor"] = "actor"


class Usecase(NamedElement, NamespacedElement, ParentNode, BaseModel):
    type: Literal["usecase"] = "usecase"
    precondition: str = ""
    postcondition: str = ""
    trigger: str = ""  # TODO: Event
    scenarios: list[str] = []
    activities: list[
        str
    ] = []  # TODO: Links to activity, i.e. list of { id: '', type: 'action', ... }
    actions: list[
        str
    ] = []  # TODO: Links to action, i.e. list of { id: '', type: 'action', ... }
    classes: list[
        str
    ] = []  # TODO: Links to class, i.e. list of { id: '', type: 'action', ... }
    application_model: list[
        str
    ] = (
        []
    )  # TODO: Links to application model, i.e. list of { id: '', type: 'action', ... }


class SystemBoundary(NamedElement, BaseModel):
    type: Literal["system_boundary"] = "system_boundary"
    height: int = 1000
    width: int = 1000


UsecaseClassifier = Union[Actor, Usecase, SystemBoundary]

__all__ = [
    "UsecaseClassifier",
]
