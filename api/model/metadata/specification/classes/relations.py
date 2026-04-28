from typing import Literal, Optional, Union

from metadata.specification.base import RelationBase
from metadata.specification.kernel import RelationLabels, RelationMultiplicity


class Association(RelationBase):
    type: Literal["association"] = "association"
    derived: bool = False
    multiplicity: Optional[RelationMultiplicity] = None
    labels: Optional[RelationLabels] = None
    label: str


class Composition(RelationBase):
    type: Literal["composition"] = "composition"
    multiplicity: Optional[RelationMultiplicity] = None
    labels: Optional[RelationLabels] = None
    label: str = ""


class Generalization(RelationBase):
    type: Literal["generalization"] = "generalization"

class Dependency(RelationBase):
    type: Literal["dependency"] = "dependency"
    label: str = ""


ClassRelation = Union[Association, Composition, Generalization, Dependency]


__all__ = [
    "ClassRelation",
]
