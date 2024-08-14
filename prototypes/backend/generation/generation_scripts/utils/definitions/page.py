from typing import List
from utils.definitions.category import Category
from utils.definitions.section_component import SectionComponent
from utils.sanitization import page_name_sanitization

class Page():
    '''Definition of a Page object. A Page object maps to a HTML template
    in the output Prototype.'''
    def __init__(
            self,
            id: str,
            application: str,
            name: str,
            category: str, # TODO: refer to category object
            section_components: List[SectionComponent]
    ):
        self.name = page_name_sanitization(name)
        self.id = id
        self.application = application
        self.category = category
        self.section_components = section_components

    def __str__(self):
        return self.name