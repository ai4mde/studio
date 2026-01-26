from typing import Optional, List

from ninja import Router

from diagram.api.schemas import NodeSchema
from diagram.models import Node
from metadata.models import System


nodes = Router()

@nodes.get("/", response=List[NodeSchema])
def get_nodes(request, node_type: Optional[str] = None):
    if not request.resolver_match:
        return 500, "Resolver match not found"
    
    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, "System not found"
    
    nodes = Node.objects.filter(
        diagram__id__in=system.diagrams.values_list("id", flat=True)
    )

    if node_type:
        nodes = nodes.filter(cls__data__type=node_type)
    return nodes

