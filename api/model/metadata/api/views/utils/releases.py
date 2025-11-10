
from metadata.models import System, Interface, Release, Classifier, Relation
from diagram.models import Diagram, Node, Edge
from typing import Dict, Any

def serialize_interfaces(system: System):
    out = []
    interfaces = Interface.objects.filter(system=system)
    for interface in interfaces:
        obj = {
            "id": str(interface.id),
            "name": str(interface.name),
            "description": str(interface.description),
            "system": str(interface.system.id),
            "actor": str(interface.actor.id),
            "data": interface.data
        }
        out.append(obj)
    return out


def serialize_nodes(diagram: Diagram):
    out = []
    nodes = Node.objects.filter(diagram=diagram)
    for node in nodes:
        serialized_node = {
            "id": str(node.id),
            "cls": {
                "id": str(node.cls.id),
                "data": node.cls.data,
            },
            "cls_ptr": str(node.cls.id),
            "data": node.data,
        }
        out.append(serialized_node)
    return out


def serialize_edges(diagram: Diagram):
    out = []
    edges = Edge.objects.filter(diagram=diagram)
    for edge in edges:
        serialized_edge = {
            "id": str(edge.id),
            "rel": {
                "id": str(edge.rel.id),
                "data": edge.rel.data,
            },
            "rel_ptr": str(edge.rel.id),
            "source_ptr": str(edge.source.id) if edge.source else None,
            "target_ptr": str(edge.target.id) if edge.target else None,
            "data": edge.data,
        }
        out.append(serialized_edge)
    return out


def serialize_diagrams(system: System):
    out = []
    diagrams = Diagram.objects.filter(system=system)
    for diagram in diagrams:
        serialized_nodes = serialize_nodes(diagram=diagram)
        serialized_edges = serialize_edges(diagram=diagram)
        obj = {
            "id": str(diagram.id),
            "project": str(system.project.id),
            "name": str(diagram.name),
            "description": str(diagram.description),
            "type": str(diagram.type),
            "system": str(diagram.system.id),
            "nodes": serialized_nodes,
            "edges": serialized_edges,
        }
        out.append(obj)
    return out


def load_interfaces(system: System, release: Release) -> bool:
    Interface.objects.filter(system=system).delete()
    
    try:
        for interface in release.interfaces:
            Interface.objects.create(
                id = interface['id'],
                system = system,
                name = interface['name'],
                description = interface['description'],
                actor_id = interface['actor'],
                data = interface['data']
            )
    except:
        return False
    return True


def load_nodes(system: System, diagram: Dict[str, Any]):
    Node.objects.filter(diagram_id=diagram['id']).delete()
    for node in diagram['nodes']:
        Classifier.objects.create(
            id = node['cls']['id'],
            project = system.project,
            system = system,
            data = node['cls']['data']
        )
        Node.objects.create(
            id = node['id'],
            diagram_id = diagram['id'],
            cls_id = node['cls']['id'],
            data = node['data'],
        )


def load_edges(system: System, diagram: Dict[str, Any]):
    Edge.objects.filter(diagram_id=diagram['id']).delete()
    for edge in diagram['edges']:
        source_node = Node.objects.get(id=edge['source_ptr'])
        target_node = Node.objects.get(id=edge['target_ptr'])
        Relation.objects.create(
            id = edge['rel']['id'],
            system = system,
            data = edge['rel']['data'],
            source = source_node.cls,
            target = target_node.cls
        )
        Edge.objects.create(
            id = edge['id'],
            diagram_id = diagram['id'],
            rel_id = edge['rel']['id'],
            source = source_node.cls,
            target = target_node.cls,
            data = edge['data'],
        )


def load_diagrams(system: System, release: Release) -> bool:
    Diagram.objects.filter(system=system).delete()
    Classifier.objects.filter(system=system).delete()
    Relation.objects.filter(system=system).delete()
    
    try:
        for diagram in release.diagrams:
            Diagram.objects.create(
                id = diagram['id'],
                type = diagram['type'],
                name = diagram['name'],
                description = diagram['description'],
                system = system
            )
            load_nodes(system, diagram)
            load_edges(system, diagram)
    except:
        return False
    return True