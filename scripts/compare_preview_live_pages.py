import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


ROOT = Path(__file__).resolve().parents[1]
GENERATION_DIR = ROOT / "prototypes" / "backend" / "generation"
GENERATION_SCRIPTS_DIR = GENERATION_DIR / "generation_scripts"

sys.path.insert(0, str(GENERATION_SCRIPTS_DIR))
sys.path.insert(0, str(GENERATION_DIR))

from utils.loading_json_utils import get_application_component  # noqa: E402
import utils.template_generation as template_generation  # noqa: E402
from utils.template_generation import _make_task_home_page, _render_unified_page  # noqa: E402
from utils.sanitization import project_name_sanitization  # noqa: E402


def read_local_template_file(template_path: str):
    template_name = Path(template_path).name
    env = Environment(loader=FileSystemLoader(str(GENERATION_DIR / "templates")))
    return env.get_template(template_name)


template_generation.read_template_file = read_local_template_file


class SectionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sections = []
        self.unsupported = []
        self._capture_unsupported = False
        self._unsupported_text = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        section_id = attrs_dict.get("data-section-id")
        if section_id:
            self.sections.append(
                {
                    "id": section_id,
                    "name": attrs_dict.get("data-section-name", ""),
                    "position": attrs_dict.get("data-position", ""),
                    "layout": attrs_dict.get("data-layout", ""),
                }
            )
        class_name = attrs_dict.get("class", "")
        if tag == "div" and "border-dashed" in class_name:
            self._capture_unsupported = True
            self._unsupported_text = []

    def handle_endtag(self, tag):
        if self._capture_unsupported and tag == "div":
            text = "".join(self._unsupported_text).strip()
            if "Unsupported section layout" in text:
                self.unsupported.append(re.sub(r"\s+", " ", text))
            self._capture_unsupported = False
            self._unsupported_text = []

    def handle_data(self, data):
        if self._capture_unsupported:
            self._unsupported_text.append(data)


def parse_html(html: str) -> dict:
    parser = SectionParser()
    parser.feed(html)
    return {
        "sections": parser.sections,
        "unsupported": parser.unsupported,
    }


def normalize_interface_entry(interface: dict) -> dict:
    if "value" in interface:
        return interface
    return {
        "label": interface.get("name") or interface.get("label") or "",
        "value": interface,
    }


def render_pair(application_component, page, tokens, project_name):
    application_name = application_component.name
    common = {
        "page": page,
        "all_pages": application_component.pages,
        "tokens": tokens,
        "styling": application_component.styling,
        "application_name": application_name,
        "project_name": project_name_sanitization(project_name),
    }
    preview = _render_unified_page(preview_mode=True, **common)
    live = _render_unified_page(preview_mode=False, **common)
    return preview, live


def compare_structure(preview_html: str, live_html: str) -> dict:
    preview = parse_html(preview_html)
    live = parse_html(live_html)
    preview_sig = [(s["id"], s["position"], s["layout"]) for s in preview["sections"]]
    live_sig = [(s["id"], s["position"], s["layout"]) for s in live["sections"]]
    return {
        "section_order_match": preview_sig == live_sig,
        "preview_sections": preview["sections"],
        "live_sections": live["sections"],
        "preview_unsupported": preview["unsupported"],
        "live_unsupported": live["unsupported"],
    }


