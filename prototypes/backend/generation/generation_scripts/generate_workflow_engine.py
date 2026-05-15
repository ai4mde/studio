import json
import sys

from utils.sanitization import project_name_sanitization
from utils.workflow_engine.view_generation import generate_views
from utils.workflow_engine.models_generation import generate_models
from utils.workflow_engine.data_generation import generate_data
from utils.workflow_engine.cron_generation import generate_cron_jobs
from utils.file_generation import write_to_file
from utils.loading_json_utils import resolve_metadata_arg

def main():
    if len(sys.argv) != 5:
        raise Exception("Invalid number of system arguments.")

    project_name = project_name_sanitization(sys.argv[1])
    metadata = resolve_metadata_arg(sys.argv[2])
    system_id = sys.argv[3]
    authentication_present = sys.argv[4] == "True"

    if not generate_models(system_id, project_name, metadata):
        raise Exception("Failed to generate models")

    try:
        cron_jobs = generate_data(system_id, project_name, metadata)
    except Exception as e:
        # Keep prototype generation resilient even when workflow activity metadata is incomplete.
        print(f"Warning: workflow_engine data generation failed: {e}")
        cron_jobs = []
        # The 0002 migration always reads this file; write an empty payload so migrate doesn't fail.
        empty_data = {"processes": [], "action_nodes": [], "join_nodes": [], "rules": []}
        json_path = f"/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}/workflow_engine/migrations/workflow_engine_data.json"
        write_to_file(json_path, json.dumps(empty_data, indent=4))

    if not generate_cron_jobs(system_id, project_name, cron_jobs):
        raise Exception("Failed to generate cron jobs")

    if not generate_views(system_id, project_name, metadata, authentication_present):
        raise Exception("Failed to generate views")
    
    return True


if __name__ == "__main__":
    main()
