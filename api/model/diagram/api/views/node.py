from typing import List
from django.http import HttpRequest
from django.core import serializers
from django.db.models import Q

from ninja import Router, Schema
from pydantic import BaseModel

import diagram.api.utils as utils

from diagram.api.schemas import CreateNode, PatchNode, NodeSchema, FullDiagram, DiagramUsageItem, ClassifierUsageResponse

from metadata.specification import Classifier
from metadata.models import Classifier as MetaClassifier, Relation

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


@node.get("/{uuid:node_id}/classifier-usage/", response=ClassifierUsageResponse)
def classifier_usage(request: HttpRequest, node_id: str):
    diagram = utils.get_diagram(request)
    
    if not diagram:
        return 404, "Diagram not found"
    
    node = diagram.nodes.select_related("cls").filter(id=node_id).first()
    if not node:
        return 404, "Node not found"

    cls = node.cls
    cls_name = (cls.data or {}).get("name", str(cls.id))
    nodes = (
        Node.objects
        .select_related("diagram", "diagram__system")
        .filter(cls=cls)
        .exclude(diagram=diagram)
    )

    seen = set()
    usage_items = []

    for n in nodes:
        d = n.diagram
        if d.id in seen:
            continue
        seen.add(d.id)

        usage_items.append(DiagramUsageItem(
            diagram_id = str(d.id),
            diagram_name = d.name,
            system_id = str(d.system.id),
            system_name = d.system.name,
        ))

    return ClassifierUsageResponse(
        classifier_id = str(cls.id),
        classifier_name = cls_name,
        usages = usage_items,
    )

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
def remove_node(request: HttpRequest, node_id: str):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"

    if utils.remove_node(diagram=diagram, node_id=node_id):
        return True
    return False


@node.delete("/{uuid:node_id}/hard/", response=bool)
def hard_delete_classifier(request: HttpRequest, node_id: str):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"
    
    node = Node.objects.filter(id=node_id).first()
    if not node:
        return 404, "Node not found"
    
    return utils.delete_classifier_everywhere(str(node.cls_id))


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

@node.post("/import/{uuid:classifier_id}/", response=NodeSchema)
def import_node(request: HttpRequest, classifier_id: str):
    diagram = utils.get_diagram(request)

    if not diagram:
        return 404, "Diagram not found"
    
    try:
        cls = MetaClassifier.objects.get(pk=classifier_id)
    except MetaClassifier.DoesNotExist:
        return 404, "Classifier not found"

    # Import the node to this diagram
    node = utils.import_node(diagram, classifier_id)
    cls = node.cls

    # Map of classifier id -> node
    nodes = diagram.nodes.select_related("cls").all()
    classifier_ids_in_diagram = [n.cls_id for n in nodes]
    nodes_by_classifier_id = {str(n.cls_id): n for n in nodes}

    relations = Relation.objects.filter(
        system__project=diagram.system.project
    ).filter(
        Q(source=cls, target_id__in=nodes_by_classifier_id.keys()) |
        Q(target=cls, source_id__in=nodes_by_classifier_id.keys())
    )

    # Add edge to diagram
    for rel in relations:
        # Create edge
        Edge.objects.get_or_create(
            diagram=diagram,
            rel=rel,
            defaults={"data": {}},
        )

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
    
    system_id = str(diagram.system_id)

    # Build classifier name map and context
    name_map: dict[str, str] = {}
    clf_data_map: dict[str, dict] = {}
    for clf in MetaClassifier.objects.filter(system_id=system_id):
        data = clf.data or {}
        clf_name = data.get("name") or ""
        if clf_name and data.get("type") in {"class", "entity", "model"}:
            name_map[str(clf.id)] = clf_name
            clf_data_map[clf_name] = data

    model_lines: list[str] = []
    rel_lines: list[str] = []
    for clf_name, data in clf_data_map.items():
        attrs = data.get("attributes") or []
        parts = [f"{a.get('name')}({a.get('type','str')})" for a in attrs if a.get("name")]
        model_lines.append(f"{clf_name}: " + (", ".join(parts) or "(no fields)"))

    for rel in Relation.objects.filter(system_id=system_id):
        rd = rel.data or {}
        src_name = name_map.get(str(rel.source_id), "")
        tgt_name = name_map.get(str(rel.target_id), "")
        if not src_name or not tgt_name:
            continue
        mult = rd.get("multiplicity") or {}
        tgt_m = str(mult.get("target", "*"))
        is_many = "*" in tgt_m or "n" in tgt_m.lower()
        if is_many:
            rel_lines.append(f"{src_name} 1-many {tgt_name}: self.{tgt_name.lower()}_set.all()")
        else:
            rel_lines.append(f"{src_name} →{tgt_name}: self.{tgt_name.lower()}")

    target_name = node.cls.data.get("name") or ""
    target_clf = clf_data_map.get(target_name) or {}
    target_attrs = target_clf.get("attributes") or []
    clf_summary = f"{target_name}: " + ", ".join(
        f"{a.get('name')}({a.get('type','str')})" for a in target_attrs if a.get("name")
    )
    reverse_hints = "; ".join(
        line.split(": ", 1)[1]
        for line in rel_lines
        if line.startswith(f"{target_name} 1-many")
    ) or "self.relatedmodel_set.all()"

    input_data = {
        "django_version": "5.0.2",
        "target_class": target_name,
        "method_name": name,
        "method_description": description,
        "classifier_summary": clf_summary,
        "model_context": "\n".join(model_lines) or "(none)",
        "relation_context": "\n".join(rel_lines) or "(none)",
        "reverse_fk_pattern": reverse_hints,
    }

    reply = llm_handler(prompt_name="DIAGRAM_GENERATE_METHOD", model=model, input_data=input_data)
    return remove_reply_markdown(reply)
    
__all__ = ["node"]
