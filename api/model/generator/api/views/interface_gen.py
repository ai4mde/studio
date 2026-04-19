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
    """Render a standalone HTML preview matching the prototype layout
    (header + sidebar + content with breadcrumbs, tables, pagination)."""
    tokens = variant.get("tokens", {})
    pages = interface_data.get("pages", [])
    sections = interface_data.get("sections", [])

    body_cls = _get_token(tokens, "page.body", "bg-white text-gray-900 font-sans")
    main_cls = _get_token(tokens, "page.main", "")
    surface_cls = _get_token(tokens, "page.surface", "")
    btn_primary = _get_token(tokens, "component.button.primary",
                             "bg-blue-600 text-white px-4 py-2 rounded-lg font-medium")
    btn_secondary = _get_token(tokens, "component.button.secondary",
                               "bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium")
    input_cls = _get_token(tokens, "element.input.editable",
                           "border border-gray-300 rounded-lg px-3 py-2 w-full")
    label_cls = _get_token(tokens, "element.label", "text-sm font-medium mb-1 block")
    heading_cls = _get_token(tokens, "element.heading", "text-2xl font-bold")
    th_cls = _get_token(tokens, "element.th",
                        "text-left text-xs font-semibold uppercase tracking-wider px-4 py-3")
    td_cls = _get_token(tokens, "element.td", "px-4 py-3 text-sm")
    card_cls = _get_token(tokens, "component.card", "rounded-lg border p-4")
    table_cls = _get_token(tokens, "component.table", "min-w-full divide-y")
    form_cls = _get_token(tokens, "region.form", "space-y-4")
    header_cls = _get_token(tokens, "region.header", "")
    nav_cls = _get_token(tokens, "region.nav", "")

    # ── Sidebar navigation links ──
    nav_links = '<a href="#">Home</a>\n'
    for p in pages:
        p_name = p.get("name", "Page")
        nav_links += f'<a href="#">{p_name}</a>\n'

    # ── First page content ──
    first_page = pages[0] if pages else {"name": interface_name, "id": ""}
    first_page_name = first_page.get("name", interface_name)
    page_id = first_page.get("id", "")

    page_sections = [s for s in sections if str(s.get("page", "")) == str(page_id)]
    if not page_sections:
        page_sections = [s for s in sections if s.get("pageName", "") == first_page_name]
    if not page_sections:
        page_sections = [
            {"name": "Data Overview", "attributes": [
                {"name": "Name", "type": "str"}, {"name": "Status", "type": "str"},
                {"name": "Created", "type": "date"}, {"name": "Amount", "type": "int"}
            ]},
        ]

    # Tab buttons when multiple sections
    tabs_html = ""
    if len(page_sections) > 1:
        tabs_html = '<div class="tabs" role="tablist">\n'
        for i, sec in enumerate(page_sections):
            sec_name = sec.get("name", f"Section {i + 1}")
            active = " tab-active" if i == 0 else ""
            tabs_html += (
                f'<button class="tab-btn{active}" role="tab">{sec_name}</button>\n'
            )
        tabs_html += "</div>\n"

    # ── Build section content (matching page.html.jinja2) ──
    page_content = ""
    for idx, sec in enumerate(page_sections):
        sec_name = sec.get("name", "Section")
        attrs = sec.get("attributes", [])
        if not attrs:
            attrs = [{"name": "Field 1", "type": "str"}, {"name": "Field 2", "type": "str"}]

        # Tab panel wrapper
        if len(page_sections) > 1:
            active_panel = " tab-panel-active" if idx == 0 else ""
            page_content += (
                f'<div class="tab-panel{active_panel}" id="tab-{idx + 1}" role="tabpanel">\n'
            )

        # Section header with accordion
        page_content += f"""
        <div class="section-header" data-accordion="section-body-{idx + 1}">
            <h2 class="{heading_cls}">{sec_name}</h2>
            <span class="accordion-icon">&#9660;</span>
        </div>
        <div class="section-body {card_cls}" id="section-body-{idx + 1}">
        """

        # Search bar
        page_content += """
        <div class="search-bar">
            <input type="text" class="search-input" placeholder="Search...">
        </div>
        """

        # Table
        visible_attrs = attrs[:6]
        th_html = "".join(
            f'<th class="{th_cls}">{a.get("name", "")}</th>' for a in visible_attrs
        )
        th_html += f'<th class="{th_cls}"></th><th class="{th_cls}"></th>'

        sample_rows = ""
        for row_i in range(3):
            cells = ""
            for a in visible_attrs:
                a_type = a.get("type", "str")
                if a_type in ("int", "float", "number"):
                    val = str(10 + row_i * 5)
                elif a_type == "date":
                    val = f"2024-01-{10 + row_i:02d}"
                elif a_type == "bool":
                    checked = " checked" if row_i % 2 == 0 else ""
                    val = f'<input type="checkbox" disabled{checked}>'
                else:
                    val = f"Sample {row_i + 1}"
                cells += f'<td class="{td_cls}" style="text-align:center;">{val}</td>'
            # Edit icon
            cells += (
                '<td><svg width="20" height="20" viewBox="0 0 24 24" fill="none">'
                '<path d="M21.28 6.4L11.74 15.94C10.79 16.89 7.97 17.33 7.34 16.7'
                "C6.71 16.07 7.14 13.25 8.09 12.3L17.64 2.75C18.43 1.94 19.71 1.94"
                ' 20.5 2.73C21.29 3.51 21.29 4.79 20.5 5.58Z"'
                ' stroke="currentColor" stroke-width="1.5" stroke-linecap="round"'
                ' stroke-linejoin="round"/>'
                '<path d="M11 4H6C4.94 4 3.92 4.42 3.17 5.17C2.42 5.92 2 6.94 2 8'
                "V18C2 19.06 2.42 20.08 3.17 20.83C3.92 21.58 4.94 22 6 22H17"
                'C19.21 22 20 20.2 20 18V13"'
                ' stroke="currentColor" stroke-width="1.5" stroke-linecap="round"'
                ' stroke-linejoin="round"/></svg></td>'
            )
            # Delete icon
            cells += (
                '<td><svg width="20" height="20" viewBox="0 0 24 24" fill="none">'
                '<path d="M10 12V17" stroke="currentColor" stroke-width="2"'
                ' stroke-linecap="round" stroke-linejoin="round"/>'
                '<path d="M14 12V17" stroke="currentColor" stroke-width="2"'
                ' stroke-linecap="round" stroke-linejoin="round"/>'
                '<path d="M4 7H20" stroke="currentColor" stroke-width="2"'
                ' stroke-linecap="round" stroke-linejoin="round"/>'
                '<path d="M6 10V18C6 19.66 7.34 21 9 21H15C16.66 21 18 19.66 18 18V10"'
                ' stroke="currentColor" stroke-width="2" stroke-linecap="round"'
                ' stroke-linejoin="round"/>'
                '<path d="M9 5C9 3.9 9.9 3 11 3H13C14.1 3 15 3.9 15 5V7H9V5Z"'
                ' stroke="currentColor" stroke-width="2" stroke-linecap="round"'
                ' stroke-linejoin="round"/></svg></td>'
            )
            sample_rows += f"<tr>{cells}</tr>\n"

        page_content += f"""
        <table class="{table_cls}">
            <thead><tr>{th_html}</tr></thead>
            <tbody>{sample_rows}</tbody>
        </table>
        """

        # Pagination
        page_content += """
        <div class="pagination">
            <button class="page-btn page-prev" disabled>&laquo; Prev</button>
            <span class="page-info">Page <span class="page-current">1</span></span>
            <button class="page-btn page-next">Next &raquo;</button>
        </div>
        """

        # Create button
        page_content += f"""
        <button class="create-open-btn {btn_primary}">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M15 12H12M12 12H9M12 12V9M12 12V15M17 21H7C4.79 21 3 19.21
                 3 17V7C3 4.79 4.79 3 7 3H17C19.21 3 21 4.79 21 7V17C21 19.21 19.21
                 21 17 21Z" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round"/>
            </svg>
            Add {sec_name}
        </button>
        """

        page_content += "</div>\n"  # close section-body

        if len(page_sections) > 1:
            page_content += "</div>\n"  # close tab-panel

    # ── Inline CSS matching prototype style.css.jinja2 ──
    inline_css = """
/* Structural layout — SIDEBAR_LEFT (prototype default) */
.header {
    padding: 15px;
    text-align: center;
}
.header h1 { margin: 0; font-size: 24px; }
.menu {
    width: 220px;
    padding: 20px;
    float: left;
    height: 100vh;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    flex-wrap: nowrap;
}
.menu a {
    text-decoration: none;
    padding: 10px;
    display: block;
    border-radius: 6px;
    margin-bottom: 8px;
    text-align: center;
    max-width: 220px;
    text-overflow: ellipsis;
    white-space: nowrap;
    overflow: hidden;
}
.menu a:hover { opacity: 0.8; }
.content {
    padding: 20px;
    margin-left: 240px;
}

/* Breadcrumbs */
.breadcrumbs {
    display: flex; align-items: center; gap: 4px;
    padding: 8px 0; margin-bottom: 16px;
    font-size: 13px; color: #666;
}
.breadcrumbs a { text-decoration: none; }
.breadcrumbs a:hover { text-decoration: underline; }
.breadcrumb-sep { margin: 0 4px; color: #999; }
.breadcrumb-current { font-weight: 600; }

/* Tabs */
.tabs {
    display: flex; gap: 2px;
    border-bottom: 2px solid #e0e0e0; margin-bottom: 0;
}
.tab-btn {
    padding: 10px 20px; border: none; background: transparent;
    cursor: pointer; font-size: 14px; font-weight: 500; color: #666;
    border-bottom: 2px solid transparent; margin-bottom: -2px;
}
.tab-btn.tab-active { font-weight: 600; border-bottom-color: currentColor; }
.tab-panel { display: none; padding-top: 16px; }
.tab-panel-active { display: block; }

/* Section header / accordion */
.section-header {
    display: flex; align-items: center; justify-content: space-between;
    cursor: pointer; padding: 8px 0; user-select: none;
}
.section-header:hover { opacity: 0.8; }
.accordion-icon { font-size: 12px; color: #999; }
.section-body { overflow: visible; }
.section-body-collapsed { max-height: 0 !important; overflow: hidden; padding: 0; margin: 0; }

/* Search bar */
.search-bar { margin-bottom: 12px; max-width: 320px; }
.search-input {
    width: 100%; padding: 8px 12px;
    border: 1px solid #ddd; border-radius: 6px;
    font-size: 14px; box-sizing: border-box;
}
.search-input:focus { outline: none; border-color: #666; box-shadow: 0 0 0 2px rgba(0,0,0,0.05); }

/* Table */
table { width: 100%; border-collapse: collapse; margin-top: 10px; border-radius: 6px; overflow: hidden; }
table th, table td { border: 1px solid #ddd; padding: 8px; text-align: left; }

/* Pagination */
.pagination {
    display: flex; align-items: center; gap: 12px;
    margin-top: 12px; font-size: 13px;
}
.page-btn {
    padding: 6px 14px; border: 1px solid #ddd; border-radius: 6px;
    cursor: pointer; font-size: 13px; background: transparent;
}
.page-btn:disabled { opacity: 0.4; cursor: default; }
.page-info { color: #666; }

/* Create button */
.create-open-btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 16px; margin-top: 12px;
    border: none; border-radius: 6px;
    cursor: pointer; font-size: 14px;
}

/* Process containers (home page) */
.process-container {
    display: flex; justify-content: flex-start; align-items: flex-start;
    gap: 20px; margin-top: 20px;
}
.process-list { display: flex; flex-direction: column; gap: 12px; }
.process-item {
    border-radius: 6px; padding: 16px; width: 320px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    display: flex; justify-content: space-between; align-items: center;
}
.process-button {
    border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer;
}
"""

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <title>{variant.get('name', 'Preview')} &mdash; {interface_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>{inline_css}</style>
</head>
<body class="{body_cls}">
  <div class="header {header_cls}">
    <h1 class="{heading_cls}">{interface_name}</h1>
  </div>
  <div class="menu {nav_cls}">
    {nav_links}
  </div>
  <div class="content {main_cls}">
    <nav class="breadcrumbs" aria-label="breadcrumb">
      <a href="#">Home</a>
      <span class="breadcrumb-sep">/</span>
      <span class="breadcrumb-current">{first_page_name}</span>
    </nav>
    <div class="{surface_cls}">
      {tabs_html}
      {page_content}
    </div>
  </div>
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
