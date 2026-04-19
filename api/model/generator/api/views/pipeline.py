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
from typing import Optional, List, Any, cast

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
  system_id: Optional[str]
  ui_design: Optional[dict]
  page_ir: Optional[dict]
  flow_graph: Optional[dict]
  theme: Optional[dict]
  layout_options: Optional[list]
  global_layout: Optional[dict]
  interface_ir: Optional[list]
  final_metadata: Optional[dict]


class ErrorSchema(Schema):
    error: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _state_to_status(thread_id: str, state: dict) -> dict:
  return {
    "thread_id": thread_id,
    "system_id": state.get("system_id"),
    "ui_design": state.get("ui_design"),
    "page_ir": state.get("page_ir"),
    "flow_graph": state.get("flow_graph") or (state.get("parser_dsl") or {}).get("flow_graph"),
    "theme": state.get("theme"),
    "layout_options": state.get("layout_options"),
    "global_layout": state.get("global_layout"),
    "interface_ir": state.get("interface_ir"),
    "final_metadata": state.get("final_metadata"),
  }


def _sync_derived_outputs(state: dict) -> dict:
  from generator.agents.nodes import interface_mapper_node, metadata_export_node

  typed_state = cast(Any, state)
  mapped = interface_mapper_node(typed_state)
  merged_state = {**state, **mapped}
  exported = metadata_export_node(cast(Any, merged_state))
  return {**mapped, **exported}


def _preview_source_from_final_metadata(state: dict) -> tuple[list, dict | None, dict]:
  final_metadata = state.get("final_metadata") or {}
  interfaces = final_metadata.get("interfaces") or []
  if not isinstance(interfaces, list) or not interfaces:
    return [], None, {}

  apps: list[dict] = []
  theme: dict | None = None
  global_layout: dict = {}

  for iface in interfaces:
    if not isinstance(iface, dict):
      continue
    data = iface.get("data") or {}
    pages: list[dict] = []
    for page in data.get("pages") or []:
      if not isinstance(page, dict):
        continue
      pages.append({
        "name": page.get("name", ""),
        "type": (page.get("type") or {}).get("value", "normal"),
        "activity_name": (page.get("action") or {}).get("label"),
        "category": page.get("category"),
        "renderAst": page.get("renderAst") or page.get("ast") or [],
        "semanticAst": page.get("semanticAst") or {},
        "ast": page.get("renderAst") or page.get("ast") or [],
      })

    if not pages:
      component_schema = data.get("componentSchema") or {}
      pages = component_schema.get("pages") or []
    actor_id = str(iface.get("actor") or iface.get("actor_id") or "")
    actor_name = iface.get("name") or iface.get("actor_name") or actor_id

    if pages:
      apps.append({
        "actor_id": actor_id,
        "actor_name": actor_name,
        "pages": pages,
      })

    if theme is None and isinstance(data.get("theme"), dict):
      theme = data.get("theme")

    layout = data.get("layout") or {}
    selected_layout = layout.get("selected") or {}
    if not global_layout and isinstance(selected_layout, dict):
      global_layout = selected_layout

  return apps, theme, global_layout


def _resolve_preview_inputs(state: dict) -> tuple[list, dict | None, dict]:
  apps, theme, global_layout = _preview_source_from_final_metadata(state)
  if apps:
    return apps, theme or state.get("theme"), global_layout or (state.get("global_layout") or {})

  ui_ir = (state.get("ui_design") or {}).get("ui_ir") or state.get("page_ir") or {}
  return ui_ir.get("apps", []), state.get("theme"), state.get("global_layout") or {}


def _collect_page_ast_nodes(page: dict) -> list:
  """Collect renderable AST nodes from either legacy or region-based page schemas."""
  ast = page.get("renderAst", []) or page.get("ast", []) or []
  if ast:
    return ast

  nodes: list = []
  for region in page.get("regions", []) or []:
    region_ast = region.get("ast", []) or []
    region_children: list = []
    if region_ast:
      region_children = list(region_ast)
    else:
      for component in region.get("components", []) or []:
        component_ast = component.get("ast", []) or []
        if component_ast:
          region_children.extend(component_ast)

    if not region_children:
      continue

    # Keep region styling dynamic via theme tokens: region.<type>.
    # This adds a wrapper mount-point for outer region styles without hardcoded classes.
    nodes.append(
      {
        "tag": "div",
        "variant": region.get("type", ""),
        "attrs": {"data-region": region.get("id", "")},
        "children": region_children,
      }
    )
  return nodes


