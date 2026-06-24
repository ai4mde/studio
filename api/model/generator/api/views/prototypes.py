from typing import Any, List, Optional, Dict
import copy
from generator.api.schemas import ReadPrototype, CreatePrototype, UpdatePrototype
from generator.models import Prototype
from llm.interface_generator.django_service import (
    map_uml_to_all_interfaces as run_uml_mapping_for_system,
    map_uml_to_interface as run_uml_mapping_for_interface,
)
from llm.interface_generator.candidate_generation import (
    generate_candidate_set,
    regenerate_candidate_set,
)
from llm.template_renderer import render_layout, normalize_interface_schema
from metadata.models import Interface
from metadata.models import System
from ninja import Router, Schema
from ninja.errors import HttpError
from django.http import StreamingHttpResponse
import json
import os
from pathlib import Path
import re
import requests
import time

prototypes = Router()

DEFAULT_HTTP_PROTO = "http://"
PROTOTYPE_API_PROTO = os.environ.get('PROTOTYPE_API_PROTO', DEFAULT_HTTP_PROTO)
PROTOTYPE_API_HOST = os.environ.get('PROTOTYPE_API_HOST', "studio-prototypes")
PROTOTYPE_API_PORT = os.environ.get('PROTOTYPE_API_PORT', 8010)
PROTOTYPE_API_URL = f"{PROTOTYPE_API_PROTO}{PROTOTYPE_API_HOST}:{PROTOTYPE_API_PORT}"


