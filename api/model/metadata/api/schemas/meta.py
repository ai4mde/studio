from typing import List
from metadata.specification import ClassifierSchema, RelationSchema
from ninja import Schema


class MetaSchema(Schema):
    classifiers: List[ClassifierSchema]
    relations: List[RelationSchema]


class MetaClassifiersSchema(Schema):
    classifiers: List[ClassifierSchema]


class MetaRelationsSchema(Schema):
    relations: List[RelationSchema]


__all__ = [
    "MetaSchema",
    "MetaClassifiersSchema",
    "MetaRelationsSchema"
]
