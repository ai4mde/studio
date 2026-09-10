from django.db import models


class ClassifierType(models.TextChoices):
    # Class
    CLASS = "class"
    SIGNAL = "signal"
    ENUM = "enum"
    INTERFACE = "interface"

    # Usecase
    USECASE = "usecase"
    ACTOR = "actor"
    SYSTEM_BOUNDARY = "systemboundary"

    # Activity
    SWIMLANE = "swimlane"
    ACTION = "action"
    DECISION = "decision"
    FINAL = "final"
    FORK = "fork"
    INITIAL = "initial"
    JOIN = "join"
    MERGE = "merge"
    OBJECT = "object"
    EVENT = "event"


    # Component
    SYSTEM = "systemcomponent"
    CONTAINER = "container"
    COMPONENT = "component"


class RelationType(models.TextChoices):
    # Class
    ASSOCIATION = "association"
    GENERALIZATION = "generalization"
    COMPOSITION = "composition"
    DEPENDENCY = "dependency"

    # Activity
    CONTROLFLOW = "controlflow"
    
    # Usecase
    INTERACTION = "interaction"
    EXTENSION = "extension"
    INCLUSION = "inclusion"
    
    # Component
    INTERFACE = "interface"


class DataType(models.TextChoices):
    STRING = "string"
    INT = "int"
    BOOL = "bool"
    DATETIME = "datetime"
    ENUM = "enum"


class ActivityScope(models.TextChoices):
    FLOW = "flow"
    ACTIVITY = "activity"


class AggregatorType(models.TextChoices):
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"


class OperatorType(models.TextChoices):
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="


class InterfaceStyle(models.TextChoices):
    ABSTRACT = "abstract"
    BASIC = "basic"
    MODERN = "modern"


class PageType(models.TextChoices):
    NORMAL = "normal"
    ACTIVITY = "activity"
