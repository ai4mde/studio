from diagram.models import Node
from metadata.models import Classifier


UNKNOWN_ACTOR = "Unknown actor"


def resolve_actor_name(actor_node_id: str) -> str:
    node = Node.objects.filter(id=actor_node_id).select_related("cls").first()
    if node:
        return node.cls.data.get("name", UNKNOWN_ACTOR)

    actor = Classifier.objects.filter(id=actor_node_id, data__type="actor").first()
    if actor:
        return actor.data.get("name", UNKNOWN_ACTOR)

    return UNKNOWN_ACTOR
