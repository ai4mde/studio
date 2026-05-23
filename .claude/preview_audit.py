"""
Preview audit script: fetches real interface data from Postgres, renders the preview,
and takes a screenshot for Claude to visually verify against the bol.com reference.
Usage: python .claude/preview_audit.py [interface_name]
"""
import sys
import os
import json
import tempfile
from pathlib import Path
def dotenv_values(path: str) -> dict:
    result = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return result

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT))

TEMPLATE_DIR = str(ROOT / "prototypes" / "backend" / "generation" / "templates")
SCREENSHOT_PATH = str(ROOT / ".claude" / "preview_screenshot.png")
HTML_PATH = str(ROOT / ".claude" / "preview_latest.html")


def load_db_config():
    cfg = {}
    for env_file in ["config/api.env", "config/secrets.env"]:
        path = ROOT / env_file
        if path.exists():
            cfg.update(dotenv_values(str(path)))
    return cfg


def fetch_interface_data(interface_name: str | None = None):
    """Connect to Postgres and fetch the interface + classifiers + relations."""
    import psycopg2, psycopg2.extras

    cfg = load_db_config()
    conn = psycopg2.connect(
        host="localhost",
        port=int(cfg.get("POSTGRES_PORT", "5432")),
        dbname=cfg.get("POSTGRES_DB", "ai4mdestudio"),
        user=cfg.get("POSTGRES_USER", "ai4mdestudio"),
        password=cfg.get("POSTGRES_PASSWORD", "") or "",
    )
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get interface
    if interface_name:
        cur.execute(
            "SELECT id, name, data, system_id FROM metadata_interface WHERE name = %s ORDER BY id LIMIT 1",
            (interface_name,)
        )
    else:
        cur.execute(
            "SELECT id, name, data, system_id FROM metadata_interface ORDER BY id LIMIT 1"
        )
    iface = cur.fetchone()
    if not iface:
        print(f"ERROR: No interface found" + (f" named '{interface_name}'" if interface_name else ""))
        conn.close()
        sys.exit(1)

    iface_id = iface["id"]
    system_id = iface["system_id"]
    interface_name = iface["name"]
    interface_data = iface["data"] or {}

    print(f"Using interface: '{interface_name}' (id={iface_id})")

    # List available interfaces for reference
    cur.execute("SELECT name FROM metadata_interface ORDER BY id")
    all_names = [r["name"] for r in cur.fetchall()]
    print(f"Available interfaces: {all_names}")

    # Get classifiers
    cur.execute(
        "SELECT id, data FROM metadata_classifier WHERE system_id = %s",
        (system_id,)
    )
    classifiers = [{"id": str(r["id"]), "data": r["data"]} for r in cur.fetchall()]

    # Get relations
    cur.execute(
        "SELECT id, source_id, target_id, data FROM metadata_relation WHERE system_id = %s",
        (system_id,)
    )
    relations = [
        {
            "id": str(r["id"]),
            "source": str(r["source_id"]),
            "target": str(r["target_id"]),
            "data": r["data"],
        }
        for r in cur.fetchall()
    ]

    conn.close()
    return interface_data, classifiers, relations, interface_name


def render_html(interface_data, classifiers, relations, interface_name):
    import api.model.llm.template_renderer as tr
    tr.TEMPLATE_DIR = TEMPLATE_DIR

    pages = tr.render_preview(
        interface_data=interface_data,
        classifiers=classifiers,
        interface_name=interface_name,
        relations=relations,
    )
    if not pages:
        print("ERROR: render_preview returned no pages")
        sys.exit(1)

    # Return all pages; screenshot the first one
    return pages


def take_screenshot(html: str, out_path: str):
    from playwright.sync_api import sync_playwright

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        f.write(html)
        tmp = f.name

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(f"file:///{tmp.replace(os.sep, '/')}")
            page.wait_for_timeout(1500)
            page.screenshot(path=out_path, full_page=True)
            browser.close()
    finally:
        os.unlink(tmp)


if __name__ == "__main__":
    target_name = sys.argv[1] if len(sys.argv) > 1 else "Customer"

    print("Fetching real interface data from Postgres...")
    try:
        interface_data, classifiers, relations, iface_name = fetch_interface_data(target_name)
    except Exception as e:
        print(f"DB connection failed ({e}), is docker running?")
        sys.exit(1)

    print(f"Rendering preview ({len(interface_data.get('pages', []))} pages, "
          f"{len(interface_data.get('sections', []))} sections)...")
    pages = render_html(interface_data, classifiers, relations, iface_name)

    # Save all pages HTML; screenshot the first
    for i, p in enumerate(pages):
        out = HTML_PATH.replace(".html", f"_{i}.html") if i > 0 else HTML_PATH
        with open(out, "w", encoding="utf-8") as f:
            f.write(p["content"])
    print(f"Saved {len(pages)} HTML page(s)")

    print("Taking screenshot of first page...")
    take_screenshot(pages[0]["content"], SCREENSHOT_PATH)
    print(f"Screenshot saved: {SCREENSHOT_PATH}")
