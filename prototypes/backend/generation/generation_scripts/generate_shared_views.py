import sys

from utils.file_generation import generate_output_file
from utils.sanitization import project_name_sanitization


def main():
    if len(sys.argv) != 4:
        raise Exception("Invalid number of system arguments.")

    project_name = project_name_sanitization(sys.argv[1])
    authentication_present = sys.argv[2] == "True"
    system_id = sys.argv[3]

    template_path = "/usr/src/prototypes/backend/generation/templates/shared_views.py.jinja2"
    output_file_path = (
        f"/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}/"
        "shared_models/views.py"
    )
    if not generate_output_file(
        template_path,
        output_file_path,
        {"authentication_present": authentication_present},
    ):
        raise Exception(f"Failed to generate {project_name}/shared_models/views.py")


if __name__ == "__main__":
    main()
