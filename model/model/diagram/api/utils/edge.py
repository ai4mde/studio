from diagram.models import Diagram, Edge, Node
from metadata.models import Relation
import metadata.specification as spec


def create_edge(diagram: Diagram, data: spec.Relation, source: Node, target: Node):
    # Create the relation
    relation = Relation.objects.create(
        system=diagram.system,
        data=data.model_dump(),
        source=source.cls,
        target=target.cls,
    )

    # Create the edge
    edge = Edge.objects.create(
        diagram=diagram,
        rel=relation,
        data={},
    )

    return edge

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


__all__ = ["create_edge", "fetch_and_update_edges"]
