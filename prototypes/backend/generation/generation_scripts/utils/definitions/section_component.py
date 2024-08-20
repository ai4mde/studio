from typing import List
from utils.definitions.model import Model, AttributeType
from utils.sanitization import section_name_sanitization


class SectionAttribute():
    def __init__(
            self,
            name: str,
            type: AttributeType,
            updatable: bool
    ):
        self.name = name
        self.type = type
        self.updatable = updatable

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
            parent_models: List[Model], # TODO: implement
            attributes: List[SectionAttribute],
            has_create_operation: bool = False,
            has_delete_operation: bool = False,
            has_update_operation: bool = False
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

    def __str__(self):
        return self.name