def _render_page_body(page: dict, theme: dict | None = None) -> str:
  """Render page HTML from legacy page.ast or the newer page.regions schema."""
  ast_nodes = _collect_page_ast_nodes(page)
  if ast_nodes:
    return render_page(ast_nodes, theme)

  action_ids = page.get("action_ids", []) or []
  return (
    f'<p class="text-gray-400 italic">Page under construction.'
    f' Actions: {", ".join(action_ids)}</p>'
  )


def _get_theme_token(theme: dict | None, key: str, fallback: str = "") -> str:
  """Return a theme token value by key, or fallback if absent/empty."""
  if not theme:
    return fallback
  tokens = (theme.get("tokens") or {}) if isinstance(theme, dict) else {}
  val = tokens.get(key, "").strip()
  return val if val else fallback


def _filter_token_classes(raw: str, prefixes: tuple[str, ...], exact: tuple[str, ...] = ()) -> str:
  """Filter class tokens by allowed prefixes/exact names.

  Keeps rendering resilient when upstream tokens contain layout-breaking utilities.
  """
  if not raw:
    return ""
  picked = [c for c in raw.split() if c in exact or any(c.startswith(p) for p in prefixes)]
  return " ".join(picked)


def _sanitize_surface_classes(raw: str) -> str:
  """Keep only container-safe classes for card/surface wrappers."""
  return _filter_token_classes(
    raw,
    (
      "bg-",
      "text-",
      "border",
      "shadow",
      "ring",
      "rounded",
      "from-",
      "via-",
      "to-",
      "backdrop-",
      "p-",
      "px-",
      "py-",
      "pt-",
      "pb-",
      "pl-",
      "pr-",
      "m-",
      "mx-",
      "my-",
      "mt-",
      "mb-",
      "ml-",
      "mr-",
      "max-w-",
      "w-",
    ),
  )


def _page_body_class(theme: dict | None) -> str:
  """Return safe <body> classes from page.body token.

  Do not let global text/layout utilities leak into every child node.
  """
  raw = _get_theme_token(theme, "page.body", "")
  return _filter_token_classes(
    raw,
    ("bg-", "text-", "font-", "tracking-", "leading-", "from-", "via-", "to-", "backdrop-"),
    ("antialiased", "subpixel-antialiased"),
  )


