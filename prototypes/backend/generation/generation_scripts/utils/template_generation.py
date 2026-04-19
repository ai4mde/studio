from utils.definitions.application_component import ApplicationComponent
from utils.sanitization import project_name_sanitization, app_name_sanitization, page_name_sanitization
from utils.file_generation import generate_output_file, write_to_file
from utils.ast_template_renderer import render_page
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
        "theme": application_component.theme,
        "global_layout": application_component.global_layout,
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
        "theme": application_component.theme,
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


def generate_ast_page(application_component: ApplicationComponent, page, output_file_path: str) -> bool:
    application_name = app_name_sanitization(application_component.name)
    page_body = render_page(page.render_ast or [], application_component.theme)
    content = (
        '{% extends "' + application_name + '_base.html" %}\n'
        '{% block content %}\n' + page_body + '\n{% endblock %}\n'
    )
    return write_to_file(output_file_path, content)


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
        # NOTE: render_ast produces visual mockups (disabled inputs, no Django
        # forms) that are not functional.  Always use page.html.jinja2 which
        # supports theme tokens and generates working CRUD pages.
        data = {
            "project_name": project_name,
            "application_name": application_name,
            "page": page,
            "theme": application_component.theme,
        }
        if not generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
            raise Exception("Failed to generate template: " + page.name)
            
    return True