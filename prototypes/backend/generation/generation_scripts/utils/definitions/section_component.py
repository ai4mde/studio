from typing import List, Optional
from utils.definitions.model import Model, AttributeType
from utils.sanitization import section_name_sanitization
import ast
import re
from re import sub

def parse_section_text(text: str) -> str:
    """
        # -> <h1>
        ## -> <h2>
        ### -> <h3>
        #### -> <h4>
        ##### -> <h5>
        ** ** -> <strong>
        * * -> <em>
        _ _ -> <em>
        \n -> <br>

    """
    text = sub(r'##### (.+)', r'<h5>\1</h5>', text)
    text = sub(r'#### (.+)', r'<h4>\1</h4>', text)
    text = sub(r'### (.+)', r'<h3>\1</h3>', text)
    text = sub(r'## (.+)', r'<h2>\1</h2>', text)
    text = sub(r'# (.+)', r'<h1>\1</h1>', text)
    text = sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = sub(r'_(.+?)_', r'<em>\1</em>', text)
    text = text.replace("\n", "<br>")
    return text

class SectionAttribute():
    def __init__(
            self,
            name: str,
            type: AttributeType,
            enum_literals: Optional[List[str]],
            updatable: bool,
            derived: bool = False,
            is_link: bool = False,
            render_as: str = "text",
            action: Optional[dict] = None
    ):
        self.name = name
        self.type = type
        self.enum_literals = enum_literals
        self.updatable = updatable
        self.derived = derived
        self.is_link = is_link
        self.render_as = render_as
        self.action = action or {"type": "none"}

    def __str__(self):
        return self.name
    

def extract_call_name(body: str) -> str:
    match = re.search(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", body or "")
    if match:
        return match.group(1)
    return None


class SectionCustomMethod():
    def __init__(
            self,
            name: str,
            body: str = None,
            parameters = None,
            action: str = None,
            target_model: str = None,
            call_name: str = None,
            label: str = None
    ):
        self.name = name
        self.call_name = call_name or extract_call_name(body) or section_name_sanitization(name).lower()
        self.label = label or name
        self.parameters = parameters or []
        self.action = action
        self.target_model = target_model
        try:
            ast.parse(body or "")
            self.body = body
            self.body_is_valid = bool(body)
        except SyntaxError:
            self.body_is_valid = False

    def __str__(self):
        return self.name


DEFAULT_SECTION_STYLE = {
    "color": "blue",
    "density": "normal",
    "radius": "xl",
    "columns": "3",
    "card_style": "elevated",
    "image_position": "top",
    "image_size": "md",
}

class SectionComponent():
    """Definition of a Section Component. A Section Component is a component
    on a page on which the end user can act on the attributes of a model."""
    def __init__(
            self,
            id: str,
            name: str,
            application: str,
            page: str,
            primary_model: Model,
            parent_models: List[str],
            attributes: List[SectionAttribute],
            text: str,
            has_create_operation: bool = False,
            has_delete_operation: bool = False,
            has_update_operation: bool = False,
            custom_methods = List[SectionCustomMethod],
            layout: str = "table",
            style: Optional[dict] = None,
            related_to_section_id: Optional[str] = None,
            relation_field: Optional[str] = None,
            query: Optional[dict] = None,
            view_detail_page: Optional[str] = None,
            col_span: int = 12,
            position: Optional[str] = None,
            component_type: str = "data",
            label: Optional[str] = None,
    ):
        self.name = section_name_sanitization(name)
        self.display_name = name
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
        self.text = parse_section_text(text)
        self.layout = layout or "table"
        self.style = {**DEFAULT_SECTION_STYLE, **(style or {})}
        self.related_to_section_id = related_to_section_id
        self.relation_field = relation_field
        self.query = query or {}
        self.query_literal = repr(self.query)
        self.view_detail_page = view_detail_page
        self.col_span = col_span if col_span in (3, 4, 6, 12) else 12
        self.position = position or 'main'
        self.component_type = component_type
        self.label = label or name

    def __str__(self):
        return self.name
