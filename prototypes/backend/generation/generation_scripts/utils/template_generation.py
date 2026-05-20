from utils.definitions.application_component import ApplicationComponent
from utils.sanitization import project_name_sanitization, app_name_sanitization, page_name_sanitization
from utils.file_generation import generate_output_file, read_template_file, write_to_file
from utils.definitions.model import AttributeType
from os import makedirs
import re
import difflib


UNIFIED_TEMPLATE = "page_unified.html.jinja2"


def _collect_position_sections(pages, position):
    seen = set()
    out = []
    for page in pages:
        for sc in page.section_components:
            if sc.position == position and sc.id not in seen:
                seen.add(sc.id)
                out.append(sc)
    return out


def generate_base_page(application_component: ApplicationComponent, OUTPUT_TEMPLATES_DIRECTORY: str) -> bool:
    application_name = app_name_sanitization(application_component.name)

    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/base.html.jinja2"
    OUTPUT_FILE_PATH = OUTPUT_TEMPLATES_DIRECTORY + "/" + application_name + "_base.html"

    logo = "" # TODO: retrieve from metadata
    categories = application_component.categories
    accent_hex = (application_component.styling.accent_color or '#0000a4') if application_component.styling else '#0000a4'
    header_sections = _collect_position_sections(application_component.pages, 'header')
    footer_sections = _collect_position_sections(application_component.pages, 'footer')

    data = {
        "application_name": application_name,
        "logo": logo,
        "pages": application_component.pages,
        "categories": categories,
        "authentication_present": application_component.authentication_present,
        "settings": application_component.settings,
        "styling": application_component.styling,
        "header_sections": header_sections,
        "footer_sections": footer_sections,
        "_accent_hex": accent_hex,
        "_brand_name": application_name,
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


def _render_unified_page(page, all_pages, tokens, styling, application_name, project_name, preview_mode=False):
    """Render one page using the shared unified unified template."""
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/" + UNIFIED_TEMPLATE
    template = read_template_file(TEMPLATE_PATH)
    return template.render(
        project_name=project_name,
        application_name=application_name,
        page=page,
        AttributeType=AttributeType,
        styling=styling,
        tokens=tokens,
        all_pages=all_pages,
        preview_mode=preview_mode,
        _accent_hex=tokens.get("accent.hex", (styling.accent_color if styling and getattr(styling, 'accent_color', None) else '#0000a4')),
        _brand_name=tokens.get("brand.name", application_name),
    )


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


def generate_templates(application_component: ApplicationComponent, system_id: str, _variant_id: str = "") -> bool:
    project_name = project_name_sanitization(application_component.project)
    application_name = app_name_sanitization(application_component.name)
    pages_in_app = application_component.pages
    styling = application_component.styling

    # Build tokens from styling so generation mode matches preview behavior
    tokens = {}
    accent = None
    if styling and getattr(styling, 'accent_color', None):
        accent = styling.accent_color
    if accent:
        tokens["region.header.bg"] = f"bg-[{accent}]"
        tokens["page.header.text"] = "text-white"
        tokens["accent.hex"] = accent
        tokens["brand.name"] = application_name

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
        # Render actual prototype page HTML from the shared unified template.
        gen_html = _render_unified_page(
            page=page,
            all_pages=pages_in_app,
            tokens=tokens,
            styling=styling,
            application_name=application_name,
            project_name=project_name,
            preview_mode=False,
        )

        write_to_file(OUTPUT_FILE_PATH, gen_html)

    return True
