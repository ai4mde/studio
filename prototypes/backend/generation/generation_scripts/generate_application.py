import sys
from utils.sanitization import project_name_sanitization, app_name_sanitization
from utils.view_generation import generate_views
from utils.url_generation import generate_urls
from utils.template_generation import generate_templates
from utils.loading_json_utils import retrieve_section_components, filter_section_components_by_application, retrieve_pages, filter_pages_by_application


def main():
    if (len(sys.argv) != 4):
        raise Exception("Invalid number of system arguments.")
    
    project_name = project_name_sanitization(sys.argv[1])
    application_name = app_name_sanitization(sys.argv[2])
    metadata = sys.argv[3]

    section_components = retrieve_section_components(metadata)
    section_components_in_app = filter_section_components_by_application(section_components=section_components, application=application_name)
    
    pages = retrieve_pages(metadata)
    pages_in_app = filter_pages_by_application(pages=pages, application=application_name)

    if not generate_views(project_name, application_name, pages_in_app, section_components_in_app):
        raise Exception("Failed to generate views")
    
    '''
    if not generate_urls(project_name, application_name, metadata):
        raise Exception("Failed to generate urls")
    
    if not generate_templates(project_name, application_name, metadata):
        raise Exception("Failed to generate urls")
    '''

    return True


if __name__ == "__main__":
    main()