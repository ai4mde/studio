import json
import re
from typing import List, Optional

from django.http import StreamingHttpResponse, HttpResponse
from metadata.api.schemas import CreateInterface, ReadInterface, UpdateInterface, ExportSingleSystem
from metadata.api.schemas.generator import GeneratePrototypeRequest, GeneratePrototypeResponse
from metadata.api.views.defaulting import create_default_interface
from metadata.models import System, Interface, Classifier
from llm.interface_generator.candidate_generation import (
    generate_candidate_set,
    regenerate_candidate_set,
)
from llm.interface_generator.django_service import apply_prompt_to_interface
from llm.template_renderer import render_layout
from ninja import Router, Body
from ninja.errors import HttpError


interfaces = Router()
INTERFACE_NOT_FOUND = "Interface not found"


_AGENT_CONTEXT_SKIP_KEYS = {
    "candidates",
    "canonical_schema",
    "preview",
    "preview_html",
    "html",
    "files",
    "generated_files",
    "rendered_files",
    "screenshots",
    "thumbnail",
    "thumbnails",
    "image_data",
    "base64",
}


def _compact_agent_value(value, depth: int = 0):
    """Keep AI edit context small enough for ADK/Gemini while preserving editable schema."""
    if depth > 8:
        return None
    if isinstance(value, dict):
        compact = {}
        for key, child in value.items():
            key_str = str(key)
            if key_str in _AGENT_CONTEXT_SKIP_KEYS or key_str.endswith("_html") or key_str.endswith("_preview"):
                continue
            compact[key_str] = _compact_agent_value(child, depth + 1)
        return compact
    if isinstance(value, list):
        return [_compact_agent_value(item, depth + 1) for item in value[:120]]
    if isinstance(value, str):
        return value if len(value) <= 2000 else value[:2000] + "...[truncated]"
    return value


def _compact_interface_data_for_agent(data: dict) -> dict:
    """Send only the canonical editable interface DSL to the AI edit agent."""
    if not isinstance(data, dict):
        return {}
    compact = {}
    for key in ("pages", "sections", "tokens", "styling", "layout_config"):
        if key in data:
            compact[key] = _compact_agent_value(data.get(key))
    return compact


def _extract_adk_event_error(event) -> str:
    found = []

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                key_l = str(key).lower()
                if key_l in {"error", "error_message", "errormessage", "message", "status"} and isinstance(child, str):
                    text = child.strip()
                    if any(term in text.lower() for term in ("error", "failed", "invalid", "exceeds", "bad request", "timeout")):
                        found.append(text)
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str):
            text = value.strip()
            if any(term in text.lower() for term in ("input token count exceeds", "bad request", "agent error", "failed to")):
                found.append(text)

    walk(event)
    return " | ".join(dict.fromkeys(found))[:1200]


@interfaces.get("/", response=List[ReadInterface])
def list_interfaces(request, system: Optional[str] = None):
    if system:
        qs = Interface.objects.filter(system=system).order_by('id')
    else:
        qs = Interface.objects.all()
    return qs


