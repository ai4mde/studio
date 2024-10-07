from typing import List

from requirement.api.schemas import CreateRequirement, ReadRequirement, UpdateRequirement
from requirement.models import Requirement
from ninja import Router

requirements = Router()


@requirements.get("/", response=List[ReadRequirement])
def list_requirements(request):
    qs = Requirement.objects.all()
    return qs


@requirements.get("/{uuid:requirement_id}", response=ReadRequirement)
def read_requirement(request, requirement_id):
    return Requirement.objects.get(id=requirement_id)


@requirements.post("/", response=ReadRequirement)
def create_requirement(request, requirement: CreateRequirement):
    return Requirement.objects.create(
        title=requirement.title,
        description=requirement.description,
        rationale=requirement.rationale,
        dependency=requirement.dependency,
    )


@requirements.put("/{uuid:requirement_id}", response=ReadRequirement)
def update_requirement(request, requirement_id, payload: UpdateRequirement):
    print(requirement_id)
    print(payload)
    return None


@requirements.delete("/{uuid:requirement_id}")
def delete_requirement(request, requirement_id):
    try:
        requirement = Requirement.objects.get(id=requirement_id)
        requirement.delete()
    except Exception as e:
        raise Exception("Failed to delete Software Requirements Specification document, error: " + e)
    return True
    

__all__ = ["requirements"]
