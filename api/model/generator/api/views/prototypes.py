from typing import Any, List, Optional, Dict
from generator.api.schemas import ReadPrototype, CreatePrototype, UpdatePrototype
from generator.models import Prototype
from metadata.models import System
from ninja import Router, Schema
from ninja.errors import HttpError
from django.http import StreamingHttpResponse
import json
import os
import requests

prototypes = Router()

PROTOTYPE_API_PROTO = os.environ.get('PROTOTYPE_API_PROTO', "http://")
PROTOTYPE_API_HOST = os.environ.get('PROTOTYPE_API_HOST', "studio-prototypes")
PROTOTYPE_API_PORT = os.environ.get('PROTOTYPE_API_PORT', 8010)
PROTOTYPE_API_URL = f"{PROTOTYPE_API_PROTO}{PROTOTYPE_API_HOST}:{PROTOTYPE_API_PORT}"


@prototypes.get("/", response=List[ReadPrototype])
def list_prototypes(request, system: Optional[str] = None):
    qs = None
    if system:
        qs = Prototype.objects.filter(system=system)
    else:
        qs = Prototype.objects.all()
    return qs


@prototypes.get("/{uuid:id}/meta/", response=Dict)
def read_prototype_meta(request, id):
    prototype = Prototype.objects.get(id=id)
    if not prototype:
        return 404, "Prototype not found"
    return prototype.metadata


@prototypes.get("/{str:database_hash}", response=List[ReadPrototype])
def list_prototypes_hash(request, database_hash):
    return Prototype.objects.filter(database_hash=database_hash)


@prototypes.get("/{uuid:id}/", response=ReadPrototype)
def read_prototype(request, id):
    return Prototype.objects.get(id=id)


@prototypes.post("/", response=ReadPrototype)
def create_prototype(request, prototype: CreatePrototype, database_prototype_name: Optional[str]):
    system = System.objects.get(pk=prototype.system)
    new_prototype = Prototype.objects.create(
        name=prototype.name,
        description=prototype.description,
        system=system,
        database_hash=prototype.database_hash,
        metadata=prototype.metadata # TODO: maybe we do not want to push all metadata to the DB?
    )
    GENERATION_URL = f"{PROTOTYPE_API_URL}/generate"
    layout_config = prototype.metadata.get('layout_config') if isinstance(prototype.metadata, dict) else None

    # Enrich metadata with system classifiers so the generator can resolve model
    # names even when no class diagram is present in the metadata.
    enriched_metadata = dict(prototype.metadata) if isinstance(prototype.metadata, dict) else {}
    enriched_metadata['classifiers'] = [
        {"id": str(c.id), "data": c.data}
        for c in system.classifiers.filter(data__type='class')
    ]

    data = {
        'id': str(new_prototype.id),
        'name': prototype.name,
        'system': str(prototype.system),
        'metadata': json.dumps(enriched_metadata),
        'variant_id': json.dumps(layout_config) if layout_config else '1',
    }
    # TODO: database retrieval should be done using ids
    if database_prototype_name and database_prototype_name != "":
        data['database_prototype_name'] = database_prototype_name
    response = requests.post(GENERATION_URL, json=data)

    if response.status_code != 200:
        detail = response.text[:1000] if response.text else f"HTTP {response.status_code}"
        raise Exception(f"Failed to generate prototype {prototype.name}: {detail}")

    return new_prototype


@prototypes.delete("/{uuid:id}/", response=bool)
def delete_prototype(request, id):
    DELETION_URL = f"{PROTOTYPE_API_URL}/remove"
    prototype = Prototype.objects.filter(id=id).first()
    if not prototype:
        return False

    data = {
        'id': str(prototype.id),
        'name': prototype.name,
        'system': str(prototype.system.id)
    }

    response = requests.delete(DELETION_URL, json=data)
    if response.status_code != 200:
        raise Exception("Failed to delete prototype " + prototype.name)
    prototype.delete()
    return True


@prototypes.delete("/system/{uuid:system_id}/", response=bool)
def delete_system_prototypes(request, system_id):
    DELETION_URL = f"{PROTOTYPE_API_URL}/remove"

    prototypes = Prototype.objects.filter(system=System.objects.get(pk=system_id))
    if not prototypes:
        return False
    
    for prototype in prototypes:
        data = {
            'id': str(prototype.id),
            'name': prototype.name,
            'system': str(prototype.system.id)
        }
        response = requests.delete(DELETION_URL, json=data)
        if response.status_code != 200:
            raise Exception("Failed to delete prototype " + prototype.name)
        prototype.delete()
    return True


