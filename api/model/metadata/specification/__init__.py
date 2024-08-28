from typing import Annotated, Union
from ninja import ModelSchema
from pydantic.fields import Field
from .activity import ActivityClassifier, ActivityRelation
from .classes import ClassClassifier, ClassRelation
from .usecase import UsecaseClassifier, UsecaseRelation

import metadata.models as models

Classifier = Annotated[
    Union[
        ActivityClassifier,
        ClassClassifier,
        UsecaseClassifier,
    ],
    Field(discriminator="type"),
]


class ClassifierSchema(ModelSchema):
    data: Classifier

    class Meta:
        model = models.Classifier
        fields = ["id", "data"]


Relation = Annotated[
    Union[
        ActivityRelation,
        ClassRelation,
        UsecaseRelation,
    ],
    Field(discriminator="type"),
]


class RelationSchema(ModelSchema):
    class Meta:
        model = models.Relation
        fields = ["id", "data", "source", "target"]


__all__ = [
    "Classifier",
    "ClassifierSchema",
    "Relation",
    "RelationSchema",
]