@interfaces.post("/{uuid:id}/generate/")
def generate_interface_prototype(request, id: str, payload: GeneratePrototypeRequest):
    try:
        interface = Interface.objects.get(id=id)
    except Interface.DoesNotExist:
        return 404, {"message": INTERFACE_NOT_FOUND}

    system = interface.system

    # Fast path: template-based render, no LLM
    if not payload.prompt or payload.interface_data_override is not None:
        interface_data = payload.interface_data_override or interface.data or {}
        classifiers = [{"id": str(c.id), "data": c.data} for c in system.classifiers.all()]
        relations = [
            {"id": str(r.id), "source": str(r.source_id), "target": str(r.target_id), "data": r.data}
            for r in system.relations.all()
        ]
        files = render_layout(
            interface_data=interface_data,
            classifiers=classifiers,
            layout_config=None,
            interface_name=interface.name,
            inject_click_handlers=payload.inject_click_handlers,
            relations=relations,
        )
        return {"message": f"Generated {len(files)} page(s).", "files": files}

    def stream_generator():
        renderer_classifiers = [{"id": str(c.id), "data": c.data} for c in system.classifiers.all()]
        renderer_relations = [
            {"id": str(r.id), "source": str(r.source_id), "target": str(r.target_id), "data": r.data}
            for r in system.relations.all()
        ]

        yield json.dumps({"status": "Connecting to agent... (连接 AI 中...)"}) + "\n"

        if "generate_candidates" in (payload.prompt or ""):
            yield json.dumps({"status": "Generating candidates..."}) + "\n"
            result = generate_candidate_set(str(id), payload.prompt or "")
            if not str(result).startswith("OK:"):
                yield json.dumps({"status": f"Agent error: {result}"}) + "\n"
                return
        else:
            yield json.dumps({"status": "Applying interface edit..."}) + "\n"
            result = apply_prompt_to_interface(str(id), str(system.id), payload.prompt or "")
            if result.get("status") != "ok":
                yield json.dumps({"status": f"Agent error: {result.get('message', '')}"}) + "\n"
                return

        interface.refresh_from_db()
        data = interface.data or {}
        render_data = data
        if "generate_candidates" in (payload.prompt or ""):
            candidates = data.get("candidates") or []
            c0 = next((c for c in candidates if c), None)
            if c0:
                render_data = {
                    "pages": c0.get("pages", data.get("pages", [])),
                    "sections": c0.get("sections", data.get("sections", [])),
                    "tokens": c0.get("tokens", data.get("tokens", {})),
                    "styling": c0.get("styling", data.get("styling", {})),
                }
        files = render_layout(
            interface_data=render_data,
            classifiers=renderer_classifiers,
            layout_config=None,
            interface_name=interface.name,
            inject_click_handlers=True,
            relations=renderer_relations,
        )
        yield json.dumps({"status": "Done", "files": files, "message": "AI Generation Successful.", "interface_data": interface.data}) + "\n"


    resp = StreamingHttpResponse(stream_generator(), content_type="application/x-ndjson")
    resp['X-Accel-Buffering'] = 'no'
    resp['Cache-Control'] = 'no-cache'
    return resp


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
        Interface.objects.filter(id=id).update(
            name=interface.name,
            description=interface.description,
            system=interface.system,
            data=interface.data,
        )
    except Interface.DoesNotExist:
        return False
    return True


@interfaces.patch("/{uuid:id}/styling/", response=bool)
def patch_interface_styling(request, id: str, payload: dict = Body(...)):
    try:
        interface = Interface.objects.get(id=id)
        data = dict(interface.data or {})
        data["styling"] = {**(data.get("styling") or {}), **payload}
        Interface.objects.filter(id=id).update(data=data)
        return True
    except Interface.DoesNotExist:
        return False


@interfaces.patch("/{uuid:id}/data/", response=bool)
def patch_interface_data(request, id: str, payload: dict = Body(...)):
    try:
        interface = Interface.objects.get(id=id)
        data = {**(interface.data or {}), **payload}
        Interface.objects.filter(id=id).update(data=data)
        return True
    except Interface.DoesNotExist:
        return False


@interfaces.delete("/{uuid:interface_id}", response=bool)
def delete_interface(request, interface_id):
    try:
        Interface.objects.filter(id=interface_id).delete()
    except Interface.DoesNotExist:
        return False
    return True


@interfaces.post("/{uuid:id}/candidates/seed_test/")
def seed_test_candidate(request, id: str):
    """Debug: directly write 1 dummy candidate to interface.data — bypasses agent entirely."""
    try:
        interface = Interface.objects.get(id=id)
    except Interface.DoesNotExist:
        return 404, {"message": INTERFACE_NOT_FOUND}
    data = dict(interface.data or {})
    dummy = {
        "id": "c_test",
        "name": "Test Candidate",
        "description": "Debug seed — written directly without agent",
        "pages": [{"id": "p_test", "name": "Test_Page"}],
        "sections": [{"id": "s_test", "name": "Test Section", "layout": "card", "primary_model": ""}],
    }
    data["candidates"] = [dummy]
    Interface.objects.filter(id=id).update(data=data)
    interface.refresh_from_db()
    saved = (interface.data or {}).get("candidates", [])
    return {"saved_count": len(saved), "first_name": saved[0]["name"] if saved else None}


@interfaces.get("/{uuid:id}/candidates/")
def list_candidates(request, id: str):
    try:
        interface = Interface.objects.get(id=id)
    except Interface.DoesNotExist:
        return 404, {"message": INTERFACE_NOT_FOUND}
    candidates = (interface.data or {}).get("candidates", [])
    return [
        {
            "index": i,
            "id": c.get("id") if c else None,
            "name": c.get("name") if c else None,
            "description": c.get("description") if c else None,
            "has_preview": bool(c.get("preview_html")) if c else False,
            "page_count": len(c.get("pages", [])) if c else 0,
            "section_count": len(c.get("sections", [])) if c else 0,
        }
        for i, c in enumerate(candidates)
    ]