def _build_preview_structural_css(layout_type: str, tokens: dict) -> str:
  """Build inline CSS that mirrors the prototype's structural layout."""
  # Extract theme colors for fallback when no Tailwind tokens fully style it
  bg = ""
  text = ""
  accent = ""
  accent_text = ""
  surface = ""
  border = ""
  font = ""
  radius = "8"

  if tokens:
    # Try to extract colors from token class strings
    # These are Tailwind classes, but we also provide CSS fallbacks
    pass

  css = """
body { margin: 0; padding: 0; font-family: sans-serif; }
.header {
  text-align: center;
  padding: 15px;
}
.header h1 { margin: 0; font-size: 24px; }
.menu {
  width: 200px;
  padding: 15px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  flex-wrap: nowrap;
}
.menu a {
  text-decoration: none;
  padding: 10px;
  display: block;
  margin-bottom: 8px;
  text-align: center;
  max-width: 200px;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}
.content { padding: 20px; }
.breadcrumbs { padding: 8px 0; font-size: 14px; }
.breadcrumbs a { text-decoration: none; }
.breadcrumb-sep { margin: 0 6px; }
.breadcrumb-current { font-weight: 600; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; overflow: hidden; }
th, td { padding: 8px; text-align: left; }
td input[type="text"], td input[type="number"], td select {
  width: 100%; height: 100%; box-sizing: border-box;
  padding: 8px; border: none; outline: none;
}
input[type="submit"] { border: none; padding: 10px; cursor: pointer; }
form a { text-decoration: none; }
.process-item {
  padding: 20px; width: 350px; text-align: center;
  display: flex; justify-content: space-between; align-items: center;
  position: relative;
}
.process-item h4 { margin: 0; padding: 0; font-size: 20px; flex: 1; text-align: left; line-height: 1; }
.process-button { border: none; padding: 12px; cursor: pointer; flex-shrink: 0; }
.no-processes { font-size: 18px; text-align: left; }
.active-node-name { font-size: 14px; margin-top: 5px; text-align: left; }
.complete-activity-button { padding: 10px 20px; border: none; cursor: pointer; font-size: 16px; }
"""

  if layout_type == "sidebar_left":
    css += """
.menu { float: left; height: 100vh; }
.content { margin-left: 220px; }
"""
  elif layout_type == "sidebar_right":
    css += """
.menu-right { float: right !important; height: 100vh; }
.content-sidebar-right { margin-left: 0 !important; margin-right: 240px; }
"""
  elif layout_type == "top_nav":
    css += """
.topnav {
  display: flex; gap: 0; padding: 0 15px;
}
.topnav a {
  padding: 10px 16px; text-decoration: none; display: inline-block;
}
.content-topnav { margin-left: 0 !important; padding: 24px; }
"""
  elif layout_type == "top_nav_sidebar":
    css += """
.header { display: flex; align-items: center; justify-content: space-between; }
.topnav-inline { display: flex; gap: 8px; }
.topnav-inline a { text-decoration: none; padding: 8px 12px; }
.menu { float: left; height: calc(100vh - 60px); }
.content { margin-left: 220px; }
"""

  return css


def _resolve_preview_token_class(
  theme: dict | None,
  preferred_prefixes: tuple[str, ...],
  *,
  page: dict | None = None,
  include_region_types: bool = False,
  sanitize_surface: bool = False,
) -> str:
  """Generic class resolver for preview shells/cards/main wrappers.

  This keeps token selection logic centralized so new component types do not
  require adding one-off resolver functions.
  """
  tokens = (theme.get("tokens") or {}) if isinstance(theme, dict) and theme else {}
  populated_keys = [k for k, v in tokens.items() if isinstance(v, str) and v.strip()]

  candidate_keys: list[str] = []
  if include_region_types and page:
    region_types = [
      r.get("type")
      for r in (page.get("regions", []) or [])
      if isinstance(r, dict) and r.get("type")
    ]
    candidate_keys.extend([f"region.{t}" for t in region_types])

  def _rank(key: str) -> tuple[int, str]:
    for idx, prefix in enumerate(preferred_prefixes):
      if key == prefix or key.startswith(prefix + ".") or key.startswith(prefix):
        return (idx, key)
    if key.startswith("region."):
      return (len(preferred_prefixes), key)
    return (len(preferred_prefixes) + 1, key)

  for key in sorted(populated_keys, key=_rank):
    if key not in candidate_keys:
      candidate_keys.append(key)

  for key in candidate_keys:
    val = tokens.get(key)
    if not isinstance(val, str) or not val.strip():
      continue
    resolved = _sanitize_surface_classes(val.strip()) if sanitize_surface else val.strip()
    if resolved:
      return resolved

  return ""


def _page_main_class(theme: dict | None, page: dict | None = None) -> str:
  """Return Tailwind classes for <main> wrapper from option/theme tokens."""
  return _resolve_preview_token_class(theme, ("page.main", "layout.main"))


def _preview_surface_class(page: dict, theme: dict | None = None) -> str:
  """Build preview content card classes from option/theme tokens."""
  return _resolve_preview_token_class(
    theme,
    ("page.surface",),
    page=page,
    include_region_types=True,
    sanitize_surface=True,
  )


def _preview_list_main_class(theme: dict | None) -> str:
  """Return classes for actor/index list <main> from option/theme tokens."""
  return _resolve_preview_token_class(theme, ("page.main", "layout.main"))


