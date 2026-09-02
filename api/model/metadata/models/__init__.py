# DESIGN CHOICE
# There are a lot of duplicate attributes on different classes and sometiems even duplicate classes with different names
# This however is to make it as easy as possible to understand for students
# And make adding new attributes to certain classes as easy as possible

from .classifier import Classifier

from .general import (
    Project,
    System,
)

from .class_diagram import (
    Class,
    Enum,
    EnumLiteral,
    Attribute,
    Operation,
    Interface,
    Signal,
)

from .activity_diagram import (
    Swimlane,
    Action,
    Object,
    Event,
    Final,
    Initial,
)

from .component_diagram import (
    System,
    Container,
    Component,
)

from .usecase_diagram import (
    SystemBoundary,
    Actor,
    Usecase,
)

