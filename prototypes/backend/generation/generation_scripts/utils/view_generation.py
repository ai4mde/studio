from typing import List
from utils.file_generation import generate_output_file
from utils.sanitization import project_name_sanitization, app_name_sanitization
from utils.definitions.section_component import SectionComponent

def generate_views(project_name: str, 
                   application_name: str, 
                   section_components_in_app: List[SectionComponent]) -> bool:
    
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/views.py.jinja2"
    OUTPUT_FILE_PATH = "/usr/src/prototypes/generated_prototypes/" + project_name_sanitization(project_name) + "/" + app_name_sanitization(application_name)+ "/views.py"

    pages = [] # TODO
    models_in_app = [] # TODO
    
    data = {
        "project_name": project_name,
        "application_name": application_name,
        "section_components": section_components_in_app,
        "pages": pages,
        "models_in_app": models_in_app
    }

    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    
    raise Exception("Failed to generate shared_models/models.py")