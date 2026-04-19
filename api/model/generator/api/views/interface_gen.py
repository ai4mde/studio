"""
Interface UI Generation API — generate 3 style variants for an interface,
preview them, and refine via human-in-the-loop.

Endpoints:
  POST /interface-gen/generate/                          Start variant generation
  GET  /interface-gen/{session_id}/                      Get session state + variants
  GET  /interface-gen/{session_id}/preview/{variant_id}/ Preview HTML for a variant
  POST /interface-gen/{session_id}/refine/                Refine a selected variant
  POST /interface-gen/{session_id}/apply/                 Apply variant to the interface
"""
import json
import logging
import uuid
from typing import Optional

from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from ninja import Router, Schema

from llm.handler import call_openai
from llm.prompts.agents import AGENT_INTERFACE_VARIANTS, AGENT_INTERFACE_REFINE

logger = logging.getLogger(__name__)

interface_gen_router = Router()

# ── In-memory session store ──────────────────────────────────────────────────
# For production, replace with Redis or DB-backed storage.
_sessions: dict[str, dict] = {}


# ── Schemas ──────────────────────────────────────────────────────────────────

class GenerateSchema(Schema):
    interface_id: str
    prompt: str


class RefineSchema(Schema):
    variant_id: str
    prompt: str


class ApplySchema(Schema):
    variant_id: str


class ErrorSchema(Schema):
    error: str


# ── Helpers ──────────────────────────────────────────────────────────────────

def _parse_json_response(raw: str) -> dict:
    """Strip markdown fences and parse JSON."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(raw)


def _build_page_structure(interface_data: dict) -> str:
    """Summarise the interface's page/section structure for the LLM."""
    pages = interface_data.get("pages", [])
    sections = interface_data.get("sections", [])
    lines = []
    for page in pages:
        name = page.get("name", "Unnamed")
        lines.append(f"Page: {name}")
        # find sections belonging to this page
        page_id = page.get("id", "")
        page_sections = [s for s in sections if str(s.get("page", "")) == str(page_id)]
        if not page_sections:
            # try matching by name
            page_sections = [s for s in sections if s.get("pageName", "") == name]
        for sec in page_sections:
            sec_name = sec.get("name", "Section")
            attrs = sec.get("attributes", [])
            attr_names = [a.get("name", "") for a in attrs if a.get("name")]
            if attr_names:
                lines.append(f"  Section: {sec_name} — Fields: {', '.join(attr_names)}")
            else:
                lines.append(f"  Section: {sec_name}")
    if not lines:
        lines.append("(No page structure defined yet)")
    return "\n".join(lines)


def _get_token(tokens: dict, key: str, fallback: str = "") -> str:
    return tokens.get(key, fallback)