def screenshot_with_playwright(out_dir: Path, page_name: str, preview_html: str, live_html: str):
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        for candidate in (
            Path("D:/Anaconda/Lib/site-packages"),
            Path(os.environ.get("CONDA_PREFIX", "")) / "Lib" / "site-packages",
        ):
            if candidate.exists() and str(candidate) not in sys.path:
                sys.path.append(str(candidate))
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            return {"skipped": True, "reason": f"playwright unavailable: {exc}"}

    shots = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        browser_page = browser.new_page(viewport={"width": 1440, "height": 1100})
        for kind, html in (("preview", preview_html), ("live", live_html)):
            browser_page.set_content(html, wait_until="networkidle")
            shot_path = out_dir / f"{page_name}.{kind}.png"
            browser_page.screenshot(path=str(shot_path), full_page=True)
            shots[kind] = str(shot_path)
        browser.close()
    result = {"skipped": False, "screenshots": shots}
    try:
        from PIL import Image, ImageChops

        preview_img = Image.open(shots["preview"]).convert("RGB")
        live_img = Image.open(shots["live"]).convert("RGB")
        width = min(preview_img.width, live_img.width)
        height = min(preview_img.height, live_img.height)
        preview_crop = preview_img.crop((0, 0, width, height))
        live_crop = live_img.crop((0, 0, width, height))
        diff = ImageChops.difference(preview_crop, live_crop)
        bbox = diff.getbbox()
        changed = 0
        if bbox:
            pixels = diff.load()
            for y in range(height):
                for x in range(width):
                    if pixels[x, y] != (0, 0, 0):
                        changed += 1
        result["pixel_diff"] = {
            "compared_size": [width, height],
            "preview_size": [preview_img.width, preview_img.height],
            "live_size": [live_img.width, live_img.height],
            "changed_pixels": changed,
            "changed_ratio": changed / float(width * height) if width and height else 0,
        }
    except Exception as exc:
        result["pixel_diff"] = {"skipped": True, "reason": str(exc)}
    return result


def live_url_for_page(live_base_url: str, interface_name: str, page) -> str:
    base = live_base_url.rstrip("/")
    page_name = str(page.name)
    if page.type == "activity":
        # Activity pages usually require an active_process_node_id; the URL is still
        # useful for screenshots after a process is started manually.
        return f"{base}/render_{interface_name}_{page_name}/1"
    if page_name.lower() in {"home", "task"}:
        return f"{base}/"
    return f"{base}/render_{interface_name}_{page_name}"


def _import_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright, None
    except Exception as exc:
        for candidate in (
            Path("D:/Anaconda/Lib/site-packages"),
            Path(os.environ.get("CONDA_PREFIX", "")) / "Lib" / "site-packages",
        ):
            if candidate.exists() and str(candidate) not in sys.path:
                sys.path.append(str(candidate))
        try:
            from playwright.sync_api import sync_playwright
            return sync_playwright, None
        except Exception:
            return None, exc


def _pixel_diff(preview_path: str, live_path: str) -> dict:
    try:
        from PIL import Image, ImageChops

        preview_img = Image.open(preview_path).convert("RGB")
        live_img = Image.open(live_path).convert("RGB")
        width = min(preview_img.width, live_img.width)
        height = min(preview_img.height, live_img.height)
        preview_crop = preview_img.crop((0, 0, width, height))
        live_crop = live_img.crop((0, 0, width, height))
        diff = ImageChops.difference(preview_crop, live_crop)
        changed = 0
        if diff.getbbox():
            pixels = diff.load()
            for y in range(height):
                for x in range(width):
                    if pixels[x, y] != (0, 0, 0):
                        changed += 1
        return {
            "compared_size": [width, height],
            "preview_size": [preview_img.width, preview_img.height],
            "live_size": [live_img.width, live_img.height],
            "changed_pixels": changed,
            "changed_ratio": changed / float(width * height) if width and height else 0,
        }
    except Exception as exc:
        return {"skipped": True, "reason": str(exc)}


def screenshot_url_pair(
    out_dir: Path,
    page_name: str,
    preview_url: str,
    live_url: str,
    preview_page_name: str,
    storage_state: str | None = None,
    live_login_url: str | None = None,
):
    sync_playwright, import_error = _import_playwright()
    if not sync_playwright:
        return {"skipped": True, "reason": f"playwright unavailable: {import_error}"}

    shots = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context_kwargs = {}
        if storage_state:
            context_kwargs["storage_state"] = storage_state
        context = browser.new_context(viewport={"width": 1440, "height": 1100}, **context_kwargs)
        browser_page = context.new_page()

        browser_page.goto(preview_url, wait_until="networkidle")
        tab = browser_page.get_by_role("button", name=re.compile(re.escape(preview_page_name).replace("_", r"[_ ]"), re.I))
        try:
            if tab.count():
                tab.first.click()
                browser_page.wait_for_timeout(300)
        except Exception:
            pass
        preview_path = out_dir / f"{page_name}.preview.url.png"
        browser_page.screenshot(path=str(preview_path), full_page=True)
        shots["preview"] = str(preview_path)

        if live_login_url:
            browser_page.goto(live_login_url, wait_until="networkidle")
        browser_page.goto(live_url, wait_until="networkidle")
        live_path = out_dir / f"{page_name}.live.url.png"
        browser_page.screenshot(path=str(live_path), full_page=True)
        shots["live"] = str(live_path)

        context.close()
        browser.close()

    return {
        "skipped": False,
        "mode": "url",
        "preview_url": preview_url,
        "live_url": live_url,
        "screenshots": shots,
        "pixel_diff": _pixel_diff(shots["preview"], shots["live"]),
    }


