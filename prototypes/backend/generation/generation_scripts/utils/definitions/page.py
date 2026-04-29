from typing import List, Literal, Optional
from utils.definitions.category import Category
from utils.definitions.section_component import SectionComponent
from utils.sanitization import page_name_sanitization, category_name_sanitization


class Page():
    '''Definition of a Page object. A Page object maps to a HTML template
    in the output Prototype.'''
    def __init__(
            self,
            id: str,
            application: str,
            name: str,
            category: Optional[str], # TODO: refer to category object
            activity_name: Optional[str],
            type: Literal['normal', 'activity'],
            section_components: List[SectionComponent],
            render_ast: Optional[list] = None,
            semantic_ast: Optional[dict] = None,
            composition: Optional[dict] = None,
            capability_profiles: Optional[list] = None,
            candidate_compositions: Optional[list] = None,
            active_composition: Optional[dict] = None,
    ):
        self.name = page_name_sanitization(name)
        self.display_name = name
        self.id = id
        self.application = application
        self.category = category_name_sanitization(category) if category is not None else None
        self.activity_name = activity_name
        self.type = type
        self.section_components = section_components
        self.render_ast = render_ast or []
        self.semantic_ast = semantic_ast or {}
        self.composition = composition or {}
        self.capability_profiles = capability_profiles or []
        self.candidate_compositions = candidate_compositions or []
        self.active_composition = active_composition or {}

    def __str__(self):
        return self.name