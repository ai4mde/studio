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

    # --- 4-Agent Pipeline Implementation ---
    
    # 1. Context Preparation
    # Renderer expects this format: list of {"id": ..., "data": ...}
    renderer_classifiers = [dict(id=str(c.id), data=c.data) for c in system.classifiers.all()]
    
    # LLM context (simplified and explicit for better reasoning)
    llm_classifiers = []
    for c in system.classifiers.all():
        llm_classifiers.append({
            "id": str(c.id),
            "name": c.data.get("name"),
            "type": c.data.get("type"),
            "attributes": [
                {"id": a.get("id"), "name": a.get("name")} 
                for a in c.data.get("attributes", [])
            ]
        })

    system_context = {
        "id": str(system.id),
        "system_name": system.name,
        "available_entities": llm_classifiers,
        "relations": [
            {
                "id": str(r.id), 
                "source_class_id": str(r.source_id), 
                "target_class_id": str(r.target_id),
                "type": r.data.get("type")
            } for r in system.relations.all()
        ]
    }
    
    interface_metadata = {
        "id": str(interface.id),
        "name": interface.name,
        "data": interface.data
    }

    # 1. Strategist
    strat_resp = llm_handler("STRATEGIST", model=payload.model, input_data={
        "metadata": json.dumps(system_context),
        "interface_metadata": json.dumps(interface_metadata),
        "prompt": payload.prompt
    })
    strategy_data = json.loads(remove_reply_markdown(strat_resp))
    strategy = strategy_data.get("strategy", "")
    
    # 2. Architect (Structure)
    arch_resp = llm_handler("ARCHITECT", model=payload.model, input_data={
        "metadata": json.dumps(system_context),
        "strategy": strategy,
        "interface_json": json.dumps({
            "pages": interface.data.get("pages", []),
            "sections": interface.data.get("sections", [])
        })
    })
    arch_json = json.loads(remove_reply_markdown(arch_resp))
    
    # 3. Stylist (Aesthetics)
    style_resp = llm_handler("STYLIST", model=payload.model, input_data={
        "strategy": strategy,
        "styling_json": json.dumps(interface.data.get("styling", {}))
    })
    style_json = json.loads(remove_reply_markdown(style_resp))
    
    # Merge Results Surgically
    new_interface_data = interface.data.copy()
    
    # Update Structure
    if isinstance(arch_json, dict):
        if "pages" in arch_json: new_interface_data["pages"] = arch_json["pages"]
        if "sections" in arch_json: new_interface_data["sections"] = arch_json["sections"]
    
    # Update Aesthetics
    if isinstance(style_json, dict):
        if "styling" in style_json: new_interface_data["styling"] = style_json["styling"]
        if "tokens" in style_json: new_interface_data["tokens"] = style_json["tokens"]
    
    # 4. Integrity Validation
    valid_resp = llm_handler("INTEGRITY", model=payload.model, input_data={
        "metadata": json.dumps(system_context),
        "proposed_json": json.dumps(new_interface_data)
    })
    validation = json.loads(remove_reply_markdown(valid_resp))
    
    if validation.get("status") == "APPROVED":
        final_data = validation.get("final_json") or new_interface_data
        # Update database
        interface.data = final_data
        interface.save()
        
        # Render Preview
        files = render_preview(
            interface_data=final_data,
            classifiers=renderer_classifiers,
            interface_name=interface.name,
        )
        return {
            "message": validation.get("feedback", "AI Generation Successful."),
            "files": files,
        }
    else:
        return {
            "message": f"Validation Failed: {validation.get('feedback')}",
            "files": []
        }


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
