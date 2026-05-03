from typing import List, Optional
import json

from metadata.api.schemas import CreateInterface, ReadInterface, UpdateInterface, ExportSingleSystem
from metadata.api.schemas.generator import GeneratePrototypeRequest, GeneratePrototypeResponse
from metadata.models import System, Interface, Classifier
from django.http import HttpRequest
from metadata.api.views.defaulting import create_default_interface
from llm.handler import llm_handler, remove_reply_markdown
from llm.template_renderer import render_layout, render_preview

from ninja import Router

interfaces = Router()


@interfaces.get("/", response=List[ReadInterface])
def list_interfaces(request, system: Optional[str] = None):
    qs = None
    if system:
        qs = Interface.objects.filter(system=system).order_by('id')
    else:
        qs = Interface.objects.all()
    return qs


@interfaces.post("/{uuid:id}/generate/", response=GeneratePrototypeResponse)
def generate_interface_prototype(request, id: str, payload: GeneratePrototypeRequest):
    try:
        interface = Interface.objects.get(id=id)
    except Interface.DoesNotExist:
        return 404, {"message": "Interface not found"}
        
    system = interface.system

    # Template-based path: skip LLM when no prompt or when override data is provided.
    # Always renders via page_preview.html.jinja2 → standalone HTML suitable for iframe display.
    if not payload.prompt or payload.interface_data_override is not None:
        interface_data = payload.interface_data_override or interface.data or {}
        classifiers = [{"id": str(c.id), "data": c.data} for c in system.classifiers.all()]
        files = render_preview(
            interface_data=interface_data,
            classifiers=classifiers,
            interface_name=interface.name,
        )
        return {
            "message": f"Generated {len(files)} page(s).",
            "files": files,
        }

    # Construct system metadata for LLM path
    diagrams_data = []
    for d in system.diagrams.all():
        nodes_data = []
        for node in d.nodes.select_related('cls').all():
            nodes_data.append({
                "id": str(node.id),
                "cls_ptr": str(node.cls_id),
                "cls": node.cls.data,
                "data": node.data,
            })
        edges_data = []
        for edge in d.edges.select_related('rel').all():
            src_node = d.nodes.filter(cls=edge.rel.source_id).first()
            tgt_node = d.nodes.filter(cls=edge.rel.target_id).first()
            edges_data.append({
                "id": str(edge.id),
                "rel": edge.rel.data,
                "source_ptr": str(src_node.id) if src_node else None,
                "target_ptr": str(tgt_node.id) if tgt_node else None,
                "data": edge.data,
            })
        diagrams_data.append({"id": str(d.id), "name": d.name, "type": d.type, "nodes": nodes_data, "edges": edges_data})

    system_data = {
        "id": str(system.id),
        "name": system.name,
        "description": system.description,
        "project": str(system.project_id),
        "diagrams": diagrams_data,
        "classifiers": [dict(id=str(c.id), data=c.data) for c in system.classifiers.all()],
        "relations": [dict(id=str(r.id), data=r.data, source=str(r.source_id), target=str(r.target_id)) for r in system.relations.all()],
        "interfaces": [dict(id=str(i.id), name=i.name, description=i.description, data=i.data) for i in system.interfaces.all()]
    }

    interface_metadata = {
        "id": str(interface.id),
        "name": interface.name,
        "description": interface.description,
        "data": interface.data
    }

    input_data = {
        "metadata": json.dumps(system_data, indent=2),
        "prompt": payload.prompt,
        "interface_metadata": json.dumps(interface_metadata, indent=2)
    }

    response_text = llm_handler("GEMINI_MAKE_PROTOTYPE", model=payload.model, input_data=input_data)
    clean_json = remove_reply_markdown(response_text)

    try:
        result = json.loads(clean_json)
        return result
    except Exception as e:
        raise Exception(f"Failed to parse LLM response as JSON: {e}\nResponse: {clean_json}")


@interfaces.get("/{uuid:id}/", response=ReadInterface)
def read_interface(request, id):
    return Interface.objects.get(id=id)


@interfaces.post("/", response=ReadInterface)
def create_interface(request, interface: CreateInterface):
    return Interface.objects.create(
        name=interface.name,
        description=interface.description,
        system=System.objects.get(pk=interface.system),
        actor=Classifier.objects.get(pk=interface.actor),
        data=interface.data
    )


@interfaces.post("/default", response=List[ReadInterface])
def create_default_interfaces(request, system_id: str):
    system = System.objects.get(pk=system_id)
    if not system:
        return []
    
    actors = system.classifiers.filter(data__type='actor')

    out = []
    for actor in actors:
        interface = create_default_interface(system, actor)
        out.append(interface)
    
    return out


@interfaces.put("/{uuid:id}/", response=bool)
def update_interface(request, id, interface: UpdateInterface):
    try: 
        Interface.objects.filter(id=id).update(name=interface.name,
                                               description=interface.description,
                                               system=interface.system, 
                                               data=interface.data)
    except Interface.DoesNotExist:
        return False
    return True


@interfaces.delete("/{uuid:interface_id}", response=bool)
def delete_interface(request, interface_id):
    try:
        Interface.objects.filter(id=interface_id).delete()
    except Interface.DoesNotExist:
        return False
    return True



__all__ = ["interfaces"]
