from pydantic import BaseModel
from pydantic.fields import Field, Literal
from pydantic.types import Annotated, List, Union

from metadata.specification.kernel import Attribute, NamedElement, NamespacedElement, Operation

class ApplicationClassifiers(BaseModel):
    id: str
    attributes: list[str] = []

class Category(BaseModel):
    name: str

class Application(NamedElement, NamespacedElement, BaseModel):
    type: Literal["application"] = "application"
    classifiers: List[ApplicationClassifiers]
    categories = List[Category]

class Page(**Application):
    type: Literal["page"] = "page"
    page_type: str
    query: str
    create: bool
    data_paths: str

class Section(**Application):
    type: Literal["section"] = "section"
    classes: str
    sorting: str
    content: str
    linked_page: str

class Class(BaseModel):
    type: Literal["class"] = "class"
    attributes: List[Attribute]
    methods: List[Operation]
    abstract: bool = False
    leaf: bool = False

class Enum(BaseModel):
    type: Literal["enum"] = "enum"
    literals: List[str]

class ClassClassifier(BaseModel):
    diagram: Literal["classes"] = "classes"
    data: Annotated[
        Union[Application,Page,Section,Class,Enum],
        Field(discriminator="type")
    ]