def request_json(method: str, url: str, body: dict | None = None, token: str | None = None):
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with {exc.code}: {detail}") from exc


def api_token(api_base: str, username: str, password: str) -> str:
    response = request_json(
        "POST",
        f"{api_base.rstrip('/')}/v1/auth/token",
        {"username": username, "password": password},
    )
    token = response.get("token")
    if not token:
        raise RuntimeError("Auth endpoint did not return a token.")
    return token


def api_preview_files(api_base: str, interface_id: str, token: str) -> list[dict]:
    response = request_json(
        "POST",
        f"{api_base.rstrip('/')}/v1/metadata/interfaces/{interface_id}/generate/",
        {
            "prompt": "",
            "inject_click_handlers": True,
        },
        token,
    )
    return [item for item in response.get("files", []) if str(item.get("path", "")).endswith(".html")]


def page_name_from_preview_file(file_obj: dict, interface_name: str) -> str:
    if file_obj.get("page"):
        return str(file_obj["page"])
    path = str(file_obj.get("path", ""))
    match = re.search(rf"{re.escape(interface_name)}_(.+?)\.html$", path, flags=re.IGNORECASE)
    if match:
        return snake_to_title(match.group(1))
    return snake_to_page_name(Path(path).stem or "Page")


def snake_to_page_name(name: str) -> str:
    raw = re.sub(r"\.html?$", "", str(name), flags=re.IGNORECASE)
    raw = re.sub(r"^templates/", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"^[a-z0-9]+_", "", raw, count=1)
    return snake_to_title(raw)


def snake_to_title(name: str) -> str:
    raw = str(name)
    return "_".join(part[:1].upper() + part[1:] for part in raw.split("_") if part)


def norm_page_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name).lower())


def live_url_for_page_name(live_base_url: str, interface_name: str, page_name: str) -> str:
    base = live_base_url.rstrip("/")
    if page_name.lower() in {"home", "task"}:
        return f"{base}/"
    if page_name.lower().startswith("workflow_"):
        return f"{base}/render_{interface_name}_{page_name}/1"
    return f"{base}/render_{interface_name}_{page_name}"


def screenshot_api_preview_pair(
    out_dir: Path,
    page_name: str,
    preview_html: str,
    live_url: str,
    storage_state: str | None = None,
    live_login_url: str | None = None,
):
    sync_playwright, import_error = _import_playwright()
    if not sync_playwright:
        return {"skipped": True, "reason": f"playwright unavailable: {import_error}"}

    shots = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context_kwargs = {}
        if storage_state:
            context_kwargs["storage_state"] = storage_state
        context = browser.new_context(viewport={"width": 1440, "height": 1100}, **context_kwargs)
        browser_page = context.new_page()

        browser_page.set_content(preview_html, wait_until="networkidle")
        preview_path = out_dir / f"{page_name}.preview.api.png"
        browser_page.screenshot(path=str(preview_path), full_page=True)
        shots["preview"] = str(preview_path)

        if live_login_url:
            browser_page.goto(live_login_url, wait_until="networkidle")
        browser_page.goto(live_url, wait_until="networkidle")
        live_path = out_dir / f"{page_name}.live.url.png"
        browser_page.screenshot(path=str(live_path), full_page=True)
        shots["live"] = str(live_path)

        context.close()
        browser.close()

    return {
        "skipped": False,
        "mode": "api-preview-to-live-url",
        "live_url": live_url,
        "screenshots": shots,
        "pixel_diff": _pixel_diff(shots["preview"], shots["live"]),
    }


