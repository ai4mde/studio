from ninja import ModelSchema

from metadata.api.schemas.system import SystemList
from metadata.models import Project


class ProjectList(ModelSchema):
    class Meta:
        model = Project
        fields = ["id", "name", "description"]


class ProjectRead(ModelSchema):
    systems: list[SystemList]

    class Meta:
        model = Project
        fields = ["id", "name", "description"]
    

class ProjectCreate(ModelSchema):
    class Meta:
        model = Project
        fields = ["name", "description"]
        fields_optional = ["description"]


class ProjectUpdate(ModelSchema):
    class Meta:
        model = Project
        fields = ["name", "description"]
        fields_optional = "__all__"
