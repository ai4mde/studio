from pydantic import BaseModel
from typing import Literal, Union

from metadata.specification.kernel import RelationMultiplicity, RelationLabels


class Association(BaseModel):
    type: Literal["association"] = "association"
    derived: bool = False
    multiplicity: RelationMultiplicity
    labels: RelationLabels


class Composition(BaseModel):
    type: Literal["composition"] = "composition"
    multiplicity: RelationMultiplicity
    labels: RelationLabels


class Generalization(BaseModel):
    type: Literal["generalization"] = "generalization"
    labels: RelationLabels


ClassRelation = Union[Association, Composition, Generalization]


__all__ = [
    "ClassRelation",
]
