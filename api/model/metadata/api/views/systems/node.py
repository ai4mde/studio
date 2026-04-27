from typing import Optional, List

from ninja import Router, Schema

from diagram.api.schemas import NodeSchema
from diagram.models import Node
from metadata.models import System


nodes = Router()


class ErrorSchema(Schema):
    detail: str

@nodes.get("/", response={200: List[NodeSchema], 404: ErrorSchema, 500: ErrorSchema})
def get_nodes(request, node_type: Optional[str] = None):
    if not request.resolver_match:
        return 500, {"detail": "Resolver match not found"}
    
    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)

    if not system:
        return 404, {"detail": "System not found"}
    
    nodes = Node.objects.filter(
        diagram__id__in=system.diagrams.values_list("id", flat=True)
    )

    if node_type:
        nodes = nodes.filter(cls__data__type=node_type)
    return nodes

