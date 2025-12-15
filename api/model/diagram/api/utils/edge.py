from diagram.models import Diagram, Edge, Node
from metadata.models import Relation
import metadata.specification as spec
from django.db import transaction


def _relation_data_key(rel_data: dict) -> dict:
    return rel_data or {}


def _find_node_for_classifier(diagram: Diagram, cls) -> Node | None:
    node = diagram.nodes.filter(cls=cls).first()
    if node:
        return node
    
    # TODO: See if this works or need to search by name
    

def _get_or_create_relation_for_diagram(diagram: Diagram, source_cls, target_cls, rel_data: dict) -> Relation:
    rel_data = _relation_data_key(rel_data)

    existing = Relation.objects.filter(
        system=diagram.system,
        source=source_cls,
        target=target_cls,
        data=rel_data,
    ).first()
    if existing:
        return existing
    
    return Relation.objects.create(
        system=diagram.system,
        source=source_cls,
        target=target_cls,
        data=rel_data,
    )


def _propagate_edge_to_project(diagram: Diagram, source: Node, target: Node, rel_data: dict):
    project = diagram.system.project

    other_diagrams = Diagram.objects.filter(system__project=project, type=diagram.type).exclude(id=diagram.id)

    for d in other_diagrams:
        # only propagate if both endpoints exist in that diagram
        n1 = _find_node_for_classifier(d, source.cls)
        n2 = _find_node_for_classifier(d, target.cls)

        if not n1 or not n2:
            continue

        rel = _get_or_create_relation_for_diagram(d, n1.cls, n2.cls, rel_data)

        Edge.objects.get_or_create(
            diagram=d,
            rel=rel,
            defaults={"data": {}},
        )


def create_edge(diagram: Diagram, data: spec.Relation, source: Node, target: Node, *, propagate: bool = True):
    rel_data = data.model_dump()

    with transaction.atomic():
        # Create the relation
        relation = Relation.objects.create(
            system=diagram.system,
            data=rel_data,
            source=source.cls,
            target=target.cls,
        )

        # Create the edge
        edge = Edge.objects.create(
            diagram=diagram,
            rel=relation,
            data={},
        )

        if propagate:
            _propagate_edge_to_project(diagram, source, target, rel_data)

    return edge


def delete_edge(diagram: Diagram, edge_id: str):
    edge = diagram.edges.filter(id=edge_id).first()
    relation = edge.rel
    edge.delete()
    if not Edge.objects.filter(rel = relation).exists():
        relation.delete()
    return True


def fetch_and_update_edges(diagram: Diagram):
    # Fetch all the nodes for the diagram
    nodes = diagram.nodes.all()

    # Fetch all the classifiers for the nodes
    classifiers = [node.cls for node in nodes]

    # Get all the relations between the nodes
    relations = Relation.objects.filter(
        source__in=classifiers,
        target__in=classifiers,
    )

    # Fetch all the edges for the diagram
    edges = diagram.edges.all()

    # Add edges for the relations that don't have an edge
    for relation in relations:
        if not edges.filter(rel=relation).exists():
            Edge.objects.create(
                diagram=diagram,
                rel=relation,
                data={},
            )

    # Remove the edges that don't have a relation
    for edge in edges:
        if not relations.filter(id=edge.rel.id).exists():
            edge.delete()

    return diagram.edges.all()


__all__ = ["create_edge", "delete_edge", "fetch_and_update_edges"]
