from utils.file_generation import write_to_file

def generate_views(system_id: str, project_name: str, authentication_present: bool) -> bool:
    VIEWS_PY_FILE_PATH = "/usr/src/prototypes/backend/generation/workflow_engine/views.py"    
    OUTPUT_FILE_PATH = f"/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}/workflow_engine/views.py"

    with open(VIEWS_PY_FILE_PATH, "r") as f:
        views_file_content = f.read()

    # Jinja2 template doesn't make sense here, since it is so little
    views_file_content = (
        views_file_content.replace("# Auth", "@user_passes_test(login_check)")
        if authentication_present
        else views_file_content.replace("# Auth", "")
    )

    if write_to_file(OUTPUT_FILE_PATH, views_file_content):
        return True
    
    raise Exception(f"Failed to generate {project_name}/workflow_engine/views.py")