def _preview_list_card_class(theme: dict | None) -> str:
  """Return classes for actor/index cards from option/theme tokens."""
  return _resolve_preview_token_class(
    theme,
    ("page.surface",),
    sanitize_surface=True,
  )


def _page_preview_subtitle(page: dict) -> str:
  """Build a human-readable preview subtitle for actor page listings."""
  ast_nodes = _collect_page_ast_nodes(page)
  if ast_nodes:
    return f"{len(ast_nodes)} AST node(s)"

  region_count = len(page.get("regions", []) or [])
  if region_count:
    return f"{region_count} region(s)"

  action_ids = page.get("action_ids", []) or []
  return f"Actions: {', '.join(action_ids)}"


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


@pipeline_router.post("/generate-interfaces/", response={200: dict, 400: ErrorSchema})
def generate_interfaces(request, body: RunPipelineSchema):
    """Run the pipeline and write interface_ir results into the Interface model.

    For each actor in the pipeline output, upserts an Interface record:
    - If an Interface with the same actor already exists for the system, update its data.
    - Otherwise create a new Interface.

    Returns the list of upserted interface IDs.
    """
    from metadata.models import System, Interface, Classifier

    # ── Run pipeline ──────────────────────────────────────────────────────
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
    state = snapshot.values
    interface_ir = state.get("interface_ir") or []
    if not interface_ir:
        return 400, {"error": "Pipeline produced no interface_ir"}

    # ── Resolve System ────────────────────────────────────────────────────
    try:
        system = System.objects.get(pk=body.system_id)
    except System.DoesNotExist:
        return 400, {"error": f"System {body.system_id} not found"}

    # ── Build actor name → Classifier lookup ──────────────────────────────
    actor_classifiers = {
        c.data.get("name", ""): c
        for c in Classifier.objects.filter(system=system, data__type="actor")
    }

    # ── Upsert interfaces ────────────────────────────────────────────────
    upserted: list[dict] = []
    for iface in interface_ir:
        actor_name = iface.get("actor_name", "")
        iface_data = iface.get("data", {})

        actor_cls = actor_classifiers.get(actor_name)
        if not actor_cls:
            continue

        existing = Interface.objects.filter(system=system, actor=actor_cls).first()
        if existing:
            existing.data = iface_data
            existing.save(update_fields=["data"])
            upserted.append({"id": str(existing.id), "actor": actor_name, "action": "updated"})
        else:
            new_iface = Interface.objects.create(
                name=actor_name,
                description=f"Generated from pipeline for {actor_name}",
                system=system,
                actor=actor_cls,
                data=iface_data,
            )
            upserted.append({"id": str(new_iface.id), "actor": actor_name, "action": "created"})

    return {
        "thread_id": thread_id,
        "upserted": upserted,
    }


@pipeline_router.get("/{thread_id}/", response={200: PipelineStatusSchema, 404: ErrorSchema})
def get_pipeline_status(request, thread_id: str):
    """Return the current state of a pipeline run."""
    snapshot = pipeline.get_state(_config(thread_id))
    if not snapshot.values:
        return 404, {"error": "thread not found"}
    return 200, _state_to_status(thread_id, snapshot.values)


class RefineSchema(Schema):
    prompt: str


class SelectLayoutSchema(Schema):
    option_id: str


@pipeline_router.post("/{thread_id}/layout/select/", response={200: PipelineStatusSchema, 404: ErrorSchema, 400: ErrorSchema})
def select_layout(request, thread_id: str, body: SelectLayoutSchema):
    """Apply one of the pre-generated layout options as the active global_layout.

    The chosen option's elements (html + position + config) become global_layout,
    ready for preview rendering and subsequent refinement via the refine endpoint.
    """
    config = _config(thread_id)
    snapshot = pipeline.get_state(config)
    if not snapshot.values:
        return 404, {"error": "thread not found"}

    options = snapshot.values.get("layout_options") or []
    chosen = next((o for o in options if o.get("id") == body.option_id), None)
    if chosen is None:
        return 400, {"error": f"option_id '{body.option_id}' not found"}

    # Apply option's theme_tokens over the current theme so form/content
    # styling matches the chosen layout's visual style.
    updates: dict = {"global_layout": chosen.get("elements", {})}
    option_tokens = chosen.get("theme_tokens") or {}
    if option_tokens:
        current_theme = dict(snapshot.values.get("theme") or {})
        merged_tokens = {**((current_theme.get("tokens") or {})), **option_tokens}
        updates["theme"] = {**current_theme, "tokens": merged_tokens, "strict_dynamic": True}

    derived_updates = _sync_derived_outputs({**snapshot.values, **updates})
    pipeline.update_state(config, {**updates, **derived_updates})
    snapshot = pipeline.get_state(config)
    return 200, _state_to_status(thread_id, snapshot.values)


