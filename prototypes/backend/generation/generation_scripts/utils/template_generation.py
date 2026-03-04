from utils.definitions.application_component import ApplicationComponent
from utils.sanitization import project_name_sanitization, app_name_sanitization, page_name_sanitization
from utils.file_generation import generate_output_file
from os import makedirs


def generate_base_page(application_component: ApplicationComponent, OUTPUT_TEMPLATES_DIRECTORY: str) -> bool:
    application_name = app_name_sanitization(application_component.name)

    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/base.html.jinja2"
    OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/" + application_name + "_base.html"
    
    logo = "" # TODO: retrieve from metadata
    categories = application_component.categories

    data = {
        "application_name": application_name,
        "logo": logo,
        "pages": application_component.pages,
        "categories": categories,
        "authentication_present": application_component.authentication_present,
        "settings": application_component.settings,
        "styling": application_component.styling,
    }
    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    return False


def generate_home_page(application_component: ApplicationComponent, OUTPUT_TEMPLATES_DIRECTORY: str) -> bool:
    application_name = app_name_sanitization(application_component.name)

    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/home.html.jinja2"
    OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/" + application_name + "_home.html"
    
    data = {
        "application_name": application_name,
        "authentication_present": application_component.authentication_present,
    }
    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    
    return False
    

def generate_action_log_page(application_component: ApplicationComponent, OUTPUT_TEMPLATES_DIRECTORY: str) -> bool:
    application_name = app_name_sanitization(application_component.name)

    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/workflow_engine/action_log.html.jinja2"
    OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/" + application_name + "_action_log.html"

    data = {
        "application_name": application_name,
    }
    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    
    return False


def generate_change_user_assignment(application_component: ApplicationComponent, OUTPUT_TEMPLATES_DIRECTORY: str) -> bool:
    application_name = app_name_sanitization(application_component.name)

    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/workflow_engine/change_user_assignment.html.jinja2"
    OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/" + application_name + "_change_user_assignment.html"

    data = {
        "application_name": application_name,
    }
    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    
    return False


def generate_detail_pages(application_component: ApplicationComponent, OUTPUT_TEMPLATES_DIRECTORY: str) -> bool:
    """Generate OOUI detail pages for each model in the application."""
    from utils.definitions.model import AttributeType
    
    application_name = app_name_sanitization(application_component.name)
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/detail.html.jinja2"
    
    # Collect all unique models from all pages
    models_info = {}
    for page in application_component.pages:
        for section_component in page.section_components:
            model_name = section_component.primary_model
            if model_name not in models_info:
                models_info[model_name] = {
                    "model_name": model_name,
                    "attributes": section_component.attributes,
                    "parent_models": section_component.parent_models,
                    "page": page_name_sanitization(page.name),
                    "section_component": section_component.name,
                    "has_update_operation": section_component.has_update_operation,
                    "has_delete_operation": section_component.has_delete_operation,
                }
    
    # Generate a detail page for each model
    for model_name, info in models_info.items():
        OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/" + application_name + "_" + model_name + "_detail.html"
        data = {
            "application_name": application_name,
            "model_name": model_name,
            "attributes": info["attributes"],
            "parent_models": info["parent_models"],
            "page": info["page"],
            "section_component": info["section_component"],
            "has_update_operation": info["has_update_operation"],
            "has_delete_operation": info["has_delete_operation"],
            "AttributeType": AttributeType,
        }
        if not generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
            return False
    
    return True


def generate_templates(application_component: ApplicationComponent, system_id: str) -> bool:
    project_name = project_name_sanitization(application_component.project)
    application_name = app_name_sanitization(application_component.name)
    pages_in_app = application_component.pages

    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/page.html.jinja2"
    OUTPUT_TEMPLATES_DIRECTORY = "/usr/src/prototypes/generated_prototypes/" + system_id + "/" + project_name + "/" + application_name + "/templates"
    
    try:
        makedirs(OUTPUT_TEMPLATES_DIRECTORY, exist_ok=True)
    except:
        raise Exception("Failed to create templates directory for " + application_name + " application")
    
    if not generate_base_page(application_component, OUTPUT_TEMPLATES_DIRECTORY):
        raise Exception("Failed to generate base page")
    
    if not generate_home_page(application_component, OUTPUT_TEMPLATES_DIRECTORY):
        raise Exception("Failed to generate home page")
    
    if application_component.settings and application_component.settings.manager_access:
        if not generate_action_log_page(application_component, OUTPUT_TEMPLATES_DIRECTORY):
            raise Exception("Failed to generate action log page")
        if not generate_change_user_assignment(application_component, OUTPUT_TEMPLATES_DIRECTORY):
            raise Exception("Failed to generate change user assignment page")

    for page in pages_in_app:
        OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/" + application_name + "_" + page_name_sanitization(page.name) + ".html"
        data = {
            "project_name": project_name,
            "application_name": application_name,
            "page": page,
        }
        if not generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
            raise Exception("Failed to generate template: " + page.name)
    
    # Generate OOUI detail pages
    if not generate_detail_pages(application_component, OUTPUT_TEMPLATES_DIRECTORY):
        raise Exception("Failed to generate detail pages")
            
    return True