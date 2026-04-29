"""
Generate a Bol.com Shop prototype and start the preview server.

Run inside the API container:
  docker exec studio-studio-api-1 bash -c "cd /usr/src/model && python /tmp/gen_bol_prototype.py"

The script will:
  1. Run the full LangGraph pipeline on bol_shop.json
     (parser → ui_designer → theme → layout_options → interface_mapper → metadata_export)
  2. Apply a default composition using product-detail/buybox-right for product pages
  3. Emit standalone HTML files to /usr/src/generated_prototypes/{proto_id}/ui/
  4. Start the prototype server and print the preview URL
"""
import os, sys, uuid, json, shutil, time

sys.path.insert(0, "/usr/src/model")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "model.settings")
import django; django.setup()

from generator.agents.pipeline import pipeline
from generator.api.views.pipeline import (
    _resolve_preview_inputs,
    _render_emit_page_body,
    _preview_surface_class,
    _page_body_class,
    _page_main_class,
)
import requests as http_requests

# ── 1. Load bol_shop.json ────────────────────────────────────────────────────

with open("/tmp/bol_shop.json") as f:
    shop_data = json.load(f)

metadata_str = json.dumps(shop_data)
thread_id    = str(uuid.uuid4())
system_id    = "bol-shop-demo"
project_name = "Bol.com Shop"

print("=" * 60)
print("BOL.COM SHOP PROTOTYPE GENERATOR")
print("=" * 60)
print(f"Thread ID: {thread_id}")
print(f"Classifiers: {len(shop_data.get('classifiers', []))}")
print(f"Relations:   {len(shop_data.get('relations', []))}")
print()

# ── 2. Run the LangGraph pipeline ────────────────────────────────────────────

initial_state = {
    "project_name":         project_name,
    "application_name":     "shop",
    "metadata":             metadata_str,
    "system_id":            system_id,
    "authentication_present": False,
    "screens":              [],
    "ui_design":            None,
}

config = {"configurable": {"thread_id": thread_id}}

print("Running pipeline (this may take 1-2 minutes)...")
t0 = time.time()
for event in pipeline.stream(initial_state, config=config):
    for node_name in event:
        elapsed = time.time() - t0
        print(f"  [{elapsed:.1f}s] node done: {node_name}")

snapshot = pipeline.get_state(config)
state    = snapshot.values
print(f"Pipeline finished in {time.time()-t0:.1f}s")
print()

# ── 3. Collect apps / theme / layout ─────────────────────────────────────────

apps, preview_theme, preview_layout = _resolve_preview_inputs(state)
print(f"Actors: {[a.get('actor_name','?') for a in apps]}")
total_pages = sum(len(a.get('pages', [])) for a in apps)
print(f"Total pages: {total_pages}")
print()

# ── 4. Emit HTML files ────────────────────────────────────────────────────────

new_proto_id = str(uuid.uuid4())
root         = "/usr/src/generated_prototypes"
new_base     = os.path.join(root, new_proto_id, "ui")
os.makedirs(new_base, exist_ok=True)

written = []