@prototypes.put("/{uuid:id}/", response=bool)
def update_prototype(request, id, prototype: UpdatePrototype):
    try: 
        Prototype.objects.filter(id=id).update(name=prototype.name,
                                               description=prototype.description,
                                               system=prototype.system,
                                               running=prototype.running)
    except Prototype.DoesNotExist:
        return False
    return True


@prototypes.post("/stop_prototypes/", response=bool)
def stop_prototypes(request):
    STOP_URL = f"{PROTOTYPE_API_URL}/stop_prototypes"
    try:
        response = requests.post(STOP_URL)
    except:
        return False
    
    if response.status_code == 200:
        return True
    return False


@prototypes.post("/run/{str:prototype_id}", response=bool)
def run_prototype(request, prototype_id):
    prototype = Prototype.objects.get(id=prototype_id)
    if not prototype:
        return False
    
    RUN_URL = f"{PROTOTYPE_API_URL}/run"
    data = {
        'id': str(prototype.id),
        'name': prototype.name,
        'system': str(prototype.system.id)
    }
    try:
        response = requests.post(RUN_URL, json=data)
    except:
        return False
    
    if response.status_code in [200, 307]:
        return True
    return False


@prototypes.get("/active_prototype/")
def get_active_prototype(request):
    STATUS_URL = f"{PROTOTYPE_API_URL}/active_prototype"
    response = requests.get(STATUS_URL)
    return response.json()


@prototypes.post("/seed/", response=str)
def seed_prototype_data(request, system_id: Optional[str] = None):
    SEED_URL = f"{PROTOTYPE_API_URL}/seed"
    seed_data = {}
    if system_id:
        proto = Prototype.objects.filter(system__id=system_id).order_by('-id').first()
        if proto:
            seed_data = {'system': str(proto.system.id), 'name': proto.name}
    try:
        response = requests.post(SEED_URL, json=seed_data, timeout=120)
    except Exception as e:
        raise Exception(f"Failed to reach prototype API: {e}")
    if response.status_code != 200:
        raise Exception(response.text or "Seed failed")
    return response.text


ADK_AGENT_URL = os.environ.get("ADK_AGENT_URL", "http://gemini-make-agent:8080")


class GenerateCandidatesPayload(Schema):
    interface_id: str
    system_id: str
    prompt: str


