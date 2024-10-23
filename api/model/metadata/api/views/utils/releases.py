
from metadata.models import System, Interface
from diagram.models import Diagram, Node, Edge

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