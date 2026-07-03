import os
from pathlib import Path
from typing import Dict, Any
import jinja2
from jinja2 import Environment, FileSystemLoader, Template
from utils.definitions.model import Attribute, AttributeType, CustomMethod, Cardinality
from utils.definitions.section_component import SectionComponent, SectionCustomMethod
from utils.definitions.page import Page
from utils.definitions.category import Category
from utils.definitions.application_component import ApplicationComponent
from utils.definitions.styling import Styling, StyleType
from utils.definitions.settings import Settings


GENERATED_PROTOTYPES_ROOT = Path(
    os.environ.get("GENERATED_PROTOTYPES_ROOT", "/usr/src/prototypes/generated_prototypes")
).resolve()


def _resolve_generated_path(path: str) -> Path:
    resolved_path = Path(path).resolve()
    if resolved_path != GENERATED_PROTOTYPES_ROOT and GENERATED_PROTOTYPES_ROOT not in resolved_path.parents:
        raise ValueError("Output path must be inside generated prototypes directory")
    return resolved_path


def ensure_generated_directory(path: str) -> Path:
    directory = _resolve_generated_path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


# TODO: there could be added more logic here to only add relevant
#       globals based on the type of output file.
def add_jinja_globals(template: Template) -> Template:
    '''This function adds Python class schemes to Jinja templates
    which ensures that attributes of these objects can be read
    inside the templates.'''
    
    template.globals['Styling'] = Styling
    template.globals['StyleType'] = StyleType
    template.globals['Attribute'] = Attribute
    template.globals['AttributeType'] = AttributeType
    template.globals['SectionComponent'] = SectionComponent
    template.globals['Page'] = Page
    template.globals['Category'] = Category
    template.globals['ApplicationComponent'] = ApplicationComponent
    template.globals['CustomMethod'] = CustomMethod
    template.globals['SectionCustomMethod'] = SectionCustomMethod
    template.globals['Cardinality'] = Cardinality
    template.globals['Settings'] = Settings

    return template


def read_template_file(TEMPLATE_PATH: str) -> Template:
    """
    Reads a Jinja2 template from the specified path and returns the template
    """
    TEMPLATE_DIR = os.path.dirname(TEMPLATE_PATH)
    TEMPLATE_NAME = os.path.basename(TEMPLATE_PATH)

    try:
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        template = env.get_template(TEMPLATE_NAME)
        template = add_jinja_globals(template)
    except jinja2.exceptions.TemplateNotFound:
        raise Exception("Could not load Jinja2 template: " + TEMPLATE_NAME)
    return template


def write_to_file(OUTPUT_FILE_PATH: str, content: str) -> bool:
    """
    Writes the given content to the specified file path.
    """
    output_path = _resolve_generated_path(OUTPUT_FILE_PATH)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w+", encoding="utf-8") as fh:
            fh.write(content)
    except Exception:
        raise Exception("Failed to write to " + OUTPUT_FILE_PATH)
    return True


def generate_output_file(TEMPLATE_PATH: str, 
                         OUTPUT_FILE_PATH: str, 
                         data: Dict[str, Any]) -> bool:
    '''This function generates an output file at "OUTPUT_FILE_PATH" by 
    combining "data" with a Jinja2 template at "TEMPLATE_PATH.'''
    return write_to_file(
        OUTPUT_FILE_PATH=OUTPUT_FILE_PATH,
        content=read_template_file(TEMPLATE_PATH).render(data)
    )
