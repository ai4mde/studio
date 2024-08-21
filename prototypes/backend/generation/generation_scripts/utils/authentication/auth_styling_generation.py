from utils.file_generation import generate_output_file
from os import makedirs

def generate_auth_styling(project_name: str) -> bool:
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/authentication/auth_style.css.jinja2"    
    OUTPUT_STATIC_DIRECTORY = "/usr/src/prototypes/generated_prototypes/" + project_name + "/authentication/static/authentication"
    
    try:
        makedirs(OUTPUT_STATIC_DIRECTORY, exist_ok=True)
    except:
        raise Exception("Failed to create static directory for authentication application")

    OUTPUT_FILE_PATH = OUTPUT_STATIC_DIRECTORY + "/authentication_style.css"

    data = {
    }

    if not generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        raise Exception("Failed to generate authentication_style.css")

    return True