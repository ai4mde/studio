from uuid import UUID
from pydantic import BaseModel, model_validator
from typing import Literal, List, Optional, Union

from metadata.models import Classifier
from metadata.specification.kernel import NamedElement

class Internal(BaseModel):
    name: str
    type: UUID
    typeName: Optional[str] = None

    @model_validator(mode="after")
    def set_type_name(self):
        try:
            classifier = Classifier.objects.get(pk=self.type)
            self.typeName = classifier.data.get("name", "Unknown type")
        except Classifier.DoesNotExist:
            self.typeName = "Unknown type"
        return self


class InternalsElement(BaseModel):
    internals: List[Internal] = []


class System(InternalsElement, NamedElement, BaseModel):
    type: Literal["system"] = "system"


class Container(InternalsElement, NamedElement, BaseModel):
    type: Literal["container"] = "container"


class Component(InternalsElement, NamedElement, BaseModel):
    type: Literal["component"] = "component"


class Interface(NamedElement, BaseModel):
    type: Literal["interface"] = "interface"


ComponentClassifier = Union[
    System,
    Container,
    Component,
    Interface,
]