def _metadata_with_latest_interface_data(system: System, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Prefer saved Interface.data over stale frontend prototype metadata snapshots."""
    if not isinstance(metadata, dict):
        return {}

    enriched = copy.deepcopy(metadata)
    layout_config = enriched.get("layout_config") if isinstance(enriched.get("layout_config"), dict) else {}
    if layout_config.get("interface_data_source") == "preview_override":
        return enriched

    entries = enriched.get("interfaces")
    if not isinstance(entries, list):
        return enriched

    interfaces = list(Interface.objects.filter(system=system))
    by_id = {str(iface.id): iface for iface in interfaces}
    by_name = {str(iface.name or "").strip().lower(): iface for iface in interfaces}

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        if not isinstance(value, dict):
            continue
        interface_id = str(value.get("id") or "")
        label = str(entry.get("label") or value.get("name") or "").strip().lower()
        iface = by_id.get(interface_id) or by_name.get(label)
        if not iface:
            continue
        value["id"] = str(iface.id)
        value["name"] = iface.name
        value["description"] = iface.description
        value["system"] = str(iface.system_id)
        value["actor"] = str(iface.actor_id) if iface.actor_id else None
        value["data"] = iface.data or {}
        entry["label"] = iface.name
    return enriched


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
    prototype_system_id = prototype.system or prototype.system_id
    if not prototype_system_id:
        raise HttpError(422, "Missing required prototype system id.")

    system = System.objects.get(pk=prototype_system_id)
    metadata = _metadata_with_latest_interface_data(system, prototype.metadata)
    new_prototype = Prototype.objects.create(
        name=prototype.name,
        description=prototype.description or "",
        system=system,
        database_hash=prototype.database_hash or "",
        metadata=metadata # TODO: maybe we do not want to push all metadata to the DB?
    )
    GENERATION_URL = f"{PROTOTYPE_API_URL}/generate"
    layout_config = metadata.get('layout_config') if isinstance(metadata, dict) else None

    # Enrich metadata with system classifiers, diagrams, and relations so the
    # generator can resolve model names and workflows even when the initial
    # metadata payload is partial.
    enriched_metadata = dict(metadata) if isinstance(metadata, dict) else {}
    
    if 'classifiers' not in enriched_metadata:
        enriched_metadata['classifiers'] = [
            {"id": str(c.id), "data": c.data}
            for c in system.classifiers.all()
        ]
    
    if 'diagrams' not in enriched_metadata:
        from diagram.api.schemas.diagram import ExportDiagram
        enriched_metadata['diagrams'] = [
            ExportDiagram.from_orm(d).dict()
            for d in system.diagrams.all()
        ]
        
    if 'relations' not in enriched_metadata:
        enriched_metadata['relations'] = [
            {"id": str(r.id), "data": r.data, "source": str(r.source_id), "target": str(r.target_id)}
            for r in system.relations.all()
        ]

    data = {
        'id': str(new_prototype.id),
        'name': prototype.name,
        'system': str(system.id),
        'metadata': json.dumps(enriched_metadata),
        'variant_id': json.dumps(layout_config) if layout_config else '1',
    }
    # TODO: database retrieval should be done using ids
    if database_prototype_name and database_prototype_name != "":
        data['database_prototype_name'] = database_prototype_name
    response = requests.post(GENERATION_URL, json=data)

    if response.status_code != 200:
        detail = response.text[:1000] if response.text else f"HTTP {response.status_code}"
        raise RuntimeError(f"Failed to generate prototype {prototype.name}: {detail}")

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
        response = requests.post(RUN_URL, json=data, allow_redirects=False)
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
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to reach prototype API: {e}") from e
    if response.status_code != 200:
        raise RuntimeError(response.text or "Seed failed")
    return response.text


def _clear_interface_candidates(interface_id: str, status: str, prompt: str = "", base_candidate_index: Optional[int] = None) -> None:
    iface = Interface.objects.get(pk=interface_id)
    data = dict(iface.data or {})
    data.pop("regeneration_base_candidate", None)
    if base_candidate_index is not None:
        candidates = data.get("candidates") or []
        if 0 <= base_candidate_index < len(candidates) and candidates[base_candidate_index]:
            data["regeneration_base_candidate"] = {
                "selected_candidate_index": base_candidate_index,
                "candidate": candidates[base_candidate_index],
            }
    data["candidates"] = []
    data["candidate_generation_status"] = {
        "status": status,
        "prompt": prompt,
        "started_at": time.time(),
    }
    Interface.objects.filter(pk=interface_id).update(data=data)



class GenerateCandidatesPayload(Schema):
    interface_id: str
    system_id: str
    prompt: str


class RegenerateCandidatesPayload(Schema):
    interface_id: str
    system_id: str
    selected_candidate_index: int
    designer_requirements: str = ""


@prototypes.post("/generate_candidates/")
def generate_interface_candidates(request, payload: GenerateCandidatesPayload):
    """Stream 3-candidate interface generation through Django-hosted agent logic."""

    def stream():
        yield json.dumps({"status": "Starting candidate generation..."}) + "\n"
        try:
            _clear_interface_candidates(payload.interface_id, "generating", payload.prompt)
        except Exception as e:
            yield json.dumps({"status": "error", "message": f"Failed to reset old candidates: {e}"}) + "\n"
            return

        yield json.dumps({"status": "Generating and saving candidates..."}) + "\n"
        result = generate_candidate_set(payload.interface_id, payload.prompt)
        if not str(result).startswith("OK:"):
            yield json.dumps({"status": "error", "message": result}) + "\n"
            return

        try:
            iface = Interface.objects.get(pk=payload.interface_id)
            candidates = (iface.data or {}).get("candidates") or []
            candidate_count = len([candidate for candidate in candidates if candidate])
        except Exception as e:
            yield json.dumps({"status": "error", "message": f"Failed to load candidates: {e}"}) + "\n"
            return

        yield json.dumps({
            "status": "done",
            "candidate_count": candidate_count,
            "fallback": False,
        }) + "\n"

    resp = StreamingHttpResponse(stream(), content_type="application/x-ndjson")
    resp['X-Accel-Buffering'] = 'no'
    resp['Cache-Control'] = 'no-cache'
    return resp




class MapUmlPayload(Schema):
    interface_id: str


@prototypes.post("/map_uml_to_interface/")
def map_uml_to_interface(request, payload: MapUmlPayload):
    """Map UML diagrams to interface pages and sections through Django service logic."""
    try:
        data = run_uml_mapping_for_interface(payload.interface_id)
        return {"ok": data.get("status") == "ok", "message": data.get("message", "")}
    except Exception as e:
        return {"ok": False, "message": str(e)}


class MapUmlAllPayload(Schema):
    system_id: str


@prototypes.post("/map_uml_to_all_interfaces/")
def map_uml_to_all_interfaces(request, payload: MapUmlAllPayload):
    """Map UML diagrams to interfaces for all actors in a system."""
    try:
        data = run_uml_mapping_for_system(payload.system_id)
        return {"ok": data.get("status") == "ok", "message": data.get("message", ""), "results": data.get("results", [])}
    except Exception as e:
        return {"ok": False, "message": str(e)}


@prototypes.post("/regenerate_candidates/")
def regenerate_interface_candidates(request, payload: RegenerateCandidatesPayload):
    """Stream selected-candidate regeneration through Django-hosted agent logic."""

    def stream():
        yield json.dumps({"status": "Starting candidate regeneration..."}) + "\n"
        try:
            _clear_interface_candidates(
                payload.interface_id,
                "regenerating",
                payload.designer_requirements,
                payload.selected_candidate_index,
            )
        except Exception as e:
            yield json.dumps({"status": "error", "message": f"Failed to reset old candidates: {e}"}) + "\n"
            return

        yield json.dumps({"status": "Regenerating and saving candidates..."}) + "\n"
        result = regenerate_candidate_set(
            payload.interface_id,
            payload.selected_candidate_index,
            payload.designer_requirements,
        )
        if not str(result).startswith("OK:"):
            yield json.dumps({"status": "error", "message": result}) + "\n"
            return

        try:
            iface = Interface.objects.get(pk=payload.interface_id)
            candidates = (iface.data or {}).get("candidates") or []
            candidate_count = len([candidate for candidate in candidates if candidate])
            if candidate_count < 3:
                yield json.dumps({
                    "status": "error",
                    "message": f"regenerate_candidate_set saved {candidate_count} candidates; expected 3.",
                }) + "\n"
                return
        except Exception as e:
            yield json.dumps({"status": "error", "message": f"Failed to load regenerated candidates: {e}"}) + "\n"
            return

        yield json.dumps({
            "status": "done",
            "candidate_count": candidate_count,
            "regenerated_from": payload.selected_candidate_index,
        }) + "\n"

    resp = StreamingHttpResponse(stream(), content_type="application/x-ndjson")
    resp['X-Accel-Buffering'] = 'no'
    resp['Cache-Control'] = 'no-cache'
    return resp




class HotReloadPayload(Schema):
    interface_id: str
    sections: Optional[List[Any]] = None
    pages: Optional[List[Any]] = None
    styling: Optional[Dict[str, Any]] = None
    tokens: Optional[Dict[str, Any]] = None

def _html_signature(html: str) -> Dict[str, Any]:
    html = html or ""
    css_vars = dict(re.findall(r"(--[a-zA-Z0-9_-]+)\s*:\s*([^;}{]+)", html))
    token_css_vars = {
        "--accent",
        "--accent-secondary",
        "--page-bg",
        "--page-text",
        "--text-muted",
        "--text-subtle",
        "--region-header-bg",
        "--region-header-text",
        "--region-main-bg",
        "--region-main-bg-elevated",
        "--region-main-bg-sunken",
        "--region-sidebar-bg",
        "--region-footer-bg",
        "--region-footer-text",
        "--border-color",
        "--border-strong",
        "--card-bg",
        "--card-border",
        "--card-text",
        "--card-muted",
        "--component-form-bg",
        "--component-table-bg",
        "--component-list-bg",
        "--component-detail-bg",
        "--component-filter-bg",
        "--component-workflow-bg",
        "--button-primary-bg",
        "--button-primary-text",
        "--button-primary-border",
        "--button-secondary-bg",
        "--button-secondary-text",
        "--button-secondary-border",
        "--button-ghost-text",
        "--button-danger-bg",
        "--button-danger-text",
        "--button-danger-border",
        "--button-link-text",
        "--method-action-bg",
        "--method-action-text",
        "--method-action-border",
        "--input-bg",
        "--input-border",
        "--input-border-focus",
        "--input-text",
        "--input-placeholder",
        "--table-header-bg",
        "--table-header-text",
        "--table-row-hover",
        "--table-border",
        "--badge-success-bg",
        "--badge-success-text",
        "--badge-error-bg",
        "--badge-error-text",
        "--badge-warning-bg",
        "--badge-warning-text",
        "--badge-info-bg",
        "--badge-info-text",
        "--badge-neutral-bg",
        "--badge-neutral-text",
        "--badge-bg",
        "--badge-text",
        "--nav-bg",
        "--nav-text",
        "--nav-border",
    }
    text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", html, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    words = re.findall(r"\w{3,}", text.lower())
    return {
        "css_vars": {k: v.strip() for k, v in css_vars.items() if k in token_css_vars},
        "word_sample": words[:80],
        "button_count": len(re.findall(r"<(?:button|a)\b[^>]*(?:si-btn|button|btn)", html, flags=re.I)),
        "section_count": len(re.findall(r"data-section-id=", html)),
    }


def _django_route_name(value: Any) -> str:
    return re.sub(r"\W+", "_", str(value or "")).strip("_")


def _preview_page_key(value: Any) -> str:
    return _django_route_name(value).lower()


def _pixel_diff(preview_path: Path, live_path: Path) -> Dict[str, Any]:
    """Return a simple screenshot pixel diff summary."""
    try:
        from PIL import Image, ImageChops
    except Exception as exc:
        return {"skipped": True, "reason": f"Pillow unavailable: {exc}"}

    preview = Image.open(preview_path).convert("RGB")
    live = Image.open(live_path).convert("RGB")
    width = min(preview.width, live.width)
    height = min(preview.height, live.height)
    if width <= 0 or height <= 0:
        return {"skipped": False, "changed_ratio": 1, "reason": "empty screenshot"}
    diff = ImageChops.difference(preview.crop((0, 0, width, height)), live.crop((0, 0, width, height)))
    changed = 0
    if diff.getbbox():
        pixels = diff.load()
        for y in range(height):
            for x in range(width):
                if pixels[x, y] != (0, 0, 0):
                    changed += 1
    return {
        "skipped": False,
        "compared_size": [width, height],
        "preview_size": [preview.width, preview.height],
        "live_size": [live.width, live.height],
        "changed_pixels": changed,
        "changed_ratio": changed / float(width * height),
    }


def _screenshot_preview_live_pair(
    preview_html: str,
    live_url: str,
    fetch_url: str,
    out_dir: Path,
    page_name: str,
) -> Dict[str, Any]:
    """Capture preview and live screenshots for a rendered prototype page."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return {"skipped": True, "reason": f"Playwright unavailable: {exc}"}

    safe_page = re.sub(r"[^A-Za-z0-9_.-]+", "_", page_name or "page")
    preview_path = out_dir / f"{safe_page}.preview.png"
    live_path = out_dir / f"{safe_page}.live.png"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport={"width": 1440, "height": 1100})
            page = context.new_page()

            page.set_content(preview_html or "", wait_until="networkidle")
            page.screenshot(path=str(preview_path), full_page=True)

            page.goto(fetch_url, wait_until="networkidle")
            if page.url != live_url:
                page.goto(live_url, wait_until="networkidle")
            page.screenshot(path=str(live_path), full_page=True)

            context.close()
            browser.close()
    except Exception as exc:
        return {"skipped": True, "reason": f"Playwright screenshot failed: {exc}"}

    diff = _pixel_diff(preview_path, live_path)
    return {
        "skipped": False,
        "preview": str(preview_path),
        "live": str(live_path),
        "pixel_diff": diff,
    }


