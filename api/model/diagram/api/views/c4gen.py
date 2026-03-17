from typing import List

from diagram.api.schemas import (
    FullDiagram,
    ImportC4Diagram,
)
from diagram.models import Diagram
from metadata.models import System
from django.db import transaction
from ninja import Router


c4gen = Router()

def build_container_diagram(system, diagram_name, containers, relations, id_map):
    container_diagram = Diagram.objects.create(
        name=diagram_name,
        system=system,
        type="classes",
    )
    try:
        # Process containers
        for container in containers:
            classifier_data = {
                "id": container.get("id"),
                "data": {
                    "type": "c4container",
                    "name": container.get("name"),
                    "label": container.get("description", ""),
                    "technologies": container.get("programming_languages", []),
                }
            }
            container_diagram.add_node_and_classifier(classifier_data, id_map)
        # Process relations
        for relation in relations:
            source_id = id_map.get(str(relation.get("source_id")))
            target_id = id_map.get(str(relation.get("target_id")))
            
            if source_id and target_id:
                relation_data = {
                    "source": source_id,
                    "target": target_id,
                    "data": {
                        "type": relation.get("type", "dependency"),
                        "label": relation.get("label", ""),
                    }
                }
                container_diagram.add_edge_and_relation(relation_data, id_map)
        container_diagram.auto_layout()  # Auto-layout after adding all relations
        return container_diagram
    except Exception as e:
        raise Exception(f"Failed to build container diagram: {e}")
    
def build_component_diagram(system, diagram_name, components, relations, id_map):
    component_diagram = Diagram.objects.create(
        name=diagram_name,
        system=system,
        type="classes",
    )
    try:
        # Process components
        for component in components:
            classifier_data = {
                "id": component.get("id"),
                "data": {
                    "type": "c4component",
                    "name": component.get("name"),
                    "label": component.get("description", ""),
                }
            }
            component_diagram.add_node_and_classifier(classifier_data, id_map)
        # Process relations
        for relation in relations:
            source_id = id_map.get(str(relation.get("source_id")))
            target_id = id_map.get(str(relation.get("target_id")))
            
            if source_id and target_id:
                relation_data = {
                    "source": source_id,
                    "target": target_id,
                    "data": {
                        "type": relation.get("type", "dependency"),
                        "label": relation.get("label", ""),
                    }
                }
                component_diagram.add_edge_and_relation(relation_data, id_map)
        component_diagram.auto_layout()  # Auto-layout after adding all relations
        return component_diagram
    except Exception as e:
        raise Exception(f"Failed to build component diagram: {e}")

@c4gen.post("/import-c4", response=List[FullDiagram])
@transaction.atomic
def import_c4_diagram(request, body: ImportC4Diagram):
    """
    Import a C4 model and convert it to a class diagram.
    
    The C4 model should contain:
    - containers: List of C4 containers
    - components: List of C4 components
    - relations: List of relationships between containers/components
    """
    system = System.objects.get(id=body.system)
    containers = body.c4_model.get("containers", [])
    components = body.c4_model.get("components", [])
    relations = body.c4_model.get("relations", [])
    id_map = {}
    container_diagram = build_container_diagram(system, body.diagram_name + " - Containers", containers, relations, id_map)

    component_diagrams = []
    for container in containers:
        container_id = container.get("id")
        container_components = components.get(container_id, [])
        
        # Filter relations to only include those within this container's components
        component_ids = {c.get("id") for c in container_components}
        filtered_relations = [
            r for r in relations 
            if str(r.get("source_id")) in component_ids and str(r.get("target_id")) in component_ids
        ]
        
        component_diagram = build_component_diagram(system, body.diagram_name + f" - Components of {container.get('name')}", container_components, filtered_relations, id_map)
        component_diagrams.append(component_diagram)

    return [container_diagram] + component_diagrams