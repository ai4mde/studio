from ninja import Schema


class EmptyClassifierData(Schema):
    pass


EMPTY_CLASSIFIER_SCHEMAS = {
    "read": EmptyClassifierData,
    "create": EmptyClassifierData,
    "update": EmptyClassifierData,
}