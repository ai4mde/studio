from diagram.models import Diagram, Node
from metadata.models import Classifier
import metadata.specification as spec


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


__all__ = ["create_node"]
