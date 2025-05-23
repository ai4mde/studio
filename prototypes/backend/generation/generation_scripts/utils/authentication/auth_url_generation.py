from utils.file_generation import generate_output_file
from utils.sanitization import project_name_sanitization

def generate_auth_urls(project_name: str, system_id: str) -> bool:
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/authentication/auth_urls.py.jinja2"
    OUTPUT_FILE_PATH = "/usr/src/prototypes/generated_prototypes/" + system_id + "/" + project_name_sanitization(project_name) + "/authentication/urls.py"

    data = {
        
    }

    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    
    raise Exception("Failed to generate " + project_name + "authentication/views.py")


def generate_noauth_home_urls(project_name: str, system_id: str) -> bool:
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/authentication/noauth_urls.py.jinja2"
    OUTPUT_FILE_PATH = "/usr/src/prototypes/generated_prototypes/" + system_id + "/" + project_name_sanitization(project_name) + "/noauth_home/urls.py"

    data = {
        
    }

    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    
    raise Exception("Failed to generate " + project_name + "noauth_home/views.py")