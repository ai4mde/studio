from pydantic import BaseModel
from pydantic.fields import Field
from pydantic.types import Annotated, Literal, Union

from metadata.specification.kernel import NamedElement, NamespacedElement


class Actor(NamedElement, BaseModel):
    type: Literal["actor"] = "actor"

class Usecase(NamedElement, NamespacedElement, BaseModel):
    type: Literal["usecase"] = "usecase"
    precondition: str = ""
    postcondition: str = ""
    trigger: str = "" # TODO: Event
    scenarios: list[str] = []
    activities: list[str] = [] # TODO: Links to activity, i.e. list of { id: '', type: 'action', ... }
    actions: list[str] = [] # TODO: Links to action, i.e. list of { id: '', type: 'action', ... }
    classes: list[str] = [] # TODO: Links to class, i.e. list of { id: '', type: 'action', ... }
    application_model: list[str] = [] # TODO: Links to application model, i.e. list of { id: '', type: 'action', ... }

class UsecaseClassifier(BaseModel):
    diagram: Literal["usecase"] = "usecase"
    data: Annotated[
        Union[Actor, Usecase],
        Field(discriminator="type")
    ]

__all__ = [
    "UsecaseClassifier",
]