def main():
    parser = argparse.ArgumentParser(description="Compare generated preview and live HTML/screenshots for every page.")
    parser.add_argument("--metadata", default=str(ROOT / "fixtures" / "Bol.com Shopping Platform-export.json"))
    parser.add_argument("--interface", default="", help="Interface name, e.g. Customer. Defaults to first interface.")
    parser.add_argument("--project-name", default="preview-live-compare")
    parser.add_argument("--out", default=str(ROOT / "tmp" / "preview-live-compare"))
    parser.add_argument("--screenshots", action="store_true", help="Capture screenshots when Playwright is installed.")
    parser.add_argument("--preview-url", default="", help="Optional live preview URL, e.g. http://ai4mde.localhost/api/v1/metadata/interfaces/<id>/candidates/0/preview/")
    parser.add_argument("--live-base-url", default="", help="Optional running prototype base URL, e.g. http://prototype.ai4mde.localhost/Customer")
    parser.add_argument("--storage-state", default="", help="Optional Playwright storage_state JSON for authenticated live pages.")
    parser.add_argument("--api-base", default="", help="Studio API base URL ending in /api, e.g. http://api.ai4mde.localhost/api.")
    parser.add_argument("--interface-id", default="", help="Interface UUID for API preview generation.")
    parser.add_argument("--auth-token", default=os.environ.get("AI4MDE_TOKEN", ""), help="Bearer token for API preview generation.")
    parser.add_argument("--auth-user", default="admin", help="API username when --auth-token is omitted.")
    parser.add_argument("--auth-password", default="sequoias", help="API password when --auth-token is omitted.")
    parser.add_argument("--live-login-user", default="", help="Prototype autologin user, e.g. jan_devries.")
    args = parser.parse_args()

    metadata_path = Path(args.metadata)
    metadata = metadata_path.read_text(encoding="utf-8")
    metadata_json = json.loads(metadata)
    interfaces = list(metadata_json.get("interfaces", []) or [])
    systems = list(metadata_json.get("systems", []) or [])
    for system in systems:
        interfaces.extend(system.get("interfaces", []) or [])
    selected = None
    if args.interface:
        selected = next((i for i in interfaces if i.get("name") == args.interface or i.get("label") == args.interface), None)
    selected = selected or (interfaces[0] if interfaces else None)
    if not selected:
        raise SystemExit("No interface found in metadata.")

    interface_name = selected.get("name") or selected.get("label")
    selected_system = None
    if systems:
        selected_system_id = selected.get("system")
        selected_system = next(
            (
                s for s in systems
                if str(s.get("id")) == str(selected_system_id)
                or any(str(i.get("id")) == str(selected.get("id")) for i in (s.get("interfaces") or []))
            ),
            systems[0],
        )
        flat_metadata = {
            "diagrams": selected_system.get("diagrams", []),
            "classifiers": selected_system.get("classifiers", []),
            "relations": selected_system.get("relations", []),
            "interfaces": [normalize_interface_entry(i) for i in (selected_system.get("interfaces", []) or [])],
        }
        metadata_for_loader = json.dumps(flat_metadata)
    else:
        flat_metadata = dict(metadata_json)
        flat_metadata["interfaces"] = [normalize_interface_entry(i) for i in interfaces]
        metadata_for_loader = json.dumps(flat_metadata)

    app = get_application_component(args.project_name, interface_name, metadata_for_loader, False)
    tokens = dict(getattr(app, "tokens", {}) or {})
    out_dir = Path(args.out) / interface_name
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = [_make_task_home_page(app)] + list(app.pages)
    report = {
        "metadata": str(metadata_path),
        "interface": interface_name,
        "out_dir": str(out_dir),
        "pages": [],
    }
    live_login_url = None
    if args.live_base_url and args.live_login_user:
        root = args.live_base_url.rstrip("/")
        if root.endswith(f"/{interface_name}"):
            root = root[: -(len(interface_name) + 1)]
        live_login_url = f"{root}/autologin?as={args.live_login_user}"

    api_files_by_page = {}
    if args.api_base and args.interface_id:
        token = args.auth_token or api_token(args.api_base, args.auth_user, args.auth_password)
        for file_obj in api_preview_files(args.api_base, args.interface_id, token):
            api_page_name = page_name_from_preview_file(file_obj, interface_name)
            api_files_by_page[norm_page_key(api_page_name)] = {"page_name": api_page_name, "file": file_obj}
            api_path = out_dir / f"{api_page_name}.preview.api.html"
            api_path.write_text(file_obj.get("content", ""), encoding="utf-8")

    for page in pages:
        preview_html, live_html = render_pair(app, page, tokens, args.project_name)
        page_name = str(page.name)
        preview_path = out_dir / f"{page_name}.preview.html"
        live_path = out_dir / f"{page_name}.live.html"
        preview_path.write_text(preview_html, encoding="utf-8")
        live_path.write_text(live_html, encoding="utf-8")

        page_report = {
            "page": page_name,
            "preview_html": str(preview_path),
            "live_html": str(live_path),
            **compare_structure(preview_html, live_html),
        }
        if args.screenshots:
            api_file_entry = api_files_by_page.get(norm_page_key(page_name))
            if args.api_base and args.interface_id and args.live_base_url and api_file_entry:
                page_report["screenshot"] = screenshot_api_preview_pair(
                    out_dir=out_dir,
                    page_name=page_name,
                    preview_html=api_file_entry["file"].get("content", ""),
                    live_url=live_url_for_page(args.live_base_url, interface_name, page),
                    storage_state=args.storage_state or None,
                    live_login_url=live_login_url,
                )
            elif args.preview_url and args.live_base_url:
                page_report["screenshot"] = screenshot_url_pair(
                    out_dir=out_dir,
                    page_name=page_name,
                    preview_url=args.preview_url,
                    live_url=live_url_for_page(args.live_base_url, interface_name, page),
                    preview_page_name=page_name,
                    storage_state=args.storage_state or None,
                    live_login_url=live_login_url,
                )
            else:
                page_report["screenshot"] = screenshot_with_playwright(out_dir, page_name, preview_html, live_html)
        report["pages"].append(page_report)

    existing_keys = {norm_page_key(item["page"]) for item in report["pages"]}
    if args.screenshots and args.api_base and args.interface_id and args.live_base_url:
        for key, api_file_entry in api_files_by_page.items():
            if key in existing_keys:
                continue
            api_page_name = api_file_entry["page_name"]
            preview_html = api_file_entry["file"].get("content", "")
            page_report = {
                "page": api_page_name,
                "preview_html": str(out_dir / f"{api_page_name}.preview.api.html"),
                "live_html": "",
                "section_order_match": None,
                "preview_sections": parse_html(preview_html)["sections"],
                "live_sections": [],
                "preview_unsupported": parse_html(preview_html)["unsupported"],
                "live_unsupported": [],
                "screenshot": screenshot_api_preview_pair(
                    out_dir=out_dir,
                    page_name=api_page_name,
                    preview_html=preview_html,
                    live_url=live_url_for_page_name(args.live_base_url, interface_name, api_page_name),
                    storage_state=args.storage_state or None,
                    live_login_url=live_login_url,
                ),
            }
            report["pages"].append(page_report)

    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    mismatches = [
        p for p in report["pages"]
        if p["section_order_match"] is False or p["preview_unsupported"] or p["live_unsupported"]
    ]
    print(json.dumps({
        "interface": interface_name,
        "pages_checked": len(report["pages"]),
        "mismatch_count": len(mismatches),
        "report": str(report_path),
        "screenshot_hint": "Run with --screenshots after installing Playwright: python -m pip install playwright && python -m playwright install chromium",
    }, indent=2))
    if mismatches:
        print("MISMATCHES:")
        for item in mismatches:
            print(f"- {item['page']}: order_match={item['section_order_match']} preview_unsupported={len(item['preview_unsupported'])} live_unsupported={len(item['live_unsupported'])}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
