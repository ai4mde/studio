from typing import List
from django.http import HttpRequest
from django.core import serializers

from ninja import Router
from pydantic import BaseModel

import diagram.api.utils as utils

from diagram.api.schemas import CreateNode, PatchNode, NodeSchema, FullDiagram

from metadata.specification import Classifier

from diagram.models import Node, Edge, Diagram

from llm.handler import llm_handler, remove_reply_markdown

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


@node.get("/{uuid:node_id}/enums/", response=List[NodeSchema])
def get_connected_enums(request: HttpRequest, node_id: str):
    out = []
    node = Node.objects.get(pk=node_id)
    if not node:
        return 404, "Node not found"
    
    edges_target = Edge.objects.filter(rel__source=node.cls)
    for edge in edges_target:
        if edge.rel.data['type'] != 'dependency':
            continue
        if edge.target.cls.data['type'] == 'enum':
            out.append(edge.target)

    return out


@node.delete("/{uuid:node_id}/", response=bool)
def delete_node(request: HttpRequest, node_id: str, deleteChildNodes: bool = False):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    if utils.delete_node(diagram=diagram, node_id=node_id, delete_child_nodes=deleteChildNodes):
        return True
    return False


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
        if node.cls.data['type'] == 'swimlane':
            node.cls.data['actorNodeName'] = Node.objects.get(id=node.cls.data['actorNode']).cls.data['name']
        node.cls.save()

    if data.data is not None:
        node.data = {**node.data, **data.data.model_dump()}
        node.save()

    return node


@node.post("{uuid:node_id}/generate_attribute/", response={200: str, 404: str, 422: str})
def generate_attribute(request: HttpRequest, node_id: str, name: str, type: str, description: str, model: str = "mixtral-8x7b-32768"):
    diagram = utils.get_diagram(request)
    if not diagram:
        return 404, "Diagram not found"
    
    node = diagram.nodes.get(id=node_id)
    if not node:
        return 404, "Node not found"
    
    if node.cls.data["type"] != "class":
        return 422, "Node is not a class"
    
    diagrams = Diagram.objects.filter(system=diagram.system)
    diagram_data = [FullDiagram.from_orm(diagram) for diagram in diagrams]
    input_data = {
        "django_version": "5.0.2", # TODO: put this in env
        "attribute_name": name,
        "attribute_return_type": type,
        "attribute_description": description, # TODO: prompt injection protection
        "classifier_metadata": serializers.serialize('json', [node.cls]),
        "diagrams_metadata": diagram_data
    }
    reply = llm_handler(prompt_name = "DIAGRAM_GENERATE_ATTRIBUTE", 
                         model = model,
                         input_data = input_data)

    return remove_reply_markdown(reply)
    

@node.post("/{uuid:node_id}/generate_method/", response={200: str, 404: str, 422: str})
def generate_method(request: HttpRequest, node_id: str, name: str, description: str, model: str = "mixtral-8x7b-32768"):
    diagram = utils.get_diagram(request)
    if not diagram:
        return 404, "Diagram not found"
    
    node = diagram.nodes.get(id=node_id)
    if not node:
        return 404, "Node not found"
    
    if node.cls.data["type"] != "class":
        return 422, "Node is not a class"
    
    diagrams = Diagram.objects.filter(system=diagram.system)
    diagram_data = [FullDiagram.from_orm(diagram) for diagram in diagrams]
    input_data = {
        "django_version": "5.0.2", # TODO: put this in env
        "method_name": name,
        "method_description": description, # TODO: prompt injection protection
        "classifier_metadata": serializers.serialize('json', [node.cls]),
        "diagrams_metadata": diagram_data
    }

    reply = llm_handler(prompt_name = "DIAGRAM_GENERATE_METHOD", 
                         model = model,
                         input_data = input_data)

    return remove_reply_markdown(reply)
    
__all__ = ["node"]
