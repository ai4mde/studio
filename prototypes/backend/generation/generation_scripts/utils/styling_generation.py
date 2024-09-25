from utils.file_generation import generate_output_file
from utils.definitions.application_component import ApplicationComponent
from utils.sanitization import project_name_sanitization, app_name_sanitization
from os import makedirs

def generate_styling(application_component: ApplicationComponent) -> bool:
    project_name = project_name_sanitization(application_component.project)
    application_name = app_name_sanitization(application_component.name)
    
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/style.css.jinja2"    
    OUTPUT_STATIC_DIRECTORY = "/usr/src/prototypes/generated_prototypes/" + project_name + "/" + application_name + "/static/" + application_name
    
    try:
        makedirs(OUTPUT_STATIC_DIRECTORY, exist_ok=True)
    except:
        raise Exception("Failed to create static directory for " + project_name + " application")

    OUTPUT_FILE_PATH = OUTPUT_STATIC_DIRECTORY + "/" + application_name + "_style.css"

    data = {
        "application_name": application_name,
        "styling": application_component.styling
    }

    if not generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        raise Exception("Failed to generate " + application_name + "_style.css")

    return True