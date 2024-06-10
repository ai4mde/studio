from pydantic import BaseModel, field_validator
from typing import Union, Literal
from metadata.specification.kernel import NamedElement, NamespacedElement
from ..usecase.classifiers import Actor
from ..classes.classifiers import Class
from ..kernel import Attribute
import re


class Category(NamedElement, BaseModel):
    pass


class Page(NamedElement, BaseModel):
    nr_columns: int = 1
    nr_rows: int = 1
    category: Category = None


class Text(BaseModel):
    tag: Literal["p", "h0", "h1", "h2", "h3", "h4", "h5"] = "p"
    content: str = ""


class Link(BaseModel):
    page_out: Page
    content: str = ""


class SectionComponent(NamedElement, BaseModel):
    primary_model: Class = None
    attributes: list[
        Attribute
    ] = []
    row: int = 0
    col: int = 0
    is_query: bool = False
    has_delete: bool = False
    has_update: bool = False
    has_create: bool = False
    text: list[
        Text
    ] = []
    links: list[
        Link
    ]
    custom_methods: list[
        str
    ] = [] # TODO: link to custom methods somewhere

    @field_validator('row', 'col')
    def must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Invalid location')
        return v


class Styling(BaseModel):
    logo: str = "" # TODO: define logo's somewhere
    type: Literal["basic", "moden", "abstract", ] = "basic"
    radius: int = 10
    text_color: str = "#000000"
    accent_color: str = "#C2C2C2"
    background_color: str = "#FFFFFF"
    text_alignment: Literal["left", "right", "center"] = "left"

    @field_validator('radius')
    def radius_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Invalid radius')
        return v
    
    @field_validator('text-color', 'accent-color', 'background_color')
    def color_must_be_hex(cls, v):
        clr = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
        if not re.match(clr, v):
            raise ValueError('Invalid color hex code')
        return v
    

# TODO: fragments definition
class Fragment(BaseModel):
    classes: str = ""
    use_cases: str = ""
    actions: str = ""


class ApplicationComponent(NamedElement, BaseModel):
    type: Literal["reusable", "non-reusable"] = "non-reusable"
    actors: list[
        Actor
    ] = []
    pages: list[
        Page
    ] = []
    fragment: Fragment = None


ApplicationsClassifier = Union[Category, Page, Text, Link, SectionComponent, Styling, Fragment, ApplicationComponent]


__all__ = [
    "ApplicationsClassifier",
]
