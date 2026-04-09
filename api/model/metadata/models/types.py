from django.db import models


class RelationType(models.TextChoices):
    ASSOCIATION = "association", "Association"
    COMPOSITION = "composition", "Composition"
    DEPENDENCY  = "dependency", "Dependency"
    GENERALIZATION = "generalization", "Generalization"
    INTERACTION = "interaction", "Interaction"
    EXTENSION = "extension", "Extension"
    INCLUSION = "inclusion", "Inclusion"
    CONTROLFLOW = "controlflow", "Control Flow"
    OBJECTFLOW = "objectflow", "Object Flow"
    INTERFACE = "interface", "Interface"


class AggregatorType(models.TextChoices):
    COUNT = "count", "Count"
    SUM = "sum", "Sum"
    AVG = "avg", "Average"
    MIN = "min", "Minimum"
    MAX = "max", "Maximum"


class OperatorType(models.TextChoices):
    EQUALS = "==", "Equals"
    NOT_EQUALS = "!=", "Not Equals"
    GREATER_THAN = ">", "Greater Than"
    LESS_THAN = "<", "Less Than"
    GREATER_OR_EQUAL = ">=", "Greater or Equal"
    LESS_OR_EQUAL = "<=", "Less or Equal"


class ClassifierType(models.TextChoices):
    # Class
    CLASS = "class", "Class"
    SIGNAL = "signal", "Signal"
    ENUMERATION = "enumeration", "Enumeration"
    INTERFACE = "interface", "Interface"

    # Usecase
    USECASE = "usecase", "Usecase"
    ACTOR = "actor", "Actor"
    SYSTEM_BOUNDARY = "system_boundary", "System Boundary"

    # Activity
    SWIMLANE = "swimlane", "Swimlane"
    ACTION = "action", "Action"
    DECISION = "decision", "Decision"
    FINAL = "final", "Final"
    FORK = "fork", "Fork"
    INITIAL = "initial", "Initial"
    JOIN = "join", "Join"
    MERGE = "merge", "Merge"
    OBJECT = "object", "Object"
    EVENT = "event", "Event"


    # Component
    SYSTEM = "system", "System"
    CONTAINER = "container", "Container"
    COMPONENT = "component", "Component"


class ActivityScope(models.TextChoices):
    NORMAL = "normal", "Normal"
    ACTIVITY = "activity", "Activity"


class AttributeType(models.TextChoices):
    STRING = "string", "String"
    INT = "int", "Integer"
    BOOL = "bool", "Boolean"
    DATETIME = "datetime", "Datetime"
    ENUM = "enum", "Enumeration"
