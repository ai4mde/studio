from typing import Dict, Any
import os
import jinja2
import pathlib
from jinja2 import Environment, FileSystemLoader, Template
from utils.definitions.model import Attribute, AttributeType, CustomMethod, Cardinality
from utils.definitions.section_component import SectionComponent, SectionCustomMethod
from utils.definitions.page import Page
from utils.definitions.category import Category
from utils.definitions.application_component import ApplicationComponent
from utils.definitions.styling import Styling, StyleType


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

    return template


def generate_output_file(TEMPLATE_PATH: str, 
                         OUTPUT_FILE_PATH: str, 
                         data: Dict[str, Any]) -> bool:
    '''This function generates an output file at "OUTPUT_FILE_PATH" by 
    combining "data" with a Jinja2 template at "TEMPLATE_PATH.'''
    
    TEMPLATES_DIR = os.path.dirname(TEMPLATE_PATH)
    TEMPLATE_NAME = os.path.basename(TEMPLATE_PATH)

    try:
        env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
        template = env.get_template(TEMPLATE_NAME)
        template = add_jinja_globals(template)

    except jinja2.exceptions.TemplateNotFound:
        raise Exception("Could not load Jinja2 template: " + TEMPLATE_NAME)

    try:
        pathlib.Path(OUTPUT_FILE_PATH).parent.mkdir(parents=True, exist_ok=True) 
        with open(OUTPUT_FILE_PATH, "w+") as fh:
            fh.write(template.render(data))
    except:
        raise Exception("Failed to write to " + OUTPUT_FILE_PATH)
    
    return True
