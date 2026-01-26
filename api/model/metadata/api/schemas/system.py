from typing import List, Optional
from uuid import UUID

from ninja import ModelSchema, Schema

from metadata.api.schemas.interface import ExportInterface, ImportInterface
from metadata.models import System, Interface
from diagram.api.schemas.diagram import ExportDiagram, ImportDiagram
from diagram.models import Diagram


class FlatDiagram(Schema):
    id: UUID
    name: str
    description: Optional[str] = None


class SystemDiagrams(Schema):
    classes: List[FlatDiagram]
    activity: List[FlatDiagram]
    usecase: List[FlatDiagram]
    component: List[FlatDiagram]


class ReadSystem(ModelSchema):
    diagrams_by_type: Optional[SystemDiagrams] = None

    class Meta:
        model = System
        fields = ["id", "name", "description", "project"]

    @staticmethod
    def resolve_diagrams_by_type(obj):
        return {
            "classes": obj.diagrams.filter(type="classes"),
            "activity": obj.diagrams.filter(type="activity"),
            "usecase": obj.diagrams.filter(type="usecase"),
            "component": obj.diagrams.filter(type="component"),
        }


class CreateSystem(ModelSchema):
    project: str

    class Meta:
        model = System
        fields = ["name", "description"]


class UpdateSystem(ModelSchema):
    class Meta:
        model = System
        fields = ["name", "description"]


class ExportSystem(ModelSchema):
    interfaces: List[ExportInterface] = []
    diagrams: List[ExportDiagram] = []

    class Meta:
        model = System
        exclude = ["project"]

    @staticmethod
    def resolve_interfaces(obj):
        return Interface.objects.filter(system=obj).all()

    @staticmethod
    def resolve_diagrams(obj):
        return Diagram.objects.filter(system=obj).all()


class ImportSystem(Schema):
    id: str
    name: str
    description: Optional[str] = ""
    interfaces: List[ImportInterface]
    diagrams: List[ImportDiagram]
