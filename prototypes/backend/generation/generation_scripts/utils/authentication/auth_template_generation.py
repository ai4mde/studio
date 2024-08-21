from utils.definitions.application_component import ApplicationComponent
from utils.sanitization import project_name_sanitization, app_name_sanitization, page_name_sanitization
from utils.file_generation import generate_output_file
from os import makedirs


def generate_auth_base_page(metadata: str, OUTPUT_TEMPLATES_DIRECTORY: str) -> bool:
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/authentication/auth_base.html.jinja2"
    OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/authentication_base.html"
    
    logo = "" # TODO: retrieve from metadata

    data = {
        "logo": logo,
    }
    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    return False
    

def generate_auth_templates(project_name: str, metadata: str) -> bool:

    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/authentication/auth_index.html.jinja2"
    OUTPUT_TEMPLATES_DIRECTORY = "/usr/src/prototypes/generated_prototypes/" + project_name + "/authentication/templates"
    OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/authentication_index.html"

    try:
        makedirs(OUTPUT_TEMPLATES_DIRECTORY, exist_ok=True)
    except:
        raise Exception("Failed to create templates directory for authentication application")
    
    if not generate_auth_base_page(metadata, OUTPUT_TEMPLATES_DIRECTORY):
        raise Exception("Failed to generate base page for authentication application")
    
    user_types = ["Customer", "Manager", "BigBoss"] # TODO: retrieve from metadata
    data = {
        "project_name": project_name,
        "user_types": user_types
    }
    if not generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        raise Exception("Failed to generate authentication index template" )
            
    return True