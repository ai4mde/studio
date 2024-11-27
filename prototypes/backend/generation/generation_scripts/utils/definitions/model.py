from enum import Enum
from typing import List, Optional
import ast

class CustomMethod():
    def __init__(
            self,
            name: str,
            body: str
    ):
        self.name = name
        try:
            ast.parse(body)
            self.body = body
            self.body_is_valid = True
        except SyntaxError:
            self.body_is_valid = False

    def __str__(self):
        return self.name


class AttributeType(Enum):
    INTEGER = 1
    STRING = 2
    BOOLEAN = 3
    ENUM = 4
    FOREIGN_MODEL = 5
    NONE = 6


class Cardinality(Enum):
    ONE_TO_ONE_SOURCE = 1              #   A=1       B=1
    ONE_TO_ONE_TARGET = 2              #   A=1       B=1
    ONE_TO_ZERO_MANY = 3               #   A=1       B=0..*
    ONE_TO_ONE_MANY = 4                #   A=1       B=1..*
    ONE_TO_ZERO_ONE = 5                #   A=1       B=0..1
    ZERO_ONE_TO_ONE = 6                #   A=0..1    B=1
    ZERO_ONE_TO_ZERO_MANY = 7          #   A=0..1    B=0..*
    ZERO_ONE_TO_ONE_MANY = 8           #   A=0..1    B=1..*
    ZERO_ONE_TO_ZERO_ONE_SOURCE = 9    #   A=0..1    B=0..1
    ZERO_ONE_TO_ZERO_ONE_TARGET = 10   #   A=0..1    B=0..1
    ZERO_MANY_TO_ONE = 11              #   A=0..*    B=1
    ZERO_MANY_TO_ZERO_MANY_SOURCE = 12 #   A=0..*    B=0..*
    ZERO_MANY_TO_ZERO_MANY_TARGET = 13 #   A=0..*    B=0..*
    ZERO_MANY_TO_ONE_MANY = 14         #   A=0..*    B=1..*
    ZERO_MANY_TO_ZERO_ONE = 15         #   A=0..*    B=0..1
    ONE_MANY_TO_ONE = 16               #   A=1..*    B=1
    ONE_MANY_TO_ZERO_MANY = 17         #   A=1..*    B=0..* 
    ONE_MANY_TO_ONE_MANY_SOURCE = 18   #   A=1..*    B=1..*
    ONE_MANY_TO_ONE_MANY_TARGET = 19   #   A=1..*    B=1..*
    ONE_MANY_TO_ZERO_ONE = 20          #   A=1..*    B=0..1


def define_cardinality(source: str, target: str, node_is_source: bool) -> Cardinality:
    cardinality_dict = {
        ("1", "1"): lambda: Cardinality.ONE_TO_ONE_SOURCE if node_is_source else Cardinality.ONE_TO_ONE_TARGET,
        ("1", "*"): lambda: Cardinality.ONE_TO_ZERO_MANY,
        ("1", "1..*"): lambda: Cardinality.ONE_TO_ONE_MANY,
        ("1", "0..1"): lambda: Cardinality.ONE_TO_ZERO_ONE,
        ("0..1", "1"): lambda: Cardinality.ZERO_ONE_TO_ONE,
        ("0..1", "*"): lambda: Cardinality.ZERO_ONE_TO_ZERO_MANY,
        ("0..1", "1..*"): lambda: Cardinality.ZERO_ONE_TO_ONE_MANY,
        ("0..1", "0..1"): lambda: Cardinality.ZERO_ONE_TO_ZERO_ONE_SOURCE if node_is_source else Cardinality.ZERO_ONE_TO_ZERO_ONE_TARGET,
        ("*", "1"): lambda: Cardinality.ZERO_MANY_TO_ONE,
        ("*", "*"): lambda: Cardinality.ZERO_MANY_TO_ZERO_MANY_SOURCE if node_is_source else Cardinality.ZERO_MANY_TO_ZERO_MANY_TARGET,
        ("*", "1..*"): lambda: Cardinality.ZERO_MANY_TO_ONE_MANY,
        ("*", "0..1"): lambda: Cardinality.ZERO_MANY_TO_ZERO_ONE,
        ("1..*", "1"): lambda: Cardinality.ONE_MANY_TO_ONE,
        ("1..*", "*"): lambda: Cardinality.ONE_MANY_TO_ZERO_MANY,
        ("1..*", "1..*"): lambda: Cardinality.ONE_MANY_TO_ONE_MANY_SOURCE if node_is_source else Cardinality.ONE_MANY_TO_ONE_MANY_TARGET,
        ("1..*", "0..1"): lambda: Cardinality.ONE_MANY_TO_ZERO_ONE,
    }
    return cardinality_dict.get((source, target), lambda: Cardinality.ONE_TO_ZERO_MANY)()


class Attribute():
    def __init__(
            self,
            name: str,
            type: AttributeType,
            enum_literals: Optional[List[str]],
            cardinality: Optional[Cardinality],
            derived: bool = False,
            body: Optional[str] = None
    ):
        self.name = name
        self.type = type
        self.enum_literals = enum_literals
        self.cardinality = cardinality
        self.derived = derived
        self.body = body

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