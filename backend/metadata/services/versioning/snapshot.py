import json
from collections.abc import Callable
from uuid import UUID

from django.core import serializers
from django.db import models
from django.db.models import Q

from diagram.models import Diagram, Edge, EdgeControlPoint, Node
from metadata.models import (
    Action,
    Actor,
    Association,
    Attribute,
    Category,
    ClassClassifier,
    Classifier,
    Component,
    Composition,
    Container,
    ControlFlow,
    Dependency,
    EndpointLabel,
    Enum,
    EnumLiteral,
    Event,
    Final,
    Initial,
    Interface,
    InterfaceClassifier,
    InterfaceRelation,
    Multiplicity,
    Object,
    Operation,
    Page,
    PageSection,
    Project,
    Relation,
    SectionAttribute,
    SectionComponent,
    Signal,
    Swimlane,
    System,
    SystemBoundary,
    SystemClassifier,
    Usecase,
)

# Each value builds a filter for rows owned by the given project.
# A model is included only if it appears in this registry. In particular,
# Release is intentionally omitted: snapshots should not contain snapshots.
PROJECT_MODELS: dict[type[models.Model], Callable[[UUID], Q]] = {
    # Root
    Project: lambda project_id: Q(pk=project_id),
    System: lambda project_id: Q(project_id=project_id),

    # Classifiers and their type-specific records
    Classifier: lambda project_id: Q(system__project_id=project_id),
    ClassClassifier: lambda project_id: Q(classifier__system__project_id=project_id),
    Enum: lambda project_id: Q(classifier__system__project_id=project_id),
    InterfaceClassifier: lambda project_id: Q(classifier__system__project_id=project_id),
    Signal: lambda project_id: Q(classifier__system__project_id=project_id),
    SystemClassifier: lambda project_id: Q(classifier__system__project_id=project_id),
    Container: lambda project_id: Q(classifier__system__project_id=project_id),
    Component: lambda project_id: Q(classifier__system__project_id=project_id),
    SystemBoundary: lambda project_id: Q(classifier__system__project_id=project_id),
    Actor: lambda project_id: Q(classifier__system__project_id=project_id),
    Usecase: lambda project_id: Q(classifier__system__project_id=project_id),
    Swimlane: lambda project_id: Q(classifier__system__project_id=project_id),
    Action: lambda project_id: Q(classifier__system__project_id=project_id),
    Object: lambda project_id: Q(classifier__system__project_id=project_id),
    Event: lambda project_id: Q(classifier__system__project_id=project_id),
    Final: lambda project_id: Q(classifier__system__project_id=project_id),
    Initial: lambda project_id: Q(classifier__system__project_id=project_id),

    # Classifier-owned records
    EnumLiteral: lambda project_id: Q(enum__classifier__system__project_id=project_id),
    Attribute: lambda project_id: Q(uml_class__classifier__system__project_id=project_id),
    Operation: lambda project_id: Q(uml_class__classifier__system__project_id=project_id),

    # Interfaces and their contents
    Interface: lambda project_id: Q(system__project_id=project_id),
    Category: lambda project_id: Q(interface__system__project_id=project_id),
    Page: lambda project_id: Q(interface__system__project_id=project_id),
    SectionComponent: lambda project_id: Q(interface__system__project_id=project_id),
    PageSection: lambda project_id: Q(page__interface__system__project_id=project_id),
    SectionAttribute: lambda project_id: Q(section__interface__system__project_id=project_id),

    # Relations and their type-specific records
    Relation: lambda project_id: Q(system__project_id=project_id),
    Multiplicity: lambda project_id: (
        Q(association__relation__system__project_id=project_id)
        | Q(composition__relation__system__project_id=project_id)
    ),
    EndpointLabel: lambda project_id: (
        Q(association__relation__system__project_id=project_id)
        | Q(composition__relation__system__project_id=project_id)
    ),
    Association: lambda project_id: Q(relation__system__project_id=project_id),
    Composition: lambda project_id: Q(relation__system__project_id=project_id),
    Dependency: lambda project_id: Q(relation__system__project_id=project_id),
    ControlFlow: lambda project_id: Q(relation__system__project_id=project_id),
    InterfaceRelation: lambda project_id: Q(relation__system__project_id=project_id),

    # Diagrams and their layout data
    Diagram: lambda project_id: Q(system__project_id=project_id),
    Node: lambda project_id: Q(diagram__system__project_id=project_id),
    Edge: lambda project_id: Q(diagram__system__project_id=project_id),
    EdgeControlPoint: lambda project_id: Q(edge__diagram__system__project_id=project_id),
}
EXCLUDED_FIELDS: dict[type[models.Model], set[str]] = {
    Project: {"current_release"}
}
SCHEMA_VERSION = 1


def snapshot_project(project_id: UUID | str) -> dict:
    project = Project.objects.only("pk").get(pk=project_id)
    objects: list[dict] = []

    for model, project_filter in PROJECT_MODELS.items():
        rows = model.objects.filter(project_filter(project.pk)).order_by("pk")
        serialized = json.loads(serializers.serialize("json", rows))
        excluded_fields = EXCLUDED_FIELDS.get(model, set())
        
        for obj in serialized:
            for field in excluded_fields:
                obj["fields"].pop(field, None)
        
        objects.extend(serialized)

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": str(project.pk),
        "objects": objects,
    }
