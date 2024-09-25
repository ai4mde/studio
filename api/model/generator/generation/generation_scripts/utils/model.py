from enum import Enum
from typing import List

class CustomMethod():
    def __init__(
            self,
            name: str,
            body: str
    ):
        self.name = name
        self.body = body


class AttributeType(Enum):
    INTEGER = 1
    STRING = 2
    BOOLEAN = 3
    FOREIGN_MODEL = 4
    NONE = 5


class Attribute():
    def __init__(
            self,
            name: str,
            type: AttributeType
    ):
        self.name = name
        self.type = type


class Model():
    def __init__(
            self,
            name: str,
            attributes: List[Attribute],
            custom_methods: List[CustomMethod]
    ):
        self.name = name
        self.attributes = attributes
        self.custom_methods = custom_methods