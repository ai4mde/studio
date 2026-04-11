"""
Pipeline API endpoints — expose the LangGraph agent pipeline over REST.

Endpoints:
  POST /generator/pipeline/run/             Start a new pipeline run.
  GET  /generator/pipeline/{id}/            Get current state of a pipeline run.
  POST /generator/pipeline/{id}/emit/       Write Jinja2 templates to disk.
  GET  /generator/pipeline/{id}/preview/    Browser-viewable HTML preview of all rendered pages.
"""
import os
import shutil
import uuid
from typing import Optional

import requests as http_requests
from django.http import HttpResponse
from ninja import Router
from ninja.schema import Schema

from generator.agents.pipeline import pipeline
from generator.agents.renderer import render_page

pipeline_router = Router()


# ── Schemas ──────────────────────────────────────────────────────────────────

class RunPipelineSchema(Schema):
    project_name: str
    application_name: str
    metadata: str           # raw JSON string
    system_id: str
    authentication_present: bool = True


class PipelineStatusSchema(Schema):
    thread_id: str
    ui_design: Optional[dict]
    page_ir: Optional[dict]


class ErrorSchema(Schema):
    error: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _state_to_status(thread_id: str, state: dict) -> dict:
    return {
        "thread_id": thread_id,
        "ui_design": state.get("ui_design"),
        "page_ir": state.get("page_ir"),
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@pipeline_router.post("/run/", response=PipelineStatusSchema)
def run_pipeline(request, body: RunPipelineSchema):
    """Kick off a new pipeline run (parser → ui_designer → END)."""
    thread_id = str(uuid.uuid4())

    initial_state = {
        "project_name": body.project_name,
        "application_name": body.application_name,
        "metadata": body.metadata,
        "system_id": body.system_id,
        "authentication_present": body.authentication_present,
        "screens": [],
        "ui_design": None,
    }

    for event in pipeline.stream(initial_state, config=_config(thread_id)):
        pass

    snapshot = pipeline.get_state(_config(thread_id))
    return _state_to_status(thread_id, snapshot.values)


@pipeline_router.get("/{thread_id}/", response=PipelineStatusSchema)
def get_pipeline_status(request, thread_id: str):
    """Return the current state of a pipeline run."""
    snapshot = pipeline.get_state(_config(thread_id))
    if not snapshot.values:
        return 404, {"error": "thread not found"}
    return _state_to_status(thread_id, snapshot.values)


@pipeline_router.post("/{thread_id}/emit/", response={200: dict, 404: ErrorSchema})
def emit_pipeline_templates(request, thread_id: str):
    """Create a new independent prototype and write AI-generated pages into it.

    Steps:
      1. Clone {system_id}/ui/ scaffold into a fresh UUID-named directory.
      2. Write templates with {% extends %}{% block content %} wrapping.
      3. Append GenericTemplateView class to each actor's views.py.
      4. Insert path() entries into each actor's urls.py.
      5. Call POST /run to start the new prototype (stops any currently running one).
    """
    snapshot = pipeline.get_state(_config(thread_id))
    if not snapshot.values:
        return 404, {"error": "thread not found"}

    state = snapshot.values
    system_id = state.get("system_id", "unknown")

    # Mirror preview: use ui_ir directly (LLM output with ASTs)
    ui_ir = (state.get("ui_design") or {}).get("ui_ir") or state.get("page_ir") or {}
    apps = ui_ir.get("apps", [])

    # Actor name lookup from parser_dsl (same as preview)
    parser_dsl = state.get("parser_dsl") or {}
    actor_name_map = {a["id"]: a.get("name", a["id"]) for a in parser_dsl.get("actors", []) or []}

    # ── Clone scaffold into a fresh prototype directory ────────────────────
    new_proto_id = str(uuid.uuid4())
    root = "/usr/src/generated_prototypes"
    scaffold_src = os.path.join(root, system_id, "ui")
    new_base = os.path.join(root, new_proto_id, "ui")

    if os.path.isdir(scaffold_src):
        shutil.copytree(
            scaffold_src,
            new_base,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "db.sqlite3"),
        )
    else:
        os.makedirs(new_base, exist_ok=True)

    project_name = state.get("project_name", thread_id)

    written = []

    for app in apps:
        actor_id = app.get("actor_id", "unknown")
        actor_name = app.get("actor_name") or actor_name_map.get(actor_id, actor_id)
        actor_dir = actor_name.replace(" ", "_")
        app_path = os.path.join(new_base, actor_dir)
        templates_dir = os.path.join(app_path, "templates")
        os.makedirs(templates_dir, exist_ok=True)

        # Wipe ALL old scaffold templates — we generate everything fresh
        if os.path.isdir(templates_dir):
            for _f in os.listdir(templates_dir):
                if _f.endswith(".html"):
                    os.remove(os.path.join(templates_dir, _f))

        pages = app.get("pages", [])

        for i, page in enumerate(pages):
            page_name = page.get("name", "page")
            view_class = f"{page_name}View"

            # Build per-page nav with correct URLs (plain HTML hrefs)
            nav_items = []
            for j, p in enumerate(pages):
                route = "/" + actor_dir + "/" + ("" if j == 0 else p["name"] + "/")
                nav_items.append(
                    f'<a href="{route}" class="text-sm text-indigo-600 hover:underline">{p["name"]}</a>'
                )
            nav_html = "\n      ".join(nav_items)

            # ── Body content (same render logic as preview) ────────────────
            ast = page.get("ast", [])
            if ast:
                body_html = render_page(ast)
            else:
                action_ids = page.get("action_ids", [])
                body_html = (
                    f'<p class="text-gray-400 italic">Page under construction.'
                    f' Actions: {", ".join(action_ids)}</p>'
                )

            # ── Full standalone HTML identical to preview layout ───────────
            full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{page_name} &mdash; {actor_dir} &mdash; {project_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
</head>
<body class="bg-gray-50 min-h-screen font-sans">
  <header class="border-b border-gray-200 bg-white px-8 py-4 flex items-center justify-between">
    <h1 class="text-xl font-bold text-gray-900">{actor_dir} &mdash; {project_name}</h1>
    <nav class="flex items-center gap-6">
      {nav_html}
      <a href="/logout/" class="text-sm text-red-500 hover:underline">Logout</a>
    </nav>
  </header>
  <main class="max-w-4xl mx-auto p-8">
    <div class="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
      <header class="mb-6 pb-4 border-b border-gray-100">
        <h2 class="text-2xl font-bold text-gray-900">{page_name}</h2>
        <p class="text-sm text-gray-500 mt-1">{actor_dir} &mdash; {project_name}</p>
      </header>
      {body_html}
    </div>
  </main>
</body>
</html>"""

            tpl_path = os.path.join(templates_dir, f"{page_name}.html")
            with open(tpl_path, "w", encoding="utf-8") as f:
                f.write(full_html)
            written.append(tpl_path.replace(f"{root}/", ""))

        # ── Write a minimal views.py with TemplateView for each page ──────
        views_lines = [
            "from django.views.generic import TemplateView\n",
            "from django.contrib.auth.mixins import LoginRequiredMixin\n\n",
        ]
        for i, page in enumerate(pages):
            p_name = page.get("name", "page")
            v_class = f"{p_name}View"
            views_lines.append(
                f"class {v_class}(LoginRequiredMixin, TemplateView):\n"
                f"    template_name = '{p_name}.html'\n\n"
            )
        views_path = os.path.join(app_path, "views.py")
        with open(views_path, "w", encoding="utf-8") as f:
            f.writelines(views_lines)

        # ── Rewrite urls.py: first page = root, rest keep own path ────────
        urls_path = os.path.join(app_path, "urls.py")
        url_lines = []
        for i, page in enumerate(pages):
            p_name = page.get("name", "page")
            v_class = f"{p_name}View"
            route = "" if i == 0 else f"{p_name}/"
            url_lines.append(
                f"    path(\"{route}\", views.{v_class}.as_view(), name=\"render_{p_name}\"),\n"
            )
        new_urls = (
            "from django.urls import path\n"
            "from . import views\n\n"
            f'app_name="{actor_dir}"\n'
            "urlpatterns = [\n"
            + "".join(url_lines)
            + "]\n"
        )
        with open(urls_path, "w", encoding="utf-8") as f:
            f.write(new_urls)

    # ── Start prototype server via Flask runner ──────────────────────────────
    prototype_started = False
    prototype_error = None
    try:
        run_resp = http_requests.post(
            "http://studio-studio-prototypes-1:8010/run",
            json={"id": new_proto_id, "name": "ui", "system": new_proto_id},
            timeout=10,
            allow_redirects=False,
        )
        # /run returns 307 on success (redirects to running prototype)
        prototype_started = run_resp.status_code in (200, 307)
        if not run_resp.ok:
            prototype_error = run_resp.text[:200]
    except Exception as exc:
        prototype_error = str(exc)

    return {
        "new_proto_id": new_proto_id,
        "system_id": system_id,
        "written": written,
        "prototype_started": prototype_started,
        "prototype_error": prototype_error,
    }


@pipeline_router.get("/{thread_id}/preview/", auth=None)
def preview_pipeline_html(request, thread_id: str, actor: str = None, page: str = None):
    """Render pages from the pipeline's ui_ir AST as viewable HTML.

    Without params        → index: list all actors with links.
    ?actor=<id>           → actor page list: links to each individual page.
    ?actor=<id>&page=<name> → standalone HTML for that single page.
    """
    snapshot = pipeline.get_state(_config(thread_id))
    if not snapshot.values:
        return HttpResponse("<h1>Thread not found</h1>", status=404, content_type="text/html")

    state = snapshot.values
    ui_ir = (state.get("ui_design") or {}).get("ui_ir") or state.get("page_ir") or {}
    apps = ui_ir.get("apps", [])
    project_name = state.get("project_name", thread_id)

    # Build actor id → name lookup from parser_dsl
    parser_dsl = state.get("parser_dsl") or {}
    actor_name_map = {a["id"]: a.get("name", a["id"]) for a in parser_dsl.get("actors", []) or []}

    base_url = f"/api/v1/generator/pipeline/{thread_id}/preview/"

    # ── Single page view: ?actor=<id>&page=<name> ────────────────────────────
    if actor and page:
        app = next((a for a in apps if a.get("actor_id") == actor), None)
        if not app:
            return HttpResponse(f"<h1>Actor '{actor}' not found</h1>", status=404, content_type="text/html")

        page_data = next((p for p in app.get("pages", []) if p.get("name") == page), None)
        if not page_data:
            return HttpResponse(f"<h1>Page '{page}' not found</h1>", status=404, content_type="text/html")

        actor_name = app.get("actor_name") or actor_name_map.get(actor, actor)
        ast = page_data.get("ast", [])
        if ast:
            body = render_page(ast)
        else:
            action_ids = page_data.get("action_ids", [])
            body = (
                f'<p class="text-gray-400 italic">AST not yet generated. '
                f'Actions: {", ".join(action_ids)}</p>'
            )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{page} — {actor_name} — {project_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
</head>
<body class="bg-gray-50 min-h-screen p-8 font-sans">
  <header class="mb-8 border-b border-gray-200 pb-4 flex items-center gap-4">
    <a href="{base_url}?actor={actor}" class="text-sm text-indigo-600 hover:underline">&larr; {actor_name}</a>
    <div>
      <h1 class="text-2xl font-bold text-gray-900">{page}</h1>
      <p class="text-sm text-gray-500 mt-1">{actor_name} &mdash; {project_name}</p>
    </div>
  </header>
  <main class="max-w-4xl mx-auto">
    <div class="rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
      {body}
    </div>
  </main>
</body>
</html>"""
        return HttpResponse(html, content_type="text/html")

    # ── Actor page list: ?actor=<id> ──────────────────────────────────────────
    if actor:
        app = next((a for a in apps if a.get("actor_id") == actor), None)
        if not app:
            return HttpResponse(f"<h1>Actor '{actor}' not found</h1>", status=404, content_type="text/html")

        actor_name = app.get("actor_name") or actor_name_map.get(actor, actor)
        cards_html = ""
        for p in app.get("pages", []):
            page_name = p.get("name", "Page")
            ast = p.get("ast", [])
            has_ast = bool(ast)
            action_ids = p.get("action_ids", [])
            subtitle = f"{len(ast)} AST node(s)" if has_ast else f"Actions: {', '.join(action_ids)}"
            cards_html += f"""
<a href="{base_url}?actor={actor}&page={page_name}"
   class="block rounded-xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all">
  <div class="flex items-start justify-between">
    <div>
      <h2 class="text-lg font-semibold text-gray-900">{page_name}</h2>
      <p class="text-sm text-gray-400 mt-1">{subtitle}</p>
    </div>
    <span class="text-indigo-400 text-lg">&rarr;</span>
  </div>
</a>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{actor_name} — {project_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen p-8 font-sans">
  <header class="mb-8 border-b border-gray-200 pb-4 flex items-center gap-4">
    <a href="{base_url}" class="text-sm text-indigo-600 hover:underline">&larr; All actors</a>
    <div>
      <h1 class="text-2xl font-bold text-gray-900">{actor_name}</h1>
      <p class="text-sm text-gray-500 mt-1">{project_name}</p>
    </div>
  </header>
  <main class="max-w-2xl mx-auto grid gap-4">
    {cards_html if cards_html else '<p class="text-gray-500">No pages for this actor.</p>'}
  </main>
</body>
</html>"""
        return HttpResponse(html, content_type="text/html")

    # ── Index page — list all actors ──────────────────────────────────────────
    cards_html = ""
    for app in apps:
        actor_id = app.get("actor_id", "unknown")
        actor_name = app.get("actor_name") or actor_name_map.get(actor_id, actor_id)
        page_count = len(app.get("pages", []))
        page_label = f"{page_count} page{'s' if page_count != 1 else ''}"
        cards_html += f"""
<a href="{base_url}?actor={actor_id}"
   class="block rounded-xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all">
  <div class="flex items-start justify-between">
    <div>
      <p class="text-xs font-mono text-indigo-500 mb-1">{actor_id}</p>
      <h2 class="text-lg font-semibold text-gray-900">{actor_name}</h2>
    </div>
    <span class="text-sm text-gray-400">{page_label}</span>
  </div>
</a>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Preview — {project_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen p-8 font-sans">
  <header class="mb-8 border-b border-gray-200 pb-4">
    <h1 class="text-2xl font-bold text-gray-900">{project_name}</h1>
    <p class="text-sm text-gray-500 mt-1">Select an actor to view their pages &mdash; <code class="font-mono text-xs">{thread_id}</code></p>
  </header>
  <main class="max-w-2xl mx-auto grid gap-4">
    {cards_html if cards_html else '<p class="text-gray-500">No actors generated yet.</p>'}
  </main>
</body>
</html>"""
    return HttpResponse(html, content_type="text/html")
