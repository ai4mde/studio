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
import os
import re
import uuid
from enum import Enum
from types import SimpleNamespace
from typing import Optional

from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from ninja import Router, Schema

from jinja2 import Environment, FileSystemLoader

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


# ── Prototype template rendering (style.css.jinja2) ─────────────────────────
# Mirror the enums from prototypes/generation/definitions/styling.py so that
# style.css.jinja2 can reference StyleType.* / LayoutType.* in conditionals.

class _StyleType(Enum):
    BASIC = 1; MODERN = 2; ABSTRACT = 3; ELEGANT = 4
    BRUTALIST = 5; GLASSMORPHISM = 6; DARK = 7

class _LayoutType(Enum):
    SIDEBAR_LEFT = 1; SIDEBAR_RIGHT = 2; TOP_NAV = 3; TOP_NAV_SIDEBAR = 4

_PROTO_TEMPLATES_DIR = "/usr/src/proto_templates"

# Tailwind named-color palette → hex (covers all standard colors).
_TW_COLORS = {
    "slate":   {50:"#f8fafc",100:"#f1f5f9",200:"#e2e8f0",300:"#cbd5e1",400:"#94a3b8",500:"#64748b",600:"#475569",700:"#334155",800:"#1e293b",900:"#0f172a",950:"#020617"},
    "gray":    {50:"#f9fafb",100:"#f3f4f6",200:"#e5e7eb",300:"#d1d5db",400:"#9ca3af",500:"#6b7280",600:"#4b5563",700:"#374151",800:"#1f2937",900:"#111827",950:"#030712"},
    "zinc":    {50:"#fafafa",100:"#f4f4f5",200:"#e4e4e7",300:"#d4d4d8",400:"#a1a1aa",500:"#71717a",600:"#52525b",700:"#3f3f46",800:"#27272a",900:"#18181b",950:"#09090b"},
    "neutral": {50:"#fafafa",100:"#f5f5f5",200:"#e5e5e5",300:"#d4d4d4",400:"#a3a3a3",500:"#737373",600:"#525252",700:"#404040",800:"#262626",900:"#171717",950:"#0a0a0a"},
    "stone":   {50:"#fafaf9",100:"#f5f5f4",200:"#e7e5e4",300:"#d6d3d1",400:"#a8a29e",500:"#78716c",600:"#57534e",700:"#44403c",800:"#292524",900:"#1c1917",950:"#0c0a09"},
    "red":     {50:"#fef2f2",100:"#fee2e2",200:"#fecaca",300:"#fca5a5",400:"#f87171",500:"#ef4444",600:"#dc2626",700:"#b91c1c",800:"#991b1b",900:"#7f1d1d",950:"#450a0a"},
    "orange":  {50:"#fff7ed",100:"#ffedd5",200:"#fed7aa",300:"#fdba74",400:"#fb923c",500:"#f97316",600:"#ea580c",700:"#c2410c",800:"#9a3412",900:"#7c2d12",950:"#431407"},
    "amber":   {50:"#fffbeb",100:"#fef3c7",200:"#fde68a",300:"#fcd34d",400:"#fbbf24",500:"#f59e0b",600:"#d97706",700:"#b45309",800:"#92400e",900:"#78350f",950:"#451a03"},
    "yellow":  {50:"#fefce8",100:"#fef9c3",200:"#fef08a",300:"#fde047",400:"#facc15",500:"#eab308",600:"#ca8a04",700:"#a16207",800:"#854d0e",900:"#713f12",950:"#422006"},
    "lime":    {50:"#f7fee7",100:"#ecfccb",200:"#d9f99d",300:"#bef264",400:"#a3e635",500:"#84cc16",600:"#65a30d",700:"#4d7c0f",800:"#3f6212",900:"#365314",950:"#1a2e05"},
    "green":   {50:"#f0fdf4",100:"#dcfce7",200:"#bbf7d0",300:"#86efac",400:"#4ade80",500:"#22c55e",600:"#16a34a",700:"#15803d",800:"#166534",900:"#14532d",950:"#052e16"},
    "emerald": {50:"#ecfdf5",100:"#d1fae5",200:"#a7f3d0",300:"#6ee7b7",400:"#34d399",500:"#10b981",600:"#059669",700:"#047857",800:"#065f46",900:"#064e3b",950:"#022c22"},
    "teal":    {50:"#f0fdfa",100:"#ccfbf1",200:"#99f6e4",300:"#5eead4",400:"#2dd4bf",500:"#14b8a6",600:"#0d9488",700:"#0f766e",800:"#115e59",900:"#134e4a",950:"#042f2e"},
    "cyan":    {50:"#ecfeff",100:"#cffafe",200:"#a5f3fc",300:"#67e8f9",400:"#22d3ee",500:"#06b6d4",600:"#0891b2",700:"#0e7490",800:"#155e75",900:"#164e63",950:"#083344"},
    "sky":     {50:"#f0f9ff",100:"#e0f2fe",200:"#bae6fd",300:"#7dd3fc",400:"#38bdf8",500:"#0ea5e9",600:"#0284c7",700:"#0369a1",800:"#075985",900:"#0c4a6e",950:"#082f49"},
    "blue":    {50:"#eff6ff",100:"#dbeafe",200:"#bfdbfe",300:"#93c5fd",400:"#60a5fa",500:"#3b82f6",600:"#2563eb",700:"#1d4ed8",800:"#1e40af",900:"#1e3a8a",950:"#172554"},
    "indigo":  {50:"#eef2ff",100:"#e0e7ff",200:"#c7d2fe",300:"#a5b4fc",400:"#818cf8",500:"#6366f1",600:"#4f46e5",700:"#4338ca",800:"#3730a3",900:"#312e81",950:"#1e1b4b"},
    "violet":  {50:"#f5f3ff",100:"#ede9fe",200:"#ddd6fe",300:"#c4b5fd",400:"#a78bfa",500:"#8b5cf6",600:"#7c3aed",700:"#6d28d9",800:"#5b21b6",900:"#4c1d95",950:"#2e1065"},
    "purple":  {50:"#faf5ff",100:"#f3e8ff",200:"#e9d5ff",300:"#d8b4fe",400:"#c084fc",500:"#a855f7",600:"#9333ea",700:"#7e22ce",800:"#6b21a8",900:"#581c87",950:"#3b0764"},
    "fuchsia": {50:"#fdf4ff",100:"#fae8ff",200:"#f5d0fe",300:"#f0abfc",400:"#e879f9",500:"#d946ef",600:"#c026d3",700:"#a21caf",800:"#86198f",900:"#701a75",950:"#4a044e"},
    "pink":    {50:"#fdf2f8",100:"#fce7f3",200:"#fbcfe8",300:"#f9a8d4",400:"#f472b6",500:"#ec4899",600:"#db2777",700:"#be185d",800:"#9d174d",900:"#831843",950:"#500724"},
    "rose":    {50:"#fff1f2",100:"#ffe4e6",200:"#fecdd3",300:"#fda4af",400:"#fb7185",500:"#f43f5e",600:"#e11d48",700:"#be123c",800:"#9f1239",900:"#881337",950:"#4c0519"},
}
_TW_SPECIAL = {"white": "#ffffff", "black": "#000000", "transparent": "transparent"}
_TW_RADIUS = {
    "rounded-none": 0, "rounded-sm": 2, "rounded": 4, "rounded-md": 6,
    "rounded-lg": 8, "rounded-xl": 12, "rounded-2xl": 16,
    "rounded-3xl": 24, "rounded-full": 999,
}


