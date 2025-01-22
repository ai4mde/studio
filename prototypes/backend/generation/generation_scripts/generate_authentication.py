import sys
from utils.sanitization import project_name_sanitization
from utils.authentication.auth_view_generation import generate_auth_views
from utils.authentication.auth_url_generation import generate_auth_urls
from utils.authentication.auth_template_generation import generate_auth_templates
from utils.authentication.auth_styling_generation import generate_auth_styling


def main():
    if (len(sys.argv) != 4):
        raise Exception("Invalid number of system arguments.")
    
    project_name = project_name_sanitization(sys.argv[1])
    metadata = sys.argv[2]
    system_id = sys.argv[3]

    if not generate_auth_views(project_name, metadata, system_id):
        raise Exception("Failed to generate authentication views")
    
    if not generate_auth_urls(project_name, system_id):
        raise Exception("Failed to generate authentication urls")
    
    if not generate_auth_templates(project_name, metadata, system_id):
        raise Exception("Failed to generate authentication templates")
    
    if not generate_auth_styling(project_name, system_id):
        raise Exception("Failed to generate authentication styling")
    
    return True


if __name__ == "__main__":
    main()