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
        # Also make sure the swimlane actor name is set
        node.cls.data['actorNodeName'] = Node.objects.get(id=node.cls.data['actorNode']).cls.data['name']
        node.cls.save()
        swimlane_group = diagram.nodes.filter(cls__data__type='swimlanegroup').first()
        if swimlane_group is None:
            swimlane_group = create_node(diagram, SwimLaneGroup(swimlanes=[]))
        swimlane_group.cls.data['swimlanes'].append({**node.cls.data})
        swimlane_group.cls.save()
        
    return node


def delete_node(diagram: Diagram, node_id: str, delete_child_nodes: bool):
    node = diagram.nodes.filter(id=node_id).first()
    if node is None:
        return

    linked_edges = diagram.edges.filter(rel__source=node.cls) | diagram.edges.filter(rel__target=node.cls)
    for linked_edge in linked_edges:
        delete_edge(diagram, linked_edge.id)

    classifier = node.cls
    if classifier.data['type'] == 'swimlane':
        child_nodes = diagram.nodes.filter(cls__data__parentNode=str(node.id))            
        for child_node in child_nodes:
            if delete_child_nodes:
                delete_node(diagram, child_node.id, False)
            else:
                del child_node.cls.data['parentNode']
                child_node.cls.save()

    node.delete()
    if not Node.objects.filter(cls = classifier).exists():
        classifier.delete()
    return True


__all__ = ["create_node", "delete_node"]