def _render_variant_preview(interface_data: dict, variant: dict, interface_name: str) -> str:
    """Render a standalone HTML preview for a variant using its theme tokens."""
    tokens = variant.get("tokens", {})
    pages = interface_data.get("pages", [])
    sections = interface_data.get("sections", [])

    body_cls = _get_token(tokens, "page.body", "bg-white text-gray-900 font-sans")
    main_cls = _get_token(tokens, "page.main", "max-w-5xl mx-auto p-8")
    surface_cls = _get_token(tokens, "page.surface", "rounded-xl bg-white shadow-lg p-6")
    btn_primary = _get_token(tokens, "component.button.primary", "bg-blue-600 text-white px-4 py-2 rounded-lg font-medium")
    btn_secondary = _get_token(tokens, "component.button.secondary", "bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium")
    input_cls = _get_token(tokens, "element.input.editable", "border border-gray-300 rounded-lg px-3 py-2 w-full")
    readonly_cls = _get_token(tokens, "element.input.readonly", "bg-gray-100 border border-gray-200 rounded-lg px-3 py-2 w-full")
    label_cls = _get_token(tokens, "element.label", "text-sm font-medium mb-1 block")
    heading_cls = _get_token(tokens, "element.heading", "text-2xl font-bold")
    th_cls = _get_token(tokens, "element.th", "text-left text-xs font-semibold uppercase tracking-wider px-4 py-3")
    td_cls = _get_token(tokens, "element.td", "px-4 py-3 text-sm")
    card_cls = _get_token(tokens, "component.card", "rounded-lg border p-4")
    table_cls = _get_token(tokens, "component.table", "min-w-full divide-y")
    form_cls = _get_token(tokens, "region.form", "space-y-4")
    header_cls = _get_token(tokens, "region.header", "flex items-center justify-between mb-6 pb-4 border-b")
    nav_cls = _get_token(tokens, "region.nav", "flex items-center gap-4")

    # Build page tabs
    tab_items = ""
    for i, p in enumerate(pages):
        p_name = p.get("name", f"Page {i+1}")
        active = "font-bold border-b-2 border-current" if i == 0 else "opacity-60 hover:opacity-100"
        tab_items += f'<button class="px-3 py-2 text-sm {active}">{p_name}</button>\n'

    # Build page content for first page (or sample)
    page_content = ""
    first_page = pages[0] if pages else {"name": interface_name, "id": ""}
    first_page_name = first_page.get("name", interface_name)
    page_id = first_page.get("id", "")

    # Find sections for this page
    page_sections = [s for s in sections if str(s.get("page", "")) == str(page_id)]
    if not page_sections:
        page_sections = [s for s in sections if s.get("pageName", "") == first_page_name]
    if not page_sections:
        # Create sample sections
        page_sections = [
            {"name": "Data Overview", "attributes": [
                {"name": "Name", "type": "str"}, {"name": "Status", "type": "str"},
                {"name": "Created", "type": "date"}, {"name": "Amount", "type": "int"}
            ]},
            {"name": "Details", "attributes": [
                {"name": "Description", "type": "str"}, {"name": "Category", "type": "str"},
                {"name": "Priority", "type": "str"}
            ]},
        ]

    for sec in page_sections:
        sec_name = sec.get("name", "Section")
        attrs = sec.get("attributes", [])
        if not attrs:
            attrs = [{"name": "Field 1", "type": "str"}, {"name": "Field 2", "type": "str"}]

        # Table view
        th_html = "".join(f'<th class="{th_cls}">{a.get("name", "")}</th>' for a in attrs[:5])
        sample_rows = ""
        for row_i in range(3):
            cells = "".join(f'<td class="{td_cls}">Sample {row_i+1}</td>' for _ in attrs[:5])
            sample_rows += f'<tr>{cells}</tr>\n'

        # Form view
        form_fields = ""
        for attr in attrs[:4]:
            a_name = attr.get("name", "Field")
            a_type = attr.get("type", "str")
            input_type = "date" if a_type == "date" else "number" if a_type in ("int", "float") else "text"
            form_fields += f'''
            <div>
              <label class="{label_cls}">{a_name}</label>
              <input type="{input_type}" placeholder="{a_name}" class="{input_cls}" />
            </div>'''

        page_content += f'''
        <section class="{card_cls} mb-6">
          <h3 class="{heading_cls} text-lg mb-4">{sec_name}</h3>
          <div class="overflow-x-auto mb-4">
            <table class="{table_cls}">
              <thead><tr>{th_html}</tr></thead>
              <tbody class="divide-y">{sample_rows}</tbody>
            </table>
          </div>
          <div class="{form_cls}">
            <h4 class="{label_cls} text-base font-semibold">Add / Edit</h4>
            <div class="grid grid-cols-2 gap-4">{form_fields}</div>
            <div class="flex gap-2 pt-2">
              <button class="{btn_primary}">Save</button>
              <button class="{btn_secondary}">Cancel</button>
            </div>
          </div>
        </section>'''

    # Stat cards
    stats_html = ""
    stat_labels = ["Total Records", "Active", "Pending", "Completed"]
    stat_values = ["128", "94", "21", "13"]
    for lbl, val in zip(stat_labels, stat_values):
        stats_html += f'''
        <div class="{card_cls}">
          <p class="{label_cls} opacity-70">{lbl}</p>
          <p class="{heading_cls}">{val}</p>
        </div>'''

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{variant.get('name', 'Preview')} — {interface_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="{body_cls} min-h-screen">
  <nav class="{nav_cls} px-6 py-3 border-b">
    <span class="font-bold text-lg">{interface_name}</span>
    <div class="flex gap-3 ml-auto">
      {tab_items}
    </div>
  </nav>
  <main class="{main_cls}">
    <div class="{surface_cls}">
      <div class="{header_cls}">
        <div>
          <h1 class="{heading_cls}">{first_page_name}</h1>
          <p class="text-sm opacity-60 mt-1">{variant.get('name', '')} — {variant.get('description', '')}</p>
        </div>
        <button class="{btn_primary}">+ Create New</button>
      </div>
      <div class="grid grid-cols-4 gap-4 mb-6">{stats_html}</div>
      {page_content}
    </div>
  </main>
</body>
</html>"""


# ── Endpoints ────────────────────────────────────────────────────────────────

@interface_gen_router.post("/generate/", response={200: dict, 400: ErrorSchema})
def generate_variants(request, body: GenerateSchema):
    """Generate 3 UI style variants for an interface based on designer's prompt."""
    from metadata.models import Interface

    try:
        iface = Interface.objects.select_related("system", "actor").get(pk=body.interface_id)
    except Interface.DoesNotExist:
        return 400, {"error": f"Interface {body.interface_id} not found"}

    interface_data = iface.data if isinstance(iface.data, dict) else {}
    system_name = iface.system.name if iface.system else "System"
    actor_name = iface.actor.data.get("name", "Actor") if iface.actor and isinstance(iface.actor.data, dict) else "Actor"
    interface_name = iface.name or "Interface"

    page_structure = _build_page_structure(interface_data)

    prompt = AGENT_INTERFACE_VARIANTS.format(
        designer_prompt=body.prompt,
        system_name=system_name,
        interface_name=interface_name,
        actor_name=actor_name,
        page_structure=page_structure,
    )

    try:
        raw = call_openai("gpt-4o", prompt)
        result = _parse_json_response(raw)
        variants = result.get("variants", [])
    except Exception as exc:
        logger.error("Interface variant generation failed: %s", exc)
        return 400, {"error": f"LLM generation failed: {exc}"}

    if not variants or len(variants) < 3:
        return 400, {"error": "LLM did not produce 3 variants"}

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "session_id": session_id,
        "interface_id": body.interface_id,
        "interface_name": interface_name,
        "system_name": system_name,
        "actor_name": actor_name,
        "interface_data": interface_data,
        "original_prompt": body.prompt,
        "variants": variants,
        "selected_variant_id": None,
        "refine_history": [],
    }

    return {
        "session_id": session_id,
        "variants": [
            {"id": v["id"], "name": v["name"], "description": v["description"]}
            for v in variants
        ],
    }


