from metadata.specification import Classifier
from ninja import Schema


class NewClassifierInput(Schema):
    data: Classifier
    type: str


__all__ = [
    "NewClassifierInput",
]
