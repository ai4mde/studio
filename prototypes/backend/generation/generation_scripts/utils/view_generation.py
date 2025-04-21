from utils.file_generation import generate_output_file
from utils.sanitization import project_name_sanitization, app_name_sanitization
from utils.definitions.application_component import ApplicationComponent
from utils.loading_json_utils import retrieve_models_on_pages

def generate_views(application_component: ApplicationComponent, system_id: str) -> bool:
    project_name = application_component.project
    application_name = application_component.name
    pages_in_app = application_component.pages

    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/views.py.jinja2"
    OUTPUT_FILE_PATH = "/usr/src/prototypes/generated_prototypes/" + system_id + "/" + project_name_sanitization(project_name) + "/" + app_name_sanitization(application_name)+ "/views.py"

    TEMPLATE_PATH_SHARED = "/usr/src/prototypes/backend/generation/templates/shared_views.py.jinja2"
    OUTPUT_FILE_PATH_SHARED = "/usr/src/prototypes/generated_prototypes/" + system_id + "/" + project_name_sanitization(project_name) + "/shared_models/views.py"

    models_on_pages = retrieve_models_on_pages(application_component)
    
    data = {
        "project_name": project_name,
        "application_name": application_name,
        "pages": pages_in_app,
        "models_on_pages": models_on_pages,
        "authentication_present": application_component.authentication_present
    }

    data_shared = {
        "authentication_present": application_component.authentication_present,
    }

    if not generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        raise Exception("Failed to generate " + project_name + "/views.py")
    if not generate_output_file(TEMPLATE_PATH_SHARED, OUTPUT_FILE_PATH_SHARED, data_shared):
        raise Exception("Failed to generate " + project_name + "/shared_models/views.py")
    return True
