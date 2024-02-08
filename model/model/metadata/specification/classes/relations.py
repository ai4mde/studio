from pydantic import BaseModel
from typing import Literal, Optional, Union

from metadata.specification.kernel import RelationMultiplicity, RelationLabels


class Association(BaseModel):
    type: Literal["association"] = "association"
    derived: bool = False
    multiplicity: Optional[RelationMultiplicity] = None
    labels: Optional[RelationLabels] = None
    label: str


class Composition(BaseModel):
    type: Literal["composition"] = "composition"
    multiplicity: Optional[RelationMultiplicity] = None
    labels: Optional[RelationLabels] = None
    label: str = ""


class Generalization(BaseModel):
    type: Literal["generalization"] = "generalization"

class Dependency(BaseModel):
    type: Literal["dependency"] = "dependency"
    label: str = ""


ClassRelation = Union[Association, Composition, Generalization, Dependency]


__all__ = [
    "ClassRelation",
]
