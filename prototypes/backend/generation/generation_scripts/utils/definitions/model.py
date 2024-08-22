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

    def __str__(self):
        return self.name


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

    def __str__(self):
        return self.name


def define_object_name_attribute(attributes: List[Attribute]) -> Attribute:
    '''Function that returns the primary 'name' attribute of a list of attributes.'''
    if not attributes:
        return None
    
    for attribute in attributes:
        if attribute.name == "name":
            return attribute
        
    for attribute in attributes:
        if attribute.type == AttributeType.STRING:
            return attribute
    
    return attributes[0]

class Model():
    def __init__(
            self,
            name: str,
            attributes: List[Attribute],
            custom_methods: List[CustomMethod]
    ):
        self.name = name
        self.attributes = attributes
        self.object_name_attribute = define_object_name_attribute(attributes)
        self.custom_methods = custom_methods

    def __str__(self):
        return self.name