@interfaces.post("/{uuid:id}/candidates/{candidate_index}/regenerate/")
def regenerate_candidates_from_selected(request, id: str, candidate_index: int, payload: dict = Body(...)):
    try:
        interface = Interface.objects.get(id=id)
    except Interface.DoesNotExist:
        return 404, {"message": INTERFACE_NOT_FOUND}

    candidates = (interface.data or {}).get("candidates", [])
    if candidate_index < 0 or candidate_index >= len(candidates) or not candidates[candidate_index]:
        raise HttpError(404, f"Candidate {candidate_index} not found")

    designer_requirements = str(
        payload.get("designer_requirements")
        or payload.get("requirements")
        or payload.get("prompt")
        or ""
    ).strip()
    if not designer_requirements:
        raise HttpError(400, "designer_requirements is required")

    def stream_generator():
        yield json.dumps({"status": "Connecting to agent..."}) + "\n"

        yield json.dumps({"status": "Regenerating candidates..."}) + "\n"
        result = regenerate_candidate_set(str(id), candidate_index, designer_requirements)
        if not str(result).startswith("OK:"):
            yield json.dumps({"status": f"Agent error: {result}"}) + "\n"
            return

        for idx in range(3):
            try:
                render_candidate(request, id, idx)
            except Exception:
                pass

        interface.refresh_from_db()
        refreshed_candidates = (interface.data or {}).get("candidates", [])
        summary = [
            {
                "index": i,
                "id": c.get("id") if c else None,
                "name": c.get("name") if c else None,
                "description": c.get("description") if c else None,
                "has_preview": bool(c.get("preview_html")) if c else False,
                "derived_from": c.get("derived_from") if c else None,
                "variation_strategy": c.get("variation_strategy") if c else None,
            }
            for i, c in enumerate(refreshed_candidates[:3])
        ]
        yield json.dumps({"status": "Done", "message": "Candidate regeneration complete.", "candidates": summary}) + "\n"


    resp = StreamingHttpResponse(stream_generator(), content_type="application/x-ndjson")
    resp["X-Accel-Buffering"] = "no"
    resp["Cache-Control"] = "no-cache"
    return resp


