from typing import Any


def build_container(project_name: str, runtime: Any):
    # TODO: Build a runtime docker container using the
    # project name and runtime JSON.
    image_name = ""
    image_tag = ""
    return {
        "status": "ok",
        "container": f"{image_name}:{image_tag}",
    }
