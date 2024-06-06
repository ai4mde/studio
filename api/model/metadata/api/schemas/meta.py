from typing import List
from metadata.specification import ClassifierSchema, RelationSchema
from ninja import Schema


class MetaSchema(Schema):
    classifiers: List[ClassifierSchema]
    relations: List[RelationSchema]


__all__ = [
    "MetaSchema",
]
