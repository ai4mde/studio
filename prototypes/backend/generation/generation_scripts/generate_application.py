import sys
from utils.sanitization import project_name_sanitization, app_name_sanitization
from utils.view_generation import generate_views
from utils.url_generation import generate_urls
from utils.template_generation import generate_templates
from utils.styling_generation import generate_styling
from utils.loading_json_utils import get_application_component


def main():
    if (len(sys.argv) != 5):
        raise Exception("Invalid number of system arguments.")
    
    project_name = project_name_sanitization(sys.argv[1])
    application_name = app_name_sanitization(sys.argv[2])
    metadata = sys.argv[3]
    authentication_present = sys.argv[4] == "True"

    application_component = get_application_component(project_name, application_name, metadata, authentication_present)

    if not generate_views(application_component):
        raise Exception("Failed to generate views")
    
    
    if not generate_urls(application_component):
        raise Exception("Failed to generate urls")
    
    
    if not generate_templates(application_component):
        raise Exception("Failed to generate templates")
    
    if not generate_styling(application_component):
        raise Exception("Failed to generate styling")

    return True


if __name__ == "__main__":
    main()