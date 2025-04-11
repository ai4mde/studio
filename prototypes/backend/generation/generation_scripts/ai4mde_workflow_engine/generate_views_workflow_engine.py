import sys

from utils.sanitization import project_name_sanitization
from utils.file_generation import read_template_file, write_to_file
from generate_models import retrieve_models

def main():
    if len(sys.argv) != 4:
        raise Exception("Invalid number of system arguments.")

    VIEWS_PY_FILE_PATH = "/usr/src/prototypes/backend/generation/workflow_engine/views.py"    
    OUTPUT_FILE_PATH = f"/usr/src/prototypes/generated_prototypes/{sys.argv[2]}/{project_name_sanitization(sys.argv[1])}/workflow_engine/views.py"

    with open(VIEWS_PY_FILE_PATH, "r") as f:
        views_file_content = f.read()

    # Jinja2 template doesn't make sense here, since it is so little
    views_file_content = (
        views_file_content.replace("# Auth", "@user_passes_test(login_check)")
        if sys.argv[3] == "True"
        else views_file_content.replace("# Auth", "")
    )

    write_to_file(OUTPUT_FILE_PATH, views_file_content)

if __name__ == "__main__":
    main()