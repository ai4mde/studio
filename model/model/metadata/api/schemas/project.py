from ninja import ModelSchema
from metadata.models import Project

class ReadProject(ModelSchema):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description']

class CreateProject(ModelSchema):
    class Meta:
        model = Project
        fields = ['name', 'description']

class UpdateProject(ModelSchema):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description']

class DeleteProject(ModelSchema):
    class Meta:
        model = Project
        fields = ['id']

__all__ = [
    'ReadProject',
    'CreateProject',
    'UpdateProject',
    'DeleteProject'
]