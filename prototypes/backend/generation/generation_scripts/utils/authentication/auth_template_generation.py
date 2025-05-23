from utils.file_generation import generate_output_file
from utils.loading_json_utils import get_apps
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
    

def generate_auth_templates(project_name: str, metadata: str, system_id: str) -> bool:
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/authentication/auth_index.html.jinja2"
    OUTPUT_TEMPLATES_DIRECTORY = "/usr/src/prototypes/generated_prototypes/" + system_id + "/" + project_name + "/authentication/templates"
    OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/authentication_index.html"

    try:
        makedirs(OUTPUT_TEMPLATES_DIRECTORY, exist_ok=True)
    except:
        raise Exception("Failed to create templates directory for authentication application")
    
    if not generate_auth_base_page(metadata, OUTPUT_TEMPLATES_DIRECTORY):
        raise Exception("Failed to generate base page for authentication application")
    
    application_names = get_apps(metadata).split()

    data = {
        "project_name": project_name,
        "user_types": application_names
    }
    if not generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        raise Exception("Failed to generate authentication index template" )
            
    return True


def generate_noauth_home_template(project_name: str, metadata: str, system_id: str) -> bool:
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/authentication/noauth_index.html.jinja2"
    OUTPUT_TEMPLATES_DIRECTORY = "/usr/src/prototypes/generated_prototypes/" + system_id + "/" + project_name + "/noauth_home/templates"
    OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/noauth_home_index.html"

    try:
        makedirs(OUTPUT_TEMPLATES_DIRECTORY, exist_ok=True)
    except:
        raise Exception("Failed to create templates directory for noauth_home application")
    
    if not generate_auth_base_page(metadata, OUTPUT_TEMPLATES_DIRECTORY):
        raise Exception("Failed to generate base page for noauth_home application")
    
    application_names = get_apps(metadata).split()

    data = {
        "project_name": project_name,
        "user_types": application_names
    }
    if not generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        raise Exception("Failed to generate noauth_home index template" )
            
    return True