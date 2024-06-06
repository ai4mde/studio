from pydantic import BaseModel
from pydantic.fields import Field
from typing import Literal, Annotated, Union

from metadata.specification.kernel import Multiplicity, NamedElement, NamespacedElement


class Buffer(NamedElement, NamespacedElement, BaseModel):
    type: Literal["buffer"] = "buffer"
    role: Literal["object"] = "object"


class Pin(NamedElement, NamespacedElement, Multiplicity, BaseModel):
    type: Literal["pin"] = "pin"
    role: Literal["object"] = "object"


ObjectClassifier = Annotated[
    Union[
        Buffer,
        Pin,
    ],
    Field(
        discriminator="type",
    ),
]

__all__ = [
    "Buffer",
    "Pin",
    "ObjectClassifier",
]