@prototypes.post("/generate_candidates/")
def generate_interface_candidates(request, payload: GenerateCandidatesPayload):
    """Stream 3-candidate interface generation via the ADK candidate_pipeline_agent."""
    import uuid as _uuid

    _STATUS_MAP = {
        "candidate_pipeline_agent": "Starting pipeline...",
        "reason_agent":             "Analysing UML metadata and designer prompt...",
        "generate_agent":           "Generating interface candidates...",
        "render_agent":             "Rendering previews...",
    }

    def stream():
        yield json.dumps({"status": "Connecting to agent..."}) + "\n"

        user_id = payload.interface_id
        session_id = str(_uuid.uuid4())
        try:
            resp = requests.post(
                f"{ADK_AGENT_URL}/apps/app/users/{user_id}/sessions",
                json={"state": {"interface_id": payload.interface_id, "system_id": payload.system_id}},
                timeout=30,
            )
            resp.raise_for_status()
            session_id = resp.json().get("id", session_id)
        except Exception as e:
            yield json.dumps({"status": f"Failed to create session: {e}"}) + "\n"
            return

        message = f"generate_candidates interface_id={payload.interface_id} prompt={payload.prompt}"
        seen_authors: set = set()

        try:
            with requests.post(
                f"{ADK_AGENT_URL}/run_sse",
                json={
                    "app_name": "app",
                    "user_id": user_id,
                    "session_id": session_id,
                    "new_message": {"role": "user", "parts": [{"text": message}]},
                    "streaming": True,
                },
                stream=True,
                timeout=600,
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
                        if author and author not in seen_authors and author in _STATUS_MAP:
                            seen_authors.add(author)
                            yield json.dumps({"status": _STATUS_MAP[author]}) + "\n"
                    except Exception:
                        pass
        except Exception as e:
            yield json.dumps({"status": f"Agent error: {e}"}) + "\n"
            return

        yield json.dumps({"status": "done"}) + "\n"

    resp = StreamingHttpResponse(stream(), content_type="application/x-ndjson")
    resp['X-Accel-Buffering'] = 'no'
    resp['Cache-Control'] = 'no-cache'
    return resp


@prototypes.post("/seed_ai/")
def seed_prototype_ai(request, system_id: str):
    """Stream seed-data generation via the ADK seed_agent."""
    import uuid as _uuid

    proto = Prototype.objects.filter(system__id=system_id).order_by('-id').first()
    if not proto:
        raise HttpError(404, "No prototype found for this system")

    project_name = proto.name

    def stream():
        yield json.dumps({"status": "Connecting to seed agent..."}) + "\n"

        user_id = system_id
        session_id = str(_uuid.uuid4())
        try:
            resp = requests.post(
                f"{ADK_AGENT_URL}/apps/app/users/{user_id}/sessions",
                json={"state": {"system_id": system_id}},
                timeout=30,
            )
            resp.raise_for_status()
            session_id = resp.json().get("id", session_id)
        except Exception as e:
            yield json.dumps({"status": f"Failed to create session: {e}"}) + "\n"
            return

        prompt = f"system_id={system_id} project_name={project_name}"
        yield json.dumps({"status": "Generating seed data..."}) + "\n"

        try:
            with requests.post(
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
                    if line_str.startswith("data: "):
                        try:
                            event = json.loads(line_str[6:])
                            if event.get("author") == "seed_agent":
                                yield json.dumps({"status": "Seeding..."}) + "\n"
                        except Exception:
                            pass
        except Exception as e:
            yield json.dumps({"status": f"Agent error: {e}"}) + "\n"
            return

        yield json.dumps({"status": "done", "message": "Seed data generated successfully."}) + "\n"

    return StreamingHttpResponse(stream(), content_type="application/x-ndjson")


class HotReloadPayload(Schema):
    interface_id: str
    sections: Optional[List[Any]] = None
    pages: Optional[List[Any]] = None


@prototypes.post("/hot_reload/")
def hot_reload_templates(request, payload: HotReloadPayload):
    from metadata.models import Interface
    from llm.template_renderer import render_layout

    # Fetch active prototype info
    try:
        status = requests.get(f"{PROTOTYPE_API_URL}/active_prototype").json()
    except Exception as e:
        raise HttpError(502, f"Could not reach prototype API: {e}")

    if not status.get("running"):
        raise HttpError(404, "No prototype running")

    proto_system = status.get("system", "")
    proto_name = status.get("name", "")
    if not proto_system or not proto_name:
        raise HttpError(500, "Active prototype missing system/name")

    proto_path = f"/usr/src/prototypes/generated_prototypes/{proto_system}/{proto_name}"

    # Load interface
    try:
        iface = Interface.objects.get(pk=payload.interface_id)
    except Interface.DoesNotExist:
        raise HttpError(404, "Interface not found")

    interface_data = dict(iface.data or {})
    if payload.sections is not None:
        interface_data["sections"] = payload.sections
    if payload.pages is not None:
        interface_data["pages"] = payload.pages

    classifiers = [
        {"id": str(c.id), "data": c.data}
        for c in iface.system.classifiers.filter(data__type='class')
    ]

    relations = [
        {"id": str(r.id), "source": str(r.source_id), "target": str(r.target_id), "data": r.data}
        for r in iface.system.relations.all()
    ]
    files = render_layout(interface_data, classifiers, None, interface_name=iface.name, relations=relations)

    updated = 0
    for f in files:
        # f["path"] = "templates/customer_browse_products.html"
        # Actual path: {proto_path}/Customer/templates/Customer_Browse_Products.html
        rel = f["path"]  # e.g. "templates/customer_browse_products.html"
        basename = rel.split("/")[-1]  # "customer_browse_products.html"
        stem, ext = basename.rsplit(".", 1)
        parts = stem.split("_")
        title_parts = [p.capitalize() for p in parts]
        title_filename = "_".join(title_parts) + "." + ext  # "Customer_Browse_Products.html"
        app_dir = title_parts[0]  # "Customer"
        dest = os.path.join(proto_path, app_dir, "templates", title_filename)
        if os.path.exists(dest):
            with open(dest, "w") as wf:
                wf.write(f["content"])
            updated += 1

    return {"updated": updated}


__all__ = ["prototypes"]
