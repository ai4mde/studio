from typing import List, Optional
from uuid import UUID

from ninja import ModelSchema, Schema

from metadata.api.schemas.meta import ExportClassifier, ExportRelation, ImportClassifier, ImportRelation
from metadata.models import System, Classifier, Relation, Interface
from diagram.models import Diagram
from diagram.api.schemas.diagram import ExportDiagram, ImportDiagram
from metadata.api.schemas.interface import ExportInterface, ImportInterface


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
    # To be used when exporting the entire system
    # This is because if a classifier is imported into this system
    # It will not be included in the list of classifiers
    # And a Node will reference a classifier that is not included in the export
    # Which will cause the import to fail
    diagrams: List[ExportDiagram] = []
    classifiers: List[ExportClassifier] = []
    relations: List[ExportRelation] = []
    interfaces: List[ExportInterface] = []

    class Meta:
        model = System
        fields = "__all__"

    @staticmethod
    def resolve_diagrams(obj):
        return Diagram.objects.filter(system=obj)
    
    @staticmethod
    def resolve_classifiers(obj):
        return Classifier.objects.filter(system=obj)

    @staticmethod
    def resolve_relations(obj):
        return Relation.objects.filter(system=obj)

    @staticmethod
    def resolve_interfaces(obj):
        return Interface.objects.filter(system=obj)
    

class ExportSingleSystem(ExportSystem):
    imported_classifiers: List[ExportClassifier]
    
    @staticmethod
    def resolve_imported_classifiers(obj):
        imported = {}

        diagrams = Diagram.objects.filter(system=obj).prefetch_related("nodes__cls")

        for diagram in diagrams:
            for node in diagram.nodes.all():
                if node.cls and node.cls.system_id != obj.id:
                    imported[node.cls.id] = node.cls
        return list(imported.values())


class ImportSystem(Schema):
    id: str
    name: str
    description: Optional[str] = None
    project: str
    diagrams: List[ImportDiagram] = []
    classifiers: List[ImportClassifier] = []
    relations: List[ImportRelation] = []
    interfaces: List[ImportInterface] = []


class ImportSingleSystem(ImportSystem):
    imported_classifiers: List[ImportClassifier]