def _tw_to_hex(classes: str, prefixes: tuple) -> str | None:
    """Extract first hex color from a Tailwind class string matching *prefixes*."""
    if not classes:
        return None
    for cls in classes.split():
        if not any(cls.startswith(p) for p in prefixes):
            continue
        # Arbitrary value: bg-[#1a1a2e]
        arb = re.search(r'\[(#[0-9a-fA-F]{3,8})\]', cls)
        if arb:
            return arb.group(1)
        # Special: bg-white, bg-black
        for sp, hx in _TW_SPECIAL.items():
            if cls.endswith(f"-{sp}"):
                return hx
        # Named: bg-gray-900
        m = re.search(r'-([a-z]+)-(\d+)$', cls)
        if m:
            return _TW_COLORS.get(m.group(1), {}).get(int(m.group(2)))
    return None


def _extract_styling_from_tokens(tokens: dict) -> SimpleNamespace:
    """Build a Styling-compatible object by deriving colours from theme tokens."""
    body = tokens.get("page.body", "")
    btn = tokens.get("component.button.primary", "")

    bg = _tw_to_hex(body, ("bg-", "from-")) or "#FFFFFF"
    text = _tw_to_hex(body, ("text-",)) or "#000000"
    accent = _tw_to_hex(btn, ("bg-", "border-")) or "#2563eb"

    radius = 4
    for cls in btn.split():
        if cls in _TW_RADIUS:
            radius = _TW_RADIUS[cls]
            break

    return SimpleNamespace(
        style_type=_StyleType.BASIC,
        layout_type=_LayoutType.SIDEBAR_LEFT,
        radius=radius,
        text_color=text,
        accent_color=accent,
        background_color=bg,
    )