@pipeline_router.post("/{thread_id}/refine/", response={200: PipelineStatusSchema, 404: ErrorSchema})
def refine_pipeline(request, thread_id: str, body: RefineSchema):
    """Re-run the theme agent with a user-supplied refinement prompt.

    Also calls the layout agent to generate/update global layout elements
    (navbar, sidebar, footer) when the prompt requests them.
    """
    import json as _json
    from generator.agents.nodes import theme_node as _theme_node
    from llm.handler import call_openai
    from llm.prompts.agents import AGENT_LAYOUT_DESIGNER

    config = _config(thread_id)
    snapshot = pipeline.get_state(config)
    if not snapshot.values:
        return 404, {"error": "thread not found"}

    state = dict(snapshot.values)
    state["refine_prompt"] = body.prompt

    # ── 1. Re-run theme node ──────────────────────────────────────────────────
    new_theme = _theme_node(cast(Any, state))
    if isinstance(new_theme, dict) and isinstance(new_theme.get("theme"), dict):
      new_theme["theme"] = {**new_theme["theme"], "strict_dynamic": True}

    # ── 2. Run layout agent if prompt mentions layout elements ────────────────
    layout_keywords = ("nav", "sidebar", "footer", "header", "menu", "bar")
    needs_layout = any(kw in body.prompt.lower() for kw in layout_keywords)
    new_layout = {}
    if needs_layout:
        try:
            parser_dsl = state.get("parser_dsl") or {}
            actors = [a.get("name", a.get("id", "")) for a in (parser_dsl.get("actors") or [])]
            design_goal = (new_theme.get("theme") or {}).get("name") or \
                          f"Clean professional UI for {state.get('project_name', '')}"
            layout_prompt = AGENT_LAYOUT_DESIGNER.format(
                project_name=state.get("project_name", ""),
                application_name=state.get("application_name", ""),
                actors_json=_json.dumps(actors),
                design_goal=design_goal,
                refine_prompt=body.prompt,
            )
            raw = call_openai("gpt-4o", layout_prompt)
            raw = raw.strip()
            if raw.startswith("```"):
                lines = raw.split("\n")
                raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            layout_result = _json.loads(raw)
            # Merge with existing global_layout so previous elements are preserved.
            # New schema: {name: {html, position}}. Null values from LLM mean "leave as-is".
            existing = state.get("global_layout") or {}
            merged = {**existing}
            for name, element in layout_result.items():
                if element is not None:
                    merged[name] = element
            new_layout = {"global_layout": merged}
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("layout agent failed: %s", exc)

    # ── 3. Persist updates back into the LangGraph checkpoint ────────────────
    derived_updates = _sync_derived_outputs({**state, **new_theme, **new_layout})
    pipeline.update_state(config, {**new_theme, **new_layout, **derived_updates})

    snapshot = pipeline.get_state(config)
    return 200, _state_to_status(thread_id, snapshot.values)


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

    apps, preview_theme, preview_layout = _resolve_preview_inputs(state)

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
            body_html = _render_page_body(page, theme=preview_theme)
            surface_class = _preview_surface_class(page, theme=preview_theme)
            body_class = _page_body_class(preview_theme)
            main_class = _page_main_class(preview_theme, page)

            def _elements_at(pos: str) -> str:
                parts = [
                    v["html"] for v in preview_layout.values()
                    if isinstance(v, dict) and v.get("position") == pos and v.get("html")
                ]
                return "\n      ".join(parts)

            top_html = _elements_at("top")
            left_html = _elements_at("left")
            right_html = _elements_at("right")
            bottom_html = _elements_at("bottom")

            if left_html or right_html:
                page_shell = f"""{top_html}
<div style="display:flex;min-height:calc(100vh - 60px);">
  {left_html}
  <div class="content {main_class}" style="flex:1;padding:20px;">
    <div class="{surface_class}">
      {body_html}
    </div>
  </div>
  {right_html}
</div>
{bottom_html}"""
            else:
                page_shell = f"""{top_html}
<div class="content {main_class}" style="padding:20px;">
  <div class="{surface_class}">
    {body_html}
  </div>
</div>
{bottom_html}"""

            # ── Full standalone HTML identical to preview layout ───────────
            full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{page_name} &mdash; {actor_dir} &mdash; {project_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  <style>body {{ margin:0; padding:0; }}</style>
</head>
<body class="{body_class}">
{page_shell}
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
def preview_pipeline_html(request, thread_id: str, actor: Optional[str] = None, page: Optional[str] = None):
    """Render pages from the pipeline's ui_ir AST as viewable HTML.

    Without params        → index: list all actors with links.
    ?actor=<id>           → actor page list: links to each individual page.
    ?actor=<id>&page=<name> → standalone HTML for that single page.
    """
    snapshot = pipeline.get_state(_config(thread_id))
    if not snapshot.values:
        return HttpResponse("<h1>Thread not found</h1>", status=404, content_type="text/html")

    state = snapshot.values
    apps, preview_theme, preview_layout = _resolve_preview_inputs(state)
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
        body = _render_page_body(page_data, theme=preview_theme)
        surface_class = _preview_surface_class(page_data, theme=preview_theme)
        body_class = _page_body_class(preview_theme)
        main_class = _page_main_class(preview_theme, page_data)

        global_layout = preview_layout or {}

        def _elements_at(pos: str) -> str:
            """Concatenate HTML for all layout elements at the given position."""
            parts = [
                v["html"] for v in global_layout.values()
                if isinstance(v, dict) and v.get("position") == pos and v.get("html")
            ]
            return "\n".join(parts)

        top_html    = _elements_at("top")
        left_html   = _elements_at("left")
        right_html  = _elements_at("right")
        bottom_html = _elements_at("bottom")

        home_url = f"{base_url}?actor={actor}"
        breadcrumb_html = f"""<nav class="breadcrumbs" style="padding:8px 0;font-size:14px;">
  <a href="{home_url}" style="text-decoration:none;">Home</a>
  <span style="margin:0 6px;">/</span>
  <span style="font-weight:600;">{page}</span>
</nav>"""

        page_body = f"""{breadcrumb_html}
<div class="{surface_class}">
  {body}
</div>"""

        if left_html or right_html:
            main_content = f"""{top_html}
<div style="display:flex;min-height:calc(100vh - 60px);">
  {left_html}
  <div class="content {main_class}" style="flex:1;padding:20px;">
    {page_body}
  </div>
  {right_html}
</div>
{bottom_html}"""
        else:
            main_content = f"""{top_html}
<div class="content {main_class}" style="padding:20px;">
  {page_body}
</div>
{bottom_html}"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <base target="_blank"/>
  <title>{page} — {actor_name} — {project_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  <style>body {{ margin:0; padding:0; }}</style>
</head>
<body class="{body_class}">
{main_content}
</body>
</html>"""
        return HttpResponse(html, content_type="text/html")

    # ── Actor Home page: ?actor=<id> ─────────────────────────────────────────
    if actor:
        app = next((a for a in apps if a.get("actor_id") == actor), None)
        if not app:
            return HttpResponse(f"<h1>Actor '{actor}' not found</h1>", status=404, content_type="text/html")

        actor_name = app.get("actor_name") or actor_name_map.get(actor, actor)
        body_class = _page_body_class(preview_theme)
        main_class = _page_main_class(preview_theme, None)

        global_layout = preview_layout or {}

        def _elements_at(pos: str) -> str:
            parts = [
                v["html"] for v in global_layout.values()
                if isinstance(v, dict) and v.get("position") == pos and v.get("html")
            ]
            return "\n".join(parts)

        top_html    = _elements_at("top")
        left_html   = _elements_at("left")
        right_html  = _elements_at("right")
        bottom_html = _elements_at("bottom")

        # Build Home page body — workflow processes + tasks
        parser_dsl = state.get("parser_dsl") or {}
        workflows = parser_dsl.get("workflows", []) or []
        all_pages = app.get("pages", [])

        process_items_html = ""
        for wf in workflows:
            wf_name = wf.get("name", "")
            lanes = wf.get("lanes", []) or []
            if lanes and lanes[0].get("actor") == actor:
                process_items_html += f"""
<div class="process-item" style="padding:20px;width:350px;display:flex;justify-content:space-between;align-items:center;">
  <h4 style="margin:0;font-size:20px;flex:1;text-align:left;">{wf_name}</h4>
  <button disabled style="border:none;padding:12px;cursor:pointer;">Start</button>
</div>"""

        if not process_items_html:
            process_items_html = '<p style="font-size:18px;">No processes available</p>'

        activity_pages = [p for p in all_pages if p.get("type") == "activity"]
        task_items_html = ""
        for ap in activity_pages:
            act_name = ap.get("activity_name") or ap.get("name", "Task")
            task_items_html += f"""
<div class="process-item" style="padding:20px;width:350px;display:flex;justify-content:space-between;align-items:center;">
  <h4 style="margin:0;font-size:20px;flex:1;text-align:left;">{act_name}</h4>
  <div style="font-size:14px;margin-top:5px;">Pending</div>
</div>"""

        if not task_items_html:
            task_items_html = '<p style="font-size:18px;">No tasks to complete</p>'

        home_body = f"""
<h2>Processes you can start</h2>
{process_items_html}
<h2 style="margin-top: 32px;">Tasks to complete</h2>
{task_items_html}
"""

        if left_html or right_html:
            main_content = f"""{top_html}
<div style="display:flex;min-height:calc(100vh - 60px);">
  {left_html}
  <div class="content {main_class}" style="flex:1;padding:20px;">
    {home_body}
  </div>
  {right_html}
</div>
{bottom_html}"""
        else:
            main_content = f"""{top_html}
<div class="content {main_class}" style="padding:20px;">
  {home_body}
</div>
{bottom_html}"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <base target="_blank"/>
  <title>Home — {actor_name} — {project_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>body {{ margin:0; padding:0; }}</style>
</head>
<body class="{body_class}">
{main_content}
</body>
</html>"""
        return HttpResponse(html, content_type="text/html")

    # ── Index page — list all actors ──────────────────────────────────────────
    cards_html = ""
    body_class = _page_body_class(preview_theme)
    list_main_class = _preview_list_main_class(preview_theme)
    card_class = _preview_list_card_class(preview_theme)
    for app in apps:
        actor_id = app.get("actor_id", "unknown")
        actor_name = app.get("actor_name") or actor_name_map.get(actor_id, actor_id)
        page_count = len(app.get("pages", []))
        page_label = f"{page_count} page{'s' if page_count != 1 else ''}"
        cards_html += f"""
<a href="{base_url}?actor={actor_id}"
  class="block {card_class}">
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
  <base target="_blank"/>
  <title>Preview — {project_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="{body_class} min-h-screen p-8 font-sans">
  <header class="mb-8 border-b border-gray-200 pb-4">
    <h1 class="text-2xl font-bold text-gray-900">{project_name}</h1>
    <p class="text-sm text-gray-500 mt-1">Select an actor to view their pages &mdash; <code class="font-mono text-xs">{thread_id}</code></p>
  </header>
  <main class="{list_main_class}">
    {cards_html if cards_html else '<p class="text-gray-500">No actors generated yet.</p>'}
  </main>
</body>
</html>"""
    return HttpResponse(html, content_type="text/html")
