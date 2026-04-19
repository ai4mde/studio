import sys
from utils.sanitization import project_name_sanitization
from utils.authentication.auth_template_generation import generate_noauth_home_template
from utils.authentication.auth_url_generation import generate_noauth_home_urls
from utils.authentication.auth_view_generation import generate_noauth_home_views
from utils.metadata_input import resolve_metadata_arg


def main():
    if (len(sys.argv) != 4):
        raise Exception("Invalid number of system arguments.")
    
    project_name = project_name_sanitization(sys.argv[1])
    metadata = resolve_metadata_arg(sys.argv[2])
    system_id = sys.argv[3]

    if not generate_noauth_home_views(project_name, metadata, system_id):
        raise Exception("Failed to generate noauth_home views")

    if not generate_noauth_home_urls(project_name, system_id):
        raise Exception("Failed to generate noauth_home urls")
    
    if not generate_noauth_home_template(project_name, metadata, system_id):
        raise Exception("Failed to generate noauth_home template")
    
    return True


if __name__ == "__main__":
    main()