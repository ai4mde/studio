from typing import Optional
from django.db import transaction
from diagram.models import Diagram, Node, Edge, get_default_background_color_hex, get_default_text_color_hex
from metadata.models import Classifier, Relation
import metadata.specification as spec
from diagram.api.utils.edge import remove_edge_from_diagram, delete_relation_everywhere


def create_node(diagram: Diagram, data: spec.Classifier):
    classifier = Classifier.objects.create(
        project=diagram.system.project,
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
            },
            "background_color_hex": get_default_background_color_hex(diagram.system, data.type),
            "text_color_hex": get_default_text_color_hex(diagram.system, data.type),
        }
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
            },
            "background_color_hex": get_default_background_color_hex(diagram.system, classifier.data.get("type", None)),
            "text_color_hex": get_default_text_color_hex(diagram.system, classifier.data.get("type", None)),
        }
    )
    return node


def remove_node(diagram: Diagram, node_id: str):
    node = diagram.nodes.filter(id=node_id).first()
    if node is None:
        return False

    linked_edges = diagram.edges.filter(rel__source=node.cls) | diagram.edges.filter(rel__target=node.cls)
    for linked_edge in linked_edges:
        remove_edge_from_diagram(diagram, linked_edge.id)
    
    node.delete()
    return True


def delete_classifier_everywhere(classifier_id: str):
    cls = Classifier.objects.filter(id=classifier_id).first()
    if cls is None:
        return False
    
    with transaction.atomic():
        nodes = Node.objects.select_related("diagram").filter(cls=cls)

        for node in nodes:
            diagram = node.diagram
            linked_edges = diagram.edges.filter(rel__source=node.cls) | diagram.edges.filter(rel__target=node.cls)

            for linked_edge in linked_edges:
                delete_relation_everywhere(diagram, linked_edge.id)

            node.delete()

        Relation.objects.filter(source=cls).delete()
        Relation.objects.filter(target=cls).delete()

        cls.delete()

    return True


__all__ = ["create_node", "remove_node", "delete_classifier_everywhere"]
