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
    SYSTEM = "system"
    CONTAINER = "container"
    COMPONENT = "component"


class RelationType(models.TextChoices):
    TEST = "test"


class DataType(models.TextChoices):
    STRING = "string"
    INT = "int"
    BOOL = "bool"
    DATETIME = "datetime"
    ENUM = "enum"


class ActivityScope(models.TextChoices):
    FLOW = "flow"
    ACTIVITY = "activity"