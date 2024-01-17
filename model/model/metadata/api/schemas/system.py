from ninja import ModelSchema
from metadata.models import System

class ReadSystem(ModelSchema):
    class Meta:
        model = System
        fields = ['id', 'name', 'description']

class CreateSystem(ModelSchema):
    class Meta:
        model = System
        fields = ['name', 'description']

class UpdateSystem(ModelSchema):
    class Meta:
        model = System
        fields = ['name', 'description']