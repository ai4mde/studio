from pydantic import BaseModel
from typing import Union, Literal

DataType = Literal["str", "int", "bool", "datetime"]


class Attribute(BaseModel):
    name: str
    type: DataType
    derived: bool = False


class Multiplicity(BaseModel):
    is_ordered: bool = False
    is_unique: bool = False
    lower: int = 1
    upper: Union[Literal["*"], int] = "*"


class NamedElement(BaseModel):
    name: str


class NamespacedElement(BaseModel):
    namespace: str = ""


class Operation(BaseModel):
    name: str
    type: DataType
    body: str = ""


class RelationMultiplicity(BaseModel):
    source: Multiplicity
    target: Multiplicity


class RelationLabels(BaseModel):
    source: str = ""
    target: str = ""


__all__ = [
    "DataType",
    "Attribute",
    "Multiplicity",
    "NamedElement",
    "NamespacedElement",
    "Operation",
    "RelationMultiplicity",
    "RelationLabels",
]
