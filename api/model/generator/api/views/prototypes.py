from typing import List, Optional
from generator.api.schemas import ReadPrototype, CreatePrototype, UpdatePrototype
from generator.models import Prototype
from metadata.models import System
from ninja import Router
import subprocess
import json

prototypes = Router()


def run_docker_command(command: List[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Command '{' '.join(command)}' failed with error: {result.stderr}")
    return result.stdout


@prototypes.get("/", response=List[ReadPrototype])
def list_prototypes(request, system: Optional[str] = None):
    qs = None
    if system:
        qs = Prototype.objects.filter(system=system)
    else:
        qs = Prototype.objects.all()
    return qs


@prototypes.get("/{uuid:id}/", response=ReadPrototype)
def read_prototype(request, id):
    return Prototype.objects.get(id=id)


@prototypes.post("/", response=ReadPrototype)
def create_prototype(request, prototype: CreatePrototype):
    command = [
        "docker", "run", "-d", "-P", "your-docker-image" # TODO: docker image
    ]
    container_id = run_docker_command(command).strip()

    inspect_command = [
        "docker", "inspect", container_id
    ]
    container_info = json.loads(run_docker_command(inspect_command))[0]
    host_port = container_info['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
    container_url = f"http://localhost:{host_port}"

    return Prototype.objects.create(
        name=prototype.name,
        description=prototype.description,
        system=System.objects.get(pk=prototype.system),
        running=False,
        container_id=container_id,
        container_url=container_url,
        container_port=host_port
    )


@prototypes.delete("/{uuid:prototype_id}/", response=bool)
def delete_prototype(request, prototype_id):
    try:
        Prototype.objects.filter(id=prototype_id).delete()
    except Prototype.DoesNotExist:
        return False
    return True


@prototypes.put("/{uuid:id}/", response=bool)
def update_prototype(request, id, prototype: UpdatePrototype):
    try: 
        Prototype.objects.filter(id=id).update(name=prototype.name,
                                               description=prototype.description,
                                               system=prototype.system,
                                               running=prototype.running)
    except Prototype.DoesNotExist:
        return False
    return True


__all__ = ["prototypes"]
