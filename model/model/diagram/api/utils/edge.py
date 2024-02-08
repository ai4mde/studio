from diagram.models import Diagram, Edge, Node
from metadata.models import Relation
import metadata.specification as spec


def create_edge(diagram: Diagram, data: spec.Relation, source: Node, target: Node):
    relation = Relation.objects.create(
        system=diagram.system,
        data=data.model_dump(),
        source=source.cls,
        target=target.cls,
    )

    edge = Edge.objects.create(
        diagram=diagram,
        rel=relation,
        data={},
    )

    return edge


__all__ = ["create_edge"]
