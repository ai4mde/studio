from diagram.models import Diagram, Node
from metadata.models import Classifier
import metadata.specification as spec
from diagram.api.utils.edge import delete_edge


def create_node(diagram: Diagram, data: spec.Classifier):
    classifier = Classifier.objects.create(
        system=diagram.system,
        data=data.model_dump(),
    )
    node = Node.objects.create(
        diagram=diagram,
        cls=classifier,
        data={
            "position": {
                "x": 0,
                "y": 0,
            }
        },
    )
    return node


def import_node(diagram: Diagram, id: str):
    classifier = Classifier.objects.get(pk=id)
    if not classifier:
        return 404

    node = Node.objects.create(
        diagram=diagram,
        cls=classifier,
        data={
            "position": {
                "x": 0,
                "y": 0,
            }
        },
    )
    return node


def delete_node(diagram: Diagram, node_id: str):
    node = diagram.nodes.filter(id=node_id).first()
    if node is None:
        return

    linked_edges = diagram.edges.filter(rel__source=node.cls) | diagram.edges.filter(rel__target=node.cls)
    for linked_edge in linked_edges:
        delete_edge(diagram, linked_edge.id)
    classifier = node.cls
    node.delete()
    if not Node.objects.filter(cls = classifier).exists():
        classifier.delete()
    return True


__all__ = ["create_node", "delete_node"]
