from pydantic import BaseModel
from typing import Union, Literal, Optional

DataType = Literal["str", "int", "bool", "datetime", "enum"]


class Attribute(BaseModel):
    name: str
    type: DataType
    enum: Optional[str]
    derived: bool = False
    description: Optional[str] = None
    body: Optional[str] = None

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
    description: str = ""
    type: DataType
    body: str = ""


class RelationMultiplicity(BaseModel):
    source: str # TODO: Multiplicity
    target: str # TODO: Multiplicity


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