@interface_gen_router.get("/{session_id}/", response={200: dict, 404: ErrorSchema})
def get_session(request, session_id: str):
    """Get current state of a generation session."""
    session = _sessions.get(session_id)
    if not session:
        return 404, {"error": "Session not found"}

    return {
        "session_id": session_id,
        "interface_id": session["interface_id"],
        "original_prompt": session["original_prompt"],
        "selected_variant_id": session["selected_variant_id"],
        "refine_history": session["refine_history"],
        "variants": [
            {"id": v["id"], "name": v["name"], "description": v["description"]}
            for v in session["variants"]
        ],
    }


@interface_gen_router.get("/{session_id}/preview/{variant_id}/", auth=None)
@xframe_options_exempt
def preview_variant(request, session_id: str, variant_id: str):
    """Render preview HTML for a specific variant."""
    session = _sessions.get(session_id)
    if not session:
        return HttpResponse("<h1>Session not found</h1>", status=404, content_type="text/html")

    variant = next((v for v in session["variants"] if v["id"] == variant_id), None)
    if not variant:
        return HttpResponse("<h1>Variant not found</h1>", status=404, content_type="text/html")

    html = _render_variant_preview(
        session["interface_data"],
        variant,
        session["interface_name"],
    )
    return HttpResponse(html, content_type="text/html")


@interface_gen_router.post("/{session_id}/refine/", response={200: dict, 404: ErrorSchema, 400: ErrorSchema})
def refine_variant(request, session_id: str, body: RefineSchema):
    """Refine a selected variant with a follow-up prompt."""
    session = _sessions.get(session_id)
    if not session:
        return 404, {"error": "Session not found"}

    variant = next((v for v in session["variants"] if v["id"] == body.variant_id), None)
    if not variant:
        return 400, {"error": f"Variant {body.variant_id} not found"}

    prompt = AGENT_INTERFACE_REFINE.format(
        system_name=session["system_name"],
        interface_name=session["interface_name"],
        original_prompt=session["original_prompt"],
        variant_name=variant["name"],
        variant_description=variant.get("description", ""),
        current_tokens=json.dumps(variant["tokens"], indent=2),
        refine_prompt=body.prompt,
    )

    try:
        raw = call_openai("gpt-4o", prompt)
        result = _parse_json_response(raw)
    except Exception as exc:
        logger.error("Interface variant refinement failed: %s", exc)
        return 400, {"error": f"Refinement failed: {exc}"}

    # Update the variant in place
    variant["name"] = result.get("name", variant["name"])
    variant["description"] = result.get("description", variant.get("description", ""))
    variant["tokens"] = result.get("tokens", variant["tokens"])

    session["selected_variant_id"] = body.variant_id
    session["refine_history"].append(body.prompt)

    return {
        "session_id": session_id,
        "variant": {"id": variant["id"], "name": variant["name"], "description": variant["description"]},
        "refine_history": session["refine_history"],
    }


@interface_gen_router.post("/{session_id}/apply/", response={200: dict, 404: ErrorSchema, 400: ErrorSchema})
def apply_variant(request, session_id: str, body: ApplySchema):
    """Apply the selected variant's theme to the interface and persist."""
    from metadata.models import Interface

    session = _sessions.get(session_id)
    if not session:
        return 404, {"error": "Session not found"}

    variant = next((v for v in session["variants"] if v["id"] == body.variant_id), None)
    if not variant:
        return 400, {"error": f"Variant {body.variant_id} not found"}

    try:
        iface = Interface.objects.get(pk=session["interface_id"])
    except Interface.DoesNotExist:
        return 400, {"error": "Interface no longer exists"}

    data = iface.data if isinstance(iface.data, dict) else {}
    data["theme"] = {
        "name": variant["name"],
        "tokens": variant["tokens"],
    }
    data["designerMeta"] = {
        "generatedFrom": "interface_gen",
        "originalPrompt": session["original_prompt"],
        "variantId": variant["id"],
        "variantName": variant["name"],
        "refineHistory": session["refine_history"],
    }
    iface.data = data
    iface.save(update_fields=["data"])

    # Clean up session
    _sessions.pop(session_id, None)

    return {
        "applied": True,
        "interface_id": session["interface_id"],
        "variant_name": variant["name"],
    }