for app in apps:
    actor_name = app.get("actor_name", "Actor")
    actor_dir  = actor_name.replace(" ", "_")
    app_path   = os.path.join(new_base, actor_dir)
    templates_dir = os.path.join(app_path, "templates")
    os.makedirs(templates_dir, exist_ok=True)

    pages = app.get("pages", [])
    print(f"  Actor '{actor_name}': {len(pages)} page(s)")

    for i, page in enumerate(pages):
        page_name  = page.get("name", "page")
        body_html  = _render_emit_page_body(page, theme=preview_theme)
        surface_cl = _preview_surface_class(page, theme=preview_theme)
        body_cl    = _page_body_class(preview_theme)
        main_cl    = _page_main_class(preview_theme, page)

        # Nav links
        nav_items = []
        for j, p in enumerate(pages):
            route = "/" + actor_dir + "/" + ("" if j == 0 else p["name"] + "/")
            nav_items.append(
                f'<a href="{route}" style="margin-right:12px;text-decoration:none;'
                f'color:#e57000;font-size:14px;">{p["name"]}</a>'
            )
        nav_html = "\n".join(nav_items)

        # Layout elements
        def _elements_at(pos):
            return "\n".join(
                v["html"] for v in preview_layout.values()
                if isinstance(v, dict) and v.get("position") == pos and v.get("html")
            )

        top_html    = _elements_at("top")
        left_html   = _elements_at("left")
        right_html  = _elements_at("right")
        bottom_html = _elements_at("bottom")

        if left_html or right_html:
            page_shell = (
                f"{top_html}\n"
                f'<div style="display:flex;min-height:calc(100vh - 60px);">\n'
                f"  {left_html}\n"
                f'  <div class="content {main_cl}" style="flex:1;padding:20px;">\n'
                f'    <div class="{surface_cl}">{body_html}</div>\n'
                f"  </div>\n"
                f"  {right_html}\n"
                f"</div>\n"
                f"{bottom_html}"
            )
        else:
            page_shell = (
                f"{top_html}\n"
                f'<div class="content {main_cl}" style="padding:20px;">\n'
                f'  <nav style="margin-bottom:16px;">{nav_html}</nav>\n'
                f'  <div class="{surface_cl}">{body_html}</div>\n'
                f"</div>\n"
                f"{bottom_html}"
            )

        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{page_name} — {actor_dir} — {project_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>body {{ margin:0; padding:0; }}</style>
</head>
<body class="{body_cl}">
{page_shell}
</body>
</html>"""

        tpl_path = os.path.join(templates_dir, f"{page_name}.html")
        with open(tpl_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        written.append(tpl_path.replace(root + "/", ""))
        print(f"    wrote: {page_name}.html ({len(full_html)} bytes)")

    # Minimal views.py + urls.py
    views_lines = ["from django.views.generic import TemplateView\n\n"]
    for p in pages:
        n = p.get("name", "page")
        views_lines.append(
            f"class {n}View(TemplateView):\n"
            f"    template_name = '{n}.html'\n\n"
        )
    with open(os.path.join(app_path, "views.py"), "w") as f:
        f.writelines(views_lines)

    url_lines = []
    for i, p in enumerate(pages):
        n = p.get("name", "page")
        route = "" if i == 0 else f"{n}/"
        url_lines.append(f'    path("{route}", views.{n}View.as_view(), name="render_{n}"),\n')
    with open(os.path.join(app_path, "urls.py"), "w") as f:
        f.write(
            "from django.urls import path\nfrom . import views\n\n"
            f'app_name="{actor_dir}"\n'
            "urlpatterns = [\n" + "".join(url_lines) + "]\n"
        )

print()
print(f"Written {len(written)} template file(s)")
print()

# ── 5. Start prototype server ─────────────────────────────────────────────────

print("Starting prototype server...")
try:
    run_resp = http_requests.post(
        "http://studio-studio-prototypes-1:8010/run",
        json={"id": new_proto_id, "name": "ui", "system": new_proto_id},
        timeout=15,
        allow_redirects=False,
    )
    started = run_resp.status_code in (200, 307)
    print(f"Server response: {run_resp.status_code}")
except Exception as exc:
    started = False
    print(f"Server start failed: {exc}")

print()
print("=" * 60)
print("DONE")
print(f"Proto ID: {new_proto_id}")
print(f"Files written: {len(written)}")
if started:
    print()
    print("Preview URLs (open in browser):")
    for a in apps:
        actor_dir = a.get("actor_name", "Actor").replace(" ", "_")
        pages = a.get("pages", [])
        if pages:
            print(f"  http://localhost:8010/{new_proto_id}/{actor_dir}/")
            for p in pages[1:]:
                print(f"  http://localhost:8010/{new_proto_id}/{actor_dir}/{p['name']}/")
else:
    print()
    print("Prototype server not started — HTML files are at:")
    print(f"  {new_base}/")
print("=" * 60)