def _render_style_css(theme: dict) -> str:
    """Render style.css.jinja2 from the prototype templates with variant tokens."""
    tokens = theme.get("tokens", {})
    styling = _extract_styling_from_tokens(tokens)
    try:
        env = Environment(loader=FileSystemLoader(_PROTO_TEMPLATES_DIR))
        tpl = env.get_template("style.css.jinja2")
        tpl.globals["StyleType"] = _StyleType
        tpl.globals["LayoutType"] = _LayoutType
        return tpl.render(
            styling=styling,
            theme=theme,
            theme_summary={},
            global_layout={},
        )
    except Exception as e:
        logger.warning("Failed to render style.css.jinja2: %s", e)
        return ""


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

    # Sidebar nav links — matches base.html.jinja2 SIDEBAR_LEFT
    nav_links = '<a href="#">Home</a>\n'
    for p in pages:
        p_name = p.get("name", "Page")
        nav_links += f'<a href="#">{p_name}</a>\n'
    nav_links += '<a href="#">Logout</a>\n'

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
            selected = "true" if i == 0 else "false"
            tabs_html += (
                f'<button class="tab-btn{active}" role="tab"'
                f' data-tab="tab-{i + 1}" aria-selected="{selected}">{sec_name}</button>\n'
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
        table_id = f"table-{idx + 1}"
        page_content += f"""
        <div class="search-bar">
            <input type="text" class="search-input" data-table="{table_id}" placeholder="Search...">
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
        <table class="{table_cls}" id="{table_id}">
            <thead><tr>{th_html}</tr></thead>
            <tbody>{sample_rows}</tbody>
        </table>
        """

        # Pagination
        page_content += f"""
        <div class="pagination" data-table="{table_id}">
            <button class="page-btn page-prev" disabled>&laquo; Prev</button>
            <span class="page-info">Page <span class="page-current">1</span></span>
            <button class="page-btn page-next">Next &raquo;</button>
        </div>
        """

        # Create button
        modal_id = f"modal-create-{idx + 1}"
        page_content += f"""
        <button class="create-open-btn {btn_primary}" data-modal="{modal_id}">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M15 12H12M12 12H9M12 12V9M12 12V15M17 21H7C4.79 21 3 19.21
                 3 17V7C3 4.79 4.79 3 7 3H17C19.21 3 21 4.79 21 7V17C21 19.21 19.21
                 21 17 21Z" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round"/>
            </svg>
            Add {sec_name}
        </button>
        """

        # Modal for create form (matching page.html.jinja2)
        modal_fields = ""
        for a in attrs[:6]:
            a_name = a.get("name", "Field")
            a_type = a.get("type", "str")
            input_type = "number" if a_type in ("int", "float", "number") else (
                "date" if a_type == "date" else "text"
            )
            if a_type == "bool":
                modal_fields += f"""
                <div class="form-group">
                    <label class="{label_cls}">{a_name}</label>
                    <input type="checkbox" class="{input_cls}">
                </div>"""
            else:
                modal_fields += f"""
                <div class="form-group">
                    <label class="{label_cls}">{a_name}</label>
                    <input type="{input_type}" class="{input_cls}" placeholder="{a_name}">
                </div>"""

        page_content += f"""
        <div class="modal-overlay" id="{modal_id}">
            <div class="modal">
                <div class="modal-header">
                    <h3>Create {sec_name}</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <form onsubmit="return false;">
                        {modal_fields}
                        <div class="modal-actions">
                            <button type="button" class="btn-cancel modal-close">Cancel</button>
                            <button type="submit" class="btn-save {btn_primary}">Save</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        """

        page_content += "</div>\n"  # close section-body

        if len(page_sections) > 1:
            page_content += "</div>\n"  # close tab-panel

    # ── CSS from the actual prototype template ──────────────────────────────
    theme = {"name": variant.get("name", ""), "tokens": tokens}
    inline_css = _render_style_css(theme)

    # JavaScript — same as page.html.jinja2 output
    page_js = """
<script>
(function(){
    /* Tabs */
    document.querySelectorAll('.tab-btn').forEach(function(btn){
        btn.addEventListener('click', function(){
            var tabId = this.getAttribute('data-tab');
            this.closest('.tabs').querySelectorAll('.tab-btn').forEach(function(b){ b.classList.remove('tab-active'); b.setAttribute('aria-selected','false'); });
            this.classList.add('tab-active');
            this.setAttribute('aria-selected','true');
            document.querySelectorAll('.tab-panel').forEach(function(p){ p.classList.remove('tab-panel-active'); });
            document.getElementById(tabId).classList.add('tab-panel-active');
        });
    });
    /* Search */
    document.querySelectorAll('.search-input').forEach(function(input){
        input.addEventListener('input', function(){
            var q = this.value.toLowerCase();
            var tableId = this.getAttribute('data-table');
            var rows = document.querySelectorAll('#'+tableId+' tbody tr');
            rows.forEach(function(row){ row.style.display = row.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none'; });
        });
    });
    /* Pagination */
    var PAGE_SIZE = 10;
    document.querySelectorAll('.pagination').forEach(function(pag){
        var tableId = pag.getAttribute('data-table');
        var rows = document.querySelectorAll('#'+tableId+' tbody tr');
        var currentPage = 1;
        var totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
        function render(){
            rows.forEach(function(r,i){ r.style.display = (i >= (currentPage-1)*PAGE_SIZE && i < currentPage*PAGE_SIZE) ? '' : 'none'; });
            pag.querySelector('.page-current').textContent = currentPage;
            pag.querySelector('.page-prev').disabled = currentPage <= 1;
            pag.querySelector('.page-next').disabled = currentPage >= totalPages;
            if(rows.length <= PAGE_SIZE) pag.style.display = 'none';
        }
        pag.querySelector('.page-prev').addEventListener('click', function(){ if(currentPage>1){currentPage--;render();} });
        pag.querySelector('.page-next').addEventListener('click', function(){ if(currentPage<totalPages){currentPage++;render();} });
        render();
    });
    /* Modal */
    document.querySelectorAll('.create-open-btn').forEach(function(btn){
        btn.addEventListener('click', function(){ document.getElementById(this.getAttribute('data-modal')).classList.add('modal-visible'); });
    });
    document.querySelectorAll('.modal-close').forEach(function(btn){
        btn.addEventListener('click', function(){ this.closest('.modal-overlay').classList.remove('modal-visible'); });
    });
    document.querySelectorAll('.modal-overlay').forEach(function(overlay){
        overlay.addEventListener('click', function(e){ if(e.target === this) this.classList.remove('modal-visible'); });
    });
    /* Accordion */
    document.querySelectorAll('.section-header[data-accordion]').forEach(function(header){
        header.addEventListener('click', function(){
            var body = document.getElementById(this.getAttribute('data-accordion'));
            var icon = this.querySelector('.accordion-icon');
            if(body.classList.contains('section-body-collapsed')){ body.classList.remove('section-body-collapsed'); icon.textContent = '\\u25BC'; }
            else { body.classList.add('section-body-collapsed'); icon.textContent = '\\u25B6'; }
        });
    });
})();
</script>"""

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
    <div class="logo"></div>
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
  {page_js}
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
