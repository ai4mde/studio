import json
import os
import uuid
from typing import List, Optional

import requests as _req
from django.http import StreamingHttpResponse
from metadata.api.schemas import CreateInterface, ReadInterface, UpdateInterface, ExportSingleSystem
from metadata.api.schemas.generator import GeneratePrototypeRequest, GeneratePrototypeResponse
from metadata.api.views.defaulting import create_default_interface
from metadata.models import System, Interface, Classifier
from llm.template_renderer import render_layout, render_preview
from ninja import Router

ADK_AGENT_URL = os.environ.get("ADK_AGENT_URL", "http://gemini-make-agent:8080")

interfaces = Router()


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
        return 404, {"message": "Interface not found"}

    system = interface.system

    # Fast path: template-based render, no LLM
    if not payload.prompt or payload.interface_data_override is not None:
        interface_data = payload.interface_data_override or interface.data or {}
        classifiers = [{"id": str(c.id), "data": c.data} for c in system.classifiers.all()]
        relations = [
            {"id": str(r.id), "source": str(r.source_id), "target": str(r.target_id), "data": r.data}
            for r in system.relations.all()
        ]
        files = render_preview(interface_data=interface_data, classifiers=classifiers, relations=relations, interface_name=interface.name)
        return {"message": f"Generated {len(files)} page(s).", "files": files}

    def stream_generator():
        renderer_classifiers = [dict(id=str(c.id), data=c.data) for c in system.classifiers.all()]
        renderer_relations = [
            {"id": str(r.id), "source": str(r.source_id), "target": str(r.target_id), "data": r.data}
            for r in system.relations.all()
        ]

        yield json.dumps({"status": "Connecting to agent... (连接 AI 中...)"}) + "\n"

        # 1. Create ADK session
        user_id = str(interface.id)
        session_id = str(uuid.uuid4())
        try:
            resp = _req.post(
                f"{ADK_AGENT_URL}/apps/app/users/{user_id}/sessions",
                json={"state": {"interface_id": str(id), "system_id": str(system.id)}},
                timeout=30,
            )
            resp.raise_for_status()
            session_id = resp.json().get("id", session_id)
            yield json.dumps({"status": "Connecting to agent... (连接 AI 中...)", "debug_session_id": session_id, "debug_user_id": user_id}) + "\n"
        except Exception as e:
            yield json.dumps({"status": f"Failed to create session: {e}"}) + "\n"
            return

        # 2. Stream SSE from gemini-make-agent
        prompt = f"system_id={system.id} interface_id={id} user_request={payload.prompt}"

        agent_status_map = {
            "gemini_make_agent": "Analyzing request... (分析中...)",
            "layout_agent":      "Adjusting layout... (调整布局...)",
            "stylist_agent":     "Refining style... (调整视觉样式...)",
        }
        seen_authors = set()

        try:
            with _req.post(
                f"{ADK_AGENT_URL}/run_sse",
                json={
                    "app_name": "app",
                    "user_id": user_id,
                    "session_id": session_id,
                    "new_message": {"role": "user", "parts": [{"text": prompt}]},
                    "streaming": True,
                },
                stream=True,
                timeout=300,
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                    if not line_str.startswith("data: "):
                        continue
                    try:
                        event = json.loads(line_str[6:])
                        author = event.get("author", "")
                        if author and author not in seen_authors and author in agent_status_map:
                            seen_authors.add(author)
                            yield json.dumps({"status": agent_status_map[author]}) + "\n"
                    except Exception:
                        pass
        except Exception as e:
            yield json.dumps({"status": f"Agent error: {e}"}) + "\n"

        # 3. The agent persists interface.data via update_interface_tool.
        # Refresh and render the preview.
        interface.refresh_from_db()
        files = render_preview(
            interface_data=interface.data,
            classifiers=renderer_classifiers,
            relations=renderer_relations,
            interface_name=interface.name,
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


@interfaces.delete("/{uuid:interface_id}", response=bool)
def delete_interface(request, interface_id):
    try:
        Interface.objects.filter(id=interface_id).delete()
    except Interface.DoesNotExist:
        return False
    return True


__all__ = ["interfaces"]