@interfaces.post("/{uuid:id}/candidates/{candidate_index}/render/")
def render_candidate(request, id: str, candidate_index: int):
    try:
        interface = Interface.objects.get(id=id)
    except Interface.DoesNotExist:
        return 404, {"message": INTERFACE_NOT_FOUND}

    candidates = (interface.data or {}).get("candidates", [])
    if candidate_index < 0 or candidate_index >= len(candidates):
        raise HttpError(404, f"Candidate {candidate_index} not found")

    candidate = candidates[candidate_index]
    system = interface.system
    classifiers = [{"id": str(c.id), "data": c.data} for c in system.classifiers.all()]
    relations = [
        {"id": str(r.id), "source": str(r.source_id), "target": str(r.target_id), "data": r.data}
        for r in system.relations.all()
    ]

    candidate_data = {
        "pages": candidate.get("pages", []),
        "sections": candidate.get("sections", []),
        "styling": candidate.get("styling", {}),
        "tokens": candidate.get("tokens", {}),
    }
    files = render_layout(
        interface_data=candidate_data,
        classifiers=classifiers,
        layout_config=None,
        interface_name=interface.name,
        inject_click_handlers=False,
        relations=relations,
    )
    page_order = []
    for page in candidate.get("pages", []):
        page_type = page.get("type")
        page_type_value = page_type.get("value") if isinstance(page_type, dict) else page_type
        page_order.append((page.get("name", ""), 1 if page_type_value == "activity" else 0))
    page_rank = {name: (kind, index) for index, (name, kind) in enumerate(page_order)}
    if page_rank:
        def _file_rank(file_obj):
            path = file_obj.get("path", "")
            match = re.search(rf"{re.escape(interface.name)}_(.+?)\.html$", path)
            page_name = match.group(1) if match else ""
            return page_rank.get(page_name, (0 if not page_name.startswith("Workflow_") else 1, 9999))
        files = sorted(files, key=_file_rank)

    # Disable all link navigation in candidate preview (iframes shouldn't navigate away)
    _nav_disable = (
        "<script>document.addEventListener('click',function(e){"
        "var l=e.target.closest&&e.target.closest('a[href]');"
        "if(l){e.preventDefault();}},true);</script>"
    )
    files = [{**f, "content": f["content"].replace("</body>", _nav_disable + "</body>", 1)} for f in files]

    # Build a single standalone HTML with tab-based page navigation
    def _clean_tab_name(raw: str) -> str:
        name = re.sub(r"^templates/[^/]+_", "", raw, flags=re.IGNORECASE)
        name = re.sub(r"\.html?$", "", name, flags=re.IGNORECASE)
        return re.sub(r"[_-]", " ", name).strip().title()

    page_names = [f.get("page", f.get("path", f"Page {i}")) for i, f in enumerate(files)]
    tab_buttons = "".join(
        f'<button class="tab-btn" onclick="showPage({i})" id="tab-{i}">{_clean_tab_name(page_names[i])}</button>'
        for i in range(len(files))
    )
    page_divs = "".join(
        f'<div class="page-frame" id="page-{i}" style="display:{"block" if i == 0 else "none"}">'
        f'<iframe srcdoc="{files[i]["content"].replace(chr(34), "&quot;").replace(chr(10), "&#10;")}" '
        f'style="width:100%;height:calc(100vh - 50px);border:none;"></iframe></div>'
        for i in range(len(files))
    )

    nav_style = (
        "position:fixed;top:0;left:0;right:0;height:50px;background:#1e293b;"
        "display:flex;align-items:center;padding:0 12px;gap:8px;z-index:999;"
        "overflow-x:auto;"
    )
    btn_style = (
        ".tab-btn{background:#334155;color:#e2e8f0;border:none;padding:6px 14px;"
        "border-radius:6px;cursor:pointer;font-size:13px;white-space:nowrap;}"
        ".tab-btn:hover,.tab-btn.active{background:#3b82f6;color:#fff;}"
    )
    js = (
        "function showPage(i){"
        "document.querySelectorAll('.page-frame').forEach((el,j)=>el.style.display=j===i?'block':'none');"
        "document.querySelectorAll('.tab-btn').forEach((el,j)=>{el.classList.toggle('active',j===i);});}"
        "showPage(0);"
    )

    preview_html = (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>body{{margin:0;padding-top:50px;}}{btn_style}</style></head>"
        f"<body><nav style='{nav_style}'>{tab_buttons}</nav>"
        f"{page_divs}"
        f"<script>{js}</script></body></html>"
    )

    data = dict(interface.data or {})
    updated_candidates = list(data.get("candidates", []))
    if candidate_index < len(updated_candidates):
        updated_candidates[candidate_index] = dict(updated_candidates[candidate_index])
        updated_candidates[candidate_index]["preview_html"] = preview_html
        updated_candidates[candidate_index]["preview_files"] = files
    data["candidates"] = updated_candidates
    Interface.objects.filter(id=id).update(data=data)

    return {"message": f"Rendered {len(files)} page(s).", "files": files}


@interfaces.get("/{uuid:id}/candidates/{candidate_index}/preview/", auth=None)
def preview_candidate(request, id: str, candidate_index: int):
    try:
        interface = Interface.objects.get(id=id)
    except Interface.DoesNotExist:
        return HttpResponse(INTERFACE_NOT_FOUND, status=404)

    candidates = (interface.data or {}).get("candidates", [])
    if candidate_index < 0 or candidate_index >= len(candidates):
        return HttpResponse("Candidate not found", status=404)

    candidate = candidates[candidate_index]
    preview_html = candidate.get("preview_html")
    if not preview_html:
        return HttpResponse("Preview not yet rendered. Call the render endpoint first.", status=404)

    return HttpResponse(preview_html, content_type="text/html")


@interfaces.post("/{uuid:id}/candidates/{candidate_index}/apply/")
def apply_candidate(request, id: str, candidate_index: int):
    try:
        interface = Interface.objects.get(id=id)
    except Interface.DoesNotExist:
        return 404, {"message": INTERFACE_NOT_FOUND}

    candidates = (interface.data or {}).get("candidates", [])
    if candidate_index < 0 or candidate_index >= len(candidates):
        return 404, {"message": f"Candidate {candidate_index} not found"}

    candidate = candidates[candidate_index]
    data = dict(interface.data or {})
    data["pages"] = candidate.get("pages", data.get("pages", []))
    data["sections"] = candidate.get("sections", data.get("sections", []))
    if candidate.get("styling"):
        data["styling"] = candidate["styling"]
    if candidate.get("tokens"):
        data["tokens"] = candidate["tokens"]
    Interface.objects.filter(id=id).update(data=data)

    return {
        "message": "Candidate applied.",
        "pages": data["pages"],
        "sections": data["sections"],
        "styling": data.get("styling", {}),
        "tokens": data.get("tokens", {}),
    }


__all__ = ["interfaces"]
