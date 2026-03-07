from pydantic import BaseModel#, Field
from typing import Literal, List, Union

from metadata.specification.kernel import NamedElement

class InternalsElement(BaseModel):
    internals: List[NamedElement] = []

class System(InternalsElement, NamedElement, BaseModel):
    type: Literal["system"] = "system"


class Container(InternalsElement, NamedElement, BaseModel):
    type: Literal["container"] = "container"


class Component(InternalsElement, NamedElement, BaseModel):
    type: Literal["component"] = "component" 

class Interface(NamedElement, BaseModel):
    type: Literal['interface']

ComponentClassifier = Union[
    System,
    Container,
    Component,
    Interface,
]
