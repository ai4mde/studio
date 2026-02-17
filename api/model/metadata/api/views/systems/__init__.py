import uuid

from django.db import transaction
from typing import List, Optional

from metadata.api.schemas import CreateSystem, ExportSystem, ReadSystem, UpdateSystem, ImportSystem
from metadata.models import Project, System, Interface
from diagram.models import Diagram, Node, Edge, Relation, Classifier
from .meta import meta
from .classifiers import classifiers, classes, actors
from .relations import relations, classifier_relations
from .node import nodes
from .settings import settings

from ninja import Router, Schema

systems = Router()


@systems.get("/", response=List[ReadSystem])
def list_systems(request, project: Optional[str] = None):
    qs = None
    if project:
        qs = System.objects.filter(project=project)
    else:
        qs = System.objects.all()
    return qs


@systems.get("/{uuid:id}/", response=ReadSystem)
def read_system(request, id):
    return System.objects.prefetch_related("diagrams").get(id=id)


@systems.post("/", response=ReadSystem)
def create_system(request, system: CreateSystem):
    return System.objects.create(
        name=system.name,
        description=system.description,
        project=Project.objects.get(pk=system.project),
    )


@systems.put("/{uuid:id}", response=ReadSystem)
def update_system(request, id, payload: UpdateSystem):
    system = System.objects.get(id=id)
    system.name = payload.name
    system.description = payload.description
    system.save()
    return system


@systems.delete("/{uuid:id}/")
def delete_system(request, id):
    try:
        system = System.objects.get(id=id)
        system.delete()
    except Exception as e:
        raise Exception("Failed to delete system, error: " + e)
    return True


class ImportResult(Schema):
    success: bool
    message: str


@systems.get("/export/{uuid:system_id}/", response=ExportSystem)
def export_system(request, system_id: str):
    system = System.objects.get(id=system_id)
    if not system:
        raise Exception("System not found")
    return system
    

@systems.post("/import/", response=ImportResult)
def import_system(request, system: ImportSystem):
    try:
        with transaction.atomic():
            # 1. Create the Project
            project_obj = Project.objects.create(
                name=system.name,
                description=system.description or "",
            )

            # 2. Create the System
            system_obj = System.objects.create(
                id=uuid.UUID(system.id),
                name=system.name,
                description=system.description or "",
                project=project_obj,
            )


            # 3. Create diagrams
            for diagram in system.diagrams:
                diagram_obj = Diagram.objects.create(
                    id=uuid.UUID(diagram.id),
                    system=system_obj,
                    name=diagram.name,
                    description=diagram.description or "",
                    type=diagram.type,
                )

                # 4. Create the nodes
                for node in diagram.nodes:
                    Node.objects.create(
                        id=uuid.UUID(node.id),
                        cls=Classifier.objects.create(
                            id=uuid.UUID(node.cls_data.id),
                            data=node.cls_data.data,
                            system=system_obj,
                        ),
                        data=node.data.dict(),
                        diagram=diagram_obj,
                    )

                # 5. Create the edges
                for edge in diagram.edges:
                    Edge.objects.create(
                        id=uuid.UUID(edge.id),
                        data=edge.data,
                        diagram=diagram_obj,
                        rel=Relation.objects.create(
                            id=uuid.UUID(edge.rel_data.id),
                            data=edge.rel_data.data,
                            system=system_obj,
                            source=Classifier.objects.get(id=uuid.UUID(edge.rel_data.source)),
                            target=Classifier.objects.get(id=uuid.UUID(edge.rel_data.target)),
                        )
                    )
                
            # 6. Create interfaces
            for interface in system.interfaces:
                Interface.objects.create(
                    id=uuid.UUID(interface.id),
                    name=interface.name,
                    description=interface.description or "",
                    system=system_obj,
                    data=interface.data,
                    actor=Classifier.objects.get(id=uuid.UUID(interface.actor)),
                )
    except Exception as e:
        return ImportResult(success=False, message=f"Failed to import system: {str(e)}")
    return ImportResult(success=True, message="System imported successfully")


systems.add_router("/{uuid:system_id}/meta", meta, tags=["metadata"])
systems.add_router("/{uuid:system_id}/classifiers", classifiers, tags=["metadata"])
systems.add_router("/{uuid:system_id}/classes", classes, tags=["metadata"])
systems.add_router("/{uuid:system_id}/actors", actors, tags=["metadata"])
systems.add_router("/{uuid:system_id}/relations", relations, tags=["metadata"])
systems.add_router("/{uuid:system_id}/classifier-relations", classifier_relations, tags=["metadata"])
systems.add_router("/{uuid:system_id}/nodes", nodes, tags=["metadata"])
systems.add_router("/{uuid:system_id}/settings", settings, tags=["settings"])


__all__ = ["systems"]
