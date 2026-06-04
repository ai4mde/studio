from ninja import Router, Schema

from llm.gemini_make_agent.django_service import (
    apply_prompt_to_interface,
    debug_uml_extract,
    map_uml_to_all_interfaces,
    map_uml_to_interface,
)

llm_router = Router()


class InterfaceMappingRequest(Schema):
    interface_id: str


class SystemMappingRequest(Schema):
    system_id: str


class PromptEditRequest(Schema):
    interface_id: str
    system_id: str = ""
    user_request: str


@llm_router.get("/healthz", auth=None, tags=["gemini-make-agent"])
def healthz(request):
    return {"status": "ok", "service": "gemini-make-agent-django"}


@llm_router.get("/gemini-make-agent/debug_uml_extract/{interface_id}", tags=["gemini-make-agent"])
def debug_uml_extract_view(request, interface_id: str):
    return debug_uml_extract(interface_id)


@llm_router.post("/gemini-make-agent/map_uml_to_interface", tags=["gemini-make-agent"])
def map_uml_to_interface_view(request, payload: InterfaceMappingRequest):
    return map_uml_to_interface(payload.interface_id)


@llm_router.post("/gemini-make-agent/map_uml_to_all_interfaces", tags=["gemini-make-agent"])
def map_uml_to_all_interfaces_view(request, payload: SystemMappingRequest):
    return map_uml_to_all_interfaces(payload.system_id)


@llm_router.post("/gemini-make-agent/apply_prompt", tags=["gemini-make-agent"])
def apply_prompt_view(request, payload: PromptEditRequest):
    return apply_prompt_to_interface(
        payload.interface_id,
        payload.system_id,
        payload.user_request,
    )


__all__ = ["llm_router"]
