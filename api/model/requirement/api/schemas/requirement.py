from ninja import ModelSchema
from requirement.models import Requirement


class ReadRequirement(ModelSchema):
    class Meta:
        model = Requirement
        fields = ["id", "title", "description", "rationale", "dependency"]


class CreateRequirement(ModelSchema):
    class Meta:
        model = Requirement
        fields = ["id", "title", "description", "rationale", "dependency"]


class UpdateRequirement(ModelSchema):
    class Meta:
        model = Requirement
        fields = ["id", "title", "description", "rationale", "dependency"]


class DeleteRequirement(ModelSchema):
    class Meta:
        model = Requirement
        fields = ["id"]


__all__ = ["ReadRequirement", "CreateRequirement", "UpdateRequirement", "DeleteRequirement"]
