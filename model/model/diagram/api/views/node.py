from typing import List
from django.http import HttpRequest

from ninja import Router

import diagram.api.utils as utils

from diagram.api.schemas import CreateNode, ListNodes, NodeSchema

from metadata.specification import Classifier

node = Router()

@node.get('/', response=List[NodeSchema])
def list_nodes(request):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    return diagram.nodes.all()

@node.post('/', response=NodeSchema)
def create_node(request: HttpRequest, data: CreateNode):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    node = utils.create_node(diagram, data.cls)

    return node

@node.get('/{uuid:node_id}', response=NodeSchema)
def read_node(request: HttpRequest, node_id: str):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    return diagram.nodes.get(id=node_id)


__all__ = ["node"]
