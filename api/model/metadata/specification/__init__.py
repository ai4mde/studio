from uuid import UUID
from typing import Annotated, Union, Optional
from ninja import ModelSchema
from pydantic.fields import Field
from .activity import ActivityClassifier, ActivityRelation
from .classes import ClassClassifier, ClassRelation
from .usecase import UsecaseClassifier, UsecaseRelation
from .component import ComponentRelation

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
    system_id: Optional[UUID] = None
    system_name: Optional[str] = None

    class Meta:
        model = models.Classifier
        fields = ["id", "data"]

    @staticmethod
    def resolve_system_id(obj):
        return obj.system_id

    @staticmethod
    def resolve_system_name(obj):
        return getattr(obj.system, "name", None)


Relation = Annotated[
    Union[
        ActivityRelation,
        ClassRelation,
        UsecaseRelation,
        ComponentRelation,
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