class VisualCheckPayload(Schema):
    interface_id: str
    pages: Optional[List[Any]] = None
    sections: Optional[List[Any]] = None
    styling: Optional[Dict[str, Any]] = None
    tokens: Optional[Dict[str, Any]] = None
    live_user: Optional[str] = None


@prototypes.post("/visual_check/")
def visual_check(request, payload: VisualCheckPayload):
    try:
        status = requests.get(f"{PROTOTYPE_API_URL}/active_prototype", timeout=10).json()
    except Exception as e:
        raise HttpError(502, f"Could not reach prototype API: {e}")
    if not status.get("running"):
        raise HttpError(404, "No prototype running")

    try:
        iface = Interface.objects.get(pk=payload.interface_id)
    except Interface.DoesNotExist:
        raise HttpError(404, "Interface not found")

    interface_data = dict(iface.data or {})
    if payload.sections is not None:
        interface_data["sections"] = payload.sections
    if payload.pages is not None:
        interface_data["pages"] = payload.pages
    if payload.styling is not None:
        interface_data["styling"] = payload.styling
    if payload.tokens is not None:
        interface_data["tokens"] = payload.tokens
    interface_data = normalize_interface_schema(interface_data)

    classifiers = [{"id": str(c.id), "data": c.data} for c in iface.system.classifiers.filter(data__type='class')]
    relations = [{"id": str(r.id), "source": str(r.source_id), "target": str(r.target_id), "data": r.data} for r in iface.system.relations.all()]
    expected_files = render_layout(interface_data, classifiers, None, interface_name=iface.name, relations=relations)

    public_host = os.environ.get("RUNNING_PROTOTYPE_HOST", "prototype.ai4mde.localhost")
    public_proto = os.environ.get("RUNNING_PROTOTYPE_PROTO", DEFAULT_HTTP_PROTO)
    public_base_url = f"{public_proto}{public_host}"
    check_proto = os.environ.get("RUNNING_PROTOTYPE_CHECK_PROTO", DEFAULT_HTTP_PROTO)
    check_host = os.environ.get("RUNNING_PROTOTYPE_CHECK_HOST")
    if not check_host:
        check_host = f"{PROTOTYPE_API_HOST}:{status.get('port') or os.environ.get('RUNNING_PROTOTYPE_PORT', 8020)}"
    check_base_url = f"{check_proto}{check_host}"
    app = re.sub(r"\W+", "_", iface.name).strip("_")
    page_route_by_key: Dict[str, Dict[str, str]] = {}
    for page in interface_data.get("pages") or []:
        if not isinstance(page, dict):
            continue
        page_type = page.get("type")
        page_type_value = page_type.get("value") if isinstance(page_type, dict) else page_type
        page_name = page.get("name") or page.get("id")
        route_name = _django_route_name(page_name)
        page_info = {
            "route_name": route_name,
            "type": str(page_type_value or "normal").lower(),
        }
        for key_source in (page.get("id"), page.get("name"), route_name):
            key = _preview_page_key(key_source)
            if key:
                page_route_by_key[key] = page_info
    live_session = requests.Session()
    live_user = payload.live_user or "jan_devries"

    checks = []
    screenshot_root = Path(os.environ.get("PREVIEW_LIVE_SCREENSHOT_DIR", "/usr/src/app/preview-live-visual-check"))
    screenshot_dir = screenshot_root / str(payload.interface_id) / str(int(time.time()))
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    for file in expected_files[:8]:
        basename = os.path.basename(file["path"])
        stem = os.path.splitext(basename)[0]
        page_name = stem
        if page_name.lower().startswith(app.lower() + "_"):
            page_name = page_name[len(app) + 1:]
        route_info = page_route_by_key.get(_preview_page_key(page_name), {})
        route_name = route_info.get("route_name") or _django_route_name(page_name)
        page_type = route_info.get("type", "")
        live_path = f"/{app}/" if page_name.lower() == "task" or page_type == "activity" else f"/{app}/render_{app}_{route_name}"
        live_url = f"{public_base_url}{live_path}"
        check_live_url = f"{check_base_url}{live_path}"
        fetch_url = f"{check_base_url}/autologin?as={live_user}&next={live_path}"
        try:
            live_resp = live_session.get(fetch_url, timeout=10, allow_redirects=True)
            live_html = live_resp.text if live_resp.ok else ""
            live_status = live_resp.status_code
        except Exception:
            live_html = ""
            live_status = 0
        expected_sig = _html_signature(file.get("content", ""))
        live_sig = _html_signature(live_html)
        css_mismatches = []
        structure_mismatches = []
        screenshot_mismatches = []
        for key, value in expected_sig["css_vars"].items():
            if live_sig["css_vars"].get(key) != value:
                css_mismatches.append(f"{key}: expected {value}, live {live_sig['css_vars'].get(key)}")
        if expected_sig["button_count"] != live_sig["button_count"]:
            structure_mismatches.append(f"button_count: expected {expected_sig['button_count']}, live {live_sig['button_count']}")
        if expected_sig["section_count"] != live_sig["section_count"]:
            structure_mismatches.append(f"section_count: expected {expected_sig['section_count']}, live {live_sig['section_count']}")
        screenshot = _screenshot_preview_live_pair(
            preview_html=file.get("content", ""),
            live_url=check_live_url,
            fetch_url=fetch_url,
            out_dir=screenshot_dir,
            page_name=page_name,
        )
        pixel_diff = screenshot.get("pixel_diff") if isinstance(screenshot, dict) else None
        changed_ratio = pixel_diff.get("changed_ratio") if isinstance(pixel_diff, dict) and not pixel_diff.get("skipped") else None
        if isinstance(changed_ratio, (int, float)) and changed_ratio > 0.08:
            screenshot_mismatches.append(f"screenshot_diff: preview/live changed ratio {changed_ratio:.3f}")
        mismatches = css_mismatches + structure_mismatches + screenshot_mismatches
        style_ok = live_status == 200 and not css_mismatches
        strict_ok = live_status == 200 and not mismatches
        checks.append({
            "page": page_name,
            "live_url": live_url,
            "check_url": check_live_url,
            "live_status": live_status,
            "ok": strict_ok,
            "style_ok": style_ok,
            "strict_pixel_ok": strict_ok,
            "mismatches": mismatches,
            "css_mismatches": css_mismatches,
            "structure_mismatches": structure_mismatches,
            "screenshot_mismatches": screenshot_mismatches,
            "expected": expected_sig,
            "live": live_sig,
            "screenshot": screenshot,
        })
    return {
        "ok": all(item["ok"] for item in checks),
        "style_ok": all(item.get("style_ok") for item in checks),
        "checks": checks,
        "schema_version": interface_data.get("canonical_schema", {}).get("version", 1),
    }


@prototypes.post("/hot_reload/")
def hot_reload_templates(request, payload: HotReloadPayload):
    from metadata.models import Interface

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
    if payload.styling is not None:
        interface_data["styling"] = payload.styling
    if payload.tokens is not None:
        interface_data["tokens"] = payload.tokens
    interface_data = normalize_interface_schema(interface_data)

    classifiers = [
        {"id": str(c.id), "data": c.data}
        for c in iface.system.classifiers.filter(data__type='class')
    ]

    relations = [
        {"id": str(r.id), "source": str(r.source_id), "target": str(r.target_id), "data": r.data}
        for r in iface.system.relations.all()
    ]
    files = render_layout(interface_data, classifiers, None, interface_name=iface.name, relations=relations, preview_mode=False)

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
