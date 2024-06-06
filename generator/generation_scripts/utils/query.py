from .section_component_utils import AttributeType
from enum import Enum


class Query:
    def __init__(self,
                 primary_model_name : str):
        self.primary_model_name = primary_model_name


class Leaf:
    pass


class Attribute(Leaf):
    def __init__(self,
                 attribute_name : str,
                 attribute_type : AttributeType):
        self.attribute_name = attribute_name
        self.attribute_type = attribute_type


class Value(Leaf):
    def __init__(self,
                 value):
        self.value = value


class Operator(Enum):
    GREATER = 1
    LESS = 2
    GREATER_EQUAL = 3
    LESS_EQUAL = 4
    EQUAL = 5
    CONTAINS = 6


class Comparison(Query):
    def __init__(self,
                 leaf1 : Leaf,
                 operator : Operator,
                 leaf2 : Leaf):
        self.leaf1 = leaf1
        self.operator = operator
        self.leaf2 = leaf2


class LogicalOperator(Enum):
    CONJUNCTION = 1
    DISJUNCTION = 2


class Logical(Query):
    def __init__(self,
                 query1 : Query,
                 operator : LogicalOperator,
                 query2 : Query):
        self.query1 = query1
        self.operator = operator
        self.query2 = query2


class Negation(Query):
    def __init__(self,
                 query : Query):
        self.query = query