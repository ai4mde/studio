from utils.file_generation import generate_output_file
from utils.loading_json_utils import retrieve_manager_roles

def generate_views(system_id: str, project_name: str, metadata: str, authentication_present: bool) -> bool:
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/workflow_engine/views.py.jinja2"    
    OUTPUT_FILE_PATH = f"/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}/workflow_engine/views.py"

    manager_roles = retrieve_manager_roles(metadata)
    
    data = {
        "manager_roles": manager_roles,
        "authentication_present": authentication_present,
    }

    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        return True
    
    raise Exception(f"Failed to generate {project_name}/workflow_engine/views.py")
