from pydantic import BaseModel
from pydantic.fields import Field
from pydantic.types import Annotated, Literal, Union

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


class ClassRelation(BaseModel):
    diagram: Literal["classes"] = "classes"
    data: Annotated[
        Union[Association, Composition, Generalization],
        Field(discriminator="type")
    ]


__all__ = [
    "ClassRelation",
]
