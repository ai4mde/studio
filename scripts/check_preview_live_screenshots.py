import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCAL_SCHEME = "http"
DEFAULT_API_BASE = f"{DEFAULT_LOCAL_SCHEME}://api.ai4mde.localhost/api"
DEFAULT_LIVE_BASE = f"{DEFAULT_LOCAL_SCHEME}://prototype.ai4mde.localhost"


def validated_http_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Only absolute http(s) URLs are supported")
    return url


def request_json(method: str, url: str, body: dict | None = None, token: str = "") -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(validated_http_url(url), data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with {exc.code}: {detail}") from exc


def auth_token(api_base: str, username: str, password: str) -> str:
    payload = request_json(
        "POST",
        f"{api_base.rstrip('/')}/v1/auth/token",
        {"username": username, "password": password},
    )
    token = payload.get("token")
    if not token:
        raise RuntimeError("Auth token endpoint did not return a token.")
    return token


def title_from_path(path: str, interface_name: str) -> str:
    stem = Path(path).stem
    prefix = f"{interface_name}_"
    if stem.lower().startswith(prefix.lower()):
        stem = stem[len(prefix):]
    return "_".join(part[:1].upper() + part[1:] for part in stem.split("_") if part)


def page_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def preview_file(api_base: str, interface_id: str, interface_name: str, page_name: str, token: str) -> dict:
    payload = request_json(
        "POST",
        f"{api_base.rstrip('/')}/v1/metadata/interfaces/{interface_id}/generate/",
        {"prompt": "", "inject_click_handlers": True},
        token,
    )
    files = [f for f in payload.get("files", []) if str(f.get("path", "")).endswith(".html")]
    target = page_key(page_name)
    for file_obj in files:
        candidates = [
            str(file_obj.get("page") or ""),
            title_from_path(str(file_obj.get("path") or ""), interface_name),
            str(file_obj.get("path") or ""),
        ]
        if any(page_key(candidate) == target for candidate in candidates):
            return file_obj
    raise RuntimeError(f"No preview HTML matched page {page_name!r}. Available: {[f.get('path') for f in files]}")


def live_url(base_url: str, interface_name: str, page_name: str) -> str:
    root = base_url.rstrip("/")
    if root.lower().endswith(f"/{interface_name.lower()}"):
        root = root[: -(len(interface_name) + 1)]
    if page_name.lower() in {"home", "task"}:
        return f"{root}/{interface_name}/"
    return f"{root}/{interface_name}/render_{interface_name}_{page_name}"


def pixel_diff(preview_path: Path, live_path: Path) -> dict:
    preview = Image.open(preview_path).convert("RGB")
    live = Image.open(live_path).convert("RGB")
    width = min(preview.width, live.width)
    height = min(preview.height, live.height)
    diff = ImageChops.difference(preview.crop((0, 0, width, height)), live.crop((0, 0, width, height)))
    changed = 0
    if diff.getbbox():
        pixels = diff.load()
        for y in range(height):
            for x in range(width):
                if pixels[x, y] != (0, 0, 0):
                    changed += 1
    return {
        "compared_size": [width, height],
        "preview_size": [preview.width, preview.height],
        "live_size": [live.width, live.height],
        "changed_pixels": changed,
        "changed_ratio": changed / float(width * height) if width and height else 0,
    }


METRICS_SCRIPT = """
() => {
  const rect = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {x:r.x, y:r.y, width:r.width, height:r.height};
  };
  const sections = Array.from(document.querySelectorAll('[data-section-id]')).map((el) => ({
    id: el.getAttribute('data-section-id'),
    name: el.getAttribute('data-section-name') || '',
    position: el.getAttribute('data-position') || '',
    layout: el.getAttribute('data-layout') || '',
    col_span: el.getAttribute('data-col-span') || '',
    rect: rect(el),
  }));
  return {
    url: location.href,
    title: document.title,
    viewport: {width: innerWidth, height: innerHeight},
    document: {
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      bodyScrollWidth: document.body ? document.body.scrollWidth : null,
    },
    main: rect(document.querySelector('main')),
    header: rect(document.querySelector('header, [data-position="header"]')),
    footer: rect(document.querySelector('footer, [data-position="footer"]')),
    sections,
  };
}
"""


def main():
    parser = argparse.ArgumentParser(description="Screenshot and compare Studio design preview vs live prototype.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--interface-id", required=True)
    parser.add_argument("--interface-name", required=True)
    parser.add_argument("--page", required=True, help="Page name, e.g. Categories")
    parser.add_argument("--live-base", default=DEFAULT_LIVE_BASE)
    parser.add_argument("--live-user", default="jan_devries")
    parser.add_argument("--auth-user", default="admin")
    parser.add_argument("--auth-password", default="sequoias")
    parser.add_argument("--auth-token", default="")
    parser.add_argument("--out", default=str(ROOT / "tmp" / "screenshot-check"))
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=1100)
    args = parser.parse_args()

    out_dir = Path(args.out).resolve() / args.interface_name / args.page
    out_dir.mkdir(parents=True, exist_ok=True)

    token = args.auth_token or auth_token(args.api_base, args.auth_user, args.auth_password)
    preview = preview_file(args.api_base, args.interface_id, args.interface_name, args.page, token)
    preview_html = str(preview.get("content") or "")
    live_page_url = live_url(args.live_base, args.interface_name, args.page)
    login_url = f"{args.live_base.rstrip('/')}/autologin?as={urllib.parse.quote(args.live_user)}&next=/{args.interface_name}/render_{args.interface_name}_{args.page}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": args.width, "height": args.height})
        page = context.new_page()

        page.set_content(preview_html, wait_until="networkidle")
        preview_png = out_dir / "preview.png"
        page.screenshot(path=str(preview_png), full_page=True)
        preview_metrics = page.evaluate(METRICS_SCRIPT)

        page.goto(login_url, wait_until="networkidle")
        page.goto(live_page_url, wait_until="networkidle")
        live_png = out_dir / "live.png"
        page.screenshot(path=str(live_png), full_page=True)
        live_metrics = page.evaluate(METRICS_SCRIPT)

        context.close()
        browser.close()

    report = {
        "interface": args.interface_name,
        "page": args.page,
        "live_url": live_page_url,
        "screenshots": {
            "preview": str(preview_png),
            "live": str(live_png),
        },
        "pixel_diff": pixel_diff(preview_png, live_png),
        "preview_metrics": preview_metrics,
        "live_metrics": live_metrics,
    }
    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "report": str(report_path),
        "preview": str(preview_png),
        "live": str(live_png),
        "changed_ratio": report["pixel_diff"]["changed_ratio"],
        "preview_scroll_width": preview_metrics["document"]["scrollWidth"],
        "live_scroll_width": live_metrics["document"]["scrollWidth"],
        "preview_main": preview_metrics["main"],
        "live_main": live_metrics["main"],
    }, indent=2))


if __name__ == "__main__":
    main()
