from diagram.models import Diagram, Node
from metadata.models import Classifier
import metadata.specification as spec
from diagram.api.utils.edge import delete_edge
from metadata.specification.activity.classifiers.swimlane import SwimLaneGroup


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
    # In case a swimlane is added make sure all the swimlanes are grouped together
    if data.type == 'swimlane':
        swimlane_group = diagram.nodes.filter(cls__data__type='swimlanegroup').first()
        if swimlane_group is None:
            swimlane_group = create_node(diagram, SwimLaneGroup(swimlanes=[]))
        swimlane_group.cls.data['swimlanes'].append({**node.cls.data})
        swimlane_group.cls.save()

    return node


def delete_node(diagram: Diagram, node_id: str):
    node = diagram.nodes.filter(id=node_id).first()
    if node is None:
        return
    
    if node.cls.data.get('type') == 'actor':
        delete_actor(node)

    linked_edges = diagram.edges.filter(rel__source=node.cls) | diagram.edges.filter(rel__target=node.cls)
    for linked_edge in linked_edges:
        delete_edge(diagram, linked_edge.id)
    classifier = node.cls
    node.delete()
    if not Node.objects.filter(cls = classifier).exists():
        classifier.delete()
    return True


def delete_actor(actor_node: Node):
    """
        After an actor node is deleted the swimlanes should be deleted as well and the action nodes should be updated.
    """
    nodes = Node.objects.filter(diagram__in=Diagram.objects.filter(system=actor_node.diagram.system, type='activity'))
    for node in nodes:
        if node.cls.data.get('actorNode') == str(actor_node.id):
            node.cls.data = {
                **node.cls.data,
                'actorNode': None
            }
        elif node.cls.data.get('type') == 'swimlanegroup':
            # In case it is the last swimlane in the group remove the group
            swimlanes = node.cls.data.get('swimlanes', [])
            if not swimlanes or len(swimlanes) == 1:
                delete_node(node.diagram, str(node.id))
                continue
            
            # Remove the swimlane from the group
            for swimlane in node.cls.data.get('swimlanes', []):
                if swimlane.get('actorNode') == str(actor_node.id):
                    node.cls.data = {
                        **node.cls.data,
                        'swimlanes': [sl for sl in node.cls.data.get('swimlanes', []) if sl.get('actorNode') != str(actor_node.id)]
                    }
        node.cls.save()


__all__ = ["create_node", "delete_node"]
