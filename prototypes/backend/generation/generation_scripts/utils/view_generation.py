from utils.file_generation import generate_output_file, write_to_file
from utils.sanitization import project_name_sanitization, app_name_sanitization
from utils.definitions.application_component import ApplicationComponent
from utils.loading_json_utils import retrieve_models_on_pages
from utils.screen_type import detect_screen_type

def generate_views(application_component: ApplicationComponent, system_id: str, llm_views: str = None) -> bool:
    project_name = application_component.project
    application_name = application_component.name
    pages_in_app = application_component.pages

    OUTPUT_FILE_PATH = "/usr/src/prototypes/generated_prototypes/" + system_id + "/" + project_name_sanitization(project_name) + "/" + app_name_sanitization(application_name) + "/views.py"
    OUTPUT_FILE_PATH_SHARED = "/usr/src/prototypes/generated_prototypes/" + system_id + "/" + project_name_sanitization(project_name) + "/shared_models/views.py"

    # If the API agent already generated a views.py, write it directly
    if llm_views:
        if not write_to_file(OUTPUT_FILE_PATH, llm_views):
            raise Exception("Failed to write LLM-generated views.py for " + project_name)
    else:
        TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/views.py.jinja2"
        # Annotate each page with its detected screen type
        for page in pages_in_app:
            page.screen_type = detect_screen_type(page)

        models_on_pages = retrieve_models_on_pages(application_component)
        data = {
            "project_name": project_name,
            "application_name": application_name,
            "pages": pages_in_app,
            "models_on_pages": models_on_pages,
            "authentication_present": application_component.authentication_present,
        }
        if not generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
            raise Exception("Failed to generate " + project_name + "/views.py")

    TEMPLATE_PATH_SHARED = "/usr/src/prototypes/backend/generation/templates/shared_views.py.jinja2"
    data_shared = {
        "authentication_present": application_component.authentication_present,
    }
    if not generate_output_file(TEMPLATE_PATH_SHARED, OUTPUT_FILE_PATH_SHARED, data_shared):
        raise Exception("Failed to generate " + project_name + "/shared_models/views.py")
    return True
