import sys

from utils.sanitization import project_name_sanitization
from utils.workflow_engine.view_generation import generate_views
from utils.workflow_engine.models_generation import generate_models
from utils.workflow_engine.data_generation import generate_data

def main():
    if len(sys.argv) != 5:
        raise Exception("Invalid number of system arguments.")
    
    project_name = project_name_sanitization(sys.argv[1])
    metadata = sys.argv[2]
    system_id = sys.argv[3]
    authentication_present = sys.argv[4] == "True"

    if not generate_models(system_id, project_name, metadata):
        raise Exception("Failed to generate models")

    if not generate_data(system_id, project_name, metadata):
        raise Exception("Failed to generate data")
    
    if not generate_views(system_id, project_name, metadata, authentication_present):
        raise Exception("Failed to generate views")
    
    return True


if __name__ == "__main__":
    main()