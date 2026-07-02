import json

from utils.file_generation import read_template_file, write_to_file
from utils.sanitization import model_name_sanitization
from generate_models import retrieve_models


def retrieve_section_model_names(metadata: str) -> list[str]:
    data = json.loads(metadata)
    names = set()
    for interface in data.get("interfaces", []):
        sections = interface.get("value", {}).get("data", {}).get("sections", [])
        for section in sections:
            if model_name := section.get("model_name"):
                names.add(model_name_sanitization(model_name))
    return sorted(names)


def generate_models(system_id: str, project_name: str, metadata: str) -> bool:
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/workflow_engine/models.py.jinja2"
    MODELS_PY_FILE_PATH = "/usr/src/prototypes/backend/generation/workflow_engine/models.py"
    OUTPUT_FILE_PATH = f"/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}/workflow_engine/models.py"
    models = sorted({model.name for model in retrieve_models(metadata)} | set(retrieve_section_model_names(metadata)))

    properties = read_template_file(TEMPLATE_PATH).render(models=models)
    imports = f"from shared_models.models import {', '.join(models)}" if models else ""

    with open(MODELS_PY_FILE_PATH, "r") as f:
        models_file_content = f.read()
    models_file_content = models_file_content.replace("# Imports", imports)
    models_file_content = models_file_content.replace("# Properties", properties)

    if write_to_file(OUTPUT_FILE_PATH, models_file_content):
        return True
    
    raise Exception(f"Failed to generate {project_name}/workflow_engine/models.py")
