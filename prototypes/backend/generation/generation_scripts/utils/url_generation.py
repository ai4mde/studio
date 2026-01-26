from utils.file_generation import generate_output_file
from utils.sanitization import project_name_sanitization, app_name_sanitization
from utils.definitions.application_component import ApplicationComponent

def generate_urls(application_component: ApplicationComponent, system_id: str) -> bool:
    project_name = application_component.project
    application_name = application_component.name
    pages_in_app = application_component.pages

    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/urls.py.jinja2"
    OUTPUT_FILE_PATH = "/usr/src/prototypes/generated_prototypes/" + system_id + "/" + project_name_sanitization(project_name) + "/" + app_name_sanitization(application_name)+ "/urls.py"

    data = {
        "project_name": project_name,
        "application_name": application_name,
        "pages": pages_in_app,
        "settings": application_component.settings,
    }

    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    
    raise Exception("Failed to generate " + project_name + "/urls.py")