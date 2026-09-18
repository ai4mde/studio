from uuid import UUID

from ninja import ModelSchema

from diagram.models import Diagram


class DiagramRead(ModelSchema):    
    class Meta:
        model = Diagram
        fields = ["id", "name", "description", "type"]


class DiagramCreate(ModelSchema):
    system_id: UUID

    class Meta:
        model = Diagram
        fields = ["name", "description", "type"]
        fields_optional = ["name", "description"]


class DiagramUpdate(ModelSchema):
    class Meta:
        model = Diagram
        fields = ["name", "description"]
        fields_optional = "_all__"
