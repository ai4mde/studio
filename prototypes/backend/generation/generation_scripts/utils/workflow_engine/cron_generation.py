from utils.file_generation import generate_output_file
from utils.workflow_engine.data_generation import CronJob


def generate_cron_jobs(system_id: str, project_name: str, cron_jobs: list[CronJob]) -> bool:
    TEMPLATE_PATH = "/usr/src/prototypes/backend/generation/templates/workflow_engine/cron_jobs.py.jinja2"
    OUTPUT_FILE_PATH = f"/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}/workflow_engine/cron_jobs.py"

    if not cron_jobs:
        return True

    data = {"cron_jobs": [cron_job._asdict() for cron_job in cron_jobs]}

    if generate_output_file(TEMPLATE_PATH, OUTPUT_FILE_PATH, data):
        cronjobs = [
            f"    ('{job.schedule}', 'workflow_engine.cron_jobs.start_process_{job.process_id}'),"
            for job in cron_jobs
        ]
        with open(f'/usr/src/prototypes/generated_prototypes/{system_id}/{project_name}/{project_name}/settings.py', 'a') as settings_file:
            settings_file.write(f"CRONJOBS = [\n")
            settings_file.write("\n".join(cronjobs))
            settings_file.write("\n]\n")
        return True
    
    raise Exception(f"Failed to generate {project_name}/workflow_engine/cron_jobs.py")