import sys
from utils.sanitization import project_name_sanitization, app_name_sanitization
from utils.view_generation import generate_views
from utils.url_generation import generate_urls
from utils.template_generation import generate_templates
from utils.loading_json_utils import get_application_component


def main():
    if (len(sys.argv) != 4):
        raise Exception("Invalid number of system arguments.")
    
    project_name = project_name_sanitization(sys.argv[1])
    application_name = app_name_sanitization(sys.argv[2])
    metadata = sys.argv[3]

    application_component = get_application_component(project_name, application_name, metadata)

    if not generate_views(application_component):
        raise Exception("Failed to generate views")
    
    
    if not generate_urls(application_component):
        raise Exception("Failed to generate urls")
    
    '''
    if not generate_templates(project_name, application_name, metadata):
        raise Exception("Failed to generate urls")
    '''

    return True


if __name__ == "__main__":
    main()