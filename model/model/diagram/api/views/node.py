from typing import List
from django.http import HttpRequest

from ninja import Router
from pydantic import BaseModel

import diagram.api.utils as utils

from diagram.api.schemas import CreateNode, PatchNode, NodeSchema

from metadata.specification import Classifier

node = Router()


@node.get("/", response=List[NodeSchema])
def list_nodes(request):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    return diagram.nodes.all()


@node.post("/", response=NodeSchema)
def create_node(request: HttpRequest, data: CreateNode):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    node = utils.create_node(diagram, data.cls)

    return node


@node.get("/{uuid:node_id}/", response=NodeSchema)
def read_node(request: HttpRequest, node_id: str):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    return diagram.nodes.get(id=node_id)


@node.delete("/{uuid:node_id}/", response=bool)
def delete_node(request: HttpRequest, node_id: str):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    diagram.nodes.filter(id=node_id).delete()
    return True


class PatchModel(BaseModel):
    cls: Classifier


@node.patch("/{uuid:node_id}/", response=NodeSchema)
def update_node(request: HttpRequest, node_id: str, data: PatchNode):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    node = diagram.nodes.get(id=node_id)

    if data.cls is not None:
        new_cls = {**node.cls.data, **data.cls}
        PatchModel.model_validate({"cls": new_cls})
        node.cls.data = new_cls
        node.cls.save()

    if data.data is not None:
        node.data = {**node.data, **data.data.model_dump()}
        node.save()

    return node


__all__ = ["node"]
