from ninja import Schema


class GenerateAttribute(Schema):
    name: str
    type: str
    description: str
    model: str = "mixtral-8x7b-32768"


class GenerateMethod(Schema):
    name: str
    description: str
    model: str = "mixtral-8x7b-32768"