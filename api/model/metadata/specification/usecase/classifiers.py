from pydantic import BaseModel
from typing import Union, Literal
from metadata.specification.kernel import NamedElement, NamespacedElement


class Actor(NamedElement, BaseModel):
    type: Literal["actor"] = "actor"


class Usecase(NamedElement, NamespacedElement, BaseModel):
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


UsecaseClassifier = Union[Actor, Usecase]

__all__ = [
    "UsecaseClassifier",
]
