from typing import List, Optional
from metadata.models import Classifier, Relation
from metadata.specification import ClassifierSchema, RelationSchema
from ninja import Schema, ModelSchema


class MetaSchema(Schema):
    classifiers: List[ClassifierSchema]
    relations: List[RelationSchema]


class MetaClassifiersSchema(Schema):
    classifiers: List[ClassifierSchema]


class MetaRelationsSchema(Schema):
    relations: List[RelationSchema]


class ExportClassifier(ModelSchema):
    class Meta:
        model = Classifier
        fields = "__all__"


class ImportClassifier(Schema):
    id: str
    project: Optional[str] = None
    system: str
    data: dict


class ExportRelation(ModelSchema):
    class Meta:
        model = Relation
        fields = "__all__"


class ImportRelation(Schema):
    id: str
    system: str
    source: str
    target: str
    data: dict


__all__ = [
    "MetaSchema",
    "MetaClassifiersSchema",
    "MetaRelationsSchema",
    "ExportClassifier",
    "ExportRelation",
    "ImportClassifier",
    "ImportRelation",
]
