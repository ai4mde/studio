from pydantic import BaseModel, Field
from typing import Literal, List, Union

from metadata.specification.kernel import (
    Attribute,
    NamedElement,
    NamespacedElement,
    Operation,
)


class ApplicationClassifiers(BaseModel):
    id: str
    attributes: list[str] = []


class Category(BaseModel):
    name: str


class ApplicationShared(NamedElement, NamespacedElement, BaseModel):
    classifiers: List[ApplicationClassifiers] = []
    categories: List[Category] = []


class Application(ApplicationShared):
    type: Literal["application"] = "application"


class Page(ApplicationShared):
    type: Literal["page"] = "page"
    page_type: str
    query: str
    create: bool
    data_paths: str


class Section(ApplicationShared):
    type: Literal["section"] = "section"
    classes: str
    sorting: str
    content: str
    linked_page: str


class Class(NamedElement, NamespacedElement, BaseModel):
    type: Literal["class"] = "class"
    attributes: List[Attribute] = []
    methods: List[Operation] = []
    abstract: bool = False
    leaf: bool = False


class Enum(NamedElement, NamespacedElement, BaseModel):
    type: Literal["enum"] = "enum"
    literals: List[str]


class Signal(NamedElement, NamespacedElement, BaseModel):
    type: Literal["signal"] = "signal"


class System(NamedElement, BaseModel):
    type: Literal["system"] = "system"


class Container(NamedElement, BaseModel):
    type: Literal["container"] = "container"


class Component(NamedElement, BaseModel):
    type: Literal["component"] = "component" 


ClassClassifier = Union[Application, Page, Section, Class, Enum, Signal, System, Container, Component]
