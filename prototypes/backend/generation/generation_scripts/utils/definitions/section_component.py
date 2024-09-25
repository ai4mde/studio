from typing import List, Optional
from utils.definitions.model import Model, AttributeType
from utils.sanitization import section_name_sanitization
import ast

class SectionAttribute():
    def __init__(
            self,
            name: str,
            type: AttributeType,
            enum_literals: Optional[List[str]],
            updatable: bool
    ):
        self.name = name
        self.type = type
        self.enum_literals = enum_literals
        self.updatable = updatable

    def __str__(self):
        return self.name
    

def extract_call_name(body: str) -> str:
    start = body.find("def ") + len("def ")
    end = body.find("(self)")
    if start and end:
        return body[start:end].strip()
    return None


class SectionCustomMethod():
    def __init__(
            self,
            name: str,
            body: str
    ):
        self.name = name
        self.call_name = extract_call_name(body)
        try:
            ast.parse(body)
            self.body = body
            self.body_is_valid = True
        except SyntaxError:
            self.body_is_valid = False

    def __str__(self):
        return self.name


class SectionComponent():
    """Definition of a Section Component. A Section Component is a component
    on a page on which the end user can act on the attributes of a model."""
    def __init__(
            self,
            id: str,
            name: str,
            application: str, # TODO: reference
            page: str, # TODO: refrenec
            primary_model: Model, # TODO: reference
            parent_models: List[str], # TODO: implement
            attributes: List[SectionAttribute],
            has_create_operation: bool = False,
            has_delete_operation: bool = False,
            has_update_operation: bool = False,
            custom_methods = List[SectionCustomMethod]
    ):
        self.name = section_name_sanitization(name)
        self.id = id
        self.application = application
        self.page = page
        self.primary_model = primary_model
        self.parent_models = parent_models
        self.attributes = attributes
        self.has_create_operation = has_create_operation
        self.has_delete_operation = has_delete_operation
        self.has_update_operation = has_update_operation
        self.custom_methods = custom_methods

    def __str__(self):
        return self.name