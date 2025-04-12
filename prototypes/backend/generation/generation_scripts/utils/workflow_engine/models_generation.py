from utils.file_generation import read_template_file, write_to_file
from generate_models import retrieve_models


def generate_models(system_id: str, project_name: str, metadata: str) -> bool:
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/workflow_engine/models.py.jinja2"
    MODELS_PY_FILE_PATH = "/usr/src/prototypes/backend/generation/workflow_engine/models.py"
    OUTPUT_FILE_PATH = f"/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}/workflow_engine/models.py"
    models = [model.name for model in retrieve_models(metadata)]
    
    properties = read_template_file(TEMPLATE_PATH).render(models=models)
    imports = f"from shared_models.models import {', '.join(models)}"

    with open(MODELS_PY_FILE_PATH, "r") as f:
        models_file_content = f.read()
    models_file_content = models_file_content.replace("# Imports", imports)
    models_file_content = models_file_content.replace("# Properties", properties)

    if write_to_file(OUTPUT_FILE_PATH, models_file_content):
        return True
    
    raise Exception(f"Failed to generate {project_name}/workflow_engine/models.py")
