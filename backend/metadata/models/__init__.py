# DESIGN CHOICE
# There are a lot of duplicate attributes on different classes and sometiems even duplicate classes with different names
# This however is to make it as easy as possible to understand for students
# And make adding new attributes to certain classes as easy as possible

from .classifier import Classifier
from .relation import Relation

from .general import (
    Project,
    System,
)

from .class_diagram import (
    # Nodes
    ClassClassifier,
    Enum,
    EnumLiteral,
    Attribute,
    Operation,
    InterfaceClassifier,
    Signal,
    
    # Relations
    Association,
    Composition,
    Dependency,
    EndpointLabel,
    Multiplicity,
)

from .activity_diagram import (
    # Nodes
    Swimlane,
    Action,
    Object,
    Event,
    Final,
    Initial,

    # Relations
    ControlFlow,
)

from .component_diagram import (
    # Nodes
    SystemClassifier,
    Container,
    Component,
    
    # Relations
    InterfaceRelation,
)

from .usecase_diagram import (
    SystemBoundary,
    Actor,
    Usecase,
)

from .interface import (
    Category,
    Interface,
    Page,
    PageSection,
    SectionAttribute,
    SectionComponent
)
