from ninja import ModelSchema

from metadata.models import Project


class ProjectRead(ModelSchema):
    class Meta:
        model = Project
        fields = ["id", "name", "description"]


class ProjectCreate(ModelSchema):
    class Meta:
        model = Project
        fields = ["name", "description"]


class ProjectUpdate(ModelSchema):
    class Meta:
        model = Project
        fields = ["name", "description"]
        fields_optional = "__all__"
